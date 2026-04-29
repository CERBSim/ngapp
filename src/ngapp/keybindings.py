"""Reusable keybinding manager with floating indicator and help overlay.

Provides :class:`KeybindingManager` — a two-layer (global + component)
keybinding dispatcher with a floating mode indicator and a help overlay
showing all registered shortcuts.

Usage::

    from ngapp.keybindings import KeybindingManager

    class MyApp(App):
        def __init__(self):
            super().__init__()
            self.kb = KeybindingManager(self)
            self.kb.add("h", self.kb.toggle_help, "Show shortcuts", "General")
            self.add_keybinding("escape", lambda e: self.kb.on_escape())
"""

from .components import Div
from .style import Style, StyleSheet, Theme

__all__ = [
    "KeybindingManager",
    "ModeIndicator",
    "HelpOverlay",
    "keybinding_styles",
]

# ---------------------------------------------------------------------------
# Default theme tokens (used when no external theme is provided)
# ---------------------------------------------------------------------------
_default_theme = Theme(
    accent="#14B8A6",
    hint="#94a3b8",
    muted="#78909c",
    border="#e0e0e0",
)

# ---------------------------------------------------------------------------
# StyleSheet — keybinding-related CSS classes
# ---------------------------------------------------------------------------
keybinding_styles = StyleSheet(prefix="ngkb")

# -- Indicator (floating keybinding bar) ------------------------------------
_indicator = Style(
    position="fixed",
    bottom="20px",
    left="50%",
    transform="translateX(-50%)",
    background="rgba(15, 23, 42, 0.92)",
    color="white",
    padding="8px 20px",
    border_radius="8px",
    font_size="0.85rem",
    z_index="9999",
    backdrop_filter="blur(4px)",
    box_shadow="0 4px 12px rgba(0,0,0,0.3)",
    align_items="center",
    gap="8px",
)
indicator_hidden = keybinding_styles.add(_indicator | Style(display="none"))
indicator_visible = keybinding_styles.add(_indicator | Style(display="flex"))

# -- Overlay (fullscreen backdrop) ------------------------------------------
_overlay = Style(
    position="fixed",
    top="0",
    left="0",
    width="100%",
    height="100%",
    background="rgba(0,0,0,0.5)",
    z_index="9998",
    align_items="center",
    justify_content="center",
)
overlay_hidden = keybinding_styles.add(_overlay | Style(display="none"))
overlay_visible = keybinding_styles.add(_overlay | Style(display="flex"))

# -- Key badge --------------------------------------------------------------
key_badge = keybinding_styles.add(
    Style(
        display="inline",
        background="#334155",
        padding="1px 6px",
        border_radius="3px",
        font_family="monospace",
        margin_right="4px",
    )
)

# -- Help overlay card ------------------------------------------------------
help_card = keybinding_styles.add(
    Style(
        background="white",
        border_radius="12px",
        max_width="480px",
        width="90%",
        max_height="80vh",
        overflow_y="auto",
        box_shadow="0 8px 32px rgba(0,0,0,0.2)",
    )
)
help_heading = keybinding_styles.add(
    Style(
        font_size="1.1rem",
        font_weight="700",
        padding="16px 20px 8px",
        border_bottom=f"1px solid {_default_theme.border}",
    )
)
help_group = keybinding_styles.add(
    Style(
        font_size="0.75rem",
        letter_spacing="0.05em",
        text_transform="uppercase",
        font_weight="700",
        color=_default_theme.muted,
        padding="12px 20px 4px",
    )
)
help_key = keybinding_styles.add(
    Style(
        min_width="80px",
        font_family="monospace",
        font_weight="600",
        background="#f1f5f9",
        padding="2px 8px",
        border_radius="4px",
        font_size="0.8rem",
        text_align="center",
    )
)
help_row = keybinding_styles.add(
    Style(display="flex", align_items="center", gap="12px", padding="3px 20px")
)
help_close = keybinding_styles.add(
    Style(
        text_align="center",
        color=_default_theme.hint,
        font_size="0.8rem",
        padding="12px",
    )
)


# ---------------------------------------------------------------------------
# Components
# ---------------------------------------------------------------------------


