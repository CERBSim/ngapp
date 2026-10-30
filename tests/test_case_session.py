"""Sync of a case session on the client side: read-only shares and their
held edits, retry after a token refresh, positions of concurrent appends,
echo counting, the saving status, deleted cases, and the runs view on
read-only and deleted cases"""

import json
import logging

import numpy as np
import pytest
from helpers import share, stored_run

from ngapp.app import App
from ngapp.state import CaseSession
from ngapp.store import CaseDeletedError, UnauthorizedError
from ngapp.store.tree import flatten
from test_job_components import click, create, open_case, run_jobs
from test_pending import Flaky
from test_state import DemoApp

MAXH = ("maxh", "input", "model-value")
LABEL = ("label", "ui", "text")


@pytest.fixture(autouse=True)
def env():
    from ngapp.utils import EnvironmentType, set_environment

    env = set_environment(EnvironmentType.STANDALONE, have_backend=False)
    env.frontend.update_component = lambda *a, **k: None
    env.data_layer = True
    yield env
    env.data_layer = False


def open_tab(server, sched, case_id, user="alice"):
    app = DemoApp()
    session = CaseSession.open(
        app, Flaky(server.client(user)), case_id, app_id=1, scheduler=sched
    )
    return app, session


def owned_case(server, sched):
    app, session = open_tab(server, sched, None)
    app.mesher.maxh.ui_model_value = 0.4
    sched.advance(30)
    assert session.case_id is not None
    return app, session


def head(server, case_id):
    return server.client("alice").case(case_id).head


def test_read_only_share(server, sched):
    """No commits and no conflict notices on a read-only share; an
    upgrade to write takes effect without reopening"""
    a, sa = owned_case(server, sched)
    share(server, sa.case_id, "bob", write=False)
    b, sb = open_tab(server, sched, sa.case_id, user="bob")
    conflicts, statuses = [], []
    sb.on_conflict(conflicts.extend)
    sb.on_status(statuses.append)
    assert sb.status == "read_only" and sb.read_only_reason == "no_write"
    rev = head(server, sa.case_id)
    b.mesher.maxh.ui_model_value = 0.9
    sched.advance(30)
    assert head(server, sa.case_id) == rev and sb.last_error is None
    a.mesher.maxh.ui_model_value = 0.7
    sched.advance(30)
    assert b.mesher.maxh.ui_model_value == 0.7
    assert conflicts == [] and sb.replaced == []
    share(server, sa.case_id, "bob", write=True)
    sched.advance(1)
    assert sb.status != "read_only" and sb.read_only_reason is None
    b.label.text = "bob writes"
    sched.advance(30)
    assert sb.status == "saved"
    assert a.label.text == "bob writes"
    assert "read_only" not in statuses[-1:]


def test_forbidden_commit_switches_to_read_only(server, sched):
    """A 403 on commit makes the session read only, no retries"""
    a, sa = owned_case(server, sched)
    share(server, sa.case_id, "bob", write=True)
    b, sb = open_tab(server, sched, sa.case_id, user="bob")
    sched.advance(30)
    assert sb.status == "saved"
    share(server, sa.case_id, "bob", write=False, event=False)
    b.mesher.maxh.ui_model_value = 0.9
    sched.advance(30)
    assert sb.status == "read_only" and sb.read_only_reason == "no_write"
    assert sb._timer is None


def test_retry_after_token_refresh(server, sched):
    """A save that failed with an expired token is retried right
    after the refresh, not after its backoff"""
    a, sa = owned_case(server, sched)
    store = sa.store
    fail = {"on": True}
    commit = store.store.commit

    def expired(*args, **kwargs):
        if fail["on"]:
            raise UnauthorizedError("token expired")
        return commit(*args, **kwargs)

    store.store.commit = expired
    a.mesher.maxh.ui_model_value = 0.25
    sched.advance(40)
    assert sa.status == "error"
    fail["on"] = False
    rev = head(server, sa.case_id)
    sa.retry()
    sched.advance(0.01)
    assert sa.status == "saved" and head(server, sa.case_id) > rev


def test_concurrent_appends_report_moved_positions(server, sched):
    """Local appends that move behind appends of another tab are
    reported with their new positions"""
    a, sa = owned_case(server, sched)
    b, sb = open_tab(server, sched, sa.case_id)
    seen = []
    a.mesher.state.on_change(lambda keys: seen.append(set(keys)))

    from ngapp.state import storage_on_change

    positions = []
    storage_on_change(a.mesher.state, lambda keys: positions.append(set(keys)))
    b.mesher.state.list("log").append("b0")
    sched.advance(30)
    positions.clear()
    a.mesher.state.list("log").append("a1")
    b.mesher.state.list("log").append("b1")
    sb.commit()
    sched.advance(30)
    assert list(a.mesher.state.log) == ["b0", "b1", "a1"]
    assert any("log#2" in keys for keys in positions), positions


