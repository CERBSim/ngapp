"""Dependency tracking of the case state: computed values, state.ref and
structures follow a key whoever changes it (set, load, pull, job, restore)"""

import numpy as np
import pytest

from ngapp.app import App, AppConfig
from ngapp.components import Col, Div, QInput
from ngapp.components.basecomponent import Component
from ngapp.components.reactive import For
from ngapp.jobs import compute
from ngapp.observable import Reaction, batch, computed
from ngapp.state import CaseSession, bind_new_components
from ngapp.store.tree import flatten
from ngapp.utils import EnvironmentType, set_environment
from helpers import run_jobs


class Row(Component):
    def __init__(self, name):
        super().__init__("div", id=name, namespace=True)
        self.label = QInput(id="label", ui_model_value=name)
        self.ui_children = [self.label]

    @compute
    def solve(self):
        self.state.result = "solved " + self.state.get("input", "nothing")


class Panel(Component):
    def __init__(self):
        super().__init__("div", id="panel")
        self.freq = QInput(
            id="freq", ui_model_value=self.state.ref("freq", 50.0, float)
        )
        self.omega = computed(lambda: 2 * self.state.get("freq", 50.0))
        self.rows = For(lambda: list(self.state.get("rows", [])), Row)
        self.ui_children = [self.freq, self.rows]

    @compute
    def run(self):
        self.state.freq = 400.0


class ReactiveApp(App):
    autosave = True

    def __init__(self):
        super().__init__()
        self.panel = Panel()
        self.component = Col(self.panel)


AppConfig(ReactiveApp, name="reactive", version="1")


@pytest.fixture(autouse=True)
def env():
    env = set_environment(EnvironmentType.STANDALONE, have_backend=False)
    env.frontend.update_component = lambda *a, **k: None
    env.data_layer = True
    yield env
    env.data_layer = False


def create(server, sched):
    app = ReactiveApp()
    session = CaseSession.create(
        app, server.client("alice"), app_id=1, name="case", scheduler=sched
    )
    return app, session


def open_case(server, sched, case_id):
    app = ReactiveApp()
    session = CaseSession.open(
        app, server.client("alice"), case_id, scheduler=sched
    )
    return app, session


def test_computed_follows_local_changes():
    comp = Component("div", id="c")
    state = comp.state
    runs = []

    def summary():
        runs.append(1)
        return (
            state.get("a"),
            sorted(state.keys()),
            list(state.get("items", [])),
            state.ns("sub").get("x"),
        )

    c = computed(summary)
    assert c.value == (None, [], [], None)
    state.a = 1
    assert c.value == (1, ["a"], [], None)
    state.list("items").append("i")
    state.list("items").append("j")
    assert c.value == (1, ["a", "items"], ["i", "j"], None)
    state.ns("sub").set("x", 5)
    state.ns("other").set("x", 6)
    assert c.value == (1, ["a", "items"], ["i", "j"], 5)
    del state["a"]
    assert c.value == (None, ["items"], ["i", "j"], 5)
    n = len(runs)
    state.unrelated_key_is_a_key = 0
    state.ns("other").set("x", 7)
    state.ns("sub").set("x", 5)
    assert c.value[1] == ["items", "unrelated_key_is_a_key"]
    assert len(runs) == n + 1  # the key set only

    # a value changed in place is reported with notify
    state.data = {"n": 1}
    size = computed(lambda: state.data["n"])
    seen = []
    state.ref("data").on_change(lambda new, old: seen.append(new["n"]))
    assert size.value == 1
    state.data["n"] = 2
    assert size.value == 1 and seen == []
    state.notify("data")
    assert size.value == 2 and seen == [2]

    # numpy values and one run per batch
    state.mesh = np.zeros(3)
    n_points = computed(lambda: (runs.append(2), len(state.mesh))[1])
    seen.clear()
    n_points.on_change(lambda new, old: seen.append(new))
    with batch():
        state.mesh = np.zeros(4)
        state.mesh = np.zeros(5)
    assert seen == [5]


def test_ref_is_two_way():
    panel = Panel()
    ref = panel.state.ref("freq")
    assert ref is panel.state.observe("freq") and ref.value == 50.0
    assert "freq" not in panel.state
    seen = []
    ref.on_change(lambda new, old: seen.append((new, old)))
    panel.freq._handle("update:model-value", "60")
    assert panel.state.freq == 60.0 and panel.omega.value == 120.0
    panel.freq._handle("update:model-value", "6x")  # not a number: ignored
    assert panel.state.freq == 60.0
    panel.state.freq = 70.0
    assert panel.freq.ui_model_value == 70.0 and ref.value == 70.0
    assert seen == [(60.0, 50.0), (70.0, 60.0)]
    del panel.state["freq"]
    assert panel.freq.ui_model_value == 50.0


