# pylint: disable=protected-access
import copy
import dataclasses
import functools
import gc
import inspect
import itertools
import logging
import os
import pickle
import sys
import threading
import time
import typing
from collections.abc import Mapping
from pathlib import Path
from types import SimpleNamespace
from typing import Callable, Generic, List, Optional, Tuple, TypeVar
import datetime

import orjson
import pydantic
import typing_extensions

from .. import api
from ..utils import (
    Environment,
    calc_hash,
    call_js,
    get_environment,
    is_pyodide,
    print_exception,
    time_now,
)

from .. import observable as _observable
from ..observable import Observable, Reaction, safe_equal
from .. import utils
from .. import state as state_module
from ..store.types import CaseDeletedError, ForbiddenError

logger = logging.getLogger("ngapp.components")

_component_counter = itertools.count(1)
_components = {}
_components_with_id = {}
# what the browser has, by component index (survives a takeover of the index
# by another component object): token of the mounted instance (None: mounted
# by a protocol 0 frontend) and the components whose init data was sent
_mount_tokens = {}
_frontend_known = set()

# events that are raised in Python only
_PYTHON_EVENTS = frozenset(
    ("mounted", "unmount", "save", "before_save", "load", "before_load")
)
# not sent to the browser; save and load are also events of Quasar
# components (QPopupEdit, QImg, ...)
_NOT_BROWSER_EVENTS = frozenset(
    ("mounted", "unmount", "before_save", "before_load")
)

_local_storage_path = Path.home() / ".cache" / "webapp_local_storage"


class _QProxy:
    def __init__(self, js):
        self.js = js

    def __getattr__(self, name):
        return self.js.document.get_quasar_obj(name)


def get_component(index: int):
    return _components.get(index, None)


def unmount_component(index: int, token=None):
    """The browser removed the instance with this mount token (None: sent
    by a protocol 0 frontend)"""
    comp = _components.get(index)
    if comp is not None:
        comp._unmount(token)


def reset_components():
    _components.clear()
    _mount_tokens.clear()
    _frontend_known.clear()


@dataclasses.dataclass
class FileData:
    app_id: str
    name: str = ""
    id: int | None = None


@dataclasses.dataclass
class AppContext:
    app: object
    capture_events: bool = False
    capture_call_stack: bool = False
    environment: utils.Environment = None
    components_by_id: dict[str, object] = dataclasses.field(
        default_factory=dict
    )
    _cached_app_id: int | None = None

    @property
    def access_level(self):
        return self.app._config.access_level

    @property
    def is_admin(self):
        from ..app import AppConfigWithAccess

        config = self.app._config
        if isinstance(config, AppConfigWithAccess):
            return config.is_admin
        return False

    @property
    def is_view_only(self):
        from ..app import AccessLevel

        return self.access_level == AccessLevel.VIEW

    @property
    def file_data(self):
        return self.app.file_data

    def update(self, options):
        if "capture_events" in options:
            self.capture_events = options["capture_events"]
        if "capture_call_stack" in options:
            self.capture_call_stack = options["capture_call_stack"]

    @property
    def app_id(self):
        if self._cached_app_id is None:
            self._cached_app_id = (
                get_environment().frontend.get_query_parameter("appId")
            )
        return self._cached_app_id

    @app_id.setter
    def app_id(self, value):
        self._cached_app_id = value

    @property
    def file_id(self):
        return self.app.file_data.id


C = TypeVar("T", bound="Component")

_NO_KEYS = frozenset()
_SCALARS = (str, int, float, bool, type(None))


class _Mapped:
    """An observable with a function applied to its value, as prop value"""

    __slots__ = ("obs", "fn")

    def __init__(self, obs, fn):
        if isinstance(obs, _Mapped):
            inner, obs = obs.fn, obs.obs
            self.fn = lambda value: fn(inner(value))
        else:
            self.fn = fn
        self.obs = obs


def _display(obs):
    """display_value without registering a dependency"""
    if _observable.is_tracking():
        with _observable.untracked():
            return obs.display_value
    return obs.display_value


def _style_str(value):
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return ";".join(f"{k}:{v}" for k, v in value.items())
    return "" if value is None else str(value)


def _class_str(value):
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple)):
        return " ".join(str(v) for v in value)
    return "" if value is None else str(value)


def _prefix_class(prefix: str, ui_class):
    """ui_class (text, list or observable) with the classes of prefix"""
    if isinstance(ui_class, (Observable, _Mapped)):
        return _Mapped(ui_class, lambda value: f"{prefix} {_class_str(value)}")
    return f"{prefix} {_class_str(ui_class)}"


def _to_text(value):
    return "" if value is None else str(value)


def _browser_shows(raw, value):
    """The input of the browser (raw) already shows value"""
    if safe_equal(raw, value):
        return True
    if (
        isinstance(raw, str)
        and isinstance(value, (int, float))
        and not isinstance(value, bool)
    ):
        try:
            return float(raw) == value
        except ValueError:
            return False
    return False


class _StorageMetadataEntry(pydantic.BaseModel):
    key: str
    hash: str
    size: int
    type_: str


class _StorageMetadata(pydantic.BaseModel):
    entries: dict[str, _StorageMetadataEntry]

    def get(self, key: str):
        return self.entries.get(key, None)

    def set(self, key: str, value: bytes, type_: str, id: bytes):
        self.entries[key] = _StorageMetadataEntry(
            key=key,
            hash=calc_hash(id, value),
            size=len(value),
            type_=type_,
        )


# Largest body sent in one request when uploading a storage entry. The proxy in
# front of the backend rejects bodies above 100 MB, so bigger entries are split
# into several appending requests (see Storage._upload).
_UPLOAD_CHUNK_BYTES = 32 * 1024 * 1024


