"""Compute functions, jobs and runs

App side: ``@compute`` on a component method submits a job through the case
store after committing the pending edits and returns a JobHandle.
Every job produces a run, a branch of the case's revisions that holds all its
commits. With ``merge=True`` (the default) the server also applies every
commit of the job to the case, so the case shows intermediate and final
results; paths a user changed since the job's input revision keep the user's
value (the job's value stays on the run). With ``merge=False`` the case is
not changed: the app reads the results from the run (``Run.state()``).

Job side: a JobSession is the CaseSession of a job process on a JobStore
(ngapp.store.job): the same State code runs in jobs, its commits go onto the
run branch as checkpoints at an adaptive interval and as the final
commit at the end.
"""

import contextvars
import functools
import importlib
import logging
import re
import threading
import time
import weakref
from collections.abc import Sequence
from dataclasses import dataclass

from .state import CaseSession, session_of
from .store.encoding import canonical_json
from .store.types import (
    CaseDeletedError,
    JobEndedError,
    JOB_TERMINAL,
    JobInfo,
    JobRequest,
    RunInfo,
)
from .utils import (
    BaseFrontend,
    EnvironmentType,
    get_environment,
    print_exception,
)

logger = logging.getLogger("ngapp.jobs")

_current: contextvars.ContextVar["JobSession | None"] = contextvars.ContextVar(
    "ngapp_job_session", default=None
)


def current_job() -> "JobSession | None":
    """The JobSession of the compute function running in this context"""
    return _current.get()


# -- compute functions --


def _memory_mb(memory) -> int | None:
    if memory is None:
        return None
    if isinstance(memory, (int, float)):
        return int(memory)
    m = re.fullmatch(
        r"\s*(\d+(?:\.\d+)?)\s*([kmgt]?)i?b?\s*", str(memory).lower()
    )
    if m is None:
        raise ValueError(
            f"invalid memory {memory!r}, e.g. 512 (MB), '512M' or '8G'"
        )
    factor = {"k": 1 / 1024, "": 1, "m": 1, "g": 1024, "t": 1024**2}[m.group(2)]
    return max(1, int(float(m.group(1)) * factor))


@dataclass(frozen=True)
class ComputeSpec:
    """Resources and policy of a compute function"""

    env: str = "default"
    cpus: int | None = None
    memory_mb: int | None = None
    gpus: int = 0
    gpu_type: str = ""
    scratch_gb: int = 0
    timeout: int | None = None
    max_attempts: int = 1
    restart: str = "none"
    cancel_previous: bool = False
    reuse: bool = True
    priority: int = 0
    merge: bool = True

    def resources(self) -> dict:
        res = {"gpus": self.gpus}
        if self.cpus is not None:
            res["cpus"] = self.cpus
        if self.memory_mb is not None:
            res["memory_mb"] = self.memory_mb
        if self.gpu_type:
            res["gpu_type"] = self.gpu_type
        if self.scratch_gb:
            res["scratch_gb"] = self.scratch_gb
        return res

    def policy(self) -> dict:
        policy = {
            "max_attempts": self.max_attempts,
            "restart": self.restart,
            "cancel_previous": self.cancel_previous,
            "reuse": self.reuse,
            "priority": self.priority,
            "merge": self.merge,
        }
        if self.timeout is not None:
            policy["timeout_s"] = self.timeout
        return policy


