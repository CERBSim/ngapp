"""State API, UI prop persistence and the commit flow of ngapp on the
SQLite store; two app instances on one store act as two browser tabs"""

import copy
import datetime
import itertools
import logging
import pickle

import numpy as np
import pytest

from ngapp.app import App, AppConfig
from ngapp.components import Col, Div, Label, QInput, QTable
from ngapp.components.basecomponent import Component
from ngapp.observable import bind
from ngapp.state import (
    CaseSession,
    State,
    ValueReadError,
)
from ngapp.store import (
    CaseDeletedError,
    ConflictError,
    JobRequest,
    Op,
    ReleaseTooOldError,
)
from ngapp.store.tree import CASE_NAME, flatten
from ngapp.utils import EnvironmentType, set_environment
from helpers import revision_count


class Mesher(Component):
    label = "Max h"

    def __init__(self):
        super().__init__("div", id="mesher")
        self.maxh = QInput(id="maxh", ui_model_value=0.1, ui_label=self.label)
        self.ui_children = [self.maxh]
        self.state.mesh = None


class DemoApp(App):
    mesher_class = Mesher

    def __init__(self):
        super().__init__()
        self.mesher = self.mesher_class()
        self.label = Label("waiting", id="label")
        self.table = QTable(
            id="table",
            ui_rows=[{"a": 1}, {"a": 2}],
            ui_columns=[{"name": "a", "label": "A", "field": "a"}],
            ui_row_key="a",
            ui_selected=[],
        )
        self.plain = QInput(ui_model_value="no id")
        self.loads = 0
        self.on_load(self._count_load)
        self.component = Col(self.mesher, self.label, self.table, self.plain)

    def _count_load(self):
        self.loads += 1


AppConfig(DemoApp, name="demo", version="1")


class Spy:
    def __init__(self, store):
        self.store = store
        self.reads = 0
        self.commits = 0
        self.conflicts = 0

    def __getattr__(self, name):
        return getattr(self.store, name)

    def read_blob(self, *args, **kwargs):
        self.reads += 1
        return self.store.read_blob(*args, **kwargs)

    def commit(self, *args, **kwargs):
        self.commits += 1
        try:
            return self.store.commit(*args, **kwargs)
        except ConflictError:
            self.conflicts += 1
            raise


class Custom:
    def __init__(self, x):
        self.x = x


@pytest.fixture(autouse=True)
def env():
    env = set_environment(EnvironmentType.STANDALONE, have_backend=False)
    env.frontend.update_component = lambda *a, **k: None
    env.data_layer = True
    yield env
    env.data_layer = False


def create(
    server, sched, cls=DemoApp, user="alice", release_id=None, **options
):
    app = cls()
    store = Spy(server.client(user, release_id=release_id))
    session = CaseSession.create(
        app, store, app_id=1, name="case", scheduler=sched, **options
    )
    return app, session


def open_case(
    server,
    sched,
    case_id,
    cls=DemoApp,
    user="alice",
    release_id=None,
    **options,
):
    app = cls()
    store = Spy(server.client(user, release_id=release_id))
    session = CaseSession.open(app, store, case_id, scheduler=sched, **options)
    return app, session


def stored(session, revision=None):
    return flatten(session.store.state(session.case_id, revision))


def n_revisions(server, session):
    return revision_count(server, session.case_id)


def test_state_api(sched, server):
    app = DemoApp()
    st = app.mesher.state
    assert isinstance(st, State) and app.mesher.state is st
    st.x = 1
    st.set("keys", "a key named like a method")
    assert st.x == 1 and st.get("x") == 1 and st.get("y", 5) == 5
    assert "x" in st and "y" not in st
    assert sorted(st.keys()) == ["keys", "mesh", "x"]
    assert st.get("keys") == "a key named like a method"
    with pytest.raises(AttributeError):
        st.y
    with pytest.raises(AttributeError):
        st.keys = 1
    with pytest.raises(AttributeError):
        st._private = 1
    del st.x
    assert "x" not in st
    with pytest.raises(AttributeError):
        del st.x
    with pytest.raises(KeyError):
        st.set("a/b", 1)
    # identity rule: the first state write of a component without id raises
    with pytest.raises(RuntimeError, match="needs an id"):
        Div().state.x = 1
    with pytest.raises(RuntimeError, match="needs an id"):
        Div().state.list("x").append(1)
    # library namespaces
    materials = app.state.ns("materials")
    materials.steel = {"E": 210e9}
    app.state.steel = "other"
    assert materials.keys() == ["steel"] and app.state.keys() == ["steel"]
    assert materials.steel == {"E": 210e9} and app.state.steel == "other"
    assert materials.ns("sub").keys() == []
    # App.state and Component.app
    assert app.mesher.app is app and app.app is app
    _, session = (
        app,
        CaseSession.create(
            app, server.client("alice"), app_id=1, scheduler=sched
        ),
    )
    base = stored(session)
    assert base[("__app__", "state", "materials/steel")] == {"E": 210e9}
    assert base[("__app__", "state", "steel")] == "other"
    assert base[("mesher", "state", "mesh")] is None


