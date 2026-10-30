"""Parts of the HTTP store that need no backend: events forwarded by the
browser (deliver_events), the client form of the server's state, and the FULL
mode entry create_app with a case id (on the SQLite store); the store
itself is tested against the backend in the webapp's backend tests"""

import pytest

from ngapp.app import App, AppConfig, create_app
from ngapp.components import Col, QInput
from ngapp.jobs import JobHandle, compute
from ngapp.store import Op
from ngapp.store import http as http_store
from ngapp.store.http import HTTPStore, _client_state, _idempotency_key
from ngapp.store.tree import Seq, flatten
from ngapp.utils import EnvironmentType, set_environment


@pytest.fixture
def deliver():
    yield HTTPStore("http://unused/api", "token", events="deliver")
    for sub in list(http_store._deliveries):
        sub.close()


def test_deliver_events(deliver):
    seen_a, seen_b, cases = [], [], []
    http_store.on_subscriptions.append(cases.append)
    try:
        close_a = deliver.subscribe([1], 0, seen_a.append)
        deliver.subscribe([2], 5, seen_b.append)
    finally:
        http_store.on_subscriptions.remove(cases.append)
    assert cases == [[1], [1, 2]] and http_store.subscribed_cases() == [1, 2]
    http_store.deliver_events(
        [
            {"seq": 12, "type": "case.head", "payload": {"case_id": 2}},
            {"seq": 11, "type": "case.head", "payload": {"case_id": 1}},
            {"seq": 4, "type": "case.head", "payload": {"case_id": 2}},
            {"seq": 13, "type": "job.status", "payload": {"case_id": 1}},
            {"seq": 14, "type": "run.status", "payload": {"case_id": 2}},
            {"seq": 15, "type": "cases.changed", "payload": {"case_id": 9}},
            {"seq": 16, "type": "job.progress", "payload": {"case_id": 9}},
            {"seq": 17, "type": "other", "payload": {}},
            {"seq": 11, "type": "case.head", "payload": {"case_id": 1}},
        ]
    )
    # in seq order, once, by case id; user events and events without a case
    # to everybody
    assert [e.seq for e in seen_a] == [11, 13, 15, 17]
    assert [e.seq for e in seen_b] == [12, 14, 15, 17]
    assert seen_a[0].payload == {"case_id": 1}
    http_store.deliver_events('[{"type": "resync"}]')
    assert seen_a[-1].type == seen_b[-1].type == "resync"
    close_a()
    http_store.deliver_events(
        [
            {
                "seq": 3,
                "type": "case.head",
                "payload": {"case_id": 2},
                "topic": "case:2",
            }
        ]
    )
    assert seen_a[-1].type == "resync" and seen_b[-1].seq == 3
    assert http_store.subscribed_cases() == [2]


def test_client_state_and_keys():
    server = {
        "case_id": 3,
        "revision": 9,
        "release_id": 4,
        "event_seq": 21,
        "state": {
            "a": {
                "ui": {},
                "input": {"x": 1},
                "state": {"log": {"$seq": ["a", "b"]}, "rows": [1, 2]},
                "slots": {},
                "children": {"b": {"ui": {"l": "L"}, "children": {}}},
            },
            "__case__": {"meta": {"name": "N"}, "children": {}},
        },
    }
    state = _client_state(server)
    assert state["revision"] == 9 and state["release"] == 4
    assert state["event_seq"] == 21
    flat = flatten(state)
    assert isinstance(flat[("a", "state", "log")], Seq)
    assert flat[("a", "state", "rows")] == [1, 2]
    assert flat[("a", "b", "ui", "l")] == "L"
    assert flat[("__case__", "meta", "name")] == "N"
    key = "6b6a1b0e-2f5c-4b3c-8d6e-9f0a1b2c3d4e"
    assert _idempotency_key(key) == key
    assert (
        _idempotency_key("k1")
        == _idempotency_key("k1")
        != _idempotency_key("k2")
    )


class WiringApp(App):
    def __init__(self):
        super().__init__()
        self.maxh = QInput(id="maxh", ui_model_value=0.1)
        self.component = Col(self.maxh)


AppConfig(WiringApp, name="wiring", version="1")


class ComputeApp(App):
    def __init__(self):
        super().__init__()
        self.maxh = QInput(id="maxh", ui_model_value=0.1)
        self.component = Col(self.maxh)

    @compute
    def solve(self):
        self.state.n = 1


@pytest.fixture
def full_mode(monkeypatch, server):
    env = set_environment(EnvironmentType.STANDALONE, have_backend=True)
    env.frontend.update_component = lambda *a, **k: None
    stores = []

    def from_environment(**options):
        store = server.client("alice", release_id=options.get("release_id"))
        stores.append(store)
        return store

    monkeypatch.setattr(HTTPStore, "from_environment", from_environment)
    yield server, stores
    env.data_layer = False
    env.have_backend = False


