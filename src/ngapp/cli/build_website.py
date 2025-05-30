import argparse
import importlib
import io
import json
import zipfile
import os
from pathlib import Path

import requests

from ..app import AppConfig
from ..utils import EnvironmentType, set_environment, zip_modules

set_environment(EnvironmentType.STANDALONE)


def build_app(app: str, app_id: int, output_dir: Path):
    obj_path = app.split(".")
    module_name = obj_path[0]
    main_module = importlib.import_module(module_name)

    obj = main_module
    for name in obj_path[1:]:
        if hasattr(obj, name):
            obj = getattr(obj, name)
        else:
            module_name = f"{module_name}.{name}"
            obj = importlib.import_module(module_name)

    config = None
    if isinstance(obj, AppConfig):
        config = obj
    elif hasattr(obj, "appconfig"):
        config = getattr(obj, "appconfig")
    elif hasattr(obj, "config"):
        config = getattr(obj, "config")
    else:
        raise ValueError(
            f"Could not find appconfig or config in {app}. "
            "Please provide a valid AppConfig object or module."
        )

    (output_dir / config.python_package_name).write_bytes(
        zip_modules([config.python_package_name])
    )

    return {
        "id": app_id,
        "name": config.name,
        "python_class": config.python_class,
        "frontend_pip_dependencies": config.frontend_pip_dependencies,
        "frontend_dependencies": config.frontend_dependencies,
        "description": config.description,
        "image": config.image,
        "logo": config.logo,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Build a static website hosting one ore more apps."
    )
    parser.add_argument(
        "-a",
        "--app",
        type=str,
        help="""Includes given app.
        Either python-path to an AppConfig object, or to a module containing an 'appconfig' or 'config' object.
        Can be passed multiple times.""",
        action="append",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="html",
        help="Output directory for the static website. Must be empty an empty directory or non-existent.",
    )
    parser.add_argument(
        "-v",
        "--version",
        type=str,
        default="dev",
        help="ngapp version to use",
    )
    args = parser.parse_args()
    output_dir = Path(args.output)

    if output_dir.exists():
        try:
            output_dir.rmdir()
        except OSError:
            raise ValueError(
                f"Output directory {output_dir} already exists and is non-empty."
            )

    response = requests.get("https://ngsolve.org/ngapp/ngapp-dev.zip")
    response.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
        zip_ref.extractall(output_dir)

    # # for some reason, some assets are loaded from assets/assets, create a symlink to work around this
    # cwd = os.getcwd()
    # os.chdir(output_dir / "assets")
    # os.symlink(".", "assets")
    # os.chdir(cwd)

    python_module_dir = output_dir / "python_modules"
    python_module_dir.mkdir(parents=True, exist_ok=True)
    configs = {}
    app_id = 1
    for app in args.app:
        configs[app_id] = build_app(app, app_id, python_module_dir)
        app_id += 1

    (output_dir / "get_available_applications").write_text(
        json.dumps(configs, indent=4)
    )


if __name__ == "__main__":
    main()
