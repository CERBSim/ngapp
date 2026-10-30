"""Compute functions, jobs and runs on the SQLite store: the test runs the function in-process with a JobSession on the job store adapter;
the checkpoint schedule with an injected clock"""

import numpy as np
import pytest

from ngapp.app import App, AppConfig
from ngapp.components import QInput
from ngapp.components.basecomponent import Component
from ngapp.jobs import (
    JobHandle,
    JobSession,
    checkpoint_interval,
    compute,
    progress,
)
from ngapp.state import CaseSession
from ngapp.store.job import JobStore
from ngapp.store.tree import flatten
from ngapp.utils import EnvironmentType, compute_node, set_environment
from helpers import (
    ManualScheduler,
    run_jobs as run_queued,
    stored_job,
    stored_run,
)

HOOKS = {}


def hook(name, *args):
    f = HOOKS.get(name)
    if f is not None:
        f(*args)


class Mesher(Component):
    def __init__(self):
        super().__init__("div", id="mesher")
        self.maxh = QInput(id="maxh", ui_model_value=0.25)
        self.result = QInput(id="result", ui_label="no mesh")
        self.ui_children = [self.maxh, self.result]
        self.state.mesh = None

    @compute(cpus=2, memory="1G", timeout=600)
    def generate(self, order=1):
        geometry = self.app.state.geometry
        n = int(round(1 / self.maxh.ui_model_value)) * 5000
        self.result.ui_label = "meshing"
        hook("generate", self)
        self.state.mesh = np.arange(n, dtype=np.float64) * order + geometry[0]
        self.state.n = n
        self.result.ui_label = f"{n} elements"

    @compute(restart="checkpoint", max_attempts=2)
    def simulate(self, steps=5, fail_at=None):
        done = len(self.state.list("steps"))
        for i in range(done, steps):
            if i == fail_at:
                raise RuntimeError(f"failed at step {i}")
            self.state.list("steps").append(i)
            hook("step", self, i)
            progress((i + 1) / steps, f"step {i}")
        self.state.total = sum(self.state.list("steps"))

    @compute(merge=False)
    def preview(self):
        self.state.preview = 42
        self.result.ui_label = "preview"

    @compute_node
    def legacy(self):
        self.state.legacy = "done"

    @compute
    def extend(self):
        self.app.state.list("log").append("job")


class JobApp(App):
    def __init__(self):
        super().__init__()
        self.mesher = Mesher()
        self.component = self.mesher


AppConfig(JobApp, name="jobs", version="1")


@pytest.fixture(autouse=True)
def env():
    env = set_environment(EnvironmentType.STANDALONE, have_backend=False)
    env.frontend.update_component = lambda *a, **k: None
    env.data_layer = True
    HOOKS.clear()
    yield env
    env.data_layer = False
    HOOKS.clear()


def create(server, sched, user="alice"):
    app = JobApp()
    app.state.geometry = np.full(8000, 2.0)  # a blob above the inline limit
    session = CaseSession.create(
        app, server.client(user), app_id=1, name="case", scheduler=sched
    )
    return app, session


def open_case(server, sched, case_id, user="alice"):
    app = JobApp()
    session = CaseSession.open(
        app, server.client(user), case_id, scheduler=sched
    )
    return app, session


def run_jobs(server, sched, job_sched, **kw):
    done = run_queued(server, JobApp, scheduler=job_sched, **kw)
    sched.run_pending()
    return done


def stored(session, revision=None):
    return flatten(session.store.state(session.case_id, revision))


def test_checkpoint_interval():
    assert checkpoint_interval(0) == 1.5
    assert checkpoint_interval(90) == 1.5
    assert checkpoint_interval(600) == 10
    assert checkpoint_interval(3600) == 60
    assert checkpoint_interval(10 * 3600) == 60
    assert checkpoint_interval(0, quiet=2) == 6
    assert checkpoint_interval(1800, quiet=3) == 60


