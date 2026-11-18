"""Reference app in the reactive style, served locally by
``python -m tests.local_app_reactive``."""

from ngapp.app import AppConfig

from .app import ReactiveSineApp

config = AppConfig(
    python_class=ReactiveSineApp,
    name="Reactive sine",
    version="0.0.1",
    frontend_dependencies=[],
    frontend_pip_dependencies=[],
)
