"""Pytest infrastructure for testing ngapp apps that use WebGPU components.

Downstream projects register this module as a pytest plugin to get a
Chrome browser with WebGPU support and a helper for visual regression
testing of canvas elements.

Usage in ``conftest.py``::

    from pathlib import Path
    import ngapp.e2e_webgpu as e2e_webgpu

    pytest_plugins = ["ngapp.e2e_webgpu"]

    TESTS_DIR = Path(__file__).parent
    e2e_webgpu.configure(
        output_dir=TESTS_DIR / "output",
        baseline_dir=TESTS_DIR / "baselines",
    )

Then in tests::

    from ngapp.e2e import app_test
    from ngapp.e2e_webgpu import assert_matches_baseline

    @app_test("my_3d_app")
    def test_scene(page, app):
        # draws happen via app-specific helpers, then just assert:
        assert_matches_baseline(page, app.my_canvas, "expected.png")
"""

from __future__ import annotations

import os
import shutil
import time
from pathlib import Path

import numpy as np
import pytest
from PIL import Image
from playwright.sync_api import Locator, sync_playwright

CHROMIUM_WEBGPU_ARGS = [
    "--no-sandbox",
    "--enable-unsafe-webgpu",
    "--enable-features=Vulkan,UnsafeWebGPU",
    "--use-vulkan=native",
    "--ignore-gpu-blocklist",
    "--disable-dev-shm-usage",
    "--enable-dawn-features=allow_unsafe_apis,disable_adapter_blocklist",
]

_output_dir: Path | None = None
_baseline_dir: Path | None = None

UPDATE_BASELINES = os.environ.get("UPDATE_BASELINES", "") == "1"

# Replace requestAnimationFrame with a no-op.  The scene's render() method
# calls _render_objects(to_canvas=False) which writes into target_texture
# *before* calling patchedRequestAnimationFrame (which only copies to the
# on-screen canvas).  Tests read target_texture directly, so the canvas
# copy is unnecessary.
_NOOP_RAF_JS = """
window.requestAnimationFrame = function() {};
"""

# How long to wait (ms) for the scene to finish initialising (GPU pipeline
# creation, first render, etc.) after it first appears.
_SCENE_INIT_WAIT_MS = 2000

# How long to wait (ms) after the scene is known to be ready, to let a
# debounced render triggered by a UI click complete.
_RENDER_SETTLE_MS = 1000


def configure(output_dir: Path | str, baseline_dir: Path | str) -> None:
    """Set the output and baseline directories for screenshot comparison."""
    global _output_dir, _baseline_dir
    _output_dir = Path(output_dir)
    _baseline_dir = Path(baseline_dir)


def _locator_for(page, target) -> Locator:
    """Resolve *target* to a Playwright Locator.

    *target* may be:
    - a Playwright ``Locator`` (returned as-is)
    - a CSS selector string
    - a ``WebgpuComponent`` instance (resolved to ``page.locator("canvas")``)
    """
    if isinstance(target, Locator):
        return target
    if isinstance(target, str):
        return page.locator(target)
    from ngapp.components.visualization import WebgpuComponent

    if isinstance(target, WebgpuComponent):
        return page.locator("canvas")
    raise TypeError(f"Cannot resolve target of type {type(target)}")


# Track which WebgpuComponent instances have already had their scene
# initialised (first render wait done).  Keyed by id(target).
_initialised_scenes: set[int] = set()


def _ensure_scene_ready(page, target, timeout: float = 30) -> None:
    """Wait for the WebgpuComponent's scene and canvas to exist.

    On the *first* call for a given target, waits for GPU pipelines to
    finish initialising.  On subsequent calls (after UI interactions)
    just waits long enough for the debounced render to complete.

    Does **not** reset the camera or perform any app-specific setup —
    that belongs in the test code.
    """
    target_key = id(target)
    first_time = target_key not in _initialised_scenes

    if first_time:
        # Poll until scene + canvas exist.
        deadline = time.time() + timeout
        while time.time() < deadline:
            if target.scene is not None and target.scene.canvas is not None:
                break
            page.wait_for_timeout(200)
        else:
            raise AssertionError(
                f"WebgpuComponent scene not initialised after {timeout}s"
            )

        # Give GPU pipelines time to finish building.
        page.wait_for_timeout(_SCENE_INIT_WAIT_MS)

        # Trigger a render (first call is not debounced — executes
        # immediately) and wait for it.
        target.scene.render()
        page.wait_for_timeout(_RENDER_SETTLE_MS)

        _initialised_scenes.add(target_key)
    else:
        # A UI click already triggered scene.render() via the normal
        # callback path.  Just wait for the debounce + render to finish.
        page.wait_for_timeout(_RENDER_SETTLE_MS)


