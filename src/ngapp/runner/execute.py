"""Run one assigned job in a sandbox and report to the backend"""

import os
import shutil
import signal
import subprocess
import sys
import threading
import time
import traceback
from pathlib import Path

import orjson

from .cache import Cache
from .client import BackendClient, BackendUnavailable, JobLost, Unauthorized

HEARTBEAT_INTERVAL = 10
LOG_FLUSH_INTERVAL = 2
LOG_FLUSH_SIZE = 64 * 1024
LOG_BUFFER_LIMIT = 16 * 1024 * 1024
KILL_GRACE = 10


class StateLog:
    """Logs a failure when it starts or changes its kind, and the recovery, instead of every
    repetition"""

    def __init__(self, log, what: str):
        self.log = log
        self.what = what
        self.kind = None

    def failed(self, kind: str, message: str):
        if kind != self.kind:
            self.log(message)
        self.kind = kind

    def ok(self):
        if self.kind is not None:
            self.log(f"{self.what} works again")
        self.kind = None


def failure_kind(e: Exception) -> str:
    return "refused" if isinstance(e, Unauthorized) else "unreachable"


class Sandbox:
    name = ""

    def work_path(self, work: Path) -> str:
        """Path of the job's work directory inside the sandbox"""
        return str(work)

    def command(
        self, image: Path | None, work: Path, layer: Path, cpus: int, memory: int, job_env: dict, gpus: list[int]
    ) -> list[str]:
        raise NotImplementedError

    def service_command(
        self, image: Path | None, directory: Path, layer: Path, cpus: int, memory: int, workers: int
    ) -> list[str]:
        raise NotImplementedError

    def environment(self, layer: Path, job_env: dict | None = None) -> dict:
        return {**os.environ, **(job_env or {})}


class NoSandbox(Sandbox):
    """Run with the runner's own python, no isolation and no limits (trusted dev machines)"""

    name = "none"

    def command(self, image, work, layer, cpus, memory, job_env, gpus):
        return [sys.executable, "-m", "ngapp.cli.run_job", str(work / "job.json")]

    def service_command(self, image, directory, layer, cpus, memory, workers):
        return [
            sys.executable, "-m", "ngapp.cli.serve_api",
            "--socket", str(directory / "api.sock"), "--workers", str(workers),
        ]

    def environment(self, layer, job_env=None):
        env = {**os.environ, **(job_env or {})}
        env["PYTHONPATH"] = str(layer) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
        return env


class ApptainerSandbox(Sandbox):
    name = "apptainer"

    def __init__(self, limits: bool = True):
        self.limits = limits
        if shutil.which("apptainer") is None:
            raise RuntimeError("apptainer not found, install it or use --sandbox none")

    def work_path(self, work):
        return "/work"

    def command(self, image, work, layer, cpus, memory, job_env, gpus):
        if image is None:
            raise RuntimeError("compute environment has no image")
        cmd = [
            "apptainer", "exec", "--containall", "--cleanenv",
            "--pwd", "/work",
            "--home", f"{work}:/work",
            "--bind", f"{work / 'tmp'}:/tmp",
            "--bind", f"{layer}:/apps:ro",
            "--env", "PYTHONPATH=/apps",
        ]
        for key, value in job_env.items():
            cmd += ["--env", f"{key}={value}"]
        if "NGAPP_JOB_CACHE_DIR" in job_env:
            cmd += ["--bind", job_env["NGAPP_JOB_CACHE_DIR"]]
        if gpus:
            cmd += ["--nv"]
        if self.limits:
            cmd += ["--cpus", str(cpus), "--memory", f"{memory}M"]
        cmd += [str(image), "python", "-m", "ngapp.cli.run_job", "/work/job.json"]
        return cmd

    def service_command(self, image, directory, layer, cpus, memory, workers):
        if image is None:
            raise RuntimeError("compute environment has no image")
        cmd = [
            "apptainer", "exec", "--containall", "--cleanenv",
            "--pwd", "/run/service",
            "--home", f"{directory}:/run/service",
            "--bind", f"{layer}:/apps:ro",
            "--env", "PYTHONPATH=/apps",
        ]
        if self.limits:
            cmd += ["--cpus", str(cpus), "--memory", f"{memory}M"]
        cmd += [
            str(image), "python", "-m", "ngapp.cli.serve_api",
            "--socket", "/run/service/api.sock", "--workers", str(workers),
        ]
        return cmd


