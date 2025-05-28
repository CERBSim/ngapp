"""command line interface for webapp to update a running job"""

import argparse
import base64
import datetime
import importlib
import importlib.util
import os
import sys
import time

import pydantic
import watchdog.events
from watchdog.observers import Observer

from .. import api
from ..app import AppConfig
from ..utils import EnvironmentType, calc_hash, print_exception, set_environment


class WatchSpec(pydantic.BaseModel):
    app_id: int
    config_module: str
    build_backend_packages: bool
    local_compute_env: bool
    reload_config: bool = True
    python_module: str
    config: AppConfig | None = None

    def update_config(self):
        if self.reload_config or self.config is None:
            module = importlib.import_module(self.config_module)
            module = importlib.reload(module)
            self.config = module.config
            if self.local_compute_env:
                for env in self.config.compute_environments:
                    env.env_type = "local"

        return self.config


def get_args_parser(description):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("backend_url", help="URL of the backend", type=str)
    parser.add_argument("token", help="Access token", type=str)
    parser.add_argument("app_id", help="App id", type=int)
    parser.add_argument(
        "python_package", help="Python package name of the app", type=str
    )
    parser.add_argument(
        "--build_backend_packages",
        help="Also build/upload backend wheels (might take some time)",
        action="store_true",
        required=False,
    )
    parser.add_argument(
        "--local_compute_env",
        help="Change configured compute envs to run on this local machine",
        action="store_true",
        required=False,
    )
    parser.add_argument(
        "--deploy",
        help="Just deploy the package and quit, implies --build_backend_packages",
        action="store_true",
        required=False,
    )
    parser.add_argument(
        "--rq",
        help="Use rq worker",
        action="store_true",
        required=False,
    )
    return parser


class EventHandler(watchdog.events.RegexMatchingEventHandler):
    """Event handler for file changes"""

    def __init__(self, callback):
        super().__init__(regexes=[r".*\.py$"])
        self._last_register_time = time.time()
        self.callback = callback

    def on_created(self, _):
        self.handle()

    def on_modified(self, _):
        self.handle()

    def on_moved(self, _):
        self.handle()

    def on_deleted(self, _):
        self.handle()

    def handle(self):
        """Called on any change in the source code"""
        # maximum one event per second
        if time.time() - self._last_register_time > 1:
            # wait for a bit in case multiple files are changed at once
            time.sleep(0.2)
            try:
                self.callback()
            except Exception as e:
                print(
                    "Error while reloading app",
                    str(e),
                    file=sys.stderr,
                    flush=True,
                )
                print_exception(e)
            self._last_register_time = time.time()


class UpdateAppHandler(EventHandler):
    spec: WatchSpec
    config: AppConfig

    def __init__(self, watch_spec):
        self.spec = spec = watch_spec
        self.config = spec.update_config()
        super().__init__(self.handle_debounced)

    def handle_debounced(self):
        """Registers/updates the app on the backend"""
        # triggers hot-reloading of app in frontend
        config = self.spec.update_config()
        t = str(datetime.datetime.now()).split(".")[0].split(" ")[1]
        print(f"{t} Update app '{config.name}', id = {self.spec.app_id}")
        config_dump = config.model_dump(exclude_defaults=True)
        config.create_frontend_package()
        config_dump["frontend_package"] = base64.b64encode(
            config.frontend_package
        ).decode("utf-8")

        if self.spec.build_backend_packages:
            print("Creating backend packages")
            md = api.post(
                f"/get_app_python_packages_metadata",
                data={
                    "app_id": self.spec.app_id,
                },
            )
            old_packages = {p["name"]: p for p in md}

            config.create_backend_packages()
            packages = []
            for pkg in config.python_packages:
                pkg_dump = {
                    "file_name": pkg.file_name,
                    "package": "",
                }
                hash = calc_hash(pkg.package)
                if (
                    pkg.file_name not in old_packages
                    or old_packages[pkg.file_name]["hash"] != hash
                ):
                    # upload only if it's different from the current package in the database
                    pkg_dump["package"] = base64.b64encode(pkg.package).decode(
                        "utf-8"
                    )
                packages.append(pkg_dump)
            config_dump["python_packages"] = packages
            config_dump["python_packages_hash"] = config.python_packages_hash

        api.post(
            f"/app_admin/update_app/{self.spec.app_id}",
            data={
                "app_config": config_dump,
                "reload_dependencies": (
                    config.frontend_dependencies
                    if self.spec.reload_config
                    else []
                ),
            },
        )


def watch_app(handler):
    """Watch modules for changes"""
    watch_spec = handler.spec

    def watch(watch_spec: WatchSpec):
        spec = importlib.util.find_spec(watch_spec.python_module)
        path = os.path.dirname(spec.origin)
        observer = Observer()
        observer.schedule(handler, path, recursive=True)
        print("\t", path)
        if watch_spec.reload_config:
            handler.handle_debounced()
        observer.start()
        return observer

    observers = []
    try:
        config = watch_spec.update_config()
        print(f"Watching for changes in app '{config.name}'")
        observers.append(watch(watch_spec))
        for module_name in config.frontend_dependencies:
            module_spec = watch_spec.model_copy(
                update={"python_module": module_name, "reload_config": False}
            )
            observers.append(watch(module_spec))
        while True:
            time.sleep(1)
            pass
    except KeyboardInterrupt:
        print("Shutting down")
    except Exception as e:
        print_exception(e)
    finally:
        for observer in observers:
            observer.stop()
            observer.join()


def main():
    """cli main function"""

    parser = get_args_parser(description="Serve frontend from local machine")
    args = parser.parse_args()

    env = set_environment(EnvironmentType.LOCAL_APP)
    env.set_backend(args.backend_url, args.token)

    watch_spec = WatchSpec(
        app_id=args.app_id,
        config_module=args.python_package,
        build_backend_packages=args.build_backend_packages,
        local_compute_env=args.local_compute_env,
        reload_config=True,
        python_module=args.python_package,
    )
    handler = UpdateAppHandler(watch_spec)

    if args.deploy:
        print("Deploying app...")
        handler.handle_debounced()
        print("App deployed")
        return
    print()
    watch_app(handler)


if __name__ == "__main__":
    main()
