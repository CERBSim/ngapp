# ngapp Styling Concept

## Problem Statement

The `gui` app styles everything with raw inline CSS strings in Python:

```python
# Duplicated 15-line strings that differ by one property
_INDICATOR_HIDDEN = "position: fixed; bottom: 20px; ... display: none;"
_INDICATOR_VISIBLE = "position: fixed; bottom: 20px; ... display: flex;"

# Hardcoded hex colors scattered across 8+ files
ui_style="font-size: 0.85rem; color: #78909c; padding-bottom: 4px;"

# String concatenation for composition
ui_style="background-color: " + self.to_hex_string()

# Style helpers that return opaque strings
def sidebar_style(*, border_side="right", extra=""):
    return f"height: 100%; ... border-{border_side}: ... {extra}"
```

**What's wrong:**
1. **Wasteful on the wire** — every component instance sends its full inline style
   string to the frontend. 50 nav items sharing the same 200-char style = 10KB of
   redundant data per render. A CSS class name is ~20 bytes.
2. **No composition** — styles are built via string concatenation and `f""` interpolation
3. **Massive duplication** — hidden/visible pairs repeat 14 identical CSS properties
4. **Scattered magic values** — `#78909c`, `#94a3b8`, `8px 12px` repeated without names
5. **Not Pythonic** — writing CSS-in-strings has no IDE support, no validation, no autocomplete

---

## Design: `Style` classes + `Theme` tokens + CSS class injection

Three pieces:
1. **`Style`** — composable CSS property bag (Python kwargs → CSS)
2. **`Theme`** — centralized design tokens (colors, spacing, fonts)
3. **`StyleSheet`** — registers `Style` objects as CSS classes, injects a `<style>` tag
   into the DOM once, components then use `ui_class="my-cls"` instead of inline CSS

### The key efficiency insight

Currently every `RecursiveComponent.vue` does:

```html
<component :is="componentClass" v-bind="props" ...>
```

Where `props` includes `{ style: "position: fixed; bottom: 20px; ..." }` — the full
CSS string travels through the WebSocket/pyodide bridge for every single component
instance.

With CSS classes: define the rule **once** in a `<style>` tag, then each component
just sends `{ class: "ngs-indicator" }`. The browser does the rest natively.

---

## API Design

### `Style` — composable CSS property bag

```python
from ngapp.style import Style

# Python kwargs → CSS properties (underscores become hyphens)
overlay = Style(
    position="fixed",
    bottom="20px",
    left="50%",
    transform="translateX(-50%)",
    background="rgba(15, 23, 42, 0.92)",
    color="white",
    padding="8px 20px",
    border_radius="8px",
    z_index=9999,
)

# Compose with | (like dict merge — right side wins)
indicator_hidden  = overlay | Style(display="none")
indicator_visible = overlay | Style(display="flex")

# Remove a property with None
no_border = sidebar | Style(border_right=None)

# Render to CSS string
str(overlay)  # → "position: fixed; bottom: 20px; left: 50%; ..."

# Still works directly with ui_style for one-off dynamic styles
Div(ui_style=overlay)
```

Implementation: ~40 lines. Thin wrapper around `dict`.
- `snake_case` keys → `kebab-case` CSS
- `|` for merge (new `Style`, right side wins, `None` deletes)
- `__str__()` → CSS string
- ints stay as-is (no implicit `px` — too magical)

### `Theme` — centralized design tokens

```python
from ngapp.style import Theme

theme = Theme(
    # Colors
    primary="#164d7d",
    secondary="#93B1D4",
    accent="#14B8A6",
    muted="#78909c",
    muted_light="#94a3b8",
    surface="#f5f7fa",
    border="#e0e0e0",
    text="#0F172A",

    # Spacing scale (index → px)
    spacing=(0, 4, 8, 12, 16, 20, 24, 32),

    # Font sizes
    font_xs="0.65rem",
    font_sm="0.75rem",
    font_md="0.85rem",
    font_lg="1rem",
    font_xl="1.1rem",
)

# Access naturally
theme.primary      # → "#164d7d"
theme.font_sm      # → "0.75rem"
theme.sp(2)        # → "8px"  (spacing[2])
theme.border_line()  # → "1px solid #e0e0e0"
```

