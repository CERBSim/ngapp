"""Cases of the local app mode

The local app keeps its cases in a SQLite store per app, by default
~/.local/share/ngapp/<app>/cases.sqlite (NGAPP_DATA_DIR or XDG_DATA_HOME
replace ~/.local/share/ngapp, or an explicit path). LocalCases opens the last
opened case (or a new one) in the app, which autosaves through its
CaseSession, and offers a case list (new, open, copy, rename, delete) for the
standalone frontend, export and import of a case as one file (state, results
of runs and blobs) and the import of files of the previous local mode (pickled
App._dump_app data, storage values from ~/.cache/webapp_local_storage).
"""

import datetime
import io
import json
import logging
import os
import pickle
import re
import sys
import threading
import zipfile
from pathlib import Path

from .state import CaseSession, storage_set
from .store.sqlite import SQLiteServer
from .store.tree import CASE_NAME
from .store.types import CaseDeletedError, NotFoundError, Op

logger = logging.getLogger("ngapp.local_cases")

CASE_FORMAT = "ngapp.case/1"
CASE_SUFFIX = ".ngcase"
USER = "local"


def data_dir() -> Path:
    base = os.environ.get("NGAPP_DATA_DIR")
    if base:
        return Path(base)
    xdg = os.environ.get("XDG_DATA_HOME")
    return (Path(xdg) if xdg else Path.home() / ".local" / "share") / "ngapp"


def store_path(app_config) -> Path:
    name = app_config.name or app_config.python_class.rpartition(".")[0]
    name = re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("._") or "app"
    return data_dir() / name / "cases.sqlite"


def _hex(h: str) -> str:
    return h.removeprefix("sha256:")


