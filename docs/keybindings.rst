Keybindings
===========

The :mod:`ngapp.keybindings` module provides a reusable keybinding manager
with a floating mode indicator and a help overlay. It supports global
shortcuts, per-component bindings, two-level modal keys, and
visibility-based activation.

Quick start
-----------

.. code-block:: python

    from ngapp.app import App
    from ngapp.components import Div
    from ngapp.keybindings import KeybindingManager, keybinding_styles

    class MyApp(App):
        def __init__(self):
            super().__init__()
            self.kb = KeybindingManager(self)
            self.kb.add("h", self.kb.toggle_help, "Show shortcuts", "General")
            self.add_keybinding("escape", lambda e: self.kb.on_escape())

            # Include the indicator and overlay in your layout
            super().__init__(
                Div("Hello"),
                self.kb.indicator,
                self.kb.help_overlay,
            )
            keybinding_styles.inject(self)

Global bindings
---------------

Use ``kb.add(key, callback, description, group)`` to register shortcuts
that are always active regardless of which component is visible::

    kb.add("ctrl+s", self.save, "Save", "General")
    kb.add("ctrl+b", self.toggle_sidebar, "Toggle sidebar", "Panels")

Component bindings (exclusive)
------------------------------

If your app shows one main component at a time (e.g. tabs), use
``kb.set_component(comp)`` to swap keybindings when the active view changes.

The component must implement ``get_keybindings()``::

    class MyView:
        def get_keybindings(self):
            return {
                "flat": [
                    ("w", self.toggle_wireframe, "Toggle wireframe", "Display"),
                ],
                "modes": [
                    ("s", "Show", [
                        ("e", self.toggle_edges, "Toggle edges"),
                        ("v", self.toggle_volumes, "Toggle volumes"),
                    ]),
                ],
            }

Then in your app::

    def on_tab_changed(self, comp):
        self.kb.set_component(comp)

Component bindings (visibility-based)
--------------------------------------

For apps where multiple panels can be visible simultaneously, use
``activate_component`` / ``deactivate_component``::

    # When component becomes visible
    self.kb.activate_component(panel)

    # When component is hidden
    self.kb.deactivate_component(panel)

Multiple components can be active at the same time. Their bindings are
merged (last-activated wins on conflicts).

Modal keys (modes)
------------------

Modes provide a two-level keybinding: pressing a trigger key (e.g. ``s``)
enters a mode, showing a floating indicator with available sub-keys.
Pressing a sub-key executes the action and exits the mode. ``Escape``
cancels.

Define modes in ``get_keybindings()``::

    "modes": [
        ("s", "Show", [
            ("w", self.toggle_wireframe, "Toggle wireframe"),
            ("e", self.toggle_edges, "Toggle edges"),
        ]),
    ]

Custom theme
------------

Pass a ``Theme`` to customize the indicator/overlay colors::

    from ngapp.style import Theme
    from ngapp.keybindings import KeybindingManager

    my_theme = Theme(accent="#FF6B35", hint="#94a3b8", muted="#666", border="#ddd")
    kb = KeybindingManager(app, theme=my_theme)

API reference
-------------

.. automodule:: ngapp.keybindings
   :members: KeybindingManager, ModeIndicator, HelpOverlay, keybinding_styles
   :undoc-members:
