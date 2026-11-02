"""Job and run components on the SQLite store, driven by the session's
events only: the jobs run in-process (helpers.run_jobs) or the test plays
the runner step by step. Covers the status sequence with queue position,
progress, cancel, failure message and attempt, reuse, a job of another tab,
the runs list with fork, keep and the outdated marker, and the compatibility
JobComponent."""

import logging

import pytest

from ngapp.app import App, AppConfig
from ngapp.components import (
    Div,
    JobComponent,
    JobControl,
    OutdatedMarker,
    QInput,
    RunsView,
)
from ngapp.components.basecomponent import Component
from ngapp.components.job_components import run_time
from ngapp.jobs import JobHandle, compute, current_job, progress
from ngapp.state import CaseSession
from ngapp.store.tree import flatten
from ngapp.utils import EnvironmentType, compute_node, set_environment
from helpers import (
    job_count,
    run_jobs as run_queued,
    share,
    stored_job,
    stored_run,
)

HOOKS = {}


def hook(name, *args):
    f = HOOKS.get(name)
    if f is not None:
        f(*args)


class Solver(Component):
    def __init__(self):
        super().__init__("div", id="solver")
        self.maxh = QInput(id="maxh", ui_model_value=0.5)
        self.ui_children = [self.maxh]

    @compute(reuse=True)
    def solve(self, steps=3, fail_at=None):
        for i in range(steps):
            hook("step", self, i)
            if i == fail_at:
                raise RuntimeError(f"diverged at step {i}")
            progress((i + 1) / steps, f"step {i + 1} of {steps}")
        self.state.n = int(round(1 / self.maxh.ui_model_value)) * steps

    @compute(max_attempts=2)
    def flaky(self):
        hook("flaky", self)
        raise RuntimeError("no license")

    @compute_node
    def legacy(self):
        hook("legacy", self)
        self.state.legacy = "done"


class UIApp(App):
    def __init__(self):
        super().__init__()
        self.solver = Solver()
        self.control = JobControl(self.solver.solve, kwargs={"steps": 3})
        self.flaky = JobControl(self.solver.flaky, show_outdated=False)
        self.runs_view = RunsView(self.solver.solve)
        self.marker = OutdatedMarker(self.solver.solve)
        self.legacy = JobComponent("legacy_job", self.solver.legacy)
        self.component = Div(
            self.solver,
            self.control,
            self.flaky,
            self.runs_view,
            self.marker,
            self.legacy,
        )


AppConfig(UIApp, name="job components", version="1")


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
    app = UIApp()
    session = CaseSession.create(
        app, server.client(user), app_id=1, name="case", scheduler=sched
    )
    return app, session


def open_case(server, sched, case_id, user="alice"):
    app = UIApp()
    session = CaseSession.open(
        app, server.client(user), case_id, scheduler=sched
    )
    return app, session


def run_jobs(server, sched, job_sched, **kw):
    done = run_queued(server, UIApp, scheduler=job_sched, **kw)
    sched.run_pending()
    return done


def click(button):
    button._handle("click.stop")


def shown(control: JobControl) -> dict:
    """What the control displays"""
    return {
        "status": (
            None
            if control.status_chip.ui_hidden
            else control.status_chip.ui_label
        ),
        "cancel": not control.cancel_button.ui_hidden,
        "progress": (
            None
            if control.progress.ui_hidden
            else (
                control.progress_bar.ui_value,
                control.progress_text.ui_children[0],
            )
        ),
        "detail": (
            None if control.detail.ui_hidden else control.detail.ui_children[0]
        ),
    }


def events_of(control):
    seen = []
    for name in ("submit", "status", "finish"):
        control.on(name, lambda ev, name=name: seen.append((name, ev.value)))
    return seen


