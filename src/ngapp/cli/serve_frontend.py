import sys

_stdout = sys.stdout
sys.stdout = sys.stderr

import http.server
import os
import socketserver
import sys
import threading
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
    STATIC_DIR = download_frontend()
    print("Serving frontend from", STATIC_DIR)

    os.chdir(STATIC_DIR)

    socketserver.ThreadingTCPServer.allow_reuse_address = True
    running = False
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
