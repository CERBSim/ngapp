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
    from colorama import Fore, Style

    print(Fore.GREEN, f"{py_exe} -m {new_dir}", Style.RESET_ALL)
    print("and for developer mode (auto update on changes):")
    print(Fore.GREEN, f"{py_exe} -m {new_dir} --dev", Style.RESET_ALL)
    print(
        f"Then go into the newly created directory {new_dir} and start editing :)"
    )


if __name__ == "__main__":
    create_app()
