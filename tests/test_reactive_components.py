"""Components that follow observables: bound props and texts, Show, For,
Dynamic and effects, as a browser (fake frontend) and a job see them"""

import logging

import pytest

import ngapp.components.basecomponent as bc
from ngapp import utils
from ngapp.components import (
    Div,
    Dynamic,
    For,
    Fragment,
    Label,
    QBtn,
    QInput,
    Row,
    Show,
)
from ngapp.observable import Observable, batch, computed
from ngapp.test_utils import mount
from ngapp.utils import EnvironmentType, set_environment


@pytest.fixture(autouse=True)
def env(monkeypatch):
    env = set_environment(EnvironmentType.STANDALONE, have_backend=False)
    env.frontend.update_component = lambda *a, **k: None
    monkeypatch.setattr(utils, "_BATCH_MAX_HOLD", 5)
    return env


def entries(message):
    return {e["compId"]: e["data"] for e in message}


def test_computed_prop_is_lazy_and_updates_in_one_batch():
    calls = []
    a, b = Observable(1), Observable(2)

    def total():
        calls.append(1)
        return a.value + b.value

    total = computed(total)
    btn = QBtn(ui_label=computed(lambda: f"sum {total.value}"), id="btn")
    other = QBtn(
        ui_color=computed(lambda: "red" if total.value > 5 else "blue")
    )
    root = Div(btn, other)
    # not evaluated by the constructor, not part of the stored data
    assert calls == [] and "label" not in btn._props
    assert btn._derived_props == {"label"}
    assert "label" not in btn._dump()

    fe = mount(root)
    assert calls == [1]
    assert fe.props(btn)["label"] == "sum 3"
    assert fe.props(other)["color"] == "blue"
    assert fe.messages == []

    with batch():
        a.value = 5
        b.value = 6
    assert len(calls) == 2 and len(fe.messages) == 1
    assert entries(fe.messages[0]) == {
        btn._index: {"props": {"label": "sum 11"}},
        other._index: {"props": {"color": "red"}},
    }
    # derived props survive a load and stay out of the dump
    btn._load({"color": "green"})
    assert btn._props == {"color": "green", "label": "sum 11"}
    assert btn._dump() == {"color": "green"}

    # no browser shows it: not evaluated, until it is shown again
    fe.unmount(root)
    a.value = 7
    assert len(calls) == 2
    fe.mount(root)
    assert len(calls) == 3 and fe.props(btn)["label"] == "sum 13"


def test_plain_write_removes_computed_binding_only(caplog):
    text = Observable("a")
    derived = QBtn(ui_label=computed(lambda: text.value + "!"))
    plain = QBtn(ui_label=text)
    fe = mount(Div(derived, plain))
    assert plain.ui_label == "a" and fe.props(derived)["label"] == "a!"

    with caplog.at_level(logging.WARNING, logger="ngapp.components"):
        derived.ui_label = "fixed"
        plain.ui_label = "fixed"
    assert [r.getMessage() for r in caplog.records] == [
        "QBtn.label bound to a computed was overwritten with a plain value: "
        "the binding is removed."
    ]
    assert derived._derived_props == set()
    text.value = "b"
    assert fe.props(derived)["label"] == "fixed"
    assert fe.props(plain)["label"] == "b"


def test_no_echo_of_browser_values():
    value = Observable(1.0, converter=float)
    name = computed(lambda: f"v{value.value:g}")
    bound, free, derived = (
        QInput(ui_model_value=value),
        QInput(ui_model_value="x"),
        QInput(ui_model_value=name),
    )
    fe = mount(Div(bound, free, derived))

    fe.event(free, "update:model-value", "xy")
    assert free.ui_model_value == "xy" and fe.messages == []
    # the converted value is what the browser shows: the text stays
    fe.event(bound, "update:model-value", "3.")
    assert value.value == 3.0 and bound.ui_model_value == "3."
    # the other input of the computed changed, nothing came back
    assert entries(fe.messages.pop()) == {
        derived._index: {"props": {"model-value": "v3"}}
    }
    fe.event(bound, "update:model-value", "")
    assert value.value == 3.0 and fe.messages == []
    # a value from the program is sent
    value.value = 4
    assert fe.props(bound)["model-value"] == 4.0
    # a derived prop is not written by the browser
    fe.event(derived, "update:model-value", "typed")
    assert fe.props(derived)["model-value"] == "v4"