def test_user_commits_are_no_echoes(server, sched, caplog):
    """Commits with edits of the user are not counted as echoes
    of change callbacks, also when a callback ran before"""
    a, sa = owned_case(server, sched)
    b, sb = open_tab(server, sched, sa.case_id)
    st = a.mesher.state
    pulls = iter(range(1000))
    st.on_change(lambda keys: st.set("pulls", next(pulls)))
    with caplog.at_level(logging.WARNING, logger="ngapp.state"):
        for i in range(6):
            b.mesher.state.x = i
            sb.commit()
            sched.advance(0.1)
            a.mesher.maxh.ui_model_value = i
            sched.advance(30)
    assert sa.echo_warnings == 0
    assert "caused by change callbacks" not in caplog.text


def test_no_saving_status_without_changes(server, sched):
    """A change that commits nothing never shows saving"""
    a, sa = owned_case(server, sched)
    statuses = []
    sa.on_status(statuses.append)
    a.mesher.maxh.ui_model_value = 0.4  # the stored value
    sched.advance(30)
    assert "saving" not in statuses
    a.mesher.maxh.ui_model_value = 0.5
    sched.advance(30)
    assert statuses[-2:] == ["saving", "saved"]


def test_new_case_pending_as_json_string(server, sched, env):
    """Pending edits of a new case (create_app data from the
    browser: one JSON string) are re-applied and the first save creates the
    case"""
    a, sa = open_tab(server, sched, None)
    sa.store.offline = True
    a.mesher.maxh.ui_model_value = 0.75
    sched.advance(30)
    assert sa.status == "offline" and sa.case_id is None
    exported = json.dumps([json.dumps(sa.export_pending())])
    sa.close()
    b = DemoApp()
    session = App._open_case(
        b, None, store=Flaky(server.client("alice")), pending=exported
    )
    session.scheduler = sched
    assert b.mesher.maxh.ui_model_value == 0.75
    sched.advance(30)
    session.commit()
    assert session.case_id is not None and session.status == "saved"
    assert flatten(server.client("alice").state(session.case_id))[MAXH] == 0.75


def test_no_autosave_retries_with_expired_token(server, sched):
    """After a 401 the session waits for a new token
    (retry) instead of committing with the dead token every 60 s"""
    a, sa = owned_case(server, sched)
    store = sa.store
    calls = []
    commit = store.store.commit

    def expired(*args, **kwargs):
        calls.append(1)
        raise UnauthorizedError("token expired")

    store.store.commit = expired
    a.mesher.maxh.ui_model_value = 0.25
    sched.advance(40)
    assert sa.status == "error" and len(calls) == 1
    sched.advance(600)
    assert len(calls) == 1
    a.mesher.maxh.ui_model_value = 0.3
    sched.advance(600)
    assert len(calls) == 1 and sa.status == "error"
    store.store.commit = commit
    sa.retry()
    sched.advance(0.01)
    assert sa.status == "saved"


def test_large_value_shows_saving_while_encoded(server, sched):
    """The status is saving while a large value is
    encoded, not saved"""
    import numpy as np

    a, sa = owned_case(server, sched)
    statuses = []
    sa.on_status(statuses.append)
    a.mesher.state.big = np.arange(100_000.0)
    # Saving until the commit with its upload
    assert statuses == ["saving"] and sa.status == "saving"
    sched.advance(30)
    assert sa.status == "saved" and "pending" not in statuses
    statuses.clear()
    a.mesher.state.small = 1
    assert "saving" not in statuses


def read_only_tab(server, sched):
    a, sa = owned_case(server, sched)
    share(server, sa.case_id, "bob", write=False)
    b, sb = open_tab(server, sched, sa.case_id, user="bob")
    assert sb.status == "read_only"
    return a, sa, b, sb


