"""Components for compute functions: a job control, the runs of a function
and an outdated marker.

Everything they show comes from the case store and the session's events
(job.status through JobHandle.on_status, job.progress, run.status,
case.head), never from polling, and nothing of it is stored
in the case: a job that crashed leaves no spinner behind. They need no
component id; the compute method's component needs one.
"""

import datetime
import logging
from typing import Callable

from ..jobs import JobHandle, JobSession, Run, function_name
from ..state import session_of
from ..store.types import JOB_TERMINAL, CaseDeletedError, ForbiddenError
from ..utils import print_exception
from .basecomponent import Component
from .qcomponents import (
    QBtn,
    QChip,
    QIcon,
    QItem,
    QItemLabel,
    QItemSection,
    QLinearProgress,
    QList,
    QTooltip,
)

__all__ = ["JobControl", "RunsView", "OutdatedMarker", "JobFollower"]

logger = logging.getLogger("ngapp.jobs")

ACTIVE = ("queued", "assigned", "running")

# refused because of the case's state (read only, deleted): no traceback
REFUSED = (ForbiddenError, CaseDeletedError)

# label, color, icon
STATUS = {
    "queued": ("Queued", "grey-7", "mdi-timer-sand"),
    "assigned": ("Starting", "blue-grey", "mdi-progress-clock"),
    "running": ("Running", "primary", "mdi-cog"),
    "succeeded": ("Done", "positive", "mdi-check-circle"),
    "failed": ("Failed", "negative", "mdi-alert-circle"),
    "timed_out": ("Timed out", "negative", "mdi-timer-alert"),
    "cancelled": ("Cancelled", "warning", "mdi-stop-circle"),
}


def _status(status) -> tuple[str, str, str]:
    return STATUS.get(status, (str(status or ""), "grey", "mdi-help-circle"))


def _same_case(session, payload) -> bool:
    return payload.get("case_id", session.case_id) == session.case_id


def _call(callback, *args):
    try:
        callback(*args)
    except Exception as e:
        print_exception(e)


def _div(*children, **kwargs) -> Component:
    return Component("div", *children, **kwargs)


def _set_text(comp: Component, text: str):
    if comp.ui_children != [text]:
        comp.ui_children = [text]


def _time(iso: str | None) -> datetime.datetime | None:
    if not iso:
        return None
    try:
        return datetime.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return None


def _duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.0f} s"
    if seconds < 3600:
        return f"{seconds / 60:.0f} min"
    return f"{seconds / 3600:.1f} h"


def run_time(run: Run) -> str:
    """Submission time of a run and how long its job ran once it ended (none
    if it never started, e.g. cancelled while queued)"""
    extra = run.info.extra
    created = _time(extra.get("created_at"))
    if created is None:
        return ""
    text = created.astimezone().strftime("%Y-%m-%d %H:%M")
    start = _time(extra["started_at"]) if "started_at" in extra else created
    end = _time(extra.get("finished_at"))
    if start is not None and end is not None:
        text += f", {_duration(max(0.0, (end - start).total_seconds()))}"
    return text


