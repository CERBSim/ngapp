"""Helpers of the tests: a deterministic scheduler, an in-process runner and
direct access to a SQLiteServer"""

import heapq
import itertools

from ngapp.store import JobEndedError, StaleAttemptError


class _Handle:
    def __init__(self, fn):
        self.fn = fn
        self.cancelled = False

    def cancel(self):
        self.cancelled = True


class ManualScheduler:
    """Time advances only on request"""

    def __init__(self, start: float = 0.0):
        self.time = start
        self._queue = []
        self._counter = itertools.count()

    def now(self) -> float:
        return self.time

    def call_later(self, delay: float, fn) -> _Handle:
        handle = _Handle(fn)
        heapq.heappush(
            self._queue,
            (self.time + max(delay, 0.0), next(self._counter), handle),
        )
        return handle

    def run_until(self, t: float, max_calls: int = 1_000_000):
        calls = 0
        while self._queue and self._queue[0][0] <= t:
            due, _, handle = heapq.heappop(self._queue)
            self.time = max(self.time, due)
            if not handle.cancelled:
                handle.fn()
                calls += 1
                if calls >= max_calls:
                    raise RuntimeError("Too many scheduled calls")
        self.time = max(self.time, t)

    def advance(self, dt: float):
        self.run_until(self.time + dt)

    def run_pending(self):
        self.run_until(self.time)


def run_jobs(server, app_factory, *, scheduler=None, limit=None) -> list[int]:
    """Run queued jobs in this process, each in an app made by app_factory"""
    from ngapp.jobs import run_job

    done = []
    while limit is None or len(done) < limit:
        data = server.claim()
        if data is None:
            break
        job_id, attempt = data["job_id"], data["attempt"]
        client = server.job_client(job_id, attempt)
        server.heartbeat(job_id, attempt)
        try:
            run_job(client, data, app_factory=app_factory, scheduler=scheduler)
        except JobEndedError:
            try:
                server.finish(job_id, attempt, "failed", 3)
            except StaleAttemptError:
                pass
        except Exception as e:
            print("Job", job_id, "failed:", repr(e))
            server.finish(job_id, attempt, "failed", 1, repr(e))
        else:
            server.finish(job_id, attempt, "succeeded", 0)
        done.append(job_id)
    return done


def share(server, case_id: int, user: str, write: bool = True, event=True):
    """Share a case; without event the change is not announced"""
    with server._write() as c:
        c.execute(
            "INSERT OR REPLACE INTO case_share (case_id, user, write)"
            " VALUES (?, ?, ?)",
            (case_id, user, int(write)),
        )
        if event:
            server._emit(
                c, f"user:{user}", "cases.changed", {"case_id": case_id}
            )
    server._deliver()


def revision_count(server, case_id: int) -> int:
    with server._read() as c:
        return c.execute(
            "SELECT COUNT(*) FROM revision WHERE case_id = ? AND run_id IS NULL",
            (case_id,),
        ).fetchone()[0]


def job_count(server) -> int:
    with server._read() as c:
        return c.execute("SELECT COUNT(*) FROM job").fetchone()[0]


def stored_job(server, job_id: int):
    with server._read() as c:
        return server._job(c, job_id)


def stored_run(server, run_id: int):
    with server._read() as c:
        return server._run_row(c, run_id)