Implementation: ~30 lines. Simple namespace with `sp()` and `border_line()` helpers.

### `StyleSheet` + `CssClass` — the efficiency layer

`css.add(style)` registers a `Style` as a CSS class and returns a `CssClass` object.
`CssClass` is a thin wrapper around a generated class name. Compose with `+` —
works with other `CssClass` objects and with plain strings (Quasar classes etc.).

```python
from ngapp.style import Style, StyleSheet

css = StyleSheet()

# css.add() returns a CssClass object
indicator = css.add(Style(
    position="fixed", bottom="20px", left="50%",
    transform="translateX(-50%)",
    background="rgba(15, 23, 42, 0.92)", color="white",
    padding="8px 20px", border_radius="8px",
    z_index=9999, backdrop_filter="blur(4px)",
    box_shadow="0 4px 12px rgba(0,0,0,0.3)",
    align_items="center", gap="8px",
))
hidden = css.add(Style(display="none"))
flex = css.add(Style(display="flex"))

section_heading = css.add(Style(
    font_size=theme.font_sm,
    letter_spacing="0.05em",
    text_transform="uppercase",
    font_weight=700,
    color=theme.muted,
))

sidebar = css.add(Style(
    height="100%",
    overflow_y="auto",
    background=theme.surface,
))

# Compose with + (CssClass + CssClass, or CssClass + str)
Div(ui_class=indicator + hidden)                            # → "s0 s1"
Div(ui_class=indicator + flex)                              # → "s0 s2"
Div(ui_class=indicator + flex + "bg-primary text-white")    # → "s0 s2 bg-primary text-white"
Div(ui_class=section_heading + "q-pa-md")                   # → "s3 q-pa-md"

# Toggle visibility: swap one object, not a 200-char string
self.ui_class = indicator + flex     # show
self.ui_class = indicator + hidden   # hide

# One-off inline override where needed
Div(
    ui_class=section_heading,               # shared style via class
    ui_style=Style(padding="12px 16px 8px"),  # only the varying part inline
)
```

**`CssClass`** (~15 lines):
- Wraps a string (the generated class name, e.g. `"s0"`)
- `__add__(other)` → returns new `CssClass` with joined names: `"s0 s1"` or `"s0 q-pa-md"`
- `__radd__(other)` → so `"some-class" + my_cls` also works
- `__str__()` → the class name string, so it's transparent to `ui_class`

**`StyleSheet`** (~40 lines):
- `add(style)` → assigns an auto-incrementing class name (e.g. `s0`, `s1`, ...),
  stores the `Style`, returns a `CssClass`
- `inject(app)` → renders all rules and injects a single `<style>` tag into the DOM
- `_render()` → generates CSS: `.s0 { position: fixed; ... }\n.s1 { display: none; }\n...`

Injection into the DOM:
- **LOCAL_APP**: `js.document.head.appendChild(styleElement)` — same pattern `set_colors`
  already uses via `call_js` / `execute_when_init`
- **COMPUTE (web app)**: one-time JS eval on mount, or a new `inject_css` callback

---

## Before & After

### Sidebar style

**Before:**
```python
SIDEBAR_BG = "#f5f7fa"
SIDEBAR_BORDER_COLOR = "#e0e0e0"

def sidebar_style(*, border_side="right", extra=""):
    return (
        f"height: 100%; overflow-y: auto;"
        f" background: {SIDEBAR_BG};"
        f" border-{border_side}: 1px solid {SIDEBAR_BORDER_COLOR};"
        f" {extra}"
    )

self.navigator.ui_style = sidebar_style(
    border_side="right", extra="width: 200px; min-width: 200px; display: none;"
)
```

