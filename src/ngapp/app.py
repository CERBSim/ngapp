# pylint: disable=invalid-name
"""Base class for all applications"""

import base64
import copy
import hashlib
import importlib.util
import json
import os
import os.path
import subprocess
import sys
import tempfile
import time
import types
from contextlib import contextmanager
from enum import IntEnum
from pathlib import Path

import pydantic
import urllib3

from . import api, utils
from .components.basecomponent import AppStatus, Component, reset_components
from .utils import (
    ComputeEnvironment,
    EnvironmentType,
    get_environment,
    is_pyodide,
    read_file,
    read_file_binary,
    read_json,
)


def asset(filename: Path | str, binary: bool | None = None, module=None) -> str:
    """Load an asset from the 'assets' directory within an application"""
    import inspect

    filename = Path(filename)
    file_format = filename.suffix[1:].lower()
    if file_format == "svg":
        file_format = "svg+xml"
    if module:
        calling_file = Path(inspect.getfile(module))
    else:
        calling_file = Path(inspect.stack()[1].filename)
    filename = calling_file.parent / "assets" / filename

    if not filename.exists():
        raise FileNotFoundError(f"Asset file {filename} not found.")

    if binary is None:
        binary = filename.suffix in [".png", ".jpg", ".jpeg", ".gif", ".svg"]

    if binary:
        data = base64.b64encode(read_file_binary(filename)).decode("ascii")
    else:
        data = read_file(filename)

    if file_format in ["png", "jpg", "jpeg", "gif", "svg+xml"]:
        data = f"data:image/{file_format};base64,{data}"

    return data


class AccessLevel(IntEnum):
    """Access levels enum to distinguish acess rights (HIDDEN, ADMIN, etc.)"""

    HIDDEN = 0
    VISIBLE = 5
    TRIAL = 10
    STANDARD = 20
    ADMIN = 9000


class AccessLevelConfig(pydantic.BaseModel):
    """Defines the restrictions of access to an Application for a certain access level"""

    model_config = pydantic.ConfigDict(extra="forbid")

    name: str
    access_level: AccessLevel = AccessLevel.HIDDEN
    max_cpus: int = 0
    max_memory: str = "0G"
    max_saved_results: int = 0


class AppAccessConfig(pydantic.BaseModel):
    """Defines the restrictions of access to an Application for a certain access level"""

    model_config = pydantic.ConfigDict(extra="forbid")

    default_level: AccessLevel = AccessLevel.STANDARD
    enable_trial: bool = False
    auto_grant_trial: bool = False
    trial_days: int = 21
    levels: dict[AccessLevel, AccessLevelConfig] = {
        AccessLevel.HIDDEN: AccessLevelConfig(
            access_level=AccessLevel.HIDDEN,
            name="hidden",
        ),
        AccessLevel.VISIBLE: AccessLevelConfig(
            access_level=AccessLevel.VISIBLE,
            name="visible",
        ),
        AccessLevel.TRIAL: AccessLevelConfig(
            access_level=AccessLevel.TRIAL,
            name="trial",
            max_memory="14G",
            max_cpus=4,
            max_saved_results=20,
        ),
        AccessLevel.STANDARD: AccessLevelConfig(
            access_level=AccessLevel.STANDARD,
            name="standard",
            max_memory="14G",
            max_cpus=4,
            max_saved_results=20,
        ),
        AccessLevel.ADMIN: AccessLevelConfig(
            access_level=AccessLevel.ADMIN,
            name="admin",
            max_memory="60G",
            max_cpus=20,
            max_saved_results=999,
        ),
    }


class PythonPackage(pydantic.BaseModel):
    """Python package model"""

    file_name: str
    package: bytes | None

    model_config = pydantic.ConfigDict(ser_json_bytes="base64")


