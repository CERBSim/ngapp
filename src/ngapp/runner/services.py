"""Persistent api services (compute environments with api = True) hosted by a runner.

The backend sends the desired services with every heartbeat response; the runner
reconciles its processes and reports their state with the next heartbeat.
"""

import http.client
import os
import shutil
import signal
import socket
import subprocess
import threading
import time
import traceback
from pathlib import Path

from .cache import Cache
from .client import BackendClient
from .execute import Sandbox

RESTART_BACKOFF = (5, 10, 30, 60, 120, 300)
START_TIMEOUT = 120


class UnixHTTPConnection(http.client.HTTPConnection):
    def __init__(self, path: str, timeout: float = 5):
        super().__init__("service", timeout=timeout)
        self.path = path

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect(self.path)


class ServiceProcess:
    def __init__(self, spec: dict, directory: Path):
        self.spec = spec
        self.directory = directory
        self.socket = directory / "api.sock"
        self.process: subprocess.Popen | None = None
        self.state = "starting"
        self.error = ""
        self.restarts = 0
        self.started: float | None = None
        self.next_start = 0.0
        self.log_file = None

    @property
    def id(self) -> int:
        return self.spec["id"]

    def same_version(self, spec: dict) -> bool:
        keys = ("sif_hash", "layer", "workers", "cpus", "memory")
        return all(self.spec.get(k) == spec.get(k) for k in keys)

    def healthy(self) -> bool:
        if not self.socket.exists():
            return False
        try:
            conn = UnixHTTPConnection(str(self.socket))
            conn.request("GET", "/health")
            return conn.getresponse().status == 200
        except OSError:
            return False

    def report(self) -> dict:
        return {
            "id": self.id,
            "state": self.state,
            "socket": str(self.socket),
            "pid": self.process.pid if self.process else None,
            "started": self.started,
            "restarts": self.restarts,
            "error": self.error[-2000:],
        }


