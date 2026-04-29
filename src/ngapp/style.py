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
    """Thin wrapper around a CSS class name string.

    Compose with ``+`` to join class names::

        sidebar = CssClass("ngs0")
        hidden  = CssClass("ngs1")
        sidebar + hidden            # CssClass("ngs0 ngs1")
        sidebar + "bg-primary"      # CssClass("ngs0 bg-primary")
        "q-pa-md" + sidebar         # CssClass("q-pa-md ngs0")
    """

    def __init__(self, name):
        self._name = name

    def __add__(self, other):
        if isinstance(other, CssClass):
            return CssClass(f"{self._name} {other._name}")
        return CssClass(f"{self._name} {other}")

    def __radd__(self, other):
        return CssClass(f"{other} {self._name}")

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

    Example::

        css = StyleSheet()
        sidebar = css.add(Style(height="100%", background="#f5f7fa"))
        hidden  = css.add(Style(display="none"))
        Div(ui_class=sidebar + hidden)  # "ngs0 ngs1"
        css.inject(app)                 # creates a <style> tag in <head>
    """

    def __init__(self, prefix="ngs"):
        self._styles = {}
        self._counter = 0
        self._prefix = prefix

    def add(self, style, name=None):
        """Register a *style* and return a :class:`CssClass` for it."""
        if name is None:
            name = f"{self._prefix}{self._counter}"
            self._counter += 1
        self._styles[name] = style
        return CssClass(name)

    def _render(self):
        """Generate the full CSS string for all registered styles."""
        lines = []
        for name, style in self._styles.items():
            lines.append(f".{name} {{ {style} }}")
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
