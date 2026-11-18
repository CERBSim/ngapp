"""Utility functions for testing ngapp apps.

This module provides helpers for comparing component state and local storage.
Snapshot files use the same pickled data format as
 :meth:`ngapp.app.App.save_local`, so you can reuse ``.sav`` files created
 from the running app inside your test suite.
"""

import contextlib
import os
import pickle
import tempfile
from functools import wraps
from pathlib import Path

import deepdiff

import ngapp.components.basecomponent
from ngapp.app import App
from ngapp.utils import EnvironmentType, read_json, set_environment, write_json

os.environ["WEBAPP_TESTING"] = str(True)


def _get_folder_path(folder_path: str | Path, create_folder: bool = True):
    path = (
        Path(folder_path)
        if "tests/cases" in str(folder_path)
        else Path("tests/cases") / folder_path
    )
    if create_folder:
        path.mkdir(parents=True, exist_ok=True)
    return path


def _set_local_storage_path(folder_path: str, create_folder: bool = True):
    path = (
        _get_folder_path(folder_path, create_folder=create_folder) / "storage"
    )
    ngapp.components.basecomponent._local_storage_path = path
    return path


def assert_equal_components_data(data: dict, comparison: dict):
    data.pop("metadata")
    comparison.pop("metadata")
    diff = deepdiff.DeepDiff(data, comparison, ignore_order=True)
    assert diff == {}


def _load_snapshot_file(path: Path) -> dict:
    """Load snapshot data from *path*.

    Snapshot files are stored as pickled dictionaries, compatible with the
    output of :meth:`ngapp.app.App._dump_app` and :meth:`ngapp.app.App.save_local`.
    For backwards compatibility, if unpickling fails we fall back to reading
    JSON from the same path.
    """

    with path.open("rb") as fh:
        return pickle.load(fh)


def snapshot(
    app: App,
    folder_path: str,
    filename: str = "data.sav",
    write_data: bool = False,
    keep_storage: bool = False,
    check_data: bool = False,
    check_storage: bool = False,
):
    """Save the data of the app to a file or compare it to the reference data if requested"""
    folder = _get_folder_path(folder_path)
    _set_local_storage_path(folder_path)
    file_path = folder / filename

    if check_data:
        data = app._dump_app()
        ref_data = _load_snapshot_file(file_path)
        assert_equal_components_data(data, ref_data)

    if check_storage:
        with tempfile.TemporaryDirectory() as tempdir:
            temp_storage = _set_local_storage_path(tempdir)
            app._save_storage_local()
            temp_storage_files = sorted(list(temp_storage.glob("*")))
            saved_storage_files = sorted(list((folder / "storage").glob("*")))
            if len(temp_storage_files) != len(saved_storage_files):
                raise AssertionError(
                    "Number of storage files do not match. Maybe you forgot to save the storage?\n"
                    f"Number of temp files: {len(temp_storage_files)}, number of saved files: {len(saved_storage_files)}.\n"
                    f"Temp files {temp_storage_files},\n saved files {saved_storage_files}"
                )
            for saved_file, temp_file in zip(
                saved_storage_files, temp_storage_files
            ):
                try:
                    # assume data is json
                    assert (
                        deepdiff.DeepDiff(
                            read_json(saved_file),
                            read_json(temp_file),
                            ignore_order=True,
                        )
                        == {}
                    )
                except Exception:
                    # try reading as text
                    try:
                        assert saved_file.read_text() == temp_file.read_text()
                    except Exception as e:
                        raise Exception(
                            f"Error comparing {saved_file}, data {saved_file.read_text()} and {temp_file}, data {temp_file.read_text()}"
                        ) from e

    if write_data:
        data = app._dump_app(keep_storage=keep_storage)
        with file_path.open("wb") as fh:
            pickle.dump(data, fh)


