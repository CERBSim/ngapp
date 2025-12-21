"""High-level helpers for end-to-end testing of ngapp apps.

This module provides a small wrapper around Playwright that makes it easy to
write browser-level tests for apps built with ngapp.

The recommended pattern is to start your app from within pytest (for example
using :class:`LocalAppRunner`) and then drive it via Playwright. ``ngapp.e2e``
does not make assumptions about routing; most ngapp apps render a single-page
layout at the base URL.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from collections.abc import Callable

import functools
import inspect
import os
import subprocess
import sys
import tempfile
import time

import pytest
from playwright.sync_api import Page
from pytest_check import check


@dataclass
class NgAppSession:
    """Thin wrapper around a Playwright :class:`Page` for ngapp apps.

    This helper focuses on a few common operations:

    * waiting for the global ``#q-loading`` spinner to disappear
    * triggering a model save and capturing the JSON payload

    It deliberately does not know anything about authentication or your
    particular app structure. You can build your own higher-level helpers on
    top of this class inside your application tests.
    """

    request: pytest.FixtureRequest
    page: Page
    base_url: str

    def wait_until_loaded(self, timeout: float | None = None) -> None:
        """Wait until the global Quasar loading overlay is hidden.

        By convention ngapp apps show a ``#q-loading`` overlay while models are
        being created or loaded. This method waits for that overlay to appear
        (if it does) and then disappear again.
        """

        locator = self.page.locator("#q-loading")
        try:
            # Use a finite default timeout so tests do not hang indefinitely
            # if the loading overlay never appears.
            eff_timeout = 10_000 if timeout is None else timeout
            locator.wait_for(state="attached", timeout=eff_timeout)
        except Exception:
            # If the loading overlay never appears, we still want to continue.
            return
        locator.wait_for(state="hidden", timeout=eff_timeout)

class LocalAppRunner:
    """Helper to start and stop a local ngapp application for tests.

    This class is intended to be used from within pytest fixtures so that
    tests can share a single running app instance across multiple test
    functions. It relies on :func:`ngapp.cli.serve_standalone.host_local_app`,
    which writes the computed URL into a file when the
    ``NGAPP_TEST_URL_FILE`` environment variable is set.

    Typical usage in a test suite::

        from ngapp.e2e import LocalAppRunner, NgAppSession


        runner = LocalAppRunner("my_app")


        @pytest.fixture(scope="session")
        def local_app_url(tmp_path_factory):
            url_file = tmp_path_factory.mktemp("ngapp_e2e") / "url.txt"
            url = runner.start(url_file=url_file)
            try:
                yield url
            finally:
                runner.stop()


        @pytest.fixture
        def ngapp_session(local_app_url, page, request):
            return NgAppSession(
                request=request,
                page=page,
                base_url=local_app_url,
            )

    Parameters
    ----------
    app_module:
        The Python module that should be executed with ``python -m`` to start
        the app, for example ``"my_app"``.
    python_executable:
        Optional path to the Python interpreter. Defaults to
        :data:`sys.executable`.
    timeout:
        Maximum time in seconds to wait for the app to write its URL to the
        URL file.
    extra_args:
        Optional list of extra command line arguments to pass after the
        module name (for example ``["--dev"]``).
    """

    def __init__(
        self,
        app_module: str,
        *,
        python_executable: str | None = None,
        timeout: float = 60.0,
        extra_args: list[str] | None = None,
    ) -> None:
        self.app_module = app_module
        self.python_executable = python_executable or sys.executable
        self.timeout = timeout
        self.extra_args = list(extra_args or [])
        self._proc: subprocess.Popen | None = None
        self.url: str | None = None

    def start(self, url_file: str | Path | None = None) -> str:
        """Start the app process and wait until its URL is available.

        The app must be implemented so that running ``python -m app_module``
        eventually calls :func:`ngapp.cli.serve_standalone.host_local_app`,
        which writes the computed URL into the file pointed to by
        ``NGAPP_TEST_URL_FILE``.
        """

        if self._proc is not None:
            raise RuntimeError("LocalAppRunner.start() called twice without stop()")

        if url_file is None:
            tmp_dir = Path(tempfile.gettempdir())
            url_file = tmp_dir / f"ngapp_e2e_url_{self.app_module.replace('.', '_')}.txt"
        else:
            url_file = Path(url_file)

        if url_file.exists():
            url_file.unlink()

        env = os.environ.copy()
        env["NGAPP_TEST_URL_FILE"] = str(url_file)

        cmd = [self.python_executable, "-u", "-m", self.app_module] + self.extra_args
        proc = subprocess.Popen(cmd, env=env, text=True)
        self._proc = proc

        start = time.time()
        while not url_file.exists():
            if proc.poll() is not None:
                raise RuntimeError(
                    f"App process exited early with code {proc.returncode}"
                )
            if time.time() - start > self.timeout:
                proc.terminate()
                raise TimeoutError("Timed out waiting for app URL file")
            time.sleep(0.1)

        url = url_file.read_text(encoding="utf-8").strip()
        if not url:
            proc.terminate()
            raise RuntimeError("App URL file was empty")

        self.url = url
        return url

    def stop(self) -> None:
        """Terminate the app process if it is still running."""

        if self._proc is None:
            return

        proc = self._proc
        self._proc = None

        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
def app_test(
    *dargs: object,
    app_module: str | None = None,
    timeout: float = 30.0,
    extra_args: list[str] | None = None,
) -> Callable[[Callable[..., object]], Callable[..., object]] | Callable[..., object]:
    """Decorator to run a local ngapp app for a single test.

    This helper wraps a pytest test function and:

    * starts the given app using :class:`LocalAppRunner`,
    * navigates the Playwright ``page`` fixture to the app URL, and
    * stops the app again when the test finishes.

    It supports two styles:

    * Explicit module name::

         from ngapp.e2e import app_test


         @app_test("my_app")
         def test_my_flow(page):
             page.get_by_label("Length (m)").fill("5")
             page.get_by_label("Width (m)").fill("3")
             page.get_by_role("button", name="Solve").click()

    * Implicit module name for single-app projects::

         from ngapp.e2e import app_test


         @app_test
         def test_my_flow(page):
             # In a project where the app itself is the top-level module
             # (e.g. ``beam_solver``) and tests live in ``beam_solver.tests``,
             # the app module is inferred as the first segment of
             # ``test_my_flow.__module__``.
             page.get_by_label("Length (m)").fill("5")

    The decorated test must accept a ``page`` argument so that pytest-
    Playwright can inject the Playwright :class:`Page` instance.
    """

    # Handle bare ``@app_test`` usage where the function is passed directly.
    if dargs and callable(dargs[0]) and app_module is None:
        func = dargs[0]
        return app_test()(func)

    # Allow ``@app_test("my_app")`` positional form.
    if dargs and isinstance(dargs[0], str) and app_module is None:
        app_module = dargs[0]

    def decorator(func: Callable[..., object]) -> Callable[..., object]:
        @functools.wraps(func)
        def wrapper(*args: object, **kwargs: object) -> object:
            sig = inspect.signature(func)
            bound = sig.bind_partial(*args, **kwargs)
            page = bound.arguments.get("page")
            if page is None:
                raise RuntimeError(
                    "@app_test-decorated tests must have a 'page' argument "
                    "so that pytest-playwright can inject the Page fixture."
                )

            module_name = app_module
            if module_name is None:
                # Infer the app module as the top-level package name of
                # the test function's module, e.g. ``beam_solver`` for
                # ``beam_solver.tests.test_something``.
                module_name = func.__module__.split(".")[0]

            runner = LocalAppRunner(
                app_module=module_name,
                timeout=timeout,
                extra_args=extra_args,
            )
            url = runner.start()
            try:
                page.goto(url)  # type: ignore[call-arg]
                return func(*args, **kwargs)
            finally:
                runner.stop()

        return wrapper

    return decorator