class AppConfig(pydantic.BaseModel):
    """App configuration class, contains all metadata about an app"""

    model_config = pydantic.ConfigDict(extra="forbid")

    name: str
    version: str

    python_class: str
    frontend_pip_dependencies: list[str] = []
    frontend_dependencies: list[str] = []

    description: str = "No description."
    image: str | None = None
    logo: dict = {}

    compute_environments: list[ComputeEnvironment] = []
    access: AppAccessConfig = AppAccessConfig()

    frontend_package: bytes = b""
    python_packages: list[PythonPackage] = []
    python_packages_hash: str = ""

    def __init__(self, python_class, **kwargs):
        if not isinstance(python_class, str):
            python_class = python_class.__module__ + "." + python_class.__name__
        super().__init__(python_class=python_class, **kwargs)

    @property
    def python_package_name(self):
        return self.python_class.split(".")[0]

    def create_frontend_package(self):
        self.frontend_package = utils.zip_modules(
            [self.python_package_name] + self.frontend_dependencies
        )

    def create_backend_packages(self, include_dependencies=True):
        if len(self.compute_environments) == 0:
            return

        origin = Path(importlib.util.find_spec(self.python_package_name).origin)
        src_dir = None
        for _ in range(3):
            origin = origin.parent
            for filename in ["pyproject.toml", "setup.py"]:
                if (origin / filename).exists():
                    src_dir = origin
                    break
        if src_dir is None:
            raise RuntimeError(
                f"Could not find source directory for package {self.python_package_name}"
            )

        with tempfile.TemporaryDirectory() as temp_dir_:
            temp_dir = Path(temp_dir_)
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "build",
                    "-n",
                    "-w",
                    "-o",
                    temp_dir,
                    src_dir,
                ],
                check=True,
            )

            package_hash = hashlib.sha256()
            packages = []

            dirs = [temp_dir]
            if include_dependencies:
                dirs.append(src_dir / "dependencies")

            for d in dirs:
                if not d.exists():
                    continue
                for filename in sorted(os.listdir(d)):
                    if filename.endswith(".whl"):
                        data = (d / filename).read_bytes()
                        package_hash.update(data)
                        packages.append(
                            PythonPackage(
                                file_name=filename,
                                package=data,
                            )
                        )
            self.python_packages = packages
            self.python_packages_hash = package_hash.hexdigest()