class LocalCases:
    """The cases of one app in the local app mode and the app showing one

    on_app(app) is called when another case (a new app instance) is shown.
    Methods return JSON values, so the frontend can call them through the
    websocket link (exposed as "ngapp_cases").
    """

    def __init__(
        self,
        app_config,
        path=None,
        *,
        user: str = USER,
        jobs: str | None = "process",
        max_jobs: int | None = None,
        app_args: dict | None = None,
        on_app=None,
        session_options: dict | None = None,
        poll_interval: float | None = 0.2,
    ):
        self.config = app_config
        self.path = Path(path) if path else store_path(app_config)
        self.user = user
        self.app_args = dict(app_args or {})
        self.on_app = on_app
        self.session_options = dict(session_options or {})
        if max_jobs is None:
            max_jobs = int(os.environ.get("NGAPP_LOCAL_MAX_JOBS", "2"))
        self.server = SQLiteServer(
            self.path,
            jobs=jobs,
            job_data=self._job_data(),
            max_jobs=max_jobs,
            poll_interval=poll_interval,
        )
        self.store = self.server.client(user)
        self.app = None
        self._lock = threading.RLock()

    @property
    def app_id(self) -> int:
        return self.config.id

    @property
    def case_id(self) -> int | None:
        session = getattr(self.app, "case_session", None)
        return None if session is None else session.case_id

    def _job_data(self) -> dict:
        cfg = self.config
        return {
            "app": {
                "id": cfg.id,
                "name": cfg.name,
                "version": cfg.version,
                "python_class": cfg.python_class,
            },
            "sys_path": [p for p in sys.path if p],
            "cwd": os.getcwd(),
        }

    # -- the shown case --

    def _new_app(self, reload_modules=()):
        from .app import create_app

        return create_app(
            self.config,
            {},
            reload_python_modules=list(reload_modules),
            app_args=self.app_args,
        )

    def _close_current(self):
        app, self.app = self.app, None
        session = getattr(app, "case_session", None)
        if session is None:
            return
        try:
            if not session.blocked:
                session.commit()
        except Exception as e:
            logger.error("Saving case %s failed: %r", session.case_id, e)
        session.close()

    def _show(self, app):
        self.app = app
        self.server.set_meta(
            f"last_case:{self.user}", str(app.case_session.case_id)
        )
        if self.on_app is not None:
            self.on_app(app)
        self.server.start_jobs()
        return app

    def _open_session(self, app, case_id):
        return CaseSession.open(
            app, self.store, case_id, **self.session_options
        )

    def _create_session(self, app, name):
        return CaseSession.create(
            app,
            self.store,
            app_id=self.app_id,
            name=name,
            **self.session_options,
        )

    def start(self):
        """Show the last opened case, or a new one"""
        last = self.server.get_meta(f"last_case:{self.user}")
        if last:
            try:
                return self.open(int(last))
            except (NotFoundError, CaseDeletedError):
                pass
        return self.new()

    def new(self, name: str | None = None):
        with self._lock:
            self._close_current()
            app = self._new_app()
            self._create_session(app, name or "untitled")
            return self._show(app)

    def open(self, case_id: int):
        with self._lock:
            self.store.case(case_id)
            self._close_current()
            app = self._new_app()
            self._open_session(app, case_id)
            return self._show(app)

    def reload(self, reload_modules=()):
        """New app instance of the reloaded code on the same case (dev mode)"""
        with self._lock:
            case_id = self.case_id
            self._close_current()
            app = self._new_app(reload_modules)
            if case_id is None:
                self._create_session(app, "untitled")
            else:
                self._open_session(app, case_id)
            return self._show(app)

    def save(self) -> int | None:
        """Commit the pending edits of the shown case"""
        session = getattr(self.app, "case_session", None)
        return None if session is None else session.commit()

    def close(self):
        with self._lock:
            self._close_current()
        self.server.close()

    # -- case list --

    def list(self) -> list[dict]:
        current = self.case_id
        out = []
        for info in self.store.cases(self.app_id):
            created, updated = self.server.case_times(info.id)
            out.append(
                {
                    "id": info.id,
                    "name": info.name,
                    "created_at": created,
                    "updated_at": updated,
                    "current": info.id == current,
                }
            )
        return out

    def copy(self, case_id: int, name: str | None = None) -> int:
        if case_id == self.case_id:
            self.save()
        src = self.store.case(case_id)
        return self.store.copy_case(
            case_id, name=name or f"{src.name} (copy)"
        ).id

    def rename(self, case_id: int, name: str):
        if case_id == self.case_id:
            self.app.name = name
            self.save()
            return
        head = self.store.case(case_id).head
        self.store.commit(case_id, head, [Op("set", CASE_NAME, name)])

    def delete(self, case_id: int):
        """Delete a case; if it is shown, the most recent other case (or a new
        one) is shown instead"""
        with self._lock:
            self.store.case(case_id)
            current = case_id == self.case_id
            if current:
                session = self.app.case_session
                session.close()
                self.app = None
            self.server.delete_case(case_id)
            if current:
                others = self.store.cases(self.app_id)
                if others:
                    self.open(others[0].id)
                else:
                    self.new()

    # -- export and import --

    def export_bytes(self, case_id: int | None = None) -> bytes:
        buf = io.BytesIO()
        self.export(buf, case_id)
        return buf.getvalue()

    def export(self, target, case_id: int | None = None):
        """Write a case as one file: case.json (state, results of runs, blob
        encodings) and blobs/<hex>"""
        case_id = self.case_id if case_id is None else case_id
        if case_id == self.case_id:
            self.save()
        data, encs = self.server.export_case(self.user, case_id)
        manifest = {
            "format": CASE_FORMAT,
            "app": {"name": self.config.name, "version": self.config.version},
            "exported_at": datetime.datetime.now(datetime.UTC).isoformat(),
            **data,
            "blobs": encs,
        }
        with zipfile.ZipFile(target, "w") as zf:
            zf.writestr(
                "case.json",
                json.dumps(manifest),
                compress_type=zipfile.ZIP_DEFLATED,
            )
            for h in sorted(encs):
                zf.write(self.server.blob_path(h), f"blobs/{_hex(h)}")

    def import_bytes(self, data: bytes, name: str | None = None) -> int:
        """Import a case file or a file of the previous local mode; returns
        the new case's id (the shown case changes only for the latter)"""
        if data[:2] == b"PK":
            return self._import_case_file(io.BytesIO(data), name)
        return self.import_legacy(pickle.loads(data), name)

    def import_file(self, path, name: str | None = None) -> int:
        return self.import_bytes(Path(path).read_bytes(), name)

    def _import_case_file(self, source, name=None) -> int:
        with zipfile.ZipFile(source) as zf:
            manifest = json.loads(zf.read("case.json"))
            fmt, _, major = str(manifest.get("format", "")).partition("/")
            if fmt != "ngapp.case" or major != "1":
                raise ValueError(
                    f"unsupported case file {manifest.get('format')!r}"
                )
            names = set(zf.namelist())

            def read_blob(h):
                entry = f"blobs/{_hex(h)}"
                return zf.read(entry) if entry in names else None

            if name is not None:
                manifest["state"].setdefault("__case__", {}).setdefault(
                    "meta", {}
                )["name"] = name
            return self.server.import_case(
                self.user, manifest, read_blob, app_id=self.app_id
            )

    def import_legacy(self, data: dict, name: str | None = None) -> int:
        """Import a model saved by the previous local mode (a pickle of
        App._dump_app()): props and storage of its components; storage values
        missing in the file are taken from ~/.cache/webapp_local_storage. The
        imported case is shown."""
        with self._lock:
            self._close_current()
            app = self._new_app()
            metadata = dict(data.get("metadata") or {})
            metadata.pop("id", None)
            name = name or metadata.get("name") or "imported"
            session = self._create_session(app, name)
            app._load_app({**data, "metadata": metadata}, update_frontend=False)
            app.name = name
            app.file_data.id = session.case_id
            lost = _storage_to_state(app)
            if lost:
                logger.warning(
                    "Storage values not found in the file or the old cache: %s",
                    lost,
                )
            session.commit(kind="import")
            self._show(app)
            return session.case_id

    # -- file pickers of the frontend --

    def save_file(self, app=None):
        """Export the shown case through the browser's save file picker"""
        from .utils import get_environment

        app = app or self.app
        write = get_environment().begin_save_file_local(
            (app.name or "untitled") + CASE_SUFFIX
        )
        if write is None:
            return
        try:
            write(self.export_bytes())
        except Exception as e:
            app._notify(f"Export failed: {e}", type="negative", timeout=6000)
            raise
        app._notify("Case exported.", type="positive", timeout=2500)

    def load_file(self):
        """Import a file chosen in the browser and show the imported case"""
        from .utils import get_environment

        picked = get_environment().load_file_local(
            {"accept": f"{CASE_SUFFIX},.sav"}
        )
        if picked is None:
            return
        _, data = picked
        try:
            case_id = self.import_bytes(data)
            if case_id != self.case_id:
                self.open(case_id)
        except Exception as e:
            if self.app is not None:
                self.app._notify(
                    f"Could not import the file: {e}",
                    type="negative",
                    timeout=6000,
                )
            raise


def _storage_to_state(app) -> list[str]:
    """Move the values of the old Storage of all components into their state;
    returns the entries whose value is missing"""
    from .components import basecomponent

    lost = []

    def visit(comp):
        storage = comp.__dict__.get("storage")
        if storage is None or not comp._id:
            return
        for key, entry in list(storage._metadata.entries.items()):
            if key in storage._data:
                value = storage._data[key]
            else:
                path = basecomponent._local_storage_path / entry.hash
                if not path.exists():
                    lost.append(f"{comp._fullid}/{key}")
                    continue
                value = storage._decode(path.read_bytes(), entry.type_)
            if entry.type_ == "pickle":
                comp.state.set(key, pickle.loads(value), pickle=True)
            else:
                storage_set(comp.state, key, value)

    app._recurse(visit, True, set())
    return lost