def compute(
    env="default",
    *,
    cpus=None,
    memory=None,
    gpus=0,
    gpu_type="",
    scratch_gb=0,
    timeout=None,
    max_attempts=1,
    restart="none",
    cancel_previous=False,
    parallel=False,
    lock_inputs=False,
    reuse=True,
    priority=0,
    merge=True,
    _legacy=None,
):
    """Run the decorated component method as a job on the case's compute
    environment env. Calling it commits the pending edits and submits a job
    on the resulting revision; it returns a JobHandle. Inside a job (and in
    nested calls) the method runs directly.

    memory: MB, or a string like "8G"; timeout: seconds per attempt;
    restart: "none" or "checkpoint" (a further attempt continues from the last
    checkpoint of its run); cancel_previous: cancel unfinished jobs of the same
    function; reuse: an identical submission reuses a succeeded run; merge:
    the job's commits change the case (True) or only its run (False). Without
    a case store (local app, legacy backend) the previous compute_node
    behaviour applies.
    """
    if callable(env) and not hasattr(env, "name"):
        return compute()(env)
    if parallel:
        raise NotImplementedError("compute(parallel=True) is not available yet")
    if lock_inputs:
        raise NotImplementedError(
            "compute(lock_inputs=True) is not available yet"
        )
    if restart not in ("none", "checkpoint"):
        raise ValueError("restart must be 'none' or 'checkpoint'")
    env_name = getattr(env, "name", env)
    spec = ComputeSpec(
        env_name,
        cpus,
        _memory_mb(memory),
        gpus,
        gpu_type,
        scratch_gb,
        timeout,
        max_attempts,
        restart,
        cancel_previous,
        reuse,
        priority,
        merge,
    )

    def decorator(f):
        from .utils import _legacy_compute_node

        legacy = (
            _legacy
            or _legacy_compute_node(compute_env=env_name, job_timeout=timeout)
        )(f)

        @functools.wraps(f)
        def wrapper(
            self, *args, _job_component=None, depends_on=None, **kwargs
        ):
            if _current.get() is not None:
                return f(self, *args, **kwargs)
            if session_of(self) is not None or _create_case(self):
                return submit(
                    self,
                    f.__name__,
                    spec,
                    args,
                    kwargs,
                    depends_on,
                    _job_component,
                )
            if legacy is f or _environment_type() == EnvironmentType.COMPUTE:
                return legacy(self, *args, **kwargs)
            return legacy(self, _job_component, depends_on, *args, **kwargs)

        wrapper.__ngapp_compute__ = spec
        setattr(wrapper, "__is_compute_node_function", True)
        setattr(wrapper, "__compute_env", env_name)
        return wrapper

    return decorator


def _create_case(comp) -> bool:
    """FULL mode without a case yet: the first save creates it, as the job
    components do; False where the app has no case store"""
    ctx = getattr(comp, "context", None)
    app = getattr(ctx, "app", None)
    if app is None or not hasattr(app, "_case_session"):
        return False
    return app._case_session() is not None


def _environment_type():
    try:
        return get_environment().type
    except RuntimeError:
        return None


def function_path(comp) -> list[str]:
    """Component path of a component (["__app__"] for the app)"""
    if not comp._id:
        raise RuntimeError(
            f"{type(comp).__name__} needs an id to run compute functions"
        )
    return list(CaseSession._path_of(comp))


def function_name(function) -> str:
    """Qualified name of a compute function: a bound method or the name"""
    if isinstance(function, str):
        return function
    comp = getattr(function, "__self__", None)
    if comp is None:
        raise TypeError("expected a bound compute method or a function name")
    return ".".join([*function_path(comp), function.__name__])


def submit(
    comp,
    method,
    spec,
    args=(),
    kwargs=None,
    depends_on=None,
    job_component=None,
):
    """Submit method of comp as a job (pending edits are committed first)"""
    session = session_of(comp)
    if session is None:
        raise RuntimeError("the app is not attached to a case store")
    request = JobRequest(
        {"component": function_path(comp), "method": method},
        0,
        list(args),
        dict(kwargs or {}),
        compute_env=spec.env,
        resources=spec.resources(),
        policy=spec.policy(),
        depends_on=[
            d.id if isinstance(d, JobHandle) else int(d)
            for d in depends_on or []
        ],
    )
    try:
        canonical_json({"args": request.args, "kwargs": request.kwargs})
    except (TypeError, ValueError) as e:
        raise TypeError(
            f"arguments of compute functions must be JSON values: {e}"
        ) from None
    handle = JobHandle(session, session.submit(request))
    if job_component is not None:
        job_component.job = handle
    return handle


