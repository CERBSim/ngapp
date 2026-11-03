"""Component state and the connection of an app to a case store

``comp.state`` holds values that are part of the case but not sent to the
browser. A CaseSession connects an App to a case in a CaseStore: it loads
the case into the components, collects operations from changed UI props,
slots and state, commits them (autosave or ``App.commit``) and applies
changes of other writers.
"""

import collections
import copy as copy_module
import io
import logging
import math
import re
import threading
import time
import uuid
import weakref
from collections.abc import Mapping, MutableMapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np
import orjson

from .observable import Observable
from .store.encoding import (
    INLINE_LIMIT,
    EncodedValue,
    decode_value,
    encode_value,
    escape_key,
    iter_blob_refs,
    unescape_key,
    value_key,
)
from .store.tree import (
    ABSENT,
    CASE_NAME,
    SECTIONS,
    Seq,
    flatten,
    is_under,
    is_value_path,
    stored_key,
)
from .store.types import (
    BaseGoneError,
    BlobRef,
    CaseDeletedError,
    ConflictError,
    ForbiddenError,
    InvalidError,
    JobInfo,
    JobRequest,
    MissingBlobsError,
    NotFoundError,
    Op,
    RateLimitedError,
    ReleaseTooOldError,
    TransientStoreError,
    UnauthorizedError,
)
from .utils import get_environment, is_pyodide, print_exception

logger = logging.getLogger("ngapp.state")

_MISSING = object()
_IMMUTABLE = (str, bytes, int, float, bool, type(None))


def data_layer_enabled() -> bool:
    try:
        return get_environment().data_layer
    except RuntimeError:
        return False


def _freeze(value):
    if isinstance(value, np.ndarray):
        try:
            value.flags.writeable = False
        except ValueError:
            pass
    return value


def _text_only(items) -> bool:
    return (
        isinstance(items, list)
        and len(items) > 0
        and all(isinstance(i, str) for i in items)
    )


def _export(value):
    if value is ABSENT:
        return None
    if isinstance(value, Seq):
        return value.to_json()
    return value


def _as_seq(value) -> Seq:
    if isinstance(value, Seq):
        return value
    return Seq(value) if isinstance(value, list) else Seq()


def _encoded(value) -> tuple:
    ev = encode_value(value)
    return ev.stored, ev.key, value, ev.blobs, ev.large


def _is_large(value) -> bool:
    if isinstance(value, np.ndarray):
        return value.nbytes > INLINE_LIMIT
    if isinstance(value, (bytes, bytearray, memoryview)):
        return len(value) > INLINE_LIMIT
    return False


def _is_blob(stored) -> bool:
    return isinstance(stored, dict) and (
        "$blob" in stored or "$artifact" in stored
    )


class _Entry:
    """A state value: stored form, content key and the decoded object"""

    __slots__ = (
        "stored",
        "key",
        "obj",
        "blobs",
        "large",
        "pickle",
        "lazy",
        "mut_key",
    )

    def __init__(
        self,
        stored,
        key,
        obj=_MISSING,
        blobs=None,
        large=False,
        pickle=False,
        lazy=None,
    ):
        self.stored = stored
        self.key = key
        self.obj = obj
        self.blobs = blobs or {}
        self.large = large
        self.pickle = pickle
        self.lazy = lazy
        self.mut_key = key

    @classmethod
    def from_stored(cls, stored, key=None, blobs=None):
        pickle = isinstance(stored, dict) and stored.get("enc") == "pickle"
        return cls(
            stored,
            key or value_key(stored),
            blobs=blobs,
            large=_is_blob(stored),
            pickle=pickle,
        )

    @property
    def mutable(self) -> bool:
        obj = self.obj
        if obj is _MISSING or isinstance(obj, _IMMUTABLE):
            return False
        if isinstance(obj, np.ndarray) and not obj.flags.writeable:
            return False
        return True

    def update(self, ev: EncodedValue):
        self.stored, self.key, self.blobs, self.large = (
            ev.stored,
            ev.key,
            ev.blobs,
            ev.large,
        )
        self.mut_key = ev.key


class _SeqEntry:
    """A sequence: committed items and local appends not committed yet;
    fresh if it replaces a sequence deleted locally"""

    __slots__ = ("items", "pending", "fresh")

    def __init__(self, items=(), fresh=False):
        self.items = list(items)
        self.pending = []
        self.fresh = fresh

    @classmethod
    def from_seq(cls, seq: Seq):
        return cls(
            _Entry.from_stored(v, k) for v, k in zip(seq.items, seq.keys)
        )


class ValueReadError(RuntimeError):
    """A stored value could not be loaded or decoded"""

    def __init__(self, path: tuple, error: Exception):
        self.path = path
        self.error = error
        super().__init__(f"Cannot read {'/'.join(path)}: {error}")


class _StateData:
    def __init__(self, component):
        self.component = component
        self.values: dict[str, _Entry | _SeqEntry] = {}
        self.deleted: set[str] = set()
        self.callbacks: list[tuple[str, Callable, bool]] = []
        self.observables: dict[str, Observable] = {}
        self.syncing = False


def _state_data(component) -> _StateData:
    data = component.__dict__.get("_state_data")
    if data is None:
        data = component._state_data = _StateData(component)
    return data


def session_of(component) -> "CaseSession | None":
    ctx = component.context
    if ctx is None or ctx.app is None:
        return None
    return getattr(ctx.app, "case_session", None)


