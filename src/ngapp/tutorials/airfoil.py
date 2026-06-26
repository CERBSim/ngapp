"""The workshop guide - you should NOT need to edit this file.

``load_tutorial(app)`` wraps your running app with a guide drawer (overview of
all steps + the current instruction + Back/Next) and a floating code popup that
hands you the snippet for the current step.  You copy that snippet into
``app.py``, save, and the app hot-reloads with the new piece in place.

It is additive: it only wraps ``app.component``, so your app keeps working
exactly as written.  We build the steps up together - only the first ones carry
code so far; the rest are the outline of where we are heading.
"""

from __future__ import annotations

import ast
import difflib
import functools
import sys

from pathlib import Path

from ngapp.components.basecomponent import BlockFrontendUpdate
from ngapp.components import (
    Col,
    Div,
    Heading,
    Label,
    Observable,
    QBadge,
    QBtn,
    QCard,
    QCardActions,
    QCardSection,
    QDialog,
    QExpansionItem,
    QIcon,
    QItem,
    QItemLabel,
    QItemSection,
    QLinearProgress,
    QScrollArea,
    QSeparator,
    QSpace,
    QSplitter,
    Row,
    Span,
)

# --------------------------------------------------------------------------- #
#  Python syntax highlighting for the code/diff view, via Pygments (already a
#  dependency).  We use its lexer for tokenising and tag each token with a CSS
#  class (not an inline color); the actual colors live in the stylesheet, with a
#  light palette by default and a dark palette under ``[data-theme="dark"]`` so
#  the code box follows the app's dark-mode toggle.  ``_highlight_source``
#  returns one list of ``(text, css_class)`` segments per source line
#  (``css_class`` ``None`` means "inherit the box's default text color").  If
#  Pygments is somehow unavailable we fall back to plain, uncolored lines.
#
#  ``_TOKEN_COLORS`` maps a class to ``(light, dark)`` hex values, kept readable
#  on the subtle green/red diff tints in both themes.
# --------------------------------------------------------------------------- #
_TOKEN_COLORS = {
    "afg-kw": ("#cf222e", "#ff7b72"),       # keywords
    "afg-str": ("#0a3069", "#a5d6ff"),      # strings
    "afg-num": ("#0550ae", "#79c0ff"),      # numbers
    "afg-com": ("#6e7781", "#8b949e"),      # comments
    "afg-def": ("#8250df", "#d2a8ff"),      # function/class names, decorators
    "afg-builtin": ("#953800", "#ffa657"),  # builtins and self/cls
}
# code box background / default text, per theme
_CODE_BG = ("#f6f8fa", "#0d1117")
_CODE_FG = ("#1f2328", "#e6edf3")

try:
    from pygments.lexers import PythonLexer
    from pygments.token import Comment, Keyword, Name, Number, String

    # stripnl/ensurenl off so the token stream is a lossless copy of the source
    # and reconstructs to exactly the same lines.
    _LEXER = PythonLexer(stripnl=False, ensurenl=False)
except Exception:  # pragma: no cover - Pygments missing
    _LEXER = None


def _color_for(tok_type):
    if tok_type in Comment:
        return "afg-com"
    if tok_type in String:
        return "afg-str"
    if tok_type in Number:
        return "afg-num"
    if tok_type in Keyword:
        return "afg-kw"
    if (tok_type in Name.Function or tok_type in Name.Class
            or tok_type in Name.Decorator):
        return "afg-def"
    if tok_type in Name.Builtin:
        return "afg-builtin"
    return None  # operators, plain names, whitespace -> box default color


def _highlight_source(src):
    """Return ``(text, css_class)`` segments per line of ``src`` (Pygments)."""
    plain = [[(ln, None)] if ln else [] for ln in src.split("\n")]
    if _LEXER is None:
        return plain
    lines = [[] for _ in plain]
    idx = 0
    try:
        for tok_type, value in _LEXER.get_tokens(src):
            css_class = _color_for(tok_type)
            for k, part in enumerate(value.split("\n")):
                if k:
                    idx += 1
                if 0 <= idx < len(lines) and part:
                    lines[idx].append((part, css_class))
    except Exception:  # pragma: no cover - lexer hiccup -> plain text
        return plain
    return lines

# --------------------------------------------------------------------------- #
#  Step 1 - the code the participant pastes to create the input panel.
# --------------------------------------------------------------------------- #
PANEL_CODE = '''\
# --- the airfoil input panel: four different input widgets ------------
# a slider for the camber (the bubble sits above the thumb, so add a top
# margin to keep it clear of the label)
self.camber = QSlider(ui_min=0, ui_max=9, ui_step=1, ui_model_value=2,
                      ui_label_always=True, ui_markers=True,
                      ui_style="margin-top: 30px;")

# a dropdown for the camber position
self.camber_pos = QSelect(ui_label="Camber position (%)", ui_outlined=True,
                          ui_options=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90],
                          ui_model_value=40)

# a number field for the thickness
self.thickness = QInput(ui_label="Thickness (%)", ui_type="number",
                        ui_model_value=12, ui_outlined=True)

# a rotary knob for the angle of attack
self.angle = QKnob(ui_min=-5, ui_max=15, ui_step=1, ui_model_value=5,
                   ui_show_value=True, ui_size="90px",
                   ui_color="primary", ui_track_color="grey-3")

self.input_panel = Col(
    Heading("Airfoil", 6),
    Label("Max camber (%)"), self.camber,
    self.camber_pos,
    self.thickness,
    Label("Angle of attack (°)"), Centered(self.angle),
    ui_style="width: 340px; height: 100%; padding: 24px; gap: 12px;",
)

self.component = self.input_panel
'''


# --------------------------------------------------------------------------- #
#  Full-file checkpoints.  Jumping to a step rewrites app.py to its checkpoint,
#  discarding the participant's edits, so they can always get back to a known
#  good state.  Built from the header + the step's body to avoid drift.
# --------------------------------------------------------------------------- #
_FILE_HEADER = '''\
"""This is your app - the file you edit during the workshop.

The workshop guide attaches itself automatically (via metaclass=TutorialMeta),
so there is nothing tutorial-related to keep in __init__ - everything inside
the class body is yours to rewrite.
"""

from ngapp.app import App
from ngapp.components import *

from ngapp.tutorials.airfoil import TutorialMeta


class AirfoilChallenge(App, metaclass=TutorialMeta):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
'''


def _indent(code, n=8):
    pad = " " * n
    return "\n".join(pad + ln if ln.strip() else "" for ln in code.splitlines())


# --------------------------------------------------------------------------- #
#  A tiny patch engine: blocks with an ``op`` ("add"/"replace") can be applied
#  straight to app.py - but only if the target method still matches its known
#  baseline (otherwise the user has edited it and must apply the diff by hand).
# --------------------------------------------------------------------------- #
_APP_FILE = None  # set by load_tutorial() to the running app's app.py


def _app_path():
    return _APP_FILE


def _read_app():
    try:
        return _app_path().read_text(encoding="utf-8")
    except Exception:
        return ""


def _norm(text):
    lines = [ln.rstrip() for ln in (text or "").splitlines()]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


def _class_methods(text):
    """name -> source for the direct methods of the first class in *text*."""
    out = {}
    try:
        tree = ast.parse(text)
    except Exception:
        return out
    lines = text.splitlines()
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for b in node.body:
                if isinstance(b, ast.FunctionDef):
                    out[b.name] = "\n".join(lines[b.lineno - 1:b.end_lineno])
    return out