def progress(fraction: float | None = None, text: str | None = None) -> None:
    """Progress of the running job, shown by clients and not stored in the
    case; checkpoints pending changes if the last checkpoint is older than the
    minimum interval. Outside of jobs it does nothing."""
    session = _current.get()
    if session is not None:
        session.progress(fraction, text)


# -- jobs and runs on the app side --

_LEGACY_STATUS = {
    "queued": "queued",
    "assigned": "queued",
    "running": "started",
    "succeeded": "finished",
    "failed": "failed",
    "cancelled": "stopped",
    "timed_out": "failed",
}

_RANK = {"queued": 0, "assigned": 1, "running": 2}


def _status_order(status: str, attempt: int) -> tuple:
    """Order of the states of a job: a requeue keeps the attempt (claims
    increment it), terminal states are final"""
    if status in JOB_TERMINAL:
        return (1, 0, 0)
    if status == "queued" and attempt > 0:
        return (0, attempt, 3)
    return (0, attempt, _RANK.get(status, 0))


class JobHandle:
    """A submitted job; status and progress follow the case's events"""

    def __init__(self, session: CaseSession, info: JobInfo):
        self._session = session
        self._callbacks = []
        self.progress: tuple[float | None, str] = (None, "")
        self._set(info)
        if session.job_events is not None:
            session.job_events.track(self)

    def _set(self, info: JobInfo):
        # an answer older than the events seen while it was in flight
        if hasattr(self, "status") and _status_order(
            info.status, info.attempt
        ) < _status_order(self.status, self.attempt):
            return
        self.info = info
        self.id = info.id
        self.function = info.function
        self.run_id = info.reused_run or info.run_id
        self.reused = info.reused_run is not None
        self.attempt = info.attempt
        self.message = info.message
        # of GET /jobs/{id} only
        self.queue_position = info.queue_position
        self.waiting = info.extra.get("waiting")
        # the last progress of a running job, until events bring newer ones
        progress = info.extra.get("progress")
        if (
            progress
            and info.status == "running"
            and self.progress == (None, "")
        ):
            self.progress = (
                progress.get("fraction"),
                progress.get("text") or "",
            )
        self._set_status(info.status)

    def _event(self, payload: dict):
        """A job.status event (also one replayed by JobEvents)"""
        attempt = payload.get("attempt", self.attempt)
        if _status_order(payload["status"], attempt) < _status_order(
            self.status, self.attempt
        ):
            return
        self.message = payload.get("message") or self.message
        self.attempt = attempt
        self._set_status(payload["status"])

    def _set_status(self, status: str):
        old, self.status = getattr(self, "status", None), status
        if old is not None and old != status:
            for cb in list(self._callbacks):
                try:
                    cb(status)
                except Exception as e:
                    print_exception(e)

    @property
    def done(self) -> bool:
        return self.status in JOB_TERMINAL

    def refresh(self) -> "JobHandle":
        self._set(self._session.store.job(self.id))
        return self

    def cancel(self) -> None:
        self._session.store.cancel(self.id)

    def on_status(self, callback) -> callable:
        """callback(status) on every change of the status"""
        self._callbacks.append(callback)
        return lambda: (
            self._callbacks.remove(callback)
            if callback in self._callbacks
            else None
        )

    def events(self, after: int = 0) -> list[dict]:
        """Progress, log lines and messages of the job"""
        return self._session.store.job_events(self.id, after)

    @property
    def run(self) -> "Run | None":
        for info in self._session.store.runs(
            self._session.case_id, self.function
        ):
            if info.id == self.run_id:
                return Run(self._session, info)
        return None

    # compatibility with Job and LocalJob

    def abort(self):
        self.cancel()

    def get_status(self) -> dict:
        return {
            "status": _LEGACY_STATUS.get(self.status, self.status),
            "progress": self.progress[0],
            "message": self.message,
        }

    def __repr__(self):
        return f"JobHandle({self.id}, {self.function!r}, {self.status!r})"