class _Runs:
    """Runs of one compute function of a case session, fetched again once
    per batch of events that can change them (new runs, status, the head for
    the outdated flag); shared by the components of a session"""

    @classmethod
    def of(cls, session, function: str) -> "_Runs":
        per = session.__dict__.setdefault("_ngapp_runs", {})
        runs = per.get(function)
        if runs is None:
            runs = per[function] = cls(session, function)
        return runs

    def __init__(self, session, function: str):
        self.session = session
        self.function = function
        self.runs: list[Run] = []
        self.loaded = False
        # the case was deleted: the runs as last seen, updated by events
        self.deleted = False
        self._listeners: list[Callable] = []
        self._scheduled = False
        session.on_event(self._on_event)
        session.on_created(lambda case_id: self._schedule())

    @property
    def latest(self) -> Run | None:
        """The run of the latest succeeded job"""
        done = [r for r in self.runs if r.status == "succeeded"]
        return max(done, key=lambda r: r.job_id) if done else None

    def _schedule(self):
        if not self._scheduled and self._listeners:
            self._scheduled = True
            self.session.scheduler.call_later(0, self.refresh)

    def listen(self, callback) -> Callable[[], None]:
        """callback(runs) now and after every change"""
        self._listeners.append(callback)
        if self.loaded:
            _call(callback, self.runs)
        else:
            self.refresh()

        def dispose():
            if callback in self._listeners:
                self._listeners.remove(callback)

        return dispose

    def _on_event(self, event):
        payload = event.payload
        if not _same_case(self.session, payload):
            return
        if event.type == "case.deleted":
            self.deleted = True
        elif event.type == "run.status":
            self._apply(payload)
        elif event.type != "case.head":
            return
        self._schedule()

    def _apply(self, payload: dict):
        """The run.status payload at once (the reload fails once the case
        is deleted)"""
        run_id = payload.get("run_id")
        run = next((r for r in self.runs if r.id == run_id), None)
        if run is None:
            return
        changed = False
        for key in ("status", "tip_revision", "kept"):
            if key in payload and getattr(run, key) != payload[key]:
                setattr(run, key, payload[key])
                setattr(run.info, key, payload[key])
                changed = True
        if changed:
            self._notify()

    def _notify(self):
        for callback in list(self._listeners):
            _call(callback, self.runs)

    def refresh(self):
        self._scheduled = False
        session = self.session
        if session.closed or not self._listeners or session.case_id is None:
            return  # a new case: loaded once the first save created it
        if self.deleted or session.read_only_reason == "deleted":
            self.deleted = True
            self._notify()
            return
        try:
            infos = session.store.runs(session.case_id, self.function)
        except CaseDeletedError:
            self.deleted = True
            self._notify()
            return
        except Exception as e:
            logger.warning("Loading the runs of %s failed: %r", self.function, e)
            return
        self.runs = [Run(session, info) for info in infos]
        self.loaded = True
        self._notify()


class _Bound:
    """Follows the case session of a component's app: on load (a case was
    opened), on mount and before actions"""

    def __init__(self, owner: Component):
        self.owner = owner
        self.session = None
        owner.on_load(self.sync)
        owner.on_mounted(self.sync)

    def sync(self):
        session = session_of(self.owner)
        if isinstance(session, JobSession):
            session = None  # the app of a job shows no jobs
        if session is not self.session:
            old, self.session = self.session, session
            self.changed(old, session)
        return session

    def changed(self, old, new):
        pass


