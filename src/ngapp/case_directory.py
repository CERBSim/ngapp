"""The cases of the app as the case list component sees them

CaseDirectory is what CaseList calls: list, open, rename, copy, delete,
export and import of a case file and (on the platform) sharing. In the
browser of the platform the operations go through the JS interface
"platformCases" of the main thread, in the local app mode through
LocalCases. Export and import run here, on the case store of the session.
"""

from typing import Optional

CASE_SUFFIX = ".ngcase"


class CaseDirectory:
    """Rows are dicts: id, name, created_at, modified_at (ISO text or epoch
    seconds), access (owner, write, read) and current (the open case)"""

    can_share = False

    def list(self) -> list[dict]:
        raise NotImplementedError

    def open(self, case_id: Optional[int]):
        """Show the case (None: a new case) in place of the current one"""
        raise NotImplementedError

    def rename(self, case_id: int, name: str):
        raise NotImplementedError

    def revisions(self, case_id: int) -> list[dict]:
        """Named versions: id, name, created_at"""
        return []

    def copy(self, case_id: int, name: str, revision: Optional[int] = None) -> int:
        raise NotImplementedError

    def delete(self, case_id: int):
        raise NotImplementedError

    def export(self, case_id: int) -> bytes:
        raise NotImplementedError

    def import_(self, data: bytes, name: Optional[str] = None) -> int:
        raise NotImplementedError

    def shares(self, case_id: int) -> list[dict]:
        """user_id, write"""
        return []

    def lookup_user(self, query: str) -> dict:
        """id, name or error"""
        raise NotImplementedError

    def share(self, case_id: int, user_id: str, write: bool):
        raise NotImplementedError

    def unshare(self, case_id: int, user_id: str):
        raise NotImplementedError


class PlatformCases(CaseDirectory):
    """The platform's case API, called in the main thread of the browser"""

    can_share = True

    def __init__(self, session):
        from .utils import get_environment

        self.session = session
        self.js = get_environment().link.get("platformCases")

    def _call(self, name, *args):
        result = getattr(self.js, name)(*args)
        if isinstance(result, dict) and result.get("error"):
            raise RuntimeError(result["error"])
        return result

    def list(self):
        rows = self._call("list") or []
        for row in rows:
            row["current"] = row["id"] == self.session.case_id
        return rows

    def open(self, case_id):
        self._call("open", case_id)

    def rename(self, case_id, name):
        if case_id == self.session.case_id:
            # the open case: its session commits the name
            self.session.app.file_data.name = name
            self.session.schedule_autosave()
        else:
            self._call("rename", case_id, name)

    def revisions(self, case_id):
        return self._call("revisions", case_id) or []

    def copy(self, case_id, name, revision=None):
        if case_id == self.session.case_id:
            self._save()
        return self._call("copy", case_id, revision, name)["id"]

    def delete(self, case_id):
        self._call("remove", case_id)

    def _save(self):
        s = self.session
        if not s.held_edits and s.status in ("pending", "saving", "offline", "error"):
            s.commit()

    def export(self, case_id):
        from . import case_file

        if case_id == self.session.case_id:
            self._save()
        cfg = self.session.app._config
        return case_file.export_case(
            self.session.store, case_id, {"name": cfg.name, "version": cfg.version}
        )

    def import_(self, data, name=None):
        from . import case_file

        app_id = self.session.app_id
        if app_id is None:
            app_id = self.session.app._config.id
        return case_file.import_case(self.session.store, app_id, data, name).id

    def shares(self, case_id):
        return self._call("shares", case_id) or []

    def lookup_user(self, query):
        # an unknown user is a result, not a failure
        return self.js.lookupUser(query)

    def share(self, case_id, user_id, write):
        self._call("share", case_id, user_id, write)

    def unshare(self, case_id, user_id):
        self._call("unshare", case_id, user_id)


class LocalDirectory(CaseDirectory):
    """The cases of the local app mode (SQLite store per app)"""

    def __init__(self, cases):
        self.cases = cases

    def list(self):
        return [
            {
                "id": c["id"],
                "name": c["name"],
                "created_at": c["created_at"],
                "modified_at": c["updated_at"],
                "access": "owner",
                "current": c["current"],
            }
            for c in self.cases.list()
        ]

    def open(self, case_id):
        if case_id is None:
            self.cases.new()
        else:
            self.cases.open(case_id)

    def rename(self, case_id, name):
        self.cases.rename(case_id, name)

    def copy(self, case_id, name, revision=None):
        return self.cases.copy(case_id, name)

    def delete(self, case_id):
        self.cases.delete(case_id)

    def export(self, case_id):
        return self.cases.export_bytes(case_id)

    def import_(self, data, name=None):
        return self.cases.import_bytes(data, name)


def available(session) -> bool:
    """A case directory exists for the case session (not for jobs and the
    static standalone mode)"""
    from .utils import get_environment, is_pyodide

    if session is None or not hasattr(session, "on_info"):
        return False
    env = get_environment()
    return env.local_cases is not None or (is_pyodide() and env.have_backend)


def case_directory(session) -> Optional[CaseDirectory]:
    """The case directory of the app of a case session, None without one"""
    from .utils import get_environment

    if not available(session):
        return None
    env = get_environment()
    if env.local_cases is not None:
        return LocalDirectory(env.local_cases)
    return PlatformCases(session)