class ModeIndicator(Div):
    """Floating bar showing available keys in the active submenu."""

    def __init__(self, theme=None):
        self._theme = theme or _default_theme
        super().__init__(ui_class=str(indicator_hidden))

    def show(self, mode_name, entries):
        children = [
            Div(
                mode_name,
                ui_style=str(
                    Style(font_weight="700", color=self._theme.accent)
                ),
            ),
        ]
        for key, desc in entries:
            children.append(
                Div(
                    Div(key, ui_class=str(key_badge)),
                    desc,
                    ui_style=str(Style(display="flex", align_items="center")),
                )
            )
        children.append(
            Div(
                Div("Esc", ui_class=str(key_badge)),
                "Cancel",
                ui_style=str(
                    Style(
                        display="flex",
                        align_items="center",
                        color=self._theme.hint,
                    )
                ),
            )
        )
        self.ui_children = children
        self.ui_class = str(indicator_visible)

    def hide(self):
        self.ui_children = []
        self.ui_class = str(indicator_hidden)


class HelpOverlay(Div):
    """Floating overlay showing all registered keybindings."""

    def __init__(self, manager):
        self._manager = manager
        super().__init__(ui_class=str(overlay_hidden))

    def show(self):
        entries = self._manager.entries
        groups = {}
        for key, desc, group in entries:
            groups.setdefault(group, []).append((key, desc))

        children = [
            Div("Keyboard Shortcuts", ui_class=str(help_heading)),
        ]
        for group_name, bindings in groups.items():
            children.append(Div(group_name, ui_class=str(help_group)))
            for key, desc in bindings:
                children.append(
                    Div(
                        Div(key, ui_class=str(help_key)),
                        Div(desc, ui_style="font-size: 0.85rem;"),
                        ui_class=str(help_row),
                    )
                )

        children.append(
            Div("Press H or Esc to close", ui_class=str(help_close))
        )

        card = Div(*children, ui_class=str(help_card))
        self.ui_children = [card]
        self.ui_class = str(overlay_visible)

    def hide(self):
        self.ui_children = []
        self.ui_class = str(overlay_hidden)


# ---------------------------------------------------------------------------
# Manager
# ---------------------------------------------------------------------------


