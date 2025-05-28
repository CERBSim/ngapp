import base64
import importlib
import json
import subprocess
import sys

from ..utils import zip_directory


def load_app_config(full_class_name, zip_data=True):
    stdout = sys.stdout
    sys.stdout = open("/dev/null", "w")
    path = full_class_name.split(".")

    parent_module = path[0]
    need_reload = parent_module in sys.modules
    module = importlib.import_module(path[0])
    if need_reload:
        module = importlib.reload(module)
    for p in path[1:-1]:
        module = getattr(module, p)
    cls = getattr(module, path[-1])

    app_config = cls.getAppConfig()
    sys.stdout = stdout

    package = importlib.import_module(module.__package__)
    package_path = package.__path__[0]

    if zip_data:
        data = zip_directory(package_path)
        app_config["python_package"] = base64.b64encode(data).decode("utf-8")

    app_config["accessConfig"]["levels"] = {}
    app_config["accessConfig"]["defaultAccessLevel"] = app_config[
        "accessConfig"
    ]["defaultAccessLevel"].value
    app_config["access_config_dict"] = app_config.pop("accessConfig")

    app_config["owner"] = None
    return {"path": package_path, "app_config": app_config}


def generate_app_config(full_class_name):
    result = subprocess.check_output(
        [sys.executable, "-m", "ngapp.cli.generate_app_config", full_class_name]
    )
    return json.loads(result.decode("utf-8"))


if __name__ == "__main__":
    print(json.dumps(load_app_config(sys.argv[1])))