def test_status_sequence_queue_position_and_progress(server, sched):
    """The test plays the runner: every state reaches the control through
    events only"""
    app, session = create(server, sched)
    control = app.control
    seen = events_of(control)
    assert shown(control)["status"] is None and control.job is None

    other = app.solver.solve(steps=5)  # a job ahead in the queue
    click(control.run_button)
    job = control.job
    assert isinstance(job, JobHandle) and job.id != other.id
    assert job.queue_position == 2
    assert shown(control) == {
        "status": "Queued (position 2)",
        "cancel": True,
        "progress": None,
        "detail": None,
    }
    assert seen == [("submit", job.id)]

    # the job ahead is claimed: the queue position follows (job.status event)
    a = server.claim(other.id)
    sched.run_pending()
    assert shown(control)["status"] == "Queued (position 1)"

    a = server.claim(job.id)
    sched.run_pending()
    assert shown(control)["status"] == "Starting"
    server.heartbeat(job.id, a["attempt"])
    sched.run_pending()
    assert shown(control)["status"] == "Running"
    assert shown(control)["progress"] == (0, "")
    assert control.progress_bar.ui_indeterminate

    client = server.job_client(job.id, a["attempt"])
    client.progress(0.25, None)
    sched.run_pending()
    assert shown(control)["progress"] == (0.25, "25 %")
    assert not control.progress_bar.ui_indeterminate
    client.progress(0.5, "half way")
    sched.run_pending()
    assert shown(control)["progress"] == (0.5, "half way")

    client.commit([], seq=1, final=True)
    server.finish(job.id, a["attempt"], "succeeded", 0)
    sched.run_pending()
    assert shown(control) == {
        "status": "Done",
        "cancel": False,
        "progress": None,
        "detail": None,
    }
    assert seen == [
        ("submit", job.id),
        ("status", "assigned"),
        ("status", "running"),
        ("status", "succeeded"),
        ("finish", "succeeded"),
    ]
    # nothing of the controls is stored in the case
    keys = {p for p in flatten(server.client("alice").state(session.case_id))}
    assert all(p[0] in ("solver", "maxh", "__case__") for p in keys), keys


def test_progress_of_a_running_job(server, sched, job_sched):
    app, session = create(server, sched)
    control = app.control
    seen = []

    def step(comp, i):
        job_sched.advance(1.1)
        sched.run_pending()
        seen.append(shown(control)["progress"])

    HOOKS["step"] = step
    click(control.run_button)
    run_jobs(server, sched, job_sched)
    assert seen == [(0, ""), (1 / 3, "step 1 of 3"), (2 / 3, "step 2 of 3")]
    assert shown(control)["status"] == "Done"
    assert app.solver.state.n == 6


def test_cancel_running_and_queued(server, sched, job_sched):
    """Cancel while running ends cancelled, a queued job ends
    at once"""
    app, session = create(server, sched)
    control = app.control
    states = []

    def step(comp, i):
        job_sched.advance(1.1)
        sched.run_pending()
        if i == 1:
            click(control.cancel_button)
            states.append(shown(control))
            assert control.cancel_button.ui_disable
            sched.run_pending()
            states.append(shown(control))

    HOOKS["step"] = step
    click(control.run_button)
    job = control.job
    run_jobs(server, sched, job_sched)
    assert states[0]["status"] == "Cancelling" and states[0]["cancel"]
    assert states[1]["status"] == "Cancelling"
    assert job.status == "cancelled"
    assert shown(control)["status"] == "Cancelled"
    assert not shown(control)["cancel"]
    [run] = app.runs_view.runs
    assert run.status == "cancelled"

    # a queued job ends at once
    click(control.run_button)
    queued = control.job
    assert queued.id != job.id and shown(control)["status"].startswith("Queued")
    click(control.cancel_button)
    sched.run_pending()
    assert queued.status == "cancelled"
    assert shown(control)["status"] == "Cancelled"
    assert run_jobs(server, sched, job_sched) == []
    # A run that never started has no duration
    runs = {r.id: r for r in app.runs_view.runs}
    assert runs[job.run_id].info.extra["started_at"]
    assert runs[queued.run_id].info.extra["started_at"] is None
    assert run_time(runs[job.run_id]).endswith(" s")
    assert run_time(runs[queued.run_id]) and "," not in run_time(
        runs[queued.run_id]
    )


