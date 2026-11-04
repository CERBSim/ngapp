"""Components showing the case of the app: its name, the save status, a note
when the case can no longer be written, and buttons for the platform's case
list and named versions. The app places them where it wants; the platform
shows no case status of its own.

Everything comes from the app's case session (status, name, the state of the
browser's main thread it reports); nothing of it is stored in the case.
Outside of a case session (local mode without store, jobs) they are hidden.
"""

from ..state import session_of
from .basecomponent import Component
from .qcomponents import QBtn, QChip, QTooltip

__all__ = [
    "CaseName",
    "CaseSaveStatus",
    "CaseNotice",
    "CaseListButton",
    "NamedVersionButton",
]

_KEPT = "Your edits are kept in this browser and saved when possible."


def _set_text(comp: Component, text: str):
    if comp.ui_children != [text]:
        comp.ui_children = [text]


def _set(comp: Component, **props):
    """Only changed props: every assignment marks the case session dirty"""
    for key, value in props.items():
        if getattr(comp, key) != value:
            setattr(comp, key, value)


class _CaseView(Component):
    """Follows the case session of the app (on load, on mount) and renders on
    its status and info changes"""

    def __init__(self, tag, *children, **kwargs):
        super().__init__(tag, *children, **kwargs)
        self.session = None
        self._dispose = []
        self.on_load(self._sync)
        self.on_mounted(self._sync)

    def _sync(self, *_a):
        session = session_of(self)
        if session is not None and not hasattr(session, "on_info"):
            session = None  # the session of a job
        if session is not self.session:
            for dispose in self._dispose:
                try:
                    dispose()
                except ValueError:
                    pass
            self.session = session
            self._dispose = []
            if session is not None:
                self._dispose = [
                    session.on_info(self._rerender),
                    session.on_created(lambda _id: self._rerender()),
                ]
        self._rerender()

    def _rerender(self):
        """Render without marking the session dirty: what these components
        show is no edit of the case"""
        s = self.session
        if s is None:
            self._render()
            return
        applying, s._applying = s._applying, True
        try:
            self._render()
        finally:
            s._applying = applying

    def _render(self):
        pass


class CaseName(_CaseView):
    """The name of the open case"""

    def __init__(self, **kwargs):
        super().__init__("span", **kwargs)

    def _render(self):
        s = self.session
        _set(self, ui_hidden=s is None)
        if s is not None:
            name = s.app.file_data.name or ("" if s.case_id is None else "untitled")
            _set_text(self, name)


def save_badge(session) -> dict:
    """label, color, icon and tooltip of the save status of a case session"""
    client = session.client
    skipped = client.get("skipped") or 0
    skip = (
        f" {skipped} large value(s) are not uploaded yet and are lost on a reload."
        if skipped
        else ""
    )
    status = session.status
    # an edit the worker has not confirmed yet is pending
    if client.get("unconfirmed") and status in ("saved", "new"):
        status = "pending"
    if session.held_edits:
        return dict(label="Not saved", color="warning", icon="mdi-content-save-alert-outline",
                    tooltip="Edits made while the case was read only: save or discard them "
                            "(notice).")
    if status == "new":
        return dict(label="New case", color="grey-6", icon="mdi-file-outline",
                    tooltip="The case is created with the first edit.")
    if status == "saving":
        return dict(label="Saving", color="grey-7", icon="mdi-cloud-upload-outline",
                    tooltip="Saving your edits.")
    if status in ("pending", "saved"):
        if status == "pending" and not getattr(session.app, "autosave", True) \
                and not client.get("unconfirmed"):
            return dict(label="Not saved", color="warning",
                        icon="mdi-content-save-alert-outline",
                        tooltip="Edits are kept in this browser until you save the case.")
        if status == "pending" and skipped:
            return dict(label="Saving", color="grey-7", icon="mdi-cloud-upload-outline",
                        tooltip=f"Large values are uploaded in a moment. {_KEPT}{skip}")
        if client.get("unconfirmed"):
            return dict(label="Saving", color="grey-7", icon="mdi-cloud-upload-outline",
                        tooltip="Saving your edits.")
        if not client.get("connected", True):
            return dict(label="Reconnecting", color="grey-7", icon="mdi-cloud-sync-outline",
                        tooltip="Changes of others are shown once the connection is back.")
        return dict(label="Saved", color="positive", icon="mdi-cloud-check-outline",
                    tooltip="Your edits are saved in a moment." if status == "pending"
                    else "All edits are saved.")
    if status == "offline":
        return dict(label="Offline", color="warning", icon="mdi-cloud-off-outline",
                    tooltip=f"The server is not reachable. {_KEPT}{skip}")
    if status == "read_only":
        if session.read_only_reason == "no_write":
            return dict(label="Read only", color="grey-7", icon="mdi-eye-outline",
                        tooltip="The case is shared with you read only.")
        return dict(label="Deleted", color="negative", icon="mdi-delete-outline",
                    tooltip="This case was deleted; changes are not saved.")
    if status == "release_too_old":
        return dict(label="Updating app", color="info", icon="mdi-update",
                    tooltip=f"A newer version of the app saved this case. {_KEPT}")
    error = session.last_error
    if type(error).__name__ == "UnauthorizedError":
        return dict(label="Session expired", color="negative",
                    icon="mdi-account-alert-outline",
                    tooltip=f"Log in again to save. {_KEPT}{skip}")
    return dict(label="Not saved", color="negative", icon="mdi-alert-circle-outline",
                tooltip=f"{error or 'Saving failed'}. {_KEPT}{skip}")


