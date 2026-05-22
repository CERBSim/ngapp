"""Composable CSS-in-Python utilities: Style, Theme, CssClass, StyleSheet.

Build CSS from Python kwargs, centralize design tokens, and inject efficient
CSS classes into the DOM instead of sending inline style strings per component.
"""

__all__ = ["Style", "Theme", "CssClass", "StyleSheet"]


class Style:
    """Composable CSS property bag.

    Keyword arguments become CSS properties (underscores → hyphens).
    Merge with ``|`` (right side wins, ``None`` removes a property).
    Converts to a CSS string via ``str()``.

    Example::

        overlay = Style(position="fixed", z_index=9999, color="white")
        hidden  = overlay | Style(display="none")
        str(overlay)  # "position: fixed; z-index: 9999; color: white;"
    """

    def __init__(self, **kwargs):
        self._props = kwargs

    def __or__(self, other):
        merged = {**self._props, **other._props}
        merged = {k: v for k, v in merged.items() if v is not None}
        return Style(**merged)

    def __str__(self):
        parts = []
        for k, v in self._props.items():
            if v is None:
                continue
            prop = k.replace("_", "-")
            parts.append(f"{prop}: {v}")
        return "; ".join(parts) + (";" if parts else "")

    def __repr__(self):
        return f"Style({self._props!r})"

    def __eq__(self, other):
        if not isinstance(other, Style):
            return NotImplemented
        return self._props == other._props


class Theme:
    """Centralized design tokens (colors, spacing, font sizes).

    All keyword arguments are stored as attributes. Pass a ``spacing``
    tuple to enable the :meth:`sp` helper.

    Attributes named after Quasar brand colors (``primary``, ``secondary``,
    ``accent``, ``dark``, ``positive``, ``negative``, ``info``, ``warning``)
    can be applied to the app with :meth:`apply`, replacing ``set_colors``.

    Example::

        theme = Theme(primary="#164d7d", border="#e0e0e0", spacing=(0, 4, 8, 12, 16))
        theme.primary       # "#164d7d"
        theme.sp(2)         # "8px"
        theme.border_line() # "1px solid #e0e0e0"
        theme.apply(app)    # sets --q-primary on the page
    """

    _QUASAR_BRANDS = frozenset(
        (
            "primary",
            "secondary",
            "accent",
            "dark",
            "positive",
            "negative",
            "info",
            "warning",
        )
    )

    def __init__(self, **kwargs):
        spacing = kwargs.pop("spacing", ())
        self._spacing = spacing
        for k, v in kwargs.items():
            setattr(self, k, v)

    def sp(self, index):
        """Return ``spacing[index]`` as a pixel string, e.g. ``"8px"``."""
        return f"{self._spacing[index]}px"

    def border_line(self, width="1px", style="solid", color=None):
        """Return a CSS border shorthand, e.g. ``"1px solid #e0e0e0"``."""
        return f"{width} {style} {color or self.border}"

    def apply(self, app):
        """Apply Quasar brand colors from this theme to the app.

        Picks up any attributes named ``primary``, ``secondary``, ``accent``,
        ``dark``, ``positive``, ``negative``, ``info``, or ``warning`` and
        passes them to ``app.set_colors()``.
        """
        colors = {
            k: getattr(self, k) for k in self._QUASAR_BRANDS if hasattr(self, k)
        }
        if colors:
            app.set_colors(**colors)


