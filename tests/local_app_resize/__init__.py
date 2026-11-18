from ngapp.app import AppConfig

from .app import ResizeApp

config = AppConfig(
    python_class=ResizeApp,
    name="Resize",
    version="0.0.1",
    frontend_dependencies=[],
    frontend_pip_dependencies=[],
)