class JobFollower(_Bound):
    """The newest job of a compute function in the open case of a component's
    app, as a JobHandle (``job``) kept current by the session's events: the
    newest unfinished job when the case is opened, then every job submitted
    for the function, also by other tabs or users. on_change(kind) is called
    with "job" (another job), "status" or "progress". Used by JobControl and
    JobComponent."""

    def __init__(self, owner: Component, function, on_change: Callable):
        super().__init__(owner)
        self.function = function
        self.on_change = on_change
        self.job: JobHandle | None = None
        self.cancelling = False
        self.error = ""
        self.failure = ""
        self._name = None
        self._functions: dict[int, str] = {}
        self._dispose_events = None
        self._dispose_created = None
        self._dispose_status = None
        self._dispose_access = None
        self._read_only = None
        self._refreshing = False
        self._position_scheduled = False

    @property
    def name(self) -> str:
        if self._name is None:
            self._name = function_name(self.function)
        return self._name

    @property
    def active(self) -> bool:
        return self.job is not None and self.job.status in ACTIVE

    def changed(self, old, new):
        if self._dispose_events is not None:
            try:
                self._dispose_events()
            except ValueError:
                pass
            self._dispose_events = None
        if self._dispose_created is not None:
            try:
                self._dispose_created()
            except ValueError:
                pass
            self._dispose_created = None
        if self._dispose_access is not None:
            try:
                self._dispose_access()
            except ValueError:
                pass
            self._dispose_access = None
        self._untrack()
        self._functions = {}
        if new is not None:
            self._dispose_events = new.on_event(self._on_event)
            self._dispose_created = new.on_created(
                lambda case_id: self.job is None and self._restore(new, notify=True)
            )
            self._read_only = new.status == "read_only"
            self._dispose_access = new.on_status(self._on_session_status)
            self._restore(new)
        self.on_change("job")

    def _restore(self, session, notify=False):
        if session.case_id is None:
            return  # a new case has no jobs
        try:
            infos = session.store.runs(session.case_id, self.name)
            if not infos:
                return
            active = [i for i in infos if i.job_status in ACTIVE]
            info = max(active or infos, key=lambda i: i.job_id)
            self.track(
                JobHandle(session, session.store.job(info.job_id)), notify=notify
            )
        except Exception as e:
            logger.warning("Loading the jobs of %s failed: %r", self._name, e)

    def _untrack(self):
        if self._dispose_status is not None:
            self._dispose_status()
            self._dispose_status = None
        self.job = None
        self.cancelling = False
        self.failure = ""

    def track(self, handle: JobHandle, notify: bool = True):
        """Follow handle (a job of the function) from now on"""
        self._untrack()
        self.job = handle
        self.error = ""
        self.cancelling = handle.info.cancel_requested and not handle.done
        self._functions[handle.id] = handle.function
        self._dispose_status = handle.on_status(self._on_status)
        if handle.status in ("failed", "timed_out"):
            self._load_failure()
        if handle.status == "queued" and handle.queue_position is None:
            self._refresh_job()
        if notify:
            self.on_change("job")

    def submit(self, *args, **kwargs):
        """Call the compute function; a JobHandle is followed. In FULL mode
        the first save creates the case (commits before submitting)."""
        self.error = ""
        session = self.sync()
        app = self.owner.app
        if session is None and hasattr(app, "_case_session"):
            app._case_session()
            session = self.sync()
        result = self.function(*args, **kwargs)
        if isinstance(result, JobHandle):
            self.track(result)
        return result

    def cancel(self):
        job = self.job
        if job is None or job.done:
            return
        job.cancel()
        self.cancelling = True
        self.on_change("status")

    def _on_session_status(self, status):
        """Errors of submitting or cancelling are stale once the access to
        the case changed (e.g. a share upgraded to write)"""
        read_only = status == "read_only"
        if read_only == self._read_only:
            return
        self._read_only = read_only
        if self.error:
            self.error = ""
            self.on_change("status")

    def _load_failure(self):
        """The error the job process reported (also in the finish message
        of the backend, not in that of every store)"""
        try:
            events = self.job.events()
        except Exception as e:
            logger.warning("Loading events of job %s failed: %r", self.job.id, e)
            return
        errors = [
            e["payload"].get("text", "")
            for e in events
            if e.get("kind") == "message"
            and e["payload"].get("level") == "error"
        ]
        if errors:
            self.failure = errors[-1]

    def _on_status(self, status):
        if status in JOB_TERMINAL:
            self.cancelling = False
            if status in ("failed", "timed_out"):
                self._load_failure()
        elif status == "queued":
            self._refresh_job()
        self.on_change("status")

    def _refresh_job(self, notify: bool = False):
        """Queue position and waiting reason (GET /jobs/{id} only)"""
        self._position_scheduled = False
        job = self.job
        if job is None or self._refreshing or job.done:
            return
        before = (job.status, job.queue_position, job.waiting)
        self._refreshing = True
        try:
            job.refresh()
        except Exception as e:
            logger.warning("Loading job %s failed: %r", job.id, e)
        finally:
            self._refreshing = False
        if notify and (job.status, job.queue_position, job.waiting) != before:
            self.on_change("status")

    def _schedule_refresh(self):
        if not self._position_scheduled and self.session is not None:
            self._position_scheduled = True
            self.session.scheduler.call_later(
                0, lambda: self._refresh_job(notify=True)
            )

    def _on_event(self, event):
        session = self.session
        payload = event.payload
        if session is None or not _same_case(session, payload):
            return
        job = self.job
        if event.type == "job.progress":
            if job is not None and payload.get("job_id") == job.id:
                self.on_change("progress")
        elif event.type == "job.status":
            job_id = payload.get("job_id")
            if job is not None and job_id == job.id:
                cancel = payload.get("message") == "cancel requested"
                if cancel and not job.done:
                    self.cancelling = True
                    self.on_change("status")
                return
            if job is not None and job.status == "queued":
                self._schedule_refresh()  # the queue moved
            if (
                job_id is None
                or job_id in self._functions
                or (job is not None and job_id < job.id)
                or payload.get("status") not in ACTIVE
            ):
                return
            try:
                info = session.store.job(job_id)
            except Exception as e:
                logger.warning("Loading job %s failed: %r", job_id, e)
                return
            self._functions[job_id] = info.function
            if info.function == self.name:
                self.track(JobHandle(session, info))
        elif event.type == "resync" and job is not None:
            self._refresh_job(notify=True)