def test_state_of_a_case_notifies_from_every_source(server, sched):
    a, sa = create(server, sched)
    assert sa.status == "saved"
    a.panel.state.freq = 100.0
    sa.commit()

    b, sb = open_case(server, sched, sa.case_id)
    locked = []
    values = []

    def watch():
        locked.append(sb._lock._is_owned())
        values.append(b.panel.state.get("freq"))

    reaction = Reaction(watch)
    # load: the constructor saw an empty state
    assert b.panel.omega.value == 200.0
    assert b.panel.state.observe("freq").value == 100.0
    assert b.panel.freq.ui_model_value == 100.0
    # opening is no edit
    assert sb.status == "saved" and not sb._dirty
    sched.advance(10)
    assert sb.commit_count == 0 and sb.status == "saved"

    # pull of a revision of another tab
    a.panel.state.freq = 150.0
    sched.advance(10)
    assert b.panel.omega.value == 300.0
    assert b.panel.freq.ui_model_value == 150.0
    sched.advance(10)
    assert sb.status == "saved" and sb.commit_count == 0

    # conflict: the head replaces the local edit, restore brings it back
    a.panel.state.freq = 160.0
    sa.commit()
    b.panel.state.freq = 170.0
    sb.commit()
    assert b.panel.omega.value == 320.0 and len(sb.replaced) == 2
    sb.restore()
    assert b.panel.omega.value == 340.0
    assert b.panel.freq.ui_model_value == 170.0
    sb.commit()

    # discard of a local edit
    b.panel.state.freq = 180.0
    sb.discard()
    assert b.panel.omega.value == 340.0

    # result of a job merged into the case
    job = b.panel.run()
    run_jobs(server, ReactiveApp)
    sched.run_pending()
    assert job.status == "succeeded"
    assert b.panel.omega.value == 800.0
    assert b.panel.freq.ui_model_value == 400.0

    assert values == [100.0, 150.0, 170.0, 160.0, 170.0, 180.0, 170.0, 400.0]
    assert not any(locked)
    reaction.dispose()


def test_structure_follows_state_in_jobs(server, sched):
    """Rows built from a state list exist in a job (and are bound to their
    stored data) before the compute function addressed inside a row runs"""
    a, sa = create(server, sched)
    assert a.panel.rows.ui_children == []
    a.panel.state.rows = ["r1", "r2"]
    r1, r2 = a.panel.rows.ui_children
    r2.state.input = "two"
    r2.label.ui_model_value = "second"
    sa.commit()
    assert sa.status == "saved"

    b, sb = open_case(server, sched, sa.case_id)
    rows = b.panel.rows.ui_children
    assert [r._id for r in rows] == ["r1", "r2"]
    assert rows[1].state.input == "two"
    assert rows[1].label.ui_model_value == "second"
    assert sb.status == "saved" and not sb._dirty
    b.panel.state.rows = ["r2", "r3"]
    assert b.panel.rows.ui_children[0] is rows[1]
    assert not bind_new_components(b)  # bound when the rows changed
    sb.commit()

    job = rows[1].solve()
    run_jobs(server, ReactiveApp)
    sched.run_pending()
    assert job.status == "succeeded"
    assert rows[1].state.result == "solved two"
    data = flatten(sb.store.state(sb.case_id))
    assert data[("r2", "state", "result")] == "solved two"


def test_derived_props_and_bound_text_are_not_stored(server, sched):
    class Derived(ReactiveApp):
        def __init__(self):
            super().__init__()
            self.title = computed(lambda: f"f = {self.panel.state.get('freq')}")
            self.out = QInput(id="out", ui_label=self.title)
            self.text = Div(self.title, id="text")
            self.component = Col(self.panel, self.out, self.text)

    app = Derived()
    session = CaseSession.create(
        app, server.client("alice"), app_id=1, name="case", scheduler=sched
    )
    app.out._resolve_bindings()
    app.panel.state.freq = 1.0
    assert app.out.ui_label == "f = 1.0"
    session.commit()
    stored = flatten(session.store.state(session.case_id))
    assert ("out", "ui", "label") not in stored
    assert not any(p[0] == "text" for p in stored)
    sched.advance(10)
    assert session.status == "saved"