@pytest.mark.parametrize("decision", ["keep", "discard"])
def test_read_only_edits_held_after_upgrade(server, sched, decision):
    """Edits of the read-only time are neither exported nor
    committed by the upgrade; the user keeps or discards them"""
    a, sa, b, sb = read_only_tab(server, sched)
    b.label.text = "made while read only"
    assert sb.export_pending() is None and not sb.held_edits
    rev = head(server, sa.case_id)
    share(server, sa.case_id, "bob", write=True)
    sched.advance(30)
    assert sb.status == "pending" and sb.held_edits
    assert head(server, sa.case_id) == rev and sb.export_pending() is None
    # a later edit waits with them
    b.mesher.maxh.ui_model_value = 0.8
    sched.advance(30)
    assert head(server, sa.case_id) == rev and sb.held_edits
    if decision == "keep":
        sb.keep_held()
        assert not sb.held_edits
        sched.advance(30)
        assert sb.status == "saved" and head(server, sa.case_id) > rev
        assert a.label.text == "made while read only"
        assert a.mesher.maxh.ui_model_value == 0.8
    else:
        sb.discard()
        assert sb.status == "saved" and not sb.held_edits
        assert b.label.text != "made while read only"
        assert b.mesher.maxh.ui_model_value == 0.4
        sched.advance(30)
        assert head(server, sa.case_id) == rev
    # edits after the decision are saved as usual
    b.mesher.maxh.ui_model_value = 0.3
    sched.advance(30)
    assert a.mesher.maxh.ui_model_value == 0.3


def test_downgrade_holds_unsaved_edits(server, sched):
    """Edits not saved when the share becomes read only are not
    exported and wait for the user after an upgrade"""
    a, sa = owned_case(server, sched)
    share(server, sa.case_id, "bob", write=True)
    b, sb = open_tab(server, sched, sa.case_id, user="bob")
    sched.advance(30)
    b.label.text = "unsaved at the downgrade"
    assert sb.export_pending() is not None
    share(server, sa.case_id, "bob", write=False)
    sched.advance(30)
    assert sb.status == "read_only" and sb.export_pending() is None
    share(server, sa.case_id, "bob", write=True)
    sched.advance(30)
    assert sb.held_edits and a.label.text != "unsaved at the downgrade"


def test_deleted_case_without_edits_is_no_save_failure(server, sched, caplog):
    """Deleting a case with nothing pending logs no save failure
    and sends no commit"""
    a, sa = owned_case(server, sched)
    sched.advance(30)
    commits = []
    commit = sa.store.store.commit
    sa.store.store.commit = lambda *args, **kw: commits.append(1) or commit(
        *args, **kw
    )
    with caplog.at_level(logging.WARNING, logger="ngapp"):
        server.delete_case(sa.case_id)
        sched.advance(30)
        assert sa.status == "read_only" and sa.read_only_reason == "deleted"
        with pytest.raises(CaseDeletedError):
            sa.commit()
    assert "Saving case" not in caplog.text and "Traceback" not in caplog.text
    assert commits == []


def test_deleted_case_with_edits_reports_once(server, sched, caplog):
    a, sa = owned_case(server, sched)
    a.label.text = "pending"
    with caplog.at_level(logging.WARNING, logger="ngapp"):
        server.delete_case(sa.case_id)
        sched.advance(30)
    assert caplog.text.count("Saving case") == 1


def test_large_value_saving_until_commit(server, sched):
    """Saving from the encoding of a large value until its
    commit, also during the autosave delay; small values stay pending"""
    a, sa = owned_case(server, sched)
    a.mesher.state.big = np.arange(100_000.0)
    sched.advance(0.5)
    assert sa.status == "saving"
    sched.advance(30)
    assert sa.status == "saved"
    a.label.text = "small"
    assert sa.status == "pending"


def test_runs_view_read_only_and_deleted(server, sched, job_sched, caplog):
    """The runs view disables its actions while read only; a
    refused action shows a short message without traceback"""
    app, session = create(server, sched)
    click(app.control.run_button)
    run_jobs(server, sched, job_sched)
    share(server, session.case_id, "bob", write=False)
    b, sb = open_case(server, sched, session.case_id, user="bob")
    sched.run_pending()
    view = b.runs_view
    [run] = view.runs
    assert view.read_only == "no_write"
    item = view.list.ui_children[0]
    keep = item.ui_children[2].ui_children[0].ui_children[0]
    assert keep.ui_disable
    with caplog.at_level(logging.WARNING):
        view.keep(run.id)
    assert (
        not stored_run(server, run.id).kept and "Traceback" not in caplog.text
    )
    # access changed without an event: the store refuses, shown in short
    share(server, session.case_id, "bob", write=True, event=False)
    share(server, session.case_id, "bob", write=True)
    sched.advance(1)
    assert view.read_only is None
    share(server, session.case_id, "bob", write=False, event=False)
    with caplog.at_level(logging.WARNING):
        view.keep(run.id)
    assert view.error.ui_children[0].startswith("Keeping the run failed")
    assert "Traceback" not in caplog.text
    # deleted: disabled, also fork; the job control without traceback
    server.delete_case(session.case_id)
    sched.advance(1)
    assert app.runs_view.read_only == "deleted"
    fork = (
        app.runs_view.list.ui_children[0]
        .ui_children[2]
        .ui_children[0]
        .ui_children[1]
    )
    assert fork.ui_disable
    caplog.clear()
    with caplog.at_level(logging.WARNING):
        app.solver.maxh.ui_model_value = 0.1
        click(app.control.run_button)
    assert app.control.detail.ui_children[0].startswith("Submitting failed")
    assert "Traceback" not in caplog.text