def test_checkpoint_schedule(server, sched):
    app, session = create(server, sched)
    job = app.mesher.simulate(steps=3)
    data = server.claim()
    server.heartbeat(data["job_id"], data["attempt"])
    client = server.job_client(data["job_id"], data["attempt"])
    js_sched = ManualScheduler(1000.0)
    japp = JobApp()
    js = JobSession.open(
        japp, JobStore(client), data["case_id"], scheduler=js_sched
    )
    tips = []

    def tip_changed():
        tips.append(stored_run(server, job.run_id).tip_revision)
        return len(set(tips)) > 1 and tips[-1] != tips[-2]

    tip_changed()
    js_sched.advance(0.1)
    japp.mesher.result.ui_label = "starting"
    js_sched.advance(1.3)
    assert not tip_changed() and client.seq == 0
    js_sched.advance(0.2)  # 1.5 s after the start
    assert tip_changed() and client.seq == 1 and js.checkpoints == 1
    assert stored(session)[("result", "ui", "label")] == "starting"
    # a burst of changes within the interval makes one checkpoint
    for i in range(5):
        japp.mesher.state.i = i
        js_sched.advance(0.2)
    assert js.checkpoints == 1
    js_sched.advance(0.5)  # 1.5 s after the last checkpoint
    assert js.checkpoints == 2 and client.seq == 2
    js_sched.advance(1.5)
    assert js.checkpoints == 2
    # quiet: the checks find nothing and their interval doubles
    assert js.quiet >= 1 and js._due - js_sched.now() > 1.5
    # in-place mutation is found by a check
    japp.mesher.state.arr = [1, 2]
    js_sched.advance(1.5)
    n = js.checkpoints
    japp.mesher.state.arr.append(3)
    js_sched.advance(60)
    assert js.checkpoints == n + 1
    # an old job checkpoints at most once per minute
    js_sched.advance(3600)
    js.checkpoint()
    t0 = js_sched.now()
    commits = []
    for i in range(120):
        japp.mesher.state.i = 100 + i
        js_sched.advance(1)
        commits.append(js.checkpoints)
    assert commits[-1] - commits[0] == 2
    assert js.last_checkpoint - t0 >= 60
    # progress checkpoints at once if the last one is older than the minimum
    japp.mesher.state.i = -1
    js_sched.advance(2)
    n = js.checkpoints
    japp.mesher.state.i = -2
    js.progress(0.5, "half")
    assert js.checkpoints == n + 1
    japp.mesher.state.i = -3
    js.progress(0.6, "more")
    assert js.checkpoints == n + 1  # younger than the minimum interval
    assert server.job_events("alice", job.id)[-1]["kind"] == "progress"
    js.finish()
    run = stored_run(server, job.run_id)
    assert (
        run.closed
        and stored(session, run.tip_revision)[("mesher", "state", "i")] == -3
    )
    js.close()


def test_checkpoints_reach_the_case(server, sched, job_sched):
    """With merge (the default) every checkpoint of a job changes the case:
    the app shows intermediate results"""
    app, session = create(server, sched)
    job = app.mesher.simulate(steps=4)
    shown = []

    def step(comp, i):
        job_sched.advance(1.6)  # a checkpoint with step i
        sched.run_pending()
        shown.append(list(app.mesher.state.list("steps")))

    HOOKS["step"] = step
    run_jobs(server, sched, job_sched)
    assert job.status == "succeeded"
    assert shown == [[0], [0, 1], [0, 1, 2], [0, 1, 2, 3]]
    assert app.mesher.state.total == 6
    assert stored(session)[("mesher", "state", "total")] == 6


def test_without_merge_the_case_is_not_changed(server, sched, job_sched):
    """A job of a function with merge=False changes only its run"""
    app, session = create(server, sched)
    job = app.mesher.preview()
    run_jobs(server, sched, job_sched)
    assert job.status == "succeeded"
    assert "preview" not in app.mesher.state
    assert app.mesher.result.ui_label == "no mesh"
    run = app.runs(app.mesher.preview).latest
    assert run.id == job.run_id
    data = flatten(run.state())
    assert data[("mesher", "state", "preview")] == 42
    assert data[("result", "ui", "label")] == "preview"


def test_failure_keeps_checkpoints(server, sched, job_sched):
    """The run of a failed job keeps its checkpoints"""
    app, session = create(server, sched)
    job = app.mesher.simulate(steps=4, fail_at=2)
    HOOKS["step"] = lambda comp, i: job_sched.advance(1.1)
    run_jobs(server, sched, job_sched)
    # a failed attempt with max_attempts=2 is retried once, then fails
    assert job.status == "failed" and stored_job(server, job.id).attempt == 2
    [run] = app.runs(app.mesher.simulate)
    assert run.status == "failed"
    assert list(app.mesher.state.list("steps")) == [0, 1]
    steps = flatten(run.state())[("mesher", "state", "steps")]
    assert list(steps.items) == [0, 1]


def test_compute_node_alias_and_list_conversion(server, sched, job_sched):
    app, session = create(server, sched)
    app.state.log = ["user"]  # a plain list value
    job = app.mesher.legacy()
    assert isinstance(job, JobHandle)
    extend = app.mesher.extend()
    run_jobs(server, sched, job_sched)
    assert job.status == "succeeded" and extend.status == "succeeded"
    assert app.mesher.state.legacy == "done"
    # appending to a plain list of the input converts it into a sequence
    assert list(app.app.state.list("log")) == ["user", "job"]
    tip = stored(session, stored_run(server, extend.run_id).tip_revision)
    assert list(tip[("__app__", "state", "log")].items) == ["user", "job"]
    # the user's own appends after the job's
    app.state.list("log").append("user 2")
    app.commit()
    assert list(stored(session)[("__app__", "state", "log")].items) == [
        "user",
        "job",
        "user 2",
    ]


def test_compute_outside_a_case_runs_locally(server, sched):
    """Without a case store compute keeps the local behaviour"""
    app = JobApp()
    app.state.geometry = np.full(10, 1.0)
    result = app.mesher.legacy()
    assert app.mesher.state.legacy == "done" and not isinstance(
        result, JobHandle
    )
    with pytest.raises(NotImplementedError):
        compute(parallel=True)
    progress(0.5)  # no job: nothing happens
