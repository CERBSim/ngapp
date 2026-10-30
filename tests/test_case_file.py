"""A case as one file: export and import through the store interface
(FULL mode, here on the SQLite store) in the format of the local mode"""

import numpy as np
import pytest

from ngapp import case_file
from ngapp.app import App, AppConfig
from ngapp.components import Col, QInput
from ngapp.jobs import compute
from ngapp.local_cases import LocalCases
from ngapp.state import CaseSession
from ngapp.utils import EnvironmentType, set_environment
from helpers import run_jobs as run_queued


class FileApp(App):
    def __init__(self):
        super().__init__()
        self.maxh = QInput(id="maxh", ui_model_value=0.5)
        self.component = Col(self.maxh, id="main")

    @compute
    def solve(self):
        self.state.mesh = np.arange(10000, dtype=np.float64)

    @compute(merge=False)
    def check(self):
        self.state.check = "ok"


config = AppConfig(FileApp, name="case file", version="1")


@pytest.fixture(autouse=True)
def env():
    env = set_environment(EnvironmentType.STANDALONE, have_backend=False)
    env.frontend.update_component = lambda *a, **k: None
    env.data_layer = True
    yield env
    env.data_layer = False


def test_export_and_import_through_the_store(tmp_path, server, sched):
    app = FileApp()
    session = CaseSession.create(
        app, server.client("alice"), app_id=7, name="case", scheduler=sched
    )
    app.maxh.ui_model_value = 0.25
    app.state.geometry = np.full(8000, 2.0)  # a blob
    app.solve()
    app.check()
    run_queued(server, FileApp)
    sched.run_pending()
    assert app.state.mesh[-1] == 9999.0 and "check" not in app.state

    data = case_file.export_case(session.store, session.case_id)
    info = case_file.import_case(server.client("bob"), 8, data, name="copy")
    assert info.name == "copy" and info.app_id == 8
    b = FileApp()
    CaseSession.open(b, server.client("bob"), info.id, scheduler=sched)
    assert b.maxh.ui_model_value == 0.25
    assert b.state.geometry.shape == (8000,) and b.state.mesh[-1] == 9999.0
    # the result of the run without merge is applied to the values
    assert b.state.check == "ok"

    # the local mode reads the file, with the run
    cases = LocalCases(config, tmp_path / "cases.sqlite", jobs=None)
    try:
        case_id = cases.import_bytes(data)
        cases.open(case_id)
        assert cases.app.maxh.ui_model_value == 0.25
        assert cases.app.state.mesh[-1] == 9999.0
        [run] = cases.store.runs(case_id)
        assert run.function == "__app__.check" and "check" not in cases.app.state
        # and a file of the local mode imports into the store
        local = cases.export_bytes(case_id)
    finally:
        cases.close()
    info = case_file.import_case(server.client("alice"), 7, local)
    c = FileApp()
    CaseSession.open(c, server.client("alice"), info.id, scheduler=sched)
    assert c.state.geometry[0] == 2.0 and c.state.mesh[-1] == 9999.0
    assert c.state.check == "ok"

    with pytest.raises(ValueError):
        case_file.import_case(
            server.client("alice"), 7, _zip({"format": "x/1"})
        )


def _zip(manifest):
    import io
    import json
    import zipfile

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("case.json", json.dumps(manifest))
    return buf.getvalue()