def test_failure_message_and_attempt(server, sched, job_sched):
    app, session = create(server, sched)
    control = app.flaky
    seen = []

    def flaky(comp):
        sched.run_pending()
        seen.append(shown(control)["status"])
        current_job().store.client.message("license server down", "error")

    HOOKS["flaky"] = flaky
    click(control.run_button)
    run_jobs(server, sched, job_sched, limit=1)
    # the first attempt failed after it started: requeued with the reason
    assert control.job.status == "queued"
    view = shown(control)
    assert view["status"] == "Queued (position 1)"
    run_jobs(server, sched, job_sched)
    assert seen == ["Running", "Running (attempt 2)"]
    view = shown(control)
    assert view["status"] == "Failed (attempt 2)" and not view["cancel"]
    # the error reported by the job process, not only the finish message
    assert view["detail"] == "license server down"
    assert "text-negative" in control.detail.ui_class


def test_identical_submission_reuses_the_run(server, sched, job_sched):
    """A double click is one job; after success the run is reused"""
    app, session = create(server, sched)
    control = app.control
    click(control.run_button)
    click(control.run_button)
    first = control.job
    assert job_count(server) == 1
    run_jobs(server, sched, job_sched)
    click(control.run_button)
    assert control.job.reused and control.job.id == first.id
    assert shown(control)["status"] == f"Done (reused run {first.run_id})"
    assert job_count(server) == 1


def test_follows_jobs_of_other_tabs_and_finds_them_again(
    server, sched, job_sched
):
    app, session = create(server, sched)
    other, so = open_case(server, sched, session.case_id)
    assert other.control.job is None
    click(app.control.run_button)
    job = app.control.job
    sched.run_pending()
    # the other tab follows the job submitted here
    assert other.control.job is not None and other.control.job.id == job.id
    assert shown(other.control)["status"] == "Queued (position 1)"
    # a third tab opened while the job is queued finds it
    third, st = open_case(server, sched, session.case_id)
    assert third.control.job.id == job.id
    assert shown(third.control)["status"] == "Queued (position 1)"
    # the flaky control does not follow jobs of another function
    assert other.flaky.job is None
    run_jobs(server, sched, job_sched)
    for a in (app, other, third):
        assert shown(a.control)["status"] == "Done"
    # a tab opened later shows the last job's result
    fourth, sf = open_case(server, sched, session.case_id)
    assert shown(fourth.control)["status"] == "Done"


def test_runs_view_fork_keep_outdated(server, sched, job_sched):
    app, session = create(server, sched)
    view, marker = app.runs_view, app.marker
    assert view.runs == [] and not view.empty.ui_hidden
    forks = []
    view.on_fork(lambda ev: forks.append(ev.value))

    click(app.control.run_button)
    first = app.control.job
    sched.run_pending()
    assert [r.id for r in view.runs] == [first.run_id]
    assert view.runs[0].status == "running" and view.empty.ui_hidden
    run_jobs(server, sched, job_sched)
    [run] = view.runs
    assert run.status == "succeeded" and not run.outdated
    assert marker.chip.ui_hidden and app.solver.state.n == 6

    # An input edit marks the latest run outdated (case.head event)
    app.solver.maxh.ui_model_value = 0.25
    app.commit()
    sched.run_pending()
    assert view.runs[0].outdated and not marker.chip.ui_hidden
    assert "run %d" % first.run_id in marker.tooltip.ui_children[0]
    assert app.control.outdated.outdated

    click(app.control.run_button)
    second = app.control.job
    run_jobs(server, sched, job_sched)
    assert [r.id for r in view.runs] == [first.run_id, second.run_id]
    # the new results are in the case and current
    assert marker.chip.ui_hidden and app.solver.state.n == 12
    assert [r.outdated for r in view.runs] == [True, False]

    # keep and fork, newest first
    view.keep(first.run_id)
    assert stored_run(server, first.run_id).kept
    assert [r.kept for r in view.runs] == [True, False]
    newest = view.list.ui_children[0]
    buttons = newest.ui_children[2].ui_children[0].ui_children
    assert [b._props.get("aria-label") for b in buttons] == [
        f"Keep run {second.run_id}",
        f"New case from run {second.run_id}",
    ]
    case_id = view.fork(first.run_id)
    assert forks == [{"run_id": first.run_id, "case_id": case_id}]
    forked, sf = open_case(server, sched, case_id)
    assert sf.store.case(case_id).name == f"case (run {first.run_id})"
    assert forked.solver.state.n == 6
    # The copied results are a run of the new case, outdated once
    # its inputs change
    [copied] = forked.runs_view.runs
    assert copied.id != first.run_id and copied.status == "succeeded"
    assert not copied.outdated and forked.marker.chip.ui_hidden
    forked.solver.maxh.ui_model_value = 0.125
    forked.commit()
    sched.run_pending()
    assert forked.runs_view.runs[0].outdated
    assert not forked.marker.chip.ui_hidden
    assert forked.solver.state.n == 6


