"""An app in the reactive style (inputs bound to the case state, computed
labels, For / Show / Dynamic, an effect): one event gives one update batch in
the browser, and a compute job builds the structure but evaluates no derived
prop and runs no effect"""

import pytest

from ngapp.app import App, AppConfig
from ngapp.components import Col, Div, Dynamic, For, Label, QBtn, QInput, Show
from ngapp.components.basecomponent import Component
from ngapp.jobs import compute
from ngapp.observable import computed
from ngapp.state import CaseSession
from ngapp.test_utils import mount
from ngapp.utils import EnvironmentType, set_environment
from ngapp import utils
from helpers import run_jobs

LOG = {"volume": 0, "effect": 0}


class Study(Component):
    def __init__(self, name):
        super().__init__("div", id=name, namespace=True)
        self.ui_children = [Label(name)]

    @compute
    def solve(self):
        self.state.result = 2 * self.app.state.get("radius", 1.0)


class CylinderApp(App):
    def __init__(self):
        super().__init__()
        s = self.state

        def volume():
            LOG["volume"] += 1
            return 3.14 * s.get("radius", 1.0) ** 2 * s.get("height", 2.0)

        self.vol = computed(volume)
        self.warnings = computed(
            lambda: ["too flat"] if s.get("height", 2.0) < 1 else []
        )
        self.radius = QInput(ui_model_value=s.ref("radius", 1.0, float))
        self.height = QInput(ui_model_value=s.ref("height", 2.0, float))
        self.volume = Label(computed(lambda: f"V = {self.vol.value:.3g}"))
        self.plot = Div()

        def draw():
            LOG["effect"] += 1
            self.plot.ui_class = f"r{s.get('radius', 1.0)}"

        self.plot.effect(draw)
        self.studies = For(lambda: list(s.get("studies", [])), Study)
        self.component = Col(
            self.radius,
            self.height,
            self.volume,
            For(self.warnings, Label, otherwise=lambda: "no warnings"),
            Show(lambda: s.get("radius", 1.0) > 5, lambda: Label("large")),
            Dynamic(lambda: Label("tall") if s.get("height", 2.0) > 3 else ""),
            self.plot,
            self.studies,
            QBtn(ui_label="add").on_click(self.add_study),
        )

    def add_study(self):
        self.state.studies = list(self.state.get("studies", [])) + ["s1"]


AppConfig(CylinderApp, name="cylinder", version="1")


@pytest.fixture(autouse=True)
def env(monkeypatch):
    env = set_environment(EnvironmentType.STANDALONE, have_backend=False)
    env.frontend.update_component = lambda *a, **k: None
    env.data_layer = True
    monkeypatch.setattr(utils, "_BATCH_MAX_HOLD", 5)
    LOG.update(volume=0, effect=0)
    yield env
    env.data_layer = False


def tree(comp, out=None):
    out = [] if out is None else out
    out.append(comp)
    for slot in comp.ui_slots.values():
        if isinstance(slot, list):
            for c in slot:
                if isinstance(c, Component):
                    tree(c, out)
    return out


def test_one_event_one_batch(server, sched):
    app = CylinderApp()
    CaseSession.create(
        app, server.client("alice"), app_id=1, name="c", scheduler=sched
    )
    assert LOG == {"volume": 0, "effect": 0}
    fe = mount(app)
    assert LOG == {"volume": 1, "effect": 1}
    fe.messages.clear()
    before = tree(app)

    fe.event(app.radius, "update:model-value", "6")
    assert len(fe.messages) == 1
    assert app.state.radius == 6.0
    assert LOG == {"volume": 2, "effect": 2}
    assert fe.props(app.plot)["class"] == "r6.0"
    # only the Show branch is new, everything else is the same object
    after = tree(app)
    new = [c for c in after if c not in before]
    assert {type(c).__name__ for c in new} <= {"Label", "Span", "Text"}
    assert all(c in after for c in before)

    fe.event(app.height, "update:model-value", "0.5")
    assert len(fe.messages) == 2
    labels = [c for c in fe.children(app.component) if isinstance(c, Label)]
    assert "too flat" in [c.text for c in labels]


def test_job_builds_structure_without_browser_work(server, sched):
    app = CylinderApp()
    session = CaseSession.create(
        app, server.client("alice"), app_id=1, name="c", scheduler=sched
    )
    app.state.radius = 3.0
    app.state.studies = ["s1"]
    session.commit()
    study = app.studies.ui_children[0]
    job = study.solve()

    LOG.update(volume=0, effect=0)
    run_jobs(server, CylinderApp)
    sched.run_pending()
    assert job.status == "succeeded"
    assert study.state.result == 6.0
    # the job process built the app (and the study row) but nothing derived
    assert LOG == {"volume": 0, "effect": 0}
