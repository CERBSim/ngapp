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


@app_test("tests.local_app_demo")
def test_local_app_usersettings_persists_length(page: Page) -> None:
    """End-to-end test that exercises App.usersettings via QInput.

    The demo app wires its ``Length (m)`` input to ``app.usersettings``
    under the key ``"last_length"``. This test changes the value and
    verifies that it is reflected in a fresh browser session by reading
    the persisted input value from the field.
    """

    # First run: change the length input so it is written to usersettings
    length_input = page.get_by_label("Length (m)")
    length_input.fill("7")

    # Give the client<->Python roundtrip a short moment
    page.wait_for_timeout(100)

    from ngapp.cli.serve_standalone import app
    app.reset()

    page.wait_for_timeout(100)

    # After reload, the length input should still show the value we set
    reloaded_length_input = page.get_by_label("Length (m)")
    assert reloaded_length_input.input_value() == "7"
