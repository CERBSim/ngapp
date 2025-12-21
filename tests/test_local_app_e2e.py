from __future__ import annotations

from playwright.sync_api import Page

from ngapp.e2e import app_test


@app_test("tests.local_app_demo")
def test_local_app_area_computation(page: Page) -> None:
    """End-to-end test for the demo local app.

    The test fills in ``Length`` and ``Width``, clicks ``Solve``, and verifies
    that the computed area is displayed. This mirrors many typical ngapp apps
    where a few parameters drive a small computation.
    """

    # Fill in geometry parameters
    length_input = page.get_by_label("Length (m)")
    width_input = page.get_by_label("Width (m)")
    length_input.fill("5")
    width_input.fill("3")

    # Click the Solve button which should trigger the Python-side computation
    page.get_by_role("button", name="Solve").click()

    # Give the client<->Python roundtrip a short moment
    page.wait_for_timeout(500)

    # The app should show the area in the result label
    assert page.get_by_text("Area: 15.0 m^2").first.is_visible()