def test_keep_reaches_other_tabs(server, sched, job_sched):
    """Keeping a run updates the runs view of other tabs; the
    keep button is pressed and named after its state"""
    app, session = create(server, sched)
    click(app.control.run_button)
    run_jobs(server, sched, job_sched)
    other, so = open_case(server, sched, session.case_id)
    sched.run_pending()
    run_id = app.runs_view.runs[0].id
    app.runs_view.keep(run_id)
    sched.run_pending()
    for view in (app.runs_view, other.runs_view):
        assert view.runs[0].kept
        keep = (
            view.list.ui_children[0]
            .ui_children[2]
            .ui_children[0]
            .ui_children[0]
        )
        assert keep._props["aria-pressed"] == "true"
        assert keep._props["aria-label"] == f"Run {run_id} kept"


def test_fork_notice_stays(server, sched, job_sched, monkeypatch):
    """The fork notice stays until dismissed"""
    from types import SimpleNamespace

    from ngapp.components import RunsView

    app, session = create(server, sched)
    click(app.control.run_button)
    run_jobs(server, sched, job_sched)
    notes = []
    quasar = SimpleNamespace(notify=notes.append)
    monkeypatch.setattr(RunsView, "quasar", property(lambda self: quasar))
    app.runs_view.fork(app.runs_view.runs[0].id)
    [note] = notes
    assert note["timeout"] == 0
    assert any(a.get("aria-label") == "Dismiss" for a in note["actions"])


def test_deleted_while_a_job_runs_is_no_save_failure(server, sched, caplog):
    """The app shows job states in components that are not
    stored (marks the session dirty without edits); the deletion during the
    job reports no save failure"""
    app, session = create(server, sched)
    click(app.control.run_button)
    job = app.control.job
    job.on_status(lambda status: setattr(app.component, "ui_class", status))
    a = server.claim(job.id)
    server.heartbeat(job.id, a["attempt"])
    sched.run_pending()
    assert app.component.ui_class == "running"
    assert session.export_pending() is None
    with caplog.at_level(logging.WARNING, logger="ngapp"):
        server.delete_case(session.case_id)
        sched.run_pending()
    assert session.status == "read_only"
    assert session.read_only_reason == "deleted"
    assert "Saving case" not in caplog.text


def test_runs_view_of_a_deleted_case_follows_run_status(server, sched, caplog):
    """The run of a job cancelled after the deletion of its case
    is shown cancelled (the runs cannot be loaded anymore), the list is
    marked as one of a deleted case"""
    app, session = create(server, sched)
    click(app.control.run_button)
    job = app.control.job
    a = server.claim(job.id)
    server.heartbeat(job.id, a["attempt"])
    sched.run_pending()
    view = app.runs_view
    assert [r.status for r in view.runs] == ["running"]
    with caplog.at_level(logging.WARNING, logger="ngapp"):
        server.delete_case(session.case_id)
        sched.run_pending()
        server.finish(job.id, a["attempt"], "cancelled", message="case deleted")
        sched.run_pending()
    assert [r.status for r in view.runs] == ["cancelled"]
    assert view.read_only == "deleted"
    assert "hidden" not in view.deleted_note.ui_class
    assert "Loading the runs" not in caplog.text


def test_run_actions_on_a_read_only_case_fail_in_short(
    server, sched, job_sched, caplog, capsys
):
    """Run.keep of an app's button on a read-only share raises
    ForbiddenError, logged in short without a traceback"""
    from ngapp.components import QBtn
    from ngapp.store import ForbiddenError

    app, session = create(server, sched)
    click(app.control.run_button)
    run_jobs(server, sched, job_sched)
    share(server, session.case_id, "bob", write=False)
    b, sb = open_case(server, sched, session.case_id, user="bob")
    [run] = b.runs(b.solver.solve)
    with pytest.raises(ForbiddenError):
        run.keep()
    button = QBtn(ui_label="keep").on_click(lambda: run.keep())
    with caplog.at_level(logging.WARNING):
        click(button)
    out = capsys.readouterr()
    assert "Traceback" not in out.out + out.err + caplog.text
    assert "Refused (click" in caplog.text
