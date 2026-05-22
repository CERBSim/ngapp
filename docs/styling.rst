Styling
=======

ngapp provides a Python-native styling system that replaces raw CSS strings
with composable, reusable objects. The module lives at :mod:`ngapp.style` and
exports four classes: :class:`~ngapp.style.Style`,
:class:`~ngapp.style.Theme`, :class:`~ngapp.style.CssClass`, and
:class:`~ngapp.style.StyleSheet`.

.. tip::

   **Prefer Quasar utilities for standard layout and spacing.** Quasar already
   provides classes for padding (``q-pa-md``), margin (``q-mt-sm``), flex
   layout (``row``, ``col``), visibility (``ui_hidden``), and colors
   (``bg-primary``, ``text-grey-7``). Use ``Style`` and ``StyleSheet`` for
   things Quasar doesn't cover: custom overlays, app-specific panel layouts,
   domain-specific visual treatments, and shared multi-property styles that
   have no Quasar equivalent.


Quick Example
-------------

A fixed-position status indicator:

.. code-block:: python

   from ngapp.style import Style, Theme, StyleSheet
   from ngapp.components import Div

   theme = Theme(
       primary="#164d7d",
       muted="#78909c",
       border="#e0e0e0",
       font_sm="0.75rem",
       spacing=(0, 4, 8, 12, 16, 20, 24, 32),
   )

   css = StyleSheet()

   # Fixed overlay
   status_indicator = css.add(Style(
       position="fixed",
       bottom="20px",
       left="50%",
       transform="translateX(-50%)",
       background="rgba(15, 23, 42, 0.92)",
       backdrop_filter="blur(4px)",
       color="white",
       padding="8px 20px",
       border_radius="8px",
       box_shadow="0 4px 12px rgba(0,0,0,0.3)",
       z_index=9999,
       font_size=theme.font_sm,
       display="flex",
       align_items="center",
       gap="8px",
   ))

   Div("Solving…", ui_class=status_indicator)
   css.inject(app)


Style — Composable CSS Property Bag
------------------------------------

:class:`~ngapp.style.Style` turns Python keyword arguments into CSS properties.
Underscores become hyphens (``font_size`` → ``font-size``).

.. code-block:: python

   from ngapp.style import Style

   overlay = Style(
       position="fixed",
       bottom="20px",
       background="rgba(0,0,0,0.8)",
       backdrop_filter="blur(4px)",
       color="white",
       z_index=9999,
   )

**Merging with** ``|``:

The ``|`` operator merges two styles. The right side wins on conflicts,
matching Python ``dict |`` semantics (PEP 584). Set a value to ``None`` to
remove a property.

.. code-block:: python

   panel = Style(
       border_right="1px solid #e0e0e0",
       height="100%",
       overflow_y="auto",
   )

   # Left panel: same but border on the other side
   panel_left = panel | Style(border_right=None, border_left="1px solid #e0e0e0")

**Using with components**:

``Style`` objects work directly with ``ui_style`` — they are converted to
strings automatically. Use this for truly dynamic, per-instance values:

.. code-block:: python

   # Dynamic color from a color picker — must be inline
   swatch.ui_style = Style(background_color=self.to_hex_string())

   # Per-instance grid placement
   cell.ui_style = Style(grid_column=f"{col} / span 2", grid_row=str(row))

.. note::

   Integer values are **not** automatically converted to pixels. Write
   ``padding="8px"`` instead of ``padding=8``. This avoids ambiguity with
   unitless properties like ``z_index`` and ``font_weight``.


Theme — Design Tokens
---------------------

:class:`~ngapp.style.Theme` is a simple namespace for centralizing colors,
spacing, and font sizes. This avoids scattering magic hex values and pixel
numbers across files.

.. code-block:: python

   from ngapp.style import Theme

   theme = Theme(
       # Quasar brand colors — applied to the app via theme.apply()
       primary="#164d7d",
       secondary="#93B1D4",
       accent="#14B8A6",
       positive="#16A34A",
       negative="#DC2626",
       info="#0EA5E9",
       warning="#F59E0B",
       # App-specific tokens — used in Style() and StyleSheet
       muted="#78909c",
       surface="#f5f7fa",
       border="#e0e0e0",
       font_sm="0.75rem",
       font_md="0.85rem",
       spacing=(0, 4, 8, 12, 16, 20, 24, 32),
   )

   theme.primary        # → "#164d7d"
   theme.font_sm        # → "0.75rem"
   theme.sp(2)          # → "8px"  (spacing[2])
   theme.border_line()  # → "1px solid #e0e0e0"

