import argparse
import importlib
import importlib.util
import json
import os
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

from watchdog.observers import Observer

from ngapp.app import loadModel
from ngapp.cli.serve_in_venv import EventHandler
from ngapp.components.basecomponent import get_component

from .. import utils


def dump(data):
    try:
        return json.dumps(data)
    except Exception as e:
        print("could not serialize data", e)
        print(data)
        return "could_not_serialize"


def watch_python_modules(modules, callback):
    observers = []
    handler = EventHandler(lambda: callback(modules))

    try:
        for module_name in modules:
            spec = importlib.util.find_spec(module_name)
            origin = spec.origin
            if origin is None:
                origin = spec.submodule_search_locations[0]
            path = os.path.dirname(origin)
            print(f"Watching python module {module_name} at {path}")
            observer = Observer()
            observer.schedule(handler, path, recursive=True)
            observers.append(observer)
            observer.start()
        while True:
            time.sleep(1)
            pass
    except KeyboardInterrupt:
        print("Shutting down")
    except Exception as e:
        utils.print_exception(e)
    finally:
        for observer in observers:
            observer.stop()
            observer.join()


app = None


def reload_app(app_module, reload_modules):
    global app
    old_app = app
    old_app.component._emit_recursive("before_save")
    data = old_app.dump(exclude_default_data=True, include_storage_data=True)
    print("Reloading app")
    app_config = importlib.import_module(app_module).config
    app_data = {
        "id": 0,
        "python_class": app_config.python_class,
        "frontend_dependencies": app_config.frontend_dependencies,
        "frontend_pip_dependencies": app_config.frontend_pip_dependencies,
    }

    app = loadModel(app_data, data, reload_python_modules=reload_modules)
    utils.get_environment().frontend.reset_app(app)


def host_local_app(
    app_module,
    start_browser=True,
    watch_code=False,
    dev_frontend=False,
    app_args={},
):
    global app
    env = utils.set_environment(utils.Environment.LOCAL_APP, False)

    app_config = importlib.import_module(app_module).config
    app_data = {
        "id": 0,
        "python_class": app_config.python_class,
        "frontend_dependencies": app_config.frontend_dependencies,
        "frontend_pip_dependencies": app_config.frontend_pip_dependencies,
    }

    app = loadModel(app_data, {}, app_args=app_args)

    from webgpu import platform

    start_http_server = not dev_frontend

    def before_wait_for_connection(server):
        server = platform.websocket_server
        server.expose("get_component", get_component)

        ws_port = server.port

        if start_http_server:
            http_process = subprocess.Popen(
                [sys.executable, "-m", "ngapp.cli.serve_frontend"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            http_port = int(http_process.stdout.readline().strip())
        else:
            http_port = 3000

        url = f"http://localhost:{http_port}?backendPort={http_port}&websocketPort={ws_port}"

        if start_browser:
            default_browser_path = (
                "/usr/bin/google-chrome-unstable"
                if sys.platform == "linux"
                else None
            )
            browser_path = os.environ.get("NGAPP_BROWSER", default_browser_path)
            if browser_path and Path(browser_path).exists():
                webbrowser.get(f"{browser_path} %s &").open("--app=" + url)
            else:
                webbrowser.open("--app=" + url)
        print("Url to run the app:\n", url, "\n")

    platform.init(before_wait_for_connection)
    from webgpu import platform

    def stop_app(event):
        for on_exit_handler in app._on_exit_handlers:
            try:
                on_exit_handler()
            except Exception as e:
                print("Error in on_exit handler:", e)
        os._exit(0)

    platform.js.addEventListener(
        "unload",
        platform.create_event_handler(stop_app, prevent_default=False),
    )
    env.frontend.reset_app(app)

    if watch_code:
        watch_modules = [app_module.split(".")[0]]
        if isinstance(watch_code, list):
            watch_modules += watch_code
    else:
        watch_modules = []

    # this is blocking until a KeyboardInterrupt occurs
    watch_python_modules(
        watch_modules,
        lambda modules: reload_app(app_module, modules),
    )
    platform.js.close()
    platform.websocket_server.stop()


def main(app_module=None):
    global app

    args = argparse.ArgumentParser()
    if not app_module:
        args.add_argument(
            "--app",
            help="Python module containing a 'config' object of type AppConfig",
        )
    args.add_argument(
        "--dev-frontend",
        help="Use existing frontend at localhost:3000",
        action="store_true",
    )
    args.add_argument(
        "--no-browser", help="Don't start webbrowser", action="store_true"
    )
    args.add_argument(
        "--dev",
        help="Development mode - watch for changes in the app code and does automatic reloading",
        action="store_true",
    )
    args = args.parse_args()

    if not app_module:
        app_module = args.app

    host_local_app(
        app_module=app_module,
        start_browser=not args.no_browser,
        watch_code=args.dev,
        dev_frontend=args.dev_frontend,
    )


if __name__ == "__main__":

    main(args.app, not args.dev)