class OutdatedMarker(Component):
    """Shown while the latest succeeded run of a compute function is
    outdated: the inputs changed since it was computed (conservative
    fingerprint).

    :param function: bound compute method or qualified name
    :param label: text of the marker
    """

    def __init__(self, function, label: str = "outdated", **kwargs):
        self.tooltip = QTooltip(
            "The inputs changed since this result was computed"
        )
        self.chip = QChip(
            self.tooltip,
            ui_label=label,
            ui_icon="mdi-alert",
            ui_color="warning",
            ui_text_color="white",
            ui_dense=True,
            ui_square=True,
            ui_class="ngapp-outdated hidden",
        )
        super().__init__("span", self.chip, **kwargs)
        self._function = function
        self._label = label
        self._dispose = None
        self.run: Run | None = None
        self._bound = _Bound(self)
        self._bound.changed = self._changed

    @property
    def outdated(self) -> bool:
        return self.run is not None and self.run.outdated

    def _changed(self, old, new):
        if self._dispose is not None:
            self._dispose()
            self._dispose = None
        self.run = None
        self._render()
        if new is not None:
            try:
                name = function_name(self._function)
            except RuntimeError as e:
                logger.warning("%s", e)
                return
            self._dispose = _Runs.of(new, name).listen(self._on_runs)

    def _on_runs(self, runs):
        done = [r for r in runs if r.status == "succeeded"]
        self.run = max(done, key=lambda r: r.job_id) if done else None
        self._render()

    def _render(self):
        self.chip.ui_hidden = not self.outdated
        if self.run is not None:
            _set_text(
                self.tooltip,
                f"The inputs changed since run {self.run.id} was computed",
            )


