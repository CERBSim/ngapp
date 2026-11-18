"""Transport of component updates to the browser (wire protocol 1): one
message per event, new components with their data, mount state"""

import logging
import math
import time

import pytest

import ngapp.components.basecomponent as bc
from ngapp import flush_updates, utils
from ngapp.app import App, AppConfig
from ngapp.components import Div, Label, QBtn, QDialog, QInput
from ngapp.observable import batch
from ngapp.test_utils import mount
from ngapp.utils import BrowserFrontend, EnvironmentType, set_environment


@pytest.fixture(autouse=True)
def env(monkeypatch):
    env = set_environment(EnvironmentType.STANDALONE, have_backend=False)
    env.frontend.update_component = lambda *a, **k: None
    monkeypatch.setattr(utils, "_BATCH_MAX_HOLD", 5)
    return env


def entries(message):
    return {e["compId"]: e["data"] for e in message}


def test_one_message_per_handler():
    label, button, box = Label("a"), QBtn("go"), Div()
    keep = Div("keep")
    root = Div(label, button, box)

    def click():
        label.text = "b"
        label.text = "c"
        box.ui_children = [Div("dropped")]
        new = QInput(ui_label="x")
        box.ui_children = [keep, new, "text"]
        new.ui_label = "y"
        button.ui_label = "done"
        button.ui_color = "red"

    button.on_click(click)
    fe = mount(root)
    assert fe.messages == []
    n = next(bc._component_counter)

    fe.event(button, "click.stop")
    assert len(fe.messages) == 1
    message = fe.messages[0]
    # first touched first, props merged, the last value wins
    assert [e["compId"] for e in message] == [
        label._index,
        box._index,
        button._index,
    ]
    data = entries(message)
    assert data[label._index]["props"] == {"text": "c"}
    assert data[label._index]["slots"] == {"default": [{"compId": "c"}]}
    assert data[button._index] == {"props": {"label": "done", "color": "red"}}
    # only the final child list, new components come with their data
    slot = data[box._index]["slots"]["default"]
    assert [c["compId"] for c in slot] == [keep._index, n + 2, "text"]
    assert slot[1]["init"]["type"] == "QInput"
    assert slot[1]["init"]["props"]["label"] == "y"
    assert slot[1]["init"]["protocol"] == 1
    assert slot[0]["init"]["slots"] == {"default": [{"compId": "keep"}]}
    # the component created and dropped in the handler was never sent
    assert n + 1 not in bc._frontend_known
    assert fe.dropped == []
    assert {keep._index, n + 2} <= fe.mounted
    assert fe.props(button)["label"] == "done"
    assert fe.children(box)[2] == "text"

    # a mounted child is sent as reference only
    box.ui_children = [keep]
    assert fe.messages[-1] == [
        {
            "compId": box._index,
            "data": {"slots": {"default": [{"compId": keep._index}]}},
        }
    ]
    assert n + 2 not in fe.mounted and not bc.get_component(n + 2)._mounted


def test_known_and_unknown_components():
    dialog_text = Label("closed")
    dialog = QDialog(dialog_text)
    root = Div(dialog)
    fe = mount(root)
    fe.unmount(dialog_text)
    assert not dialog_text._mounted and not dialog_text._frontend_known
    dialog_text.text = "not sent"
    assert fe.messages == []

    # known again once its parent sent it, also without an instance
    dialog.ui_children = [dialog_text]
    assert dialog_text._frontend_known and not dialog_text._mounted
    assert "init" in fe.messages[-1][0]["data"]["slots"]["default"][0]
    n = len(fe.messages)
    dialog_text.ui_class = "pending"
    assert len(fe.messages) == n + 1
    assert fe.props(dialog_text)["class"] == "pending"

    unknown = Label("x")
    unknown.text = "y"
    unknown.ui_children = ["z"]
    assert len(fe.messages) == n + 1


