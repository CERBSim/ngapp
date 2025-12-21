"""Entry point to run the test local app in standalone mode.

This mirrors the command shown in the user documentation (``python -m
<module_name> --dev``) but uses the lower-level
:func:`ngapp.cli.serve_standalone.host_local_app` directly. For the tests we do
not enable code watching or auto-opening a browser.
"""

from ngapp.cli.serve_standalone import host_local_app


def main() -> None:
    host_local_app(
        "tests.local_app_demo",
        start_browser=False,
        watch_code=False,
        dev_frontend=False,
    )


if __name__ == "__main__":  # pragma: no cover - manual entry point
    main()