def _snippet_methods(code):
    """name -> source for the methods defined in a class-body snippet."""
    return _class_methods("class _T:\n" + code)


def _apply_replace(text, name, new_code):
    tree = ast.parse(text)
    lines = text.splitlines()
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for b in node.body:
                if isinstance(b, ast.FunctionDef) and b.name == name:
                    merged = lines[:b.lineno - 1] + new_code.splitlines() + lines[b.end_lineno:]
                    return "\n".join(merged) + ("\n" if text.endswith("\n") else "")
    return text


def _apply_add(text, code):
    tree = ast.parse(text)
    lines = text.splitlines()
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            last = max((b.end_lineno for b in node.body), default=node.lineno)
            merged = lines[:last] + [""] + code.splitlines() + lines[last:]
            return "\n".join(merged) + ("\n" if text.endswith("\n") else "")
    return text


def _block_status(block, methods):
    """Return None (copy-only) or one of apply / done / manual."""
    if block.get("atomic"):
        bm = _snippet_methods(block["code"])
        base = block.get("base", {})
        if bm and all(n in methods and _norm(methods[n]) == _norm(bm[n]) for n in bm):
            return "done"
        for n in bm:
            if n in base:                       # this step changes method n
                if n not in methods or _norm(methods[n]) != _norm(base[n]):
                    return "manual"
            elif n in methods and _norm(methods[n]) != _norm(bm[n]):
                return "manual"                 # an added method already exists, edited
        return "apply"
    op = block.get("op")
    if not op:
        return None
    bm = _snippet_methods(block["code"])
    names = list(bm)
    if not names:
        return None
    if op == "add":
        present = [n for n in names if n in methods]
        if not present:
            return "apply"
        if len(present) == len(names) and all(
                _norm(methods[n]) == _norm(bm[n]) for n in present):
            return "done"
        return "manual"
    # op == "replace"
    name = names[0]
    cur = methods.get(name)
    if cur is None or _norm(cur) == _norm(block.get("base", "")):
        # safe to (re)place - but only once any required methods exist
        need = block.get("requires", [])
        return "apply" if all(r in methods for r in need) else "wait"
    if _norm(cur) == _norm(bm[name]):
        return "done"
    return "manual"


def _apply_block(block):
    text = _read_app()
    if not text:
        return
    if block.get("atomic"):
        # apply every method in the block (replace if present, else add) in one
        # write - the result is exactly this step's checkpoint, always valid.
        for name, src in _snippet_methods(block["code"]).items():
            if name in _class_methods(text):
                text = _apply_replace(text, name, src)
            else:
                text = _apply_add(text, src)
        try:
            _app_path().write_text(text, encoding="utf-8")
        except Exception as exc:
            print("apply failed:", exc)
        return
    methods = _class_methods(text)
    bm = _snippet_methods(block["code"])
    names = list(bm)
    if block.get("op") == "replace" and names and names[0] in methods:
        text = _apply_replace(text, names[0], block["code"])
    else:
        text = _apply_add(text, block["code"])
    try:
        _app_path().write_text(text, encoding="utf-8")
    except Exception as exc:
        print("apply failed:", exc)


SNAPSHOT_WELCOME = _FILE_HEADER + '''
        # --- hello world (straight from ngapp.create_app) ----------------
        self.title = Heading("Airfoil Challenge")
        self.button = QBtn("Click me", ui_color="primary")
        self.counter_view = QInput(ui_model_value=0, ui_style="width: 200px;")
        self.button.on_click(self.increment_counter)
        self.component = Centered(
            self.title,
            self.button,
            self.counter_view,
            ui_style="padding-top: 50px;",
        )

    def increment_counter(self):
        self.counter_view.ui_model_value = int(self.counter_view.ui_model_value) + 1
'''

# =========================================================================== #
#  Method-based build.  The app is assembled from small methods from step 1, so
#  each step only ADDS or tweaks a method (picking is no longer a rebuild).  We
#  author a full checkpoint per step and DERIVE each step's patch (the methods
#  that changed) by diffing consecutive checkpoints - applied atomically, so
#  every step is a valid app.
# =========================================================================== #
_HEADER = '''\
"""This is your app - the file you edit during the workshop.

The workshop guide attaches itself automatically (via metaclass=TutorialMeta),
so everything inside the class is yours to rewrite.
"""

from ngapp.app import App
from ngapp.components import *

from ngapp.tutorials.airfoil import TutorialMeta


class AirfoilChallenge(App, metaclass=TutorialMeta):
'''

_INIT1 = '''    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.build_inputs()
        self.component = self.input_panel
'''
_INIT2 = '''    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.build_inputs()
        self.build_view()
        self.connect()
        self.build_layout()
'''
_INIT3 = '''    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.build_inputs()
        self.build_results()
        self.build_view()
        self.connect()
        self.build_layout()
'''
_INIT4 = '''    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.build_inputs()
        self.build_results()
        self.build_view()
        self.connect()
        self.build_layout()
        self.apply_style()
'''

_BUILD_INPUTS = '''    def build_inputs(self):
        # four different input widgets - slider, dropdown, number field, knob
        self.camber = QSlider(ui_min=0, ui_max=9, ui_step=1, ui_model_value=2,
                              ui_label_always=True, ui_markers=True,
                              ui_style="margin-top: 30px;")
        self.camber_pos = QSelect(ui_label="Camber position (%)", ui_outlined=True,
                                  ui_options=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90],
                                  ui_model_value=40)
        self.thickness = QInput(ui_label="Thickness (%)", ui_type="number",
                                ui_model_value=12, ui_outlined=True)
        self.angle = QKnob(ui_min=-5, ui_max=15, ui_step=1, ui_model_value=5,
                           ui_show_value=True, ui_size="90px",
                           ui_color="primary", ui_track_color="grey-3")
        self.input_panel = Col(
            Heading("Airfoil", 6),
            Label("Max camber (%)"), self.camber,
            self.camber_pos,
            self.thickness,
            Label("Angle of attack (°)"), Centered(self.angle),
            ui_style="width: 340px; height: 100%; padding: 24px; gap: 12px;",
        )
'''

_BUILD_RESULTS = '''    def build_results(self):
        # a lift/drag table + an L/D plot of every attempt, under the inputs
        self.history = []
        self.result_table = QTable(
            ui_columns=[{"name": "q", "label": "Quantity", "field": "q", "align": "left"},
                        {"name": "v", "label": "Value", "field": "v", "align": "right"}],
            ui_rows=[], ui_row_key="q", ui_dense=True, ui_flat=True,
            ui_bordered=True, ui_hide_pagination=True)
        self.plot = PlotlyComponent(id="ld_plot",
                                    ui_style="height: 230px; margin-top: 12px;")
        self.input_panel.ui_children = self.input_panel.ui_children + [
            QSeparator(ui_class="q-my-md"),
            Label("Results", ui_class="text-subtitle2"),
            self.result_table,
            self.plot,
        ]
'''

