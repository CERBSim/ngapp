"""Reactive core: computed values, reactions, batch scopes, flush order"""

import gc
import logging
import threading

import numpy as np
import pytest

from ngapp import observable as obs_module
from ngapp.observable import (
    EFFECT,
    SYNC,
    Observable,
    Reaction,
    Signal,
    add_flush_hook,
    batch,
    collect_observables,
    computed,
    current_batch,
    effect,
    flush,
    observable_batch,
    remove_flush_hook,
    restore,
    safe_equal,
    snapshot,
    untracked,
)


def test_computed_lazy_and_cached():
    a = Observable(1, "a")
    calls = []

    def fn():
        calls.append(1)
        return a.value * 2

    c = computed(fn, "c")
    assert c.read_only and not a.read_only
    assert calls == []
    assert c.value == 2 and c.value == 2
    assert len(calls) == 1
    a.value = 3
    assert len(calls) == 1
    assert c.value == 6 and c.peek() == 6
    assert len(calls) == 2
    with pytest.raises(AttributeError):
        c.value = 1


def test_computed_conditional_dependencies():
    use_a = Observable(True, "use_a")
    a = Observable(1, "a")
    b = Observable(10, "b")
    calls = []

    def fn():
        calls.append(1)
        return a.value if use_a.value else b.value

    c = computed(fn)
    assert c.value == 1
    b.value = 11
    assert c.value == 1 and len(calls) == 1
    use_a.value = False
    assert c.value == 11 and len(calls) == 2
    a.value = 2
    assert c.value == 11 and len(calls) == 2


