import importlib
import json
import sys

import ngapp.app

if __name__ == "__main__":
    module_name = sys.argv[1]
    importlib.import_module(module_name)

    apps = {}
    for app in ngapp.app._app_register:
        id = app.modelName
        data = dict(
            id=app.modelName,
            name=app.modelName,
            version=app.modelVersion,
            group=app.modelGroup,
            picture=app.getPicture(),
            description=app.getDescription().replace(r"\\", r"\\\\"),
            default_name=app.modelName,
            python_module=app.__module__,
            python_class=app.__name__,
            can_run=app.canRun,
        )
        if hasattr(app, "modelDefaultAccess"):
            data["default_access_level_v"] = app.modelDefaultAccess.value
        apps[id] = data
    json.dump(apps, open(sys.argv[2], "w"), indent=4)
