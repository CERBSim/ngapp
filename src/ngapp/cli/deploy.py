"""Upload an app to a webapp backend.

    python -m ngapp.cli.deploy <backend_url> <token> <app_module>.appconfig

The command including a token is copied from "Add new app" on the App Dev page. The app
is created on the backend if the user does not own one with the same python class yet.
Frontend package and compute packages are built and uploaded (see
ngapp.compute_packages); compute environment images are rebuilt by the backend when
their definition changed.
"""

import argparse
import base64
import datetime
import importlib

from .. import api
from ..app import AppConfig
from ..utils import EnvironmentType, calc_hash, set_environment


def upload_app(
    config: AppConfig,
    app_id: int,
    build_backend_packages: bool = True,
    reload_dependencies: list[str] | None = None,
    wheels_dir: str | None = None,
):
    """Build packages and post the app config to /app_admin/update_app"""
    t = str(datetime.datetime.now()).split(".")[0].split(" ")[1]
    print(f"{t} Update app '{config.name}', id = {app_id}")
    config_dump = config.model_dump(exclude_defaults=True)
    config_dump.pop("compute_dependencies", None)  # resolved here, not used by the backend
    config.create_frontend_package()
    config_dump["frontend_package"] = base64.b64encode(config.frontend_package).decode("utf-8")

    if build_backend_packages:
        print("Creating backend packages")
        md = api.post("/get_app_python_packages_metadata", data={"app_id": app_id})
        old_packages = {p["name"]: p for p in md}

        config.create_backend_packages(old_packages, wheels_dir)
        packages = []
        for pkg in config.python_packages:
            pkg_dump = {"file_name": pkg.file_name, "package": "", "build_key": pkg.build_key}
            if pkg.package is not None and (
                pkg.file_name not in old_packages
                or old_packages[pkg.file_name]["hash"] != calc_hash(pkg.package)
            ):
                # upload only if it differs from the package in the database
                pkg_dump["package"] = base64.b64encode(pkg.package).decode("utf-8")
            packages.append(pkg_dump)
        config_dump["python_packages"] = packages
        config_dump["python_packages_hash"] = config.python_packages_hash

    api.post(
        f"/app_admin/update_app/{app_id}",
        data={
            "app_config": config_dump,
            "reload_dependencies": reload_dependencies or [],
        },
    )


def find_or_create_app(config: AppConfig) -> int:
    """Id of the user's app with this python class, created if missing"""
    for app in api.post("/app_admin/my_apps", {}):
        if app["python_class"] == config.python_class:
            return app["id"]
    for app in api.post("/app_admin/my_apps", {}):
        if app["name"] == config.name:
            return app["id"]
    print(f"Creating app '{config.name}'")
    app = api.post(
        "/app_admin/create_app",
        {
            "name": config.name,
            "version": config.version,
            "description": config.description,
            "python_class": config.python_class,
        },
    )
    return app["id"]


def load_config(module_name: str) -> AppConfig:
    module = importlib.import_module(module_name)
    config = getattr(module, "config", None)
    if not isinstance(config, AppConfig):
        raise SystemExit(f"{module_name} has no AppConfig named 'config'")
    return config


def main():
    parser = argparse.ArgumentParser(description="Deploy an app to a webapp backend")
    parser.add_argument("backend_url")
    parser.add_argument("token")
    parser.add_argument("config_module", help="module with the AppConfig, e.g. myapp.appconfig")
    parser.add_argument(
        "--local-compute-env",
        action="store_true",
        help="set all compute environments to 'local' (run on your own runner, no image)",
    )
    parser.add_argument(
        "--wheels",
        metavar="DIR",
        help="also upload the wheels in DIR (prebuilt compute dependencies)",
    )
    args = parser.parse_args()

    config = load_config(args.config_module)
    if args.local_compute_env:
        for env in config.compute_environments:
            env.env_type = "local"

    set_environment(EnvironmentType.LOCAL_APP).set_backend(args.backend_url, args.token)
    app_id = find_or_create_app(config)
    upload_app(
        config,
        app_id,
        reload_dependencies=config.frontend_dependencies,
        wheels_dir=args.wheels,
    )
    print(f"Deployed '{config.name}' (id {app_id}) to {args.backend_url}")


if __name__ == "__main__":
    main()