class JobControl(Component):
    """Run a compute function as a job and follow it: a run button, the
    status with the queue position or the reason the job waits, its progress
    (fraction and text, from ``ngapp.jobs.progress`` in the job), the attempt,
    a cancel button, the error message of a failed job and an outdated marker
    of the latest result.

    :param function: bound compute method, e.g. ``self.mesher.generate``
    :param args: positional arguments of the job, or a callable returning them
        when the button is pressed (JSON values)
    :param kwargs: keyword arguments of the job, or a callable returning them
    :param label: label of the run button
    :param confirm_cancel: ask before cancelling a job
    :param show_outdated: show the outdated marker of the latest result

    The control follows the newest job of the function in the open case, also
    one submitted by another tab, and finds an unfinished job again when the
    case is opened; ``job`` is its JobHandle. Submitting commits the pending
    edits first; an identical submission returns the same job or
    reuses a succeeded run. Events: ``submit`` (value: job id),
    ``status`` (value: status) and ``finish`` (value: final status).
    """

    def __init__(
        self,
        function,
        *,
        args=(),
        kwargs=None,
        label: str = "Run",
        confirm_cancel: bool = False,
        show_outdated: bool = True,
        **props,
    ):
        self._args = args
        self._kwargs = kwargs
        self.confirm_cancel = confirm_cancel
        self._submitting = False
        self.run_button = QBtn(
            ui_label=label,
            ui_icon="mdi-play",
            ui_color="primary",
            ui_no_caps=True,
            ui_class="ngapp-job-run",
        )
        self.cancel_button = QBtn(
            ui_label="Cancel",
            ui_icon="mdi-stop",
            ui_color="negative",
            ui_flat=True,
            ui_no_caps=True,
            ui_class="ngapp-job-cancel hidden",
        )
        self.status_chip = QChip(
            ui_dense=True,
            ui_square=True,
            ui_text_color="white",
            ui_class="ngapp-job-status hidden",
        )
        self.outdated = OutdatedMarker(function) if show_outdated else None
        self.progress_bar = QLinearProgress(
            ui_value=0, ui_size="6px", ui_rounded=True, ui_color="primary"
        )
        self.progress_text = _div(ui_class="text-caption text-grey-8")
        self.progress = _div(
            self.progress_bar,
            self.progress_text,
            ui_class="ngapp-job-progress hidden",
            ui_style="min-width:200px",
        )
        self.detail = _div(ui_class="ngapp-job-detail text-caption hidden")
        row = [self.run_button, self.cancel_button, self.status_chip]
        if self.outdated is not None:
            row.append(self.outdated)
        props.setdefault("ui_class", "ngapp-job-control column q-gutter-xs")
        super().__init__(
            "div",
            _div(*row, ui_class="row items-center q-gutter-sm no-wrap"),
            self.progress,
            self.detail,
            **props,
        )
        self.follower = JobFollower(self, function, self._on_change)
        self._last_status = None
        self.run_button.on_click(self.submit)
        self.cancel_button.on_click(self._on_cancel)

    @property
    def job(self) -> JobHandle | None:
        return self.follower.job

    def on_submit(self, handler: Callable, arg: object = None):
        return self.on("submit", handler, arg)

    def on_status(self, handler: Callable, arg: object = None):
        return self.on("status", handler, arg)

    def on_finish(self, handler: Callable, arg: object = None):
        return self.on("finish", handler, arg)

    def submit(self):
        """Submit the job with the current arguments; returns the JobHandle
        (or the result of a compute_node without case store)"""
        args = self._args() if callable(self._args) else self._args
        kwargs = self._kwargs() if callable(self._kwargs) else self._kwargs
        self._submitting = True
        self._render()
        try:
            result = self.follower.submit(*(args or ()), **(kwargs or {}))
        except REFUSED as e:
            logger.warning("Submitting %s failed: %s", self.follower.name, e)
            self.follower.error = f"Submitting failed: {e}"
            return None
        except Exception as e:
            print_exception(e)
            self.follower.error = f"Submitting failed: {e}"
            return None
        finally:
            self._submitting = False
            self._render()
        if isinstance(result, JobHandle):
            self._last_status = result.status
            self._handle("submit", result.id)
        else:
            self.follower.error = "" if result is None else "Submitted"
            self._render()
        return result

    def cancel(self):
        """Cancel the followed job (queued jobs end at once)"""
        try:
            self.follower.cancel()
        except REFUSED as e:
            logger.warning("Cancelling %s failed: %s", self.follower.name, e)
            self.follower.error = f"Cancelling failed: {e}"
            self._render()
        except Exception as e:
            print_exception(e)
            self.follower.error = f"Cancelling failed: {e}"
            self._render()

    def _on_cancel(self):
        if not self.confirm_cancel:
            return self.cancel()
        self.quasar.dialog(
            {
                "title": "Cancel job",
                "message": "Cancel the running job?",
                "cancel": True,
            }
        ).onOk(lambda *_: self.cancel())

    def _on_change(self, kind):
        job = self.job
        self._render()
        if kind == "progress" or job is None:
            return
        if job.status != self._last_status:
            self._last_status = job.status
            if kind == "status":
                self._handle("status", job.status)
                if job.done:
                    self._handle("finish", job.status)

    def _render(self):
        follower = self.follower
        job = follower.job
        status = job.status if job is not None else None
        active = status in ACTIVE
        self.run_button.ui_loading = self._submitting
        self.cancel_button.ui_hidden = not active
        self.cancel_button.ui_disable = follower.cancelling
        label, color, icon = _status(status)
        if job is not None:
            if status == "queued" and job.queue_position:
                label += f" (position {job.queue_position})"
            if active and follower.cancelling:
                label, color = "Cancelling", "warning"
            if job.attempt > 1 and status != "queued":
                label += f" (attempt {job.attempt})"
            if job.reused and status == "succeeded":
                label += f" (reused run {job.run_id})"
        self.status_chip.ui_label = label
        self.status_chip.ui_color = color
        self.status_chip.ui_icon = icon
        self.status_chip.ui_hidden = job is None

        running = status == "running"
        self.progress.ui_hidden = not running
        if running:
            fraction, text = job.progress
            self.progress_bar.ui_indeterminate = fraction is None
            self.progress_bar.ui_value = fraction or 0
            if not text and fraction is not None:
                text = f"{100 * fraction:.0f} %"
            _set_text(self.progress_text, text or "")

        detail, negative = follower.error, bool(follower.error)
        if not detail and job is not None:
            if status == "queued":
                detail = job.waiting or ""
            elif status in ("failed", "timed_out"):
                detail, negative = follower.failure or job.message or "", True
            elif status == "cancelled" and job.message not in ("", "cancelled"):
                detail = job.message
        _set_text(self.detail, detail)
        self.detail.ui_class = (
            "ngapp-job-detail text-caption"
            + (" text-negative" if negative else " text-grey-8")
            + ("" if detail else " hidden")
        )

        if self.outdated is not None:
            self.outdated._render()