def test_cancel_after_the_final_commit(server, sched):
    """A cancel after the final commit keeps the result"""
    app, session = create(server, sched)
    click(app.control.run_button)
    job = app.control.job
    a = server.claim(job.id)
    server.heartbeat(job.id, a["attempt"])
    client = server.job_client(job.id, a["attempt"])
    client.commit([], seq=1, final=True)
    click(app.control.cancel_button)
    sched.run_pending()
    assert not stored_job(server, job.id).cancel_requested
    assert server.heartbeat(job.id, a["attempt"]) == {"cancel": False}
    server.finish(job.id, a["attempt"], "succeeded", 0)
    sched.run_pending()
    assert job.status == "succeeded" and shown(app.control)["status"] == "Done"
    [run] = app.runs_view.runs
    assert run.id == job.run_id and run.status == "succeeded"


def test_no_requests_before_the_case_exists(server, sched, job_sched):
    """A new case (created by the first save) asks for no runs or jobs"""
    store = server.client("alice")
    calls = []
    for name in ("runs", "job", "case"):
        method = getattr(store, name)

        def wrapped(case_id, *a, _m=method, _n=name, **k):
            calls.append((_n, case_id))
            return _m(case_id, *a, **k)

        setattr(store, name, wrapped)
    app = UIApp()
    session = CaseSession.open(app, store, None, scheduler=sched)
    for comp in (app.control, app.runs_view, app.marker, app.flaky):
        comp._handle("load")
        comp._handle("mounted")
    sched.run_pending()
    assert session.case_id is None and calls == []
    click(app.control.run_button)
    sched.run_pending()
    assert session.case_id is not None
    assert all(c[1] is not None for c in calls)
    job = app.control.job
    run_jobs(server, sched, job_sched)
    assert job.status == "succeeded"
    assert [r.id for r in app.runs_view.runs] == [job.run_id]


def test_job_component_compatibility(server, sched, job_sched):
    """The compute_node button follows its job and stores nothing of it"""
    app, session = create(server, sched)
    legacy = app.legacy
    starts, finishes = [], []
    legacy.on_start(lambda: starts.append(1))
    legacy.on_finish(lambda ev: finishes.append(ev.value))
    states = []
    HOOKS["legacy"] = lambda comp: (
        sched.run_pending(),
        states.append((legacy.job_status["status"], legacy._props["icon"])),
    )
    legacy._handle("click")
    assert isinstance(legacy.job, JobHandle) and starts == [1]
    assert legacy.job_status["status"] == "queued"
    assert legacy._props["icon"] == "mdi-stop"
    assert legacy.job_id == legacy.job.id
    app.commit()
    run_jobs(server, sched, job_sched)
    assert states == [("started", "mdi-stop")]
    assert legacy.job_status["status"] == "finished"
    assert legacy._props["icon"] == "mdi-play"
    assert finishes == ["succeeded"]
    assert app.solver.state.legacy == "done"
    stored = flatten(server.client("alice").state(session.case_id))
    assert not any(p[0].startswith("legacy_job") for p in stored), stored
    # a reopened case finds the job again
    other, so = open_case(server, sched, session.case_id)
    assert other.legacy.job.id == legacy.job.id
    assert other.legacy.job_status["status"] == "finished"