def test_style_class_hidden_bindings():
    cls, hidden = Observable("a overflow-hidden"), Observable(False)
    wide = Observable(True)
    box = Div(ui_class=cls, ui_hidden=hidden)
    row = Row(ui_class=cls, ui_style=computed(lambda: {"width": "9px"}))
    lazy = Div(
        ui_class=computed(lambda: "wide" if wide.value else "narrow"),
        ui_invisible=computed(lambda: not wide.value),
    )
    assert box.ui_class == "a overflow-hidden" and not box.ui_hidden
    assert row.ui_class == "row a overflow-hidden"
    assert "class" not in lazy._props

    fe = mount(Div(box, row, lazy))
    assert fe.props(row)["style"] == "width:9px"
    assert fe.props(lazy)["class"] == "wide"
    hidden.value = True
    assert fe.props(box)["class"] == "a overflow-hidden hidden"
    cls.value = ["b", "c"]
    assert fe.props(box)["class"] == "b c hidden"
    assert fe.props(row)["class"] == "row b c"
    wide.value = False
    assert fe.props(lazy)["class"] == "narrow invisible"

    plain = Div(ui_class="overflow-hidden x")
    plain.ui_hidden = True
    plain.ui_hidden = False
    assert plain.ui_class == "overflow-hidden x"


def test_bound_text_and_label():
    n = Observable(1)
    calls = []

    def text():
        calls.append(1)
        return f"n = {n.value}"

    label = Label(computed(text))
    box = Div("Value: ", n, "!")
    root = Div(label, box)
    assert calls == [] and "text" not in label._props
    assert all(not isinstance(c, Observable) for c in box.ui_children)

    fe = mount(root)
    assert fe.children(label) == ["n = 1"]
    assert fe.children(box) == ["Value: ", "1", "!"]
    assert label.text == "n = 1"

    n.value = 2
    # the texts are updated in place: no slot is sent
    assert len(fe.messages) == 1
    assert entries(fe.messages[0]) == {
        f"t{label.ui_children[0]._index}": {"text": "n = 2"},
        f"t{box.ui_children[1]._index}": {"text": "2"},
    }
    assert fe.children(label) == ["n = 2"] and fe.dropped == []

    label.text = "plain"
    assert fe.children(label) == ["plain"] and label.text == "plain"
    n.value = 3
    assert fe.children(label) == ["plain"]
    label.text = n
    assert fe.children(label) == ["3"] and "text" not in label._props


def test_show():
    on = Observable(False)
    built = []

    def build():
        built.append("yes")
        return [QInput(ui_label="kept"), "text"]

    keep = Show(on, build, lambda: Label("off"))
    drop = Show(lambda: on.value, lambda: Label("on"), keep=False)
    before, after = Label("before"), Label("after")
    root = Div(before, keep, drop, after)
    # built without a browser, only the branch that is needed
    assert built == [] and len(keep.ui_children) == 1
    assert drop.ui_children == []

    fe = mount(root)
    off = keep.ui_children[0]
    assert fe.children(root) == [before, off, after]
    assert keep._index not in fe.mounted

    on.value = True
    inp, text = keep.ui_children[:2]
    assert built == ["yes"] and off.ui_class == "hidden"
    shown = drop.ui_children[0]
    assert fe.children(root) == [before, inp, text, off, shown, after]
    assert fe.props(off)["class"] == "hidden"
    # the slot of the parent and the class of the hidden branch
    assert len(fe.messages) == 1
    assert set(entries(fe.messages[0])) == {root._index, off._index}

    on.value = False
    # kept and hidden, the other one is removed
    assert built == ["yes"] and keep.ui_children[:2] == [inp, text]
    assert fe.props(inp)["class"] == fe.props(text)["class"] == "hidden"
    assert fe.props(off)["class"] == ""
    assert fe.children(root) == [before, inp, text, off, after]
    assert inp._index in fe.mounted and shown._index not in fe.mounted
    on.value = True
    assert built == ["yes"] and fe.props(inp)["class"] == ""
    assert drop.ui_children[0] is not shown