class Storage:
    """Storage class for components, use it to store large chunks of data on the backend"""

    _data: dict[str, str | dict | list | bytes]
    _metadata: _StorageMetadata
    _needs_deletion: list[str]
    _needs_save: set[str]
    _component: C
    _saved_file_id: object

    def __init__(self, component: C | "ngapp.App"):
        self._component = component
        self._data = {}
        self._metadata = _StorageMetadata(entries={})
        self._needs_deletion = []
        self._deferred_deletion = []
        self._needs_save = set()
        self._saved_file_id = None
        self._unpublished = set()
        self._on_change = []

    def _state(self):
        """The storage namespace of the component state when the data layer
        is active, else None"""
        if not state_module.data_layer_enabled():
            return None
        return state_module.storage_state(self._component)

    def _encode(self, value: str | dict | list | bytes) -> bytes:
        if isinstance(value, bytes):
            return value
        if isinstance(value, str):
            return value.encode("utf-8")
        return orjson.dumps(value, option=orjson.OPT_SERIALIZE_NUMPY)

    def _decode(self, value: bytes, type_: str) -> str | dict | list | bytes:
        if type_ == "str":
            return value.decode("utf-8")
        if type_ in ["bytes", "pickle"]:
            return value
        return orjson.loads(value)

    def _dump_metadata(self):
        return self._metadata.model_dump()["entries"]

    def _dump_data(self):
        return copy.deepcopy(self._data)

    def _dump(self, include_data=False):
        metadata = self._dump_metadata()
        if include_data:
            return {
                "_have_data": True,
                "data": self._dump_data(),
                "metadata": metadata,
            }
        return metadata

    def _load_metadata(self, data):
        """Replace the metadata, dropping cached data of changed entries.
        Returns the keys that were added, changed or removed."""
        self._saved_file_id = self._component.context.file_id
        metadata = _StorageMetadata(entries=data)
        for key in list(self._data):
            entry = metadata.get(key)
            old = self._metadata.get(key)
            if entry is None or old is None or entry.hash != old.hash:
                del self._data[key]
                self._needs_save.discard(key)
        old, new = self._metadata.entries, metadata.entries
        changed = {k for k in old.keys() | new.keys()
                   if k not in old or k not in new or old[k].hash != new[k].hash}
        self._metadata = metadata
        return changed

    def _load_local(self):
        for key, mdata in self._metadata.entries.items():
            local_path = _local_storage_path / mdata.hash
            if local_path.exists():
                self._data[key] = self._decode(
                    local_path.read_bytes(), mdata.type_
                )

    def _save_local(self):
        _local_storage_path.mkdir(parents=True, exist_ok=True)
        for key, mdata in self._metadata.entries.items():
            local_path = _local_storage_path / mdata.hash
            if not local_path.exists() and key in self._data:
                local_path.write_bytes(self._encode(self._data[key]))

    def _load_data(self, data: dict | None):
        if data is None:
            return
        if data.get("_have_data", False):
            self._load_metadata(data["metadata"])
            self._data = copy.deepcopy(data["data"])
        else:
            self._load_metadata(data)

    def _fetch(self, key: str):
        """Download (or read locally) the decoded value of *key*, or None."""
        mdata = self._metadata.get(key)
        if mdata is None:
            return None
        if not get_environment().have_backend:
            local_path = _local_storage_path / mdata.hash
            if not local_path.exists():
                return None
            return self._decode(local_path.read_bytes(), mdata.type_)
        file_id = self._component.context.file_id
        if file_id is None:
            return None
        return self._decode(api.get(f"/files/{file_id}/files/{mdata.hash}"),
                            mdata.type_)

    def load(self, key: str):
        if (state := self._state()) is not None:
            state_module.storage_get(state, key)
            return
        if not get_environment().have_backend:
            self._load_local()
            return
        value = self._fetch(key)
        if value is None:
            return
        self._data[key] = value
        if key in self._needs_save:
            self._needs_save.remove(key)

    def __contains__(self, key: str) -> bool:
        if (state := self._state()) is not None:
            return key in state
        return key in self._metadata.entries

    def _upload(self, url: str, data: bytes):
        """Upload one storage entry, in chunks if it is large.

        Proxies in front of the backend limit the size of a single request
        body, so anything above `_UPLOAD_CHUNK_BYTES` is sent as several
        requests: the first writes the file, the rest are appended to it. A
        backend without the append route answers those with an error rather
        than silently keeping only the last chunk.
        """
        if len(data) <= _UPLOAD_CHUNK_BYTES:
            api.post(url, data)
            return
        for i, start in enumerate(range(0, len(data), _UPLOAD_CHUNK_BYTES)):
            api.post(
                url if i == 0 else url + "/append",
                data[start : start + _UPLOAD_CHUNK_BYTES],
            )

    def save(self):
        if self._state() is not None:
            return
        if not get_environment().have_backend:
            if self._needs_save:
                self._save_local()
            return
        file_id = self._component.context.file_id
        if file_id != self._saved_file_id:
            self._needs_save.update(
                key for key in self._metadata.entries if key in self._data
            )
            self._needs_deletion.clear()
            self._deferred_deletion = []
            self._saved_file_id = file_id
        referenced = {e.hash for e in self._metadata.entries.values()}
        # Entries replaced by the previous save: the stored model refers to the
        # new ones by now. Deleting them only then keeps a save that is cut off
        # (reload, closed tab) from leaving the model pointing at deleted data.
        stale = [h for h in self._deferred_deletion if h not in referenced]
        if stale:
            api.delete(f"/files/{file_id}/files", data=stale)
        self._deferred_deletion = [
            h for h in dict.fromkeys(self._needs_deletion) if h not in referenced
        ]
        self._needs_deletion.clear()
        # a copy: a second save (double click) may start while this one uploads
        for key in list(self._needs_save):
            mdata = self._metadata.get(key)
            self._upload(
                f"/files/{file_id}/files/{mdata.hash}",
                self._encode(self._data[key]),
            )
            # set again meanwhile: the new value still needs an upload
            if self._metadata.get(key) is mdata:
                self._needs_save.discard(key)

    def get(self, key: str, default=None, cache=True):
        """Get data from storage. With ``cache=False`` a value that is not in
        memory yet is downloaded without being kept (for large entries that
        are only needed once)."""
        if (state := self._state()) is not None:
            return state_module.storage_get(state, key, default, cache)
        if key in self._data:
            value = self._data[key]
        elif cache:
            self.load(key)
            value = self._data.get(key, default)
        else:
            value = self._fetch(key)
            if value is None:
                value = default

        if (
            value is not None
            and self._metadata.get(key)
            and self._metadata.get(key).type_ == "pickle"
        ):
            value = pickle.loads(value)

        return value

    def set(
        self,
        key: str,
        value: str | dict | list | bytes | object,
        use_pickle=False,
    ):
        """Set data in storage"""
        from ..app import App

        if (state := self._state()) is not None:
            state_module.storage_set(state, key, value, use_pickle)
            return

        if use_pickle:
            value = pickle.dumps(value)
            type_ = "pickle"
        else:
            type_ = type(value).__name__

        if key in self._data and value == self._data[key]:
            return

        old_hash = None
        if key in self._metadata.entries:
            old_hash = self._metadata.get(key).hash

        self._data[key] = copy.deepcopy(value)
        fullid = (
            "__app__"
            if isinstance(self._component, App)
            else self._component._fullid
        )
        self._metadata.set(
            key,
            self._encode(value),
            type_,
            id=self._encode(fullid),
        )
        self._needs_save.add(key)
        self._unpublished.add(key)
        if old_hash and old_hash != self._metadata.get(key).hash:
            self._needs_deletion.append(old_hash)

    def delete(self, key: str):
        """Delete data from storage"""
        if (state := self._state()) is not None:
            state_module.storage_delete(state, key)
            return
        if key in self._data:
            del self._data[key]
        if key in self._metadata.entries:
            self._needs_deletion.append(self._metadata.get(key).hash)
            del self._metadata.entries[key]
        if key in self._needs_save:
            self._needs_save.remove(key)
        self._unpublished.add(key)

    # -- append-only lists, stored as one entry per item ("key#0", "key#1", ...)
    # so that appending uploads (and a client downloads) only the new items.

    @staticmethod
    def _list_key(key: str, i: int) -> str:
        return f"{key}#{i}"

    def list_len(self, key: str) -> int:
        """Number of items in the list stored under *key*."""
        if (state := self._state()) is not None:
            return state_module.storage_list_len(state, key)
        n = 0
        while self._list_key(key, n) in self._metadata.entries:
            n += 1
        return n

    def append(self, key: str, value, use_pickle=False):
        """Append *value* to the list stored under *key*."""
        if (state := self._state()) is not None:
            state.list(key).append(value, pickle=use_pickle)
            return
        self.set(self._list_key(key, self.list_len(key)), value, use_pickle)

    def get_list(self, key: str, start: int = 0, stop: int | None = None,
                 cache=True) -> list:
        """Items ``start:stop`` of the list stored under *key*."""
        if (state := self._state()) is not None:
            return state_module.storage_list(state, key)[start:stop]
        n = self.list_len(key)
        stop = n if stop is None else min(stop, n)
        return [self.get(self._list_key(key, i), cache=cache)
                for i in range(start, stop)]

    def delete_list(self, key: str):
        if (state := self._state()) is not None:
            state_module.storage_delete(state, key)
            return
        for i in range(self.list_len(key)):
            self.delete(self._list_key(key, i))

    @staticmethod
    def list_keys(changed) -> "set[str]":
        """The list names among the *changed* keys of an on_change callback."""
        return {k.rsplit("#", 1)[0] for k in changed
                if "#" in k and k.rsplit("#", 1)[1].isdigit()}

    # -- change notification --

    def on_change(self, callback):
        """Call ``callback(changed_keys)`` when published changes arrive.

        In a local app this happens on :meth:`publish` itself; when the
        changes come from a compute node, once the client received them (the
        data of changed entries is fetched lazily on ``get``). A full load of
        the app does not trigger it, use the app's ``load`` event for that.
        Returns a function that removes the callback.
        """
        if (state := self._state()) is not None:
            return state_module.storage_on_change(state, callback)
        self._on_change.append(callback)
        return lambda: self._on_change.remove(callback)

    def _notify(self, changed):
        for cb in list(self._on_change):
            try:
                cb(set(changed))
            except Exception as e:
                print_exception(e, file=sys.stdout)

    def publish(self):
        """Make the changes since the last publish visible to the on_change
        callbacks: directly in a local app, on a compute node by uploading them
        and pushing the metadata through the backend, which also stores it in
        the file (a later load of the file sees the same state). With the
        data layer, changes are committed automatically and this is a no-op."""
        if self._state() is not None:
            return
        changed, self._unpublished = self._unpublished, set()
        if not changed:
            return
        if get_environment().type == utils.EnvironmentType.COMPUTE:
            self.save()
            self._component._update_frontend({"storage": self._dump_metadata()})
        else:
            self._notify(changed)


