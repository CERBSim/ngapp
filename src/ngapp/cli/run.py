import base64
import shutil
from pathlib import Path

import orjson
from pydantic import BaseModel

from .. import api
from ..app import create_app
from ..utils import (
    EnvironmentType,
    _get_app_assets,
    get_environment,
    set_environment,
    write_file,
)


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

    def update_app_context(self, app_context):
        app_context.capture_events = self.capture_events
        app_context.capture_call_stack = self.capture_call_stack

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


def execute(data: RunData):
    """Run the compute function described by data in this process"""
    set_environment(EnvironmentType.COMPUTE)
    env = get_environment()
    env.set_backend(data.api_url, data.api_token)

    model = create_app(
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

    data.update_app_context(model.context)

    func_name = data.func_name

    if data.comp_id is not None:
        comp = model[data.comp_id]
        func = getattr(comp, func_name)
    else:
        if not hasattr(model, func_name):
            raise RuntimeError(f"Function {func_name} not found in model")
        func = getattr(model, func_name)

    if not hasattr(func, "__is_compute_node_function"):
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
    data.kwargs["job_id"] = data.job_id or None
    return func(*data.args, **data.kwargs)


def main():
    execute(RunData.load(input()))


if __name__ == "__main__":
    main()