_BUILD_VIEW1 = '''    def build_view(self):
        self.webgpu = WebgpuComponent(id="viewport", width="100%", height="100%")
'''
_BUILD_VIEW2 = '''    def build_view(self):
        # reuse a component from another app: ngsolve_gui's pick-info card
        from ngsolve_gui.pick_overlay import PickOverlay
        self.webgpu = WebgpuComponent(id="viewport", width="100%", height="100%")
        self.pick_overlay = PickOverlay()
        # the card defaults to the bottom; pin it to the top-left of the canvas
        self.pick_overlay.ui_style = "top: 12px; right: 12px; left: auto; bottom: auto;"
'''

_CONNECT = '''    def connect(self):
        # redraw whenever an input changes, and draw once the canvas is mounted
        for w in (self.camber, self.thickness, self.angle):
            w.on_change(self.solve_and_draw)
        self.camber_pos.on_update_model_value(self.solve_and_draw)
        self.webgpu.on_mounted(self.solve_and_draw)
'''

_LAYOUT2 = '''    def build_layout(self):
        self.dark_mode = QToggle(ui_label="Dark", ui_icon="mdi-weather-night",
                                 ui_color="white", ui_model_value=False)
        toolbar = QToolbar(QToolbarTitle("Airfoil Challenge"), QSpace(),
                           self.dark_mode, ui_class="bg-primary text-white")
        self.component = Col(
            toolbar,
            Row(
                Div(self.input_panel,
                    ui_style="flex: 0 0 auto; height: 100%; overflow: auto;"),
                Div(self.webgpu,
                    ui_style="flex: 1 1 0; min-width: 0; height: 100%;"
                             " overflow: hidden; position: relative;"),
                ui_class="no-wrap items-stretch col-grow",
                ui_style="min-height: 0;",
            ),
            ui_class="no-wrap",
            ui_style="width: 100%; height: 100vh; overflow: hidden;",
        )
'''
_LAYOUT3 = '''    def build_layout(self):
        self.dark_mode = QToggle(ui_label="Dark", ui_icon="mdi-weather-night",
                                 ui_color="white", ui_model_value=False)
        toolbar = QToolbar(QToolbarTitle("Airfoil Challenge"), QSpace(),
                           self.dark_mode, ui_class="bg-primary text-white")
        self.component = Col(
            toolbar,
            Row(
                Div(self.input_panel,
                    ui_style="flex: 0 0 auto; height: 100%; overflow: auto;"),
                Div(self.webgpu, self.pick_overlay,
                    ui_style="flex: 1 1 0; min-width: 0; height: 100%;"
                             " overflow: hidden; position: relative;"),
                ui_class="no-wrap items-stretch col-grow",
                ui_style="min-height: 0;",
            ),
            ui_class="no-wrap",
            ui_style="width: 100%; height: 100vh; overflow: hidden;",
        )
'''

_SOLVE1 = '''    def solve_and_draw(self, *args):
        import ngsolve_webgpu as nw
        from .utils import solve
        result = solve(self.camber.ui_model_value, self.camber_pos.ui_model_value,
                       self.thickness.ui_model_value, self.angle.ui_model_value)
        mesh_data = nw.MeshData(result.mesh)
        cmap = nw.Colormap(colormap="viridis")
        renderer = nw.CFRenderer(nw.FunctionData(mesh_data, result.speed, order=3),
                                 colormap=cmap)
        self.webgpu.draw([renderer, nw.Colorbar(cmap)])
'''
_SOLVE2 = '''    def solve_and_draw(self, *args):
        import ngsolve_webgpu as nw
        from .utils import solve
        result = solve(self.camber.ui_model_value, self.camber_pos.ui_model_value,
                       self.thickness.ui_model_value, self.angle.ui_model_value)
        mesh_data = nw.MeshData(result.mesh)
        cmap = nw.Colormap(colormap="viridis")
        renderer = nw.CFRenderer(nw.FunctionData(mesh_data, result.speed, order=3),
                                 colormap=cmap)
        self.webgpu.draw([renderer, nw.Colorbar(cmap)])
        self.result_table.ui_rows = [
            {"q": "Lift  C_L", "v": f"{result.lift:.3f}"},
            {"q": "Drag  C_D", "v": f"{result.drag:.4f}"},
            {"q": "L / D",     "v": f"{result.ld:.1f}"},
        ]
        self.history.append(result.ld)
        self.plot.draw({
            "data": [{"x": list(range(1, len(self.history) + 1)), "y": self.history,
                      "type": "scatter", "mode": "lines+markers",
                      "line": {"color": "#1565C0"}}],
            "layout": {"margin": {"l": 44, "r": 14, "t": 52, "b": 36},
                       "title": {"text": "L/D over your attempts", "y": 0.92},
                       "xaxis": {"title": "attempt"}, "yaxis": {"title": "L/D"}},
        })
'''
_SOLVE3 = '''    def solve_and_draw(self, *args):
        import ngsolve_webgpu as nw
        from .utils import solve
        result = solve(self.camber.ui_model_value, self.camber_pos.ui_model_value,
                       self.thickness.ui_model_value, self.angle.ui_model_value)
        mesh_data = nw.MeshData(result.mesh)
        cmap = nw.Colormap(colormap="viridis")
        renderer = nw.CFRenderer(nw.FunctionData(mesh_data, result.speed, order=3),
                                 colormap=cmap)
        self.webgpu.draw([renderer, nw.Colorbar(cmap)])
        self.result_table.ui_rows = [
            {"q": "Lift  C_L", "v": f"{result.lift:.3f}"},
            {"q": "Drag  C_D", "v": f"{result.drag:.4f}"},
            {"q": "L / D",     "v": f"{result.ld:.1f}"},
        ]
        self.history.append(result.ld)
        self.plot.draw({
            "data": [{"x": list(range(1, len(self.history) + 1)), "y": self.history,
                      "type": "scatter", "mode": "lines+markers",
                      "line": {"color": "#1565C0"}}],
            "layout": {"margin": {"l": 44, "r": 14, "t": 52, "b": 36},
                       "title": {"text": "L/D over your attempts", "y": 0.92},
                       "xaxis": {"title": "attempt"}, "yaxis": {"title": "L/D"}},
        })
        self.setup_pick(renderer, result.mesh, result.speed)
'''

_SETUP_PICK = '''    def setup_pick(self, renderer, mesh, field):
        # hover picking: on_mousemove triggers a GPU pick at the cursor, the
        # result comes back through the renderer's on_select, and on_mouseout
        # hides the card when the pointer leaves the canvas.
        from ngsolve_webgpu.pick import MeshPickResult
        scene = self.webgpu.scene

        def on_select(event):
            try:
                r = MeshPickResult(event, mesh, scene.options, kind="surface")
                x, y, _ = r.world_pos
                self.pick_overlay.show_info("Flow", [
                    ("x", f"{x:.2f}"), ("y", f"{y:.2f}"),
                    ("speed", f"{r.evaluate(field, mesh):.3f}")], accent_last=True)
            except Exception:
                self.pick_overlay.hide()

        renderer.on_select(on_select)
        scene.input_handler.on_mousemove(
            lambda ev: scene.select(ev["canvasX"], ev["canvasY"])
            if ev.get("buttons", 0) == 0 else None)
        scene.input_handler.on_mouseout(lambda ev: self.pick_overlay.hide())
'''