class _InitTiming(threading.local):
    # time spent in the constructors of components created by the running one
    nested = 0.0


_init_timing = _InitTiming()
# [time spent in garbage collections, start of the running one]
_gc_time = [0.0, 0.0]


def _gc_callback(phase, info):
    if phase == "start":
        _gc_time[1] = time.perf_counter()
    else:
        _gc_time[0] += time.perf_counter() - _gc_time[1]


gc.callbacks.append(_gc_callback)
_slow_init = 0.1
_slow_app_init = 1.0
_slow_init_reported = set()
_SLOW_INIT_HINT = (
    "Constructors also run in compute jobs: build expensive content in "
    "on_mounted or in an effect."
)


def _read_slow_init_limits():
    """Limits of the slow constructor warning in seconds (0: off), from
    NGAPP_SLOW_INIT (own time of a component) and NGAPP_SLOW_APP_INIT
    (total time of the app)"""
    global _slow_init, _slow_app_init

    def read(name, default):
        try:
            return float(os.environ.get(name, default))
        except ValueError:
            return default

    _slow_init = read("NGAPP_SLOW_INIT", 0.1)
    _slow_app_init = read("NGAPP_SLOW_APP_INIT", 1.0)


_read_slow_init_limits()
_package_dir = str(Path(__file__).resolve().parent.parent) + os.sep


def _creation_site():
    """file:line of the code outside ngapp that creates a component"""
    frame = first = sys._getframe(3)
    while frame is not None and frame.f_code.co_filename.startswith(
        _package_dir
    ):
        frame = frame.f_back
    frame = frame or first
    return f"{frame.f_code.co_filename}:{frame.f_lineno}"


def _caller_site():
    """file:line of the innermost caller outside ngapp"""
    frame = sys._getframe(1)
    while frame is not None and frame.f_code.co_filename.startswith(
        _package_dir
    ):
        frame = frame.f_back
    if frame is None:
        return "<unknown>"
    return f"{frame.f_code.co_filename}:{frame.f_lineno}"


def _code_site(func):
    """file:line of a handler, looks through the wrappers of on()"""
    code = getattr(func, "__code__", None)
    if code is None:
        return "<unknown>"
    if code.co_filename.startswith(_package_dir):
        for cell in getattr(func, "__closure__", None) or ():
            try:
                inner = cell.cell_contents
            except ValueError:
                continue
            if callable(inner) and hasattr(inner, "__code__"):
                return _code_site(inner)
    return f"{code.co_filename}:{code.co_firstlineno}"


# number of components created so far, for the handler warning
_created = 0
_dev_reported = set()
_REBUILD_COUNT = 4
_REBUILD_WINDOW = 2.0
_HANDLER_MAX_CREATED = 100
# called with (component, slot key, old, new) by every slot assignment while
# test_utils.assert_stable is active
_slot_recorder = None


def _dev_warning(ident, msg, *args):
    """Hint for app authors, once per ident; off with NGAPP_DEV_WARNINGS=0
    and in compute jobs"""
    if ident in _dev_reported:
        return
    if os.environ.get("NGAPP_DEV_WARNINGS", "1") == "0":
        return
    env = get_environment()
    if env is not None and env.type == utils.EnvironmentType.COMPUTE:
        return
    _dev_reported.add(ident)
    logger.warning(msg, *args)


def _report_slow_init(comp, own, total, created):
    app_module = sys.modules.get("ngapp.app")
    is_app = app_module is not None and isinstance(
        comp, getattr(app_module, "App", ())
    )
    if is_app:
        # builds the page layout itself: only the app limit applies
        if not total > _slow_app_init > 0:
            return
        logger.warning(
            "Slow app constructor: %s took %.2f s in total (limit %g s), "
            "%d components. %s",
            type(comp).__name__,
            total,
            _slow_app_init,
            created,
            _SLOW_INIT_HINT,
        )
        return
    if own > _slow_init > 0:
        site = _creation_site()
        if (type(comp), site) not in _slow_init_reported:
            _slow_init_reported.add((type(comp), site))
            logger.warning(
                "Slow constructor: %s took %.0f ms (own time, limit %.0f ms), "
                "created at %s. %s",
                type(comp).__name__,
                1000 * own,
                1000 * _slow_init,
                site,
                _SLOW_INIT_HINT,
            )


class BlockFrontendUpdate(type):
    def __new__(cls, name, bases, dct):
        init_method = dct.get("__init__")
        if init_method is not None:

            @functools.wraps(init_method)
            def wrapped_init(self, *args, **kwargs):
                depth = self.__dict__.get("_init_depth", 0)
                self._init_depth = depth + 1
                self._block_frontend_update = True
                if depth:
                    init_method(self, *args, **kwargs)
                    self._block_frontend_update = False
                    self._init_depth = depth
                    return
                timing = _init_timing
                outer = timing.nested
                timing.nested = 0.0
                created = len(_components)
                collecting = _gc_time[0]
                start = time.perf_counter()
                try:
                    init_method(self, *args, **kwargs)
                    total = time.perf_counter() - start
                    own = total - timing.nested
                    self._block_frontend_update = False
                    self._init_depth = depth
                    self._after_init()
                finally:
                    timing.nested = outer + time.perf_counter() - start
                if own > _slow_init > 0 or total > _slow_app_init > 0:
                    # a garbage collection is not the constructor's fault
                    collecting = _gc_time[0] - collecting
                    _report_slow_init(
                        self,
                        own - collecting,
                        total - collecting,
                        len(_components) - created,
                    )

            dct["__init__"] = wrapped_init
        return super().__new__(cls, name, bases, dct)


@dataclasses.dataclass
class Event:
    name: str
    component: "Component"
    arg: Optional[object] = None
    value: Optional[object] = None

    def __getitem__(self, item):
        """For backward compatibility"""
        if item == "arg":
            return self.arg
        elif item == "value":
            return self.value
        elif item == "name":
            return self.name
        elif item == "comp":
            return self.component
        raise AttributeError(f"{item} not found in Event class")


# the state class of a component: Component[MyState] with a StateModel
S = typing_extensions.TypeVar(
    "S", bound="state_module.StateBase", default="state_module.State"
)


def _state_class_of(cls):
    """The StateModel of Component[MyState] among the bases of cls"""
    for base in cls.__dict__.get("__orig_bases__", ()):
        for arg in typing.get_args(base):
            if isinstance(arg, type) and issubclass(arg, state_module.StateBase):
                return arg
    return None


