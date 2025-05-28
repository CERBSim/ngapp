import base64
import glob
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import orjson
from pydantic import BaseModel

from .. import api
from .._version import version
from ..app import loadModel
from ..utils import (
    EnvironmentType,
    _get_app_assets,
    get_environment,
    print_exception,
    set_environment,
    write_file,
)

_VENV_DIR = Path(f"/tmp/webapp_venv_compute_environments_{version}")


class RunData(BaseModel):
    api_url: str
    api_token: str
    app_id: int
    job_id: int
    file_id: int
    func_name: str
    compute_env: dict
    app: dict
    args: list = []
    kwargs: dict = {}
    comp_id: str | None = None
    capture_output: bool = True
    capture_events: bool = False
    capture_call_stack: bool = False
    env: dict = {}
    use_venv: bool = False

    def update_app_status(self, app_status):
        app_status.capture_events = self.capture_events
        app_status.capture_call_stack = self.capture_call_stack

    def load_file(self):
        return api.get(f"/files/{self.file_id}")

    def load_file_data(self):
        return api.get(f"/files/{self.file_id}/data")

    def dump_bytes(self):
        return base64.b64encode(orjson.dumps(self.model_dump()))

    def dump(self):
        return self.dump_bytes().decode()

    @staticmethod
    def load(data: str | bytes):
        if isinstance(data, bytes):
            data = data.decode()
        return RunData.model_validate(orjson.loads(base64.b64decode(data)))


def create_venv(venv_path):
    subprocess.check_output([sys.executable, "-m", "venv", venv_path])


def install_webapp_wheels(venv_path):
    """Install ngapp wheels and their dependencies from backend in venv"""
    wheels = ["ngapp"]
    site_dir = glob.glob(str(venv_path / "lib/python3.*/site-packages/"))[0]
    for package_name in wheels:
        data = api.get(f"/pyodide/client_package/{package_name}")
        filename = "package.zip"
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file = Path(temp_dir) / filename
            with open(temp_file, "wb") as f:
                f.write(data)
            subprocess.check_output(["unzip", temp_file, "-d", site_dir])
            os.remove(temp_file)
    subprocess.check_output(
        [
            venv_path / "bin/python",
            "-m",
            "pip",
            "install",
            "numpy",
            "pint",
            "pydantic",
            "urllib3",
            "certifi",
        ]
    )


def install_packages(venv_path, packages):
    with tempfile.TemporaryDirectory() as temp_dir:
        wheel_names = []
        for p in packages:
            data = base64.b64decode(p["data"].encode())
            file_path = Path(temp_dir) / p["name"]
            with open(file_path, "wb") as file:
                file.write(data)
            wheel_names.append(file_path)
        subprocess.check_output(
            [venv_path / "bin/python", "-m", "pip", "install", *wheel_names]
        )


def create_app_venv(app: dict):
    venv_hash = app["python_packages_hash"]
    if not venv_hash:
        raise RuntimeError("App does not have python packages hash")
    venv_path = _VENV_DIR / str(app["id"]) / venv_hash

    if venv_path.exists():
        return venv_path

    print("create venv for app", app["id"], app["name"], "with hash", venv_hash)

    create_venv(venv_path)
    install_webapp_wheels(venv_path)
    packages = api.post("/get_app_python_packages", data={"app_id": app["id"]})
    install_packages(venv_path, packages)
    return venv_path


def run_compute_function(
    data: RunData | str,
):
    try:
        if isinstance(data, str):
            data = RunData.load(data)

        env = set_environment(EnvironmentType.COMPUTE)
        env.set_backend(data.api_url, data.api_token)

        api_url = f"/job/{data.job_id}"
        api.post(f"{api_url}/stdout", "\nSTATUS: Job started on compute node\n")
        api.post(f"{api_url}/stderr", "")
        api.put(api_url, {"status": "Running"})

        if data.use_venv:
            venv_path = create_app_venv(data.app)
            command = [venv_path / "bin/python"]
        else:
            command = [sys.executable]
        command += ["-m", "ngapp.cli.run"]

        # track maximum RSS memory and elapsed time using /usr/bin/time tool
        if sys.platform == "linux" and os.path.exists("/usr/bin/time"):
            command = [
                "/usr/bin/time",
                "-q",
                "-f",
                "%M",
                "-o",
                "mem_usage",
            ] + command
        elif sys.platform == "darwin" and os.path.exists(
            "/opt/homebrew/bin/gtime"
        ):
            command = [
                "/opt/homebrew/bin/gtime",
                "-q",
                "-f",
                "%M",
                "-o",
                "mem_usage",
            ] + command

        with tempfile.TemporaryDirectory() as temp_dir:
            tmp = Path(temp_dir)
            env = os.environ.copy()
            env.update(data.env)
            p = subprocess.Popen(
                command,
                stdout=open(tmp / "stdout", "wb"),
                stdin=subprocess.PIPE,
                stderr=open(tmp / "stderr", "wb"),
                text=False,
                cwd=temp_dir,
                env=env,
            )
            p.communicate(input=data.dump_bytes())[0]
            api.put(f"{api_url}/stdout", (tmp / "stdout").read_text("utf-8"))
            api.post(f"{api_url}/stderr", (tmp / "stderr").read_text("utf-8"))
            print("stdout\n", (tmp / "stdout").read_text("utf-8"), "\n")
            print("stderr\n", (tmp / "stderr").read_text("utf-8"))
        api.put(
            f"{api_url}/stdout",
            f"\nSTATUS: Job finished on compute node with exit code {p.returncode}",
        )
        print("return code", p.returncode)
        api.put(
            api_url, {"status": "Finished" if p.returncode == 0 else "Failed"}
        )
    except Exception as e:
        print("error", e, flush=True)
        print_exception(e)


def main():
    data = RunData.load(input())
    set_environment(EnvironmentType.COMPUTE)
    env = get_environment()
    env.set_backend(data.api_url, data.api_token)

    model = loadModel(
        data.app,
        {"component": data.load_file_data(), "metadata": data.load_file()},
    )
    # add app assets
    try:
        for filename, file_data in _get_app_assets(data.app["name"]):
            asset_path = Path().cwd() / "assets"
            asset_path.mkdir(parents=True, exist_ok=True)
            write_file(asset_path / filename, file_data, binary=True)
    except:
        if (Path("/") / "assets").exists():
            shutil.copytree(Path("/") / "assets", Path().cwd() / "assets")

    data.update_app_status(model._status)

    func_name = data.func_name

    if data.comp_id is not None:
        comp = model[data.comp_id]
        func = getattr(comp, func_name)
    else:
        if not hasattr(model, func_name):
            raise RuntimeError(f"Function {func_name} not found in model")
        func = getattr(model, func_name)

    if not func.__is_compute_node_function:
        raise RuntimeError(
            f"Function {func} not allowed in backend computation"
        )

    compute_env = data.compute_env
    if (
        compute_env["env_type"] != "local"
        and compute_env["name"] != func.__compute_env
    ):
        raise RuntimeError(
            f"Function {func} not allowed in compute environment {compute_env}"
        )
    data.kwargs["job_id"] = data.job_id
    return func(*data.args, **data.kwargs)


if __name__ == "__main__":
    main()