class ServiceManager:
    def __init__(self, client: BackendClient, cache: Cache, sandbox: Sandbox, services_dir: Path, log=print):
        self.client = client
        self.cache = cache
        self.sandbox = sandbox
        self.services_dir = services_dir
        self.log = log
        self.services: dict[int, ServiceProcess] = {}
        self.lock = threading.Lock()
        self.stopped = threading.Event()
        services_dir.mkdir(parents=True, exist_ok=True)
        threading.Thread(target=self._check_loop, daemon=True).start()

    def _check_loop(self):
        while not self.stopped.wait(2):
            with self.lock:
                for svc in self.services.values():
                    try:
                        self._check(svc)
                    except Exception as e:
                        self.log(f"[service {svc.id}] check failed: {e}")

    def all_ready(self) -> bool:
        with self.lock:
            return all(s.state == "ready" for s in self.services.values())

    def reserved(self) -> tuple[int, int]:
        with self.lock:
            return (
                sum(s.spec["cpus"] for s in self.services.values()),
                sum(s.spec["memory"] for s in self.services.values()),
            )

    def reconcile_reports(self) -> list[dict]:
        """Current states without changing anything (sent with the heartbeat)"""
        with self.lock:
            for svc in self.services.values():
                self._check(svc)
            return [s.report() for s in self.services.values()]

    def reconcile(self, desired: list[dict]) -> list[dict]:
        """Start/stop/restart processes to match desired, return the current states"""
        wanted = {d["id"]: d for d in desired}
        with self.lock:
            for sid in list(self.services):
                if sid not in wanted:
                    self._stop(self.services.pop(sid), "removed")
                    self.cache.unpin(("service", sid))
            for sid, spec in wanted.items():
                svc = self.services.get(sid)
                if svc is None:
                    svc = self.services[sid] = ServiceProcess(spec, self.services_dir / str(sid))
                    self._start(svc)
                elif not svc.same_version(spec):
                    self.log(f"[service {sid}] new version, restarting")
                    self._stop(svc, "update")
                    svc.spec = spec
                    svc.restarts = 0
                    self._start(svc)
            for svc in self.services.values():
                self._check(svc)
            return [s.report() for s in self.services.values()]

    def stop_all(self):
        self.stopped.set()
        with self.lock:
            for svc in self.services.values():
                self._stop(svc, "shutdown")
                self.cache.unpin(("service", svc.id))
            self.services.clear()

    # internals, called with the lock held

    def _start(self, svc: ServiceProcess):
        self.cache.pin(
            ("service", svc.id), images=[svc.spec.get("sif_hash")], layers=[svc.spec["layer"]["hash"]]
        )
        svc.state = "starting"
        svc.error = ""
        svc.process = None
        svc.started = None
        threading.Thread(target=self._start_thread, args=(svc,), daemon=True).start()

    def _start_thread(self, svc: ServiceProcess):
        spec = svc.spec
        try:
            self._kill_stale(svc.directory)
            if svc.directory.exists():
                shutil.rmtree(svc.directory)
            svc.directory.mkdir(parents=True)
            image = None
            if spec.get("sif_hash") and self.sandbox.name != "none":
                image = self.cache.ensure_image(self.client, spec, log=self.log)
            layer = self.cache.ensure_layer(self.client, spec["layer"], log=self.log)
            cmd = self.sandbox.service_command(
                image, svc.directory, layer, spec["cpus"], spec["memory"], spec["workers"]
            )
            svc.log_file = open(svc.directory / "service.log", "ab")
            svc.process = subprocess.Popen(
                cmd,
                stdout=svc.log_file,
                stderr=subprocess.STDOUT,
                cwd=svc.directory,
                env=self.sandbox.environment(layer),
                start_new_session=True,
            )
            svc.started = time.time()
            (svc.directory / "pid").write_text(str(svc.process.pid))
            self.log(f"[service {svc.id}] started (pid {svc.process.pid})")
        except Exception as e:
            svc.state = "failed"
            svc.error = f"{e}\n{traceback.format_exc()}"
            self._schedule_restart(svc)
            self.log(f"[service {svc.id}] start failed: {e}")

    def _kill_stale(self, directory: Path):
        """A service left behind by a crashed runner would keep the socket busy"""
        pid_file = directory / "pid"
        if not pid_file.exists():
            return
        try:
            pid = int(pid_file.read_text())
            os.killpg(pid, signal.SIGTERM)
            self.log(f"killed stale service process group {pid}")
            time.sleep(1)
        except (ValueError, ProcessLookupError, PermissionError):
            pass

    def _check(self, svc: ServiceProcess):
        if svc.state == "failed":
            if svc.next_start and time.time() >= svc.next_start:
                svc.next_start = 0
                self._start(svc)
            return
        if svc.process is None:
            return
        if svc.process.poll() is not None:
            svc.state = "failed"
            svc.error = f"exited with code {svc.process.returncode}\n" + self._log_tail(svc)
            self.log(f"[service {svc.id}] exited with code {svc.process.returncode}")
            self._schedule_restart(svc)
            return
        if svc.state == "starting":
            if svc.healthy():
                svc.state = "ready"
                self.log(f"[service {svc.id}] ready on {svc.socket}")
            elif svc.started and time.time() - svc.started > START_TIMEOUT:
                self._stop(svc, "no health response")
                svc.state = "failed"
                svc.error = "service did not become healthy\n" + self._log_tail(svc)
                self._schedule_restart(svc)
        elif svc.state == "ready" and not svc.healthy():
            svc.state = "starting"

    def _schedule_restart(self, svc: ServiceProcess):
        delay = RESTART_BACKOFF[min(svc.restarts, len(RESTART_BACKOFF) - 1)]
        svc.restarts += 1
        svc.next_start = time.time() + delay

    def _stop(self, svc: ServiceProcess, reason: str):
        if svc.process is not None and svc.process.poll() is None:
            self.log(f"[service {svc.id}] stopping ({reason})")
            try:
                os.killpg(svc.process.pid, signal.SIGTERM)
                try:
                    svc.process.wait(10)
                except subprocess.TimeoutExpired:
                    os.killpg(svc.process.pid, signal.SIGKILL)
                    svc.process.wait(5)
            except ProcessLookupError:
                pass
        if svc.log_file:
            svc.log_file.close()
            svc.log_file = None
        svc.process = None
        svc.state = "stopping"
        if svc.socket.exists():
            svc.socket.unlink()

    def _log_tail(self, svc: ServiceProcess, lines: int = 30) -> str:
        try:
            return "\n".join((svc.directory / "service.log").read_text(errors="replace").splitlines()[-lines:])
        except OSError:
            return ""
