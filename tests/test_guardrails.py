"""Dev warnings for rebuilding apps and the assert_stable test helper"""

import logging

import pytest

import ngapp.components.basecomponent as bc
from ngapp import utils
from ngapp.components import Div, For, Label, QBtn, Show, creating_ui
from ngapp.observable import Observable, computed
from ngapp.test_utils import assert_stable, mount
from ngapp.utils import EnvironmentType, set_environment


@pytest.fixture(autouse=True)
def env(monkeypatch):
    env = set_environment(EnvironmentType.STANDALONE, have_backend=False)
    env.frontend.update_component = lambda *a, **k: None
    monkeypatch.setattr(utils, "_BATCH_MAX_HOLD", 5)
    monkeypatch.setattr(bc, "_dev_reported", set())
    monkeypatch.delenv("NGAPP_DEV_WARNINGS", raising=False)
    return env


def rebuilding_app(n=1):
    panel = Div(Label("start"))
    btn = QBtn(ui_label="go")

    def on_click():
        panel.ui_children = [Label(str(i)) for i in range(n)]

    btn.on("click", on_click)
    return Div(btn, panel), btn, panel


def dev_warnings(caplog):
    return [
        r.getMessage()
        for r in caplog.records
        if r.name == "ngapp.components" and r.levelno == logging.WARNING
    ]


def test_rebuild_warning(caplog):
    caplog.set_level(logging.WARNING, "ngapp.components")
    root, btn, panel = rebuilding_app()
    fe = mount(root)
    for _ in range(3):
        fe.event(btn, "click")
    assert dev_warnings(caplog) == []
    for _ in range(3):
        fe.event(btn, "click")
    (msg,) = dev_warnings(caplog)
    assert msg.startswith("Div.ui_children replaced 4 times within 2 s")
    assert "Show / For / Dynamic" in msg and __file__ in msg

    # updates of a structural component do not count
    caplog.clear()
    items = Observable([1])
    rows = Div(For(items, lambda i: Label(str(i)), key=lambda i: 0))
    mount(rows)
    for i in range(6):
        items.value = [i + 2]
    assert dev_warnings(caplog) == []


def test_handler_warning(caplog):
    caplog.set_level(logging.WARNING, "ngapp.components")
    root, btn, panel = rebuilding_app(150)
    fe = mount(root)
    fe.event(btn, "click")
    fe.event(btn, "click")
    (msg,) = dev_warnings(caplog)
    assert msg.startswith("Handler of QBtn 'click' created 150 components")
    assert __file__ in msg

    # lifecycle events are excluded
    caplog.clear()
    big = Div()
    big.on_mounted(lambda: big._set_slot("default", [Div() for _ in range(150)]))
    mount(big)
    assert dev_warnings(caplog) == []


def test_handler_warning_allows_intended_ui(caplog):
    caplog.set_level(logging.WARNING, "ngapp.components")
    shown = Observable(False, "shown")
    lazy = QBtn(ui_label="open")
    lazy.on("click", lambda: shown.toggle())
    opened = Div()
    tab = QBtn(ui_label="tab")

    def open_tab():
        with creating_ui():
            opened.ui_children = [Label(str(i)) for i in range(150)]

    tab.on("click", open_tab)
    root = Div(lazy, Show(shown, lambda: [Label(str(i)) for i in range(150)]), tab, opened)
    fe = mount(root)
    fe.event(lazy, "click")
    fe.event(tab, "click")
    assert dev_warnings(caplog) == []


@pytest.mark.parametrize("off", ["switch", "compute"])
def test_no_dev_warnings(caplog, monkeypatch, env, off):
    caplog.set_level(logging.WARNING, "ngapp.components")
    if off == "switch":
        monkeypatch.setenv("NGAPP_DEV_WARNINGS", "0")
    else:
        monkeypatch.setattr(env, "type", EnvironmentType.COMPUTE)
    root, btn, panel = rebuilding_app(150)
    for _ in range(5):
        btn._handle("click")
    assert dev_warnings(caplog) == []


def test_assert_stable():
    value = Observable(1)
    label = QBtn(ui_label=computed(lambda: f"value {value.value}"))
    root, btn, panel = rebuilding_app()
    root.ui_children = [*root.ui_children, label]
    fe = mount(root)

    with assert_stable(root):
        value.value = 2
        panel.ui_children = [*panel.ui_children, Label("added")]
    assert fe.props(label)["label"] == "value 2"
    with assert_stable(root, allow=[panel]):
        fe.event(btn, "click")

    with pytest.raises(AssertionError) as info:
        with assert_stable(root):
            fe.event(btn, "click")
    msg = str(info.value)
    assert "Label (id '') in Div > Div" in msg
    assert f"{__file__}:" in msg and "replacing: Label" in msg