class CaseSaveStatus(_CaseView):
    """The save status of the case as a chip (Saved, Saving, Not saved,
    Offline, Deleted, ...) with an explaining tooltip"""

    def __init__(self, **kwargs):
        self.tooltip = QTooltip("")
        self.chip = QChip(self.tooltip, ui_dense=True, ui_square=True,
                          ui_text_color="white", ui_class="case-sync-status")
        super().__init__("span", self.chip, **kwargs)

    def _render(self):
        s = self.session
        _set(self, ui_hidden=s is None)
        if s is None:
            return
        b = save_badge(s)
        _set(self.chip, ui_label=b["label"], ui_color=b["color"], ui_icon=b["icon"])
        _set_text(self.tooltip, b["tooltip"])


class CaseNotice(_CaseView):
    """A note while the case can no longer be written: deleted, or shared
    read only; hidden otherwise. The text has the class case-notice-deleted or
    case-notice-read-only (and a Quasar text colour) for the app's styles."""

    def __init__(self, **kwargs):
        self.text = Component("span")
        self.tooltip = QTooltip("")
        super().__init__("span", self.text, self.tooltip, **kwargs)

    def _render(self):
        s = self.session
        if s is None or s.status != "read_only":
            _set(self, ui_hidden=True)
            return
        _set(self, ui_hidden=False)
        if s.read_only_reason == "no_write":
            _set(self.text, ui_class="case-notice-read-only text-grey-8")
            _set_text(self.text, "Read only: your edits are not saved")
            _set_text(self.tooltip, "This case is shared with you read only: you see the "
                      "changes of others, your edits are not saved and are lost on a reload. "
                      "If you get write access, you are asked whether to save them.")
        else:
            _set(self.text, ui_class="case-notice-deleted text-negative")
            _set_text(self.text, "Case deleted: changes are not saved")
            _set_text(self.tooltip, "This case was deleted. Changes are not saved anymore.")


class CaseListButton(_CaseView):
    """Opens the platform's case list (open, new, copy, rename, delete,
    import and export of cases)"""

    def __init__(self, label: str = "", icon: str = "mdi-folder-open", **kwargs):
        self.button = QBtn(QTooltip("Cases"), ui_icon=icon, ui_label=label or None,
                           ui_flat=True, ui_dense=True, ui_round=not label,
                           ui_no_caps=True, ui_class="case-list-button")
        self.button.on_click(self._open)
        super().__init__("span", self.button, **kwargs)

    def _open(self, *_a):
        self._sync()
        if self.session is not None:
            self.session.request_ui("cases")

    def _render(self):
        _set(self, ui_hidden=self.session is None)


class NamedVersionButton(_CaseView):
    """Saves the current state of the case as a named version (the platform
    asks for the name)"""

    def __init__(self, label: str = "", icon: str = "mdi-tag-plus-outline", **kwargs):
        self.button = QBtn(QTooltip("Save as named version"), ui_icon=icon,
                           ui_label=label or None, ui_flat=True, ui_dense=True,
                           ui_round=not label, ui_no_caps=True,
                           ui_class="case-version-button")
        self.button.on_click(self._open)
        super().__init__("span", self.button, **kwargs)

    def _open(self, *_a):
        self._sync()
        if self.session is not None:
            self.session.request_ui("version")

    def _render(self):
        s = self.session
        _set(self, ui_hidden=s is None or s.case_id is None or s.status in (
            "read_only", "release_too_old"))
