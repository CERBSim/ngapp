from __future__ import annotations

from pathlib import Path

import orjson

from ngapp.utils import SettingsFile, UserSettings


def _read_json(path: Path) -> dict:
    return orjson.loads(path.read_bytes())


def test_usersettings_uses_app_subfolder_and_config_json(tmp_path, monkeypatch):
    """UserSettings should store data in <config_root>/<app_id>/config.json.

    The config root itself is provided by platformdirs.user_config_dir, which
    we monkeypatch to a temporary directory for the test.
    """

    # Point ngapp's config root to a temporary directory
    def fake_user_config_dir(app_name: str) -> str:
        return str(tmp_path / app_name)

    monkeypatch.setattr(
        "ngapp.utils.user_config_dir", fake_user_config_dir, raising=True
    )

    app_id = "tests.MyApp"
    settings = UserSettings(app_id=app_id)

    # Write a value and ensure it is persisted to config.json
    settings.set("nthreads", 8)

    # Directory and config path
    expected_root = tmp_path / "ngapp"
    expected_dir = expected_root / app_id
    expected_config = expected_dir / "config.json"

    assert settings.directory == expected_dir
    assert settings.path == expected_config
    assert expected_config.is_file()

    data = _read_json(expected_config)
    assert data == {"nthreads": 8}

    # A fresh instance with the same app_id should see the stored value
    settings_again = UserSettings(app_id=app_id)
    assert settings_again.get("nthreads", default=None) == 8


def test_usersettings_additional_json_files(tmp_path, monkeypatch):
    """UserSettings.json_file should manage extra JSON files in same folder."""

    def fake_user_config_dir(app_name: str) -> str:
        return str(tmp_path / app_name)

    monkeypatch.setattr(
        "ngapp.utils.user_config_dir", fake_user_config_dir, raising=True
    )

    app_id = "tests.MyApp"
    settings = UserSettings(app_id=app_id)

    extra = settings.json_file("recent_projects")
    extra.set("items", ["proj1", "proj2"])

    expected_root = tmp_path / "ngapp"
    expected_dir = expected_root / app_id
    expected_extra = expected_dir / "recent_projects.json"

    assert extra.path == expected_extra
    assert expected_extra.is_file()

    data = _read_json(expected_extra)
    assert data == {"items": ["proj1", "proj2"]}


def test_settingsfile_update_handler_uses_event_value(tmp_path):
    """SettingsFile.update should store event.value (or the raw value)."""

    cfg = SettingsFile(tmp_path / "other.json")

    handler = cfg.update("key")

    class Event:
        def __init__(self, value):
            self.value = value

    # With an Event that has .value
    handler(Event("abc"))
    assert cfg.get("key") == "abc"

    # With a raw value (no .value attribute)
    handler("xyz")
    assert cfg.get("key") == "xyz"