def test_equal_result_stops_propagation():
    a = Observable(1, "a")
    runs = {"sign": 0, "label": 0, "seen": []}

    def sign():
        runs["sign"] += 1
        return a.value > 0

    def label():
        runs["label"] += 1
        return "pos" if s.value else "neg"

    s = computed(sign)
    lab = computed(label)
    lab.on_change(lambda new, old: runs["seen"].append((new, old)))
    assert runs == {"sign": 1, "label": 1, "seen": []}
    a.value = 5
    assert runs == {"sign": 2, "label": 1, "seen": []}
    a.value = -1
    assert runs == {"sign": 3, "label": 2, "seen": [("neg", "pos")]}

    custom = computed(lambda: [a.value // 10], equal=lambda x, y: x == y)
    first = custom.value
    a.value = -2
    assert custom.value is first


def test_batch_runs_each_computed_once():
    a = Observable(1, "a")
    b = Observable(2, "b")
    calls = []
    seen = []
    total = computed(lambda: calls.append(1) or a.value + b.value)
    total.on_change(lambda new, old: seen.append((new, old)))
    calls.clear()
    with batch():
        a.value = 10
        b.value = 20
        a.value = 11
        assert current_batch() is not None
        assert seen == []
    assert current_batch() is None
    assert seen == [(31, 3)] and len(calls) == 1


def test_listeners_sync_in_event_scope_and_deferred_in_batch():
    a = Observable(1, "a")
    plain = []
    reacted = []
    a.on_change(lambda new, old: plain.append(new))
    dispose = effect(lambda: reacted.append(a.value))
    with batch(defer_listeners=False):
        a.value = 2
        assert plain == [2] and reacted == [1]
        with observable_batch():
            a.value = 3
            assert plain == [2]
        assert plain == [2, 3] and reacted == [1]
    assert reacted == [1, 3]
    with observable_batch():
        a.value = 4
        a.value = 5
        assert plain == [2, 3]
    assert plain == [2, 3, 4, 5] and reacted == [1, 3, 5]
    dispose()
    a.value = 6
    assert reacted == [1, 3, 5]


def test_flush_order_and_hooks():
    a = Observable(0, "a")
    log = []
    sync = Reaction(lambda: log.append(("sync", a.value)), SYNC)
    eff = Reaction(lambda: log.append(("effect", a.value)), EFFECT)
    a.on_change(lambda new, old: log.append(("listener", new)))
    hooks = [lambda: log.append("hook"), lambda: log.append("end")]
    add_flush_hook(hooks[0])
    add_flush_hook(hooks[1], stage="effect")
    try:
        log.clear()
        with batch():
            a.value = 1
            flush()
            assert log == [("listener", 1), ("sync", 1), "hook"]
            a.value = 2
        assert log[3:] == [
            ("listener", 2),
            ("sync", 2),
            "hook",
            ("effect", 2),
            "hook",
            "end",
        ]
    finally:
        for hook in hooks:
            remove_flush_hook(hook)
    del sync, eff


def test_reaction_lifecycle():
    a = Observable(1, "a")
    seen = []
    r = Reaction(lambda: seen.append(a.value), EFFECT, start=False)
    a.value = 2
    assert seen == []
    r.resume()
    a.value = 3
    assert seen == [2, 3]
    r.suspend()
    a.value = 4
    assert seen == [2, 3] and a._subs is None
    with batch():
        r.resume(run=False)
        assert seen == [2, 3]
    assert seen == [2, 3, 4]
    r.dispose()
    a.value = 5
    assert seen == [2, 3, 4]

    weak = Reaction(lambda: seen.append(a.value))
    del weak
    gc.collect()
    a.value = 6
    assert seen == [2, 3, 4, 5]


def test_errors_do_not_stop_the_flush(capsys, caplog):
    a = Observable(1, "a")
    seen = []

    def fail():
        if a.value == 2:
            raise ValueError("boom")
        return a.value

    c = computed(fail)
    bad = Reaction(lambda: seen.append(("bad", c.value)))
    good = Reaction(lambda: seen.append(("good", a.value)))
    a.value = 2
    assert seen[-1] == ("good", 2)
    captured = capsys.readouterr()
    assert "boom" in captured.out + captured.err
    with pytest.raises(ValueError):
        c.value
    a.value = 3
    assert seen[-2:] == [("bad", 3), ("good", 3)]

    loop = Reaction(lambda: setattr(a, "value", a.value + 1))
    with caplog.at_level(logging.ERROR, logger="ngapp.observable"):
        a.value = 100
    assert "did not settle" in caplog.text
    del bad, good, loop


def test_untracked_and_signal():
    a = Observable(1, "a")
    b = Observable(1, "b")
    sig = Signal()
    data = {"x": 1}
    runs = []

    def fn():
        sig.track()
        runs.append(1)
        with untracked():
            extra = b.value
        return a.value + extra + untracked(lambda: b.value) + data["x"]

    c = computed(fn)
    assert c.value == 4
    b.value = 5
    assert c.value == 4 and len(runs) == 1
    data["x"] = 2
    sig.changed()
    assert c.value == 13 and len(runs) == 2


def test_numpy_values_and_safe_equal():
    seen = []
    o = Observable(np.zeros(3), "o")
    o.on_change(lambda new, old: seen.append(new))
    o.value = np.ones(3)
    assert len(seen) == 1
    c = computed(lambda: o.value * 2)
    assert c.value[0] == 2
    o.value = np.ones(3)
    assert c.value[0] == 2
    assert safe_equal(1, 1.0) and not safe_equal(np.ones(2), np.ones(2))


def test_snapshot_skips_computed():
    class Holder:
        def __init__(self):
            self.a = Observable(1, "a")
            self.c = computed(lambda: self.a.value + 1, "c")

    h = Holder()
    assert list(collect_observables(h)) == ["a"]
    assert snapshot(h) == {"a": 1}
    restore(h, {"a": 5, "c": 0})
    assert h.c.value == 6


def test_threads_do_not_lose_or_duplicate_reactions():
    n, per_thread = 4, 300
    values = [Observable(0, f"v{i}") for i in range(n)]
    total = computed(lambda: sum(v.value for v in values))
    seen = []
    r = Reaction(lambda: seen.append(total.value))
    start = threading.Barrier(n)

    def work(i):
        start.wait()
        for k in range(per_thread):
            if k % 3:
                values[i].value += 1
            else:
                with batch():
                    values[i].value += 1

    threads = [threading.Thread(target=work, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert total.value == n * per_thread
    assert seen[-1] == n * per_thread
    assert len(seen) <= n * per_thread + 1
    assert all(x < y for x, y in zip(seen, seen[1:]))
    assert obs_module._n_trackers == 0 and obs_module._n_scopes == 0
    del r


def test_raising_computed_is_evaluated_once_per_change():
    calls = []
    x = Observable(0)

    def f():
        calls.append(1)
        return {}["k"] if x.value else "ok"

    v = computed(f)
    w = computed(lambda: not v.value)
    seen = []
    r = Reaction(lambda: seen.append(w.value))
    calls.clear()
    x.value = 1
    assert len(calls) == 1
    x.value = 0
    assert len(calls) == 2 and seen[-1] is False
    r.dispose()
