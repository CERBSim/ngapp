Testing ngapp applications
==========================

ngapp supports two complementary testing patterns:

* **Calculation tests** that work purely on Python state and saved
  ``.sav`` files (no browser).
* **End-to-end (E2E) tests** that drive the full UI in a real browser.

Calculation tests (state/snapshot based)
----------------------------------------

Calculation tests focus on the *numerical* or *algorithmic* part of your
app, for example a ``solve`` routine in a FEM solver. They start from a
saved app state, run some Python-side logic, save the app again and compare
the result to a reference state.

You can create input and reference states directly from the running app
using :meth:`ngapp.app.App.save_local`. The files produced (``.sav``) are
pickled dictionaries and use the same format as the snapshots handled by
:mod:`ngapp.test_utils`.

Snapshot files are stored under ``tests/cases/<folder_path>``. A typical
calculation test might look like this::

   from ngapp.test_utils import load_case, snapshot, standalone_app_test
   from my_app.app import MySolverApp


   @standalone_app_test
   def test_my_solver_case():
      # 1. Load an input state saved via ``App.save_local`` into the app
      app = MySolverApp()
      load_case(
         app,
         folder_path="my_app/cantilever_case",
         filename="input.sav",   # copied from a user-saved .sav file
         load_storage=True,
      )

      # 2. Run the calculation you want to test
      app.solve()

      # 3. Compare the new state to an expected reference .sav
      snapshot(
         app,
         folder_path="my_app/cantilever_case",
         filename="expected.sav",  # another .sav created via save_local
         check_data=True,
         check_storage=True,
      )

In this repository, the file [tests/test_snapshot.py](tests/test_snapshot.py)
shows the same pattern applied to the small demo app in
[tests/local_app_demo](tests/local_app_demo).

Under the hood, :mod:`ngapp.test_utils` uses ``deepdiff`` to compare
component data and JSON files to compare local storage. See that module for
more advanced options.

End-to-end (browser) tests with Playwright
------------------------------------------

E2E tests focus on the *user experience*: they start the full app, interact
with the UI like a user (typing into inputs, clicking buttons, etc.), and
assert on what is rendered. ngapp provides a small helper around
`pytest <https://docs.pytest.org/>`_ and
`Playwright <https://playwright.dev/python/docs/intro>`_ for this.

Install the optional dependencies::

   pip install "ngapp[e2e]"
   playwright install

The easiest way to test a local app is to use the
:func:`ngapp.e2e.app_test` decorator. It starts your app with the same
mechanism as :func:`ngapp.cli.serve_standalone.host_local_app`, navigates the
Playwright ``page`` to the app URL, and then runs your test function.

Single-app projects (implicit app module)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If your project is structured so that the app itself is the top-level
package (for example ``beam_solver``) and tests live inside that package
(``beam_solver.tests``), you can let :func:`ngapp.e2e.app_test` infer the app
module::

   # file: beam_solver/tests/test_e2e.py

   from ngapp.e2e import app_test


   @app_test
   def test_basic_flow(page):
      """Drive the app through the browser using Playwright locators."""

      page.get_by_label("Length (m)").fill("5")
      page.get_by_label("Width (m)").fill("3")
      page.get_by_role("button", name="Solve").click()

      # Check that the result appears in the UI
      assert page.get_by_text("Area:").first.is_visible()


   @app_test
   def test_invalid_input(page):
      page.get_by_label("Length (m)").fill("not-a-number")
      page.get_by_role("button", name="Solve").click()
      assert page.get_by_text("invalid input").first.is_visible()

Here the app module is inferred as ``"beam_solver"`` from the test module
name (``beam_solver.tests.test_e2e``). If you have multiple apps in one
package or place tests outside the app package, you can instead pass the
module name explicitly, for example ``@app_test("my_other_app")``.

In all cases the decorated test must accept a ``page`` argument so that the
Playwright :class:`~playwright.sync_api.Page` fixture can be injected by
pytest.

Under the hood :func:`ngapp.e2e.app_test` uses :class:`ngapp.e2e.LocalAppRunner`,
which you can also use directly if you want finer control over when the app
is started and stopped (for example, sharing one app instance across many
tests via a session-scoped fixture).

Run the tests with::

   pytest tests -s

By default Playwright will open a headless browser. To debug a failing test,
you can use Playwright's own command line flags or insert ``page.pause()``
statements in your tests.
