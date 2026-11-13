"""The case list of the app as a standard component: open (also by double
click on a row), new, rename, copy, delete, download and upload of case
files and sharing. The cases come from the case directory of the app's case
session (the platform's case API or the local cases)."""

import datetime

from ..case_directory import CASE_SUFFIX, case_directory
from ..state import session_of
from .helper_components import Div, Label, Row
from .qcomponents import (
    QBadge,
    QBtn,
    QCard,
    QCardActions,
    QCardSection,
    QDialog,
    QIcon,
    QInput,
    QItem,
    QItemLabel,
    QItemSection,
    QList,
    QMarkupTable,
    QOptionGroup,
    QSpace,
    QTd,
    QTh,
    QTooltip,
    QTr,
)

__all__ = ["CaseList"]

_FAILED = object()


def _when(value) -> str:
    if value in (None, ""):
        return ""
    try:
        if isinstance(value, (int, float)):
            t = datetime.datetime.fromtimestamp(value)
        else:
            t = datetime.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if t.tzinfo is not None:
            t = t.astimezone()
        return t.strftime("%Y-%m-%d %H:%M")
    except (ValueError, OSError, OverflowError):
        return str(value)


def _label(row) -> str:
    return row.get("name") or "untitled"


def _icon_button(icon, tooltip, handler, color=None):
    btn = QBtn(QTooltip(tooltip), ui_icon=icon, ui_flat=True, ui_dense=True,
               ui_round=True, ui_size="sm", ui_color=color)
    btn.on_click(handler)
    return btn


