"""Interactive compute service: answers compute_node calls over a unix socket.

    python -m ngapp.cli.serve_api --socket /run/service/api.sock --workers 2

Started by ngapp.runner for compute environments with ``api = True``. One process per
worker shares the listening socket (prefork); the backend proxies
``POST /app/{app_id}/call/{func}`` to ``POST /call`` with a RunData body.
"""

import argparse
import os
import signal
import socket
import sys
import time
import traceback
from http.server import BaseHTTPRequestHandler, HTTPServer

import orjson

from .run import RunData, execute


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def address_string(self):
        return "unix"

    def log_message(self, fmt, *args):
        print(f"[{os.getpid()}] " + fmt % args, flush=True)

    def _send(self, status: int, payload):
        body = orjson.dumps(payload, option=orjson.OPT_SERIALIZE_NUMPY)
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            return self._send(200, {"pid": os.getpid()})
        self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/call":
            return self._send(404, {"error": "not found"})
        length = int(self.headers.get("Content-Length", 0))
        try:
            data = RunData.model_validate_json(self.rfile.read(length))
            t = time.time()
            result = execute(data)
            self.log_message("%s %.0f ms", data.func_name, 1000 * (time.time() - t))
            self._send(200, result)
        except Exception as e:
            traceback.print_exc()
            self._send(500, {"error": str(e), "traceback": traceback.format_exc()})


class UnixHTTPServer(HTTPServer):
    address_family = socket.AF_UNIX

    def __init__(self, listening_socket, handler):
        super().__init__("", handler, bind_and_activate=False)
        self.socket.close()
        self.socket = listening_socket
        self.server_name = "service"
        self.server_port = 0


def worker(sock):
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    UnixHTTPServer(sock, Handler).serve_forever()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--socket", required=True)
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()

    if os.path.exists(args.socket):
        os.unlink(args.socket)
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(args.socket)
    os.chmod(args.socket, 0o660)
    sock.listen(64)

    children: dict[int, int] = {}

    def spawn(index):
        pid = os.fork()
        if pid == 0:
            worker(sock)
            os._exit(0)
        children[pid] = index

    def shutdown(*_):
        for pid in list(children):
            os.kill(pid, signal.SIGTERM)
        for pid in list(children):
            os.waitpid(pid, 0)
        sock.close()
        if os.path.exists(args.socket):
            os.unlink(args.socket)
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    for i in range(args.workers):
        spawn(i)
    print(f"service listening on {args.socket} with {args.workers} worker(s)", flush=True)
    while True:
        pid, status = os.wait()
        index = children.pop(pid, None)
        if index is not None:
            print(f"worker {index} exited ({status}), restarting", flush=True)
            time.sleep(1)
            spawn(index)


if __name__ == "__main__":
    main()