**Applying Quasar brand colors:**

If the theme has attributes matching Quasar brand color names (``primary``,
``secondary``, ``accent``, ``dark``, ``positive``, ``negative``, ``info``,
``warning``), calling :meth:`~ngapp.style.Theme.apply` sets them on the app.
This replaces the manual ``app.set_colors(...)`` call:

.. code-block:: python

   # In your app's __init__:
   theme.apply(self)   # equivalent to self.set_colors(primary="#164d7d", secondary=...)

Tokens that are not Quasar brand names (``muted``, ``surface``, ``border``,
``font_sm``, etc.) are ignored by ``apply()`` and are only used in your own
``Style`` definitions.

**Helpers:**

- ``sp(index)`` — returns ``f"{spacing[index]}px"``
- ``border_line(width, style, color)`` — returns a CSS border shorthand,
  defaults to ``1px solid {theme.border}``


StyleSheet and CssClass — The Efficiency Layer
-----------------------------------------------

Instead of sending full inline CSS strings over the wire for every component,
:class:`~ngapp.style.StyleSheet` registers styles as CSS classes and injects a
single ``<style>`` tag into the DOM. Components then reference short class
names.

.. code-block:: python

   from ngapp.style import Style, StyleSheet

   css = StyleSheet()

   # Custom sidebar panel — Quasar has no single class for this combination
   sidebar = css.add(Style(
       height="100%",
       overflow_y="auto",
       background=theme.surface,
       border_right=theme.border_line(),
       min_width="200px",
   ))

   # Section heading style used in 3+ places across the app
   section_heading = css.add(Style(
       font_size=theme.font_sm,
       letter_spacing="0.05em",
       text_transform="uppercase",
       font_weight=700,
       color=theme.muted,
   ))

**Composing classes with** ``+``:

:class:`~ngapp.style.CssClass` objects compose with ``+``. You can combine
them with each other and with Quasar utility classes:

.. code-block:: python

   # Custom style + Quasar padding
   Div("Properties", ui_class=section_heading + "q-pa-sm")

   # Multiple custom styles
   Div(ui_class=sidebar + "col-3")

**Combining classes with inline overrides:**

Use classes for the shared base, inline ``Style`` only for the part that
varies per instance:

.. code-block:: python

   # Same heading style, different padding per usage site
   Div("Properties", ui_class=section_heading, ui_style=Style(padding="12px 16px 8px"))
   Div("Settings",   ui_class=section_heading, ui_style=Style(padding="8px 12px"))

**Injecting into the DOM:**