class Run:
    """The run of one job: its data is the branch from the input revision"""

    def __init__(self, session: CaseSession, info: RunInfo):
        self._session = session
        self.info = info
        self.id = info.id
        self.function = info.function
        self.job_id = info.job_id
        self.status = info.status
        self.outdated = info.outdated
        self.fingerprint = info.fingerprint
        self.kept = info.kept
        self.input_revision = info.input_revision
        self.tip_revision = info.tip_revision
        self.release_id = info.release_id

    def state(self) -> dict:
        """Data of the run (the case's state tree at the run's tip)"""
        session = self._session
        return session.store.state(session.case_id, self.tip_revision)

    def fork(self, name: str) -> int:
        """New case from the run (its input and its data); returns its id"""
        session = self._session
        return session.store.copy_case(
            session.case_id, run_id=self.id, name=name
        ).id

    def keep(self) -> None:
        """Exclude the run from retention"""
        self._session.store.keep(self.id)
        self.kept = True

    def changes(self):
        return self._session.store.run_changes(self.id)

    def __repr__(self):
        return f"Run({self.id}, {self.function!r}, {self.status!r}, outdated={self.outdated})"


class RunList(Sequence):
    """Runs of one compute function of a case, oldest first"""

    def __init__(self, session: CaseSession, function: str):
        self._session = session
        self.function = function
        self._runs = [
            Run(session, info)
            for info in session.store.runs(session.case_id, function)
        ]

    def __getitem__(self, index):
        return self._runs[index]

    def __len__(self):
        return len(self._runs)

    @property
    def latest(self) -> Run | None:
        """The run of the latest succeeded job"""
        done = [r for r in self._runs if r.status == "succeeded"]
        return max(done, key=lambda r: r.job_id) if done else None


def runs(app, function) -> RunList:
    session = app.case_session
    if session is None:
        raise RuntimeError("the app is not attached to a case store")
    return RunList(session, function_name(function))


# seconds the newest events of a job are kept for handles created later
RECENT_JOB_EVENTS_S = 60.0


class JobEvents:
    """Status and progress events of the case's jobs, forwarded to their
    handles; the newest ones are replayed to handles created later (events
    processed while a submit was in flight)"""

    def __init__(self, session: CaseSession):
        self.session = session
        self._handles: dict[int, list] = {}
        self._recent: dict[int, dict] = {}
        session.on_event(self._on_event)

    def track(self, handle: JobHandle):
        refs = self._handles.setdefault(handle.id, [])
        refs.append(weakref.ref(handle))
        recent = self._recent.get(handle.id)
        if recent is None:
            return
        if "status" in recent:
            handle._event(recent["status"])
        if "progress" in recent and not handle.done:
            handle.progress = recent["progress"]

    def _remember(self, job_id, kind, value):
        now = time.monotonic()
        for old in [
            j
            for j, r in self._recent.items()
            if now - r["at"] > RECENT_JOB_EVENTS_S
        ]:
            del self._recent[old]
        recent = self._recent.setdefault(job_id, {})
        recent["at"] = now
        recent[kind] = value

    def _handles_of(self, job_id):
        refs = self._handles.get(job_id, [])
        handles = [h for h in (r() for r in refs) if h is not None]
        if len(handles) != len(refs):
            self._handles[job_id] = [weakref.ref(h) for h in handles]
        return handles

    def _on_event(self, event):
        payload = event.payload
        if payload.get("case_id", self.session.case_id) != self.session.case_id:
            return
        if event.type == "job.status":
            self._remember(payload.get("job_id"), "status", payload)
            for handle in self._handles_of(payload.get("job_id")):
                handle._event(payload)
        elif event.type == "job.progress":
            value = (payload.get("fraction"), payload.get("text") or "")
            self._remember(payload.get("job_id"), "progress", value)
            for handle in self._handles_of(payload.get("job_id")):
                handle.progress = value