class RunsView(Component):
    """The runs of a compute function in the open case, newest first: status,
    start time and duration, an outdated marker (inputs changed since the
    run) and the kept flag. Per run a button keeps it (excluded from
    retention) and one creates a new case from it (fork). While the case is
    read only (a read-only share or deleted) keep is disabled.

    :param function: bound compute method or qualified name
    :param title: heading of the list
    :param max_runs: number of runs listed
    :param fork_name: callable(run) returning the name of a forked case

    Events: ``fork`` (value: {"run_id", "case_id"}).
    """

    def __init__(
        self,
        function,
        *,
        title: str = "Runs",
        max_runs: int = 20,
        fork_name: Callable[[Run], str] | None = None,
        **props,
    ):
        self._function = function
        self.max_runs = max_runs
        self.fork_name = fork_name
        self.runs: list[Run] = []
        self.empty = _div(
            "No runs yet", ui_class="text-caption text-grey-7 q-pa-sm"
        )
        self.list = QList(ui_dense=True, ui_bordered=True, ui_separator=True)
        self.error = _div(
            ui_class="ngapp-runs-error text-caption text-negative hidden"
        )
        self.deleted_note = _div(
            "The case was deleted: runs as last seen",
            ui_class="ngapp-runs-deleted text-caption text-grey-7 hidden",
        )
        props.setdefault("ui_class", "ngapp-runs")
        super().__init__(
            "div",
            _div(title, ui_class="text-subtitle2"),
            self.deleted_note,
            self.empty,
            self.list,
            self.error,
            **props,
        )
        self._name = None
        self._shown = None
        self._dispose = None
        self._dispose_status = None
        # read_only reason of the session (no_write, deleted) or None
        self.read_only = None
        self._bound = _Bound(self)
        self._bound.changed = self._changed

    def on_fork(self, handler: Callable, arg: object = None):
        return self.on("fork", handler, arg)

    def _changed(self, old, new):
        if self._dispose is not None:
            self._dispose()
            self._dispose = None
        if self._dispose_status is not None:
            try:
                self._dispose_status()
            except ValueError:
                pass
            self._dispose_status = None
        self.runs = []
        self.read_only = None
        self._set_error("")
        self._render()
        if new is not None:
            self._dispose_status = new.on_status(self._on_session_status)
            self._on_session_status(new.status)
            try:
                self._name = function_name(self._function)
            except RuntimeError as e:
                logger.warning("%s", e)
                return
            self._dispose = _Runs.of(new, self._name).listen(self._on_runs)

    def _watch(self) -> _Runs | None:
        session = self._bound.sync()
        if session is None or self._name is None:
            return None
        return _Runs.of(session, self._name)

    def refresh(self):
        watch = self._watch()
        if watch is not None:
            watch.refresh()

    def _on_runs(self, runs):
        self.runs = list(runs)
        watch = self._watch()
        if watch is not None and watch.deleted:
            self.read_only = "deleted"
        self._render()

    def _run(self, run_id) -> Run | None:
        return next((r for r in self.runs if r.id == run_id), None)

    def _on_session_status(self, status):
        session = self._bound.session
        reason = None
        if status == "read_only" and session is not None:
            reason = session.read_only_reason or "no_write"
        if reason != self.read_only:
            self.read_only = reason
            if reason is None:
                self._set_error("")
            self._render()

    def _set_error(self, text: str):
        _set_text(self.error, text)
        self.error.ui_class = "ngapp-runs-error text-caption text-negative" + (
            "" if text else " hidden"
        )

    def _action(self, what: str, action) -> bool:
        """Run action(); refusals of the store (read only, deleted) are
        shown in short, other errors with their traceback in the log"""
        if self.read_only is not None and what != "Creating a case":
            return False
        try:
            action()
        except REFUSED as e:
            logger.warning("%s failed: %s", what, e)
            self._set_error(f"{what} failed: {e}")
            return False
        except Exception as e:
            print_exception(e)
            self._set_error(f"{what} failed: {e}")
            return False
        self._set_error("")
        return True

    def keep(self, run_id: int):
        run = self._run(run_id)
        if run is not None and self._action("Keeping the run", run.keep):
            self._render()
            self.refresh()

    def fork(self, run_id: int) -> int | None:
        """New case from the run (its input revision and its data); returns
        the id of the new case"""
        run = self._run(run_id)
        if run is None:
            return None
        if self.fork_name is not None:
            name = self.fork_name(run)
        else:
            case = getattr(self.app.file_data, "name", "") or "case"
            name = f"{case} (run {run.id})"
        created = []
        if not self._action(
            "Creating a case", lambda: created.append(run.fork(name))
        ):
            return None
        case_id = created[0]
        self._handle("fork", {"run_id": run_id, "case_id": case_id})
        try:
            # stays until dismissed: it links to the new case
            self.quasar.notify(
                {
                    "message": f"New case {name!r} created",
                    "color": "positive",
                    "timeout": 0,
                    "actions": [
                        {
                            "label": "Open",
                            "color": "white",
                            "handler": lambda *_: self.open_case(case_id),
                        },
                        {
                            "icon": "close",
                            "color": "white",
                            "aria-label": "Dismiss",
                        },
                    ],
                }
            )
        except Exception:
            pass
        return case_id

    def open_case(self, case_id: int):
        """Open another case of the app in this tab (FULL mode)"""
        self.app.env.frontend.set_query_parameter("fileId", str(case_id))

    def _item(self, run: Run) -> QItem:
        label, color, icon = _status(run.status)
        status = QIcon(QTooltip(label), ui_name=icon, ui_color=color)
        main = [QItemLabel(f"Run {run.id}")]
        caption = run_time(run)
        if caption:
            main.append(QItemLabel(caption, ui_caption=True))
        side = []
        if run.outdated:
            side.append(
                QChip(
                    QTooltip("The inputs changed since this run"),
                    ui_label="outdated",
                    ui_color="warning",
                    ui_text_color="white",
                    ui_dense=True,
                    ui_square=True,
                    ui_class="ngapp-run-outdated",
                )
            )
        read_only = self.read_only is not None
        keep = QBtn(
            QTooltip(
                "Kept (excluded from clean-up)"
                if run.kept
                else "Keep (excluded from clean-up)"
            ),
            ui_icon="mdi-pin" if run.kept else "mdi-pin-outline",
            ui_flat=True,
            ui_round=True,
            ui_dense=True,
            ui_disable=run.kept or read_only,
            ui_class="ngapp-run-keep" + (" ngapp-run-kept" if run.kept else ""),
        )
        keep._props["aria-label"] = (
            f"Run {run.id} kept" if run.kept else f"Keep run {run.id}"
        )
        keep._props["aria-pressed"] = "true" if run.kept else "false"
        keep.on_click(lambda: self.keep(run.id))
        fork = QBtn(
            QTooltip("New case from this run"),
            ui_icon="mdi-source-fork",
            ui_flat=True,
            ui_round=True,
            ui_dense=True,
            ui_disable=self.read_only == "deleted",
            ui_class="ngapp-run-fork",
        )
        fork._props["aria-label"] = f"New case from run {run.id}"
        fork.on_click(lambda: self.fork(run.id))
        side += [keep, fork]
        return QItem(
            QItemSection(status, ui_avatar=True),
            QItemSection(*main),
            QItemSection(
                _div(*side, ui_class="row items-center no-wrap"), ui_side=True
            ),
            ui_dense=True,
            ui_class="ngapp-run",
        )

    def _render(self):
        runs = list(reversed(self.runs))[: self.max_runs]
        shown = [
            (
                r.id,
                r.status,
                r.outdated,
                r.kept,
                r.info.extra.get("finished_at"),
            )
            for r in runs
        ]
        self.empty.ui_hidden = bool(runs)
        self.list.ui_hidden = not runs
        shown.append(self.read_only)
        if shown == self._shown:
            return
        self._shown = shown
        self.deleted_note.ui_class = (
            "ngapp-runs-deleted text-caption text-grey-7"
            + ("" if self.read_only == "deleted" else " hidden")
        )
        self.list.ui_children = [self._item(r) for r in runs]