Call ``inject()`` once (typically in your app's ``__init__``):

.. code-block:: python

   class MyApp(App):
       def __init__(self):
           # ... build UI ...
           css.inject(self)

This creates a ``<style>`` element in the page ``<head>`` containing all
registered rules. It uses ``call_js`` internally, so it's safe to call during
``__init__``.


Scoped Nested Rules — Targeting Child Components
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When you have a container (like a settings panel) and want to automatically
style **all** Quasar widgets inside it without touching each child component,
use :meth:`~ngapp.style.CssClass.rule` on the class handle returned by
``css.add()``:

.. code-block:: python

   panel = css.add(Style(height="100%", overflow_y="auto"))

   # Every QCheckbox inside panel gets compact sizing
   panel.rule(".q-checkbox__label", font_size="0.82rem")
   panel.rule(".q-field--dense .q-field__control", min_height="30px")
   panel.rule(".q-slider", margin="4px 0")

This generates CSS like:

.. code-block:: css

   .ngs0 .q-checkbox__label { font-size: 0.82rem; }
   .ngs0 .q-field--dense .q-field__control { min-height: 30px; }
   .ngs0 .q-slider { margin: 4px 0; }

Any component with ``ui_class=str(panel)`` automatically applies these rules
to all its descendants — no manual ``ui_style`` needed on each widget.

**Chaining:**

Multiple rules can be chained in a single expression:

.. code-block:: python

   panel.rule(".q-checkbox__label", font_size="0.82rem") \
        .rule(".q-field--dense", margin_bottom="2px") \
        .rule(".q-slider", margin="4px 0") \
        .rule(".q-btn--dense", font_size="0.78rem")

**Passing Style objects:**

You can pass an existing ``Style`` object instead of kwargs:

.. code-block:: python

   compact_input = Style(min_height="30px", font_size="0.82rem")
   panel.rule(".q-field--dense .q-field__control", compact_input)

**Dict-style subscript:**

An alternative syntax using ``[]``:

.. code-block:: python

   panel[".q-checkbox__label"] = Style(font_size="0.82rem")
   panel[".q-slider"] = Style(margin="4px 0")

**Real-world example — property panel styling:**

.. code-block:: python

   # In styles.py — one block styles the entire property panel
   sidebar_props = css.add(Style(height="100%", overflow_y="auto"))

   sidebar_props.rule(".q-checkbox", padding="0", min_height="28px") \
                .rule(".q-checkbox__label", font_size="0.82rem") \
                .rule(".q-field--dense .q-field__control", min_height="32px") \
                .rule(".q-field--dense .q-field__label", font_size="0.72rem") \
                .rule(".q-slider", margin="4px 0") \
                .rule(".q-expansion-item .q-item", padding="8px 12px",
                      min_height="38px", background="rgba(0,0,0,0.02)")

   # Every section added to the panel inherits compact styling automatically

.. note::

   Scoped rules use standard CSS descendant selectors. They work with any
   valid CSS selector — class names, pseudo-classes, combinators, etc.
   The rules are injected along with all other StyleSheet rules when
   ``css.inject(app)`` is called.


When to Use What
-----------------

.. list-table::
   :header-rows: 1
   :widths: 30 40 30

   * - Need
     - Use
     - Example
   * - Padding, margin, flex
     - **Quasar classes**
     - ``ui_class="q-pa-md row"``
   * - Show / hide
     - ``ui_hidden``
     - ``self.ui_hidden = True``
   * - Background / text color from Quasar palette
     - **Quasar classes**
     - ``ui_class="bg-primary text-white"``
   * - Multi-property style shared across components
     - **StyleSheet + CssClass**
     - overlay, sidebar panel, section heading
   * - Custom positioning, backdrop-filter, gradients, box-shadow combos
     - **StyleSheet + CssClass**
     - fixed indicator, visualization toolbar
   * - Truly dynamic per-instance value
     - **inline Style**
     - ``Style(background_color=hex_val)``


Examples
--------

**Fixed-position status overlay** (no Quasar equivalent):

.. code-block:: python

   status_bar = css.add(Style(
       position="fixed",
       bottom="20px",
       left="50%",
       transform="translateX(-50%)",
       background="rgba(15, 23, 42, 0.92)",
       backdrop_filter="blur(4px)",
       color="white",
       padding="8px 20px",
       border_radius="8px",
       box_shadow="0 4px 12px rgba(0,0,0,0.3)",
       z_index=9999,
       display="flex",
       align_items="center",
       gap="8px",
   ))

   indicator = Div("Solving…", ui_class=status_bar)
   indicator.ui_hidden = True   # use ui_hidden to toggle, not custom CSS

**Visualization container with CSS grid** (Quasar grid is flex-based, not CSS
grid):

.. code-block:: python

   viewer_grid = css.add(Style(
       display="grid",
       grid_template_columns="1fr 280px",
       grid_template_rows="auto 1fr auto",
       height="100%",
       gap="0",
   ))

   viewer_toolbar = css.add(Style(
       grid_column="1 / -1",
       background="linear-gradient(135deg, #1a1a2e, #16213e)",
       color="white",
       padding="4px 12px",
       display="flex",
       align_items="center",
       gap="8px",
   ))

**App-specific sidebar with custom border** (Quasar drawers exist, but
sometimes you need a simpler panel inside a layout):

.. code-block:: python

   sidebar_base = css.add(Style(
       height="100%",
       overflow_y="auto",
       background=theme.surface,
   ))
   sidebar_left = css.add(Style(border_right=theme.border_line()))
   sidebar_right = css.add(Style(border_left=theme.border_line()))

   # Compose: base + side-specific
   self.navigator.ui_class = sidebar_base + sidebar_left + "col-3"
   self.properties.ui_class = sidebar_base + sidebar_right + "col-3"

**Dynamic per-instance color** (stays inline — correct for runtime values):

.. code-block:: python

   # Each swatch has a different user-chosen color — must be inline
   self.ui_style = Style(
       background_color=self.to_hex_string(),
       border="1px solid rgba(0,0,0,0.15)",
       border_radius="4px",
   )


API Reference
-------------

See :doc:`api/style` for the full class reference.
