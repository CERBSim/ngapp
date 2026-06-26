"""End-to-end WebGPU visual regression tests for ngapp.

Starts the demo app once, reads back the rendered frame via the active
render backend (JS engine or the legacy Python path), and runs all
assertions in a single test to avoid port conflicts between consecutive
in-process app launches.
"""

from __future__ import annotations

from playwright.sync_api import Page

from ngapp.e2e import app_test
from ngapp.e2e_webgpu import assert_matches_baseline, capture_canvas


@app_test("tests.local_app_webgpu_demo")
def test_webgpu_triangle(page: Page, app) -> None:
    """The demo app should render a visible triangle that matches a baseline."""
    img = capture_canvas(page, app.canvas)

    # The canvas must not be blank
    assert img.std() > 5, (
        f"Canvas appears blank (std={img.std():.1f}) "
        "– the scene probably did not render."
    )

    # Compare against the stored baseline
    assert_matches_baseline(page, app.canvas, "triangle.png")