_APPLY_STYLE = '''    def apply_style(self):
        # adopt the ngsolve_gui theme + wire the dark toggle to a user setting
        try:
            from ngsolve_gui.cerbsim_style import install, set_theme
            install(self)

            # self.usersettings is a per-user, per-app key/value store that
            # persists to a small JSON file on disk - so choices survive an app
            # restart. Restore the saved theme (default light on first run).
            self.dark_mode.ui_model_value = self.usersettings.get(
                "dark_mode", default=False)

            def toggle(*args):
                dark = bool(self.dark_mode.ui_model_value)
                set_theme(self, "dark" if dark else "light")
                try:
                    self.dark_mode.quasar.dark.set(dark)
                except Exception:
                    pass
                # remember the choice for next time
                self.usersettings.set("dark_mode", dark)

            self.dark_mode.on_update_model_value(toggle)
            self.on_mounted(toggle)   # apply the restored theme on startup
        except Exception as exc:
            print("ngsolve_gui style not available:", exc)

        # your own color palette, then your own CSS class on the panel
        self.set_colors(primary="#0E7C86", secondary="#3AA8B0", accent="#FF8A3D",
                        dark="#1F2933", positive="#2E9E5B", negative="#E5484D",
                        info="#3AA8B0", warning="#F5A524")
        from ngapp.style import Style, StyleSheet
        self.style_sheet = StyleSheet(prefix="af")
        card = self.style_sheet.add(Style(
            background="var(--panel, #ffffff)",
            border_left="4px solid var(--accent, #FF8A3D)",
            border_right="1px solid var(--border, #e0e0e0)",
            box_shadow="2px 0 16px rgba(0, 0, 0, 0.12)"), name="af-panel")
        self.style_sheet.inject(self)
        self.input_panel.ui_class = str(card)
'''


def _cp(*methods):
    return _HEADER + "\n".join(methods)


# Full method-based checkpoints (one per step).
CP_PANEL = _cp(_INIT1, _BUILD_INPUTS)
CP_VIEWPORT = _cp(_INIT2, _BUILD_INPUTS, _BUILD_VIEW1, _CONNECT, _SOLVE1, _LAYOUT2)
CP_RESULTS = _cp(_INIT3, _BUILD_INPUTS, _BUILD_RESULTS, _BUILD_VIEW1, _CONNECT,
                 _SOLVE2, _LAYOUT2)
CP_STYLING = _cp(_INIT4, _BUILD_INPUTS, _BUILD_RESULTS, _BUILD_VIEW1, _CONNECT,
                 _SOLVE2, _LAYOUT2, _APPLY_STYLE)
CP_PICKING = _cp(_INIT4, _BUILD_INPUTS, _BUILD_RESULTS, _BUILD_VIEW2, _CONNECT,
                 _SOLVE3, _LAYOUT3, _APPLY_STYLE, _SETUP_PICK)


def _derive(prev_cp, cp, text):
    """Patch block (code + base) = the methods that changed from prev_cp to cp."""
    prev = _class_methods(prev_cp)
    cur = _class_methods(cp)
    changed, base = [], {}
    for name, src in cur.items():
        if _norm(prev.get(name, "")) != _norm(src):
            changed.append(src)
            if name in prev:
                base[name] = prev[name]
    return {"text": text, "code": "\n".join(changed), "base": base, "atomic": True}


PANEL_BLOCK = _derive(SNAPSHOT_WELCOME, CP_PANEL,
    "build_inputs() creates the four input widgets and the panel. __init__ calls "
    "it and shows the panel.")
VIEWPORT_BLOCK = _derive(CP_PANEL, CP_VIEWPORT,
    "build_view() makes the canvas, solve_and_draw() solves the flow and draws "
    "it, connect() redraws when an input changes, and build_layout() puts the "
    "canvas next to the panel. __init__ calls them.")
RESULTS_BLOCK = _derive(CP_VIEWPORT, CP_RESULTS,
    "build_results() adds the lift/drag table and the plot below the inputs. "
    "solve_and_draw() fills them after each solve.")
STYLING_BLOCK = _derive(CP_RESULTS, CP_STYLING,
    "apply_style() loads the ngsolve_gui theme, sets the colors, styles the "
    "panel, and connects the dark toggle.")
PICKING_BLOCK = _derive(CP_STYLING, CP_PICKING,
    "build_view() also creates the PickOverlay, build_layout() puts it on the "
    "canvas, solve_and_draw() calls setup_pick(), and setup_pick() shows the "
    "field value where you hover. __init__ does not change.")

FINALIZE_CODE = '''\
# remove the metaclass and the tutorial import - the app is now yours
from ngapp.app import App
from ngapp.components import *


class AirfoilChallenge(App):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ...   # everything you built stays exactly as it is
'''