def test_mount_and_unmount():
    mounted = []
    child = Div("x")
    child.on_mounted(lambda: mounted.append("mounted"))
    child.on_unmount(lambda: mounted.append("unmount"))
    fe = mount(Div(child))
    assert mounted == ["mounted"]
    assert child._mounted and child._js_component is not None
    assert "update_frontend" in child._js_callbacks
    token = child._mount_token

    # the unmount of an earlier instance arrives after the next mount
    bc.unmount_component(child._index, token - 1)
    assert child._mounted and mounted == ["mounted"]

    fe.unmount(child)
    assert mounted == ["mounted", "unmount"]
    assert not child._mounted and not child._frontend_known
    assert child._js_component is None and child._js_callbacks == {}
    fe.mount(child)
    assert child._mounted and child._mount_token != token
    assert mounted == ["mounted", "unmount", "mounted"]

    # a new event of a known component reaches the browser
    child.on("click", lambda: None)
    assert fe.messages[-1] == [
        {"compId": child._index, "data": {"events": ["save", "click"]}}
    ]
    assert fe.events(child) == ["save", "click"]


def test_flush_order_and_hold(monkeypatch, env):
    button, label = QBtn("go"), Label("")
    button.on_click(lambda: click())
    fe = mount(Div(button, label))
    env.type = EnvironmentType.LOCAL_APP
    seen = []

    def click():
        label.text = "1"
        button.ui_click()  # a JS method: the pending updates go first
        seen.append((len(fe.messages), len(fe.calls)))
        label.text = "2"
        flush_updates()
        seen.append(len(fe.messages))
        label.text = "3"

    fe.event(button, "click.stop")
    assert seen == [(1, 1), 2]
    assert [c[:2] for c in fe.calls] == [(button._index, "click")]
    assert len(fe.messages) == 3

    # without a scope every update leaves at once, with NGAPP_BATCH_UPDATES=0
    # also inside one
    n = len(fe.messages)
    label.ui_class = "c4"
    assert len(fe.messages) == n + 1
    with batch():
        label.ui_class = "c5"
        assert len(fe.messages) == n + 1
        monkeypatch.setattr(utils, "_BATCH_UPDATES", False)
        label.ui_style = "color: red"
        assert len(fe.messages) == n + 2
        monkeypatch.setattr(utils, "_BATCH_UPDATES", True)

    # a long handler does not hide its progress
    monkeypatch.setattr(utils, "_BATCH_MAX_HOLD", 0.02)
    n = len(fe.messages)
    with batch():
        label.ui_class = "c6"
        assert len(fe.messages) == n
        time.sleep(0.2)  # the watchdog sends it
        assert len(fe.messages) == n + 1
        label.ui_class = "c7"
        assert len(fe.messages) == n + 1
    assert len(fe.messages) == n + 2

    # without watchdog (pyodide): the next update sends what waited too long
    monkeypatch.setattr(utils, "_watch", lambda: None)
    time.sleep(0.05)  # the watchdog is idle again
    with batch():
        label.ui_class = "c8"
        time.sleep(0.03)
        assert len(fe.messages) == n + 2
        label.ui_style = ""
        assert len(fe.messages) == n + 3
    assert fe.props(label)["class"] == "c8"


def test_nan_and_budget(monkeypatch):
    box = Div()
    fe = mount(Div(box))
    box._set_prop("data", {"a": [1.0, math.nan, {"b": math.inf}], "c": "NaN"})
    assert fe.messages[-1][0]["data"]["props"]["data"] == {
        "a": [1.0, None, {"b": None}],
        "c": "NaN",
    }
    big = [float(i) for i in range(100)] + [math.nan]
    assert utils._json_safe(big)[-1] is None and math.isnan(big[-1])
    ok = list(range(100))
    assert utils._json_safe(ok) is ok

    # more new components than fit in a message: the rest is pulled
    monkeypatch.setattr(utils, "_INLINE_MAX_COMPONENTS", 3)
    box.ui_children = [Div(Div(str(i))) for i in range(4)]
    slot = fe.messages[-1][0]["data"]["slots"]["default"]
    assert ["init" in c for c in slot] == [True, True, False, False]
    assert len(fe.children(box)) == 4
    assert all(c._mounted for c in fe.children(box))
    assert fe.children(fe.children(fe.children(box)[3])[0]) == ["3"]


