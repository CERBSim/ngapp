from pathlib import Path

import pytest
from helpers import ManualScheduler

import ngapp.e2e_webgpu as e2e_webgpu
from ngapp.store.sqlite import SQLiteServer

pytest_plugins = ["ngapp.e2e_webgpu"]

TESTS_DIR = Path(__file__).parent

e2e_webgpu.configure(
    output_dir=TESTS_DIR / "output",
    baseline_dir=TESTS_DIR / "baselines",
)


@pytest.fixture(autouse=True)
def _local_data_dir(tmp_path, monkeypatch):
    """Cases of the local app mode go to a temporary directory"""
    monkeypatch.setenv("NGAPP_DATA_DIR", str(tmp_path / "ngapp-data"))


@pytest.fixture
def server(tmp_path):
    server = SQLiteServer(tmp_path / "cases.sqlite", poll_interval=None)
    yield server
    server.close()


@pytest.fixture
def sched():
    return ManualScheduler()


@pytest.fixture
def job_sched():
    return ManualScheduler()
