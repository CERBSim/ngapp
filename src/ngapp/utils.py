"""Utility functions for the ngapp module"""

import base64
import datetime
import functools
import hashlib
import importlib.util
import io
import os
import shutil
import sys
import tempfile
import traceback
import typing
from contextlib import contextmanager
from enum import Enum
from importlib import import_module
from pathlib import Path
from zipfile import ZipFile

import orjson
import pydantic

from . import api


def calc_hash(*data):
    hash_ = hashlib.sha256()
    for d in data:
        hash_.update(d)
    return hash_.hexdigest()


class BaseFrontend:
    """Base class for the frontend"""

    app = None

    def update_component(self, component_id: str, data, method):
        raise NotImplementedError()

    def reset_app(self, app):
        raise NotImplementedError("Calling reset from invalid environment!")

    def get_query_parameter(self, name: str):
        """Get a query parameter from the URL"""
        raise NotImplementedError()


class BrowserFrontend(BaseFrontend):
    def update_component(self, comp, data, method):
        if method not in comp._js_callbacks:
            return

        if comp._js_component is None:
            return

        if data is None:
            data = {
                "slots": comp._get_js_slots(),
                "props": comp._get_js_props(),
                "type": comp.component,
            }

        if "source" not in data:
            data["source"] = "frontend"

        if data["source"] == "frontend" and comp._status.capture_events:
            data["debug"] = comp._get_debug_data(
                method=method,
                **data,
            )
        for func in comp._js_callbacks[method]:
            func(data)

    def reset_app(self, app):
        from webgpu.platform import link

        link.call_method_ignore_return(
            "resetApp", [app.component._get_my_wrapper_props()]
        )
        self.app = app

    def get_query_parameter(self, name: str, default=None):
        from webgpu.platform import link

        return link.get("router").currentRoute.value.query.get(name, default)

    def set_query_parameter(self, name: str, value: str):
        from webgpu.platform import link

        router = link.get("router")
        q = router.currentRoute.value.query
        q[name] = value
        router.replace({"query": q})

    @property
    def url_hash(self):
        from webgpu.platform import link

        h = link.get("router").currentRoute.value.hash or "#"
        return h[1:]

    @url_hash.setter
    def url_hash(self, value):
        from webgpu.platform import link

        return link.get("router").replace({"hash": "#" + value})


class ComputeFrontend(BaseFrontend):
    def update_component(self, comp, data, method):
        try:
            if comp._block_frontend_update:
                return

            if comp._status is None:
                return

            if comp._status.app is None:
                return

            if data is None:
                data = {
                    "data": comp.dump(),
                    "storage": comp.storage._dump_metadata(),
                }

            data["source"] = "backend"

            if comp._status.capture_events:
                data["debug"] = comp._get_debug_data(
                    method=method,
                    **data,
                )

            file_id = comp._status.app.metadata["id"]
            component_id = comp._fullid
            if component_id:
                api.post(
                    "/update_frontend",
                    data={
                        "file_id": file_id,
                        "component_id": component_id,
                        "method": method,
                        "data": data,
                    },
                )
        except Exception as e:
            print_exception(e, file=sys.stdout)


class EnvironmentType(str, Enum):
    """
    Environment type
    PYODIDE: Environment is a frontend (running with pyodide in the browser)
    COMPUTE: We are running a compute function on a separate compute node
    APP: Backend serves one app locally
    STANDALONE: Standalone mode with no frontend, used for testing
    """

    BACKEND = "Backend"
    PYODIDE = "Pyodide"
    COMPUTE = "Compute"
    LOCAL_APP = "LocalApp"
    STANDALONE = "Standalone"


