# pylint: disable=protected-access
import copy
import dataclasses
import inspect
import itertools
import pickle
import sys
import functools
from pathlib import Path
from typing import Callable, List, Optional, Tuple, TypeVar

import orjson
import pydantic

from .. import api
from ..utils import (
    Environment,
    calc_hash,
    get_environment,
    is_pyodide,
    print_exception,
    time_now,
)

_component_counter = itertools.count()
_components = {}
_components_with_id = {}

_local_storage_path = Path.home() / ".cache" / "webapp_local_storage"


def get_component(index: int):
    return _components[index]


def reset_components():
    global _component_counter
    _components.clear()


@dataclasses.dataclass
class AppStatus:
    capture_events: bool = False
    capture_call_stack: bool = False
    app_id: int | None = None
    file_id: int | None = None
    app: object = None
    components_by_id: dict[str, object] = dataclasses.field(
        default_factory=dict
    )

    def update(self, options):
        if "capture_events" in options:
            self.capture_events = options["capture_events"]
        if "capture_call_stack" in options:
            self.capture_call_stack = options["capture_call_stack"]


C = TypeVar("T", bound="Component")


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


class Storage:
    """Storage class for components, use it to store large chunks of data on the backend"""

    _data: dict[str, str | dict | list | bytes]
    _metadata: _StorageMetadata
    _needs_deletion: list[str]
    _needs_save: set[str]
    _component: C

    def __init__(self, component: C):
        self._component = component
        self._data = {}
        self._metadata = _StorageMetadata(entries={})
        self._needs_deletion = []
        self._needs_save = set()

    def _encode(self, value: str | dict | list | bytes) -> bytes:
        if isinstance(value, bytes):
            return value
        if isinstance(value, str):
            return value.encode("utf-8")
        return orjson.dumps(value, option=orjson.OPT_SERIALIZE_NUMPY)

    def _decode(self, value: bytes, type_: str) -> str | dict | list | bytes:
        if type_ == "str":
            return value.decode("utf-8")
        if type_ == "bytes":
            return value
        return orjson.loads(value)

    def _dump_metadata(self):
        return self._metadata.model_dump()["entries"]

    def _dump_data(self):
        return copy.deepcopy(self._data)

    def _load_metadata(self, data):
        self._metadata = _StorageMetadata(entries=data)

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

    def load(self, key: str):
        if not get_environment().have_backend:
            self._load_local()
            return
        file_id = self._component._status.file_id
        if file_id is None:
            return
        mdata = self._metadata.get(key)
        if mdata is None:
            return
        data = api.get(f"/files/{file_id}/files/{mdata.hash}")
        self._data[key] = self._decode(data, mdata.type_)
        if key in self._needs_save:
            self._needs_save.remove(key)

    def save(self):
        if not self._needs_save:
            return
        if not get_environment().have_backend:
            self._save_local()
            return
        file_id = self._component._status.file_id
        if self._needs_deletion:
            api.delete(f"/files/{file_id}/files", data=self._needs_deletion)
        for key in self._needs_save:
            mdata = self._metadata.get(key)
            api.post(
                f"/files/{file_id}/files/{mdata.hash}",
                self._encode(self._data[key]),
            )
        self._needs_save.clear()

    def get(self, key: str):
        """Get data from storage"""
        if key not in self._data:
            self.load(key)

        value = self._data.get(key, None)

        if value is not None and self._metadata.get(key).type_ == "pickle":
            value = pickle.loads(value)

        return value

    def set(
        self,
        key: str,
        value: str | dict | list | bytes | object,
        use_pickle=False,
    ):
        """Set data in storage"""
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
        self._metadata.set(
            key,
            self._encode(value),
            type_,
            id=self._encode(self._component._fullid),
        )
        self._needs_save.add(key)
        if old_hash and old_hash != self._metadata.get(key):
            self._needs_deletion.append(old_hash)

    def delete(self, key: str):
        """Delete data from storage"""
        if key in self._data:
            del self._data[key]
        if key in self._metadata.entries:
            self._needs_deletion.append(self._metadata.get(key).hash)
            del self._metadata.entries[key]
        if key in self._needs_save:
            self._needs_save.remove(key)


class BlockFrontendUpdate(type):
    def __new__(cls, name, bases, dct):
        init_method = dct.get("__init__")
        if init_method is not None:

            @functools.wraps(init_method)
            def wrapped_init(self, *args, **kwargs):
                self._block_frontend_update = True
                init_method(self, *args, **kwargs)
                self._block_frontend_update = False

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