class App:
    """Base class for all applications"""

    component: Component
    metadata: dict
    _default_data: dict | None
    _status: AppStatus

    def __init__(self, component: Component | None = None, name=None):
        self.metadata = {"name": name}
        self._default_data = None
        self._status = AppStatus()
        self._status.app = self

        if component is not None:
            self.component = component
            component._namespace_id = ""
            component._parent = self
            component._status = self._status
            component._recurse(Component._calc_namespace_id, True, set())

    def __getitem__(self, key: str) -> Component:
        return self._status.components_by_id[key]

    @property
    def assets_path(self) -> Path:
        """Get the path to the assets directory in the python package of the app"""
        return (
            Path(sys.modules[self.__module__.split(".")[0]].__file__).parent
            / "assets"
        )

    def set_colors(
        self,
        primary: str | None = None,
        secondary: str | None = None,
        accent: str | None = None,
        dark: str | None = None,
        positive: str | None = None,
        negative: str | None = None,
        info: str | None = None,
        warning: str | None = None,
    ):
        """Set the colors of the app"""
        if get_environment().type == EnvironmentType.LOCAL_APP:
            from webgpu.platform import execute_when_init

            def f(js):
                if primary is not None:
                    js.document.body.style.setProperty("--q-primary", primary)
                if secondary is not None:
                    js.document.body.style.setProperty(
                        "--q-secondary", secondary
                    )
                if accent is not None:
                    js.document.body.style.setProperty("--q-accent", accent)
                if dark is not None:
                    js.document.body.style.setProperty("--q-dark", dark)
                if positive is not None:
                    js.document.body.style.setProperty("--q-positive", positive)
                if negative is not None:
                    js.document.body.style.setProperty("--q-negative", negative)
                if info is not None:
                    js.document.body.style.setProperty("--q-info", info)
                if warning is not None:
                    js.document.body.style.setProperty("--q-warning", warning)

            execute_when_init(f)

    @property
    def name(self):
        return self.metadata.get("name", "Untitled")

    @name.setter
    def name(self, value):
        self.metadata["name"] = value

    def upgrade(self, data):
        """Upgrade data to the current version"""
        return data

    def dump(
        self,
        exclude_default_data=False,
        keep_storage=False,
        include_storage_data=False,
    ):
        """Get input data for storage"""
        if self.component is None:
            return {}
        if (
            not include_storage_data
            and keep_storage
            and not get_environment().have_backend
        ):
            self._save_storage_local()
        component_data = {
            "data": self.component._dump_recursive(),
            "storage": self.component._dump_storage(include_storage_data),
        }

        if exclude_default_data:

            def remove_default_data(data, default_data):
                if isinstance(data, dict):
                    for key in list(data.keys()):
                        if key not in default_data:
                            return
                        if isinstance(data[key], dict) and isinstance(
                            default_data[key], dict
                        ):
                            if data[key] == default_data[key]:
                                del data[key]
                            else:
                                remove_default_data(
                                    data[key], default_data[key]
                                )

            remove_default_data(
                component_data["data"], self._default_data["data"]
            )
            remove_default_data(
                component_data["storage"], self._default_data["storage"]
            )

        return {"component": component_data, "metadata": self.metadata}

    def save(self):
        """Save data to backend"""
        env = get_environment()
        if not env.have_backend:
            return

        self.component._emit_recursive("before_save")
        status = self._status
        file_id = status.file_id
        if file_id is None:
            metadata = api.post(
                "/create_model",
                {
                    "app_id": self.metadata["app_id"],
                    "name": self.name or "Untitled",
                },
            )
            self.metadata |= metadata
            status.file_id = metadata["id"]

        api.put(f"/model/{status.file_id}", self.dump())
        self.component._emit_recursive("save")

        if env.type == EnvironmentType.PYODIDE:
            env.frontend.set_query_parameter("fileId", status.file_id)

    @classmethod
    def reset(cls):
        """
        Reset the app in the user interface to clean initial state. Only available in frontend and local environment. Return value is the new app instance.
        """
        app = cls()
        get_environment().frontend.reset_app(app)
        return app

    def save_local(self):
        from webgpu import platform

        dump = self.dump(include_storage_data=True)
        name = self.name + ".sav" if self.name is not None else "untitled.sav"
        options = {"suggestedName": name}
        import pickle

        pick = platform.js.showSaveFilePicker(options)
        stream = pick.createWritable()
        stream.write(pickle.dumps(dump))
        stream.close()

    def load_local(self):
        from webgpu import platform

        options = {"multiple": False, "accept": ".sav"}
        pick = platform.js.showOpenFilePicker(options)
        import pickle

        data = pickle.loads(pick[0].getFile().arrayBuffer())
        self.load(data)

    def update(
        self, data: dict, load_local_storage=False, update_frontend=False
    ):
        """Update app with new data"""
        metadata = data.get("metadata", None)
        component_data = data.get(
            "component", data.get("data", {}).get("component", {})
        )

        if metadata:
            self.metadata.update(metadata)
            self._status.app_id = metadata.get("app_id", None)
            self._status.file_id = metadata.get("id", None)

        if "storage" in component_data:
            self.component._load_storage(component_data["storage"])

        if load_local_storage:
            self.component._load_storage_local()

        if "data" in component_data:
            self.component._load_recursive(
                component_data["data"], update_frontend=update_frontend
            )

        def block_frontend_update(comp):
            comp._block_frontend_update = True

        self.component._recurse(block_frontend_update, True, set())
        self.component._emit_recursive("load")

        def unblock_frontend_update(comp):
            comp._block_frontend_update = False

        self.component._recurse(unblock_frontend_update, True, set())
        if is_pyodide() and update_frontend:
            import webapp_frontend

            webapp_frontend.reload(
                webapp_frontend.to_js(self.component._get_my_wrapper_props())
            )

    def load(
        self,
        data,
        load_local_storage=False,
        update_frontend=None,
    ):
        """Load app from stored data"""
        self.component._namespace_id = ""
        self.component._parent = self
        self.component._status = self._status
        self._namespace_id = ""

        if update_frontend is None:
            update_frontend = get_environment().type in [
                EnvironmentType.PYODIDE,
                EnvironmentType.LOCAL_APP,
            ]

        self.component._recurse(Component._calc_namespace_id, True, set())

        component_data = data.get("component", {})

        if self._default_data and "data" in component_data:
            # we are hot-reloading the app, this means we skipped the default data when dumping before
            # so we need to update the data with the default data
            def update_props(data, default_data):
                for key, value in default_data.items():
                    if not key in data:
                        data[key] = copy.deepcopy(value)
                        continue
                    if isinstance(value, dict):
                        update_props(value, default_data[key])
                    data[key] = copy.deepcopy(value)

        self.update(
            data,
            load_local_storage=load_local_storage,
            update_frontend=update_frontend,
        )

    def report_context(self) -> tuple[dict, dict]:
        """
        Returns the context and images for the report (docx, md).
        """
        return ({}, {})

    def load_asset(self, filename: str) -> str:
        """
        Load an asset from the 'assets' directory within an application.
        If the asset is an image, it will be returned as a data url.
        """
        module = sys.modules[self.__module__.split(".")[0]]
        return asset(filename, module=module)

    def _get_file_url(self, name: str):
        if "WEBAPP_JOB_ID" in os.environ:
            id_ = int(os.environ["WEBAPP_JOB_ID"])
        else:
            id_ = self.metadata["id"]
        url = "results" if isinstance(self, Report) else "files"
        return os.environ["WEBAPP_API_URL"] + f"/{url}/{id_}/files/{name}"

    def _load_data_file(self, name):
        if is_pyodide():
            http = urllib3.PoolManager()
            response = http.request(
                "GET",
                self._get_file_url(name),
                headers={"Authorization": f'{os.environ["WEBAPP_API_TOKEN"]}'},
            )
            return response.json()
        return read_json(f"_data_files/{name}")

    def _store_data_file(self, data, name):
        # if is_pyodide():
        if True:
            id_ = self.metadata["id"]
            api.post(
                f"/files/{id_}/files/{name}",
                data,
            )
        # else:
        #     os.makedirs("_data_files", exist_ok=True)
        #     import json
        #     write_json(json.dumps(data), f"_data_files/{name}")

    def _save_storage_local(self):
        self.component._save_storage_local()

    def _load_storage_local(self):
        self.component._load_storage_local()

    def testing_data(self):
        """
        Get data for testing purposes. User should implement this method in the app class.
        Returns:
            dict: Dictionary with filename, data and type keys
        """
        app_data = self.dump()
        app_data["component"].pop("storage", None)
        return {
            "filename": f"{self.name}.json",
            "data": json.dumps(app_data),
            "type": "application/json",
        }