**After:**
```python
sidebar = css.add(Style(height="100%", overflow_y="auto", background=theme.surface))
sidebar_left = css.add(Style(border_right=theme.border_line(), width="200px", min_width="200px"))
sidebar_right = css.add(Style(border_left=theme.border_line(), width="280px", min_width="280px"))

self.navigator.ui_class = sidebar + sidebar_left
self.navigator.ui_hidden = True  # use the built-in mechanism
```

Wire cost: `"s0 s1"` (5 bytes) vs 120-char inline string.

### Indicator hidden/visible

**Before:** Two 5-line strings that are 95% identical.

**After:**
```python
indicator = css.add(Style(
    position="fixed", bottom="20px", left="50%",
    transform="translateX(-50%)",
    background="rgba(15, 23, 42, 0.92)", color="white",
    padding="8px 20px", border_radius="8px",
    font_size=theme.font_md, z_index=9999,
    backdrop_filter="blur(4px)",
    box_shadow="0 4px 12px rgba(0,0,0,0.3)",
    align_items="center", gap="8px",
))

# Show/hide by swapping one object
self.ui_class = indicator + flex     # show
self.ui_class = indicator + hidden   # hide
```

Wire cost per toggle: `"s0 s2"` (5 bytes) vs re-sending 280-char string.

### Section heading (used in 3+ files with same magic values)

**Before:** Same 6-property CSS string copy-pasted in `navigator.py`, `property_panel.py`,
`keybindings.py` with slight padding variations.

**After:**
```python
# Defined once in theme module
section_heading = css.add(Style(
    font_size=theme.font_sm,
    letter_spacing="0.05em",
    text_transform="uppercase",
    font_weight=700,
    color=theme.muted,
))

# Usage — only the varying part is inline
Div("Properties", ui_class=section_heading, ui_style=Style(padding="12px 16px 8px"))
```

### Dynamic color (stays inline — correct for truly dynamic values)

```python
# This is inherently per-instance, so inline is appropriate
self.ui_style = Style(background_color=self.to_hex_string())
```

---

## CSS Injection Mechanism

### LOCAL_APP (standalone gui)

Uses `call_js` / `execute_when_init`, same as `set_colors`:

```python
def inject(self, app):
    css_text = self._render()  # generate full CSS string

    def _inject(js):
        el = js.document.createElement("style")
        el.textContent = css_text
        js.document.head.appendChild(el)

    app.call_js(_inject)
```

### COMPUTE (web app)

Two options, from simplest to most robust:

**Option A — JS eval on mount (no frontend changes):**
```python
def inject(self, app):
    css_text = self._render()
    escaped = css_text.replace("\\", "\\\\").replace("`", "\\`")
    app.on_mounted(lambda: app.js.eval(
        f"var s=document.createElement('style');s.textContent=`{escaped}`;document.head.appendChild(s)"
    ))
```

**Option B — New `inject_css` method on frontend (cleaner, tiny JS change):**

Add to `Component.ts`:
```javascript
const inject_css = async (data) => {
    const el = document.createElement('style');
    el.textContent = data.css;
    document.head.appendChild(el);
};
```

Register it alongside `update_frontend` in `initMounted`. Python side:
```python
def inject(self, app):
    app._update_frontend({"css": self._render()}, method="inject_css")
```

**Recommendation:** Start with Option A (zero frontend changes). Migrate to Option B
later if needed.

---

## Implementation Plan

### Phase 1: Core module — `ngapp/src/ngapp/style.py` (~120 LOC)