class CssClass:
    """CSS class handle with support for nested descendant rules.

    Compose with ``+`` to join class names::

        sidebar = CssClass("ngs0")
        hidden  = CssClass("ngs1")
        sidebar + hidden            # CssClass("ngs0 ngs1")
        sidebar + "bg-primary"      # CssClass("ngs0 bg-primary")
        "q-pa-md" + sidebar         # CssClass("q-pa-md ngs0")

    Add nested CSS rules that target children/descendants::

        panel = css.add(Style(height="100%"))
        panel.rule(".q-checkbox__label", font_size="0.82rem")
        panel.rule(".q-slider", margin="2px 0", padding="0 4px")

        # Pass a Style object instead of kwargs:
        panel.rule(".q-field", Style(margin_bottom="2px"))

        # Chaining:
        panel.rule(".q-checkbox__label", font_size="0.82rem") \
             .rule(".q-slider", margin="2px 0")

        # Dict-style subscript:
        panel[".q-checkbox__label"] = Style(font_size="0.82rem")
    """

    def __init__(self, name, sheet=None):
        self._name = name
        self._sheet = sheet

    def rule(self, selector, style=None, **kwargs):
        """Add a nested CSS rule scoped to this class.

        Args:
            selector: CSS selector for descendants, e.g. ``.q-checkbox__label``
            style: Optional :class:`Style` object. If not given, kwargs are
                   used to construct one.
            **kwargs: CSS properties (same syntax as :class:`Style`).

        Returns:
            ``self`` for chaining.

        Example::

            panel.rule(".q-checkbox__label", font_size="0.82rem")
            panel.rule(".q-input", Style(margin_bottom="2px"))
        """
        if self._sheet is None:
            raise RuntimeError(
                "CssClass.rule() requires a stylesheet reference. "
                "Use css.add(...) to create the class."
            )
        if style is None:
            style = Style(**kwargs)
        self._sheet._rules.append((f".{self._name} {selector}", style))
        return self

    def __setitem__(self, selector, style):
        """Dict-style syntax: panel[".q-checkbox"] = Style(...)."""
        if self._sheet is None:
            raise RuntimeError(
                "CssClass[] requires a stylesheet reference. "
                "Use css.add(...) to create the class."
            )
        if not isinstance(style, Style):
            raise TypeError("Value must be a Style instance")
        self._sheet._rules.append((f".{self._name} {selector}", style))

    def __add__(self, other):
        if isinstance(other, CssClass):
            return CssClass(f"{self._name} {other._name}", self._sheet)
        return CssClass(f"{self._name} {other}", self._sheet)

    def __radd__(self, other):
        return CssClass(f"{other} {self._name}", self._sheet)

    def __str__(self):
        return self._name

    def __repr__(self):
        return f"CssClass({self._name!r})"

    def __eq__(self, other):
        if isinstance(other, CssClass):
            return self._name == other._name
        return self._name == other


class StyleSheet:
    """Registers :class:`Style` objects as CSS classes and injects them into the DOM.

    Basic usage::

        css = StyleSheet()
        sidebar = css.add(Style(height="100%", background="#f5f7fa"))
        hidden  = css.add(Style(display="none"))
        Div(ui_class=str(sidebar + hidden))  # "ngs0 ngs1"
        css.inject(app)                      # creates a <style> tag in <head>

    Nested rules via the returned :class:`CssClass` handle::

        panel = css.add(Style(overflow_y="auto"))
        panel.rule(".q-checkbox__label", font_size="0.82rem")
        panel.rule(".q-slider", margin="2px 0", padding="0 4px")

        # Chaining:
        panel.rule(".q-checkbox__label", font_size="0.82rem") \\
             .rule(".q-field--dense", margin_bottom="2px")

        # Dict-style:
        panel[".q-checkbox__label"] = Style(font_size="0.82rem")
    """

    def __init__(self, prefix="ngs"):
        self._styles = {}
        self._rules = []
        self._counter = 0
        self._prefix = prefix

    def add(self, style, name=None):
        """Register a *style* and return a :class:`CssClass` for it."""
        if name is None:
            name = f"{self._prefix}{self._counter}"
            self._counter += 1
        self._styles[name] = style
        return CssClass(name, sheet=self)

    def add_rule(self, selector, style):
        """Add a CSS rule with an arbitrary selector.

        Use this for descendant/nested selectors that target sub-components
        within a container::

            css.add_rule(".my-panel .q-checkbox", Style(font_size="0.8rem"))
            css.add_rule(".my-panel .q-input", Style(margin_bottom="2px"))
        """
        self._rules.append((selector, style))

    def scoped(self, parent, rules):
        """Add multiple nested rules scoped under a parent class.

        Args:
            parent: A :class:`CssClass` (from :meth:`add`) or a string class name.
            rules: A dict mapping CSS selectors to :class:`Style` objects.
                   Each selector is prefixed with ``.parent_class``.

        Example::

            panel = css.add(Style(overflow_y="auto"))
            css.scoped(panel, {
                ".q-checkbox__label": Style(font_size="0.82rem"),
                ".q-slider": Style(margin="2px 0"),
            })
        """
        parent_name = str(parent)
        for selector, style in rules.items():
            self._rules.append((f".{parent_name} {selector}", style))

    def _render(self):
        """Generate the full CSS string for all registered styles."""
        lines = []
        for name, style in self._styles.items():
            lines.append(f".{name} {{ {style} }}")
        for selector, style in self._rules:
            lines.append(f"{selector} {{ {style} }}")
        return "\n".join(lines)

    def inject(self, app):
        """Inject all registered styles into the DOM as a ``<style>`` tag.

        Uses ``app.call_js``, so it is safe to call during ``__init__``.
        """
        css_text = self._render()

        def _inject(js):
            el = js.document.createElement("style")
            el.textContent = css_text
            js.document.head.appendChild(el)

        app.call_js(_inject)