class Component(Generic[S], metaclass=BlockFrontendUpdate):
    """Base component class, the component name is passed as argument"""

    _callbacks: dict[str, List[Callable]]
    _id: str
    _namespace_id: str | None = None
    _parent: C | None = None
    context: AppContext = None
    _namespace: bool
    _js_component = None
    _component_name: str
    _keybindings: List[Tuple[str, Callable, dict]]
    storage: Storage
    _two_way_props: tuple[str, ...] = ()
    _is_text = False
    # no DOM element: the children appear in the slot of the parent
    _transparent = False
    # prop keys that are computed from observables: not stored in the case
    _derived_props = _NO_KEYS
    # prop key -> Reaction of a binding that is evaluated for a browser only
    _lazy_bindings = None
    # values the browser sent for two-way props bound to an observable
    _browser_values = None
    _effects = None
    # bound texts sent with the slots: slot name -> list of Text
    _live_texts = None
    _resolving = False

    @utils._count_calls
    def __init__(
        self,
        component: str,
        *ui_children: C | str,
        ui_slots: dict[str, list] | None = None,
        namespace: bool = False,
        ui_style: str | dict | None = None,
        ui_class: str | list[str] | None = None,
        ui_hidden: bool | None = None,
        id: str = "",
        ui_invisible: bool | None = None,
    ):
        global _created
        _created += 1
        self._index = next(_component_counter)
        _components[self._index] = self
        self._keybindings = []

        if "." in id:
            raise ValueError("Component id cannot contain '.'")

        self._callbacks = {}
        self._js_callbacks = {}

        self._component_name = component
        self._props = {}
        self._observable_bindings = {}
        self.ui_slots = ui_slots = ui_slots or {}
        self._namespace = namespace
        self._id = id

        self.storage = Storage(self)
        self.on_save(self.storage.save)

        for key, slot in ui_slots.items():
            if key != "default" and isinstance(slot, list):
                ui_slots[key] = self._wrap_children(slot)

        children = list(ui_children)
        for i, c in enumerate(children):
            if isinstance(c, Component):
                c._parent = self
            elif isinstance(c, Observable):
                children[i] = c = Text(c)
                c._parent = self
        ui_slots["default"] = children

        if ui_style is None:
            self._props["style"] = ""
        elif isinstance(ui_style, (Observable, _Mapped)):
            self._props["style"] = ""
            self._bind_prop("style", ui_style, init=True)
        else:
            self._props["style"] = _style_str(ui_style)

        if isinstance(ui_class, (Observable, _Mapped)):
            self._bind_prop("class", ui_class, init=True)
        elif ui_class:
            self._props["class"] = _class_str(ui_class)

        if ui_hidden is not None:
            self.ui_hidden = ui_hidden
        if ui_invisible is not None:
            self.ui_invisible = ui_invisible

    def _after_init(self):
        if self._id and state_module.data_layer_enabled():
            state_module.snapshot_defaults(self)

    @property
    def _mounted(self) -> bool:
        """An instance of the component exists in the browser"""
        return self._index in _mount_tokens

    @_mounted.setter
    def _mounted(self, value):
        if value:
            _mount_tokens.setdefault(self._index, None)
        else:
            _mount_tokens.pop(self._index, None)

    @property
    def _mount_token(self):
        return _mount_tokens.get(self._index)

    @property
    def _frontend_known(self) -> bool:
        """The browser has the data of the component (protocol >= 1, sent
        with its parent or mounted): updates are sent"""
        return self._index in _frontend_known

    @_frontend_known.setter
    def _frontend_known(self, value):
        if value:
            _frontend_known.add(self._index)
        else:
            _frontend_known.discard(self._index)

    _state_class = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        state_class = _state_class_of(cls)
        if state_class is not None:
            cls._state_class = state_class

    def _get_state(self) -> S:
        state = self.__dict__.get("_state")
        if state is None:
            state = self._state = (self._state_class or state_module.State)(self)
        return state

    @property
    def state(self) -> S:
        """Values of the component that are stored in the case but not sent
        to the browser (requires a component id); used like a dict, assigning
        a dict replaces its values"""
        override = self.__dict__.get("_state_override", None)
        return self._get_state() if override is None else override

    @state.setter
    def state(self, value):
        if isinstance(value, Mapping) and getattr(self, "_id", None):
            self.__dict__.pop("_state_override", None)
            state = self._get_state()
            if value is not state:
                state._assign(value)
            return
        # apps that use an own attribute named state keep working
        self._state_override = value

    @property
    def app(self):
        override = self.__dict__.get("_app_override", None)
        if override is not None:
            return override
        return self.context.app if self.context is not None else None

    @app.setter
    def app(self, value):
        self._app_override = value

    def _mark_dirty(self):
        if not self._id:
            return  # not stored in the case
        ctx = self.context
        if ctx is not None and ctx.app is not None:
            session = getattr(ctx.app, "case_session", None)
            if session is not None:
                session.schedule_autosave()

    def _update_two_way_prop(self, prop: str, value):
        """Back-sync of a two-way prop (update:<prop> event of the browser).
        The browser shows the value already: it is not sent back, unless a
        bound observable ends up with another value"""
        binding = self._observable_bindings.get(prop)
        if binding is not None and binding[0].read_only:
            # derived: the browser gets the value of the computed again
            if prop in self._props:
                self._update_frontend({"props": {prop: self._props[prop]}})
            return
        if get_environment().frontend.protocol < 1:
            # the old frontend shows what it gets back
            self._set_prop(prop, value)
            if binding is not None:
                binding[0].value = value
            return
        self._props[prop] = value
        self._mark_dirty()
        if binding is None:
            return
        if self._browser_values is None:
            self._browser_values = {}
        # read by _bound_changed when the observable reports the change
        self._browser_values[prop] = value
        binding[0].value = value

    def create_event_handler(
        self,
        function,
        prevent_default: bool = True,
        stop_propagation: bool = False,
        stop_immediate_propagation: bool = False,
        return_value: Optional[object] = None,
    ):
        """
        Create an event handler for the component.

        Args:
            function (Callable): The function to call when the event is triggered.
            prevent_default (bool): Whether to prevent the default action of the event.
            stop_propagation (bool): Whether to stop the propagation of the event.
            stop_immediate_propagation (bool): Whether to stop immediate propagation of the event.
            return_value (object, optional): The value to return from the event handler.
        """
        import webgpu.platform as pl

        return pl.create_event_handler(
            function,
            prevent_default=prevent_default,
            stop_propagation=stop_propagation,
            stop_immediate_propagation=stop_immediate_propagation,
            return_value=return_value,
        )

    def add_keybinding(
        self,
        key: str,
        callback: Callable,
        local: bool = False,
        keyup: bool = False,
        keydown: bool = True,
        split_key: str = "+",
        capture: bool = False,
        single: bool = False,
        prevent_default: bool = False,
        match: str | None = None,
        allow_typing: bool = False,
    ):
        """Add key binding to component.

        ``callback(ev)`` gets the key event with attributes ``combo``,
        ``type``, ``key``, ``code``, ``ctrlKey``, ``shiftKey``, ``altKey``,
        ``metaKey``, ``repeat``, ``timeStamp``, ``target`` (tag name) and
        ``isContentEditable``.

        Args:
            prevent_default: call ``preventDefault()`` on the event in the
                browser listener (e.g. ``"ctrl+s"``, ``"tab"``).
            match: ``"code"`` matches with hotkeys-js (key codes, symbols on
                US layout only), ``"key"`` matches ``KeyboardEvent.key`` (any
                layout, ``"?"``, ``"["``, ``"+"``; shift / alt producing a
                symbol are ignored unless listed). ``None`` picks ``"key"``
                for symbols hotkeys-js does not know (``"?"``, ``"+"``, ...).
                ``single`` has no effect with ``"key"``.
            allow_typing: also fire while an input, textarea or select has the
                focus (filtered by default so shortcuts do not fire while
                typing). Uses ``"key"`` matching.
        """
        import webgpu.platform as pl

        options = {
            "local": local,
            "keyup": keyup,
            "keydown": keydown,
            "split_key": split_key,
            "capture": capture,
            "single": single,
            "prevent_default": prevent_default,
            "match": match,
            "allow_typing": allow_typing,
        }

        if f := self._js_callbacks.get("add_keybinding", None):

            def on_key(ev):
                if hasattr(ev, "to_py"):
                    ev = ev.to_py()
                with _observable.batch(defer_listeners=False):
                    callback(SimpleNamespace(**ev))

            # no link: a frontend of tests
            proxy = pl.create_proxy(on_key, True) if pl.create_proxy else on_key
            f(key, proxy, options, _ignore_result=True)
            return
        # store keybindings until component is mounted
        if not self._keybindings:
            def add_keybinding_later():
                bindings = self._keybindings
                self._keybindings = []
                for key, func, options in bindings:
                    self.add_keybinding(key, func, **options)

            self.on_mounted(add_keybinding_later)

        self._keybindings.append((key, callback, options))

    def remove_keybinding(self, key: str):
        """Remove the key bindings of this component for ``key``."""
        self._keybindings = [b for b in self._keybindings if b[0] != key]
        if f := self._js_callbacks.get("remove_keybinding", None):
            f(key, _ignore_result=True)

    @property
    def js(self):
        """
        Direct access to the JavaScript environment for immediate execution.

        This property provides direct access to the JavaScript runtime environment,
        allowing you to run any JavaScript function or access any JavaScript object
        immediately.

        Note:
            - Cannot be used in __init__ methods - use call_js() instead for deferred execution
            - Only available after the JavaScript environment is fully loaded

        Example:
            self.js.console.log("Hello from Python!")
        """
        import webgpu.platform as pl

        if pl.js is None:
            raise RuntimeError(
                "JavaScript environment is not initialized. .js is only available outside of the __init__ method of the app."
            )
        return pl.js

    def call_js(self, func: Callable, *args, **kwargs):
        """
        This method ensures safe JavaScript execution by automatically deferring the
        function call until the JavaScript environment is ready. If JavaScript is
        already available, the function executes immediately.

        Args:
            func (callable): A Python function
            ``*args``: Positional arguments to pass to the function when called.
            ``**kwargs``: Keyword arguments to pass to the function when called.

        Note:
            - Safe to call in app __init__ method (when .js is not yet available)

        Example:
            >>> def my_method(js):
            ...     return js.console.log("Hi from JS when app is initialized")
            >>> self.call_js(my_method)
        """
        call_js(func, *args, **kwargs)

    @property
    def quasar(self):
        """
        Access to the Quasar framework's $q object and utilities.

        Provides access to all Quasar framework functionality through a Python interface.
        The returned proxy object allows calling any method available on Quasar's $q object
        as documented at: https://quasar.dev/options/the-q-object

        Note:
            - Cannot be used in __init__ methods

        Example:
            >>> # Show a notification
            >>> self.quasar.notify({
            ...     'message': 'Operation completed successfully!',
            ...     'color': 'positive',
            ... })

        """
        return _QProxy(self.js)

    @property
    def ui_children(self):
        return self.ui_slots["default"]

    @ui_children.setter
    def ui_children(self, value):
        self._set_slot("default", value)

    @property
    def ui_style(self):
        return self._props.get("style", "")

    @ui_style.setter
    def ui_style(self, value):
        if not isinstance(value, (Observable, _Mapped)):
            value = _style_str(value)
        self._set_prop("style", value)

    @property
    def ui_class(self):
        return self._props.get("class", "")

    @ui_class.setter
    def ui_class(self, value):
        if not isinstance(value, (Observable, _Mapped)):
            value = _class_str(value)
        self._set_prop("class", value)

    @property
    def ui_hidden(self):
        """Set display to none. Compare with below - the class hidden means the element will not show and will not take up space in the layout."""
        if self.__dict__.get("_hidden_by"):
            return self.__dict__.get("_user_hidden", False)
        return "hidden" in self._props.get("class", "").split()

    @ui_hidden.setter
    def ui_hidden(self, value):
        self._set_flag("hidden", value)

    @property
    def ui_invisible(self):
        """Set visibility to hidden. Compare with above - the class invisible means the element will not show, but it will still take up space in the layout."""
        return "invisible" in self._props.get("class", "").split()

    @ui_invisible.setter
    def ui_invisible(self, value):
        self._set_flag("invisible", value)

    def _set_flag(self, token: str, value):
        """ui_hidden / ui_invisible: a class of the component"""
        key = "@" + token
        if isinstance(value, (Observable, _Mapped)):
            self._bind_prop(key, value)
            return
        self._unbind_prop(key)
        self._apply_bound(key, value)

    def _set_class_token(self, token: str, on: bool, dirty=True):
        cls = self._props.get("class", "")
        tokens = cls.split()
        if on == (token in tokens):
            return
        if on:
            cls = f"{cls} {token}" if cls else token
        else:
            cls = " ".join(t for t in tokens if t != token)
        self._apply_prop(
            "class", cls, dirty and "class" not in self._derived_props
        )

    def _hide_by(self, owner, hide: bool):
        """Hidden by a structural component (Show), whatever ui_hidden says"""
        owners = self.__dict__.get("_hidden_by")
        if owners is None:
            if not hide:
                return
            owners = self._hidden_by = set()
        if hide:
            if not owners:
                self._user_hidden = self.ui_hidden
            owners.add(owner)
            self._set_class_token("hidden", True, dirty=False)
        elif owner in owners:
            owners.discard(owner)
            if not owners:
                self._set_class_token(
                    "hidden",
                    self.__dict__.pop("_user_hidden", False),
                    dirty=False,
                )

    def _calc_namespace_id(self):
        if self._namespace_id is None:
            utils._trace_call("_calc_namespace_id")
            from ..app import App

            if isinstance(self, App):
                self._namespace_id = ""
            else:
                parent = self._parent
                if parent is None:
                    raise RuntimeError(
                        "Parent of component is not set", self._id, type(self)
                    )
                if parent._namespace_id is None:
                    parent._calc_namespace_id()
                self._namespace_id = (
                    parent._fullid
                    if parent._namespace
                    else parent._namespace_id
                )
                self.context = parent.context
            if self._id:
                _components_with_id[self._fullid] = self
                self.context.components_by_id[self._fullid] = self

    @property
    def _fullid(self):
        if self._namespace_id is None:
            utils._trace_call("_calc_namespace_id._fullid")
            self._calc_namespace_id()

        if not self._id:
            return ""

        if self._namespace_id:
            return self._namespace_id + "." + self._id
        return self._id

    def _init_prop(self, key, value):
        """Set a prop during __init__, with Observable support."""
        if isinstance(value, (Observable, _Mapped)):
            self._bind_prop(key, value, init=True)
        else:
            self._props[key] = value

    @utils._count_calls
    def _set_prop(self, key: str, value):
        if isinstance(value, (Observable, _Mapped)):
            self._bind_prop(key, value)
            return
        if self._lazy_bindings and key in self._lazy_bindings:
            # the last write wins
            self._unbind_prop(key)
            _dev_warning(
                ("overwrite", type(self), key),
                "%s.%s bound to a computed was overwritten with a plain "
                "value: the binding is removed.",
                type(self).__name__,
                key,
            )
        if self._browser_values:
            self._browser_values.pop(key, None)
        self._apply_prop(key, value)

    def _apply_prop(self, key: str, value, dirty=True, send=True):
        old_value = self._props.get(key, None)
        new_key = key not in self._props
        changed = not safe_equal(value, old_value)
        self._props[key] = value
        if send and changed:
            self._update_frontend({"props": {key: value}})
        # an equal container may have been changed in place
        if dirty and (changed or new_key or not isinstance(value, _SCALARS)):
            self._mark_dirty()

    def _bind_prop(self, key: str, source, init=False):
        """Bind a prop (or @hidden, @invisible) to an observable. A plain
        observable is read now and followed, a read-only one (computed) is
        evaluated when the props are needed for a browser"""
        self._unbind_prop(key)
        transform = None
        if isinstance(source, _Mapped):
            source, transform = source.obs, source.fn
        if key == "style":
            transform = (
                (lambda v, f=transform: _style_str(f(v)))
                if transform
                else _style_str
            )
        prop = "class" if key[0] == "@" else key
        if source.read_only:

            def update():
                value = source.display_value
                if transform is not None:
                    value = transform(value)
                self._apply_bound(key, value, False, not self._resolving)

            reaction = Reaction(
                update, _observable.SYNC, type(self).__name__ + "." + key, False
            )
            reaction.owner = self
            if self._lazy_bindings is None:
                self._lazy_bindings = {}
            self._lazy_bindings[key] = reaction
            self._observable_bindings[key] = (source, reaction.dispose)
            self._mark_derived(prop)
            if not init and (
                self._index in _frontend_known
                or self._js_component is not None
            ):
                self._resolve_bindings()
            return
        value = _display(source)
        if transform is not None:
            value = transform(value)
        dispose = source.on_change(
            lambda new, old: self._bound_changed(key, source, transform)
        )
        self._observable_bindings[key] = (source, dispose)
        if prop == "class":
            # partly computed: not stored
            self._mark_derived(prop)
        if init and key[0] != "@" and key != "class":
            self._props[key] = value
        else:
            self._apply_bound(key, value)

    def _mark_derived(self, prop: str):
        if self._derived_props is _NO_KEYS:
            self._derived_props = set()
        self._derived_props.add(prop)

    def _unbind_prop(self, key: str):
        binding = self._observable_bindings.pop(key, None)
        if binding is None:
            return
        binding[1]()
        if self._lazy_bindings:
            self._lazy_bindings.pop(key, None)
        prop = "class" if key[0] == "@" else key
        if self._derived_props and (
            prop != "class"
            or not any(
                k in self._observable_bindings
                for k in ("class", "@hidden", "@invisible")
            )
        ):
            self._derived_props.discard(prop)

    def _bound_changed(self, key: str, obs, transform):
        """The plain observable bound to a prop changed"""
        value = _display(obs)
        sent = self._browser_values
        if sent and key in sent:
            raw = sent[key]
            if _browser_shows(raw, obs.peek()) or safe_equal(raw, value):
                # the value came from the browser: no echo
                return
            del sent[key]
        if transform is not None:
            value = transform(value)
        self._apply_bound(key, value)

    def _apply_bound(self, key: str, value, dirty=True, send=True):
        if key[0] == "@":
            if key == "@hidden" and self.__dict__.get("_hidden_by"):
                self._user_hidden = bool(value)
            else:
                self._set_class_token(key[1:], bool(value), dirty)
            return
        if key == "class":
            # hidden and invisible are set through their own properties
            value = _class_str(value)
            old = self._props.get("class", "").split()
            for token in ("hidden", "invisible"):
                if token in old and token not in value.split():
                    value = f"{value} {token}" if value else token
            dirty = False
        self._apply_prop(key, value, dirty, send)

    def _resolve_bindings(self, send=True):
        """Evaluate the props bound to computed values and follow them; done
        when the props are needed for a browser. send: changed values are
        sent to the browser"""
        for reaction in tuple((self._lazy_bindings or {}).values()):
            if reaction.active or reaction.disposed:
                continue
            self._resolving = not send
            try:
                reaction.resume()
            except Exception as e:
                print_exception(e, file=sys.stdout)
            finally:
                self._resolving = False

    def _suspend_bindings(self):
        """No browser shows the component: bound values are not evaluated"""
        if self._lazy_bindings:
            for reaction in self._lazy_bindings.values():
                reaction.suspend()
        if self._live_texts:
            for texts in self._live_texts.values():
                for text in texts:
                    text._suspend()

    def _wrap_children(self, children: list) -> list:
        """children with observables replaced by bound texts"""
        for i, child in enumerate(children):
            if isinstance(child, Observable):
                children = list(children)
                for j in range(i, len(children)):
                    if isinstance(children[j], Observable):
                        children[j] = Text(children[j])
                break
        return children

    @utils._count_calls
    def _set_slot(self, key: str, value):
        old = self.ui_slots.get(key)
        if isinstance(value, list):
            value = self._wrap_children(value)
        self.ui_slots[key] = value
        if _slot_recorder is not None:
            _slot_recorder(self, key, old, value)
        if isinstance(value, list):
            for comp in value:
                if isinstance(comp, Component):
                    comp._set_parent_recursive(self)
            if old and isinstance(old, list) and len(old) == len(value):
                self._check_rebuild(key, old, value)
        elif isinstance(value, Component):
            value._set_parent_recursive(self)
        if get_environment().frontend.protocol >= 1:
            # serialised when the update is sent
            if self._index in _frontend_known:
                self._update_frontend({"slots": {key: None}})
        elif self._js_component is not None or not (
            isinstance(value, list)
            and any(
                isinstance(c, Component) and (c._is_text or c._transparent)
                for c in value
            )
        ):
            # bound texts are evaluated for a browser only
            self._update_frontend({"slots": {key: self._serialize_slot(key)}})
        self._mark_dirty()

    def _check_rebuild(self, key: str, old: list, new: list):
        """Dev warning: the slot is built again and again with new
        components of the same types"""
        if any(type(a) is not type(b) for a, b in zip(old, new)):
            return
        kept = {id(c) for c in old if isinstance(c, Component)}
        if not kept or any(id(c) in kept for c in new):
            return
        now = time.monotonic()
        times = self.__dict__.get("_rebuild_times")
        if times is None:
            times = self._rebuild_times = []
        times[:] = [t for t in times if now - t < _REBUILD_WINDOW]
        times.append(now)
        if len(times) >= _REBUILD_COUNT:
            site = _caller_site()
            slot = "ui_children" if key == "default" else f"ui_slots[{key!r}]"
            _dev_warning(
                ("rebuild", type(self), site),
                "%s.%s replaced %d times within %g s with the same component "
                "types: bind the changing values (computed) or use Show / "
                "For / Dynamic. Assigned at %s",
                type(self).__name__,
                slot,
                len(times),
                _REBUILD_WINDOW,
                site,
            )

    def _serialize_slot(self, key: str, budget: list | None = None):
        """The slot as sent to the browser: a list of wrapper props, the slot
        name for a slot built by a function. budget: see _get_wrapper_props"""
        slot = self.ui_slots[key]
        if isinstance(slot, (list, tuple)):
            texts = []
            result = self._serialize_children(slot, budget, texts)
            live = self._live_texts
            if texts or (live and key in live):
                if live is None:
                    live = self._live_texts = {}
                for text in live.get(key, ()):
                    if text not in texts:
                        text._suspend()
                live[key] = texts
            return result
        if callable(slot):
            self.on(
                "create_slot_" + key,
                self._handle_create_slot,
                slot,
                clear_existing=True,
            )
            return key
        return slot

    def _serialize_children(
        self, children, budget: list | None = None, texts: list | None = None
    ):
        """Wrapper props of a list of children (components and strings),
        the children of transparent components are spliced in. texts
        collects the bound texts"""
        result = []
        for i, child in enumerate(children):
            if isinstance(child, str):
                result.append({"compId": child})
                continue
            if isinstance(child, Observable):
                # put into the list directly
                child = Text(child)
                child._parent = self
                if isinstance(children, list):
                    children[i] = child
            if child._transparent:
                result.extend(
                    self._serialize_children(
                        child.ui_slots["default"], budget, texts
                    )
                )
                continue
            if child._is_text:
                if texts is None:
                    if self._live_texts is None:
                        self._live_texts = {}
                    texts = self._live_texts.setdefault(None, [])
                if child not in texts:
                    texts.append(child)
            result.append(child._get_wrapper_props(budget))
        return result

    def _resend_slot_of(self, child):
        """The children of a transparent child changed, or a bound text
        with a protocol 0 frontend: send the slot that holds it"""
        if self._transparent:
            parent = self._parent
            if parent is not None:
                parent._resend_slot_of(self)
            return
        for key, slot in self.ui_slots.items():
            if isinstance(slot, list) and any(c is child for c in slot):
                break
        else:
            return
        if get_environment().frontend.protocol >= 1:
            if self._index in _frontend_known:
                self._update_frontend({"slots": {key: None}})
        elif self._js_component is not None:
            self._update_frontend({"slots": {key: self._serialize_slot(key)}})

    def _get_wrapper_props(self, budget: list | None = None):
        """Wrapper props with the init data of the component (and of its
        children) if the browser has no instance of it. budget: [number of
        components that may still be sent along], None for a protocol 0
        frontend"""
        props = self._get_my_wrapper_props()
        if (
            budget is not None
            and budget[0] > 0
            and self._index not in _mount_tokens
        ):
            budget[0] -= 1
            props["init"] = self._get_init_data(budget)
        return props

    def _get_init_data(self, budget: list | None = None):
        """All the browser needs to create the component (protocol >= 1)"""
        # first: updates from now on are sent
        _frontend_known.add(self._index)
        return {
            "type": self._component_name,
            "props": utils._json_safe(dict(self._get_js_props())),
            "slots": self._get_js_slots(budget),
            "methods": self._get_js_methods(),
            "events": self._get_frontend_events(),
            "protocol": 1,
            "comp": self,
        }

    def _handle_create_slot(self, ev: "Event"):
        comps = self._wrap_children(list(ev.arg(ev.value)))
        for comp in comps:
            if isinstance(comp, Component):
                comp._set_parent_recursive(self)
        if get_environment().frontend.protocol >= 1:
            return self._serialize_children(
                comps, [utils._INLINE_MAX_COMPONENTS]
            )
        return self._serialize_children(comps)

    def _get_debug_data(self, **kwargs):
        stack_trace = ""
        if self.context.capture_call_stack:
            import traceback

            stack_trace = "".join(
                traceback.format_list(traceback.extract_stack()[:-2])
            )
        return dict(**kwargs) | {
            "timestamp": time_now(),
            "stack_trace": stack_trace,
            "component_id": self._fullid,
            "component_index": self._index,
            "component_type": type(self).__name__,
        }

    def _js_call_method(self, method, args=[]):
        """Call method on frontend component"""
        env = get_environment()
        if env.type not in [Environment.LOCAL_APP, Environment.PYODIDE]:
            raise RuntimeError(
                f"JS component method call not supported in environment {env.type}"
            )
        if self._js_component is None:
            return  # not shown
        self._js_component._call_method(method, args, ignore_result=True)

    def _js_callback(self, name, arg=None):
        """Call callback on frontend component"""
        if name in self._js_callbacks:
            self._js_callbacks[name](arg)

    # @result_to_js
    def _js_init(self):
        if get_environment().frontend.protocol >= 1:
            return self._get_init_data([utils._INLINE_MAX_COMPONENTS])
        return {
            "slots": self._get_js_slots(),
            "props": self._get_js_props(),
            "methods": self._get_js_methods(),
            "events": self._get_registered_events(),
            "type": self._component_name,
        }

    @utils._count_calls
    def _update_frontend(self, data=None, method="update_frontend", blocking=False):
        environment = get_environment()
        environment.frontend.update_component(self, data, method, blocking=blocking)

    def download_file(
        self,
        data: bytes,
        filename: str,
        mime_type: str = "application/octet-stream",
    ):
        import base64

        if callback := self._js_callbacks.get("download", None):
            ret = callback(
                dict(
                    encoded_data=base64.b64encode(data).decode("utf-8"),
                    filename=filename,
                    applicationType=mime_type,
                )
            )
            if ret:
                ret.catch(print_exception)

    @utils._count_calls
    def on(
        self,
        events: str | list,
        func: Callable[[Event], None] | Callable[[], None],
        arg: object = None,
        clear_existing: bool = False,
    ):
        """Add event listener"""
        events = [events] if isinstance(events, str) else events

        num_args = len(inspect.signature(func).parameters)

        if num_args == 0:
            wrapper = lambda _: func()
        elif arg is not None:

            def wrapper(ev: Event):
                ev.arg = arg
                return func(ev)

        else:
            wrapper = func

        added = False
        for event in events:
            if clear_existing:
                self._callbacks[event] = []

            if event not in self._callbacks:
                self._callbacks[event] = []
                added = added or (
                    event not in _NOT_BROWSER_EVENTS
                    and not event.startswith("create_slot_")
                )
            self._callbacks[event].append(wrapper)
        if added and self._index in _frontend_known:
            self._update_frontend({"events": None})
        return self

    @utils._count_calls
    def on_mounted(
        self,
        func: Callable[[dict], None] | Callable[[], None],
        arg: object = None,
    ):
        return self.on("mounted", func, arg)

    @utils._count_calls
    def on_unmount(
        self,
        func: Callable[[dict], None] | Callable[[], None],
        arg: object = None,
    ):
        return self.on("unmount", func, arg)

    @utils._count_calls
    def on_before_save(
        self,
        func: Callable[[dict], None] | Callable[[], None],
        arg: object = None,
    ):
        return self.on("before_save", func, arg)

    @utils._count_calls
    def on_save(
        self,
        func: Callable[[dict], None] | Callable[[], None],
        arg: object = None,
    ):
        return self.on("save", func, arg)

    @utils._count_calls
    def on_before_load(
        self,
        func: Callable[[dict], None] | Callable[[], None],
        arg: object = None,
    ):
        return self.on("before_load", func, arg)

    def on_load(
        self,
        func: Callable[[dict], None] | Callable[[], None],
        arg: object = None,
    ):
        return self.on("load", func, arg)

    def _dump(self):
        if self._id:
            derived = self._derived_props
            if derived:
                return {
                    k: v for k, v in self._props.items() if k not in derived
                }
            return self._props
        return None

    def _load(self, data):
        if data is not None:
            for key in self._derived_props:
                # computed, not loaded
                if key in self._props:
                    data[key] = self._props[key]
                else:
                    data.pop(key, None)
            self._props = data

    def _dump_recursive(self, exclude_default):
        def func(comp, arg):
            data, exclude = arg
            if comp._namespace:
                if comp._id in data:
                    raise RuntimeError("Duplicate id in components", comp._id)
                data[comp._id] = {}
                data = data[comp._id]
                exclude = exclude[comp._id] if exclude else None

            value = comp._dump()
            if not value:
                return (data, exclude)
            if exclude is not None and comp._id in exclude:
                for key in list(value.keys()):
                    if (
                        key in exclude[comp._id]
                        and exclude[comp._id][key] == value[key]
                    ):
                        del value[key]
            if not value:
                return (data, exclude)

            if not comp._id:
                raise RuntimeError(
                    f"Component {type(comp)} with input data {value} must have id"
                )
            if comp._id in data:
                raise RuntimeError("Duplicate id in components", comp._id)

            data[comp._id] = value
            return (data, exclude)

        data = {}
        self._recurse(func, True, set(), (data, exclude_default))
        return data

    def _dump_storage(self, include_data=False):
        def func(comp, data):
            if comp._namespace:
                data[comp._id] = {}
                data = data[comp._id]

            if not comp.storage._metadata.entries.keys():
                return data

            if not comp._id:
                raise RuntimeError(
                    "Component with input storage must have id"
                    + str(comp.__class__)
                    + str(comp.storage._metadata.entries.keys())
                )

            if comp._id in data:
                raise RuntimeError("Duplicate keys in components", comp._id)

            data[comp._id] = comp.storage._dump(include_data)
            return data

        data = {}
        self._recurse(func, True, set(), data)
        return data

    def _save_storage_local(self):
        self._recurse(lambda comp: comp.storage._save_local(), True, set())

    def _load_storage_local(self):
        self._recurse(lambda comp: comp.storage._load_local(), True, set())

    def _load_storage(self, data):
        def func(comp, data):
            if comp._namespace:
                if comp._id not in data:
                    return data
                data = data[comp._id]

            if not comp._id:
                return data

            comp.storage._load_data(data.get(comp._id, None))
            return data

        self._recurse(func, True, set(), data)

    def _load_recursive(self, data, update_frontend=False):
        self._block_frontend_update = True

        def func(comp, data):
            if comp._namespace:
                if comp._id not in data:
                    return data
                data = data[comp._id]

            if not comp._id:
                return data

            if comp._id in data:
                comp._block_frontend_update = True
                comp._load(data[comp._id])
                if update_frontend:
                    comp._update_frontend()
                comp._block_frontend_update = False
            return data

        self._recurse(func, True, set(), data)
        self._block_frontend_update = False

    @utils._count_calls
    def _recurse(
        self, func: Callable, parent_first: bool, visited: set, arg=None
    ):
        """Recursively call function for all components"""
        if len(visited) == 0:
            utils._trace_call("_recurse.start")

        if self in visited:
            utils._trace_call("_recurse.alread_visited")
            return
        visited.add(self)

        if parent_first:
            arg = func(self) if arg is None else func(self, arg)

        for slot in self.ui_slots.values():
            if isinstance(slot, Callable):
                continue
            for comp in slot:
                if not isinstance(comp, str):
                    comp._parent = self
                    comp.context = self.context
                    comp._recurse(func, parent_first, visited, arg)

        if not parent_first:
            arg = func(self) if arg is None else func(self, arg)

    @utils._count_calls
    def _emit_recursive(self, event, value: Optional[dict] = None) -> None:
        """Emit event to all components"""
        if _observable.current_batch() is None:
            # one scope for all handlers
            with _observable.batch(defer_listeners=False):
                return self._emit_recursive(event, value)
        self._recurse(
            lambda comp: comp._handle(event, value),
            parent_first=False,
            visited=set(),
        )
        return None

    @utils._count_calls
    def _set_parent(self, parent):
        self._parent = parent
        self.context = parent.context
        if self._namespace_id is None:
            return
        # the namespace follows the new parent, now or when it is known
        if parent._namespace_id is None:
            self._namespace_id = None
            return
        expected = parent._fullid if parent._namespace else parent._namespace_id
        if expected != self._namespace_id:
            self._namespace_id = None
            if self.context and not self._block_frontend_update:
                utils._trace_call("_calc_namespace_id._set_parent")
                self._calc_namespace_id()

    @utils._count_calls
    def _set_parent_recursive(self, parent):
        """Set parent for all components"""
        self._set_parent(parent)

        def func(comp):
            for slot in comp.ui_slots.values():
                if isinstance(slot, Callable):
                    continue
                for child in slot:
                    if not isinstance(child, str):
                        child._set_parent(comp)

        self._recurse(func, True, set())

    def _clear_js_callbacks(self):
        self._js_callbacks = {}

    @utils._count_calls
    def _set_js_component(self, js_comp):
        """Mount signal of a protocol 0 frontend"""
        self._js_component = js_comp
        if self._index not in _mount_tokens:
            _mount_tokens[self._index] = None
            self._run_mount_hook()

    @utils._count_calls
    def _set_js_callback(self, name, func):
        if name == "__protocol__":
            # handshake of the frontend, sent before the first _js_init
            get_environment().frontend.protocol = func
            return
        self._js_callbacks[name] = func

    def _mount(self, js_comp, token, callbacks):
        """The browser mounted an instance of the component (protocol >= 1):
        js_comp is its JS component, callbacks are pairs (name, function)"""
        current = _components.get(self._index)
        if current is not None and current is not self:
            # another component object took over the index
            return current._mount(js_comp, token, callbacks)
        if hasattr(callbacks, "to_py"):
            callbacks = callbacks.to_py()
        self._js_callbacks = {name: func for name, func in callbacks}
        self._js_component = js_comp
        _mount_tokens[self._index] = token
        _frontend_known.add(self._index)
        with _observable.batch(defer_listeners=False):
            # bindings suspended by an unmount (the instance was moved)
            if self._lazy_bindings:
                self._resolve_bindings()
            if self._live_texts:
                for texts in self._live_texts.values():
                    for text in texts:
                        text._resume()
            self._handle("mounted")
            self._run_mount_hook()

    def _unmount(self, token=None):
        """The browser removed the instance mounted with token, None: any
        (protocol 0)"""
        index = self._index
        if token is not None and token != _mount_tokens.get(index):
            return  # of an earlier instance, the component is mounted again
        with _observable.batch(defer_listeners=False):
            self._handle("unmount")
            try:
                self._unmount_hook()
            except Exception as e:
                print_exception(e, file=sys.stdout)
        _mount_tokens.pop(index, None)
        _frontend_known.discard(index)
        self._js_component = None
        self._js_callbacks = {}
        if self._lazy_bindings or self._live_texts:
            self._suspend_bindings()

    def _run_mount_hook(self):
        try:
            self._mount_hook()
        except Exception as e:
            print_exception(e, file=sys.stdout)

    def _mount_hook(self):
        """Called after the mounted handlers of every mount"""
        if self._effects:
            for reaction in self._effects:
                # runs when the handler that mounted is done
                reaction.resume(run=False)

    def _unmount_hook(self):
        """Called after the unmount handlers, the component still counts as
        mounted"""
        if self._effects:
            for reaction in self._effects:
                reaction.suspend()

    def effect(self, fn: Callable[[], None], name: str = ""):
        """Run fn when the component is mounted and again, while it stays
        mounted, after an observable, computed value or state key it read
        has changed (once per event, after the bound props were updated).

        For imperative updates of the browser: drawing a figure, updating a
        viewer. Never runs where nothing is shown (compute jobs). Returns a
        function that removes the effect.

        >>> plot.effect(lambda: plot.draw(figure(self.state["radius"])))
        """

        deferred = [False]

        def run_deferred():
            if reaction.active:
                deferred[0] = True
                try:
                    reaction.run()
                finally:
                    deferred[0] = False

        def run():
            if not deferred[0] and not _can_block():
                # e.g. a timer callback in pyodide: fn may need blocking
                # calls of the browser
                _defer(run_deferred)
                return
            fn()

        reaction = Reaction(
            run,
            _observable.EFFECT,
            name or type(self).__name__ + ".effect",
            start=False,
        )
        reaction.owner = self
        if self._effects is None:
            self._effects = []
        self._effects.append(reaction)
        if self._index in _mount_tokens:
            reaction.resume(run=False)

        def dispose():
            reaction.dispose()
            try:
                self._effects.remove(reaction)
            except ValueError:
                pass

        return dispose

    @utils._count_calls
    def _get_my_wrapper_props(self, *args, **kwargs):
        return {"compId": self._index}

    def _get_js_slots(self, budget: list | None = None):
        return {key: self._serialize_slot(key, budget) for key in self.ui_slots}

    def _get_js_props(self):
        """The props as needed by a browser: called when the init data or a
        full update of the component is sent"""
        if self._lazy_bindings:
            self._resolve_bindings(send=False)
        return self._props

    def _get_js_methods(self):
        return []

    def _handle(self, event, value: Optional[dict] = None) -> None:
        """Handle event"""
        callbacks = self._callbacks.get(event)
        if not callbacks:
            return None
        ret = None
        try:
            if is_pyodide():
                import pyodide.ffi

                if isinstance(value, pyodide.ffi.JsProxy):
                    value = value.to_py()

            ev = Event(component=self, name=event, value=value)
            if _observable.current_batch() is None:
                created = _created
                # updates of the handlers leave as one message
                with _observable.batch(defer_listeners=False):
                    for func in callbacks:
                        ret = func(ev)
                if (
                    _created - created > _HANDLER_MAX_CREATED
                    and event not in _PYTHON_EVENTS
                    and not event.startswith("create_slot_")
                ):
                    self._report_handler(event, callbacks, _created - created)
            else:
                for func in callbacks:
                    ret = func(ev)

        except (ForbiddenError, CaseDeletedError) as e:
            # refusals of the case store (read only, deleted): no traceback
            logger.warning("Refused (%s): %s", event, e)
        except Exception as e:
            print("have exception in _handle", str(e))
            print_exception(e, file=sys.stdout)
        return ret

    def _report_handler(self, event, callbacks, created):
        sites = ", ".join(_code_site(func) for func in callbacks)
        _dev_warning(
            ("handler", type(self), event, sites),
            "Handler of %s '%s' created %d components: a parameter change "
            "should update values, not rebuild the UI. Handler at %s",
            type(self).__name__,
            event,
            created,
            sites,
        )

    def _get_registered_events(self):
        return list(self._callbacks.keys())

    def _get_frontend_events(self):
        """Events the browser has to send (protocol >= 1)"""
        return [
            event
            for event in self._callbacks
            if event not in _NOT_BROWSER_EVENTS
            and not event.startswith("create_slot_")
        ]