# -- the job side --


def checkpoint_interval(
    age: float, quiet: int = 0, start: float = 1.5, maximum: float = 60.0
) -> float:
    """Seconds between checkpoints: start for young jobs, growing with
    the job's age (age / 60, so maximum after one hour) and doubling with every
    check that found nothing to commit (quiet), at most maximum"""
    base = min(maximum, max(start, age / 60.0))
    return min(maximum, base * 2**quiet)


class JobFrontend(BaseFrontend):
    """A job has no browser: changes reach clients through commits"""

    def update_component(self, comp, data, method, blocking=True):
        pass

    def reset_app(self, app):
        pass

    def get_query_parameter(self, name: str, default=None):
        return default


def job_environment():
    """Environment of a job process"""
    from .utils import set_environment

    env = set_environment(EnvironmentType.COMPUTE, have_backend=False)
    env.frontend = JobFrontend(None)
    env.data_layer = True
    return env


def app_from_config(config: dict):
    """Factory of the app of a job from the app's configuration (python_class)"""
    from .app import _get_app_config
    from .components.basecomponent import reset_components

    cfg = _get_app_config(dict(config))
    module_name, _, class_name = cfg.python_class.rpartition(".")
    cls = getattr(importlib.import_module(module_name), class_name)
    cls._config = cfg

    def make():
        reset_components()
        return cls()

    return make