class State(MutableMapping):
    """Values of a component that are stored in the case but not sent to the
    browser. Keys are strings; reading a blob value loads it on first access.

    A State is used like a dict (``state[key]``, ``in``, iteration,
    ``update``, ``pop``, ``dict(state)``); ``comp.state = {...}`` replaces its
    values and a copy or pickle of it is a dict. Keys that do not start with
    ``_`` and are not named like a method are also attributes. A value
    changed in place (``state["a"]["b"] = 1``) is stored by the next save or
    commit, assigning the key again stores it with the next autosave."""

    def __init__(self, component, prefix: str = ""):
        object.__setattr__(self, "_component", component)
        object.__setattr__(self, "_prefix", prefix)

    @property
    def _data(self) -> _StateData:
        return _state_data(self._component)

    def _full(self, key: str) -> str:
        if not isinstance(key, str) or not key:
            raise KeyError(f"Invalid state key {key!r}")
        if "/" in key:
            raise KeyError(f"State key {key!r} must not contain '/', use ns()")
        return self._prefix + key

    def _check_identity(self):
        if not self._component._id:
            raise RuntimeError(
                f"{type(self._component).__name__} needs an id to use state"
            )

    def __getattr__(self, key: str) -> Any:
        if key.startswith("_"):
            raise AttributeError(key)
        value = self.get(key, _MISSING)
        if value is _MISSING:
            raise AttributeError(f"state has no key {key!r}")
        return value

    def __setattr__(self, key: str, value: Any) -> None:
        if key.startswith("_") or hasattr(type(self), key):
            raise AttributeError(f"Use state.set({key!r}, value) for this key")
        self.set(key, value)

    def __delattr__(self, key: str) -> None:
        if key not in self:
            raise AttributeError(f"state has no key {key!r}")
        self.delete(key)

    def __contains__(self, key) -> bool:
        try:
            return self._entry(self._full(key)) is not None
        except KeyError:
            return False

    def __getitem__(self, key: str) -> Any:
        value = self.get(key, _MISSING)
        if value is _MISSING:
            raise KeyError(key)
        return value

    def __setitem__(self, key: str, value: Any) -> None:
        self.set(key, value)

    def __delitem__(self, key: str) -> None:
        self.delete(key)

    def __iter__(self):
        return iter(self.keys())

    def __len__(self) -> int:
        return len(self.keys())

    def copy(self) -> dict:
        """The values as dict, sequences as lists"""
        return {
            k: v.copy() if isinstance(v, StateList) else v
            for k, v in self.items()
        }

    __copy__ = copy

    def __deepcopy__(self, memo):
        return copy_module.deepcopy(self.copy(), memo)

    def __reduce__(self):
        return dict, (self.copy(),)

    def _assign(self, values: Mapping) -> None:
        """Replace the values by the ones of a mapping (comp.state = {...})"""
        values = values.copy() if isinstance(values, State) else dict(values)
        for key in self.keys():
            if key not in values:
                self.delete(key)
        self.update(values)

    def __repr__(self):
        return f"State({self._component._id!r}, {self.keys()})"

    def _entry(self, full: str):
        return self._data.values.get(full)

    def keys(self) -> list[str]:
        n = len(self._prefix)
        return [
            k[n:]
            for k in self._data.values
            if k.startswith(self._prefix) and "/" not in k[n:]
        ]

    def get(self, key: str, default=None, *, cache=True) -> Any:
        entry = self._entry(self._full(key))
        if entry is None:
            return default
        if isinstance(entry, _SeqEntry):
            return StateList(self, key)
        return self._value(entry, cache)

    def set(
        self, key: str, value: Any, *, pickle=False, lazy: bool | None = None
    ) -> None:
        self._check_identity()
        full = self._full(key)
        # encoding a large value takes a while: the session shows it as saving
        session = session_of(self._component) if _is_large(value) else None
        if session is not None:
            session._encoding(1)
        try:
            self._set(full, value, pickle, lazy)
        finally:
            if session is not None:
                session._encoding(-1)

    def _set(self, full, value, pickle, lazy):
        ev = encode_value(value, pickle=pickle, lazy=lazy)
        data = self._data
        old = data.values.get(full)
        if isinstance(old, _Entry) and old.key == ev.key:
            old.obj = _freeze(value) if old.large else value
            old.mut_key = ev.key
            return
        if ev.large:
            _freeze(value)
        data.values[full] = _Entry(
            ev.stored, ev.key, value, ev.blobs, ev.large, pickle, lazy
        )
        self._changed(full, value)

    def delete(self, key: str) -> None:
        full = self._full(key)
        data = self._data
        if full not in data.values:
            raise KeyError(key)
        del data.values[full]
        data.deleted.add(full)
        self._changed(full, None)

    def list(self, key: str) -> "StateList":
        entry = self._entry(self._full(key))
        if isinstance(entry, _Entry) and not isinstance(
            self._value(entry, True), list
        ):
            raise TypeError(f"state key {key!r} holds a value, not a list")
        return StateList(self, key)

    def observe(self, key: str) -> Observable:
        """Observable bound to a key: assigning its value sets the key, and
        local and remote changes of the key update it"""
        full = self._full(key)
        data = self._data
        obs = data.observables.get(full)
        if obs is None:
            try:
                value = self.get(key)
            except ValueReadError:
                value = None
            obs = Observable(value, key)

            def to_state(new, _old):
                if not data.syncing:
                    self.set(key, new)

            obs.on_change(to_state)
            data.observables[full] = obs
        return obs

    def on_change(
        self, callback: Callable[[set[str]], None]
    ) -> Callable[[], None]:
        """Call callback(changed_keys) when changes of other writers are
        applied (pulled revisions, job results, adopted conflicts)"""
        item = (self._prefix, callback, False)
        callbacks = self._data.callbacks
        callbacks.append(item)

        def dispose():
            if item in callbacks:
                callbacks.remove(item)

        return dispose

    def ns(self, name: str) -> "State":
        if not name or "/" in name:
            raise ValueError(f"Invalid namespace {name!r}")
        return State(self._component, self._prefix + name + "/")

    async def prefetch(self, *keys: str) -> None:
        entries = []
        for key in keys or self.keys():
            entry = self._entry(self._full(key))
            if isinstance(entry, _Entry):
                entries.append(entry)
            elif isinstance(entry, _SeqEntry):
                entries.extend(entry.items + entry.pending)
        session = session_of(self._component)
        if session is not None:
            session.prefetch(
                ref
                for e in entries
                if e.obj is _MISSING
                for ref in iter_blob_refs(e.stored)
                if ref.hash not in e.blobs
            )
        for entry in entries:
            self._value(entry, True)

    def _value(self, entry: _Entry, cache: bool):
        if entry.obj is not _MISSING:
            return entry.obj
        try:
            value = decode_value(entry.stored, self._reader(entry))
        except Exception as e:
            raise self._read_failed(entry, e) from e
        if entry.large:
            _freeze(value)
        if cache:
            entry.obj = value
            if entry.pickle:
                entry.mut_key = encode_value(
                    value, pickle=True, lazy=entry.lazy
                ).key
        return value

    def _read_failed(self, entry: _Entry, error: Exception) -> ValueReadError:
        """Report a value that cannot be read (once per value) and return the
        error naming its path"""
        if isinstance(error, ValueReadError):
            return error
        session = session_of(self._component)
        data = self._data
        full = next(
            (
                k
                for k, e in data.values.items()
                if e is entry
                or (isinstance(e, _SeqEntry) and entry in e.items + e.pending)
            ),
            None,
        )
        path = tuple(self._component._fullid.split(".")) + (
            "state",
            escape_key(full or "?"),
        )
        err = ValueReadError(path, error)
        if session is not None:
            session._read_failed(err, entry.key)
        else:
            logger.error("%s", err)
        return err

    def _reader(self, entry: _Entry):
        def read(ref: BlobRef) -> bytes:
            if ref.hash in entry.blobs:
                return entry.blobs[ref.hash][1]
            session = session_of(self._component)
            if session is None:
                raise RuntimeError(
                    "State value is not loaded and no case store is attached"
                )
            return session.read_blob(ref)

        return read

    def _changed(self, full: str, value):
        data = self._data
        obs = data.observables.get(full)
        if obs is not None and not data.syncing:
            data.syncing = True
            try:
                obs.value = value
            finally:
                data.syncing = False
        session = session_of(self._component)
        if session is not None:
            session.schedule_autosave()


class StateList(Sequence):
    """Append-only sequence in the state; positions are assigned by the
    server in commit order, so concurrent appends never collide"""

    def __init__(self, state: State, key: str):
        self._state = state
        self._key = key
        self._fullkey = state._full(key)

    def _entry(self) -> _SeqEntry | None:
        entry = self._state._entry(self._fullkey)
        return entry if isinstance(entry, _SeqEntry) else None

    def _items(self):
        entry = self._entry()
        if entry is None:
            return self._list_items()
        return entry.items + entry.pending

    def _list_items(self):
        """Items of a plain list value (appending makes it a sequence)"""
        entry = self._state._entry(self._fullkey)
        if not isinstance(entry, _Entry):
            return []
        value = self._state._value(entry, True)
        if not isinstance(value, list):
            return []
        return [_Entry(*_encoded(v)) for v in value]

    def __len__(self):
        entry = self._entry()
        if entry is None:
            return len(self._list_items())
        return len(entry.items) + len(entry.pending)

    def __getitem__(self, index):
        items = self._items()
        if isinstance(index, slice):
            return [self._state._value(e, True) for e in items[index]]
        return self._state._value(items[index], True)

    def __eq__(self, other):
        if isinstance(other, (list, StateList)):
            return self[:] == other[:]
        return NotImplemented

    def copy(self) -> list:
        return self[:]

    __copy__ = copy

    def __deepcopy__(self, memo):
        return copy_module.deepcopy(self[:], memo)

    def __reduce__(self):
        return list, (self[:],)

    def append(self, value: Any, *, pickle=False) -> None:
        state = self._state
        state._check_identity()
        ev = encode_value(value, pickle=pickle)
        data = state._data
        entry = self._entry()
        if entry is None:
            old = data.values.get(self._fullkey)
            if isinstance(old, _Entry):
                # appending to a plain list makes it a sequence, stored anew
                if not isinstance(state._value(old, True), list):
                    raise TypeError(
                        f"state key {self._key!r} holds a value, not a list"
                    )
                entry = _SeqEntry(fresh=True)
                entry.pending = self._list_items()
                data.values[self._fullkey] = entry
            else:
                entry = data.values[self._fullkey] = _SeqEntry(
                    fresh=self._fullkey in data.deleted
                )
        if ev.large:
            _freeze(value)
        entry.pending.append(
            _Entry(ev.stored, ev.key, value, ev.blobs, ev.large, pickle)
        )
        session = session_of(state._component)
        if session is not None:
            session.schedule_autosave()

    def __repr__(self):
        return f"StateList({self._key!r}, len={len(self)})"


