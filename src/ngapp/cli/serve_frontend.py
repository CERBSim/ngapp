import sys

_stdout = sys.stdout
sys.stdout = sys.stderr

import http.server
import os
import socketserver
import sys
import threading
import time
from urllib.parse import urlparse

from .. import utils
from .utils import download_frontend

HTTP_PORT = 8765


class _HTTPServer(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        super().end_headers()

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
    cache_only = os.environ.get("NGAPP_FRONTEND_CACHE_ONLY", "0") in (
        "1",
        "true",
        "True",
    )
    timing_enabled = os.environ.get("NGAPP_STARTUP_TIMING", "0") in (
        "1",
        "true",
        "True",
    )
    t0 = time.perf_counter()
    STATIC_DIR = download_frontend(cache_only=cache_only)
    t1 = time.perf_counter()
    if timing_enabled:
        print(
            f"Serving frontend from {STATIC_DIR} "
            f"(download_frontend={t1 - t0:.3f}s, cache_only={cache_only})"
        )

    os.chdir(STATIC_DIR)

    socketserver.ThreadingTCPServer.allow_reuse_address = True
    running = False
    env_port = os.environ.get("NGAPP_FRONTEND_PORT")
    try:
        port = int(env_port) if env_port else HTTP_PORT
    except ValueError:
        port = HTTP_PORT
    while not running:
        try:
            httpd = socketserver.ThreadingTCPServer(("", port), _HTTPServer)
            running = True
            thread = threading.Thread(target=httpd.serve_forever)
            thread.start()
            print(f"{port}\n", file=_stdout, flush=True)
            thread.join()
        except OSError as e:
            if e.errno in [48, 98]:
                print(f"Port {port} is already in use, trying next port")
                port += 1


if __name__ == "__main__":
    run_http_server()