class LogPump(threading.Thread):
    """Forwards one output stream of the job process to the backend in chunks; keeps the data
    while the backend is unreachable"""

    def __init__(self, stream, send, echo=None):
        super().__init__(daemon=True)
        self.stream = stream
        self.send = send
        self.echo = echo
        self.buffer = []
        self.size = 0
        self.lock = threading.Lock()
        self.last_flush = time.time()
        self.lost = False

    def run(self):
        for line in iter(self.stream.readline, b""):
            text = line.decode("utf-8", errors="replace")
            if self.echo:
                self.echo(text.rstrip("\n"))
            if self.lost:
                continue
            with self.lock:
                self.buffer.append(text)
                self.size += len(text)
                while self.size > LOG_BUFFER_LIMIT and len(self.buffer) > 1:
                    self.size -= len(self.buffer.pop(0))
            if self.size >= LOG_FLUSH_SIZE or time.time() - self.last_flush > LOG_FLUSH_INTERVAL:
                self.flush()
        self.flush()

    def flush(self):
        with self.lock:
            data = "".join(self.buffer)
            self.buffer = []
            self.size = 0
            self.last_flush = time.time()
        if not data or self.lost:
            return
        try:
            self.send(data)
        except JobLost:
            self.lost = True
        except (BackendUnavailable, Unauthorized):
            with self.lock:
                self.buffer.insert(0, data)
                self.size += len(data)
        except Exception as e:
            print(f"log upload failed: {e}", file=sys.stderr)


def maxrss_mb(maxrss: int, platform: str = sys.platform) -> int:
    """ru_maxrss in MB: bytes on macOS, KB elsewhere"""
    return maxrss // (1024 * 1024 if platform == "darwin" else 1024)


def write_atomic(path: Path, data: str):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(data)
    os.replace(tmp, path)