def snapshot_defaults(component):
    """Remember the constructor's props and text slots of a component"""
    props = {}
    for key, value in dict(component._dump() or {}).items():
        if callable(value):
            continue
        try:
            props[key] = encode_value(value)
        except (TypeError, ValueError):
            continue
    slots = {
        name: encode_value(list(items))
        for name, items in component.ui_slots.items()
        if _text_only(items)
    }
    component._prop_defaults = props
    component._slot_defaults = slots


# -- compatibility of Storage --

_list_item = re.compile(r"^(.*)#(\d+)$")

# namespace of the Storage values in the state: they do not show up as
# keys of comp.state
STORAGE_NS = "storage"


def storage_state(component) -> State:
    return component._get_state().ns(STORAGE_NS)


def storage_set(state: State, key, value, use_pickle=False):
    try:
        state.set(key, value, pickle=use_pickle)
    except TypeError:
        if use_pickle:
            raise
        value = orjson.loads(
            orjson.dumps(value, option=orjson.OPT_SERIALIZE_NUMPY)
        )
        state.set(key, value)


def storage_get(state: State, key, default=None, cache=True):
    if key in state:
        value = state.get(key, default, cache=cache)
        return list(value) if isinstance(value, StateList) else value
    m = _list_item.match(key)
    if m and m.group(1) in state:
        items = state.get(m.group(1))
        i = int(m.group(2))
        if isinstance(items, StateList) and i < len(items):
            return items[i]
    return default


def storage_delete(state: State, key):
    if key in state:
        state.delete(key)


def storage_list(state: State, key) -> list:
    return list(state.get(key)) if key in state else []


def storage_list_len(state: State, key) -> int:
    value = state.get(key) if key in state else None
    return len(value) if isinstance(value, StateList) else 0


def storage_on_change(state: State, callback):
    """Storage.on_change: list appends are reported as "key#i" as before"""

    def wrapper(changed, appended):
        keys = set(changed)
        for key, positions in appended.items():
            keys.update(f"{key}#{i}" for i in positions)
        callback(keys)

    item = (state._prefix, wrapper, True)
    callbacks = state._data.callbacks
    callbacks.append(item)
    return lambda: callbacks.remove(item) if item in callbacks else None


# -- schedulers --


class _Handle:
    __slots__ = ("fn", "cancelled", "timer")

    def __init__(self, fn):
        self.fn = fn
        self.cancelled = False
        self.timer = None

    def cancel(self):
        self.cancelled = True
        if self.timer is not None:
            self.timer.cancel()


class ThreadingScheduler:
    def now(self) -> float:
        return time.monotonic()

    def call_later(self, delay: float, fn) -> _Handle:
        handle = _Handle(fn)

        def run():
            if not handle.cancelled:
                fn()

        handle.timer = threading.Timer(max(delay, 0.0), run)
        handle.timer.daemon = True
        handle.timer.start()
        return handle


class _JsHandle:
    def __init__(self, timer_id):
        self.timer_id = timer_id

    def cancel(self):
        import js

        js.clearTimeout(self.timer_id)


class JsScheduler:
    """setTimeout in pyodide"""

    def now(self) -> float:
        return time.monotonic()

    def call_later(self, delay: float, fn):
        import js
        from pyodide.ffi import create_once_callable

        return _JsHandle(
            js.setTimeout(create_once_callable(fn), int(delay * 1000))
        )


def default_scheduler():
    return JsScheduler() if is_pyodide() else ThreadingScheduler()


# -- case session --


@dataclass
class ReplacedEdit:
    """A local edit replaced by the head value after a conflict"""

    path: tuple
    mine: Any
    head: Any
    blobs: dict = field(default_factory=dict, repr=False)


@dataclass
class _Changes:
    keys: dict = field(default_factory=dict)
    appended: dict = field(default_factory=dict)
    any: bool = False

    def add(self, comp, key, pos=None):
        self.any = True
        if comp is None:
            return
        self.keys.setdefault(comp, set()).add(key)
        if pos is not None:
            self.appended.setdefault(comp, {}).setdefault(key, []).append(pos)


