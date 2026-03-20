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
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from typing import final

import pydantic
import urllib3

from . import api, utils
from .components.basecomponent import (
    AppStatus,
    Component,
    FileData,
    Storage,
    _QProxy,
    reset_components,
)
from .components.helper_components import Div
from .utils import (
    ComputeEnvironment,
    EnvironmentType,
    UserSettings,
    call_js,
    get_environment,
    is_pyodide,
    read_file,
    read_file_binary,
    read_json,
    replace_app,
    save_file_local,
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
        binary = filename.suffix in [
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".svg",
            ".webp",
        ]

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

    id: int = -1
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
            python_class._config = self
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


class AppConfigWithAccess(AppConfig):
    access_level: AccessLevel = AccessLevel.HIDDEN

    @property
    def is_admin(self) -> bool:
        return self.access_level == AccessLevel.ADMIN


class App(Div):
    """Base class for all applications"""

    _default_data: dict | None
    _status: AppStatus
    _usersettings: UserSettings | None = None

    _config: AppConfigWithAccess
    file_data: FileData

    def __init__(
        self, *ui_children: Component | str, name: str | None = None, **kwargs
    ):
        self._status = AppStatus(app=self, environment=get_environment())
        super().__init__(id="__app__", *ui_children, **kwargs)

        self.file_data = FileData(
            name=name or "",
            app_id=self._config.id,
        )
        self._default_data = None
        self._on_exit_handlers = []
        self._usersettings: UserSettings | None = None
        self.storage = Storage(self)

        self._namespace_id = ""
        self._parent = None
        self._status.components_by_id[self._id] = self
        if not self._id:
            return None
        if ui_children:
            self._recurse(Component._calc_namespace_id, True, set())

        env = get_environment()
        if isinstance(env.frontend, utils.BrowserFrontend):
            def initialize_quasar_proxy():
                self.js.eval(
                    """
    document.get_quasar_obj = (name) =>
                { return document.querySelector('#q-app').__vue_app__.config.globalProperties.$q[name] }
    """
                )

            self.on_mounted(initialize_quasar_proxy)

    @property
    def component(self) -> Component:
        return self.ui_children[0]

    @component.setter
    def component(self, value: Component):
        self.ui_children = [value]

    def __getitem__(self, key: str) -> Component:
        return self._status.components_by_id[key]

    def on_exit(self, handler):
        """
        Register a handler to be called when the app is exited.
        This is useful for cleanup tasks or saving state.
        """
        self._on_exit_handlers.append(handler)

    @property
    def usersettings(self) -> UserSettings:
        """Per-user, per-app persistent settings.

        Settings are backed by ``config.json`` in a per-app subfolder
        of the user-wide ngapp configuration directory and keyed by
        simple strings, e.g. "nthreads".
        """

        if self._usersettings is None:
            # Use a stable identifier for the app; fall back to the
            # fully qualified class name if no name is set.
            app_id = self._config.name or (
                self.__class__.__module__ + "." + self.__class__.__name__
            )
            self._usersettings = UserSettings(app_id=app_id)
        return self._usersettings

    @property
    def assets_path(self) -> Path:
        """Get the path to the assets directory in the python package of the app"""
        return (
            Path(sys.modules[self.__module__.split(".")[0]].__file__).parent
            / "assets"
        )

    @property
    def metadata(self):
        return {} | self.file_data.__dict__

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
        if self.env.type == EnvironmentType.LOCAL_APP:
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
        return self.file_data.name

    @name.setter
    def name(self, value):
        self.file_data.name = value

    def upgrade(self, data):
        """Upgrade data to the current version"""
        return data

    def _dump_app(
        self,
        exclude_default_data=False,
        keep_storage=False,
        include_storage_data=False,
    ):
        """Get input data for storage"""
        if (
            not include_storage_data
            and keep_storage
            and not self.env.have_backend
        ):
            self._save_storage_local()
        exclude_default = (
            self._default_data["data"] if exclude_default_data else None
        )
        component_data = {
            "data": self._dump_recursive(exclude_default),
            "storage": self._dump_storage(include_storage_data),
        }

        storage = self.storage._dump(include_storage_data)

        return {
            "component": component_data,
            "metadata": {} | self.file_data.__dict__,
            "storage": storage,
        }

    @property
    def env(self):
        return self._status.environment

    @final
    @classmethod
    def load(cls, path: str):
        get_environment().load(cls, path)

    @final
    @classmethod
    def load_local(cls):
        env = get_environment()
        data = env.load_data_local()
        app = cls()
        app._load_app(data)
        env.reset_app(app)

    @final
    def save_as(self, name: str):
        self.env.save_as(self, name)

    @final
    @classmethod
    def delete(cls, path):
        get_environment().delete(path)

    @final
    def save(self):
        if self.env.have_backend:
            self.save_backend()
        else:
            self.save_local()

    @final
    def save_backend(self):
        """Save data to backend"""
        env = self.env
        if not env.have_backend:
            raise RuntimeError("No backend available")

        env.frontend.app = self
        self.component._emit_recursive("before_save")
        status = self._status
        file_id = status.file_id
        if file_id is None:
            self.file_data = FileData(
                **api.post(
                    "/create_model",
                    {
                        "app_id": self._status.app_id,
                        "name": self.name or "untitled",
                    },
                )
            )

        api.put(f"/model/{status.file_id}", self._dump_app())
        self.component._emit_recursive("save")
        self.storage.save()

        if env.type == EnvironmentType.PYODIDE:
            env.frontend.set_query_parameter("fileId", status.file_id)

    @final
    @classmethod
    def reset(cls):
        """
        Reset the app in the user interface to clean initial state. Only available in frontend and local environment. Return value is the new app instance.
        """
        app = cls()
        app._load_app({})
        get_environment().reset_app(app)
        return app

    @final
    def save_local(self):
        import pickle

        self._emit_recursive("before_save")
        dump = self._dump_app(include_storage_data=True)
        name = self.name + ".sav" if self.name is not None else "untitled.sav"
        data = pickle.dumps(dump)
        self.env.save_file_local(data, name)

    @final
    def quit(self):
        self.js.close()
        os._exit(0)

    def update(
        self, data: dict, load_local_storage=False, update_frontend=False
    ):
        """Update app with new data"""
        metadata = data.get("metadata", None)
        component_data = data.get(
            "component", data.get("data", {}).get("component", {})
        )

        self.storage._load_data(data.get("storage", None))

        if metadata:
            self.file_data.app_id = metadata.get("app_id", None)
            self.file_data.id = metadata.get("id", None)

        self._emit_recursive("before_load")

        if "storage" in component_data:
            self._load_storage(component_data["storage"])

        if load_local_storage:
            self._load_storage_local()

        if "data" in component_data:
            self._load_recursive(
                component_data["data"], update_frontend=update_frontend
            )

        def block_frontend_update(comp):
            comp._block_frontend_update = True

        self._recurse(block_frontend_update, True, set())
        self._emit_recursive("load")

        def unblock_frontend_update(comp):
            comp._block_frontend_update = False
            if comp._namespace_id is None:
                comp._calc_namespace_id()

        self._recurse(unblock_frontend_update, True, set())

    def _load_app(
        self,
        data,
        load_local_storage=False,
        update_frontend=None,
    ):
        """Load app from stored data"""

        self._namespace_id = ""
        self._parent = self
        self._status = self._status
        self._namespace_id = ""

        if update_frontend is None:
            update_frontend = self.env.type in [
                EnvironmentType.PYODIDE,
                EnvironmentType.LOCAL_APP,
            ]

        self._recurse(Component._calc_namespace_id, True, set())

        component_data = data.get("component", {})
        metadata = data.get("metadata", {})
        self.file_data.__dict__.update(metadata)

        if self._default_data and "data" in component_data:
            # we are hot-reloading the app, this means we skipped the default data when dumping before
            # so we need to update the data with the default data
            def update_props(data, default_data):
                for key, default_value in default_data.items():
                    if not key in data:
                        data[key] = copy.deepcopy(default_value)
                        continue
                    if isinstance(default_value, dict):
                        update_props(data[key], default_value)

            update_props(component_data["data"], self._default_data["data"])

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
                headers={"Authorization": f"{os.environ['WEBAPP_API_TOKEN']}"},
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

    def testing_data(self):
        """
        Get data for testing purposes. User should implement this method in the app class.
        Returns:
            dict: Dictionary with filename, data and type keys
        """
        app_data = self._dump_app()
        app_data["component"].pop("storage", None)
        return {
            "filename": f"{self.name}.json",
            "data": json.dumps(app_data),
            "type": "application/json",
        }


BaseModel = App

_app_cache = {}


def _get_app_config(
    app_config: int | dict | AppConfigWithAccess,
) -> AppConfigWithAccess:
    if isinstance(app_config, AppConfig):
        return AppConfigWithAccess(**app_config.model_dump())

    if isinstance(app_config, AppConfigWithAccess):
        return app_config

    if isinstance(app_config, int):
        if app_config in _app_cache:
            return _app_cache[app_config]
        app_config = api.get(f"/get_app/{app_config}")

    if isinstance(app_config, dict):
        if "app_id" in app_config and app_config["app_id"] in _app_cache:
            return _app_cache[app_config["app_id"]]

        # Ignore extra fields by filtering only those accepted by AppConfig
        allowed_fields = set(AppConfigWithAccess.model_fields)
        filtered_config = {
            k: v for k, v in app_config.items() if k in allowed_fields
        }
        app_config = AppConfigWithAccess(**filtered_config)
        _app_cache[app_config.id] = app_config
        return app_config
    raise ValueError(f"Unsupported app_config type: {type(app_config)}")


def reload_package(package_name):
    """Reload python package and all submodules (searches in modules for references to other submodules)"""
    _app_cache.clear()
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
            print(f"Reloaded module {module.__name__} in {1000 * t:.0f} ms")

        var_values = vars(module).values()
        for var in list(var_values):
            if isinstance(var, types.ModuleType):
                file_name = getattr(var, "__file__", None)
                if file_name is not None and file_name.startswith(package_dir):
                    if file_name not in reloaded_modules:
                        reloaded_modules[file_name] = reload_recursive(var)

        return module

    reload_recursive(package)
    return reloaded_modules


def create_app(
    app_config: AppConfig | int | dict,
    data,
    reload_python_modules=[],
    load_local_storage=False,
    app_args={},
):
    """Load model from data"""
    utils._print_counts()
    utils._reset_counts()

    app_config = _get_app_config(app_config)

    reloaded_modules = {}
    for m in reload_python_modules:
        # hot reloading of python module on client side
        t = time.time()
        reloaded_modules |= reload_package(m)
        t = time.time() - t
        print(f"Reloaded package {m} in {1000 * t:.0f} ms")

    module_name = app_config.python_class.split(".")
    module_name, class_name = ".".join(module_name[:-1]), module_name[-1]
    if module_name in reloaded_modules:
        module = reloaded_modules[module_name]
    else:
        module = importlib.import_module(module_name)
    cls = getattr(module, class_name)
    cls._config = app_config
    reset_components()
    app = cls(**app_args)
    app._default_data = copy.deepcopy(app._dump_app()["component"])
    app._load_app(data=data, load_local_storage=load_local_storage)
    utils._print_counts()
    utils._reset_counts()
    return app


_app_register = []


def register_application(app):
    """Class decorator to register an application"""
    _app_register.append(app)
    return app