class Environment:
    """Environment class to store the current environment

    Following situations are possible:

    1.) Pyodide environment
        type = EnvironmentType.PYODIDE
        have_backend = True | False

        This python instance is running in the browser in a web worker and communicates with the main thread via web worker postMessage interface.

        The backend might be:
            - No backend
            - A "full" backend with http api interface + websocket interface

    2.) Local App environment
        type = EnvironmentType.LOCAL_APP

        This python instance is running on a local machine and communicates with the frontend (also running locally) via websockets.

    3.) Compute environment
        type = EnvironmentType.COMPUTE

        This is a compute node running a compute function. It communicates with the full backend via http api interface.

    4.) Standalone environment
        type = EnvironmentType.STANDALONE


    """

    BACKEND = EnvironmentType.BACKEND
    PYODIDE = EnvironmentType.PYODIDE
    COMPUTE = EnvironmentType.COMPUTE
    LOCAL_APP = EnvironmentType.LOCAL_APP
    STANDALONE = EnvironmentType.STANDALONE

    type: EnvironmentType
    have_backend: bool = False

    frontend: BaseFrontend
    backend_api_url: str = ""
    backend_api_token: str = ""
    backend_api_client_id: str = ""

    def __init__(self, type: EnvironmentType, have_backend: bool):
        self.type = type
        self.have_backend = have_backend

        match type:
            case EnvironmentType.PYODIDE:
                self.frontend = BrowserFrontend()
            case EnvironmentType.LOCAL_APP:
                self.frontend = BrowserFrontend()
            case EnvironmentType.COMPUTE:
                self.frontend = ComputeFrontend()
            case EnvironmentType.STANDALONE:
                self.frontend = BaseFrontend()

    def set_backend(self, api_url: str, api_token: str, client_id: str = ""):
        self.backend_api_url = api_url
        self.backend_api_token = api_token
        self.backend_api_client_id = client_id

    def update_component(
        self,
        file_id: int,
        method: str,
        data: dict,
        component_id: int | None = None,
    ):
        if self.type not in [
            EnvironmentType.PYODIDE,
            EnvironmentType.LOCAL_APP,
        ]:
            raise RuntimeError(
                "update_component is only available in pyodide or local app environment"
            )
        app = self.frontend.app
        if app is None or app._status.file_id != file_id:
            return

        if component_id is None:
            app.load(data)
            return

        comp = app[component_id]

        if not data:
            return

        if method == "update_frontend":
            if "data" in data:
                comp.load(data["data"])
            if "props" in data:
                comp._props.update(data["props"])
            if "storage" in data:
                comp.storage._load_metadata(data["storage"])

        if method in comp._js_callbacks:
            for func in comp._js_callbacks[method]:
                func(data)


_environment = None


def set_environment(type: EnvironmentType, have_backend: bool = True):
    global _environment
    _environment = Environment(type, have_backend)
    if type == Environment.PYODIDE:
        import webgpu.platform
    return _environment


def get_environment() -> Environment:
    if _environment is None:
        raise RuntimeError("Environment not set")
    return _environment


def is_pyodide() -> bool:
    """Check if the code is executed in pyodide"""
    try:
        import pyodide.ffi
    except ImportError:
        return False
    return True


def is_production() -> bool:
    """Check if the code is executed in pyodide"""
    try:
        import pyodide.ffi
    except ImportError:
        return False
    return webapp_frontend.prod


def log(*args) -> None:
    """Log a message to the console"""
    if is_production():
        return
    message = " ".join(map(str, args))
    if is_pyodide():
        import webapp_frontend

        webapp_frontend.log(message)
    else:
        print("Log:", message)


def warning(*args) -> None:
    """Log a warning to the console"""
    if is_production():
        return
    message = " ".join(map(str, args))
    if is_pyodide():
        import webapp_frontend

        webapp_frontend.warning(message)
    else:
        print("Warning:", message)


def error(*args) -> None:
    """Log an message to the console"""
    message = " ".join(map(str, args))
    if is_pyodide():
        import webapp_frontend

        webapp_frontend.error(message)
        webapp_frontend.dialog({"type": "error", "message": message})
    else:
        print("Error:", message)


def confirm(title="", message="", on_ok=None, on_cancel=None):
    """Show a confirmation dialog"""
    if not is_pyodide():
        raise Exception("confirm() is only available in pyodide")

    import pyodide.ffi
    import webapp_frontend

    data = {
        "title": title,
        "message": message,
        "ok": True,
        "cancel": True,
    }

    if on_ok is not None:
        data["onOk"] = pyodide.ffi.create_once_callable(lambda: on_ok())
    if on_cancel is not None:
        data["onwCancel"] = pyodide.ffi.create_once_callable(
            lambda: on_cancel()
        )

    webapp_frontend.dialog(data)


def read_json(filename: str | Path) -> dict:
    """Read a file from the filesystem"""
    return orjson.loads(Path(filename).read_bytes())


def write_json(data: dict, filename: str | Path) -> None:
    """Write a file from the filesystem"""
    Path(filename).write_bytes(orjson.dumps(data))


def read_file(filename: str | Path) -> str:
    """Read a file from the filesystem"""
    with open(filename, "r", encoding="utf-8") as file:
        return file.read()


def read_file_binary(filename: str | Path) -> bytes:
    """Read a binary file from the filesystem"""
    with open(filename, "rb") as file:
        return file.read()


def write_file(
    filename: str | Path, data: str | bytes, binary: bool = False
) -> int:
    """Write a file to the filesystem"""
    with open(
        filename, "wb" if binary else "w", encoding=None if binary else "utf-8"
    ) as file:
        return file.write(data)


def time_now() -> float:
    """Return the current time as a timestamp"""
    return datetime.datetime.now().timestamp()