def _readback_webgpu_texture(page, target, out_path: Path, size: tuple[int, int] = (800, 600)) -> None:
    """Read back the GPU texture from a WebgpuComponent at a fixed size.

    Forces the canvas to *size* (width, height) before rendering so that
    screenshots are independent of the actual browser layout.
    """
    from webgpu.utils import read_texture

    scene = target.scene
    assert (
        scene is not None
    ), "WebgpuComponent.scene is None — draw() hasn't run"

    # Force the HTML canvas element to a fixed size and re-create GPU textures
    canvas = scene.canvas
    html_canvas = canvas.canvas
    width, height = size
    html_canvas.style.width = f"{width}px"
    html_canvas.style.height = f"{height}px"
    canvas.resize()
    scene._render_objects(to_canvas=False)
    page.wait_for_timeout(200)

    texture = canvas.target_texture
    data = read_texture(texture)

    if texture.format == "bgra8unorm":
        data = data[:, :, [2, 1, 0, 3]]

    Image.fromarray(data[:, :, :3]).save(str(out_path))


def assert_matches_baseline(
    page,
    target,
    filename: str,
    *,
    size: tuple[int, int] = (800, 600),
    threshold: float = 0.01,
    output_dir: Path | str | None = None,
    baseline_dir: Path | str | None = None,
) -> None:
    """Screenshot a canvas element and compare against a baseline image.

    For :class:`~ngapp.components.visualization.WebgpuComponent` targets
    this function automatically waits for the scene to be ready and for
    any pending render (triggered by a prior UI interaction) to complete
    before reading back the GPU texture.  No manual ``wait_for_scene``
    or ``render`` calls are needed.

    Parameters
    ----------
    page : playwright.sync_api.Page
        The Playwright page containing the element.
    target : Locator | str | WebgpuComponent
        What to screenshot – a Playwright Locator, a CSS selector, or a
        :class:`~ngapp.components.visualization.WebgpuComponent`.
    filename : str
        Baseline image filename (e.g. ``"cylinder.png"``).
    threshold : float
        Maximum fraction of pixels allowed to differ.
    output_dir, baseline_dir : Path, optional
        Override the directories set via :func:`configure`.
    """
    out_dir = Path(output_dir) if output_dir else _output_dir
    base_dir = Path(baseline_dir) if baseline_dir else _baseline_dir
    assert (
        out_dir
    ), "output_dir not configured – call ngapp.e2e_webgpu.configure()"
    assert (
        base_dir
    ), "baseline_dir not configured – call ngapp.e2e_webgpu.configure()"

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / filename

    from ngapp.components.visualization import WebgpuComponent

    if isinstance(target, WebgpuComponent):
        _ensure_scene_ready(page, target)
        _readback_webgpu_texture(page, target, out_path, size=size)
    else:
        locator = _locator_for(page, target)
        locator.screenshot(path=str(out_path))

    baseline_path = base_dir / filename

    if UPDATE_BASELINES:
        base_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(out_path, baseline_path)
        print(f"  Updated baseline: {filename}")
        return

    if not baseline_path.exists():
        pytest.skip(
            f"No baseline {filename} – run with UPDATE_BASELINES=1 to create"
        )

    out_img = np.array(Image.open(out_path))
    ref_img = np.array(Image.open(baseline_path))

    if out_img.shape != ref_img.shape:
        pytest.fail(
            f"Shape mismatch: output {out_img.shape} vs baseline {ref_img.shape}"
        )

    diff = np.abs(out_img.astype(int) - ref_img.astype(int))
    bad_pixels = (diff.max(axis=-1) > 2).sum()
    total = out_img.shape[0] * out_img.shape[1]
    ratio = bad_pixels / total

    if ratio > threshold:
        diff_path = out_dir / f"diff_{filename}"
        diff_img = np.clip(diff * 10, 0, 255).astype(np.uint8)
        Image.fromarray(diff_img).save(str(diff_path))
        pytest.fail(
            f"{ratio:.1%} pixels differ (threshold {threshold:.1%}). "
            f"Diff saved to {diff_path}"
        )


# ---------------------------------------------------------------------------
# Pytest fixtures – activated when this module is listed in pytest_plugins
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def _playwright():
    pw = sync_playwright().start()
    yield pw
    pw.stop()


@pytest.fixture(scope="session")
def browser(_playwright):
    """Headless Chrome with WebGPU support (overrides pytest-playwright)."""
    b = _playwright.chromium.launch(
        channel="chrome",
        headless=False,
        args=["--headless=new"] + CHROMIUM_WEBGPU_ARGS,
    )
    yield b
    b.close()


@pytest.fixture
def page(browser):
    """Fresh browser page from the WebGPU-capable Chrome.

    ``requestAnimationFrame`` is patched to a no-op so the render loop
    never copies to the on-screen canvas.  Tests only need the off-screen
    ``target_texture`` which is read back via ``read_texture``.
    """
    p = browser.new_page(viewport={"width": 1280, "height": 720})
    # Kill requestAnimationFrame before anything loads so the render-to-
    # canvas loop never starts.  This keeps the GPU queue idle for readback.
    p.add_init_script(_NOOP_RAF_JS)
    yield p
    # Clean up the per-target scene tracking so a fresh page starts clean.
    _initialised_scenes.clear()
    p.close()