def test_state_as_dict():
    """A State is used like a dict; assigning a dict replaces its values"""
    app = DemoApp()
    st = app.state
    app.state = {"U": 110.0, "curves": {"core": [1, 2]}, "items": "a key"}
    assert app.state is st and len(st) == 3
    assert st["U"] == 110.0 and st.get("V") is None
    assert "V" not in st and 5 not in st and "a/b" not in st
    assert sorted(st) == ["U", "curves", "items"]
    assert st == {"U": 110.0, "curves": {"core": [1, 2]}, "items": "a key"}
    assert "{U:g} kV".format(**st) == "110 kV"
    with pytest.raises(KeyError):
        st["V"]
    st.update(V=1, W=2)
    assert st.pop("W") == 2 and st.setdefault("V", 5) == 1
    del st["V"]
    st.list("log").append("x")
    assert st["log"] == ["x"]
    copied = st.copy()
    assert type(copied) is dict and type(copied["log"]) is list
    for c in (copy.copy(st), copy.deepcopy(st), pickle.loads(pickle.dumps(st))):
        assert type(c) is dict and c == copied
    assert copy.deepcopy(st)["curves"] is not st["curves"]
    # assigning replaces the values, also those of another State
    app.state = {"U": 220.0}
    assert dict(app.state) == {"U": 220.0} and app.state is st
    other = DemoApp()
    other.state = st
    assert dict(other.state) == {"U": 220.0}
    # without an id or for other values the attribute is the app's own
    div = Div()
    div.state = {"a": 1}
    assert type(div.state) is dict
    app.mesher.state = "own value"
    assert app.mesher.state == "own value"
    app.mesher.state = {"mesh": None}
    assert isinstance(app.mesher.state, State)


def test_state_dict_is_stored_per_key(server, sched):
    """Every key of a state used like a dict is a value of the case: changes
    of other writers are merged per key, a value changed in place is stored by
    the next commit"""
    a, sa = create(server, sched)
    a.state = {"U": 110.0, "curves": {"core": [1, 2]}}
    a.commit()
    b, sb = open_case(server, sched, sa.case_id)
    assert b.state == {"U": 110.0, "curves": {"core": [1, 2]}}
    seen = []
    a.state.on_change(seen.append)
    b.state["U"] = 220.0
    sb.commit()
    a.state["curves"]["core"].append(3)
    a.commit()
    sched.advance(30)
    assert a.state["U"] == 220.0 and {"U"} in seen
    base = stored(sa)
    assert base[("__app__", "state", "U")] == 220.0
    assert base[("__app__", "state", "curves")] == {"core": [1, 2, 3]}


def test_pickle_only_on_request(server, sched):
    a, sa = create(server, sched)
    with pytest.raises(TypeError, match="pickle=True"):
        a.mesher.state.obj = Custom(1)
    a.mesher.state.set("obj", Custom(1), pickle=True)
    assert a.mesher.state.obj.x == 1


def test_assign_to_change(server, sched):
    a, sa = create(server, sched)
    st = a.mesher.state
    st.rows = [1, 2]
    st.big = np.zeros(100000)
    a.commit()
    rev = sa.base_revision
    # no-op writes by hash do not commit
    st.rows = [1, 2]
    st.big = np.zeros(100000)
    a.mesher.maxh.ui_model_value = 0.1
    assert a.commit() == rev
    # in-place mutation of small values is detected at commit
    st.rows.append(3)
    rev2 = a.commit()
    assert rev2 != rev and stored(sa)[("mesher", "state", "rows")] == [1, 2, 3]
    # large values are read-only, in-place mutation raises instead of being lost
    with pytest.raises(ValueError):
        st.big[0] = 1
    arr = st.big.copy()
    arr[0] = 1
    st.big = arr
    assert a.commit() != rev2