STEPS = [
    dict(
        icon="mdi-hand-wave",
        title="Welcome",
        sub="What we'll build",
        body=(
            "On the left is your app. Right now it is what "
            "python -m ngapp.create_app gives you: a heading, a button and a "
            "counter.\n\n"
            "An ngapp app is a Python class. It subclasses App, and self.component "
            "is a tree of UI components (Heading, QBtn, QSlider, Row, Col, ...) "
            "that render in the browser. You build the UI in Python, no HTML or "
            "JavaScript. It all lives in one file, ngapp_tutorial/app.py (of course you can "
            "split it up into multiple files later).\n\n"
            "Each step shows its change as a diff. Press Apply to write it into "
            "app.py; the app reloads and the new part shows up. If you edited "
            "that part yourself, Apply is disabled and you copy the change in by "
            "hand, so your edits are kept. You can always reset the app to a state by "
            "clicking on one of steps in the menu above.\n\n"
            "Over the next steps this becomes a small airfoil tool: set a NACA "
            "profile and look at the lift and drag.\n\n"
            "Press Next to start."
        ),
        code=None,
        snapshot=SNAPSHOT_WELCOME,
    ),
    dict(
        icon="mdi-tune-variant",
        title="The input panel",
        sub="NACA sliders",
        body=(
            "The four numbers of a NACA airfoil are a good reason to use four "
            "kinds of input: a slider (camber), a dropdown (camber position), a "
            "number field (thickness) and a knob (angle of attack).\n\n"
            "Apply the change and the panel replaces the hello-world.\n\n"
            "Try editing it: swap the knob for a QSlider, change the dropdown "
            "options, or add a control. Save and it reloads."
        ),
        blocks=[PANEL_BLOCK],
        done_attr="input_panel",  # once app.input_panel exists, hide the popup
        snapshot=CP_PANEL,
    ),
    dict(
        icon="mdi-cube-outline",
        title="3D viewport",
        sub="solve and draw",
        body=(
            "Now the airfoil gets a 3D view and a solver. build_view() adds a "
            "WebGPU canvas, solve_and_draw() runs a potential-flow solve and "
            "draws the result, and build_layout() puts the canvas next to the "
            "panel.\n\n"
            "The meshing and the solve are in utils.py; the app just calls "
            "solve() and draws what comes back.\n\n"
            "After Apply, the flow field shows up. Color is the speed, highest "
            "over the top of the wing. Move the inputs and it re-solves.\n\n"
            "There is also a toolbar with a dark toggle. It does nothing yet; the "
            "styling step connects it."
        ),
        blocks=[VIEWPORT_BLOCK],
        done_attr="webgpu",
        snapshot=CP_VIEWPORT,
        card_pos="left: 392px;",  # floats over where the viewport will appear
    ),
    dict(
        icon="mdi-chart-line",
        title="Results",
        sub="lift, drag, a table and a plot",
        body=(
            "The solver also returns lift and drag, so build_results() shows them "
            "in a table and adds a plot of the lift-to-drag ratio for each "
            "airfoil you try. solve_and_draw() fills both after every solve.\n\n"
            "Apply, then change the inputs and watch the table and plot update."
        ),
        blocks=[RESULTS_BLOCK],
        done_attr="result_table",
        snapshot=CP_RESULTS,
    ),
    dict(
        icon="mdi-palette",
        title="Styling",
        sub="adopt the ngsolve_gui look",
        body=(
            "apply_style() does three things:\n"
            "- install() loads the ngsolve_gui look (IBM Plex fonts, theme "
            "tokens, CSS) and connects the dark toggle.\n"
            "- set_colors() sets the app's color palette.\n"
            "- a small StyleSheet of your own adds a class on the panel, reusing "
            "ngsolve_gui's --panel and --border colors.\n\n"
            "The dark toggle is wired to a user setting. self.usersettings is a "
            "per-user, per-app key/value store backed by a small JSON file on "
            "disk:\n"
            "- usersettings.get(key, default=...) reads a value,\n"
            "- usersettings.set(key, value) writes and persists it,\n"
            "- usersettings.update(key) returns a ready-made on_update handler.\n"
            "Unlike app storage (which lives in one saved file), user settings "
            "are global to the user and the app, so they're the right place for "
            "preferences like the theme.\n\n"
            "Apply, then use the dark toggle: the whole app switches theme, and "
            "because we save the choice, it comes back the same way next time you "
            "start the app."
        ),
        blocks=[STYLING_BLOCK],
        done_attr="style_sheet",
        snapshot=CP_STYLING,
    ),
    dict(
        icon="mdi-crosshairs-gps",
        title="Picking",
        sub="hover to read the field",
        body=(
            "Two things here: reusing a component from another app, and reading "
            "values back from the canvas.\n\n"
            "build_view() now also creates ngsolve_gui's PickOverlay card, "
            "build_layout() puts it on the canvas, and setup_pick() handles the "
            "hover: it reads the element under the cursor off the GPU and "
            "evaluates the flow speed there. solve_and_draw() calls setup_pick() "
            "after each draw.\n\n"
            "Apply, then hover the flow to read the value under your cursor."
        ),
        blocks=[PICKING_BLOCK],
        done_attr="pick_overlay",
        snapshot=CP_PICKING,
    ),
    dict(
        icon="mdi-rocket-launch",
        title="Make it yours",
        sub="detach and play",
        body=(
            "That is the whole app. Now detach it from the tutorial.\n\n"
            "In app.py, drop the metaclass and the tutorial import. On the next "
            "save the guide goes away and you are left with your own app, just "
            "app.py and utils.py.\n\n"
            "This was never a throwaway scaffold: it is a full ngapp project "
            "(the same one python -m ngapp.create_app gives you), with a "
            "pyproject.toml and a GitHub Pages deploy workflow. It is already "
            "installed in editable mode, which is why python -m <name> works.\n\n"
            "To ship it: from the project folder run\n"
            "    pip install .\n"
            "and you get a console command named after your app, so you can "
            "launch it as an executable from anywhere - just type its name (the "
            "folder name) instead of python -m <name>. Add --dev for "
            "auto-reload.\n\n"
            "From here it is yours: tune the airfoil for the best lift-to-drag, "
            "or build on it (a streamlines view, a second airfoil, a save "
            "button).\n\n"
            "Docs: https://cerbsim.github.io/ngapp\n"
            "Publish it on GitHub Pages: "
            "https://cerbsim.github.io/ngapp/tutorials/host_on_github.html"
        ),
        paste="Replace the top of app.py with this:",
        code=FINALIZE_CODE,
        card_pos="left: 28px;",
    ),
]

_N_ACTIVE = sum(1 for s in STEPS if not s.get("upcoming"))

_CARD_BASE = (
    "position: fixed; top: 56px; z-index: 3000;"
    # The card grows to fit its content (header with Copy/Apply + the code), but
    # never past the viewport: ``max-height`` caps it and the body scrolls
    # vertically when the code is taller than the screen, so it stays reachable.
    # The header stays pinned; only the body scrolls.  Width is responsive.
    " width: min(860px, calc(100vw - 48px)); box-sizing: border-box;"
    " max-height: calc(100vh - 72px);"
    " display: flex; flex-direction: column;"
    " background: var(--panel, #ffffff); color: var(--fg, #1b222d);"
    " border: 1px solid var(--border, #e0e0e0); border-radius: 12px;"
    " box-shadow: 0 12px 32px rgba(0,0,0,0.28); padding: 16px;"
)
# where the popup floats per step - over the spot the pasted code will fill.
_CARD_POS_DEFAULT = "left: 28px;"

# default / min / max width of the resizable guide drawer (px)
_DRAWER_DEFAULT_W = 380
_DRAWER_MIN_W = 300
_DRAWER_MAX_W = 760


