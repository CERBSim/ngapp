import hashlib
import shutil
import sys
import zipfile
from pathlib import Path

import platformdirs
import requests

from .._version import version


def get_version_name() -> str:
    if ".dev" in version:
        return "main"
    return version


def get_data_dir() -> Path:
    return Path(platformdirs.user_data_dir("ngapp"))


def get_cache_dir() -> Path:
    return Path(platformdirs.user_cache_dir("ngapp"))


def get_frontend_dir() -> Path:
    return get_cache_dir() / "frontend" / get_version_name()


def download_frontend(
    output_dir: Path | str | None = None, check_path=True
) -> Path:
    if output_dir is None:
        output_dir = get_frontend_dir()
    output_dir = Path(output_dir)
    version = get_version_name()

    if check_path and not "ngapp" in str(output_dir):
        raise ValueError("Output directory must contain 'ngapp' in its path.")

    file_name = f"ngapp-{version}.zip"
    data_url = f"https://ngsolve.org/ngapp/{file_name}"
    hash_url = data_url + ".md5"
    data_file = get_cache_dir() / "frontend" / file_name
    hash_file = data_file.with_suffix(".zip.md5")
    output_hash_file = output_dir / ".zip_hash.md5"

    if not hash_file.parent.exists():
        hash_file.parent.mkdir(parents=True, exist_ok=True)

    if version == "main":
        try:
            # use local version if no internet connection is available
            response = requests.get(hash_url, timeout=1000)
            response.raise_for_status()
            hash_file.write_text(response.text.strip())
        except Exception as e:
            if output_hash_file.exists():
                print(
                    "Error downloading latest frontend hash, using cached version",
                    file=sys.stderr,
                )
            else:
                raise e

    if not hash_file.exists():
        response = requests.get(hash_url)
        response.raise_for_status()
        hash_file.write_text(response.text.strip())

    if (
        output_hash_file.exists()
        and output_hash_file.read_bytes() == hash_file.read_bytes()
    ):
        return output_dir

    if (
        not data_file.exists()
        or hashlib.md5(data_file.read_bytes()).hexdigest()
        != hash_file.read_text().strip().split()[0]
    ):
        response = requests.get(data_url)
        response.raise_for_status()
        data_file.write_bytes(response.content)

    if (
        hashlib.md5(data_file.read_bytes()).hexdigest()
        != hash_file.read_text().strip().split()[0]
    ):
        hash_file.unlink(missing_ok=True)
        data_file.unlink(missing_ok=True)
        shutil.rmtree(output_dir, ignore_errors=True)
        raise ValueError("Downloaded file hash does not match expected hash.")

    if output_dir.exists():
        shutil.rmtree(output_dir, ignore_errors=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(open(str(data_file), "rb")) as zip_ref:
        zip_ref.extractall(output_dir)

    # copy the assets folder to assets/assets, because for some reason, assets are loaded from there
    shutil.copytree(output_dir / "assets", output_dir / "assets" / "assets")

    # write the hash file to the output directory at the very last step,
    # so that we can be sure everything was installed correctly if the file is there
    (output_dir / ".zip_hash.md5").write_text(hash_file.read_text())

    return output_dir