def test_ui_prop_rules(server, sched):
    a, sa = create(server, sched)
    base = stored(sa)
    # two-way props are always stored, also with the constructor's value
    assert base[("maxh", "input", "model-value")] == 0.1
    assert base[("table", "input", "selected")] == []
    # one-way props and text slots only when they differ from the constructor
    assert not any(p[1] in ("ui", "slots") for p in base)
    # components without id are not stored
    assert not any("no id" == v for v in base.values())
    assert base[CASE_NAME] == "case"

    a.mesher.maxh.ui_label = "Mesh size"
    a.label.text = "done"
    a.commit()
    base = stored(sa)
    assert base[("maxh", "ui", "label")] == "Mesh size"
    assert base[("label", "ui", "text")] == "done"
    assert base[("label", "slots", "default")] == ["done"]
    assert not any(p[0] in ("mesher",) and p[1] == "slots" for p in base)

    # reverting to the constructor's value removes the stored prop
    a.mesher.maxh.ui_label = Mesher.label
    ops = sa._collect()[0]
    assert [(o.op, o.path) for o in ops] == [
        ("delete", ("maxh", "ui", "label"))
    ]
    a.commit()
    assert ("maxh", "ui", "label") not in stored(sa)

    b, sb = open_case(server, sched, sa.case_id)
    assert b.label.text == "done" and b.label.ui_children == ["done"]
    assert b.mesher.maxh.ui_label == Mesher.label


def test_two_way_props_from_generator(server, sched):
    assert QTable._two_way_props == (
        "expanded",
        "fullscreen",
        "pagination",
        "selected",
    )
    assert QInput._two_way_props == ("model-value",)
    a, sa = create(server, sched)
    # back-sync of update:selected as sent by the browser
    a.table._handle("update:selected", [{"a": 2}])
    assert a.table.ui_selected == [{"a": 2}]
    a.table._handle("update:pagination", {"rowsPerPage": 5})
    assert a.table.ui_pagination == {"rowsPerPage": 5}
    sched.advance(10)
    base = stored(sa)
    assert base[("table", "input", "selected")] == [{"a": 2}]
    assert base[("table", "input", "pagination")] == {"rowsPerPage": 5}
    b, sb = open_case(server, sched, sa.case_id)
    assert b.table.ui_selected == [{"a": 2}]


def test_untouched_props_follow_app_updates(server, sched):
    a, sa = create(server, sched)

    class Mesher2(Mesher):
        label = "Element size"

    class DemoApp2(DemoApp):
        mesher_class = Mesher2

        def __init__(self):
            super().__init__()
            self.mesher.maxh.ui_model_value = 0.5

    b, sb = open_case(server, sched, sa.case_id, cls=DemoApp2)
    # the new label of the app version, the input of the case
    assert b.mesher.maxh.ui_label == "Element size"
    assert b.mesher.maxh.ui_model_value == 0.1


def test_observe(server, sched):
    a, sa = create(server, sched)
    obs = a.mesher.state.observe("level")
    assert obs.value is None
    obs.value = 3
    assert a.mesher.state.level == 3
    a.mesher.state.level = 4
    assert obs.value == 4
    widget = QInput(ui_model_value=4)
    bind(obs, widget)
    widget._handle("update:model-value", 5)
    assert a.mesher.state.level == 5
    sched.advance(10)
    b, sb = open_case(server, sched, sa.case_id)
    bobs = b.mesher.state.observe("level")
    assert bobs.value == 5
    a.mesher.state.level = 6
    sched.advance(10)
    assert bobs.value == 6


def test_conflict_on_pull_of_same_path(server, sched):
    a, sa = create(server, sched)
    b, sb = open_case(server, sched, sa.case_id)
    a.mesher.state.mesh = "a"
    sched.advance(0.5)
    b.mesher.state.mesh = "b"
    sched.advance(30)
    assert b.mesher.state.mesh == "a"
    assert [e.path for e in sb.replaced] == [("mesher", "state", "mesh")]
    assert sb.store.conflicts == 0


def test_deterministic_callbacks_converge(server, sched):
    """Derived values written by change callbacks in two tabs"""
    a, sa = create(server, sched)
    b, sb = open_case(server, sched, sa.case_id)
    for app in (a, b):
        st = app.mesher.state

        def derive(keys, st=st):
            if "x" in st:
                st.y = 2 * st.x

        st.on_change(derive)
    a.mesher.state.x = 3
    revs = n_revisions(server, sa)
    sched.advance(600)
    assert a.mesher.state.y == b.mesher.state.y == 6
    assert n_revisions(server, sa) - revs <= 2
    assert sa.echo_warnings == sb.echo_warnings == 0