def test_protocol_0():
    env = set_environment(EnvironmentType.STANDALONE, have_backend=False)
    env.frontend = BrowserFrontend(None)
    sent = []
    label, button = Label("a"), QBtn("go")
    root = Div(label, button)
    init = root._js_init()
    assert "protocol" not in init and "comp" not in init
    assert init["slots"]["default"] == [
        {"compId": label._index},
        {"compId": button._index},
    ]
    label.text = "dropped"
    for comp in (label, button):
        comp._set_js_callback(
            "update_frontend",
            lambda data, _ignore_result=False, i=comp._index: sent.append(
                (i, data)
            ),
        )
        comp._set_js_component(object())
    assert label._mounted and not label._frontend_known

    def click():
        label.text = "b"
        button.ui_label = "c"

    button.on_click(click)
    button._handle("click.stop")
    assert sent == [
        (
            label._index,
            {"slots": {"default": [{"compId": "b"}]}, "source": "frontend"},
        ),
        (label._index, {"props": {"text": "b"}, "source": "frontend"}),
        (button._index, {"props": {"label": "c"}, "source": "frontend"}),
    ]
    bc.unmount_component(label._index)
    assert label._js_component is None and not label._mounted
    label.text = "d"
    assert len(sent) == 3


class Slow(Div):
    def __init__(self, delay, *children):
        time.sleep(delay)
        super().__init__(*children)


class SlowApp(App):
    def __init__(self, delay=0.0):
        super().__init__()
        time.sleep(delay)
        self.component = Div(Slow(0.08), Div("x"))
        self.ids = [
            c._index for c in (self.component, *self.component.ui_children)
        ]


AppConfig(SlowApp, name="slow", version="1")


def test_slow_constructor_warning(monkeypatch, caplog):
    class Fast(Div):
        pass

    monkeypatch.setenv("NGAPP_SLOW_INIT", "0.05")
    bc._read_slow_init_limits()
    try:
        with caplog.at_level(logging.WARNING, logger="ngapp.components"):
            # the time of the children is not the time of the parent
            for _ in range(2):
                Fast(Slow(0.08), Fast(Slow(0.0)))
        messages = [r.getMessage() for r in caplog.records]
        assert len(messages) == 1  # once per class and creation site
        assert messages[0].startswith("Slow constructor: Slow took ")
        assert "limit 50 ms" in messages[0]
        assert f"created at {__file__}:" in messages[0]

        caplog.clear()
        monkeypatch.setenv("NGAPP_SLOW_INIT", "0")
        bc._read_slow_init_limits()
        with caplog.at_level(logging.WARNING, logger="ngapp.components"):
            Slow(0.08)
        assert not caplog.records

        # the app is measured in total
        monkeypatch.setenv("NGAPP_SLOW_APP_INIT", "0.05")
        bc._read_slow_init_limits()
        with caplog.at_level(logging.WARNING, logger="ngapp.components"):
            app = SlowApp()
        messages = [r.getMessage() for r in caplog.records]
        assert len(messages) == 1
        assert messages[0].startswith("Slow app constructor: SlowApp took 0.")
        assert "(limit 0.05 s), 4 components." in messages[0]
        assert mount(app).mounted == {app._index, *app.ids}

        # the own time of the app only counts against the app limit
        caplog.clear()
        monkeypatch.setenv("NGAPP_SLOW_INIT", "0.05")
        monkeypatch.setenv("NGAPP_SLOW_APP_INIT", "1")
        bc._read_slow_init_limits()
        with caplog.at_level(logging.WARNING, logger="ngapp.components"):
            SlowApp(0.08)
        assert all("SlowApp" not in r.getMessage() for r in caplog.records)
    finally:
        monkeypatch.undo()
        bc._read_slow_init_limits()