def test_compute_without_a_case_creates_it(full_mode):
    """A direct call of a compute method in FULL mode before the first save
    creates the case and submits on it (not the old /job path)"""
    server, stores = full_mode
    config = {
        "id": 32,
        "name": "compute",
        "version": "1",
        "python_class": f"{__name__}.ComputeApp",
        "release_id": 2,
    }
    app = create_app(config, {"case_id": None})
    try:
        assert app.case_session.case_id is None
        handle = app.solve()
        assert isinstance(handle, JobHandle)
        case_id = app.case_session.case_id
        assert case_id is not None and handle.status == "queued"
        assert stores[-1].job(handle.id).case_id == case_id
    finally:
        app.case_session.close()

    # no session at all (e.g. after the previous case was closed)
    assert app.case_session is None and app.env.data_layer
    handle = app.solve()
    try:
        assert isinstance(handle, JobHandle)
        assert app.case_session.case_id not in (None, case_id)
        assert stores[-1].job(handle.id).case_id == app.case_session.case_id
    finally:
        app.case_session.close()


def test_http_store_sends_its_release(monkeypatch):
    """A job runs with the release of the client that submits it"""
    sent = []
    store = HTTPStore("http://unused/api", "token", release_id=7)
    monkeypatch.setattr(
        store,
        "_request",
        lambda method, path, body=None, **kw: sent.append(body)
        or {
            "job": {
                "id": 1,
                "case_id": 1,
                "function": "f",
                "status": "queued",
                "input_revision": 5,
            }
        },
    )
    from ngapp.store.types import JobRequest

    store.submit(1, JobRequest({"component": [], "method": "f"}, 5))
    assert sent[0]["release_id"] == 7 and sent[0]["input_revision"] == 5


def test_submission_of_an_older_release_blocks_the_session(full_mode):
    """A client of an older release cannot submit (its code is not
    the runner's); the session asks for the newer app as on a commit"""
    server, stores = full_mode
    case = server.client("alice", release_id=5).create_case(34, "c", [])
    config = {
        "id": 34,
        "name": "compute",
        "version": "1",
        "python_class": f"{__name__}.ComputeApp",
        "release_id": 4,
    }
    app = create_app(config, {"case_id": case.id})
    try:
        from ngapp.store import ReleaseTooOldError

        with pytest.raises(ReleaseTooOldError):
            app.solve()
        assert app.case_session.status == "release_too_old"
    finally:
        app.case_session.close()


def test_events_wait_for_a_promising_entry(deliver, monkeypatch):
    """In the browser, events that arrive through a synchronous
    entry point (callbacks there cannot read blobs: no stack switching) are
    delivered later from a task; their order is kept"""
    seen = []
    deliver.subscribe([1], 0, seen.append)
    deferred = []
    monkeypatch.setattr(http_store, "_can_block", lambda: False)
    monkeypatch.setattr(http_store, "_defer", deferred.append)
    http_store.deliver_events(
        [{"seq": 2, "type": "case.head", "payload": {"case_id": 1}}]
    )
    http_store.deliver_events(
        [{"seq": 1, "type": "case.head", "payload": {"case_id": 1}}]
    )
    assert seen == [] and len(deferred) >= 1
    monkeypatch.setattr(http_store, "_can_block", lambda: True)
    for f in deferred:
        f()
    assert [e.seq for e in seen] == [1, 2]


def test_events_during_create_app_wait_until_it_finished(
    full_mode, monkeypatch
):
    """Events delivered while create_app opens a case (e.g. a job's
    events right after a reload) reach the callbacks only once the app is
    created, not in the middle of loading it"""
    server, stores = full_mode
    case = server.client("alice").create_case(
        35, "c", [Op("set", ("maxh", "input", "model-value"), 0.5)]
    )
    config = {
        "id": 35,
        "name": "wiring",
        "version": "1",
        "python_class": f"{__name__}.WiringApp",
        "release_id": 1,
    }
    seen, apps = [], []
    orig = WiringApp._open_case

    def open_case(self, *args, **kw):
        apps.append(self)
        self._loading = True
        orig(self, *args, **kw)
        http_store.deliver_events(
            [{"seq": 7, "type": "job.status", "payload": {"case_id": case.id}}]
        )
        assert seen == []
        self._loading = False

    monkeypatch.setattr(WiringApp, "_open_case", open_case)
    deliver = HTTPStore("http://unused/api", "token", events="deliver")
    close = deliver.subscribe(
        [case.id], 0, lambda e: seen.append((e.seq, apps[-1]._loading))
    )
    try:
        app = create_app(config, {"case_id": case.id})
        assert seen == [(7, False)]
    finally:
        close()
        apps[-1].case_session.close()