def test_nondeterministic_callbacks_are_rate_limited(server, sched, caplog):
    a, sa = create(server, sched)
    b, sb = open_case(server, sched, sa.case_id)
    counter = itertools.count()
    for app in (a, b):
        st = app.mesher.state
        st.on_change(lambda keys, st=st: st.set("z", next(counter)))
    a.mesher.state.z = -1
    revs = n_revisions(server, sa)
    with caplog.at_level(logging.WARNING, logger="ngapp.state"):
        sched.advance(600)
    commits = n_revisions(server, sa) - revs
    # without the limit this loop commits about once per second
    assert 10 < commits < 60
    assert sa.echo_warnings >= 1 and sb.echo_warnings >= 1
    assert "caused by change callbacks" in caplog.text


def test_save_hook_exception_keeps_edits_pending(server, sched):
    """No partial commit, edits stay pending, the error is visible"""
    a, sa = create(server, sched)
    errors = []
    sa.on_error(errors.append)
    fail = [True]

    def hook():
        if fail[0]:
            raise RuntimeError("hook failed")

    a.label.on_before_save(hook)
    revs = n_revisions(server, sa)
    a.mesher.maxh.ui_model_value = 0.7
    a.mesher.state.mesh = "new"
    sched.advance(30)
    assert n_revisions(server, sa) == revs
    assert isinstance(sa.last_error, RuntimeError) and errors
    assert ("maxh", "input", "model-value") in [
        o.path for o in sa._collect()[0]
    ]
    with pytest.raises(RuntimeError):
        a.commit()
    fail[0] = False
    sched.advance(120)
    assert n_revisions(server, sa) == revs + 1
    base = stored(sa)
    assert base[("maxh", "input", "model-value")] == 0.7
    assert base[("mesher", "state", "mesh")] == "new"
    assert sa.last_error is None


def test_encoding_error_aborts_commit(server, sched):
    a, sa = create(server, sched)
    a.mesher.state["items"] = [1]
    a.commit()
    revs = n_revisions(server, sa)
    a.mesher.maxh.ui_model_value = 0.9
    a.mesher.state["items"].append(Custom(1))
    with pytest.raises(TypeError):
        a.commit()
    sched.advance(30)
    assert n_revisions(server, sa) == revs
    a.mesher.state["items"].pop()
    a.mesher.state["items"].append(2)
    sched.advance(120)
    base = stored(sa)
    assert base[("mesher", "state", "items")] == [1, 2]
    assert base[("maxh", "input", "model-value")] == 0.9


def test_autosave_debounce_and_coalescing(server, sched):
    a, sa = create(server, sched)
    revs = n_revisions(server, sa)
    for i in range(20):
        a.mesher.state.x = i
        sched.advance(0.1)
    sched.advance(10)
    assert n_revisions(server, sa) == revs + 1
    # continuous edits are committed at least every autosave_max_delay
    for i in range(100):
        a.mesher.state.x = 100 + i
        sched.advance(0.2)
    sched.advance(10)
    assert 4 <= n_revisions(server, sa) - revs - 1 <= 6
    a.autosave = False
    a.mesher.state.x = -1
    sched.advance(10)
    assert stored(sa)[("mesher", "state", "x")] == 199


def test_save_hook_changes_are_committed_without_new_timer(server, sched):
    a, sa = create(server, sched)
    a.label.on_before_save(lambda: setattr(a.label, "text", "saved"))
    a.mesher.state.x = 1
    sched.advance(30)
    assert stored(sa)[("label", "ui", "text")] == "saved"
    assert sa._timer is None and sched._queue == []


def test_submit_commits_pending_edits_first(server, sched):
    """An edit followed by Run is in the job's input"""
    a, sa = create(server, sched)
    a.mesher.maxh.ui_model_value = 0.01
    job = sa.submit(
        JobRequest({"component": ["mesher"], "method": "generate"}, 0)
    )
    assert job.input_revision == sa.base_revision
    assert (
        stored(sa, job.input_revision)[("maxh", "input", "model-value")] == 0.01
    )


def test_storage_compatibility(server, sched):
    a, sa = create(server, sched)
    b, sb = open_case(server, sched, sa.case_id)
    storage = a.mesher.storage
    storage.set("meta", {"x": 1})
    storage.set("date", {"d": datetime.date(2020, 1, 2)})
    storage.set("obj", Custom(3), use_pickle=True)
    storage.append("results", {"step": 0})
    storage.append("results", {"step": 1})
    assert storage.get("meta") == {"x": 1} and "meta" in storage
    assert storage.get("date") == {"d": "2020-01-02"}
    assert storage.get("obj").x == 3
    assert storage.list_len("results") == 2
    assert storage.get_list("results", 1) == [{"step": 1}]
    assert storage.get("results#0") == {"step": 0}
    # the storage values are in a namespace of the state, not its keys
    assert "meta" not in a.mesher.state and a.mesher.state.keys() == ["mesh"]
    assert a.mesher.state.ns("storage").meta == {"x": 1}
    storage.save()
    storage.publish()
    changed = []
    b.mesher.storage.on_change(changed.append)
    sched.advance(30)
    assert b.mesher.storage.get_list("results") == [{"step": 0}, {"step": 1}]
    assert set().union(*changed) >= {
        "meta",
        "results",
        "results#0",
        "results#1",
    }
    storage.append("results", {"step": 2})
    storage.delete("meta")
    sched.advance(30)
    assert "results#2" in changed[-1] and "meta" in changed[-1]
    assert (
        "meta" not in b.mesher.storage and b.mesher.storage.get("meta") is None
    )