class KeybindingManager:
    """Two-layer keybinding manager with floating indicator and help overlay.

    *Global* bindings (``add``) are always active.
    *Component* bindings come from ``comp.get_keybindings()`` and are swapped
    on every ``set_component()`` call so only relevant shortcuts are shown.

    ``get_keybindings()`` returns::

        {
            "flat": [(key, callback, description, group), ...],
            "modes": [(trigger_key, mode_name, [(key, cb, desc), ...]), ...],
        }

    Parameters
    ----------
    app : App or Component
        The app (or root component) that owns the keybindings.
        Must support ``add_keybinding(key, callback)``.
    after_action : callable, optional
        Called after every keybinding action (e.g. to refresh UI).
    theme : Theme, optional
        Custom theme tokens for the indicator colors.
    """

    def __init__(self, app, after_action=None, theme=None):
        self._app = app
        self._after_action = after_action

        # Global layer
        self._global_entries = []
        self._global_key_callbacks = {}

        # Component layer
        self._active_components = set()  # set of id(comp)
        self._component_specs = {}  # id(comp) -> spec dict

        # Active set (rebuilt on set_component / activate / deactivate)
        self._entries = []
        self._key_callbacks = {}
        self._modes = {}  # mode_name -> {key: callback}
        self._mode_entries = {}  # mode_name -> [(key, desc)]
        self._mode_triggers = {}  # trigger_key -> mode_name

        self._registered_keys = set()
        self._mode = None
        self._help_visible = False
        self.indicator = ModeIndicator(theme=theme)
        self.help_overlay = HelpOverlay(self)

    @property
    def entries(self):
        return list(self._entries)

    # -- Global bindings ------------------------------------------------

    def add(self, key, callback, description, group="General"):
        """Register a global keybinding (always active)."""
        self._global_entries.append((key, description, group))
        self._global_key_callbacks[key] = callback
        self._entries.append((key, description, group))
        self._key_callbacks[key] = callback
        self._ensure_key(key)

    # -- Component bindings ---------------------------------------------

    def set_component(self, comp):
        """Swap component bindings (exclusive). Only these + global are active.

        This deactivates all previously active components and activates only
        the given one. Use :meth:`activate_component` / :meth:`deactivate_component`
        for non-exclusive visibility-based activation.
        """
        self._exit_mode()
        self._active_components = set()
        self._component_specs = {}

        # Rebuild from global
        self._entries = list(self._global_entries)
        self._key_callbacks = dict(self._global_key_callbacks)
        self._modes = {}
        self._mode_entries = {}
        self._mode_triggers = {}

        if comp is None or not hasattr(comp, "get_keybindings"):
            return

        self._active_components.add(id(comp))
        self._apply_spec(comp.get_keybindings())

    def activate_component(self, comp):
        """Activate a component's keybindings (additive).

        Call this when a component becomes visible. Multiple components
        can be active simultaneously. Use :meth:`deactivate_component`
        when the component is hidden.

        The component must implement ``get_keybindings()`` returning::

            {"flat": [(key, cb, desc, group), ...],
             "modes": [(trigger, name, [(key, cb, desc), ...]), ...]}
        """
        if not hasattr(comp, "get_keybindings"):
            return
        self._active_components.add(id(comp))
        self._component_specs[id(comp)] = comp.get_keybindings()
        self._rebuild()

    def deactivate_component(self, comp):
        """Deactivate a component's keybindings.

        Call this when a component becomes hidden.
        """
        self._exit_mode()
        self._active_components.discard(id(comp))
        self._component_specs.pop(id(comp), None)
        self._rebuild()

    def _rebuild(self):
        """Rebuild active entries from global + all active component specs."""
        self._entries = list(self._global_entries)
        self._key_callbacks = dict(self._global_key_callbacks)
        self._modes = {}
        self._mode_entries = {}
        self._mode_triggers = {}

        for spec in self._component_specs.values():
            self._apply_spec(spec)

    def _apply_spec(self, spec):
        """Apply a single keybinding spec to the active set."""
        for key, cb, desc, group in spec.get("flat", []):
            self._entries.append((key, desc, group))
            self._key_callbacks[key] = self._wrap(cb)
            self._ensure_key(key)

        for trigger, name, bindings in spec.get("modes", []):
            self._modes[name] = {}
            self._mode_entries[name] = []
            for key, cb, desc in bindings:
                self._modes[name][key] = self._wrap(cb)
                self._mode_entries[name].append((key, desc))
                self._entries.append((f"{trigger} \u2192 {key}", desc, name))
                self._ensure_key(key)
            self._entries.append((trigger, f"{name}\u2026", name))
            self._mode_triggers[trigger] = name
            self._key_callbacks[trigger] = lambda n=name: self._enter_mode(n)
            self._ensure_key(trigger)

    # -- Internals ------------------------------------------------------

    def _wrap(self, cb):
        def wrapped():
            cb()
            if self._after_action:
                self._after_action()

        return wrapped

    def _ensure_key(self, key):
        if key not in self._registered_keys:
            self._registered_keys.add(key)
            self._app.add_keybinding(key, lambda e, k=key: self._dispatch(k))

    def _dispatch(self, key):
        if self._help_visible and key == "h":
            self.toggle_help()
            return
        if self._mode:
            handlers = self._modes.get(self._mode, {})
            if key in handlers:
                handlers[key]()
                self._exit_mode()
                return
            exited_mode = self._mode
            self._exit_mode()
            if self._mode_triggers.get(key) == exited_mode:
                return
        cb = self._key_callbacks.get(key)
        if cb:
            cb()

    def _enter_mode(self, mode_name):
        if self._mode == mode_name:
            self._exit_mode()
            return
        self._mode = mode_name
        self.indicator.show(mode_name, self._mode_entries.get(mode_name, []))

    def _exit_mode(self):
        self._mode = None
        self.indicator.hide()

    def toggle_help(self):
        if self._mode:
            self._exit_mode()
        self._help_visible = not self._help_visible
        if self._help_visible:
            self.help_overlay.show()
        else:
            self.help_overlay.hide()

    def on_escape(self):
        if self._mode:
            self._exit_mode()
        elif self._help_visible:
            self._help_visible = False
            self.help_overlay.hide()
