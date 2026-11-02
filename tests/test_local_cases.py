"""Local app mode: cases in a SQLite store per app, the last opened case
after a restart, the case list, export and import, files of the previous
local mode; storage of revisions and several processes on one database"""

import os
import pickle
import subprocess
import sys
import textwrap
import time

import numpy as np
import pytest

from local_jobs_app import JobsApp, config
from ngapp.components import basecomponent
from ngapp.local_cases import LocalCases, store_path
from ngapp.store import Op
from ngapp.store.sqlite import SQLiteServer
from ngapp.store.tree import flatten
from ngapp.utils import EnvironmentType, set_environment
from helpers import ManualScheduler, revision_count, run_jobs as run_queued


@pytest.fixture(autouse=True)
def env():
    env = set_environment(EnvironmentType.STANDALONE, have_backend=False)
    env.frontend.update_component = lambda *a, **k: None
    env.data_layer = True
    yield env
    env.data_layer = False


def local(**kw):
    return LocalCases(
        config,
        jobs=None,
        poll_interval=None,
        session_options={"scheduler": ManualScheduler()},
        **kw,
    )


def test_default_path(tmp_path):
    assert (
        store_path(config)
        == tmp_path / "ngapp-data" / "local_jobs" / "cases.sqlite"
    )


def test_open_edit_restart_reopen():
    cases = local()
    app = cases.start()
    assert isinstance(app, JobsApp) and cases.case_id is not None
    first = cases.case_id
    app.solver.maxh.ui_model_value = 0.125
    app.state.geometry = np.arange(10000.0)  # a blob
    app.state.list("log").append("a")
    app.name = "first"
    cases.close()  # commits the pending edits

    cases = local()
    app = cases.start()
    assert cases.case_id == first and app.name == "first"
    assert app.solver.maxh.ui_model_value == 0.125
    np.testing.assert_array_equal(app.state.geometry, np.arange(10000.0))
    assert list(app.state.list("log")) == ["a"]

    # case list: new, copy, rename, open, delete
    other = cases.new("second")
    assert other is cases.app and other.solver.maxh.ui_model_value == 0.25
    second = cases.case_id
    copy = cases.copy(first)
    cases.rename(copy, "copy of first")
    listed = {c["id"]: c for c in cases.list()}
    assert set(listed) == {first, second, copy}
    assert listed[second]["current"] and listed[copy]["name"] == "copy of first"
    app = cases.open(copy)
    assert app.solver.maxh.ui_model_value == 0.125
    np.testing.assert_array_equal(app.state.geometry, np.arange(10000.0))
    cases.delete(copy)
    assert cases.case_id != copy and copy not in {c["id"] for c in cases.list()}
    cases.close()

    cases = local()
    cases.start()
    assert cases.case_id in (first, second)
    cases.close()


def test_export_import_round_trip(tmp_path):
    cases = local()
    app = cases.start()
    app.state.geometry = np.full(8000, 2.0)
    app.solver.maxh.ui_model_value = 0.5
    app.name = "exported"
    # the job's data is in the case
    job = app.solver.mesh()
    run_queued(cases.server, JobsApp)
    app.case_session.scheduler.run_pending()
    assert job.status == "succeeded" and app.solver.state.n == 10000
    path = tmp_path / "case.ngcase"
    cases.export(path)

    other = local(path=tmp_path / "other.sqlite")
    case_id = other.import_file(path)
    app2 = other.open(case_id)
    assert app2.name == "exported" and app2.solver.maxh.ui_model_value == 0.5
    np.testing.assert_array_equal(app2.state.geometry, np.full(8000, 2.0))
    assert app2.solver.state.n == 10000 and app2.solver.state.mesh.shape == (
        10000,
    )
    # merged results are part of the state, their runs are not exported
    assert len(app2.runs(app2.solver.mesh)) == 0
    other.close()
    cases.close()


def test_import_of_the_previous_local_mode(tmp_path, monkeypatch):
    monkeypatch.setattr(
        basecomponent, "_local_storage_path", tmp_path / "cache"
    )
    env = set_environment(EnvironmentType.STANDALONE, have_backend=False)
    env.frontend.update_component = lambda *a, **k: None
    old = JobsApp()
    old.name = "old model"
    old.solver.maxh.ui_model_value = 0.75
    old.storage.set("table", {"rows": [1, 2]})
    old.solver.storage.set("obj", {1, 2}, use_pickle=True)
    with_data = old._dump_app(include_storage_data=True)
    old._save_storage_local()
    without_data = old._dump_app()

    env.data_layer = True
    cases = local()
    for data in (with_data, without_data):
        case_id = cases.import_bytes(pickle.dumps(data))
        app = cases.app
        assert cases.case_id == case_id and app.name == "old model"
        assert app.solver.maxh.ui_model_value == 0.75
        assert app.state.ns("storage").table == {"rows": [1, 2]}
        assert app.solver.state.ns("storage").obj == {1, 2}
        assert "table" not in app.state
        assert app.storage.get("table") == {"rows": [1, 2]}
    cases.close()


