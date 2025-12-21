from __future__ import annotations

from ngapp.test_utils import load_case, snapshot, standalone_app_test
from tests.local_app_demo.app import InputChangeApp


@standalone_app_test
def test_snapshot_roundtrip() -> None:
    """Verify that snapshot and load_case work for a simple ngapp App.

    This uses the small area demo app from tests/local_app_demo and stores
    snapshot data under tests/cases/snapshot_demo/default.
    """

    # First, write reference data and (potential) local storage
    app = InputChangeApp()
    snapshot(
        app,
        folder_path="snapshot_demo/default",
        write_data=True,
        keep_storage=True,
    )

    # Then, create a fresh instance and compare against the stored snapshot
    app_again = InputChangeApp()
    snapshot(
        app_again,
        folder_path="snapshot_demo/default",
        check_data=True,
        check_storage=True,
    )

    # Finally, ensure load_case can load the stored data without error
    data = load_case(app_again, folder_path="snapshot_demo/default", load_storage=True)
    assert isinstance(data, dict)