class JobSession(CaseSession):
    """CaseSession of a job attempt on a JobStore

    A change is committed as checkpoint at least checkpoint_interval(age) after
    the previous one (the start of the job for the first), so about 1.5 s at
    the start and once per minute after one hour. Changes that do not notify
    the session (in-place mutation) are found by checks at the same interval,
    doubling while nothing changes. progress() and App.save() checkpoint at
    once if the last checkpoint is older than min_interval. run() runs the
    function and makes the final commit.
    """

    def __init__(
        self,
        app,
        store,
        case_id: int,
        *,
        start_interval: float = 1.5,
        min_interval: float = 1.0,
        max_interval: float = 60.0,
        on_ended=None,
        **options,
    ):
        super().__init__(
            app,
            store,
            case_id,
            min_interval=min_interval,
            max_interval=max_interval,
            **options,
        )
        self.start_interval = start_interval
        self.started_at = self.scheduler.now()
        self.last_checkpoint: float | None = None
        self.quiet = 0
        self.checkpoints = 0
        self.ended: Exception | None = None
        self.on_ended = on_ended
        self.final: int | None = None
        self._due = None

    def _job_events(self):
        return None

    def age(self) -> float:
        return self.scheduler.now() - self.started_at

    def interval(self, quiet: int = 0) -> float:
        return checkpoint_interval(
            self.age(), quiet, self.start_interval, self.max_interval
        )

    def _last(self) -> float:
        return (
            self.started_at
            if self.last_checkpoint is None
            else self.last_checkpoint
        )

    def _arm_at(self, due: float):
        if self._timer is not None:
            self._timer.cancel()
        self._due = due
        self._timer = self.scheduler.call_later(
            due - self.scheduler.now(), self._autosave_fire
        )

    def schedule_autosave(self):
        if self._applying or self.closed or self.final is not None:
            return
        if self.ended is not None:
            raise self.ended
        self.quiet = 0
        due = max(self.scheduler.now(), self._last() + self.interval())
        if self._timer is None or self._due > due + 1e-9:
            self._arm_at(due)

    def _autosave_fire(self):
        self._timer = None
        if self.closed or self.final is not None or self.ended is not None:
            return
        due = self._last() + self.interval()
        if due > self.scheduler.now() + 1e-9:
            # an explicit checkpoint (progress, save) came in between
            self._arm_at(due)
            return
        self.checkpoint()
        if self.ended is None and self.final is None and self._timer is None:
            self._arm_at(self.scheduler.now() + self.interval(self.quiet))

    def _end(self, error: Exception):
        self.ended = error
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None
        if self.on_ended is not None:
            self.on_ended(error)

    def checkpoint(self, raise_ended: bool = False) -> bool:
        """Commit the pending changes as checkpoint; False if there were none"""
        with self._lock:
            if self.final is not None or self.closed or self.ended is not None:
                return False
            before = self.base_revision
            try:
                revision = self.commit()
            except (JobEndedError, CaseDeletedError) as e:
                self._end(e)
                if raise_ended:
                    raise
                return False
            except Exception as e:
                self._report_error(e)
                return False
            changed = revision != before
            if changed:
                self.last_checkpoint = self.scheduler.now()
                self.quiet = 0
                self.checkpoints += 1
            else:
                self.quiet += 1
            return changed

    def _soon(self):
        """Checkpoint now if the last one is older than the minimum interval"""
        if self.ended is not None:
            raise self.ended
        if self.scheduler.now() - self._last() >= self.min_interval:
            self.checkpoint(raise_ended=True)

    def save(self) -> int:
        self._soon()
        return self.base_revision

    def progress(self, fraction: float | None = None, text: str | None = None):
        self.store.progress(fraction, text)
        self._soon()

    def finish(self) -> int:
        """The final commit: pending changes and the end of the run branch"""
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None
            if self.ended is not None:
                raise self.ended
            self.final = self.commit(kind="final")
        return self.final

    def resolve(self, function: str):
        """Component and compute method of a qualified function name"""
        *path, method = function.split(".")
        comp = self._walk().get(tuple(path))
        if comp is None and path == ["__app__"]:
            comp = self.app
        if comp is None:
            raise LookupError(f"component {path} of {function} not found")
        func = getattr(comp, method, None)
        if func is None or not hasattr(func, "__ngapp_compute__"):
            raise LookupError(f"{function} is not a compute function")
        return comp, func

    def run(
        self,
        function: str,
        args=(),
        kwargs=None,
        compute_env: dict | None = None,
    ):
        """Run the compute function and make the final commit; changes made
        before a failure are committed as checkpoint"""
        _, func = self.resolve(function)
        env = compute_env or {}
        if (
            env.get("env_type", "local") != "local"
            and env.get("name") != func.__ngapp_compute__.env
        ):
            raise RuntimeError(
                f"{function} is not allowed in compute environment {env.get('name')!r}"
            )
        token = _current.set(self)
        try:
            result = func(*args, **(kwargs or {}))
        except BaseException:
            if self.ended is None:
                self.checkpoint()
            raise
        finally:
            _current.reset(token)
        self.finish()
        return result


def run_job(
    client,
    data: dict | None = None,
    *,
    app_factory=None,
    scheduler=None,
    on_ended=None,
):
    """Rebuild the app from the job's input, run the function with its
    arguments and commit through the client; returns the JobSession"""
    from .store.job import JobStore

    store = JobStore(client)
    make = app_factory or app_from_config(data["app"])
    app = make()
    session = JobSession.open(
        app, store, store.case_id, scheduler=scheduler, on_ended=on_ended
    )
    try:
        session.run(
            store.input["function"],
            store.input["args"],
            store.input["kwargs"],
            (data or {}).get("compute_env"),
        )
    finally:
        session.close()
    return session


def interrupt_main(error):
    """on_ended of job processes: a checkpoint in a timer thread learned that
    the attempt ended, stop the function in the main thread"""
    import _thread

    if threading.current_thread() is not threading.main_thread():
        _thread.interrupt_main()