def test_trees_share_nodes(tmp_path):
    """A commit stores only the changed components; long sequences are kept
    in pages; a new server instance (cold caches) reads the same state"""
    path = tmp_path / "t.sqlite"
    server = SQLiteServer(path, poll_interval=None)
    store = server.client("alice")
    ops = [Op("set", (f"c{i}", "input", "x"), "v" * 50) for i in range(200)]
    ops.append(Op("set", ("big", "state", "v"), "x" * 10000))
    case = store.create_case(1, "c", ops)

    def nodes():
        with server._read() as c:
            return c.execute("SELECT COUNT(*) FROM node").fetchone()[0]

    before, head = nodes(), case.head
    for i in range(50):
        head = store.commit(
            case.id, head, [Op("set", ("c7", "input", "x"), i)]
        ).revision
    assert nodes() - before <= 2 * 50 + 2
    for i in range(25):
        head = store.commit(
            case.id,
            head,
            [
                Op("append", ("log", "state", "lines"), i * 100 + j)
                for j in range(100)
            ],
        ).revision
    with server._read() as c:
        pages = c.execute(
            'SELECT COUNT(*) FROM node WHERE body LIKE \'%"k":"page"%\''
        ).fetchone()[0]
    assert pages < 40
    expected = store.state(case.id)
    server.close()

    server = SQLiteServer(path, poll_interval=None)
    store = server.client("alice")
    state = store.state(case.id)
    assert state["children"] == expected["children"]
    lines = flatten(state)[("log", "state", "lines")]
    assert list(lines.items) == list(range(2500))
    assert flatten(state)[("big", "state", "v")] == "x" * 10000
    server.close()


WRITER = textwrap.dedent("""
    import sys
    from ngapp.store import Op
    from ngapp.store.sqlite import SQLiteServer
    server = SQLiteServer(sys.argv[1], poll_interval=None)
    store = server.client("alice")
    case_id, n, tag = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    for i in range(n):
        head = store.case(case_id).head
        store.commit(case_id, head, [
            Op("set", (tag, "state", f"k{i}"), i),
            Op("append", ("log", "state", "lines"), f"{tag}{i}")])
    server.close()
    """)


def test_two_processes_commit_to_one_case(tmp_path):
    path = tmp_path / "shared.sqlite"
    server = SQLiteServer(path, poll_interval=0.02)
    store = server.client("alice")
    case = store.create_case(1, "c")
    seen = []
    store.subscribe([case.id], store.state(case.id)["event_seq"], seen.append)
    n = 30
    procs = [
        subprocess.Popen(
            [
                sys.executable,
                "-c",
                WRITER,
                str(path),
                str(case.id),
                str(n),
                tag,
            ],
            env=dict(
                os.environ, PYTHONPATH=os.pathsep.join(p for p in sys.path if p)
            ),
        )
        for tag in ("p", "q")
    ]
    base = case.head
    for i in range(n):  # always the same base: the commits are merged
        store.commit(
            case.id, base, [Op("append", ("log", "state", "lines"), f"m{i}")]
        )
    assert [p.wait(60) for p in procs] == [0, 0]
    state = flatten(store.state(case.id))
    for tag in ("p", "q"):
        assert all(state[(tag, "state", f"k{i}")] == i for i in range(n))
    lines = list(state[("log", "state", "lines")].items)
    assert len(lines) == 3 * n
    for tag in ("p", "q", "m"):
        assert [x for x in lines if x[0] == tag] == [
            f"{tag}{i}" for i in range(n)
        ]
    assert revision_count(server, case.id) == 1 + 3 * n
    end = time.monotonic() + 10
    while len([e for e in seen if e.type == "case.head"]) < 3 * n:
        assert time.monotonic() < end
        time.sleep(0.05)
    seqs = [e.seq for e in seen]
    assert seqs == sorted(seqs) and len(set(seqs)) == len(seqs)
    server.close()
