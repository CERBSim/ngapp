"""Local job runners of the SQLite store (local app mode)

A runner claims queued jobs of the database one at a time and runs each in a
process of its own (python -m ngapp.cli.run_job job.json) whose job client
works directly on the database (SQLiteJobClient, NGAPP_JOB_DB). Like a server
runner it marks the job running, kills the process on a cancel request or at
the deadline, stores its output as log events and reports the end of the
attempt; the store decides the job's state. The claims limit the jobs running
at once (max_jobs); a runner ends when no job is left.

spawn_runner starts a runner as a detached process, so jobs survive the end of
the app. A runner that dies leaves its job assigned or running until
SQLiteServer.recover() finds its process gone.
"""

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

from .types import CaseDeletedError, JobEndedError, StoreError

KILL_GRACE = 5.0
EXIT_ENDED = 3
LOG_FLUSH = 64 * 1024

_children: list[subprocess.Popen] = []


def _python_path(sys_path) -> str:
    paths = [p for p in [*sys_path, os.environ.get("PYTHONPATH", "")] if p]
    return os.pathsep.join(dict.fromkeys(paths))


def spawn_runner(db_path, max_jobs: int) -> subprocess.Popen:
    """Start a detached runner process for the database"""
    global _children
    _children = [p for p in _children if p.poll() is None]
    db_path = Path(db_path)
    work = db_path.with_name(db_path.stem + ".jobs")
    work.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PYTHONPATH=_python_path(sys.path))
    with open(work / "runner.log", "ab") as log:
        proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "ngapp.store.local_jobs",
                str(db_path),
                "--max-jobs",
                str(max_jobs),
            ],
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            env=env,
            start_new_session=True,
        )
    _children.append(proc)
    return proc


class _Output:
    """Lines of one output stream of the job process, sent in batches"""

    def __init__(self, stream, name):
        self.name = name
        self.lines: list[str] = []
        self.size = 0
        self.last = ""
        self.lock = threading.Lock()
        self.thread = threading.Thread(
            target=self._read, args=(stream,), daemon=True
        )
        self.thread.start()

    def _read(self, stream):
        for raw in iter(stream.readline, b""):
            line = raw.decode(errors="replace")
            with self.lock:
                self.lines.append(line)
                self.size += len(line)
                if line.strip():
                    self.last = line.strip()
        stream.close()

    def take(self, force=False) -> str:
        with self.lock:
            if not self.lines or (not force and self.size < LOG_FLUSH):
                return ""
            data, self.lines, self.size = "".join(self.lines), [], 0
            return data


class LocalRunner:
    def __init__(
        self,
        server,
        max_jobs: int = 2,
        *,
        interval: float = 0.2,
        kill_grace: float = KILL_GRACE,
    ):
        from .sqlite import _process_tag

        self.server = server
        self.max_jobs = max_jobs
        self.interval = interval
        self.kill_grace = kill_grace
        self.tag = _process_tag()
        self.processes: dict[int, subprocess.Popen] = {}
        self._stop = threading.Event()

    def run(self):
        while not self._stop.is_set():
            data = self.server.claim(runner=self.tag, limit=self.max_jobs)
            if data is None:
                return
            try:
                self.execute(data)
            except Exception as e:
                print(
                    f"Local runner: job {data['job_id']} failed: {e!r}",
                    flush=True,
                )
                self._finish(data, "failed", None, f"runner error: {e!r}")

    def _finish(self, data, status, exit_code, message):
        try:
            return self.server.finish(
                data["job_id"], data["attempt"], status, exit_code, message
            )
        except JobEndedError:
            return None

    def _kill(self, proc):
        if proc.poll() is not None:
            return
        try:
            if hasattr(os, "killpg"):
                os.killpg(proc.pid, signal.SIGTERM)
            else:
                proc.terminate()
            try:
                proc.wait(self.kill_grace)
            except subprocess.TimeoutExpired:
                if hasattr(os, "killpg"):
                    os.killpg(proc.pid, signal.SIGKILL)
                else:
                    proc.kill()
                proc.wait()
        except ProcessLookupError:
            pass

    def _log(self, data, outputs, force=False):
        for out in outputs:
            text = out.take(force)
            if text:
                try:
                    self.server.job_log(
                        data["job_id"], data["attempt"], out.name, text
                    )
                except StoreError:
                    pass

    def execute(self, data: dict):
        job_id, attempt = data["job_id"], data["attempt"]
        try:
            if self.server.heartbeat(job_id, attempt)["cancel"]:
                self._finish(data, "cancelled", None, "cancelled before start")
                return
        except (JobEndedError, CaseDeletedError):
            return
        work = self.server.work_dir / f"{job_id}-{attempt}"
        work.mkdir(parents=True, exist_ok=True)
        (work / "job.json").write_text(json.dumps(data))
        env = dict(
            os.environ,
            NGAPP_JOB_DB=str(self.server.path),
            NGAPP_JOB_ID=str(job_id),
            NGAPP_JOB_ATTEMPT=str(attempt),
            PYTHONPATH=_python_path(data.get("sys_path") or []),
        )
        cwd = data.get("cwd")
        if not cwd or not os.path.isdir(cwd):
            cwd = None
        proc = subprocess.Popen(
            [sys.executable, "-m", "ngapp.cli.run_job", str(work / "job.json")],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            env=env,
            start_new_session=True,
        )
        self.processes[job_id] = proc
        outputs = [
            _Output(proc.stdout, "stdout"),
            _Output(proc.stderr, "stderr"),
        ]
        timeout = data.get("timeout")
        deadline = time.monotonic() + timeout if timeout else None
        status = message = None
        try:
            while proc.poll() is None:
                try:
                    proc.wait(self.interval)
                except subprocess.TimeoutExpired:
                    pass
                else:
                    break
                self._log(data, outputs)
                try:
                    cancel = self.server.cancel_requested(job_id, attempt)
                except CaseDeletedError:
                    cancel = True
                except JobEndedError:
                    status, message = "lost", "the attempt ended"
                    self._kill(proc)
                    break
                if cancel or self._stop.is_set():
                    status = "cancelled" if cancel else "failed"
                    message = "cancelled" if cancel else "runner stopped"
                    self._kill(proc)
                    break
                if deadline is not None and time.monotonic() > deadline:
                    status, message = "timed_out", f"timeout after {timeout} s"
                    self._kill(proc)
                    break
            code = proc.wait()
            for out in outputs:
                out.thread.join(timeout=10)
            self._log(data, outputs, force=True)
        finally:
            self.processes.pop(job_id, None)
            shutil.rmtree(work, ignore_errors=True)
        if status == "lost":
            return
        if status is None:
            status = "succeeded" if code == 0 else "failed"
            if code == EXIT_ENDED:
                message = "the attempt ended"
            elif code < 0:
                message = f"killed by signal {-code}"
            elif code:
                last = outputs[1].last or outputs[0].last
                message = f"exit code {code}" + (
                    f": {last[-500:]}" if last else ""
                )
        self._finish(data, status, code, message or "")


def main(argv=None):
    from .sqlite import SQLiteServer

    parser = argparse.ArgumentParser(
        description="Run the queued jobs of a local ngapp case database"
    )
    parser.add_argument("database")
    parser.add_argument("--max-jobs", type=int, default=2)
    args = parser.parse_args(argv)
    server = SQLiteServer(args.database, poll_interval=None)
    try:
        server.recover()
        LocalRunner(server, args.max_jobs).run()
    finally:
        server.close()


if __name__ == "__main__":
    main()
