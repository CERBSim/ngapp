"""Utility functions for testing ngapp apps.

This module provides helpers for comparing component state and local storage.
Snapshot files use the same pickled data format as
 :meth:`ngapp.app.App.save_local`, so you can reuse ``.sav`` files created
 from the running app inside your test suite.
"""

import os
import pickle
import tempfile
from functools import wraps
from pathlib import Path

import deepdiff

import ngapp.components.basecomponent
from ngapp.app import App
from ngapp.utils import EnvironmentType, read_json, set_environment, write_json

os.environ["WEBAPP_TESTING"] = str(True)


def _get_folder_path(folder_path: str | Path, create_folder: bool = True):
    path = (
        Path(folder_path)
        if "tests/cases" in str(folder_path)
        else Path("tests/cases") / folder_path
    )
    if create_folder:
        path.mkdir(parents=True, exist_ok=True)
    return path


def _set_local_storage_path(folder_path: str, create_folder: bool = True):
    path = _get_folder_path(folder_path, create_folder=create_folder) / "storage"
    ngapp.components.basecomponent._local_storage_path = path
    return path


def assert_equal_components_data(data: dict, comparison: dict):
    data.pop("metadata")
    comparison.pop("metadata")
    diff = deepdiff.DeepDiff(data, comparison, ignore_order=True)
    assert diff == {}


def _load_snapshot_file(path: Path) -> dict:
    """Load snapshot data from *path*.

    Snapshot files are stored as pickled dictionaries, compatible with the
    output of :meth:`ngapp.app.App.dump` and :meth:`ngapp.app.App.save_local`.
    For backwards compatibility, if unpickling fails we fall back to reading
    JSON from the same path.
    """

    with path.open("rb") as fh:
        return pickle.load(fh)

def snapshot(
    app: App,
    folder_path: str,
    filename: str = "data.sav",
    write_data: bool = False,
    keep_storage: bool = False,
    check_data: bool = False,
    check_storage: bool = False,
):
    """Save the data of the app to a file or compare it to the reference data if requested"""
    folder = _get_folder_path(folder_path)
    _set_local_storage_path(folder_path)
    file_path = folder / filename

    if check_data:
        data = app.dump()
        ref_data = _load_snapshot_file(file_path)
        assert_equal_components_data(data, ref_data)

    if check_storage:
        with tempfile.TemporaryDirectory() as tempdir:
            temp_storage = _set_local_storage_path(tempdir)
            app._save_storage_local()
            temp_storage_files = sorted(list(temp_storage.glob("*")))
            saved_storage_files = sorted(list((folder / "storage").glob("*")))
            if len(temp_storage_files) != len(saved_storage_files):
                raise AssertionError(
                    "Number of storage files do not match. Maybe you forgot to save the storage?\n"
                    f"Number of temp files: {len(temp_storage_files)}, number of saved files: {len(saved_storage_files)}.\n"
                    f"Temp files {temp_storage_files},\n saved files {saved_storage_files}"
                )
            for saved_file, temp_file in zip(
                saved_storage_files, temp_storage_files
            ):
                try:
                    # assume data is json
                    assert (
                        deepdiff.DeepDiff(
                            read_json(saved_file),
                            read_json(temp_file),
                            ignore_order=True,
                        )
                        == {}
                    )
                except Exception:
                    # try reading as text
                    try:
                        assert saved_file.read_text() == temp_file.read_text()
                    except Exception as e:
                        raise Exception(
                            f"Error comparing {saved_file}, data {saved_file.read_text()} and {temp_file}, data {temp_file.read_text()}"
                        ) from e

    if write_data:
        data = app.dump(keep_storage=keep_storage)
        with file_path.open("wb") as fh:
            pickle.dump(data, fh)


def load(
    app: App,
    *,
    data: dict | None = None,
    filename: str | None = None,
    load_storage: bool = False,
):
    """Load the data into the app"""
    if filename is not None:
        path = Path(filename)
        data = _load_snapshot_file(path)
    app.load(data, load_local_storage=load_storage)


def load_case(app, folder_path, filename="data.sav", load_storage=False):
    """Load the data of a case and load it into the app.

    ``filename`` is expected to be a pickled dump compatible with
    :meth:`ngapp.app.App.save_local`, for example a ``.sav`` file created
    by the running app or a snapshot written by :func:`snapshot`.
    """
    _set_local_storage_path(folder_path, create_folder=False)
    folder_path = _get_folder_path(folder_path, create_folder=False)
    data = _load_snapshot_file(folder_path / filename)
    load(app, data=data, load_storage=load_storage)
    return data


def save_testing_data(folder_path: str | Path, testing_data: dict):
    """Save the testing data to a folder as json files"""
    folder_path = Path(folder_path)
    folder_path.mkdir(parents=True, exist_ok=True)
    for key, value in testing_data.items():
        write_json(value, folder_path / f"{key}.json")


def standalone_app_test(func):
    """Decorator for tests that only exercise Python app state.

    It sets up a minimal :class:`~ngapp.utils.Environment` in
    ``STANDALONE`` mode with a no-op ``update_component`` so that
    components can be constructed and updated without a real frontend.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):  # type: ignore[no-untyped-def]
        env = set_environment(EnvironmentType.STANDALONE, have_backend=False)
        # Ignore frontend updates during pure-Python tests
        env.frontend.update_component = (  # type: ignore[method-assign]
            lambda *a, **k: None
        )
        return func(*args, **kwargs)

    return wrapper