class CaseSession:
    """Connection of an App to one case of a CaseStore

    Options: autosave_delay and autosave_max_delay (debounce, seconds),
    min_interval and max_interval (rate limit of autosave commits),
    echo_limit (consecutive commits caused by change callbacks before the
    client is logged and slowed down), retries (transient store errors).

    Without a case id the session is new: the first commit after an edit
    creates the case (app_id, default the app's).
    """

    def __init__(
        self,
        app,
        store,
        case_id: int | None,
        *,
        app_id: int | None = None,
        scheduler=None,
        autosave_delay: float = 1.0,
        autosave_max_delay: float = 5.0,
        min_interval: float = 1.0,
        max_interval: float = 60.0,
        echo_limit: int = 3,
        retries: int = 3,
    ):
        self.app = app
        self.store = store
        self.case_id = case_id
        self.app_id = app_id
        self.scheduler = scheduler or default_scheduler()
        self.autosave_delay = autosave_delay
        self.autosave_max_delay = autosave_max_delay
        self.min_interval = min_interval
        self.max_interval = max_interval
        self.echo_limit = echo_limit
        self.retries = retries
        self.base_revision: int | None = None
        self.release_id = None
        self.base: dict = {}
        self.base_keys: dict = {}
        self.replaced: list[ReplacedEdit] = []
        self.events = collections.deque(maxlen=1000)
        self.last_error: Exception | None = None
        self.blocked: str | None = None
        self.closed = False
        self.commit_count = 0
        self.echo_warnings = 0
        self._index: dict[tuple, set] = {}
        self._components: dict[tuple, weakref.ref] = {}
        self._pending_deletes: list[tuple] = []
        self._lock = threading.RLock()
        self._timer = None
        self._dirty_since = None
        self._last_change = None
        self._next_allowed = -math.inf
        self._error_delay = min_interval
        self._echo_count = 0
        self._echo_dirty = False
        self._user_dirty = False
        self._in_callbacks = False
        self._applying = False
        self._inbox = []
        self._inbox_scheduled = False
        self._unsubscribe = None
        self._warned_props = set()
        self._error_callbacks = []
        self._conflict_callbacks = []
        self._event_callbacks = []
        self._pending_callbacks = []
        self._status_callbacks = []
        self._created_callbacks = []
        self._read_error_callbacks = []
        # large values being encoded (shown as saving)
        self._encoding_values = 0
        # local values with blobs not uploaded yet (shown as saving)
        self._large_pending = False
        # local edits made while read only (no_write): not committed and not
        # exported until the user keeps them (keep_held) or drops them
        self._held = False
        self._read_errors = set()
        # local edits since the last commit (change counter for commits)
        self._dirty = False
        self._edits = 0
        self._saving = False
        self._opening = False
        self._initial: dict = {}
        self._status = None
        # blobs the store has: uploaded or reported present
        self._uploaded: set[str] = set()
        # imported operations of components that do not exist yet
        self._detached: list[Op] = []
        self.job_events = None

    # -- opening --

    @classmethod
    def open(cls, app, store, case_id: int | None, **options) -> "CaseSession":
        """Open a case; None opens a new one, created by the first commit"""
        session = cls(app, store, case_id, **options)
        session._attach()
        return session

    @classmethod
    def create(
        cls, app, store, *, app_id=None, name=None, **options
    ) -> "CaseSession":
        """Create a case and store the app's values as its first revision"""
        app_id = app._config.id if app_id is None else app_id
        name = app.name if name is None else name
        info = store.create_case(app_id, name or "", [])
        session = cls(app, store, info.id, **options)
        session._attach()
        session.commit()
        return session

    def _attach(self):
        app = self.app
        if getattr(app, "case_session", None) is not None:
            raise RuntimeError("App is already attached to a case")
        with self._lock:
            app.case_session = self
            try:
                self._load()
            except BaseException:
                self.close()
                raise
        if self.case_id is None:
            # values set by load handlers of a new case are no edits
            self._applying = True
            try:
                app._emit_recursive("load")
            finally:
                self._applying = False
            self._initial = self._op_keys(self._collect()[0])
            return
        app._emit_recursive("load")
        self._initial = self._op_keys(self._collect()[0])
        self._opening = True
        try:
            self.schedule_autosave()
        finally:
            self._opening = False

    def _load(self):
        app = self.app
        if self.case_id is None:
            state = {
                "revision": None,
                "release": getattr(self.store, "release_id", None),
            }
        else:
            state = self.store.state(self.case_id)
            # events after the position read before the state; without one, all
            self._unsubscribe = self.store.subscribe(
                [self.case_id], state.get("event_seq") or 0, self._on_event
            )
            if not getattr(self.store.case(self.case_id), "write", True):
                self.blocked = "no_write"
        self.base_revision = state["revision"]
        self.release_id = state.get("release")
        self.base, self.base_keys, self._index = {}, {}, {}
        for path, value in flatten(state).items():
            self._base_set(path, value)
        if self.case_id is not None:
            self.job_events = self._job_events()
        app._emit_recursive("before_load")
        self._applying = True
        try:
            for path, comp in self._walk(bind=False).items():
                snapshot_defaults(comp)
                self._bind(path, comp)
            name = self.base.get(CASE_NAME, ABSENT)
            if isinstance(name, str):
                app.file_data.name = name
            app.file_data.id = self.case_id
        finally:
            self._applying = False

    def _job_events(self):
        """Status and progress of the case's jobs for their handles"""
        from .jobs import JobEvents

        return JobEvents(self)

    def close(self):
        with self._lock:
            self.closed = True
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None
            if self._unsubscribe is not None:
                self._unsubscribe()
                self._unsubscribe = None
            if getattr(self.app, "case_session", None) is self:
                self.app.case_session = None

    # -- callbacks --

    def on_error(self, callback) -> Callable[[], None]:
        self._error_callbacks.append(callback)
        return lambda: self._error_callbacks.remove(callback)

    def on_conflict(self, callback) -> Callable[[], None]:
        """callback(replaced_edits) after local edits were replaced by the
        head values (409 or pulled changes of the same paths)"""
        self._conflict_callbacks.append(callback)
        return lambda: self._conflict_callbacks.remove(callback)

    def on_event(self, callback) -> Callable[[], None]:
        self._event_callbacks.append(callback)
        return lambda: self._event_callbacks.remove(callback)

    def on_pending_change(self, callback) -> Callable[[], None]:
        """callback() after local edits and after commits and pulls, e.g. to
        store export_pending() durably"""
        self._pending_callbacks.append(callback)
        return lambda: self._pending_callbacks.remove(callback)

    def on_status(self, callback) -> Callable[[], None]:
        """callback(status) when status changes"""
        self._status_callbacks.append(callback)
        return lambda: self._status_callbacks.remove(callback)

    def on_created(self, callback) -> Callable[[], None]:
        """callback(case_id) when the first commit of a new case created it"""
        self._created_callbacks.append(callback)
        return lambda: self._created_callbacks.remove(callback)

    def on_read_error(self, callback) -> Callable[[], None]:
        """callback(error: ValueReadError) once per value that cannot be
        read (e.g. a codec missing in this environment), to tell the user"""
        self._read_error_callbacks.append(callback)
        return lambda: self._read_error_callbacks.remove(callback)

    def _read_failed(self, error: ValueReadError, key: str):
        if (error.path, key) in self._read_errors:
            return
        self._read_errors.add((error.path, key))
        logger.error("%s", error, exc_info=error.error)
        self._call_all(self._read_error_callbacks, error)

    def _encoding(self, delta: int):
        self._encoding_values += delta
        if delta < 0:
            self._large_pending = self._dirty and self._has_uploads()
        self._status_changed()

    def _has_uploads(self) -> bool:
        """Local state values hold blobs the store does not have yet"""
        for comp in self._walk(bind=False).values():
            data = comp.__dict__.get("_state_data")
            if data is None:
                continue
            for entry in list(data.values.values()):
                entries = (
                    entry.pending if isinstance(entry, _SeqEntry) else (entry,)
                )
                for e in entries:
                    if any(h not in self._uploaded for h in e.blobs):
                        return True
        return False

    def _call_all(self, callbacks, *args):
        for cb in list(callbacks):
            try:
                cb(*args)
            except Exception as e:
                print_exception(e)

    @property
    def status(self) -> str:
        """new (case not created yet), saved, pending (local edits), saving,
        offline (saving failed transiently, edits pending), error,
        read_only (case deleted or no write access, see read_only_reason) or
        release_too_old"""
        if self.read_only_reason is not None:
            return "read_only"
        if self.blocked:
            return self.blocked
        if self._saving or self._encoding_values:
            return "saving"
        if self.last_error is not None:
            if isinstance(self.last_error, TransientStoreError):
                return "offline"
            return "error"
        if self._dirty and self._large_pending and not self._held:
            return "saving"
        if self._dirty:
            return "pending"
        return "new" if self.case_id is None else "saved"

    @property
    def read_only_reason(self) -> str | None:
        """deleted or no_write (a read-only share) while read only"""
        return {"case_deleted": "deleted", "no_write": "no_write"}.get(
            self.blocked
        )

    @property
    def held_edits(self) -> bool:
        """Local edits made while the case was read only (or not saved when
        it became read only); after an upgrade to write they are committed
        only by keep_held() or an explicit commit, discard() drops them"""
        return self._held and self._dirty and not self.blocked

    def _status_changed(self):
        status = self.status
        if status != self._status:
            self._status = status
            self._call_all(self._status_callbacks, status)

    def _pending_changed(self):
        self._call_all(self._pending_callbacks)
        self._status_changed()

    def _block(self, error: Exception):
        if isinstance(error, CaseDeletedError):
            self.blocked = "case_deleted"
        elif isinstance(error, ReleaseTooOldError):
            self.blocked = "release_too_old"
        elif isinstance(error, ForbiddenError):
            self.blocked = "no_write"
            self._held = self._dirty

    def _report_error(self, error: Exception):
        self.last_error = error
        self._block(error)
        logger.error("Saving case %s failed: %r", self.case_id, error)
        self._call_all(self._error_callbacks, error)
        self._status_changed()

    # -- base revision --

    def _base_set(self, path, value, key=None):
        if value is ABSENT:
            if path in self.base:
                del self.base[path]
                del self.base_keys[path]
                self._index[path[:-2]].discard(path)
            return
        self.base[path] = value
        self.base_keys[path] = key or stored_key(value)
        self._index.setdefault(path[:-2], set()).add(path)

    def read_blob(self, ref: BlobRef) -> bytes:
        return self.store.read_blob(self.case_id, ref)

    def prefetch(self, refs) -> None:
        """Announce many blob reads at once, if the store can batch them"""
        prefetch = getattr(self.store, "prefetch", None)
        refs = list(refs)
        if prefetch is None or not refs:
            return
        try:
            prefetch(self.case_id, refs)
        except Exception as e:
            logger.warning("Prefetch of case %s failed: %r", self.case_id, e)

    def _decode(self, stored, blobs=None):
        blobs = blobs or {}

        def read(ref):
            if ref.hash in blobs:
                return blobs[ref.hash][1]
            return self.read_blob(ref)

        return decode_value(stored, read)

    # -- components --

    @staticmethod
    def _path_of(comp) -> tuple:
        return tuple(comp._fullid.split("."))

    def _walk(self, bind=True) -> dict:
        found = {}

        def visit(comp):
            if not comp._id or comp.__dict__.get("_case_deleted"):
                return
            path = self._path_of(comp)
            other = found.get(path)
            if other is not None and other is not comp:
                raise RuntimeError(f"Duplicate component path {list(path)}")
            found[path] = comp

        self.app._recurse(visit, True, set())
        for path, ref in list(self._components.items()):
            comp = ref()
            if comp is None or comp.__dict__.get("_case_deleted"):
                del self._components[path]
            elif path not in found:
                found[path] = comp
        if bind:
            for path, comp in found.items():
                if self._components.get(path, lambda: None)() is not comp:
                    applying, self._applying = self._applying, True
                    try:
                        if "_prop_defaults" not in comp.__dict__:
                            snapshot_defaults(comp)
                        self._bind(path, comp)
                    finally:
                        self._applying = applying
            if self._detached:
                detached, self._detached = self._detached, []
                self._apply_local(detached, found)
        return found

    def _bind(self, path, comp):
        """Apply the stored values of the base to a component"""
        props, slots = {}, {}
        data = None
        for p in sorted(self._index.get(path, ())):
            section, key, value = p[-2], unescape_key(p[-1]), self.base[p]
            if section in ("ui", "input"):
                props[key] = self._decode(value)
            elif section == "slots":
                slots[key] = self._decode(value)
            elif section == "state":
                data = data or _state_data(comp)
                data.values[key] = (
                    _SeqEntry.from_seq(value)
                    if isinstance(value, Seq)
                    else _Entry.from_stored(value, self.base_keys[p])
                )
        if props:
            full = dict(comp._dump() or {})
            full.update(props)
            comp._load(full)
        for name, items in slots.items():
            comp._set_slot(name, list(items))
        if props or slots:
            comp._update_frontend()
        self._components[path] = weakref.ref(comp)

    def delete_component(self, comp):
        """Remove the stored data of a component (and its children)"""
        with self._lock:
            path = self._path_of(comp)
            comp._case_deleted = True
            self._components.pop(path, None)
            self._pending_deletes.append(path)
        self.schedule_autosave()

    def _encode_prop(self, comp, key, value):
        if callable(value):
            return None
        try:
            return encode_value(value)
        except (TypeError, ValueError) as e:
            ident = (type(comp).__name__, key)
            if ident not in self._warned_props:
                self._warned_props.add(ident)
                logger.warning(
                    "Prop %s of %s is not stored: %s", key, ident[0], e
                )
            return None

    def _current(self, comp, section, key) -> EncodedValue | None:
        """Encoded current local value of a path, None if not stored"""
        if section in ("ui", "input"):
            dump = comp._dump() or {}
            if key not in dump:
                return None
            ev = self._encode_prop(comp, key, dump[key])
            if ev is None:
                return None
            if section == "ui":
                default = comp.__dict__.get("_prop_defaults", {}).get(key)
                if key in comp._two_way_props or (
                    default is not None and default.key == ev.key
                ):
                    return None
            elif key not in comp._two_way_props:
                return None
            return ev
        if section == "slots":
            items = comp.ui_slots.get(key)
            if not _text_only(items):
                return None
            ev = encode_value(list(items))
            default = comp.__dict__.get("_slot_defaults", {}).get(key)
            return None if default is not None and default.key == ev.key else ev
        if section == "state":
            entry = _state_data(comp).values.get(key)
            if isinstance(entry, _Entry):
                self._recheck(entry)
                return EncodedValue(
                    entry.stored, entry.key, entry.blobs, entry.large
                )
            if isinstance(entry, _SeqEntry):
                return EncodedValue(None, "seq", {}, False)
        return None

    @staticmethod
    def _recheck(entry: _Entry):
        """Re-encode a mutable value to detect in-place changes"""
        if entry.mutable:
            ev = encode_value(entry.obj, pickle=entry.pickle, lazy=entry.lazy)
            if ev.key != entry.mut_key:
                entry.update(ev)

    def _set_local(self, comp, section, key, value, blobs=None, changes=None):
        """Set the local value of a path (stored form or ABSENT)"""
        if section in ("ui", "input"):
            if value is ABSENT:
                default = comp.__dict__.get("_prop_defaults", {}).get(key)
                new = (
                    ABSENT
                    if default is None
                    else self._decode(default.stored, default.blobs)
                )
            else:
                new = self._decode(value, blobs)
            full = dict(comp._dump() or {})
            if new is ABSENT:
                full.pop(key, None)
            else:
                full[key] = new
            comp._load(full)
            binding = comp._observable_bindings.get(key)
            if binding is not None and new is not ABSENT:
                binding[0].value = new
            comp._update_frontend()
        elif section == "slots":
            if value is ABSENT:
                default = comp.__dict__.get("_slot_defaults", {}).get(key)
                if default is None:
                    return
                value = default.stored
            comp._set_slot(key, list(self._decode(value, blobs)))
        elif section == "state":
            data = _state_data(comp)
            if value is ABSENT:
                data.values.pop(key, None)
            elif isinstance(value, Seq):
                data.values[key] = _SeqEntry.from_seq(value)
            else:
                data.values[key] = _Entry.from_stored(value, blobs=blobs)
            obs = data.observables.get(key)
            if obs is not None:
                data.syncing = True
                try:
                    obs.value = (
                        State(comp).get(key) if key in data.values else None
                    )
                except ValueReadError:
                    obs.value = None
                finally:
                    data.syncing = False
            if changes is not None:
                changes.add(comp, key)

    # -- collecting operations --

    def _collect(self):
        """Operations that turn the base into the current local state"""
        found = self._walk()
        current = {}
        uploads = {}
        seq_ops = []
        seq_paths = set()
        committed = []
        for path, comp in found.items():
            self._collect_component(
                path, comp, current, seq_ops, seq_paths, committed
            )
        name = self.app.file_data.name or ""
        if name or CASE_NAME in self.base:
            current[CASE_NAME] = encode_value(name)
        ops = [Op("delete", p) for p in self._pending_deletes]
        deleted = list(self._pending_deletes)
        for p, ev in current.items():
            if any(is_under(p, d) for d in deleted):
                continue
            if ev.key != self.base_keys.get(p):
                ops.append(Op("set", p, ev.stored))
                uploads.update(ev.blobs)
        for p in self.base:
            if (
                p in current
                or p in seq_paths
                or any(is_under(p, d) for d in deleted)
            ):
                continue
            if p[:-2] in found and p[-2] in SECTIONS:
                ops.append(Op("delete", p))
        for op, blobs in seq_ops:
            ops.append(op)
            uploads.update(blobs)
        ops.extend(self._detached)
        return ops, uploads, committed

    def _collect_component(
        self, path, comp, current, seq_ops, seq_paths, committed
    ):
        dump = comp._dump()
        if dump:
            defaults = comp.__dict__.get("_prop_defaults", {})
            two_way = comp._two_way_props
            for key, value in dict(dump).items():
                ev = self._encode_prop(comp, key, value)
                if ev is None:
                    continue
                if key in two_way:
                    current[path + ("input", escape_key(key))] = ev
                else:
                    default = defaults.get(key)
                    if default is None or default.key != ev.key:
                        current[path + ("ui", escape_key(key))] = ev
        slot_defaults = comp.__dict__.get("_slot_defaults", {})
        for name, items in list(comp.ui_slots.items()):
            if _text_only(items):
                ev = encode_value(list(items))
                default = slot_defaults.get(name)
                if default is None or default.key != ev.key:
                    current[path + ("slots", escape_key(name))] = ev
        data = comp.__dict__.get("_state_data")
        if data is None:
            return
        if data.deleted:
            committed.append(data)
        for key, entry in list(data.values.items()):
            p = path + ("state", escape_key(key))
            if isinstance(entry, _Entry):
                self._recheck(entry)
                current[p] = EncodedValue(
                    entry.stored, entry.key, entry.blobs, entry.large
                )
                if entry.blobs:
                    committed.append(entry)
                continue
            seq_paths.add(p)
            if entry.fresh and p in self.base:
                seq_ops.append((Op("delete", p), {}))
            for item in entry.pending:
                seq_ops.append((Op("append", p, item.stored), item.blobs))
            if entry.pending or entry.fresh:
                committed.append((entry, len(entry.pending)))

    # -- committing --

    def _emit_before_save(self):
        from .components.basecomponent import Event

        def visit(comp):
            for event in ("before_save", "save"):
                for func in list(comp._callbacks.get(event, [])):
                    func(Event(name=event, component=comp))

        # changes of save hooks are part of this commit
        applying, self._applying = self._applying, True
        try:
            self.app._recurse(visit, False, set())
        finally:
            self._applying = applying

    def _upload(self, ops, uploads) -> str | None:
        refs = {}
        for op in ops:
            if op.op != "delete":
                for ref in iter_blob_refs(op.value):
                    refs[ref.hash] = (
                        uploads[ref.hash][0] if ref.hash in uploads else ref
                    )
        if not refs:
            return None
        result = self.store.blobs_missing(self.case_id, list(refs.values()))
        self._uploaded.update(set(refs) - set(result.missing))
        for h in result.missing:
            if h not in uploads:
                raise MissingBlobsError(
                    [h], f"content of blob {h} is not available"
                )
            ref, data = uploads[h]
            self.store.upload(result.upload_session, ref, io.BytesIO(data))
            self._uploaded.add(h)
        return result.upload_session

    def _store_commit(self, ops, kind, name, upload_session):
        key = str(uuid.uuid4())
        for attempt in range(self.retries + 1):
            try:
                return self.store.commit(
                    self.case_id,
                    self.base_revision,
                    ops,
                    kind=kind,
                    name=name,
                    upload_session=upload_session,
                    idempotency_key=key,
                )
            except TransientStoreError:
                if attempt == self.retries:
                    raise

    def commit(
        self,
        kind: str = "autosave",
        name: str | None = None,
        *,
        _retry=True,
        _auto=False,
    ) -> int:
        """Commit the pending local edits; returns the new base revision

        An exception in a save hook or in encoding aborts the commit and the
        edits stay pending. On a conflict the head values are adopted (the
        replaced edits are kept in self.replaced) and the remaining edits are
        committed once more.
        """
        with self._lock:
            if self.closed:
                raise RuntimeError("Case session is closed")
            if self.blocked == "no_write":
                raise ForbiddenError(f"no write access to case {self.case_id}")
            if self.blocked == "case_deleted":
                raise CaseDeletedError(f"case {self.case_id} was deleted")
            if self._held and _auto:
                return self.base_revision
            if self.base_revision is None and _auto and not self._edited():
                self._dirty = False
                self._status_changed()
                return None
            edits = self._edits
            # the status shows saving only while something is sent
            self._saving = True
            try:
                self._emit_before_save()
                if self.base_revision is None:
                    self._status_changed()
                    self._create_case()
                ops, uploads, committed = self._collect()
                if not ops and kind == "autosave":
                    self._dirty_since = None
                    self._echo_dirty = self._user_dirty = False
                    self._saved(edits)
                    return self.base_revision
                self._status_changed()
                upload_session = self._upload(ops, uploads)
                try:
                    result = self._store_commit(ops, kind, name, upload_session)
                except (ConflictError, BaseGoneError):
                    self.pull()
                    if _retry:
                        self._saving = False
                        return self.commit(kind, name, _retry=False, _auto=_auto)
                    raise
                except (
                    CaseDeletedError,
                    ReleaseTooOldError,
                    ForbiddenError,
                ) as e:
                    self._block(e)
                    raise
                changes = self._committed(ops, result, committed)
                self._saved(edits)
            finally:
                if self._saving:
                    self._saving = False
                    self._status_changed()
        self._notify(changes)
        return result.revision

    @staticmethod
    def _op_keys(ops) -> dict:
        return {
            (op.op, op.path): None if op.op == "delete" else value_key(op.value)
            for op in ops
        }

    def _unsaved_ops(self) -> bool:
        """Local edits not committed: changes of components that are not
        stored (e.g. set when job events arrive) mark the session dirty
        without any"""
        if not self._dirty:
            return False
        with self._lock:
            return bool(self._collect()[0])

    def _edited(self) -> bool:
        """A new case differs from the app as opened (not just by values
        the browser reports back when it shows the app)"""
        if not self._dirty:
            return False
        return self._op_keys(self._collect()[0]) != self._initial

    def _saved(self, edits: int):
        """A commit took the local edits up to the change counter edits"""
        self.last_error = None
        if self._edits == edits:
            self._dirty = False
        self._held = False
        self._large_pending = self._dirty and self._has_uploads()
        self._saving = False
        self._pending_changed()

    def _create_case(self):
        """First commit of a new case: create it (with the app's name)"""
        app = self.app
        if self.case_id is None:
            name = app.file_data.name or "untitled"
            app_id = self.app_id if self.app_id is not None else app._config.id
            self.case_id = self.store.create_case(app_id, name, []).id
            app.file_data.name = name
            app.file_data.id = self.case_id
        # its first revision holds the name only
        state = self.store.state(self.case_id)
        self._unsubscribe = self.store.subscribe(
            [self.case_id], state.get("event_seq") or 0, self._on_event
        )
        self.base_revision = state["revision"]
        self.release_id = state.get("release")
        for path, value in flatten(state).items():
            self._base_set(path, value)
        self.job_events = self._job_events()
        self._call_all(self._created_callbacks, self.case_id)

    def _committed(self, ops, result, committed):
        changes = _Changes()
        self._applying = True
        try:
            found = self._walk()
            self._apply_ops(result.remote_ops, found, changes, record=False)
            for op in ops:
                self._base_apply(op)
            for item in committed:
                if isinstance(item, _Entry):
                    item.blobs = {}
                elif isinstance(item, _StateData):
                    item.deleted.clear()
                else:
                    entry, n = item
                    entry.items.extend(entry.pending[:n])
                    del entry.pending[:n]
                    entry.fresh = False
            self._pending_deletes = []
            self._detached = [op for op in self._detached if op not in ops]
            self.base_revision = result.revision
        finally:
            self._applying = False
        self.commit_count += 1
        self._note_commit()
        return changes

    def _base_apply(self, op: Op):
        if op.op == "append":
            seq = self.base.get(op.path, ABSENT)
            seq = _as_seq(seq)
            self._base_set(op.path, seq.appended(op.value))
        elif op.op == "delete" and not is_value_path(op.path):
            for p in [p for p in self.base if is_under(p, op.path)]:
                self._base_set(p, ABSENT)
        else:
            self._base_set(op.path, op.value if op.op == "set" else ABSENT)

    def _note_commit(self):
        now = self.scheduler.now()
        # only commits without edits of the user count as echoes
        echo = self._echo_dirty and not self._user_dirty
        self._echo_dirty = self._user_dirty = False
        self._echo_count = self._echo_count + 1 if echo else 0
        interval = self.min_interval
        if self._echo_count >= self.echo_limit:
            interval = min(
                self.max_interval,
                self.min_interval
                * 2 ** (self._echo_count - self.echo_limit + 1),
            )
            if self._echo_count == self.echo_limit:
                self.echo_warnings += 1
                logger.warning(
                    "Case %s: %d consecutive commits caused by change callbacks, "
                    "commits are slowed down",
                    self.case_id,
                    self._echo_count,
                )
        self._next_allowed = now + interval

    # -- applying changes of other writers --

    def pull(self, to_revision: int | None = None) -> bool:
        """Apply the changes up to to_revision (default: head)"""
        with self._lock:
            if self.closed:
                return False
            if to_revision is None:
                to_revision = self.store.case(self.case_id).head
            if to_revision <= self.base_revision:
                return False
            try:
                ops = self.store.changes(
                    self.case_id, self.base_revision, to_revision
                )
            except BaseGoneError:
                to_revision, ops = self._head_ops()
            n_replaced = len(self.replaced)
            changes = _Changes()
            self._applying = True
            try:
                # read only: the head replaces local edits without notices
                record = self.read_only_reason is None
                self._apply_ops(ops, self._walk(), changes, record=record)
                self.base_revision = to_revision
            finally:
                self._applying = False
            new = self.replaced[n_replaced:]
        self._notify(changes)
        if new:
            self._call_all(self._conflict_callbacks, list(new))
            self.schedule_autosave()
        elif self._dirty:
            self._pending_changed()
        return True

    def _head_ops(self) -> tuple[int, list[Op]]:
        """The base revision was dropped by retention: the head and the
        operations from the base held here to it; applied like pulled
        changes, so local edits stay pending unless the head changed them"""
        state = self.store.state(self.case_id)
        return state["revision"], self._ops_to(flatten(state))

    def _ops_to(self, head: dict) -> list[Op]:
        """Operations that turn the base held here into a flat state"""
        ops = [Op("delete", p) for p in self.base if p not in head]
        for p, value in head.items():
            if stored_key(value) == self.base_keys.get(p):
                continue
            if not isinstance(value, Seq):
                ops.append(Op("set", p, value))
                continue
            old = self.base.get(p, ABSENT)
            start = 0
            if isinstance(old, Seq) and value.keys[: len(old)] == old.keys:
                start = len(old)
            elif old is not ABSENT:
                ops.append(Op("delete", p))
            ops.extend(
                Op("append", p, item, pos=i)
                for i, item in enumerate(value.items[start:], start)
            )
        return ops

    def _apply_ops(self, ops, found, changes: _Changes, record: bool):
        for op in ops:
            if op.op == "append":
                self._apply_append(op, found, changes)
            elif op.op == "delete" and not is_value_path(op.path):
                for p in [p for p in self.base if is_under(p, op.path)]:
                    self._apply_value(p, ABSENT, found, changes, record)
            else:
                value = op.value if op.op == "set" else ABSENT
                self._apply_value(op.path, value, found, changes, record)

    def _apply_value(self, path, value, found, changes, record):
        old_key = self.base_keys.get(path)
        new_key = stored_key(value)
        if path == CASE_NAME:
            name = self.app.file_data.name or ""
            cur_key = value_key(name) if name or old_key else None
            if record and cur_key not in (old_key, new_key):
                self.replaced.append(ReplacedEdit(path, name, _export(value)))
            self.app.file_data.name = value if isinstance(value, str) else ""
            self._base_set(path, value, new_key)
            changes.add(None, None)
            return
        comp = found.get(path[:-2])
        if comp is not None and path[-2] in SECTIONS:
            section, key = path[-2], unescape_key(path[-1])
            cur = self._current(comp, section, key)
            cur_key = None if cur is None else cur.key
            if cur_key == "seq":
                cur_key = old_key
                entry = _state_data(comp).values[key]
                if entry.pending and not isinstance(value, Seq):
                    if record:
                        self.replaced.append(
                            ReplacedEdit(path, None, _export(value))
                        )
            elif record and cur_key not in (old_key, new_key):
                self.replaced.append(
                    ReplacedEdit(
                        path,
                        None if cur is None else cur.stored,
                        _export(value),
                        {} if cur is None else dict(cur.blobs),
                    )
                )
            if cur_key != new_key:
                self._set_local(comp, section, key, value, changes=changes)
        changes.add(None, None)
        self._base_set(path, value, new_key)

    def _apply_append(self, op, found, changes):
        path = op.path
        before = self.base.get(path, ABSENT)
        seq = _as_seq(before)
        if op.pos is not None and op.pos != len(seq):
            logger.warning(
                "Append at %s: position %s, expected %s",
                list(path),
                op.pos,
                len(seq),
            )
        self._base_set(path, seq.appended(op.value))
        changes.add(None, None)
        comp = found.get(path[:-2])
        if comp is None:
            return
        key = unescape_key(path[-1])
        data = _state_data(comp)
        entry = data.values.get(key)
        if isinstance(entry, _Entry) and isinstance(before, list):
            if entry.key == stored_key(before):
                # a plain list became a sequence
                data.values[key] = _SeqEntry.from_seq(self.base[path])
                changes.add(comp, key, len(seq))
            return
        if entry is None:
            if before is not ABSENT:
                return  # deleted locally, the delete is still pending
            entry = data.values[key] = _SeqEntry()
        if isinstance(entry, _SeqEntry) and not entry.fresh:
            entry.items.append(_Entry.from_stored(op.value))
            changes.add(comp, key, len(entry.items) - 1)
            # local appends not committed yet move back by one
            for i in range(len(entry.pending)):
                changes.add(comp, key, len(entry.items) + i)

    def _notify(self, changes: _Changes):
        if changes.any:
            self._last_pull_change = self.scheduler.now()
        self._in_callbacks = True
        try:
            for comp, keys in changes.keys.items():
                data = _state_data(comp)
                appended = changes.appended.get(comp, {})
                for prefix, callback, raw in list(data.callbacks):
                    n = len(prefix)
                    rel = {
                        k[n:]
                        for k in keys
                        if k.startswith(prefix) and "/" not in k[n:]
                    }
                    if not rel:
                        continue
                    try:
                        if raw:
                            callback(
                                rel,
                                {
                                    k[n:]: v
                                    for k, v in appended.items()
                                    if k[n:] in rel
                                },
                            )
                        else:
                            callback(rel)
                    except Exception as e:
                        print_exception(e)
        finally:
            self._in_callbacks = False

    def restore(self, edits: list[ReplacedEdit] | None = None):
        """Re-apply replaced local edits; they are committed by the next save"""
        with self._lock:
            edits = list(self.replaced) if edits is None else edits
            found = self._walk()
            changes = _Changes()
            for edit in edits:
                if edit in self.replaced:
                    self.replaced.remove(edit)
                value = ABSENT if edit.mine is None else edit.mine
                if edit.path == CASE_NAME:
                    self.app.file_data.name = (
                        value if isinstance(value, str) else ""
                    )
                    continue
                comp = found.get(edit.path[:-2])
                if comp is not None and edit.path[-2] in SECTIONS:
                    self._set_local(
                        comp,
                        edit.path[-2],
                        unescape_key(edit.path[-1]),
                        value,
                        edit.blobs,
                        changes,
                    )
            self._notify(changes)
        self.schedule_autosave()

    def keep_held(self):
        """Commit the edits made while read only (see held_edits)"""
        with self._lock:
            if not self._held:
                return
            self._held = False
            self._large_pending = self._dirty and self._has_uploads()
        self._pending_changed()
        if self._dirty:
            self._schedule(edit=False)

    def discard(self):
        """Drop the local edits not committed yet: the values of the base
        are shown again"""
        with self._lock:
            ops = self._collect()[0]
            found = self._walk()
            changes = _Changes()
            self._applying = True
            try:
                for op in ops:
                    path = tuple(op.path)
                    if path == CASE_NAME:
                        name = self.base.get(CASE_NAME, ABSENT)
                        self.app.file_data.name = (
                            name if isinstance(name, str) else ""
                        )
                        continue
                    comp = found.get(path[:-2])
                    if (
                        not is_value_path(path)
                        or comp is None
                        or path[-2] not in SECTIONS
                    ):
                        continue
                    self._set_local(
                        comp,
                        path[-2],
                        unescape_key(path[-1]),
                        self.base.get(path, ABSENT),
                        changes=changes,
                    )
                self._pending_deletes = []
                self._detached = []
            finally:
                self._applying = False
            self.replaced = []
            self._held = False
            self._large_pending = False
            self._dirty = False
            self._dirty_since = self._last_change = None
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None
            if not self.blocked:
                self.last_error = None
        self._notify(changes)
        self._pending_changed()

    # -- durable pending edits --

    def export_pending(self) -> dict | None:
        """The local edits not committed yet as JSON, to be stored by the
        client (e.g. in IndexedDB) and re-applied with import_pending after a
        reload: case_id (None for a new case), base_revision, release_id,
        ops. Values whose blobs were not uploaded yet cannot be restored and
        are left out (their paths are listed in skipped)."""
        with self._lock:
            if self.closed or (self.base_revision is None and not self._edited()):
                return None
            if self.blocked == "no_write" or self._held:
                return None
            ops, uploads, _ = self._collect()
        kept, skipped = [], []
        for op in ops:
            refs = () if op.op == "delete" else iter_blob_refs(op.value)
            if any(r.hash in uploads and r.hash not in self._uploaded for r in refs):
                skipped.append(list(op.path))
            else:
                kept.append(op.to_json())
        if not kept and not skipped:
            return None
        return {
            "case_id": self.case_id,
            "base_revision": self.base_revision,
            "release_id": getattr(self.store, "release_id", None)
            or self.release_id,
            "ops": kept,
            "skipped": skipped,
        }

    def import_pending(self, data) -> bool:
        """Re-apply edits of export_pending (data or its JSON) on a freshly
        opened session of the same case: they become local edits on the
        revision they were based on, then the head is pulled, so changes of
        other writers to the same paths replace them as usual (on_conflict,
        restore); the next commit saves the rest. Returns whether edits were
        applied."""
        if isinstance(data, (str, bytes)):
            data = orjson.loads(data)
        if not data or data.get("case_id") != self.case_id:
            return False
        ops = [Op.from_json(op) for op in data.get("ops") or ()]
        if not ops:
            return False
        base = data.get("base_revision")
        with self._lock:
            if self.closed:
                return False
            rebased = (
                base is not None
                and self.base_revision is not None
                and base < self.base_revision
                and self.commit_count == 0
                and self._op_keys(self._collect()[0]) == self._initial
                and self._rebase(base)
            )
            changes = _Changes()
            self._apply_local(ops, changes=changes)
            self._notify(changes)
        if rebased:
            self.pull()
        self.schedule_autosave()
        return True

    def _rebase(self, revision: int) -> bool:
        """Go back to an older revision (base and local values)"""
        try:
            state = self.store.state(self.case_id, revision)
        except (BaseGoneError, NotFoundError, InvalidError):
            return False  # dropped: the edits apply to the head
        changes = _Changes()
        self._applying = True
        try:
            ops = self._ops_to(flatten(state))
            self._apply_ops(ops, self._walk(), changes, record=False)
            self.base_revision = revision
        finally:
            self._applying = False
        self._notify(changes)
        return True

    def _apply_local(self, ops, found=None, changes=None):
        """Operations as local edits; those of components that do not exist
        are applied when they appear, or committed as they are"""
        found = self._walk() if found is None else found
        for op in ops:
            path = tuple(op.path)
            if path == CASE_NAME:
                if op.op == "set" and isinstance(op.value, str):
                    self.app.file_data.name = op.value
                continue
            if not is_value_path(path):
                if op.op == "delete":
                    comp = found.get(path)
                    if comp is not None:
                        comp._case_deleted = True
                    self._components.pop(path, None)
                    self._pending_deletes.append(path)
                continue
            comp = found.get(path[:-2])
            if comp is None or path[-2] not in SECTIONS:
                self._detached.append(op)
                continue
            section, key = path[-2], unescape_key(path[-1])
            if op.op == "append":
                if section == "state":
                    self._append_local(comp, key, op.value, path in self.base)
                continue
            value = op.value if op.op == "set" else ABSENT
            self._set_local(comp, section, key, value, changes=changes)

    def _append_local(self, comp, key, value, stored: bool):
        data = _state_data(comp)
        entry = data.values.get(key)
        if not isinstance(entry, _SeqEntry):
            items = []
            if isinstance(entry, _Entry):
                old = State(comp)._value(entry, True)
                if isinstance(old, list):
                    items = [_Entry(*_encoded(v)) for v in old]
            # a new sequence replaces a stored value
            entry = data.values[key] = _SeqEntry(fresh=stored)
            entry.pending = items
        entry.pending.append(_Entry.from_stored(value))

    # -- events --

    def _on_event(self, event):
        self._inbox.append(event)
        if not self._inbox_scheduled:
            self._inbox_scheduled = True
            self.scheduler.call_later(0, self._process_inbox)

    def _process_inbox(self):
        self._inbox_scheduled = False
        events, self._inbox = self._inbox, []
        target = None
        access = False
        for event in events:
            payload = event.payload
            if (
                event.type == "cases.changed"
                and payload.get("case_id") == self.case_id
                and payload.get("change") in (None, "shared", "unshared")
            ):
                access = True
            elif (
                event.type == "case.head"
                and payload.get("case_id") == self.case_id
            ):
                target = max(target or 0, payload["revision"])
            elif (
                event.type == "case.deleted"
                and payload.get("case_id") == self.case_id
            ):
                self._case_deleted()
            elif event.type == "resync":
                target = math.inf
            self.events.append(event)
            self._call_all(self._event_callbacks, event)
        if access and not self.closed:
            self._check_access()
        if target is None or self.closed:
            return
        if self.blocked and self.blocked != "no_write":
            return
        try:
            self.pull(None if target == math.inf else target)
        except Exception as e:
            self._report_error(e)

    def _case_deleted(self):
        """The case was deleted by another client: read only, no save
        attempts; reported as an error only with edits not saved"""
        if self.blocked == "case_deleted":
            return
        error = CaseDeletedError(f"case {self.case_id} was deleted")
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None
        if self._unsaved_ops():
            self._report_error(error)
            return
        self.blocked = "case_deleted"
        self.last_error = error
        self._call_all(self._error_callbacks, error)
        self._status_changed()

    # -- autosave --

    def schedule_autosave(self):
        """A local edit: commit it after the debounce delay"""
        self._schedule(edit=not self._opening)

    def _schedule(self, edit: bool):
        if self._applying or self.closed:
            return
        if edit:
            self._dirty = True
            self._edits += 1
            if self.blocked == "no_write":
                self._held = True
            self._pending_changed()
        if self.blocked or self._held:
            return
        if self._in_callbacks:
            self._echo_dirty = True
        elif edit:
            self._user_dirty = True
        if not getattr(self.app, "autosave", True):
            return
        if isinstance(self.last_error, UnauthorizedError):
            return
        now = self.scheduler.now()
        self._last_change = now
        if self._dirty_since is None:
            self._dirty_since = now
        if self._timer is None:
            self._arm(now + self.autosave_delay)

    def _arm(self, due):
        due = max(due, self._next_allowed)
        self._timer = self.scheduler.call_later(
            due - self.scheduler.now(), self._autosave_fire
        )

    def _autosave_fire(self):
        self._timer = None
        if self.closed or self.blocked:
            return
        now = self.scheduler.now()
        due = now
        if self._last_change is not None:
            due = self._last_change + self.autosave_delay
            if self._dirty_since is not None:
                due = min(due, self._dirty_since + self.autosave_max_delay)
        due = max(due, self._next_allowed)
        if due > now + 1e-9:
            self._arm(due)
            return
        self._last_change = None
        try:
            self.commit(_auto=True)
        except RateLimitedError as e:
            self._arm(now + e.retry_after)
            return
        except Exception as e:
            self._report_error(e)
            # an expired token: wait for a new one (retry)
            if not self.blocked and not isinstance(e, UnauthorizedError):
                self._arm(now + self._error_delay)
                self._error_delay = min(
                    self._error_delay * 2, self.max_interval
                )
            return
        self._error_delay = self.min_interval
        self.last_error = None
        self._dirty_since = None
        if self._last_change is not None and self._timer is None:
            self._arm(self._last_change + self.autosave_delay)

    def retry(self):
        """A save that failed (e.g. with an expired token) now instead of
        after its backoff"""
        with self._lock:
            if self.closed or self.blocked or self.last_error is None:
                return
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None
            self._error_delay = self.min_interval
            self._arm(self.scheduler.now())

    def _check_access(self):
        """After a change of the shares: a read-only share upgraded to write
        takes effect at once, a downgrade makes the session read only"""
        if self.blocked == "case_deleted":
            return
        try:
            write = getattr(self.store.case(self.case_id), "write", True)
        except CaseDeletedError:
            self._case_deleted()
            return
        except (ForbiddenError, NotFoundError):
            write = False
        except Exception as e:
            print_exception(e)
            return
        if write and self.blocked == "no_write":
            self.blocked = None
            self.last_error = None
            if self._held and not self._collect()[0]:
                # the head replaced them meanwhile
                self._held = self._dirty = False
            # edits of the read-only time wait for keep_held() or discard()
            self._pending_changed()
            if self._dirty:
                self._schedule(edit=False)
        elif not write and self.blocked is None:
            self.blocked = "no_write"
            self._held = self._dirty
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None
            self._pending_changed()

    def save(self) -> int:
        """Explicit save of app code (App.save): a commit"""
        return self.commit()

    # -- jobs --

    def submit(self, request: JobRequest) -> JobInfo:
        """Commit pending edits, then submit the job on the new revision; if
        the commit fails, no job is submitted"""
        with self._lock:
            request.input_revision = self.commit()
            try:
                return self.store.submit(self.case_id, request)
            except ReleaseTooOldError as e:
                # the runners have newer code: reload the app first
                self._block(e)
                self._status_changed()
                raise
