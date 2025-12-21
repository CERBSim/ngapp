"""Test-only local ngapp application used by end-to-end tests.

The :data:`config` object is discovered by ``ngapp.cli.serve_standalone`` and
provides the metadata required to host the app locally.
"""

from ngapp.app import AppConfig

from .app import InputChangeApp

config = AppConfig(
    python_class=InputChangeApp,
    name="Local input change demo",
    version="0.0.1",
    frontend_dependencies=[],
    frontend_pip_dependencies=[],
)
