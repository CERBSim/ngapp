"""Test-only ngapp app with a WebgpuComponent for visual regression tests."""

from ngapp.app import AppConfig

from .app import WebgpuDemoApp

config = AppConfig(
    python_class=WebgpuDemoApp,
    name="WebGPU demo",
    version="0.0.1",
    frontend_dependencies=[],
    frontend_pip_dependencies=[],
)