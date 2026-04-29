"""End-to-end WebGPU visual regression tests for ngapp.

Starts the demo app once, waits for the 3D scene to render, then reads
back the GPU texture and runs all assertions in a single test to avoid
port conflicts between consecutive in-process app launches.
"""

from __future__ import annotations

import time

import numpy as np
from playwright.sync_api import Page

from ngapp.e2e import app_test
from ngapp.e2e_webgpu import assert_matches_baseline, _readback_webgpu_texture


def _wait_for_scene(page: Page, app, timeout: float = 15) -> None:
    """Poll until the WebgpuComponent's scene is initialised."""
    deadline = time.time() + timeout
    while app.canvas.scene is None and time.time() < deadline:
        page.wait_for_timeout(500)
    assert (
        app.canvas.scene is not None
    ), f"WebgpuComponent.scene is still None after {timeout}s"


@app_test("tests.local_app_webgpu_demo")
def test_webgpu_triangle(page: Page, app) -> None:
    """The demo app should render a visible triangle that matches a baseline."""
    _wait_for_scene(page, app)

    from webgpu.utils import read_texture

    texture = app.canvas.scene.canvas.target_texture
    img = read_texture(texture)

    # The canvas must not be blank
    assert img.std() > 5, (
        f"Canvas appears blank (std={img.std():.1f}) "
        "– the scene probably did not render."
    )

    # Compare against the stored baseline
    assert_matches_baseline(page, app.canvas, "triangle.png")