class CaseList(Div):
    """The cases of the app; on_open(case_id) after a case was opened (None:
    a new one). files=False leaves out download and upload of case files."""

    def __init__(self, on_open=None, files: bool = True, **kwargs):
        self._on_open = on_open
        self._files = files
        self._directory = None
        self._session = None
        upload = ([_icon_button("mdi-file-upload-outline",
                                f"Upload a case file ({CASE_SUFFIX})", self._upload)]
                  if files else [])
        header = Row(
            Label("Cases", ui_class="text-h6"), QSpace(),
            _icon_button("mdi-refresh", "Refresh", lambda: self.reload()),
            *upload,
            _icon_button("mdi-file-plus", "New case", lambda: self._open(None)),
            ui_style="align-items: center; gap: 4px;",
        )
        self._table = Div()
        self._dialog = QDialog(ui_model_value=False)
        super().__init__(header, self._table, self._dialog, **kwargs)
        self.on_mounted(self.reload)

    # -- data --

    def directory(self):
        session = session_of(self)
        if session is not self._session:
            self._session = session
            self._directory = case_directory(session)
        return self._directory

    def _notify(self, message, negative=True):
        app = self.app
        if app is not None:
            app._notify(message, type="negative" if negative else "positive",
                        timeout=6000 if negative else 2500)

    def _try(self, what, func, *args):
        """func(*args), _FAILED after telling the user"""
        try:
            return func(*args)
        except Exception as e:
            self._notify(f"{what} failed: {e}")
            return _FAILED

    def reload(self):
        d = self.directory()
        if d is None:
            self._table.ui_children = [Label("No cases here.", ui_class="text-grey-7")]
            return
        rows = self._try("Loading the cases", d.list_cases)
        if rows is _FAILED:
            return
        rows = sorted(rows, key=lambda r: r["id"], reverse=True)
        own = [r for r in rows if not r.get("owner_group_id")]
        group = [r for r in rows if r.get("owner_group_id")]
        self._table.ui_children = [self._rows_table(d, own)] + (
            [Label("Group results", ui_class="text-subtitle1 q-mt-md"), self._rows_table(d, group)]
            if group else [])

    def _rows_table(self, d, rows):
        head = QTr(*[QTh(t, ui_class="text-left") for t in
                     ("Name", "Created", "Modified", "")])
        return QMarkupTable(head, *[self._row(d, r) for r in rows], ui_flat=True,
                            ui_dense=True, ui_separator="horizontal",
                            ui_style="max-height: 60vh; overflow: auto;")

    def _row(self, d, row):
        name = [Label(_label(row), ui_class="text-weight-bold" if row.get("current") else "")]
        if row.get("transferred_at"):
            left = _when(row["transferred_at"])
            name.append(QBadge(ui_label=f"from {row.get('owner_name', '')}, left {left}",
                               ui_color="orange-8", ui_class="q-ml-sm"))
        if row.get("access", "owner") != "owner":
            name.append(QBadge(ui_label="shared" if row["access"] == "write" else "read only",
                               ui_color="grey-6", ui_class="q-ml-sm"))
        cells = [QTd(*name), QTd(_when(row.get("created_at"))),
                 QTd(_when(row.get("modified_at")))]
        for td in cells:
            td.on("dblclick", lambda _e, r=row: self._open(r["id"]))
        access = row.get("access", "owner")
        buttons = [_icon_button("edit", "Open", lambda _e, r=row: self._open(r["id"]))]
        if access != "read":
            buttons.append(_icon_button("mdi-cursor-text", "Rename",
                                        lambda _e, r=row: self._rename(r)))
        buttons.append(_icon_button("mdi-content-copy", "Copy",
                                    lambda _e, r=row: self._copy(r)))
        if self._files:
            buttons.append(_icon_button("mdi-file-download-outline", "Download as case file",
                                        lambda _e, r=row: self._download(r)))
        if access == "owner" and d.can_share:
            buttons.append(_icon_button("mdi-share-variant", "Share",
                                        lambda _e, r=row: self._share(r)))
        if access == "owner":
            buttons.append(_icon_button("delete", "Delete",
                                        lambda ev, r=row: self._delete(r, ev), "negative"))
        return QTr(*cells, QTd(*buttons, ui_class="text-right", ui_style="white-space: nowrap;"),
                   ui_class="cursor-pointer")

    # -- dialog --

    def _ask(self, title, body, on_ok, ok_label="OK", ok_color="primary"):
        """Show a dialog; on_ok() returns False to keep it open"""
        cancel = QBtn(ui_label="Cancel", ui_flat=True, ui_no_caps=True)
        ok = QBtn(ui_label=ok_label, ui_flat=True, ui_no_caps=True, ui_color=ok_color)

        def close():
            self._dialog.ui_model_value = False

        def accept():
            if on_ok() is not False:
                close()

        cancel.on_click(close)
        ok.on_click(accept)
        self._dialog.ui_children = [QCard(
            QCardSection(Label(title, ui_class="text-h6")),
            QCardSection(*body, ui_class="q-pt-none column", ui_style="gap: 8px;"),
            QCardActions(cancel, ok, ui_align="right"),
            ui_style="min-width: 380px; max-width: 90vw;",
        )]
        self._dialog.ui_model_value = True

    # -- actions --

    def _open(self, case_id):
        d = self.directory()
        if d is None:
            return
        if self._try("Opening the case", d.open, case_id) is _FAILED:
            return
        if self._on_open is not None:
            self._on_open(case_id)

    def _rename(self, row):
        name = QInput(ui_model_value=row.get("name") or "", ui_label="Name",
                      ui_dense=True, ui_autofocus=True)

        def ok():
            new = (name.ui_model_value or "").strip()
            if new and new != row.get("name"):
                self._try("Renaming", self.directory().rename, row["id"], new)
                self.reload()

        self._ask("Rename", [name], ok)

    def _copy(self, row):
        d = self.directory()
        versions = self._try("Loading the versions", d.revisions, row["id"])
        versions = [] if versions is _FAILED else versions
        body = []
        source = None
        if versions:
            source = QOptionGroup(
                ui_type="radio", ui_model_value=None,
                ui_options=[{"label": "Current state", "value": None}] + [
                    {"label": f"{v['name']} ({_when(v.get('created_at'))})", "value": v["id"]}
                    for v in versions])
            body += [Label(f'Copy of "{_label(row)}" from'), source]
        name = QInput(ui_model_value=f"{_label(row)} (copy)", ui_label="Name of the new case",
                      ui_dense=True)
        body.append(name)

        def ok():
            revision = source.ui_model_value if source is not None else None
            new_id = self._try("Copying", d.copy, row["id"],
                               (name.ui_model_value or "").strip() or f"{_label(row)} (copy)",
                               revision)
            if new_id is not _FAILED:
                self._open(new_id)

        self._ask("Copy", body, ok)

    def _delete(self, row, event=None):
        def ok():
            if self._try("Deleting", self.directory().delete, row["id"]) is _FAILED:
                return
            if row.get("current"):
                self._open(None)
            else:
                self.reload()

        value = getattr(event, "value", None)
        if isinstance(value, dict) and value.get("ctrlKey"):
            ok()
            return
        self._ask("Delete", [Label(f'Delete "{_label(row)}"? This cannot be undone.')],
                  ok, ok_label="Delete", ok_color="negative")

    def _download(self, row):
        from ..utils import get_environment

        data = self._try("Download", self.directory().export, row["id"])
        if data is _FAILED:
            return
        write = get_environment().begin_save_file_local(_label(row) + CASE_SUFFIX)
        if write is not None and self._try("Download", write, data) is not _FAILED:
            self._notify("Case file saved.", negative=False)

    def _upload(self):
        from ..utils import get_environment

        d = self.directory()
        if d is None:
            return
        picked = get_environment().load_file_local({"accept": CASE_SUFFIX})
        if picked is None:
            return
        file_name, data = picked
        name = file_name[: -len(CASE_SUFFIX)] if file_name.endswith(CASE_SUFFIX) else file_name
        case_id = self._try("Upload", d.import_, bytes(data), name or None)
        if case_id is not _FAILED:
            self._open(case_id)

    def _share(self, row):
        d = self.directory()
        shares = self._try("Loading the shares", d.shares, row["id"])
        shares = [] if shares is _FAILED else shares
        def describe(s):
            who = ("group " if s.get("group_id") else "") + (
                s.get("name") or s.get("user_id") or "")
            state = "" if s.get("active", True) else f", not working: {s.get('reason')}"
            return f"{who} ({'write' if s['write'] else 'read'}{state})"

        text = ", ".join(describe(s) for s in shares)
        # the members of the own groups, filtered here; others by their exact name (Search)
        targets = self._try("Loading the members of your groups", d.share_targets, row["id"], "")
        targets = [] if targets is _FAILED or isinstance(targets, dict) else targets
        user = QInput(ui_model_value="", ui_dense=True, ui_autofocus=True,
                      ui_label="Filter, or the exact name or e-mail address of someone else")
        error = Label("", ui_class="text-negative text-caption")
        listing = QList(ui_dense=True, ui_style="max-height: 50vh; overflow: auto;")

        def filtered(ev=None):
            query = ((ev.value if ev is not None else "") or "").strip().lower()
            error.ui_children = []
            shown = [t for t in targets
                     if query in t["name"].lower() or query in str(t["id"]).lower()]
            listing.ui_children = [self._target_item(row, t, shares) for t in shown] or [
                QItem(QItemSection(Label("Nobody of your groups matches, search for the "
                                         "exact name", ui_class="text-grey")))]

        user.on_update_model_value(filtered)
        filtered()
        body = ([Label(f"Shared with {text}.")] if text else []) + [user, error, listing]

        def found():
            query = (user.ui_model_value or "").strip()
            if not query:
                return False
            users = self._try("Searching", d.share_targets, row["id"], query)
            if users is _FAILED:
                return False
            if isinstance(users, dict) or not users:
                error.ui_children = [users.get("error") if users else f'Nobody found for "{query}".']
                return False
            self._pick(row, users, shares)
            return False  # the dialog shows the next step

        self._ask(f'Share "{_label(row)}"', body, found, ok_label="Search")

    def _target_item(self, row, who, shares):
        group = who.get("kind") == "group"
        caption = "no access to the app" if not who["access"] else (
            who["id"] if not group and who["name"] != who["id"] else "")
        item = QItem(
            QItemSection(QIcon(ui_name="mdi-account-group" if group else "mdi-account"),
                         ui_avatar=True),
            QItemSection(QItemLabel(f"Group {who['name']}" if group else who["name"]),
                         *([QItemLabel(caption, ui_caption=True)] if caption else [])),
            ui_clickable=who["access"], ui_disable=not who["access"])
        if who["access"]:
            item.on("click", lambda: self._access(row, who, self._current(shares, who)))
        return item

    @staticmethod
    def _current(shares, who):
        key = "group_id" if who.get("kind") == "group" else "user_id"
        return next((s for s in shares if s.get(key) == who["id"]), None)

    def _pick(self, row, users, shares):
        usable = [u for u in users if u["access"]]
        if len(users) == 1 and usable:
            self._access(row, usable[0], self._current(shares, usable[0]))
            return

        def label(u):
            if u.get("kind") == "group":
                return f"Group {u['name']}"
            return u["name"] if u["access"] else f"{u['name']} (no access to the app)"

        options = [{"label": label(u), "value": f"{u.get('kind', 'user')}:{u['id']}",
                    "disable": not u["access"]} for u in users]
        first = f"{usable[0].get('kind', 'user')}:{usable[0]['id']}" if usable else None
        pick = QOptionGroup(ui_type="radio", ui_options=options, ui_model_value=first)

        def ok():
            who = next((u for u in usable
                        if f"{u.get('kind', 'user')}:{u['id']}" == pick.ui_model_value), None)
            if who is None:
                return False
            self._access(row, who, self._current(shares, who))
            return False

        self._ask(f'Share "{_label(row)}" with', [pick], ok, ok_label="Next")

    def _access(self, row, who, current):
        d = self.directory()
        group = who.get("kind") == "group"
        if group:
            name = f"the members of {who['name']}"
        else:
            name = who["name"] if who["name"] == who["id"] else f"{who['name']} ({who['id']})"
        options = [{"label": "Can edit", "value": "write"},
                   {"label": "Can view", "value": "read"}]
        if current is not None:
            options.append({"label": "No access", "value": "none"})
        access = QOptionGroup(ui_type="radio", ui_options=options, ui_model_value=(
            "write" if current is None or current["write"] else "read"))

        def ok():
            if access.ui_model_value == "none":
                self._try("Sharing", d.unshare_group if group else d.unshare, row["id"], who["id"])
            else:
                self._try("Sharing", d.share_group if group else d.share, row["id"], who["id"],
                          access.ui_model_value == "write")

        self._ask("Share", [Label(f'Access of {name} to "{_label(row)}"'), access], ok)