class Component(metaclass=BlockFrontendUpdate):
    """Base component class, the component name is passed as argument"""

    _callbacks: dict[str, List[Callable]]
    _id: str
    _namespace_id: str | None = None
    _parent: C | None = None
    _status: AppStatus = None
    _namespace: bool
    _js_component = None
    storage: Storage

    def __init__(
        self,
        component: str,
        *ui_children: C | str,
        ui_slots: dict[str, list] | None = None,
        namespace: bool = False,
        ui_style: str | dict | None = None,
        ui_class: str | list[str] | None = None,
        id: str = "",
    ):
        self._index = next(_component_counter)
        _components[self._index] = self

        if "." in id:
            raise ValueError("Component id cannot contain '.'")

        self._callbacks = {}
        self._js_callbacks = {}

        self.component = component
        self._component_name = component
        self._props = {}
        self.ui_slots = ui_slots or {}
        self._namespace = namespace
        self._id = id

        self.storage = Storage(self)
        self.on_save(self.storage.save)

        self.ui_slots["default"] = list(ui_children)

        for c in self.ui_slots["default"]:
            if isinstance(c, Component):
                c._parent = self

        if isinstance(ui_style, dict):
            self._props["style"] = ";".join(
                f"{k}:{v}" for k, v in ui_style.items()
            )
        elif isinstance(ui_style, str):
            self._props["style"] = ui_style
        else:
            self._props["style"] = ""

        if ui_class:
            self._props["class"] = (
                ui_class if isinstance(ui_class, str) else " ".join(ui_class)
            )

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
        self._set_prop("style", value)

    @property
    def ui_class(self):
        return self._props.get("class", "")

    @ui_class.setter
    def ui_class(self, value):
        self._set_prop("class", value)

    @property
    def ui_hidden(self):
        """Set display to none. Compare with below - the class hidden means the element will not show and will not take up space in the layout."""
        return (
            False
            if "class" not in self._props
            else ("hidden" in self._props["class"].split(" "))
        )

    @ui_hidden.setter
    def ui_hidden(self, value):
        if value:
            if "class" not in self._props:
                self._set_prop("class", "hidden")
            elif "hidden" not in self._props["class"].split(" "):
                self._set_prop("class", self._props["class"] + " hidden")
        else:
            if "class" in self._props:
                self._set_prop(
                    "class", self._props["class"].replace("hidden", "").strip()
                )

    @property
    def ui_invisible(self):
        """Set visibility to hidden. Compare with above - the class invisible means the element will not show, but it will still take up space in the layout."""
        return (
            False
            if "class" not in self._props
            else ("invisible" in self._props["class"].split(" "))
        )

    @ui_invisible.setter
    def ui_invisible(self, value):
        if value:
            if "class" not in self._props:
                self._set_prop("class", "invisible")
            elif "invisible" not in self._props["class"].split(" "):
                self._set_prop("class", self._props["class"] + " invisible")
        else:
            if "class" in self._props:
                self._set_prop(
                    "class",
                    self._props["class"].replace("invisible", "").strip(),
                )

    def _calc_namespace_id(self):
        if self._namespace_id is None:
            parent = self._parent
            if parent is None:
                raise RuntimeError(
                    "Parent of component is not set", self._id, type(self)
                )
            self._namespace_id = (
                parent._fullid if parent._namespace else parent._namespace_id
            )
            self._status = parent._status
            if self._id:
                _components_with_id[self._fullid] = self
                self._status.components_by_id[self._fullid] = self

    @property
    def _fullid(self):
        if self._namespace_id is None:
            self._calc_namespace_id()

        if not self._id:
            return ""

        if self._namespace_id:
            return self._namespace_id + "." + self._id
        return self._id

    def _set_prop(self, key: str, value):
        self._props[key] = value
        self._update_frontend({"props": {key: value}})

    def _set_slot(self, key: str, value):
        self.ui_slots[key] = value
        if isinstance(value, list):
            for comp in value:
                if isinstance(comp, Component):
                    comp._set_parent_recursive(self)
        elif isinstance(value, Component):
            value._set_parent_recursive(self)
        self._update_frontend(
            {
                "slots": {
                    key: (
                        [
                            (
                                {"compId": v}
                                if isinstance(v, str)
                                else v._get_my_wrapper_props()
                            )
                            for v in value
                        ]
                        if isinstance(value, list)
                        else value
                    )
                }
            }
        )

    def _get_debug_data(self, **kwargs):
        stack_trace = ""
        if self._status.capture_call_stack:
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
        self._js_component._call_method(method, args, ignore_result=True)

    # @result_to_js
    def _js_init(self):
        self._js_callbacks = {}
        return {
            "slots": self._get_js_slots(),
            "props": self._get_js_props(),
            "methods": self._get_js_methods(),
            "events": self._get_registered_events(),
            "type": self.component,
        }

    def _update_frontend(self, data=None, method="update_frontend"):
        environment = get_environment()
        environment.frontend.update_component(self, data, method)

    def download_file(
        self,
        data: bytes,
        filename: str,
        mime_type: str = "application/octet-stream",
    ):
        import base64

        for callback in self._js_callbacks.get("download", []):
            callback(
                dict(
                    encoded_data=base64.b64encode(data).decode("utf-8"),
                    filename=filename,
                    applicationType=mime_type,
                )
            ).catch(print_exception)

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

        for event in events:
            if clear_existing:
                self._callbacks[event] = []

            if event not in self._callbacks:
                self._callbacks[event] = []
            self._callbacks[event].append(wrapper)
        return self

    def on_mounted(
        self,
        func: Callable[[dict], None] | Callable[[], None],
        arg: object = None,
    ):
        return self.on("mounted", func, arg)

    def on_before_save(
        self,
        func: Callable[[dict], None] | Callable[[], None],
        arg: object = None,
    ):
        return self.on("before_save", func, arg)

    def on_save(
        self,
        func: Callable[[dict], None] | Callable[[], None],
        arg: object = None,
    ):
        return self.on("save", func, arg)

    def on_load(
        self,
        func: Callable[[dict], None] | Callable[[], None],
        arg: object = None,
    ):
        return self.on("load", func, arg)

    def dump(self):
        """Override this method for components with a state. Dumps component state for storage on backend. Only data types which can be converted to json are allowed"""
        if self._id:
            return self._props
        return None

    def load(self, data):
        """Override this method for components with a state. Loads component data from backend (data argument is the return value of dump)"""
        if data is not None:
            self._props = data

    def _dump_recursive(self):
        def func(comp, data):
            if comp._namespace:
                data[comp._id] = {}
                data = data[comp._id]

            value = comp.dump()
            if not value:
                return data

            if not comp._id:
                raise RuntimeError("Component with input data must have id")

            if comp._id in data:
                raise RuntimeError("Duplicate keys in components", comp._id)

            data[comp._id] = value
            return data

        data = {}
        self._recurse(func, True, set(), data)
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

            metadata = comp.storage._dump_metadata()
            if include_data:
                data[comp._id] = {
                    "_have_data": True,
                    "data": comp.storage._dump_data(),
                    "metadata": metadata,
                }
            else:
                data[comp._id] = metadata
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

            if comp._id in data:
                comp_data = data[comp._id]
                if comp_data.get("_have_data", False):
                    comp.storage._load_metadata(comp_data["metadata"])
                    comp.storage._data = copy.deepcopy(comp_data["data"])
                else:
                    comp.storage._load_metadata(comp_data)
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
                comp.load(data[comp._id])
                if update_frontend:
                    comp._update_frontend()
                comp._block_frontend_update = False
            return data

        self._recurse(func, True, set(), data)
        self._block_frontend_update = False

    def _recurse(
        self, func: Callable, parent_first: bool, visited: set, arg=None
    ):
        """Recursively call function for all components"""

        if self in visited:
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
                    comp._status = self._status
                    comp._recurse(func, parent_first, visited, arg)

        if not parent_first:
            arg = func(self) if arg is None else func(self, arg)

    def _emit_recursive(self, event, value: Optional[dict] = None) -> None:
        """Emit event to all components"""
        self._recurse(
            lambda comp: comp._handle(event, value),
            parent_first=False,
            visited=set(),
        )
        return None

    def _set_parent_recursive(self, parent):
        """Set parent for all components"""
        self._parent = parent
        self._status = parent._status

        def func(comp):
            for slot in comp.ui_slots.values():
                if isinstance(slot, Callable):
                    continue
                for child in slot:
                    if not isinstance(child, str):
                        child._parent = comp
                        child._status = comp._status

        self._recurse(func, True, set())

    def _clear_js_callbacks(self):
        self._js_callbacks = {}

    def _set_js_component(self, js_comp):
        self._js_component = js_comp

    def _set_js_callback(self, name, func):
        if name not in self._js_callbacks:
            self._js_callbacks[name] = []

        self._js_callbacks[name].append(func)

    def _get_my_wrapper_props(self, *args, **kwargs):
        return {"compId": self._index}

    def _get_js_slots(self):
        ret = {}
        for key, slot in self.ui_slots.items():
            if isinstance(slot, Callable):

                def handle_create(ev: Event):
                    create_function = ev.arg
                    comps = create_function(ev.value)
                    for comp in comps:
                        comp._set_parent_recursive(self)
                    return [
                        (
                            {"compId": comp}
                            if isinstance(comp, str)
                            else comp._get_my_wrapper_props()
                        )
                        for comp in comps
                    ]

                ret[key] = key
                self.on(
                    "create_slot_" + key,
                    handle_create,
                    slot,
                    clear_existing=True,
                )
            else:
                ret[key] = [
                    (
                        {"compId": comp}
                        if isinstance(comp, str)
                        else comp._get_my_wrapper_props()
                    )
                    for comp in slot
                ]
        return ret

    def _get_js_props(self):
        return self._props

    def _get_js_methods(self):
        return []

    def _handle(self, event, value: Optional[dict] = None) -> None:
        """Handle event"""
        ret = None
        try:
            if is_pyodide():
                import pyodide.ffi

                if isinstance(value, pyodide.ffi.JsProxy):
                    value = value.to_py()

            if event in self._callbacks:
                ev = Event(component=self, name=event, value=value)
                for func in self._callbacks[event]:
                    ret = func(ev)

        except Exception as e:
            print("have exception in _handle", str(e))
            print_exception(e, file=sys.stdout)
        return ret

    def _get_registered_events(self):
        return list(self._callbacks.keys())


del C
