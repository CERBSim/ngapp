"""Durable pending edits and the sync status of a session on the SQLite
store: export_pending, import_pending after a reload of the tab,
on_pending_change and on_status"""

import json

import pytest

from ngapp.state import CaseSession
from ngapp.store import TransientStoreError
from ngapp.store.tree import flatten

from test_state import DemoApp

MAXH = ("maxh", "input", "model-value")
LABEL = ("label", "ui", "text")


class Flaky:
    """Store of a tab that can go offline"""

    def __init__(self, store):
        self.store = store
        self.offline = False

    def __getattr__(self, name):
        attr = getattr(self.store, name)
        if not callable(attr) or name in ("subscribe",):
            return attr

        def call(*args, **kwargs):
            if self.offline:
                raise TransientStoreError("offline")
            return attr(*args, **kwargs)

        return call


@pytest.fixture(autouse=True)
def env():
    from ngapp.utils import EnvironmentType, set_environment

    env = set_environment(EnvironmentType.STANDALONE, have_backend=False)
    env.frontend.update_component = lambda *a, **k: None
    env.data_layer = True
    yield env
    env.data_layer = False


def tab(server, sched, case_id, user="alice", pending=()):
    """A tab: the app opened on a case (None: a new case), with pending
    edits of an earlier tab re-applied"""
    app = DemoApp()
    store = Flaky(server.client(user))
    session = CaseSession.open(app, store, case_id, app_id=1, scheduler=sched)
    for data in pending:
        session.import_pending(json.loads(json.dumps(data)))
    return app, session


def stored(server, case_id):
    return flatten(server.client("alice").state(case_id))


def new_case(server, sched):
    app, session = tab(server, sched, None)
    app.mesher.state.k = 0
    sched.advance(30)
    assert session.case_id is not None
    return app, session


def test_pending_change_and_status(server, sched):
    app, session = new_case(server, sched)
    calls, statuses = [], []
    session.on_pending_change(lambda: calls.append(session.export_pending()))
    session.on_status(statuses.append)
    assert session.export_pending() is None and session.status == "saved"
    app.mesher.maxh.ui_model_value = 0.5
    assert calls and calls[-1]["ops"] == [
        {"op": "set", "path": list(MAXH), "value": 0.5}
    ]
    assert calls[-1]["case_id"] == session.case_id
    assert calls[-1]["base_revision"] == session.base_revision
    sched.advance(30)
    assert calls[-1] is None and statuses == ["pending", "saving", "saved"]
    session.store.offline = True
    app.label.text = "offline"
    sched.advance(30)
    assert session.status == "offline" and calls[-1]["ops"]
    session.store.offline = False
    sched.advance(120)
    assert (
        session.status == "saved"
        and stored(server, session.case_id)[LABEL] == "offline"
    )
    server.delete_case(session.case_id)
    app.label.text = "deleted"
    sched.advance(30)
    assert session.status == "read_only"
    assert {op["path"][1] for op in calls[-1]["ops"]} == {"ui", "slots"}


def test_import_of_other_case_is_ignored(server, sched):
    a, sa = new_case(server, sched)
    a.label.text = "x"
    exported = sa.export_pending()
    b, sb = new_case(server, sched)
    assert sb.import_pending(exported) is False
    assert b.label.text == "waiting"


def test_detached_ops_of_dynamic_components(server, sched):
    """Edits of components created later than the import are applied when
    they appear"""
    a, sa = new_case(server, sched)
    exported = {
        "case_id": sa.case_id,
        "base_revision": sa.base_revision,
        "ops": [{"op": "set", "path": ["late", "state", "v"], "value": 3}],
    }
    sa.close()
    from ngapp.components.basecomponent import Component

    c, sc = tab(server, sched, sa.case_id, pending=[exported])
    late = Component("div", id="late")
    c.component.ui_children = [*c.component.ui_children, late]
    sched.advance(30)
    assert late.state.v == 3
    assert stored(server, sa.case_id)[("late", "state", "v")] == 3