def load_image(filename: Path | str) -> str:
    filename = Path(filename)
    """Load an image from the filesystem and return it as a base64 encoded string"""
    with open(filename, "rb") as file:
        pic_enc = base64.b64encode(file.read()).decode("ascii")

    file_format = filename.suffix[1:].lower()
    if file_format == "svg":
        file_format = "svg+xml"

    return f"data:image/{file_format};base64," + pic_enc


@contextmanager
def set_directory(path: str):
    """Context manager to change the current working directory"""
    origin = Path().absolute()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(origin)


def zip_directory(path: str, ignore: str = "*backend*") -> bytes:
    """Zip a directory and return the zip file as a bytes object"""
    root = os.path.dirname(path)
    base_dir = os.path.basename(path)
    with tempfile.TemporaryDirectory() as temp_dir:
        shutil.copytree(
            path,
            os.path.join(temp_dir, base_dir),
            ignore=shutil.ignore_patterns(ignore),
        )
        temp = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
        shutil.make_archive(temp.name[:-4], "zip", temp_dir, base_dir)
        data = read_file_binary(temp.name)
        os.remove(temp.name)
        return data


def zip_modules(modules) -> bytes:
    """Zip a list of python modules and return the zip file as a bytes object"""
    with tempfile.TemporaryDirectory() as root:
        for module_name in modules:
            spec = importlib.util.find_spec(module_name)
            if spec is None:
                raise ModuleNotFoundError(f"Module {module_name} not found")
            for path in spec.submodule_search_locations:
                shutil.copytree(
                    path,
                    os.path.join(root, os.path.basename(path)),
                    ignore=shutil.ignore_patterns("*backend*", "*__pycache__*"),
                )
        with tempfile.NamedTemporaryFile(suffix=".zip") as temp:
            pass
        with ZipFile(temp.name, mode="w") as zipfile:
            for dirname, _, files in os.walk(root):
                for file in files:
                    fn = Path(dirname, file)
                    afn = fn.relative_to(root)
                    zipfile.write(fn.absolute(), arcname=afn)
        data = read_file_binary(temp.name)
        os.remove(temp.name)
        return data


@contextmanager
def temp_dir_with_files(
    data: dict[str, bytes], extract_zip: bool = False, return_list=True
) -> list[Path] | Path:
    """Context manager to handle files stored in a dictionary

    :param data: The dictionary containing the file names and data
    :param extract_zip: Whether to extract zip files
    :param return_list: Whether to return a single file as list, or the file directly
    :yields: A list containing the file paths objects
    """

    def handle_zip(data: bytes, tmp_path: Path, files: list[Path]):

        byte_stream = io.BytesIO(data)
        with ZipFile(byte_stream, "r") as zip_ref:
            zip_ref.extractall(tmp_path)
            extracted_file_names = zip_ref.namelist()
            for extracted_file_name in extracted_file_names:
                files.append(tmp_path / extracted_file_name)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        file_paths = []
        for filename, file_data in data.items():
            if filename.endswith(".zip") and extract_zip:
                handle_zip(file_data, tmpdir, file_paths)
            else:
                file_path = tmpdir / filename
                with open(file_path, "wb") as file:
                    file.write(file_data)
                file_paths.append(file_path)
        if len(file_paths) == 1 and return_list is False:
            file_paths = file_paths[0]
        yield file_paths


class Job(pydantic.BaseModel):
    id: int

    def abort(self):
        api.post(f"/job/cancel/{self.id}", {})

    def get_status(self) -> dict:
        return api.get(f"/job/status/{self.id}")


_job_component = None


def get_job_component():
    """Get the current job component of the running job"""
    global _job_component
    return _job_component


__DEFAULT_DOCKERFILE__ = """
FROM python:3.12
RUN python3 -m venv /venv
ENV PATH="/venv/bin:$PATH"
RUN pip3 install watchdog websockets wheel pydantic==2.* urllib3 certifi pint colorama fore
ADD wheels /webapp_wheels
RUN pip3 install /webapp_wheels/*.whl
RUN unzip /webapp_wheels/ngapp.zip -d /venv/lib/python3.12/site-packages/
"""

__PDF_DOCKERFILE__ = """
FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt update && apt-get -y upgrade
RUN apt install -y python3 python3-pip python3-venv pandoc texlive texlive-xetex texlive-latex-base texlive-latex-extra
RUN python3 -m venv /opt/venv
RUN . /opt/venv/bin/activate && \
pip install --upgrade pip && \
pip install playwright && \
playwright install-deps chromium && \
playwright install chromium && \
pip install docxtpl && \
pip install jinja2\n
ENV PATH="/opt/venv/bin:$PATH"
"""


