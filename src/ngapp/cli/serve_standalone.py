import argparse
import http.server
import importlib
import importlib.util
import json
import os
import socketserver
import sys
import tempfile
import threading
import time
import webbrowser
import zipfile
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

import requests
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


def download_and_extract_frontend():
    temp_dir = tempfile.mkdtemp()

    response = requests.get("https://ngsolve.org/files/webapp/spa.zip")
    response.raise_for_status()

    with zipfile.ZipFile(BytesIO(response.content), "r") as zip_ref:
        zip_ref.extractall(temp_dir)

    return temp_dir


HTTP_PORT = 8765


class _HTTPServer(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path.startswith("/python_module"):
            package_name = parsed_path.path.split("/")[-1]
            return self.serve_zip(package_name)
        else:
            return super().do_GET()

    def serve_zip(self, name: str):
        data = utils.zip_modules([name])
        filename = f"{name}.zip"
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Type", "application/zip")
        self.send_header(
            "Content-Disposition", f"attachment; filename={filename}"
        )
        self.end_headers()
        self.wfile.write(data)


def run_http_server():
    STATIC_DIR = download_and_extract_frontend()

    os.chdir(STATIC_DIR + "/spa")

    socketserver.ThreadingTCPServer.allow_reuse_address = True
    running = False
    port = HTTP_PORT
    while not running:
        try:
            httpd = socketserver.ThreadingTCPServer(("", port), _HTTPServer)
            running = True
            thread = threading.Thread(target=httpd.serve_forever)
            thread.daemon = True
            thread.start()
            return port
        except OSError as e:
            if e.errno == 98:
                print(f"Port {port} is already in use, trying next port")
                port += 1


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
    app_module, start_browser=True, watch_code=False, dev_frontend=False
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

    app = loadModel(app_data, {})

    from webgpu import platform

    start_http_server = not dev_frontend

    def before_wait_for_connection(server):
        server = platform.websocket_server
        server.expose("get_component", get_component)

        ws_port = server.port

        if start_http_server:
            http_port = run_http_server()
            print("running on port", http_port)
        else:
            http_port = 3000

        url = f"http://localhost:{http_port}?backendPort={http_port}&websocketPort={ws_port}"

        if start_browser:
            chrome_path = Path("/usr/bin/google-chrome-unstable")
            if sys.platform.startswith("linux") and chrome_path.exists():
                webbrowser.get(f"/usr/bin/google-chrome-unstable %s &").open(
                    "--app=" + url
                )
            else:
                webbrowser.open("--app=" + url)
        print("Url to run the app:\n", url, "\n")

    platform.init(before_wait_for_connection)
    print("Client connected")
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