BaseModel = App


def replace_app(new_app):
    env = get_environment()
    env.frontend.reset_app(new_app)


def reload_package(package_name):
    """Reload python package and all submodules (searches in modules for references to other submodules)"""
    package = importlib.import_module(package_name)
    assert hasattr(package, "__package__")
    file_name = package.__file__
    if file_name is None:
        file_name = package.__path__[0]
    package_dir = os.path.dirname(file_name) + os.sep
    reloaded_modules = {file_name: package}

    def reload_recursive(module):
        t = time.time()
        module = importlib.reload(module)
        t = time.time() - t

        if t > 0.1:
            print(f"Reloaded module {module.__name__} in {1000*t:.0f} ms")

        var_values = vars(module).values()
        for var in var_values:
            if isinstance(var, types.ModuleType):
                file_name = getattr(var, "__file__", None)
                if file_name is not None and file_name.startswith(package_dir):
                    if file_name not in reloaded_modules:
                        reloaded_modules[file_name] = reload_recursive(var)

        return module

    reload_recursive(package)
    return reloaded_modules


def loadModel(
    app_metadata, data, reload_python_modules=[], load_local_storage=False
):
    """Load model from data"""

    reloaded_modules = {}
    for m in reload_python_modules:
        # hot reloading of python module on client side
        t = time.time()
        reloaded_modules |= reload_package(m)
        t = time.time() - t
        print(f"Reloaded package {m} in {1000*t:.0f} ms")

    module_name = app_metadata["python_class"].split(".")
    module_name, class_name = ".".join(module_name[:-1]), module_name[-1]
    if module_name in reloaded_modules:
        module = reloaded_modules[module_name]
    else:
        module = importlib.import_module(module_name)
    cls = getattr(module, class_name)
    reset_components()
    app = cls()
    app._default_data = app.dump()["component"]
    if not "metadata" in data:
        data["metadata"] = {
            "app_id": app_metadata["id"],
            "python_class": app_metadata["python_class"],
        }
    app.load(data=data, load_local_storage=load_local_storage)
    return app


_app_register = []


def register_application(app):
    """Class decorator to register an application"""
    _app_register.append(app)
    return app
