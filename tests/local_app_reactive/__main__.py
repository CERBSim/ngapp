"""Serve the reactive reference app locally."""

from ngapp.cli.serve_standalone import host_local_app


def main() -> None:
    host_local_app(
        "tests.local_app_reactive",
        start_browser=False,
        watch_code=False,
        dev_frontend=False,
    )


if __name__ == "__main__":  # pragma: no cover - manual entry point
    main()