class ComputeEnvironment(pydantic.BaseModel):
    """Defines the maximal resource usage and type of compute environments on the backend"""

    model_config = pydantic.ConfigDict(extra="forbid")

    name: str = "default"
    cpus: int = 1
    memory: str = "1G"
    env_type: typing.Literal["venv", "docker", "local"] = "venv"
    dockerfile: str = __DEFAULT_DOCKERFILE__

    def __call__(self, *args, **kwargs):
        return compute_node(*args, **kwargs, compute_env=self)


pdf_compute_env = ComputeEnvironment(
    name="_internal_pdf",
    cpus=1,
    memory="1G",
    env_type="docker",
    dockerfile=__PDF_DOCKERFILE__,
)

webgui_compute_env = pdf_compute_env


def compute_node(
    _func=None, *, compute_env: str | ComputeEnvironment = "default"
):
    from .app import App
    from .components.basecomponent import Component

    if isinstance(compute_env, ComputeEnvironment):
        compute_env = compute_env.name

    def decorator(f):
        try:
            environment = get_environment()
        except RuntimeError:
            return f
        match environment.type:
            case Environment.STANDALONE:
                return f

            case Environment.LOCAL_APP:
                return f

            case Environment.PYODIDE:

                @functools.wraps(f)
                def wrapper(
                    self: App | Component,
                    _job_component=None,
                    depends_on: list[str | int | Job] | None = None,
                    *args,
                    **kwargs,
                ):
                    app = self._status.app
                    comp_id = None
                    kwargs["job_component_id"] = (
                        _job_component._fullid if _job_component else ""
                    )
                    if issubclass(type(self), Component):
                        # compute node called from component function
                        comp_id = self._fullid
                        if comp_id is None:
                            raise RuntimeError(
                                f"Component needs `id` set to use compute node."
                            )
                    app.save()

                    if depends_on:
                        for i, job in enumerate(depends_on):
                            if isinstance(job, Job):
                                job = job.id
                            depends_on[i] = str(job)

                    # TODO: self.lock() # lock the object to prevent changes during the computation
                    job = Job.model_validate(
                        api.post(
                            "/job",
                            {
                                "file_id": app.metadata["id"],
                                "compute_env": compute_env,
                                "comp_id": comp_id,
                                "func": f.__name__,
                                "status": {
                                    "capture_events": app._status.capture_events,
                                    "capture_call_stack": app._status.capture_call_stack,
                                },
                                "depends_on": depends_on,
                                "args": args,
                                "kwargs": kwargs,
                            },
                        )
                    )
                    return job

                return wrapper

            case Environment.COMPUTE:

                @functools.wraps(f)
                def wrap(
                    self: App | Component,
                    job_id: int,
                    job_component_id: str = "",
                    *args,
                    **kwargs,
                ):
                    global _job_component

                    app = self._status.app
                    _job_component = (
                        app[job_component_id] if job_component_id else None
                    )
                    if _job_component:
                        _job_component.set_job_from_id(job_id=job_id)
                        _job_component.update_job_status()
                        app.save()

                    ret = f(self, *args, **kwargs)

                    # workaound the issue https://github.com/rq/rq/issues/1631,
                    # once fixed use update_job_status in on_succes callback
                    if _job_component:
                        _job_component._reset_button()

                    return ret

                # mark this function as a compute node function (for security checks on the server side)
                wrap.__is_compute_node_function = True
                wrap.__compute_env = compute_env
                return wrap

    # support both @compute_node and @compute_node()
    if _func is None:
        return decorator
    else:
        return decorator(_func)


def new_simulation():
    """Create a new simulation"""
    import webapp_frontend

    webapp_frontend.set_file_id()


def load_simulation(file_id: str):
    """Load a simulation from file id"""
    env = get_environment()
    env.frontend.set_query_parameter("fileId", file_id)


def copy_simulation(data: dict):
    """Create a new simulation and copy the data"""
    import webapp_frontend

    webapp_frontend.copy_simulation(data)


def print_exception(ex, file=sys.stderr):
    """Prints the exception and the traceback in red"""
    try:
        if is_pyodide():
            print(f"ERROR:  {ex}")
        else:
            from colorama import Fore

            print(Fore.RED + f"ERROR:  {ex}")
        if not isinstance(ex, str):
            traceback.print_exception(*sys.exc_info(), file=file)
    finally:
        if not is_pyodide():
            print(Fore.RESET)


def _get_app_assets(app_name: str):
    app_path = Path(import_module(app_name).__file__).parent
    for file in app_path.rglob("assets/*"):
        with open(file, "rb") as f:
            yield file.name, f.read()