def test_for():
    items = Observable(["a", "b", "c"])
    rendered = []

    def render(item):
        rendered.append(item)
        return Label(item)

    rows = For(items, render, otherwise=lambda: "nothing")
    root = Div("head", rows)
    assert rendered == ["a", "b", "c"]
    a, b, c = rows.ui_children

    fe = mount(root)
    assert fe.children(root) == ["head", a, b, c]
    items.value = ["c", "a", "d", "a"]
    # kept rows are moved, only new keys are rendered
    assert rendered == ["a", "b", "c", "d", "a"]
    assert rows.ui_children[:2] == [c, a]
    assert fe.children(root) == ["head", *rows.ui_children]
    assert {a._index, c._index} <= fe.mounted and b._index not in fe.mounted
    assert len(fe.messages) == 1

    items.value = []
    (empty,) = rows.ui_children
    assert fe.children(empty) == ["nothing"]

    with pytest.raises(TypeError, match="hashable"):
        For(lambda: [[1]], render)._reconcile([[1]])

    # rows following their item
    data = Observable([{"id": 1, "n": 1}, {"id": 2, "n": 2}])
    count = []

    def row(item):
        count.append(1)
        return Label(computed(lambda: f"n={item.value['n']}"))

    live = For(data, row, key=lambda d: d["id"], reactive=True)
    plain = For(data, lambda d: Label(str(d["n"])), key=lambda d: d["id"])
    first, plain_first = live.ui_children[0], plain.ui_children[0]
    fe = mount(Div(live, plain))
    data.value = [{"id": 1, "n": 5}, {"id": 2, "n": 2}]
    assert count == [1, 1] and live.ui_children[0] is first
    assert fe.children(first) == ["n=5"]
    # without reactive the changed row is built again, the other is kept
    assert plain.ui_children[0] is not plain_first
    assert fe.children(plain.ui_children[0]) == ["5"]


def test_dynamic_and_fragments():
    kind, label = Observable("a"), Observable("x")
    builds = []

    def build():
        builds.append(kind.value)
        if kind.value == "a":
            return Fragment(QBtn(ui_label=label), "text")
        return [Label("b1"), Label("b2")]

    region = Dynamic(build)
    last = Label("last")
    root = Div(Fragment("first", region), last)
    fe = mount(root)
    fragment = region.ui_children[0]
    btn = fragment.ui_children[0]
    # nested fragments are spliced into the slot of the parent
    assert fe.children(root) == ["first", btn, "text", last]
    assert fe.mounted == {root._index, btn._index, last._index}

    label.value = "y"  # bound inside: not built again
    assert builds == ["a"] and fe.props(btn)["label"] == "y"
    kind.value = "b"
    assert builds == ["a", "b"] and len(fe.messages) == 2
    assert set(entries(fe.messages[1])) == {root._index}
    assert fe.children(root) == ["first", *region.ui_children, last]
    assert btn._index not in fe.mounted

    def fail():
        raise ValueError(kind.value)

    region._build = fail
    kind.value = "c"  # reported, the content stays
    assert len(region.ui_children) == 2
    for register in (region.on_mounted, region.effect):
        with pytest.raises(TypeError, match="never mounted"):
            register(lambda: None)


def test_effect_lifecycle():
    n = Observable(1)
    runs = []
    target = Div()
    target.effect(lambda: runs.append(n.value))
    dialog = Div(target)
    root = Div(dialog)
    n.value = 2
    assert runs == []  # not mounted

    fe = mount(root)
    assert runs == [2]
    with batch():
        n.value = 3
        n.value = 4
    assert runs == [2, 4]
    fe.unmount(dialog)
    n.value = 5
    assert runs == [2, 4]
    fe.mount(dialog)  # every mount needs its content again
    assert runs == [2, 4, 5]
    fe.unmount(dialog)
    fe.mount(dialog)
    assert runs == [2, 4, 5, 5]


def test_job_builds_structure_only():
    set_environment(EnvironmentType.COMPUTE, have_backend=False)
    known = set(bc._frontend_known)
    n = Observable(1)
    calls = []

    def text():
        calls.append("computed")
        return str(n.value)

    text = computed(text)
    label, btn = Label(text), QBtn(ui_label=text, id="b")
    btn.effect(lambda: calls.append("effect"))
    rows = For(lambda: range(n.value), lambda i: Div(id=f"row{i}"))
    root = Div(label, btn, rows, Show(lambda: n.value > 1, lambda: Div(id="s")))
    n.value = 3
    assert [c._id for c in rows.ui_children] == ["row0", "row1", "row2"]
    assert root.ui_children[3].ui_children[0]._id == "s"
    assert calls == [] and btn._dump() == {"style": ""}
    assert bc._frontend_known == known
