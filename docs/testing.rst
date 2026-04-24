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

WebGPU visual regression tests
------------------------------

If your app uses :class:`~ngapp.components.visualization.WebgpuComponent`,
you can write tests that compare rendered 3D scenes against stored baseline
images. The framework reads back the GPU texture directly, so it works in
headless Chrome where normal Playwright screenshots of WebGPU canvases are
blank.

Setup
~~~~~

Install the extra dependencies::

   pip install "ngapp[e2e]"
   playwright install

Create a ``tests/conftest.py`` that registers the WebGPU plugin and
configures directories for output images and baselines::

   from pathlib import Path
   import ngapp.e2e_webgpu as e2e_webgpu

   pytest_plugins = ["ngapp.e2e_webgpu"]

   TESTS_DIR = Path(__file__).parent
   e2e_webgpu.configure(
       output_dir=TESTS_DIR / "output",
       baseline_dir=TESTS_DIR / "baselines",
   )

``output/`` receives images from the current run. ``baselines/`` stores the
reference images you commit to version control.

Writing a test
~~~~~~~~~~~~~~

Use :func:`~ngapp.e2e.app_test` with an ``app`` parameter to get access to
the live ``App`` instance. Call
:func:`~ngapp.e2e_webgpu.assert_matches_baseline` with the
``WebgpuComponent`` you want to check::

   import time
   from playwright.sync_api import Page
   from ngapp.e2e import app_test
   from ngapp.e2e_webgpu import assert_matches_baseline


   @app_test("my_3d_app")
   def test_scene_renders(page: Page, app):
       # The mounted callback that calls draw() runs asynchronously,
       # so poll until the scene is ready.
       deadline = time.time() + 15
       while app.my_canvas.scene is None and time.time() < deadline:
           page.wait_for_timeout(500)
       assert app.my_canvas.scene is not None, "scene never initialised"

       assert_matches_baseline(page, app.my_canvas, "my_scene.png")

``assert_matches_baseline`` accepts these keyword arguments:

- **threshold** (float, default ``0.01``): maximum fraction of pixels
  allowed to differ before the test fails.
- **output_dir** / **baseline_dir**: override the directories set in
  ``conftest.py`` for a single call.

When the *target* is a ``WebgpuComponent`` the GPU texture is read back
automatically. For any other target (a Playwright ``Locator`` or a CSS
selector string) it falls back to a regular Playwright screenshot.

Generating baselines
~~~~~~~~~~~~~~~~~~~~

On the first run there are no baselines yet. Set the ``UPDATE_BASELINES``
environment variable to create them::

   UPDATE_BASELINES=1 pytest tests/ -vv -s

This writes the current output images into ``tests/baselines/``. Commit
these files to version control. Subsequent runs without the variable will
compare against them and fail if any pixels differ beyond the threshold.

Running in Docker (CI)
~~~~~~~~~~~~~~~~~~~~~~

WebGPU requires a GPU driver. In CI or on machines without a physical GPU,
run the tests inside Docker using ``ghcr.io/cerbsim/ngapp-base`` which
ships Chrome, Mesa Vulkan drivers, and the lavapipe software renderer with
ngapp pre-installed.

A minimal ``Dockerfile`` for your app's tests::

   FROM ghcr.io/cerbsim/ngapp-base:latest
   WORKDIR /app
   COPY . .
   ENV SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0.dev0
   RUN pip install --no-cache-dir --break-system-packages .
   CMD ["pytest", "tests/", "-vv", "-s"]

Build and run::

   docker build -t my-tests .

   # First run: generate baselines
   docker run --rm \
       -v "$(pwd)/tests/baselines:/app/tests/baselines" \
       -e UPDATE_BASELINES=1 my-tests

   # Subsequent runs: compare against baselines
   docker run --rm \
       -v "$(pwd)/tests/baselines:/app/tests/baselines" \
       my-tests

The ngapp repository ships a helper script ``run_tests_in_docker.sh`` that
wraps these steps and accepts ``--update-baselines``.

Complete example
~~~~~~~~~~~~~~~~

Given an app that renders a triangle::

   # my_app/app.py
   import numpy as np
   from ngapp.app import App
   from ngapp.components import Col
   from ngapp.components.visualization import WebgpuComponent


   class MyApp(App):
       def __init__(self):
           super().__init__()
           self.canvas = WebgpuComponent(width="400px", height="400px")
           self.canvas.on_mounted(self._draw)
           self.component = Col(self.canvas)

       def _draw(self):
           from webgpu.triangles import TriangulationRenderer

           points = np.array(
               [[-1, -1, 0], [1, -1, 0], [0, 1, 0]], dtype=np.float32
           )
           renderer = TriangulationRenderer(points, color=(0.2, 0.6, 1.0, 1.0))
           self.canvas.draw([renderer])

The test file::

   # tests/test_visual.py
   import time
   from playwright.sync_api import Page
   from ngapp.e2e import app_test
   from ngapp.e2e_webgpu import assert_matches_baseline


   @app_test("my_app")
   def test_triangle(page: Page, app):
       deadline = time.time() + 15
       while app.canvas.scene is None and time.time() < deadline:
           page.wait_for_timeout(500)
       assert app.canvas.scene is not None

       assert_matches_baseline(page, app.canvas, "triangle.png")

And ``tests/conftest.py``::

   from pathlib import Path
   import ngapp.e2e_webgpu as e2e_webgpu

   pytest_plugins = ["ngapp.e2e_webgpu"]

   TESTS_DIR = Path(__file__).parent
   e2e_webgpu.configure(
       output_dir=TESTS_DIR / "output",
       baseline_dir=TESTS_DIR / "baselines",
   )