class JobExecution(threading.Thread):
    """One job attempt: prepare, run the process, heartbeat, report. While the backend is
    unreachable the job keeps running; heartbeats, logs and finish are retried."""

    def __init__(
        self,
        assignment: dict,
        client: BackendClient,
        cache: Cache,
        sandbox: Sandbox,
        work_root: Path,
        on_done,
        log=print,
        gpus: list[int] | None = None,
        on_released=None,
    ):
        super().__init__(daemon=True, name=f"job-{assignment['job_id']}")
        self.a = assignment
        self.job_id = assignment["job_id"]
        self.attempt = assignment["attempt"]
        self.cpus = assignment["cpus"]
        self.memory = assignment["memory_mb"]
        self.gpus = gpus or []
        self.scratch_gb = assignment.get("scratch_gb", 0)
        lease = assignment.get("lease_s", 90)
        self.heartbeat_interval = max(0.2, min(HEARTBEAT_INTERVAL, lease / 3))
        self.client = client
        self.cache = cache
        self.sandbox = sandbox
        self.work = work_root / f"{self.job_id}-{self.attempt}"
        self.on_done = on_done
        self.on_released = on_released
        self.log = lambda msg: log(f"[job {self.job_id}] {msg}")
        self.process: subprocess.Popen | None = None
        self.cancelled = False
        self.timed_out = False
        self.lost = False
        self.shutting_down = False
        self.exited = threading.Event()
        self.next_heartbeat = 0.0
        self.peak_memory_mb: int | None = None
        self.pumps: list[LogPump] = []
        self.heartbeat_lock = threading.Lock()
        self.beat = StateLog(self.log, "heartbeat")

    def run(self):
        status, exit_code, message = "failed", None, ""
        started = time.time()
        try:
            status, exit_code, message = self._execute()
        except JobLost as e:
            self.log(f"lost: {e}")
            self.lost = True
            self._kill()
        except Exception as e:
            message = f"runner error: {e}\n{traceback.format_exc()}"
            self.log(message)
            self._kill()
        if self.on_released:
            self.on_released(self)
        if not self.lost:
            seconds = (time.time() - started) * (self.cpus + len(self.gpus))
            self._report(status, exit_code, message, seconds)
        self._cleanup()
        self.on_done(self)

    def _report(self, status, exit_code, message, resource_seconds):
        """Deliver finish, retrying with backoff; heartbeats keep the lease meanwhile"""
        delay = 0.5
        finish = StateLog(self.log, "finish")
        while True:
            for pump in self.pumps:
                pump.flush()
            try:
                result = self.client.job_finish(
                    self.job_id, self.attempt, status, exit_code, self.peak_memory_mb, message,
                    resource_seconds,
                )
                self.log(f"finished: {result.get('status')}")
                return
            except (JobLost, Unauthorized) as e:
                self.log(f"finish rejected: {e}")
                return
            except BackendUnavailable as e:
                finish.failed("unreachable", f"backend unavailable, finish is retried ({e})")
            except Exception as e:
                self.log(f"could not report result: {e}")
                return
            time.sleep(delay)
            delay = min(delay * 2, self.heartbeat_interval)
            try:
                self._heartbeat(force=True)
            except JobLost as e:
                self.log(f"finish rejected: {e}")
                return

    def _heartbeat(self, force=False, starting=False) -> bool:
        """Renew the lease and the job token; False if the backend is unreachable"""
        now = time.time()
        if not force and now < self.next_heartbeat:
            return True
        with self.heartbeat_lock:
            try:
                answer = self.client.job_heartbeat(self.job_id, self.attempt, self.peak_memory_mb, starting)
            except (BackendUnavailable, Unauthorized) as e:
                self.next_heartbeat = now + min(1.0, self.heartbeat_interval)
                self.beat.failed(failure_kind(e), f"heartbeat failed, job continues ({e})")
                return False
            self.beat.ok()
            self.next_heartbeat = now + self.heartbeat_interval
            if answer.get("token"):
                write_atomic(self.work / "job_token", answer["token"])
        if answer.get("cancel") and not self.cancelled:
            self.cancelled = True
            self.log("cancel requested")
            self._kill()
        return True

    def _keep_lease(self, prepared: threading.Event):
        """Heartbeats while images and layers are downloaded"""
        while not prepared.wait(self.heartbeat_interval):
            try:
                self._heartbeat(force=True, starting=True)
            except JobLost:
                self.lost = True
                return

    def job_env(self) -> dict:
        inside = self.sandbox.work_path(self.work)
        env = {
            "NGAPP_JOB_API": self.client.base,
            "NGAPP_JOB_ID": str(self.job_id),
            "NGAPP_JOB_ATTEMPT": str(self.attempt),
            "NGAPP_JOB_TOKEN_FILE": f"{inside}/job_token",
        }
        if self.gpus:
            env["CUDA_VISIBLE_DEVICES"] = ",".join(str(g) for g in self.gpus)
        # blob cache of the job's case, bound at the same path into the sandbox
        cache_dir = self.cache.job_dir(self.a["case_id"])
        if cache_dir is not None:
            env["NGAPP_JOB_CACHE_DIR"] = str(cache_dir)
        return env

    def _execute(self):
        self.work.mkdir(parents=True, exist_ok=True)
        (self.work / "tmp").mkdir(exist_ok=True)
        (self.work / "job.json").write_bytes(orjson.dumps(self.a["run_data"]))
        write_atomic(self.work / "job_token", self.a["token"])

        env = self.a["env"]
        image = None
        prepared = threading.Event()
        threading.Thread(target=self._keep_lease, args=(prepared,), daemon=True).start()
        try:
            if env.get("sif_hash") and self.sandbox.name != "none":
                image = self.cache.ensure_image(self.client, env, log=self.log)
            layer = self.cache.ensure_layer(self.client, self.a["layer"], log=self.log)
        finally:
            prepared.set()
        if self.lost:
            raise JobLost("lost during preparation")
        # the first heartbeat marks the job running; it must reach the backend
        while True:
            if self.shutting_down:
                return "returned", None, "runner shutting down"
            if self._heartbeat(force=True):
                break
            if self.beat.kind == "refused":
                raise JobLost("the backend refuses the runner")
            time.sleep(1)
        if self.cancelled:
            return "cancelled", None, "cancelled before start"
        if self.shutting_down:
            return "failed", None, "runner shut down"

        job_env = self.job_env()
        cmd = self.sandbox.command(image, self.work, layer, self.cpus, self.memory, job_env, self.gpus)
        self.log("start: " + " ".join(cmd[-4:]))
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self.work,
            env=self.sandbox.environment(layer, job_env),
            start_new_session=True,
        )
        self.pumps = pumps = [
            LogPump(self.process.stdout, lambda d: self.client.job_log(self.job_id, self.attempt, "stdout", d)),
            LogPump(self.process.stderr, lambda d: self.client.job_log(self.job_id, self.attempt, "stderr", d)),
        ]
        for p in pumps:
            p.start()

        # wait4 in a thread to keep the rusage (poll() would reap the child first)
        result = {}

        def waiter():
            _, status, rusage = os.wait4(self.process.pid, 0)
            result["code"] = os.waitstatus_to_exitcode(status)
            result["rusage"] = rusage
            self.exited.set()

        threading.Thread(target=waiter, daemon=True).start()

        deadline = time.time() + self.a["timeout"]
        stopped = False
        while not self.exited.wait(0.2):
            if any(p.lost for p in pumps):
                raise JobLost("log rejected")
            if self.shutting_down and not stopped:
                stopped = True
                self._kill()
            self._heartbeat()
            if time.time() > deadline and not self.timed_out:
                self.timed_out = True
                self.log("timeout")
                self._kill()

        exit_code = result["code"]
        self.process.returncode = exit_code
        self.peak_memory_mb = maxrss_mb(result["rusage"].ru_maxrss)
        for p in pumps:
            p.join(timeout=30)

        if self.cancelled:
            return "cancelled", exit_code, "cancelled"
        if self.shutting_down:
            return "failed", exit_code, "runner shut down"
        if self.timed_out:
            return "timed_out", exit_code, f"timeout after {self.a['timeout']} s"
        if exit_code == 0:
            return "succeeded", exit_code, ""
        if exit_code == 137 or exit_code == -9:
            return "failed", exit_code, f"killed (memory limit {self.memory} MB?)"
        return "failed", exit_code, f"exit code {exit_code}"

    def _kill(self):
        if self.process is None or self.exited.is_set():
            return
        try:
            os.killpg(self.process.pid, signal.SIGTERM)
            if not self.exited.wait(KILL_GRACE):
                os.killpg(self.process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

    def _cleanup(self):
        shutil.rmtree(self.work, ignore_errors=True)
