import os
import subprocess
import sys


def create_app():
    py_exe = sys.executable
    try:
        import cookiecutter
    except ImportError:
        raise ImportError(
            "cookiecutter is not installed. Please install ngapp with:\n"
            f'{py_exe} -m pip install "ngapp[dev]"'
        )

    # check dirs before
    dirs = os.listdir(".")
    subprocess.run(
        [
            py_exe,
            "-m",
            "cookiecutter",
            "https://github.com/CERBSim/ngapp_template",
        ]
    )
    dirs_after = os.listdir(".")
    new_dir = list(set(dirs_after) - set(dirs))[0]
    print("Created new directory:", new_dir)
    os.chdir(new_dir)
    print("Install app")
    subprocess.run([py_exe, "-m", "pip", "install", "-e", "."])
    print("")
    print("App created successfully!")
    print("You can run it now with the command:")
    OKGREEN = "\033[92m"
    BOLD = "\033[1m"
    ENDC = "\033[0m"
    print(OKGREEN, BOLD, f"{py_exe} -m {new_dir}", ENDC)
    print("and for developer mode (auto update on changes):")
    print(OKGREEN, BOLD, f"{py_exe} -m {new_dir} --dev", ENDC)
    print(
        f"Then go into the newly created directory {new_dir} and start editing :)"
    )


if __name__ == "__main__":
    create_app()
