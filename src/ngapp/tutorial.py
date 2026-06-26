"""Scaffold the airfoil tutorial as a *full* ngapp app and run it.

    python -m ngapp.tutorial [name]

This creates exactly what :mod:`ngapp.create_app` creates - a complete,
installable project (``pyproject.toml``, a GitHub Pages deploy workflow,
``src/<name>/`` package, ...) - and then injects the tutorial: the app class
gets ``metaclass=TutorialMeta`` so an in-app guide walks you through building it
up step by step.  The guide and its metaclass live in
:mod:`ngapp.tutorials.airfoil`.

The project is installed (``pip install -e``) and launched right away.  After
the last step you drop the metaclass and are left with your own standalone app
that you can ``pip install`` and run as an executable, or publish via the
included GitHub workflow.

If the target folder already exists, it is simply started again.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import subprocess
import sys
from importlib import resources
from pathlib import Path

TEMPLATE_URL = "https://github.com/CERBSim/ngapp_template"

# The class name baked into the tutorial snapshots; the generated package wires
# everything (``__init__`` / ``appconfig``) to this name via cookiecutter.
APP_CLASS = "AirfoilChallenge"
APP_TITLE = "Airfoil Tutorial"


def _run_app(module, *, start_browser=True, watch_code=True):
    """Host the installed tutorial app (the guide hot-reloads on edits)."""
    from ngapp.cli.serve_standalone import host_local_app

    host_local_app(
        f"{module}.appconfig",
        start_browser=start_browser,
        watch_code=watch_code,
    )


def _ensure_installed(module, target):
    """Install the (src-layout) project and make it importable in-process.

    ``pip install -e`` makes the app a real, runnable project (deps, the
    console-script entry point), but an editable install added by a subprocess
    is not visible to this already-running interpreter.  So we also put the
    project's ``src`` directory on ``sys.path`` directly, which is what lets us
    host the app immediately afterwards.
    """
    if importlib.util.find_spec(module) is None:
        print(f"Installing {module} ...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", str(target)],
            check=True,
        )

    src = str(target / "src")
    if src not in sys.path:
        sys.path.insert(0, src)
    importlib.invalidate_caches()


def _scaffold(module, target):
    """Generate the full app from the template and inject the tutorial."""
    try:
        import cookiecutter  # noqa: F401
    except ImportError:
        raise ImportError(
            "cookiecutter is not installed. Please install ngapp with:\n"
            f'{sys.executable} -m pip install "ngapp[dev]"'
        )
    from cookiecutter.main import cookiecutter

    # Exactly what ``ngapp.create_app`` produces, but with fixed names so the
    # generated package matches the tutorial snapshots (no interactive prompts).
    cookiecutter(
        TEMPLATE_URL,
        no_input=True,
        output_dir=str(Path.cwd()),
        extra_context={
            "app_title": APP_TITLE,
            "python_module": module,
            "python_class": APP_CLASS,
        },
    )

    pkg = target / "src" / module
    from ngapp.tutorials import airfoil

    # Inject the tutorial: the welcome snapshot is the template's hello-world
    # app plus ``metaclass=TutorialMeta`` (and the airfoil class name).
    (pkg / "app.py").write_text(airfoil.SNAPSHOT_WELCOME, encoding="utf-8")

    # The later steps need the meshing/solve helpers next to the app.
    utils_src = (resources.files("ngapp.tutorials")
                 .joinpath("airfoil_utils.py").read_text(encoding="utf-8"))
    (pkg / "utils.py").write_text(utils_src, encoding="utf-8")

    # The airfoil app pulls its solver/UI from these frontend packages.
    appconfig = pkg / "appconfig.py"
    appconfig.write_text(
        appconfig.read_text(encoding="utf-8").replace(
            "frontend_pip_dependencies=[]",
            'frontend_pip_dependencies=["ngsolve", "ngsolve_webgpu", "ngsolve_gui"]',
        ),
        encoding="utf-8",
    )

    # Make the finished app runnable as an executable after ``pip install``.
    pyproject = target / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")
    if "[project.scripts]" not in text:
        text += f'\n[project.scripts]\n{module} = "{module}.__main__:main"\n'
        pyproject.write_text(text, encoding="utf-8")

    print(f"Created {target}")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Create the airfoil tutorial as a full ngapp app, install "
                    "it, and launch it.")
    parser.add_argument("name", nargs="?", default="airfoil_tutorial",
                        help="app module/folder name (default: airfoil_tutorial)")
    parser.add_argument("--no-browser", action="store_true",
                        help="don't open a web browser")
    parser.add_argument("--no-watch", action="store_true",
                        help="don't reload the app when its code changes")
    parser.add_argument("--no-run", action="store_true",
                        help="only scaffold and install the app, don't launch it")
    args = parser.parse_args(argv)
    module = args.name

    target = Path.cwd() / module
    if target.exists():
        print(f"{target} already exists - starting it.")
    else:
        _scaffold(module, target)

    _ensure_installed(module, target)

    if args.no_run:
        print("Run it from anywhere with:")
        print(f"    python -m {module}")
        print("Then follow the guide on the right.")
        return 0

    print("Launching the app - follow the guide on the right.")
    print(f"Re-run it later with:\n    python -m {module}")
    _run_app(
        module,
        start_browser=not args.no_browser,
        watch_code=not args.no_watch,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
