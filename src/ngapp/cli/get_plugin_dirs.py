"""command line interface for webapp to show the paths of all plugins
(useful for automatic reload during development)"""

import importlib.metadata
import os
import sys

import ngapp


def main():
    """Print all directories containing webapp plugins"""

    # make sure that the output is not displayed in the console
    stdout_bak = sys.stdout
    with open(os.devnull, "w", encoding="utf-8") as dummy_out:
        sys.stdout = dummy_out

        entry_points = (
            importlib.metadata.entry_points().get("webapp.plugin") or []
        )
        paths = []
        try:
            import webapp

            paths += webapp.__path__
        except ImportError:
            pass
        paths += ngapp.__path__
        for entry_point in entry_points:
            try:
                paths += __import__(entry_point.value).__path__
            except ImportError:
                pass
    print(":".join(paths), file=stdout_bak)


if __name__ == "__main__":
    main()
