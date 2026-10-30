"""Local jobs of the SQLite store end to end: a runner claims the job, runs it
in a process of its own that works on the database, and the app follows its
status through the events of the database"""

import os
import signal
import sys
import threading
import time

import numpy as np
import pytest

from local_jobs_app import JobsApp
from ngapp.jobs import JobHandle
from ngapp.state import CaseSession
from ngapp.store import Op
from ngapp.store.local_jobs import LocalRunner, spawn_runner
from ngapp.store.sqlite import SQLiteServer, process_alive
from ngapp.store.tree import flatten
from ngapp.utils import EnvironmentType, set_environment
from helpers import run_jobs as run_queued


@pytest.fixture(autouse=True)
def env():
    env = set_environment(EnvironmentType.STANDALONE, have_backend=False)
    env.frontend.update_component = lambda *a, **k: None
    env.data_layer = True
    yield env
    env.data_layer = False


def job_data():
    cfg = JobsApp._config
    return {
        "app": cfg.model_dump(
            include={"id", "name", "version", "python_class"}
        ),
        "sys_path": [p for p in sys.path if p],
        "cwd": os.getcwd(),
    }


class ThreadedServer(SQLiteServer):
    """Local jobs in runner threads of the test process"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.runner = None
        self.threads = []

    def start_jobs(self):
        if self.jobs is None:
            return
        self.recover()
        queued, active = self.pending_jobs()
        if not queued or active >= self.max_jobs:
            return
        if self.runner is None:
            self.runner = LocalRunner(self, self.max_jobs)
        self.threads = [t for t in self.threads if t.is_alive()]
        thread = threading.Thread(target=self.runner.run, daemon=True)
        self.threads.append(thread)
        thread.start()

    def close(self):
        if self.runner is not None:
            self.runner._stop.set()
            for proc in list(self.runner.processes.values()):
                self.runner._kill(proc)
            for thread in self.threads:
                thread.join(timeout=self.runner.kill_grace + 5)
        super().close()


@pytest.fixture
def make_server(tmp_path):
    servers = []

    def make(jobs="thread", **kw):
        cls = ThreadedServer if jobs == "thread" else SQLiteServer
        server = cls(
            tmp_path / "cases.sqlite",
            poll_interval=None,
            jobs=jobs,
            job_data=job_data(),
            **kw,
        )
        servers.append(server)
        return server

    yield make
    for server in servers:
        server.close()


@pytest.fixture
def server(make_server):
    return make_server()


def create(server, sched):
    app = JobsApp()
    app.state.geometry = np.full(8000, 2.0)  # a blob above the inline limit
    session = CaseSession.create(
        app, server.client("local"), app_id=1, name="case", scheduler=sched
    )
    return app, session


def wait(condition, server, sched, timeout=60.0):
    end = time.monotonic() + timeout
    while True:
        server.poll()
        sched.run_pending()
        if condition():
            return
        if time.monotonic() > end:
            raise AssertionError("condition not reached")
        time.sleep(0.05)


def stored(session, revision=None):
    return flatten(session.store.state(session.case_id, revision))


def test_job_in_a_process(server, sched):
    """Input blob, state blob, final commit merged into the case line;
    identical submissions and the outdated marker"""
    app, session = create(server, sched)
    app.solver.maxh.ui_model_value = 0.5
    statuses = []
    job = app.solver.mesh(order=2)
    job.on_status(statuses.append)
    assert isinstance(job, JobHandle) and job.status == "queued"
    again = app.solver.mesh(order=2)
    assert again.id == job.id
    wait(lambda: job.done, server, sched)
    assert job.status == "succeeded", server.job("local", job.id).message
    assert statuses[-1] == "succeeded" and "running" in statuses
    mesh = app.solver.state.mesh
    assert mesh.shape == (10000,) and mesh[1] == 4.0 and mesh[0] == 2.0
    assert app.solver.state.n == 10000
    assert app.solver.result.ui_label == "10000 elements"
    head = stored(session)
    assert head[("result", "ui", "label")] == "10000 elements"
    assert head[("solver", "state", "mesh")]["$blob"].startswith("sha256:")
    run = job.run
    assert run.status == "succeeded" and not run.outdated
    tip = stored(session, run.tip_revision)
    assert tip[("solver", "state", "mesh")]["$blob"].startswith("sha256:")
    # The run is reused, no job is started
    reused = app.solver.mesh(order=2)
    assert (
        reused.reused and reused.id == job.id and reused.status == "succeeded"
    )
    # An input the job read changes
    app.solver.maxh.ui_model_value = 1.0
    app.commit()
    [run] = app.runs(app.solver.mesh)
    assert run.outdated
    events = server.job_events("local", job.id)
    assert any(e["kind"] == "log" for e in events)


def test_checkpoints_cancel_and_crash(server, sched):
    """Checkpoints reach the run branch while the job runs; a cancel kills the
    process; a crashed process ends its job as failed and keeps its
    checkpoints"""
    app, session = create(server, sched)
    job = app.solver.steps(n=200, delay=0.3)
    wait(lambda: job.status == "running", server, sched)
    wait(lambda: len(app.solver.state.list("log")) >= 4, server, sched)
    assert job.progress[0] is not None and job.progress[1].startswith("step")
    job.cancel()
    wait(lambda: job.done, server, sched)
    assert job.status == "cancelled"
    [run] = app.runs(app.solver.steps)
    assert run.status == "cancelled"
    shown = list(
        stored(session, run.tip_revision)[("solver", "state", "log")].items
    )
    assert shown[:4] == [0, 1, 2, 3] and len(shown) < 200

    # the cancelled job's checkpoints are in the case; the next jobs start
    # without them
    assert list(app.solver.state.list("log"))[:4] == [0, 1, 2, 3]
    app.solver.state.delete("log")
    crash = app.solver.steps(n=6, delay=0.6, crash_at=4)
    wait(lambda: crash.done, server, sched)
    info = server.job("local", crash.id)
    assert crash.status == "failed" and info.exit_code == 9
    run = crash.run
    assert run.status == "failed"
    sched.run_pending()
    assert list(app.solver.state.list("log"))[:2] == [0, 1]

    app.solver.state.delete("log")
    failed = app.solver.steps(n=3, fail_at=1)
    wait(lambda: failed.done, server, sched)
    assert failed.status == "failed"
    assert "failed at step 1" in server.job("local", failed.id).message

    slow = app.solver.slow()
    wait(lambda: slow.done, server, sched)
    assert slow.status == "timed_out"


def test_runner_process_and_lost_runner(make_server, sched):
    """A detached runner process runs the job; a runner that dies leaves the
    job until recover() finds its process gone"""
    server = make_server(jobs="process")
    app, session = create(server, sched)
    job = app.solver.steps(n=3)
    wait(lambda: job.done, server, sched)
    assert job.status == "succeeded"

    server.jobs = None
    long = app.solver.steps(n=100, delay=0.3)
    runner = spawn_runner(server.path, 1)
    wait(lambda: long.status == "running", server, sched)
    with server._read() as c:
        tag = c.execute(
            "SELECT runner FROM job WHERE id = ?", (long.id,)
        ).fetchone()[0]
    assert process_alive(tag) and tag.startswith(f"{runner.pid}:")
    os.killpg(runner.pid, signal.SIGKILL)
    runner.wait()
    assert not process_alive(tag)
    assert server.recover() == [long.id]
    wait(lambda: long.done, server, sched)
    assert (
        long.status == "failed"
        and server.job("local", long.id).message == "runner lost"
    )


def test_fork_keeps_the_run_and_its_times(make_server, sched):
    """Runs carry their times; the case made from a run has
    a copy of the run, outdated once its inputs change"""
    server = make_server(jobs=None)
    app, session = create(server, sched)
    job = app.solver.steps(n=3)
    assert run_queued(server, JobsApp) == [job.id]
    sched.run_pending()
    [run] = app.runs(app.solver.steps)
    extra = run.info.extra
    assert extra["created_at"] and extra["started_at"] and extra["finished_at"]
    store = session.store
    fork = store.copy_case(session.case_id, run_id=run.id, name="fork")
    [copied] = store.runs(fork.id)
    assert copied.id != run.id and copied.status == "succeeded"
    assert not copied.outdated
    assert copied.extra["started_at"]
    head = store.case(fork.id).head
    store.commit(fork.id, head, [Op("set", ("solver", "input", "x"), 3)])
    [copied] = store.runs(fork.id)
    assert copied.outdated
    assert not store.runs(session.case_id)[0].outdated
