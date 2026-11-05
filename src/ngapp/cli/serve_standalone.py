import argparse
import importlib
import importlib.util
import json
import os
import socket
import subprocess
import sys
import time
import webbrowser
from collections.abc import Callable
from pathlib import Path
from threading import Event, Thread

from webgpu.link.websocket import WebsocketLinkServer

from ngapp.app import create_app
from ngapp.components.basecomponent import get_component, unmount_component

from .. import utils


def dump(data):
    try:
        return json.dumps(data)
    except Exception as e:
        print("could not serialize data", e)
        print(data)
        return "could_not_serialize"


def wait_until_stopped(stop_event: Event | None = None):
    """Block until explicitly stopped (tests) or interrupted (CLI usage)."""
    try:
        while True:
            if stop_event is not None and stop_event.is_set():
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down")


def watch_python_modules(modules, callback, stop_event: Event | None = None):
    from watchdog.observers import Observer

    from ngapp.cli.serve_in_venv import EventHandler

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
        wait_until_stopped(stop_event)
    except Exception as e:
        utils.print_exception(e)
    finally:
        for observer in observers:
            observer.stop()
            observer.join()


app = None

# seconds the local app waits for a page to connect again after the last
# one was closed (a reload) before it exits
_EXIT_GRACE = float(os.environ.get("NGAPP_EXIT_GRACE", "10"))


class _PageLinkServer(WebsocketLinkServer):
    """Link of the local app: a new page (a reload, another window) takes
    over the connection of the previous one; on_page() runs for each page
    after the first"""

    on_page = None

    async def _websocket_handler(self, websocket, path=""):
        old = self._connection
        first = not self._event_is_connected.is_set()
        self._connection = websocket
        self._event_is_connected.set()
        if old is not None:
            await old.close(4000, "The app was opened in another window")
        if not first and self.on_page is not None:
            Thread(target=self.on_page, daemon=True).start()
        try:
            async for message in websocket:
                if websocket is not self._connection:
                    break
                if self._is_chunk(message):
                    full = self._reassemble_chunk(message)
                    if full is not None:
                        self._dispatch(full)
                else:
                    self._dispatch(message)
        finally:
            if self._connection is websocket:
                self._connection = None
                self._chunk_buffers.clear()


def _reset_page_state(platform):
    """Forget the objects of the previous page: JavaScript ids restart in a
    new page, so proxies of the old one must not release or reach objects of
    the new one; calls waiting for the old page end"""
    import gc

    from webgpu.link.proxy import Proxy

    server = platform.websocket_server
    for obj in gc.get_objects():
        if issubclass(type(obj), Proxy) and obj.__dict__.get("_link") is server:
            obj.__dict__["_link"] = None
    with server._refcount_lock:
        server._cache.clear()
        server._js_id_refcount.clear()
        server._release_queue.clear()
    for value in list(server._requests.values()):
        if isinstance(value, tuple) and hasattr(value[0], "set"):
            value[0].set()
    platform.js = server.get(None, None)
    try:
        from webgpu import font
        from webgpu import utils as wutils

        wutils._device = None
        wutils._device_failure = None
        font._default_font_atlas = None
    except Exception as e:
        utils.print_exception(e)


def reload_app(app_module, reload_modules):
    global app
    cases = utils.get_environment().local_cases
    if cases is not None:
        print("Reloading app")
        cases.reload(reload_modules)
        return
    old_app = app
    old_app._emit_recursive("before_save")
    data = old_app._dump_app(
        exclude_default_data=True, include_storage_data=True
    )
    print("Reloading app")
    app_config = importlib.import_module(app_module).config
    app = create_app(app_config, data, reload_python_modules=reload_modules)
    utils.get_environment().frontend.reset_app(app)