def test_controls_without_case_store():
    """Without a case store compute_node keeps the local behaviour"""
    app = UIApp()
    result = app.legacy.compute_function(_job_component=app.legacy)
    assert not isinstance(result, JobHandle)
    assert app.solver.state.legacy == "done"
    assert app.control.job is None


def test_outdated_marker_of_the_latest_result(server, sched, job_sched):
    """The control's outdated marker refers to the latest succeeded run"""
    app, session = create(server, sched)
    click(app.control.run_button)
    first = app.control.job
    run_jobs(server, sched, job_sched)
    chip = app.control.outdated.chip
    assert chip.ui_hidden
    app.solver.maxh.ui_model_value = 0.25
    app.commit()
    sched.run_pending()
    assert not chip.ui_hidden and not app.marker.chip.ui_hidden
    click(app.control.run_button)
    second = app.control.job
    sched.run_pending()
    assert second.id != first.id and not second.done
    # the latest result is the first job's until the second one ends
    assert not chip.ui_hidden
    run_jobs(server, sched, job_sched)
    assert chip.ui_hidden and app.marker.chip.ui_hidden


def test_control_errors_cleared_when_access_changes(server, sched, caplog):
    """A failed submit on a read-only share is logged
    without a traceback, its error goes once the share allows writing"""
    app, session = create(server, sched)
    share(server, session.case_id, "bob", write=False)
    b, sb = open_case(server, sched, session.case_id, user="bob")
    assert sb.status == "read_only"
    with caplog.at_level(logging.WARNING):
        click(b.control.run_button)
    assert shown(b.control)["detail"].startswith("Submitting failed")
    assert "Traceback" not in caplog.text
    share(server, session.case_id, "bob", write=True)
    sched.advance(1)
    assert sb.status != "read_only"
    assert shown(b.control)["detail"] is None


def test_events_before_the_submit_answer(server, sched):
    """Job.status events processed while the submit is in
    flight reach the control once the answer arrives (no "Starting" forever)"""
    app, session = create(server, sched)
    other, so = open_case(server, sched, session.case_id)
    store = session.store
    submit = store.submit

    def in_flight(case_id, request):
        info = submit(case_id, request)
        a = server.claim(info.id)
        server.heartbeat(info.id, a["attempt"])
        sched.run_pending()
        # an answer with the queue position: no reload of the job
        info.queue_position = 1
        return info

    store.submit = in_flight
    click(app.control.run_button)
    job = app.control.job
    assert job.status == "running"
    assert shown(app.control)["status"] == "Running"
    sched.run_pending()
    assert shown(other.control)["status"] == "Running"


def test_stale_job_answer_does_not_undo_events(server, sched):
    """A job answer older than the events processed while it was in flight
    (a component loads the job on its "assigned" event) does not set the
    status back"""
    app, session = create(server, sched)
    store = session.store
    job_of = store.job
    raced = []

    def in_flight(job_id):
        info = job_of(job_id)
        if info.status == "assigned" and not raced:
            raced.append(job_id)
            server.heartbeat(job_id, info.attempt)
            sched.run_pending()
        return info

    click(app.control.run_button)
    job = app.control.job
    store.job = in_flight
    server.claim(job.id)
    sched.run_pending()
    assert raced == [job.id]
    assert job.status == "running"
    assert shown(app.control)["status"] == "Running"
    job.refresh()
    assert shown(app.control)["status"] == "Running"


def test_progress_shown_after_opening_the_case(server, sched):
    """A case opened while its job runs (a reload) shows the job's last
    progress, not only the one of later events"""
    app, session = create(server, sched)
    click(app.control.run_button)
    job = app.control.job
    a = server.claim(job.id)
    server.heartbeat(job.id, a["attempt"])
    server.job_client(job.id, a["attempt"]).progress(0.5, "half way")
    sched.run_pending()
    assert shown(app.control)["progress"] == (0.5, "half way")
    b, sb = open_case(server, sched, session.case_id)
    sched.run_pending()
    assert shown(b.control)["status"] == "Running"
    assert shown(b.control)["progress"] == (0.5, "half way")