| Class | Size | Description |
|-------|------|-------------|
| `Style` | ~40 LOC | Composable CSS property bag with `\|` merge and `__str__` |
| `Theme` | ~30 LOC | Design token namespace with `sp()`, `border_line()` helpers |
| `CssClass` | ~15 LOC | Thin wrapper around class name string, `+` to compose |
| `StyleSheet` | ~40 LOC | `add(style)` → `CssClass`, renders CSS, injects into DOM |

### Phase 2: Framework integration (~10 LOC across 2 files)

**`basecomponent.py`** — accept `Style` objects in `ui_style`:
```python
# In __init__, extend the existing ui_style handling:
elif hasattr(ui_style, '__str__') and not isinstance(ui_style, (str, dict)):
    self._props["style"] = str(ui_style)

# In ui_style setter:
@ui_style.setter
def ui_style(self, value):
    if not isinstance(value, str):
        value = str(value)
    self._set_prop("style", value)
```

Backwards-compatible — strings and dicts keep working.

### Phase 3: Tests — `ngapp/tests/test_style.py` (~80 LOC)

- `Style` rendering, merge with `|`, `None` removal
- `Theme` token access, `sp()`, `border_line()`
- `CssClass` composition with `+`, `str()`, mixing with plain strings
- `StyleSheet.add()` returns `CssClass`, CSS rendering

### Phase 4: Migrate `gui` app (incremental, per-file)

1. Create `gui/src/ngsolve_gui/theme.py` — define `theme`, `css` (StyleSheet), shared styles
2. Update `styles.py` → replace `sidebar_style()` with classes
3. Update `keybindings.py` → replace duplicated indicator/overlay strings
4. Update `navigator.py`, `property_panel.py` → use `css["section-heading"]`
5. Update `app.py` → call `css.inject(self)`, derive `_colors` from `theme`
6. Update sections → use theme tokens for any remaining inline colors

Each file is independent. No big-bang migration needed.

### Summary

| Item | Location | Size |
|------|----------|------|
| `style.py` | `ngapp/src/ngapp/style.py` | ~130 LOC |
| Framework patch | `basecomponent.py` | ~10 LOC |
| Tests | `ngapp/tests/test_style.py` | ~80 LOC |
| App theme | `gui/theme.py` | ~50 LOC |
| File migrations | `gui/**/*.py` | incremental |

**Total new code: ~220 lines** for core + tests. No new dependencies.

---

## Design Decisions

**Why CSS classes over inline styles?**
Efficiency. The Python→JS bridge sends component props as JSON. Inline styles are
~100-300 bytes per component. A class name is ~20 bytes. With 50+ components sharing
styles, that's a meaningful reduction. The browser also handles class-based styling
more efficiently (style recalc, caching).

**Why keep `Style` objects too (not just classes)?**
Truly dynamic values (e.g., `background_color=self.to_hex_string()` for a color
picker) must be inline. `Style` gives those a clean API. The pattern is: shared/static
→ class, dynamic/per-instance → inline `Style`.

**Why auto-generated class names (`s0`, `s1`, ...) instead of user-provided names?**
The Python variable *is* the name. `sidebar_left = css.add(...)` is self-documenting.
String keys would be redundant (`css.add("sidebar_left", ...)` then `css["sidebar_left"]`).
Auto-generated names are also shorter on the wire.

**Why `|` for merge?**
Matches Python `dict |` semantics (PEP 584). Communicates "last value wins" = CSS
cascade in miniature.

**Why no implicit int→px conversion?**
`z_index=9999` must not become `"9999px"`. Explicit strings are unambiguous.

**Why `+` for class composition (not `|`)?**
`+` means concatenation — you're joining class names, not overriding properties.
`|` is for `Style` merging where last-value-wins semantics apply.
Different operations, different operators.

**Why `CssClass` mixes with plain strings?**
Quasar utility classes (`"bg-primary text-grey-4"`) and custom classes must coexist.
`indicator + flex + "bg-primary"` just works — `CssClass.__add__` handles both
`CssClass` and `str` on the right side, `__radd__` handles `str` on the left.