def host_local_app(
    app_module,
    start_browser=True,
    watch_code=False,
    dev_frontend=False,
    app_args={},
    *,
    exit_on_unload: bool = True,
    stop_event: Event | None = None,
    url_callback: Callable[[str], None] | None = None,
    store: str | os.PathLike | None = None,
    import_files: list | None = None,
    cases: bool = True,
):
    """Serve the app locally; its cases live in a local SQLite store (store,
    default ngapp.local_cases.store_path), the last opened one is shown and
    import_files (case files or .sav files of the previous local mode) are
    imported first. With cases=False there is no case store, every page
    shows a new app instance"""
    from webgpu import platform

    from ..local_cases import LocalCases

    # the local app's link accepts reloads and new pages
    platform.WebsocketLinkServer = _PageLinkServer

    global app
    use_cases = cases
    cases: LocalCases | None = None
    shown = Event()

    def show_app(new_app):
        global app
        app = new_app
        if shown.is_set():
            utils.get_environment().frontend.reset_app(new_app)

    timing_enabled = os.environ.get("NGAPP_STARTUP_TIMING", "0") in (
        "1",
        "true",
        "True",
    )
    reuse_frontend = os.environ.get("NGAPP_FRONTEND_REUSE", "0") in (
        "1",
        "true",
        "True",
    )
    persist_frontend = os.environ.get("NGAPP_FRONTEND_PERSIST", "0") in (
        "1",
        "true",
        "True",
    )
    frontend_port_env = os.environ.get("NGAPP_FRONTEND_PORT")
    try:
        frontend_port = int(frontend_port_env) if frontend_port_env else 8765
    except ValueError:
        frontend_port = 8765
    startup_t0 = time.perf_counter()
    last_checkpoint = startup_t0

    def _is_port_open(port: int) -> bool:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                return True
        except OSError:
            return False

    start_http_server = not dev_frontend
    http_process: subprocess.Popen | None = None
    env: Environment = None

    def before_wait_for_connection(server):
        nonlocal http_process, env, last_checkpoint, startup_t0, cases
        global app

        server = platform.websocket_server
        server.expose("get_component", get_component)
        server.expose("unmount_component", unmount_component)

        env = utils.set_environment(utils.Environment.LOCAL_APP, False, server)
        if use_cases:
            env.data_layer = True
            app_config = importlib.import_module(app_module).config
            cases = LocalCases(
                app_config, store, app_args=app_args, on_app=show_app
            )
            env.local_cases = cases
            server.expose("ngapp_cases", cases)
        server.on_page = on_page
        last_checkpoint = time.perf_counter()

        ws_port = server.port
        ws_token = server.auth_token

        if start_http_server:
            if reuse_frontend and _is_port_open(frontend_port):
                http_port = frontend_port
                if timing_enabled:
                    print(
                        f"Standalone startup: frontend_reuse=True (port={http_port})"
                    )
            else:
                child_env = os.environ.copy()
                child_env["NGAPP_FRONTEND_PORT"] = str(frontend_port)
                http_process = subprocess.Popen(
                    [sys.executable, "-m", "ngapp.cli.serve_frontend"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=child_env,
                )
                output = http_process.stdout.readline().strip()
                try:
                    http_port = int(output)
                except ValueError:
                    print("Failed to start fronten server:", output)
                    sys.exit(1)

        else:
            http_port = 3000

        now = time.perf_counter()
        if timing_enabled:
            print(
                f"Standalone startup: frontend_server={now - last_checkpoint:.3f}s "
                f"(total={now - startup_t0:.3f}s, port={http_port})"
            )
        last_checkpoint = now

        startup_timing_query = "&startupTiming=1" if timing_enabled else ""
        url = (
            f"http://localhost:{http_port}?backendPort={http_port}"
            f"&websocketPort={ws_port}&wsToken={ws_token}{startup_timing_query}"
        )

        # Optional test hook: when running under automated tests, write the
        # computed URL into a file so that external processes can discover it
        # without relying on stdout buffering behaviour.
        url_file = os.environ.get("NGAPP_TEST_URL_FILE")
        if url_file:
            try:
                Path(url_file).write_text(url, encoding="utf-8")
            except Exception as e:  # pragma: no cover - best effort only
                print("Failed to write NGAPP_TEST_URL_FILE:", e)

        if start_browser:
            if os.environ.get("NGAPP_BROWSER"):
                args = os.environ.get("NGAPP_BROWSER").split()
            else:
                args = [None]
            browser = args.pop(0)
            browser_path = None
            if browser:
                if browser.startswith("/"):
                    browser_path = browser
                else:
                    for path_dir in os.environ.get("PATH", "").split(
                        os.pathsep
                    ):
                        candidate = Path(path_dir) / browser
                        if candidate.exists() and candidate.is_file():
                            browser_path = str(candidate)
                            break
            if not browser_path and sys.platform == "linux":
                for name in (
                    "google-chrome-unstable",
                    "google-chrome-stable",
                    "google-chrome",
                    "chromium",
                    "chromium-browser",
                ):
                    candidate = f"/usr/bin/{name}"
                    if Path(candidate).exists():
                        browser_path = candidate
                        break
            if not browser_path and sys.platform == "darwin":
                for candidate in (
                    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                ):
                    if Path(candidate).exists():
                        browser_path = candidate
                        break
            if not browser_path and sys.platform == "win32":
                win_candidates = []
                for env_var in (
                    "PROGRAMFILES",
                    "PROGRAMFILES(X86)",
                    "LOCALAPPDATA",
                ):
                    base = os.environ.get(env_var)
                    if base:
                        win_candidates.append(
                            Path(base)
                            / "Google"
                            / "Chrome"
                            / "Application"
                            / "chrome.exe"
                        )
                        win_candidates.append(
                            Path(base)
                            / "Microsoft"
                            / "Edge"
                            / "Application"
                            / "msedge.exe"
                        )
                for candidate in win_candidates:
                    if candidate.exists():
                        browser_path = str(candidate)
                        break
            opened_as_app = False
            if browser_path and Path(browser_path).exists():
                user_data_dir = Path(
                    os.environ.get(
                        "NGAPP_CHROME_PROFILE",
                        Path.home() / ".config" / "ngapp-chrome",
                    )
                )
                subprocess.Popen(
                    [
                        browser_path,
                        f"--user-data-dir={user_data_dir}",
                        "--app=" + url,
                    ]
                    + args,
                    start_new_session=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                opened_as_app = True
            else:
                webbrowser.open(url)
        now = time.perf_counter()
        if timing_enabled:
            print(
                f"Standalone startup: browser_launch={now - last_checkpoint:.3f}s "
                f"(total={now - startup_t0:.3f}s)"
            )
        last_checkpoint = now
        if not (start_browser and opened_as_app):
            print("Url to run the app:\n", url, "\n")

        # Optional hook for in-process test runners which prefer to
        # receive the computed URL directly instead of polling a
        # temporary file.
        if url_callback is not None:
            try:
                url_callback(url)
            except Exception as e:  # pragma: no cover - best effort only
                print("Failed to call url_callback:", e)

    pages = [0]

    def exit_app():
        for on_exit_handler in app._on_exit_handlers:
            try:
                on_exit_handler()
            except Exception as e:
                print("Error in on_exit handler:", e)
        os._exit(0)

    def stop_app(event):
        if cases is not None:
            cases.save()
        # In normal CLI usage we exit the whole process, unless a page
        # connects again soon (a reload). For tests or embedded usage,
        # ``exit_on_unload`` can be set to ``False`` so that the caller
        # controls shutdown.
        if exit_on_unload:
            page = pages[0]

            def later():
                time.sleep(_EXIT_GRACE)
                if pages[0] == page:
                    exit_app()

            Thread(target=later, daemon=True).start()

    def show_page():
        """The case in the connected page: opened after the connection, so
        that on_load can create views that need the browser (WebGPU)"""
        platform.js.addEventListener(
            "unload",
            platform.create_event_handler(stop_app, prevent_default=False),
        )
        if cases is None:
            show_app(
                create_app(
                    importlib.import_module(app_module).config,
                    {},
                    app_args=app_args,
                )
            )
            if not shown.is_set():
                shown.set()
                env.frontend.reset_app(app)
            return
        if not shown.is_set():
            imported = None
            for path in import_files or []:
                imported = cases.import_file(path)
                print(f"Imported {path} as case {imported}")
            if imported is not None and imported != cases.case_id:
                cases.open(imported)
            elif cases.app is None:
                cases.start()
            shown.set()
            env.frontend.reset_app(app)
        elif cases.case_id is not None:
            # a fresh app instance for the new page
            cases.open(cases.case_id)
        else:
            cases.start()

    def on_page():
        """Another page connected (a reload or a new window): it shows the
        app, the previous page was disconnected"""
        pages[0] += 1
        _reset_page_state(platform)
        try:
            show_page()
        except Exception as e:
            utils.print_exception(e)

    platform.init(before_wait_for_connection)
    from webgpu import platform

    show_page()
    if timing_enabled:
        print(
            "Standalone startup: app_shown="
            f"{time.perf_counter() - startup_t0:.3f}s"
        )

    if watch_code:
        watch_modules = [app_module.split(".")[0]]
        if isinstance(watch_code, list):
            watch_modules += watch_code
        elif isinstance(watch_code, str):
            watch_modules += [mod.strip() for mod in watch_code.split(",")]

        watch_python_modules(
            watch_modules,
            lambda modules: reload_app(app_module, modules),
            stop_event=stop_event,
        )
    else:
        wait_until_stopped(stop_event)

    # Gracefully shut down the frontend and backend servers.
    if http_process is not None and not persist_frontend:
        http_process.terminate()
        try:
            http_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            http_process.kill()

    if cases is not None:
        cases.close()
        env.local_cases = None
    try:
        platform.js.close()
    except Exception:
        pass
    platform.reset()


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
        help="Development mode - watch for changes in the app code (and additionally provided modules) and does automatic reloading",
        nargs="?",
        const=True,
        default=False,
        metavar="MODULES",
    )
    args.add_argument(
        "--store",
        help="Case database (default ~/.local/share/ngapp/<app>/cases.sqlite)",
    )
    args.add_argument(
        "--import",
        dest="import_files",
        nargs="+",
        metavar="FILE",
        help="Import case files (.ngcase) or saved files of the previous local mode (.sav)",
    )
    args = args.parse_args()

    if not app_module:
        app_module = args.app

    host_local_app(
        app_module=app_module,
        start_browser=not args.no_browser,
        watch_code=args.dev,
        dev_frontend=args.dev_frontend,
        store=args.store,
        import_files=args.import_files,
    )


if __name__ == "__main__":
    main()
