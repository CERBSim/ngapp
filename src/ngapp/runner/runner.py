"""Runner main loop: long-poll for jobs while capacity is free, heartbeat, self-update"""

import os
import platform
import subprocess
import sys
import threading
import time
from pathlib import Path

import httpx

from .. import __version__
from .cache import Cache
from .client import BackendClient, BackendUnavailable, Unauthorized
from .execute import JobExecution, Sandbox, StateLog, failure_kind

HEARTBEAT_INTERVAL = 30
BACKOFF_MAX = 10
ANNOUNCE_TIMEOUT = 5
STOP_WAIT = 20  # seconds the jobs have at shutdown to end and report
PRUNE_INTERVAL = 300  # seconds between two evictions of the caches besides those at job ends


def version_tuple(v: str) -> tuple:
    parts = []
    for p in v.split("."):
        digits = "".join(c for c in p if c.isdigit())
        if not digits:
            break
        parts.append(int(digits))
    return tuple(parts)


class Runner:
    def __init__(
        self,
        client: BackendClient,
        cache: Cache,
        sandbox: Sandbox,
        cpus: int,
        memory: int,
        name: str,
        work_root: Path,
        poll_wait: int = 30,
        self_update: bool = True,
        cache_size: int = 0,
        log=print,
        gpus: int = 0,
        gpu_type: str = "",
        scratch_gb: int = 0,
        heartbeat_interval: float = HEARTBEAT_INTERVAL,
    ):
        self.client = client
        self.cache = cache
        self.sandbox = sandbox
        self.cpus = cpus
        self.memory = memory
        self.gpus = gpus
        self.gpu_type = gpu_type
        self.scratch_gb = scratch_gb
        self.heartbeat_interval = heartbeat_interval
        self.name = name
        self.work_root = work_root
        self.poll_wait = poll_wait
        self.self_update = self_update
        self.cache_size = cache_size
        self.log = log
        self.jobs: dict[int, JobExecution] = {}  # holding resources
        self.reporting: dict[int, JobExecution] = {}  # process ended, finish not delivered yet
        self.lock = threading.Lock()
        self.stop = threading.Event()
        self.wake = threading.Event()  # a job ended
        self.stopping = threading.Event()  # announce the shutdown to the backend
        self.announced = threading.Event()
        self.update_to: str | None = None
        self.last_prune = time.monotonic()

    # capacity: the backend claims from the reported totals minus the runner's jobs it knows;
    # free counts the processes that still run (a job whose finish is not answered yet still
    # counts on the backend until the finish)

    def _holding(self) -> list[JobExecution]:
        with self.lock:
            return list(self.jobs.values())

    def free(self) -> tuple[int, int]:
        jobs = self._holding()
        cpus = self.cpus - sum(j.cpus for j in jobs)
        memory = self.memory - sum(j.memory for j in jobs)
        return cpus, memory

    def free_gpus(self) -> list[int]:
        used = {g for j in self._holding() for g in j.gpus}
        return [g for g in range(self.gpus) if g not in used]

    def free_scratch(self) -> int:
        return self.scratch_gb - sum(j.scratch_gb for j in self._holding())

    def state(self) -> dict:
        free_cpus, free_memory = self.free()
        return {
            "cpus": self.cpus,
            "memory": self.memory,
            "free_cpus": free_cpus,
            "free_memory": free_memory,
            "gpus": self.gpus,
            "free_gpus": len(self.free_gpus()),
            "gpu_type": self.gpu_type,
            "scratch_gb": self.scratch_gb,
            "free_scratch_gb": self.free_scratch(),
            "cached_envs": self.cache.cached_envs(),
            "sandbox": self.sandbox.name,
            "version": __version__,
            "hostname": platform.node(),
        }

    def running_jobs(self) -> list[int]:
        """Jobs the backend must not consider lost: running or still reporting"""
        with self.lock:
            return list(self.jobs.keys() | self.reporting.keys())

    # loop

    def run(self):
        self.log(
            f"runner '{self.name}' ({__version__}) connecting to {self.client.base}, "
            f"{self.cpus} cpus, {self.memory} MB, sandbox {self.sandbox.name}"
        )
        try:
            self.cache.start(self.log)
        except Exception as e:
            self.log(f"cache cleanup failed: {e}")
        self._prune()
        threading.Thread(target=self._heartbeat_loop, daemon=True).start()
        threading.Thread(target=self._announcer, daemon=True).start()
        backoff = 1
        requests = StateLog(self.log, "job requests")
        while not self.stop.is_set():
            free_cpus, free_memory = self.free()
            if free_cpus < 1 or free_memory < 1 or self.update_to:
                # full: poll again as soon as a job ends
                self.wake.wait(1)
                self.wake.clear()
                self._maybe_update()
                continue
            try:
                assignment = self.client.request_job(self.state(), self.poll_wait)
                backoff = 1
                requests.ok()
            except (httpx.HTTPError, OSError, BackendUnavailable, Unauthorized) as e:
                if isinstance(e, Unauthorized):
                    message = f"backend refuses the runner, no new jobs ({e})"
                else:
                    message = f"backend not reachable ({e})"
                requests.failed(failure_kind(e), f"{message}, retrying every {BACKOFF_MAX} s at most")
                self.stop.wait(backoff)
                backoff = min(backoff * 2, BACKOFF_MAX)
                continue
            if assignment is None:
                continue
            if self.stop.is_set():
                # after the announcement, so that the backend does not count the return
                self.stopping.set()
                self.announced.wait(ANNOUNCE_TIMEOUT + 1)
                self._give_back(assignment, "runner shutting down")
                break
            free_cpus, free_memory = self.free()
            gpus = self.free_gpus()[: assignment.get("gpus", 0)]
            if (
                assignment["cpus"] > free_cpus
                or assignment["memory_mb"] > free_memory
                or len(gpus) < assignment.get("gpus", 0)
            ):
                self._give_back(assignment, "runner capacity changed")
                self.wake.wait(1)
                self.wake.clear()
                continue
            job = JobExecution(
                assignment,
                self.client,
                self.cache,
                self.sandbox,
                self.work_root,
                self._job_done,
                log=self.log,
                gpus=gpus,
                on_released=self._job_released,
            )
            with self.lock:
                self.jobs[job.job_id] = job
            # what the job uses stays in the caches until its process ended
            self.cache.pin(
                (job.job_id, job.attempt),
                images=[assignment["env"].get("sif_hash")],
                layers=[assignment["layer"]["hash"]],
                cases=[assignment["case_id"]],
            )
            self.log(
                f"[job {job.job_id}] assigned ({job.cpus} cpus, {job.memory} MB, "
                f"{len(gpus)} gpus, attempt {job.attempt})"
            )
            job.start()
        self._stop_jobs()
        self.log("runner stopped")

    def shutdown(self):
        """Stop taking jobs, also from a signal handler while run() waits in its long poll: the
        announcement of the shutdown ends the poll, then run() ends the jobs"""
        self.stop.set()
        self.stopping.set()
        self.wake.set()

    def _announcer(self):
        self.stopping.wait()
        try:
            state, jobs = self.state(), self.running_jobs()
            self.client.heartbeat(state, jobs, stopping=True, timeout=ANNOUNCE_TIMEOUT)
        except Exception as e:
            self.log(f"could not announce the shutdown to the backend: {e}")
        self.announced.set()

    def _stop_jobs(self):
        """After the long poll ended: the shutdown is announced first (the backend claims nothing
        more for the runner), then the jobs end. Jobs that have not started are given back,
        running ones are killed and reported (the backend requeues them if their policy allows)"""
        self.stop.set()
        self.stopping.set()
        self.announced.wait(ANNOUNCE_TIMEOUT + 1)
        with self.lock:
            jobs = list(self.jobs.values()) + list(self.reporting.values())
        for job in jobs:
            job.shutting_down = True
        deadline = time.monotonic() + STOP_WAIT
        for job in jobs:
            job.join(max(0.0, deadline - time.monotonic()))
        if any(job.is_alive() for job in jobs):
            self.log("jobs still reporting, the backend handles them as lost")

    def _give_back(self, assignment: dict, reason: str):
        """An assignment the runner does not start goes back to the queue; the backend counts it as
        a start unless the runner announced its shutdown before"""
        job_id = assignment["job_id"]
        self.log(f"[job {job_id}] {reason}, giving it back")
        try:
            self.client.job_finish(job_id, assignment["attempt"], "returned", message=reason)
        except Exception as e:
            self.log(f"[job {job_id}] could not give it back: {e}")

    def _job_released(self, job: JobExecution):
        """The process ended: free its resources, keep reporting the job until finish arrives"""
        self.cache.unpin((job.job_id, job.attempt))
        with self.lock:
            if self.jobs.get(job.job_id) is job:
                del self.jobs[job.job_id]
            self.reporting[job.job_id] = job
        self.wake.set()

    def _job_done(self, job: JobExecution):
        self.cache.unpin((job.job_id, job.attempt))
        with self.lock:
            if self.jobs.get(job.job_id) is job:
                del self.jobs[job.job_id]
            if self.reporting.get(job.job_id) is job:
                del self.reporting[job.job_id]
        self.wake.set()
        self.log(f"[job {job.job_id}] done")
        self._prune()

    def _prune(self):
        """Evict images and layers above cache_size and job blobs above their limit"""
        self.last_prune = time.monotonic()
        try:
            if self.cache_size:
                self.cache.prune(self.cache_size, log=self.log)
            self.cache.prune_jobs(log=self.log)
        except Exception as e:
            self.log(f"cache prune failed: {e}")

    def _heartbeat_loop(self):
        beat = StateLog(self.log, "runner heartbeat")
        while not self.stop.is_set():
            try:
                response = self.client.heartbeat(self.state(), self.running_jobs())
                required = response.get("required_version") or ""
                if required and version_tuple(required) > version_tuple(__version__) and self.self_update:
                    self.update_to = required
                if response.get("shutdown"):
                    self.log("backend asked us to shut down")
                    self.shutdown()
                beat.ok()
            except Exception as e:
                beat.failed(failure_kind(e), f"heartbeat failed: {e}")
            if time.monotonic() - self.last_prune > PRUNE_INTERVAL:
                self._prune()
            self.stop.wait(self.heartbeat_interval)

    def _maybe_update(self):
        if not self.update_to or self.running_jobs():
            return
        self.log(f"updating ngapp {__version__} -> {self.update_to}")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "-q", "--upgrade", f"ngapp[runner]=={self.update_to}"]
            )
        except subprocess.CalledProcessError as e:
            self.log(f"update failed: {e}")
            self.update_to = None
            return
        os.execv(sys.executable, [sys.executable, "-m", "ngapp.runner", *sys.argv[1:]])