class _Tutorial:
    def __init__(self, app):
        self.app = app
        self.steps = STEPS
        self.current = Observable(0)
        self.block = 0   # active sub-step (code block) within the current step
        self.splitter = None  # set by load_tutorial; drives the drawer width

        # --- floating code popup (one or more labelled, copyable blocks) -
        # Copy/Apply live in this header (rebuilt per block in _refresh), so they
        # stay pinned at the top of the card - always visible and clickable, no
        # matter how long the diff is.
        self.code_actions = Row(ui_class="items-center no-wrap q-gutter-x-xs")
        self.code_header = Row(
            QIcon(ui_name="mdi-code-tags", ui_color="primary"),
            Label("Edit app.py", ui_class="text-weight-bold q-ml-sm"),
            QSpace(),
            self.code_actions,
            ui_class="items-center no-wrap",
            ui_style="flex: 0 0 auto;",
        )
        # The body holds the note + code box and is the single VERTICAL scroller:
        # it shrinks within the viewport-capped card so the header stays pinned
        # and long code becomes scrollable (reachable) instead of clipped.
        # It must be a plain block (not a flex column): a flex column would make
        # the code box a flex item that shrinks to nothing, hiding the code.
        # ``min-width: 0`` stops it (a flex item of the card) from expanding to
        # its widest line, so the box keeps the card width and scrolls sideways.
        self.code_body = Div(
            ui_class="afg-scroll",
            ui_style="flex: 0 1 auto; min-height: 0; min-width: 0;"
                     " overflow-y: auto; overflow-x: hidden; margin-top: 8px;",
        )
        self.code_card = Div(
            self.code_header,
            self.code_body,
            ui_style=_CARD_BASE,
        )

        # --- guide drawer (right) ----------------------------------------
        self.list_box = Col(ui_class="q-gutter-y-xs q-px-sm q-pt-sm")
        # The step text lives here.  It fills the space between the (foldable)
        # step list and the nav bar; ``min-height: 0`` lets it shrink inside the
        # flex column.  Folding the step list above gives long steps (e.g. the
        # final one) the room they need, so no scrollbar is needed in normal
        # use - ``overflow-y: auto`` is only a fallback for very short windows.
        self.body_box = Col(ui_class="col-grow",
                            ui_style="overflow-y: auto; min-height: 0;")
        self.progress = QLinearProgress(
            ui_value=0.0, ui_color="primary", ui_size="6px", ui_rounded=True,
            ui_class="q-mt-sm",
        )
        self.step_label = Label("", ui_class="text-caption",
                                ui_style="color: var(--fg-muted, #6b7689);")
        self.prev_btn = QBtn(
            ui_label="Back", ui_icon="mdi-chevron-left", ui_flat=True,
            ui_style="color: var(--fg-muted, #64748b);",  # readable in dark too
        ).on_click(self.prev)
        self.next_btn = QBtn(
            ui_label="Next", ui_icon_right="mdi-chevron-right",
            ui_unelevated=True, ui_color="primary",
        ).on_click(self.next)
        # --- confirm dialog for jumping to a step ------------------------
        self._pending = 0
        self.dialog_text = Label("", ui_class="text-body2")
        self.dialog = QDialog(
            QCard(
                QCardSection(Label("Jump to this step?", ui_class="text-h6")),
                QCardSection(self.dialog_text),
                QCardActions(
                    QSpace(),
                    QBtn(ui_label="Cancel", ui_flat=True,
                         ui_style="color: var(--fg-muted, #64748b);").on_click(
                        self._close_dialog
                    ),
                    QBtn(
                        ui_label="Reset & go",
                        ui_icon="mdi-restore",
                        ui_color="negative",
                        ui_unelevated=True,
                    ).on_click(self._confirm),
                    ui_align="right",
                ),
                ui_style="min-width: 360px;",
            ),
            ui_model_value=False,
        )

        self.drawer = self._build_drawer()

        self.current.on_change(lambda new, old: self._refresh())
        self._refresh()
        # survive hot reloads: restore the step from app storage on (re)load
        app.on_load(self._restore)

    # -- jump-to-step confirmation ----------------------------------------
    def _ask(self, i):
        def handler():
            # steps with a checkpoint rewrite app.py, so confirm first; steps
            # without one (e.g. the final graduate step) just navigate.
            if not self.steps[i].get("snapshot"):
                self._set(i)
                return
            self._pending = i
            self.dialog_text.text = (
                f"Go to “{self.steps[i]['title']}”? This rewrites app.py to the "
                "checkpoint for this step and discards your own changes."
            )
            self.dialog.ui_model_value = True

        return handler

    def _close_dialog(self):
        self.dialog.ui_model_value = False

    def _confirm(self):
        self.dialog.ui_model_value = False
        self._jump(self._pending)

    def _jump(self, i):
        # navigate first so the post-reload restore lands on this step
        self._set(i)
        snapshot = self.steps[i].get("snapshot")
        if snapshot:
            target = _app_path()
            if target is not None:
                try:
                    target.write_text(snapshot, encoding="utf-8")
                except Exception:
                    pass
        self._reset_theme()

    def _reset_theme(self):
        # The theme lives on the document (a <html data-theme> attribute, an
        # injected <style>, $q.dark) - an app reload does NOT undo it. So when
        # we reset to a checkpoint, clear it back to a light slate by hand.
        def _do(js):
            js.document.documentElement.setAttribute("data-theme", "light")
        try:
            self.code_card.call_js(_do)
        except Exception:
            pass
        try:
            self.code_card.quasar.dark.set(False)
        except Exception:
            pass

    # -- drawer width (persisted so it survives the tutorial's hot reloads) --
    def _save_width(self, event):
        try:
            self.app.storage.set("tutorial_width", float(event.value))
        except Exception:
            pass

    def _restore_width(self):
        if self.splitter is None:
            return
        try:
            w = float(self.app.storage.get("tutorial_width", 0) or 0)
        except (TypeError, ValueError):
            w = 0
        if w:
            self.splitter.ui_model_value = w

    # -- navigation --------------------------------------------------------
    def _restore(self):
        try:
            n = int(self.app.storage.get("tutorial_step", 0) or 0)
        except (TypeError, ValueError):
            n = 0
        self._set(n)
        self._restore_width()

    def _nblocks(self, step_index):
        return len(self._blocks(self.steps[step_index]))

    def _set(self, i, block=0):
        i = max(0, min(i, _N_ACTIVE - 1))
        self.block = block
        if self.current.value == i:
            self._refresh()             # same step, block changed -> redraw
        else:
            self.current.value = i      # fires on_change -> _refresh

    def _set_block(self, b):
        self.block = b
        self._refresh()

    def next(self):
        # advance through the sub-steps of this step, then to the next step
        if self.block < self._nblocks(self.current.value) - 1:
            self._set_block(self.block + 1)
        else:
            self._set(self.current.value + 1)

    def prev(self):
        if self.block > 0:
            self._set_block(self.block - 1)
        elif self.current.value > 0:
            prev_i = self.current.value - 1
            self._set(prev_i, block=max(0, self._nblocks(prev_i) - 1))

    # -- code blocks -------------------------------------------------------
    @staticmethod
    def _blocks(s):
        """Normalise a step to a list of {text, code} blocks."""
        if s.get("blocks"):
            return s["blocks"]
        if s.get("code"):
            return [{"text": s.get("paste", ""), "code": s["code"]}]
        return []

    def _copy_factory(self, code, comp):
        def handler():
            def writer(js):
                js.navigator.clipboard.writeText(code)
            try:
                comp.call_js(writer)
            except Exception:
                pass
        return handler

    def _apply_factory(self, block):
        def handler():
            _apply_block(block)          # writes app.py -> watcher hot-reloads
        return handler

    # One monospace line holding inline coloured spans (syntax highlighting).
    # ngapp renders each child component in its own block-level wrapper, so a
    # plain block line would stack every token vertically; a flex row (the same
    # trick Row/Col use) lays the spans out left-to-right instead.  ``nowrap``
    # keeps a long line on one row - the code box scrolls horizontally for it.
    # ``width: max-content`` lets a long line grow past the box (so the box
    # scrolls horizontally) while ``min-width: 100%`` keeps a short line's diff
    # tint spanning the full width.
    _LINE = ("display: flex; flex-wrap: nowrap; width: max-content;"
             " min-width: 100%; font-family: 'JetBrains Mono', monospace;"
             " font-size: 15px; line-height: 1.6; padding: 0 6px;")
    # each token keeps its own whitespace (indentation, gaps between tokens)
    # and must not shrink, or long lines would be squeezed instead of scrolling.
    _SPAN = "white-space: pre; flex: 0 0 auto;"
    # diff line tints (add/remove) come from theme-aware classes (afg-add/
    # afg-del); no +/- gutter so a line copies cleanly.  Context lines get none.
    # A self-contained scroll region: height-capped with both scrollbars at its
    # own edges, so the horizontal one is always reachable (instead of stranded
    # at the bottom of a tall diff that you first have to scroll down to).  Its
    # background/text color are themed via the ``.afg-code`` class.
    # The code box scrolls horizontally for long lines.  ``min-width: 0`` keeps
    # it from growing past the card (flex items default to their min-content
    # width); instead it stays at the card width and scrolls inside.
    _BOX = ("border-radius: 8px; padding: 10px 12px;"
            " overflow-x: auto; min-width: 0;")

    def _code_line(self, segments, line_class=""):
        """One syntax-highlighted code line, optionally with a diff tint.

        ``segments`` is a list of ``(text, css_class)`` (from
        ``_highlight_source``); ``line_class`` adds the diff tint (afg-add /
        afg-del).  No +/- gutter: the tint shows add/remove, and the line stays
        copy-pasteable as real code.
        """
        spans = [
            Span(text, ui_class=cls or "", ui_style=self._SPAN)
            for text, cls in segments
        ] or [Span(" ", ui_style=self._SPAN)]
        return Div(*spans, ui_class=line_class, ui_style=self._LINE)

    def _diff_lines(self, block, methods):
        """Highlighted add/remove/context lines comparing previous code to new."""
        bm = _snippet_methods(block["code"])
        if block.get("atomic"):
            base_map = block.get("base", {})
            # previous version of each method (changed methods only); added
            # methods have no baseline -> they show up as pure additions.
            base = "\n".join(base_map.get(n, "") for n in bm)
            new = "\n".join(bm[n] for n in bm)
        elif block.get("op") == "replace" and bm:
            name = list(bm)[0]
            base = methods.get(name, block.get("base", "")) or ""
            new = block["code"]
        else:
            base = ""                    # an "add" -> everything is new
            new = block["code"]
        base, new = _norm(base), _norm(new)
        a, b = base.split("\n"), new.split("\n")
        # highlight the whole snippet (so multi-line strings etc. are correct),
        # then index per line - aligned with ``a``/``b``.
        ha, hb = _highlight_source(base), _highlight_source(new)
        rows = []

        # group changes (all removals, then all additions per hunk) so the diff
        # reads as a clean "remove these / add these" instead of interleaved.
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b).get_opcodes():
            if tag in ("replace", "delete"):
                rows += [self._code_line(ha[i], "afg-del") for i in range(i1, i2)]
            if tag in ("replace", "insert"):
                rows += [self._code_line(hb[j], "afg-add") for j in range(j1, j2)]
            if tag == "equal":
                rows += [self._code_line(ha[i]) for i in range(i1, i2)]
        return rows

    def _block_view(self, block):
        """Return ``(actions, body)``: the header buttons (Copy/Apply) and the
        scrolling body (note + code box) for one block."""
        code = block["code"]
        note = block.get("text", "")
        note_color = "var(--fg-muted, #64748b)"
        copy = QBtn(ui_label="Copy", ui_icon="mdi-content-copy", ui_dense=True,
                    ui_flat=True, ui_color="primary")
        copy.on_click(self._copy_factory(code, copy))

        methods = _class_methods(_read_app())
        status = _block_status(block, methods)

        # Copy/Apply go into the pinned card header, so they never scroll away.
        actions = [copy]
        if status is None:
            lines = [self._code_line(seg) for seg in _highlight_source(code)] or \
                [self._code_line([])]
        else:
            lines = self._diff_lines(block, methods)
            if status == "apply":
                actions.append(QBtn(ui_label="Apply", ui_icon="mdi-check",
                                    ui_dense=True, ui_unelevated=True,
                                    ui_color="positive").on_click(self._apply_factory(block)))
            elif status == "done":
                actions.append(QBtn(ui_label="Applied", ui_icon="mdi-check-all",
                                    ui_dense=True, ui_flat=True, ui_color="positive",
                                    ui_disable=True))
            elif status == "wait":
                note += "  ·  apply the blocks above first"
                actions.append(QBtn(ui_label="Apply", ui_icon="mdi-check",
                                    ui_dense=True, ui_flat=True, ui_disable=True))
            else:  # manual - user has edited this part
                note += "  ·  ⚠ you've edited this - apply the diff by hand (Copy)"
                note_color = "var(--warning, #b8860b)"
                actions.append(QBtn(ui_label="Apply", ui_icon="mdi-pencil-off",
                                    ui_dense=True, ui_flat=True, ui_disable=True))

        body = [
            Label(note, ui_class="text-body2 q-mb-sm",
                  ui_style=f"color: {note_color}; white-space: pre-line;"
                           " display: block;"),
            Div(*lines, ui_class="afg-code", ui_style=self._BOX),
        ]
        return actions, body

    # -- rendering ---------------------------------------------------------
    def _is_done(self, s):
        """A code step counts as done once the attribute it creates exists."""
        attr = s.get("done_attr")
        return bool(attr) and hasattr(self.app, attr)

    def _refresh(self):
        n = self.current.value
        s = self.steps[n]
        done = self._is_done(s)
        blocks = self._blocks(s)
        self.block = max(0, min(self.block, len(blocks) - 1)) if blocks else 0

        # persist the step so a hot reload returns to it
        try:
            self.app.storage.set("tutorial_step", int(n))
        except Exception:
            pass

        # step list - the active step expands to show its sub-steps (blocks)
        items = []
        for i, st in enumerate(self.steps):
            items.append(self._list_item(i, st))
            if i == n and len(blocks) > 1:
                items += [self._sub_item(bi, b) for bi, b in enumerate(blocks)]
        self.list_box.ui_children = items

        body_children = [
            Label(s["title"], ui_class="text-h6"),
            Label(
                s["body"],
                ui_class="text-body2 q-mt-sm",
                ui_style="white-space: pre-line; color: var(--fg, #1b222d);",
            ),
        ]
        if done:
            body_children.append(
                Row(
                    QIcon(ui_name="mdi-check-circle", ui_color="positive"),
                    Label(
                        "Done - it's on the left. Press Next →",
                        ui_class="text-positive text-weight-medium q-ml-sm",
                    ),
                    ui_class="items-center q-mt-md",
                )
            )
        self.body_box.ui_children = [Div(*body_children, ui_class="q-pa-md")]

        self.progress.ui_value = (n + 1) / _N_ACTIVE
        label = f"Step {n + 1} of {_N_ACTIVE}"
        if len(blocks) > 1:
            label += f"  ·  part {self.block + 1} of {len(blocks)}"
        self.step_label.text = label
        self.prev_btn.ui_disable = n == 0 and self.block == 0
        self.next_btn.ui_disable = (n == _N_ACTIVE - 1
                                    and self.block == max(0, len(blocks) - 1))

        # show one block at a time (the active sub-step), hidden once done
        if blocks and not done:
            actions, body = self._block_view(blocks[self.block])
            self.code_actions.ui_children = actions
            self.code_body.ui_children = body
            self.code_card.ui_style = (
                _CARD_BASE + " " + s.get("card_pos", _CARD_POS_DEFAULT)
            )
        else:
            self.code_card.ui_style = _CARD_BASE + " display: none;"

    def _list_item(self, i, s):
        n = self.current.value
        upcoming = s.get("upcoming", False)
        done = (not upcoming) and (i < n or self._is_done(s))
        active = i == n
        if done:
            badge = QIcon(ui_name="mdi-check-circle", ui_color="positive", ui_size="24px")
        elif upcoming:
            badge = QIcon(ui_name=s["icon"], ui_color="grey-4", ui_size="22px")
        else:
            badge = QBadge(
                str(i + 1),
                ui_color="primary" if active else "grey-5",
                ui_rounded=True,
                ui_style="min-width: 22px; min-height: 22px; justify-content: center;",
            )
        item = QItem(
            QItemSection(badge, ui_avatar=True),
            QItemSection(
                QItemLabel(
                    s["title"],
                    ui_class=("text-grey-5" if upcoming else "text-weight-medium" if active else ""),
                ),
                QItemLabel(s["sub"], ui_caption=True),
            ),
            ui_clickable=not upcoming,
            ui_active=active,
            ui_active_class="bg-blue-1 text-primary",
            ui_class="rounded-borders",
        )
        if not upcoming:
            item.on("click", self._ask(i))
        return item

    def _go_block(self, b):
        return lambda *a: self._set_block(b)

    def _sub_item(self, bi, block):
        active = bi == self.block
        txt = block.get("label") or block.get("text", "") or f"Part {bi + 1}"
        short = txt.split(":")[0].strip()
        if len(short) > 42:
            short = short[:40].rstrip() + "..."
        item = QItem(
            QItemSection(
                QIcon(ui_name="mdi-circle-medium" if active else "mdi-circle-small",
                      ui_color="primary" if active else "grey-5", ui_size="18px"),
                ui_avatar=True),
            QItemSection(QItemLabel(
                short, ui_class="text-weight-medium" if active else "")),
            ui_clickable=True,
            ui_active=active,
            ui_active_class="bg-blue-1 text-primary",
            ui_class="rounded-borders q-ml-lg",   # indented under the parent step
            ui_style="min-height: 30px;",
        )
        item.on("click", self._go_block(bi))
        return item

    def _build_drawer(self):
        header = Div(
            Row(
                QIcon(ui_name="mdi-airplane", ui_color="primary", ui_size="24px"),
                Heading("ngapp Tutorial - Airfoil", 6, ui_class="q-my-none q-ml-sm"),
                ui_class="items-center no-wrap",
            ),
            self.step_label,
            self.progress,
            ui_class="q-pa-md",
            ui_style="border-bottom: 1px solid var(--border, #e0e0e0);",
        )
        nav = Row(
            self.prev_btn,
            QSpace(),
            self.next_btn,
            ui_class="q-pa-md items-center",
            ui_style="border-top: 1px solid var(--border, #e0e0e0); padding-bottom: 44px;",
        )
        # The step overview folds away (QExpansionItem) so long step text can
        # use the full height instead of needing a scrollbar.
        steps_list = QExpansionItem(
            QScrollArea(self.list_box, ui_style="height: 300px;"),
            ui_label="Steps",
            ui_icon="mdi-format-list-numbered",
            ui_default_opened=True,
            ui_dense=True,
            ui_header_class="text-weight-medium",
        )
        return Col(
            header,
            steps_list,
            QSeparator(),
            self.body_box,
            nav,
            self.dialog,
            ui_class="column no-wrap afg",
            # width is driven by the (resizable) container in load_tutorial.
            ui_style=(
                "width: 100%; height: 100vh;"
                " background: var(--panel, #fafafa); color: var(--fg, #1b222d);"
                " border-left: 1px solid var(--border, #e0e0e0);"
            ),
        )