def load(
    app: App,
    *,
    data: dict | None = None,
    filename: str | None = None,
    load_storage: bool = False,
):
    """Load the data into the app"""
    if filename is not None:
        path = Path(filename)
        data = _load_snapshot_file(path)
    app._load_app(data, load_local_storage=load_storage)


def load_case(app, folder_path, filename="data.sav", load_storage=False):
    """Load the data of a case and load it into the app.

    ``filename`` is expected to be a pickled dump compatible with
    :meth:`ngapp.app.App.save_local`, for example a ``.sav`` file created
    by the running app or a snapshot written by :func:`snapshot`.
    """
    _set_local_storage_path(folder_path, create_folder=False)
    folder_path = _get_folder_path(folder_path, create_folder=False)
    data = _load_snapshot_file(folder_path / filename)
    load(app, data=data, load_storage=load_storage)
    return data


def save_testing_data(folder_path: str | Path, testing_data: dict):
    """Save the testing data to a folder as json files"""
    folder_path = Path(folder_path)
    folder_path.mkdir(parents=True, exist_ok=True)
    for key, value in testing_data.items():
        write_json(value, folder_path / f"{key}.json")


def standalone_app_test(func):
    """Decorator for tests that only exercise Python app state.

    It sets up a minimal :class:`~ngapp.utils.Environment` in
    ``STANDALONE`` mode with a no-op ``update_component`` so that
    components can be constructed and updated without a real frontend.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):  # type: ignore[no-untyped-def]
        env = set_environment(EnvironmentType.STANDALONE, have_backend=False)
        # Ignore frontend updates during pure-Python tests
        env.frontend.update_component = (  # type: ignore[method-assign]
            lambda *a, **k: None
        )
        return func(*args, **kwargs)

    return wrapper


class _FakeJs:
    """Stand-in for a JS object: every attribute and call works and calls
    are recorded as (path, args)"""

    def __init__(self, calls, path=""):
        self.__dict__["_calls"] = calls
        self.__dict__["_path"] = path

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        return _FakeJs(self._calls, f"{self._path}.{name}".lstrip("."))

    def __setattr__(self, name, value):
        pass

    def __call__(self, *args, **kwargs):
        self._calls.append((self._path, args))
        return _FakeJs(self._calls, self._path + "()")

    def _call_method(self, method, args=(), ignore_result=True):
        self._calls.append((method, tuple(args)))


class _FakeLink:
    def __init__(self, frontend):
        self._frontend = frontend

    def call_method_ignore_return(self, id=None, prop=None, args=None):
        self._frontend._receive(id, args or [])

    def _split_and_send(self, data, key=None):
        return None


class FakeFrontend:
    """A browser stand-in speaking wire protocol 1 with the components, for
    tests without a browser (see :func:`mount`).

    It holds what a browser would show: the data of every component it got
    and which components are mounted. A component is mounted when it is
    reachable from the root through the slot lists it received; slots built
    by a function are rendered with :meth:`slot`.
    """

    def __init__(self):
        from ngapp.utils import BrowserFrontend, get_environment

        try:
            env = get_environment()
        except RuntimeError:
            env = set_environment(EnvironmentType.STANDALONE, False)
        self.frontend = env.frontend = BrowserFrontend(_FakeLink(self))
        #: every update message: a list of entries {"compId", "data"}
        self.messages: list[list[dict]] = []
        #: entries for components the browser has no data of
        self.dropped: list[dict] = []
        #: (component index, name, args) of calls of JS methods and callbacks
        self.calls: list[tuple] = []
        self.root = None
        self._nodes = {}
        self._texts = {}
        self._mounted = {}
        self._parents = {}
        self._hidden = set()
        self._tokens = 0
        self._dirty = False
        self._rendering = False

    # -- public ------------------------------------------------------------

    def mount(self, comp):
        """Show comp (the app, or a component unmounted before) with all
        its children, the way a browser does"""
        if self.root is None:
            self.root = comp._index
            # handshake and pull of the root, its children come inline
            comp._set_js_callback("__protocol__", 1)
        self._hidden.discard(comp._index)
        self._dirty = True
        self.render()
        return self

    def unmount(self, comp):
        """Remove the instance of comp and of its children (a closed dialog,
        an inactive tab) until :meth:`mount` shows it again"""
        self._hidden.add(comp._index)
        self._dirty = True
        self.render()

    def event(self, comp, name: str, value=None):
        """Send the event of a component as the browser does and return the
        result of its handlers; ``update:<prop>`` events change the prop
        shown in the browser as well. ``"click"`` also finds handlers
        registered with modifiers (``on_click`` registers ``"click.stop"``)"""
        if name not in comp._callbacks:
            match = [e for e in comp._callbacks if e.split(".")[0] == name]
            if len(match) == 1:
                name = match[0]
        node = self._nodes.get(comp._index)
        if name.startswith("update:") and node is not None:
            node["props"][name[len("update:") :]] = value
        result = comp._handle(name, value)
        self.render()
        return result

    def slot(self, comp, name: str, slot_props: dict | None = None):
        """Render a slot of comp that is built by a function and return its
        children"""
        slot_props = slot_props or {}
        result = comp._handle("create_slot_" + name, slot_props)
        node = self._nodes[comp._index]
        key = f"{name}:{slot_props.get('key')}"
        node["scoped"][key] = self._take_list(result or [])
        self._dirty = True
        self.render()
        return self._children(node["scoped"][key])

    @property
    def mounted(self) -> set:
        """Indices of the mounted components"""
        self.render()
        return set(self._mounted)

    def props(self, comp) -> dict | None:
        """Props of comp in the browser, None if it has no data of it"""
        self.render()
        node = self._nodes.get(comp._index)
        return None if node is None else node["props"]

    def children(self, comp, slot: str = "default") -> list | None:
        """Children of comp in the browser: components and texts"""
        self.render()
        node = self._nodes.get(comp._index)
        if node is None:
            return None
        return self._children(node["slots"].get(slot, []))

    def events(self, comp) -> list | None:
        self.render()
        node = self._nodes.get(comp._index)
        return None if node is None else node["events"]

    def render(self):
        """Mount and unmount what changed (done by all methods above)"""
        if self._rendering or self.root is None:
            return
        self._rendering = True
        try:
            for _ in range(100):
                if not self._dirty:
                    return
                self._dirty = False
                self._render()
            raise RuntimeError("FakeFrontend: mount handlers do not settle")
        finally:
            self._rendering = False

    # -- browser side --------------------------------------------------------

    def _js_call(self, call):
        # a message of the link: buffered updates leave first
        self.frontend.link._split_and_send({"type": "call"})
        self.calls.append(call)

    def _receive(self, name, args):
        if name == "resetApp":
            props = args[0]
            self.root = props["compId"]
            if "init" in props:
                self._take_init(self.root, props["init"])
            self._dirty = True
        elif name == "updateComponents":
            self.messages.append(args[0])
            for entry in args[0]:
                self._apply(entry["compId"], entry["data"], entry)

    def _apply(self, comp_id, data, entry=None):
        if isinstance(comp_id, str):
            if comp_id in self._texts and "text" in data:
                self._texts[comp_id] = data["text"]
            elif entry is not None:
                self.dropped.append(entry)
            return
        node = self._nodes.get(comp_id)
        if node is None:
            if entry is not None:
                self.dropped.append(entry)
            return
        if "props" in data:
            node["props"].update(data["props"])
        if "slots" in data:
            for key, slot in data["slots"].items():
                node["slots"][key] = self._take_list(slot)
        if data.get("type"):
            node["type"] = data["type"]
        if "events" in data:
            node["events"] = list(data["events"])
        self._dirty = True

    def _take_list(self, slot):
        """Moves init data and bound texts of wrapper props into the stores"""
        if not isinstance(slot, list):
            return slot
        out = []
        for wrapper in slot:
            comp_id = wrapper["compId"]
            if isinstance(comp_id, str):
                if "text" in wrapper:
                    self._texts[comp_id] = wrapper["text"]
            elif "init" in wrapper:
                self._take_init(comp_id, wrapper["init"])
            out.append({k: v for k, v in wrapper.items() if k != "init"})
        return out

    def _take_init(self, comp_id, init):
        slots = {k: self._take_list(v) for k, v in init["slots"].items()}
        if comp_id in self._mounted:
            return  # a live instance is up to date
        self._nodes[comp_id] = {
            "type": init["type"],
            "props": dict(init["props"]),
            "slots": slots,
            "scoped": {},
            "methods": list(init["methods"]),
            "events": list(init["events"]),
            "comp": init["comp"],
        }

    def _children(self, slot):
        from ngapp.components.basecomponent import get_component

        if not isinstance(slot, list):
            return slot
        out = []
        for wrapper in slot:
            comp_id = wrapper["compId"]
            if isinstance(comp_id, str):
                out.append(
                    self._texts.get(comp_id, wrapper["text"])
                    if "text" in wrapper
                    else comp_id
                )
            else:
                out.append(get_component(comp_id))
        return out

    def _render(self):
        from ngapp.components.basecomponent import (
            get_component,
            unmount_component,
        )

        order = []
        parents = {}
        texts = set()
        # not rendered, their data is kept
        pending = set()

        def visit(comp_id, parent, live):
            if comp_id in parents or comp_id in pending:
                return
            live = live and comp_id not in self._hidden
            if comp_id not in self._nodes:
                comp = get_component(comp_id) if live else None
                if comp is None:
                    return
                self._take_init(comp_id, comp._js_init())
            if live:
                parents[comp_id] = parent
                order.append(comp_id)
            else:
                pending.add(comp_id)
            node = self._nodes[comp_id]
            for slot in (*node["slots"].values(), *node["scoped"].values()):
                if not isinstance(slot, list):
                    continue
                for wrapper in slot:
                    child = wrapper["compId"]
                    if isinstance(child, str):
                        texts.add(child)
                    else:
                        visit(child, comp_id, live)

        visit(self.root, None, True)
        # a component under another parent gets a new instance, as do its
        # children
        moved = set()
        for comp_id in order:
            if comp_id in self._mounted and (
                parents[comp_id] != self._parents.get(comp_id)
                or parents[comp_id] in moved
            ):
                moved.add(comp_id)
        for comp_id in list(self._mounted):
            if comp_id not in parents or comp_id in moved:
                token = self._mounted.pop(comp_id)
                self._parents.pop(comp_id, None)
                if comp_id not in parents:
                    self._nodes.pop(comp_id, None)
                    pending.discard(comp_id)
                unmount_component(comp_id, token)
        # data nothing refers to is dropped
        for comp_id in list(self._nodes):
            if comp_id not in parents and comp_id not in pending:
                del self._nodes[comp_id]
        for text_id in list(self._texts):
            if text_id not in texts:
                del self._texts[text_id]
        for comp_id in order:
            if comp_id in self._mounted or comp_id not in self._nodes:
                continue
            node = self._nodes[comp_id]
            self._tokens += 1
            self._mounted[comp_id] = self._tokens
            self._parents[comp_id] = parents[comp_id]
            node["comp"]._mount(
                _FakeJs(_IndexedCalls(self, comp_id)),
                self._tokens,
                self._callbacks(comp_id, node),
            )

    def _callbacks(self, comp_id, node):
        def update_frontend(data, _ignore_result=False):
            self._apply(comp_id, data)

        def recorder(name):
            def call(*args, _ignore_result=False):
                self._js_call((comp_id, name, args))

            return call

        names = ["download", "add_keybinding", "remove_keybinding"]
        return [["update_frontend", update_frontend]] + [
            [name, recorder(name)] for name in names + node["methods"]
        ]


class _IndexedCalls:
    """Records the calls of a _FakeJs with the index of its component"""

    def __init__(self, frontend, index):
        self._frontend = frontend
        self._index = index

    def append(self, call):
        self._frontend._js_call((self._index, *call))


def mount(app) -> FakeFrontend:
    """Show the app (or a single component) in a :class:`FakeFrontend`: it
    replaces the frontend of the environment, mounts the components and
    records the update messages.

    >>> fe = mount(app)
    >>> fe.event(app.button, "click")
    >>> assert fe.props(app.label)["text"] == "clicked"
    >>> assert len(fe.messages) == 1
    """
    return FakeFrontend().mount(app)


def _stable_tree(root, allow) -> dict:
    """index -> (component, index of the parent, parent path, managed by a
    structural component) of the components of the tree outside the allowed
    subtrees, transparent components flattened"""
    from ngapp.components.basecomponent import Component
    from ngapp.components.reactive import _Structural

    def allowed(comp):
        for a in allow:
            if isinstance(a, str):
                if a and comp._id and (a == comp._id or a == comp._fullid):
                    return True
            elif a is comp:
                return True
        return False

    def name(comp):
        return f"{type(comp).__name__}#{comp._id}" if comp._id else type(
            comp
        ).__name__

    tree = {}

    def walk(comp, parent, path):
        managed = isinstance(comp, _Structural)
        for slot in comp.ui_slots.values():
            if not isinstance(slot, (list, tuple)):
                continue
            for child in slot:
                if not isinstance(child, Component) or allowed(child):
                    continue
                if child._transparent:
                    walk(child, parent, path)
                    continue
                if child._index not in tree:
                    tree[child._index] = (child, parent._index, path, managed)
                    walk(child, child, path + " > " + name(child))

    walk(root, root, name(root))
    return tree


@contextlib.contextmanager
def assert_stable(app, allow=()):
    """Fail with an AssertionError when the code in the block replaced
    components of the tree of app by new ones (a rebuild) instead of updating
    them. Components in the subtrees of allow (components or ids) and the
    content of Show, For and Dynamic are not checked; adding or removing
    components alone is fine.

    >>> with assert_stable(app):
    ...     fe.event(app.radius, "update:model-value", 2.0)
    """
    from ngapp.components import basecomponent

    allow = tuple(allow)
    before = _stable_tree(app, allow)
    sites = {}
    previous = basecomponent._slot_recorder

    def record(comp, key, old, value):
        site = basecomponent._caller_site()
        for child in value if isinstance(value, (list, tuple)) else (value,):
            if isinstance(child, basecomponent.Component):
                sites.setdefault(child._index, site)
        if previous is not None:
            previous(comp, key, old, value)

    basecomponent._slot_recorder = record
    try:
        yield
    finally:
        basecomponent._slot_recorder = previous
    after = _stable_tree(app, allow)

    def top(tree, other):
        """components missing in other whose parent is in both trees"""
        result = {}
        for index, (comp, parent, path, managed) in tree.items():
            if index in other or managed:
                continue
            if parent in other or parent == app._index:
                result.setdefault(parent, []).append((comp, path, index))
        return result

    removed = top(before, after)
    added = top(after, before)
    replaced = [p for p in added if p in removed]
    if not replaced:
        return
    lines = []
    for parent in replaced:
        old = ", ".join(type(c).__name__ for c, _, _ in removed[parent])
        for comp, path, index in added[parent]:
            lines.append(
                f"  {type(comp).__name__} (id {comp._id!r}) in {path}, "
                f"assigned at {sites.get(index, '<not recorded>')}"
            )
        lines.append(f"    replacing: {old}")
    raise AssertionError(
        "Components were recreated instead of updated (bind the changing "
        "values or use Show / For / Dynamic):\n" + "\n".join(lines)
    )