def test_dynamic_components_are_bound(server, sched):
    a, sa = create(server, sched)
    extra = QInput(id="extra", ui_model_value=1)
    a.label.ui_children = ["text", extra]
    a.commit()
    extra.ui_model_value = 2
    a.commit()
    b, sb = open_case(server, sched, sa.case_id)
    late = QInput(id="extra", ui_model_value=1)
    b.label.ui_children = ["text", late]
    b.commit()
    assert late.ui_model_value == 2
    sa.delete_component(extra)
    a.commit()
    assert not any(p[0] == "extra" for p in stored(sa))


def test_large_array_artifact_through_store(server, sched):
    a, sa = create(server, sched)
    array = np.zeros(33 * 1024 * 1024 // 8)
    array[::4096] = 1.0
    a.mesher.state.field = array
    a.commit()
    value = stored(sa)[("mesher", "state", "field")]
    assert value["$artifact"] == "ngapp.array/1"
    b, sb = open_case(server, sched, sa.case_id)
    back = b.mesher.state.field
    assert sb.store.reads == len(value["chunks"])
    np.testing.assert_array_equal(back, array)
    assert not back.flags.writeable and not array.flags.writeable


def test_case_deleted_blocks_autosave(server, sched):
    a, sa = create(server, sched)
    server.delete_case(sa.case_id)
    a.mesher.state.x = 1
    sched.advance(30)
    assert sa.blocked == "case_deleted" and isinstance(
        sa.last_error, CaseDeletedError
    )


def test_release_too_old(server, sched):
    a, sa = create(server, sched, release_id=2)
    b, sb = open_case(server, sched, sa.case_id, release_id=1)
    b.mesher.state.x = 1
    sched.advance(30)
    assert sb.blocked == "release_too_old"
    assert isinstance(sb.last_error, ReleaseTooOldError)
    assert "x" not in a.mesher.state


def test_remote_component_delete_and_case_name(server, sched):
    a, sa = create(server, sched)
    b, sb = open_case(server, sched, sa.case_id)
    a.name = "renamed"
    a.mesher.state.x = 1
    sched.advance(30)
    assert (
        b.name == "renamed"
        and server.client("alice").case(sa.case_id).name == "renamed"
    )
    store = server.client("alice")
    store.commit(sa.case_id, sb.base_revision, [Op("delete", ("mesher",))])
    sched.advance(30)
    assert "x" not in b.mesher.state


def test_unreadable_value_is_reported_and_does_not_block_others(server, sched):
    a, sa = create(server, sched)
    a.mesher.state.big = b"x" * 100_000
    a.mesher.state.small = 1
    a.commit()
    b, sb = open_case(server, sched, sa.case_id)
    errors, seen = [], []
    sb.on_read_error(errors.append)
    big_hash = None

    def read_blob(case_id, ref, *args, **kwargs):
        if ref.hash == big_hash:
            raise ModuleNotFoundError("No module named 'zstandard'")
        return sb.store.store.read_blob(case_id, ref, *args, **kwargs)

    sb.store.read_blob = read_blob
    obs_big = b.mesher.state.observe("big")
    obs_small = b.mesher.state.observe("small")
    b.mesher.state.on_change(lambda keys: seen.append(b.mesher.state.big))
    b.mesher.state.on_change(lambda keys: seen.append(b.mesher.state.small))
    a.mesher.state.big = b"y" * 100_000
    a.mesher.state.small = 2
    a.commit()
    big_hash = stored(sa)[("mesher", "state", "big")]["$blob"]
    sb.pull()
    assert obs_small.value == 2 and obs_big.value is None
    assert seen == [2]
    assert [e.path for e in errors] == [("mesher", "state", "big")]
    assert "zstandard" in str(errors[0]) and "mesher/state/big" in str(
        errors[0]
    )
    with pytest.raises(ValueReadError):
        b.mesher.state.big
    assert len(errors) == 1
