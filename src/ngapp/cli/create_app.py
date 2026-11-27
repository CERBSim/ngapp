"""Create a new app on a webapp backend and upload it.

    python -m ngapp.cli.create_app <backend_url> <token> <group_id>

The command including a token and the group of the app is copied from "Add new app" on the
App Dev page. It asks for the python package of the app (the AppConfig is read from
<package>.appconfig). The creator owns the app.
"""

import argparse

from .. import api
from ..utils import EnvironmentType, set_environment
from .deploy import load_config, upload_app


def ask(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        raise SystemExit("\nAborted")


def main():
    parser = argparse.ArgumentParser(description="Create a new app on a webapp backend")
    parser.add_argument("backend_url")
    parser.add_argument("token")
    parser.add_argument("group_id", type=int, help="group of the app (Add new app shows it)")
    args = parser.parse_args()

    module = ""
    while not module:
        module = ask("Python package of the app (e.g. myapp or myapp.appconfig): ")
    if not module.endswith(".appconfig"):
        module += ".appconfig"
    config = load_config(module)
    package = config.python_class.split(".")[0]

    set_environment(EnvironmentType.LOCAL_APP).set_backend(args.backend_url, args.token)
    existing = [
        app
        for app in api.post("/app_admin/my_apps", {})
        if app["python_class"].split(".")[0] == package
    ]
    for app in existing:
        print(f"App '{app['name']}' (id {app['id']}) already uses the python package '{package}'")
    if existing and ask("Create another app anyway? [y/N] ").lower() not in ("y", "yes"):
        raise SystemExit("Aborted")

    print(f"Creating app '{config.name}'")
    app = api.post(
        "/v2/apps",
        {
            "name": config.name,
            "version": config.version,
            "description": config.description,
            "python_class": config.python_class,
            "group_id": args.group_id,
        },
    )
    upload_app(config, app["id"], reload_dependencies=config.frontend_dependencies)
    print(f"Created '{config.name}' (id {app['id']}) on {args.backend_url}")


if __name__ == "__main__":
    main()