def load_tutorial(app):
    """Wrap ``app`` with the guide drawer and the floating code popup."""
    global _APP_FILE
    _mod = sys.modules.get(type(app).__module__)
    if _mod is not None and getattr(_mod, "__file__", None):
        _APP_FILE = Path(_mod.__file__)
    tut = _Tutorial(app)
    app.tutorial = tut  # keep a reference alive

    # Quasar hardcodes a dark caption color; map it to the theme token so the
    # guide stays readable in dark mode (black-on-black otherwise).
    from ngapp.style import Style, StyleSheet
    guide_css = StyleSheet(prefix="afg")
    guide_css.add_rule(".afg .q-item__label--caption",
                       Style(color="var(--fg-muted, #64748b)"))
    # Keep the splitter panels from adding their own scrollbars - each side
    # manages its own layout (the app on the left, the drawer on the right).
    guide_css.add_rule(".afg-panel", Style(overflow="hidden", padding="0"))

    # --- code box theming: light by default, dark under the app's theme ------
    # ngsolve_gui's dark toggle sets ``data-theme="dark"`` on <html> (the same
    # switch that drives --panel/--fg everywhere else), so the code box follows
    # it via ``[data-theme="dark"]`` - NOT Quasar's body--dark, which the rest of
    # the app doesn't use.
    DARK = '[data-theme="dark"] '
    guide_css.add_rule(".afg-code",
                       Style(background=_CODE_BG[0], color=_CODE_FG[0]))
    guide_css.add_rule(DARK + ".afg-code",
                       Style(background=_CODE_BG[1], color=_CODE_FG[1]))
    # syntax token colors
    for cls, (lc, dc) in _TOKEN_COLORS.items():
        guide_css.add_rule(f".{cls}", Style(color=lc))
        guide_css.add_rule(DARK + f".{cls}", Style(color=dc))
    # diff tints (slightly stronger on the dark box)
    guide_css.add_rule(".afg-add", Style(background="rgba(46,160,67,0.15)"))
    guide_css.add_rule(".afg-del", Style(background="rgba(207,34,46,0.12)"))
    guide_css.add_rule(DARK + ".afg-add", Style(background="rgba(46,160,67,0.18)"))
    guide_css.add_rule(DARK + ".afg-del", Style(background="rgba(248,81,73,0.18)"))

    # Thin, theme-matched scrollbars: the body scrolls vertically (long code),
    # the code box horizontally (long lines) - native ones look jarring.
    for sel in (".afg-code", ".afg-scroll"):
        guide_css.add_rule(sel + "::-webkit-scrollbar",
                           Style(width="10px", height="10px"))
        guide_css.add_rule(sel + "::-webkit-scrollbar-track",
                           Style(background="transparent"))
        guide_css.add_rule(sel + "::-webkit-scrollbar-thumb",
                           Style(background="rgba(140,149,159,0.35)",
                                 border_radius="6px"))
        guide_css.add_rule(DARK + sel + "::-webkit-scrollbar-thumb",
                           Style(background="#30363d", border_radius="6px"))
    guide_css.inject(app)
    main = app.component

    # A Quasar QSplitter gives a real, draggable separator between the app
    # (left) and the guide drawer (right).  ``reverse`` makes the model size the
    # second panel, so the model value is simply the drawer width in px.
    splitter = QSplitter(
        ui_model_value=_DRAWER_DEFAULT_W,
        ui_reverse=True,
        ui_unit="px",
        ui_limits=[_DRAWER_MIN_W, _DRAWER_MAX_W],
        ui_before_class="afg-panel",
        ui_after_class="afg-panel",
        ui_style="position: fixed; inset: 0;",
    )
    splitter.ui_slot_before = [
        Div(main, ui_style="position: relative; height: 100%; overflow: hidden;")
    ]
    splitter.ui_slot_after = [tut.drawer]
    # persist the width the user drags to (survives the tutorial's hot reloads)
    splitter.on("update:model-value", tut._save_width)
    tut.splitter = splitter
    # The floating code card is a top-level sibling of the splitter (not inside
    # the clipped left panel) so it floats above everything - the drawer can no
    # longer paint over its right edge and hide the Apply button.
    app.component = Div(splitter, tut.code_card, ui_style="position: fixed; inset: 0;")


class TutorialMeta(BlockFrontendUpdate):
    """Metaclass that attaches the workshop guide automatically.

    The app class simply declares ``metaclass=TutorialMeta``; the guide is wired
    in right after ``__init__`` runs. Participants can rewrite the entire
    ``__init__`` body without ever losing the tutorial - there is no
    ``load_tutorial()`` line to delete by accident.
    """

    def __new__(mcs, name, bases, dct):
        cls = super().__new__(mcs, name, bases, dct)
        if "__init__" in dct:
            base_init = cls.__init__

            @functools.wraps(base_init)
            def init_with_tutorial(self, *args, **kwargs):
                base_init(self, *args, **kwargs)
                load_tutorial(self)

            cls.__init__ = init_with_tutorial
        return cls