class Text(Component):
    """A text child bound to an observable: created for an observable in a
    list of children. It has no element of its own, the browser updates the
    text in place."""

    _is_text = True

    def __init__(self, source: Observable):
        super().__init__("text")
        self._source = source
        self._text = None
        self._quiet = False
        self._reaction = None

    @property
    def text(self) -> str:
        """The current text"""
        return _to_text(_display(self._source))

    def _update(self):
        text = _to_text(self._source.display_value)
        if text == self._text:
            return
        self._text = text
        if self._quiet:
            return
        if get_environment().frontend.protocol >= 1:
            self._update_frontend({"text": text})
        elif self._parent is not None:
            self._parent._resend_slot_of(self)

    def _resume(self, quiet=False):
        reaction = self._reaction
        if reaction is None:
            reaction = self._reaction = Reaction(
                self._update, _observable.SYNC, "Text", False
            )
            reaction.owner = self
        if get_environment().frontend.protocol >= 1:
            _frontend_known.add(self._index)
        if reaction.active:
            return
        self._quiet = quiet
        try:
            reaction.resume()
        except Exception as e:
            print_exception(e, file=sys.stdout)
        finally:
            self._quiet = False

    def _suspend(self):
        _frontend_known.discard(self._index)
        if self._reaction is not None:
            self._reaction.suspend()

    def _get_wrapper_props(self, budget: list | None = None):
        self._resume(quiet=True)
        text = self._text or ""
        if get_environment().frontend.protocol >= 1:
            return {"compId": f"t{self._index}", "text": text}
        return {"compId": text}

    def _get_my_wrapper_props(self, *args, **kwargs):
        return self._get_wrapper_props()

    def _hide_by(self, owner, hide: bool):
        pass

    def on_mounted(self, func, arg=None):
        raise TypeError("A bound text is never mounted")

    def effect(self, fn, name=""):
        raise TypeError("A bound text is never mounted: no effect")


def _can_block() -> bool:
    if not is_pyodide():
        return True
    try:
        from pyodide.ffi import can_run_sync
    except ImportError:
        return True
    return can_run_sync()


def _defer(fn) -> None:
    """fn from an asyncio task: a promising entry point in pyodide"""
    import asyncio

    async def run():
        fn()

    asyncio.get_event_loop().create_task(run())


del C
