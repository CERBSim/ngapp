"""Compute layer packages: pure python dependencies are zipped, compiled ones built from
source and kept on the backend while their build key is unchanged"""

import io
import shutil
import sys
import zipfile
from pathlib import Path

import pytest

from ngapp import compute_packages as cp
from ngapp.app import AppConfig, PythonPackage
from ngapp.utils import ComputeEnvironment


def _wheel(name="pkg-1.0-py3-none-any.whl", files=None, requires=()):
    dist = "-".join(name.split("-")[:2])
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        for path, data in (files or {"pkg/__init__.py": ""}).items():
            zf.writestr(path, data)
        meta = "Metadata-Version: 2.1\nName: pkg\nVersion: 1.0\n"
        meta += "".join(f"Requires-Dist: {r}\n" for r in requires)
        zf.writestr(f"{dist}.dist-info/METADATA", meta)
    return buffer.getvalue()


def _package(root: Path, name: str, files=None):
    for path, data in ({"__init__.py": ""} | (files or {})).items():
        target = root / name / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(data)
    return root / name


def _config(envs=None, **kwargs):
    if envs is None:
        envs = [ComputeEnvironment(env_type="docker", python="3.14")]
    return AppConfig(
        name="test", version="1", python_class="myapp.App", compute_environments=envs, **kwargs
    )


@pytest.fixture
def layer(tmp_path, monkeypatch):
    """Importable packages in tmp_path/site, no app wheel build"""
    site = tmp_path / "site"
    site.mkdir()
    monkeypatch.syspath_prepend(str(site))
    monkeypatch.setattr(cp, "_app_source_dir", lambda name: tmp_path)
    monkeypatch.setattr(
        cp, "_app_wheel", lambda src: PythonPackage(file_name="myapp-1-py3-none-any.whl", package=b"app")
    )
    yield site
    for name in list(sys.modules):
        if name.startswith("cpkg_"):
            del sys.modules[name]


class FakeVenv:
    """Builds a wheel named after the source without running any build"""

    built: list[str] = []

    def __init__(self, target, root, log):
        self.target = target

    def build(self, src, out):
        name = src.name.removeprefix("src-")
        FakeVenv.built.append(name)
        tag = "cp" + self.target.python.replace(".", "")
        wheel = out / f"{name}-1.0-{tag}-{tag}-linux_x86_64.whl"
        wheel.write_bytes(_wheel(wheel.name, {f"{name}/__init__.py": (src / "v").read_text()}))
        return wheel

    def install(self, *args, **kwargs):
        pass


def test_parse_dependency():
    assert cp.parse_dependency("trafomodel") == ("trafomodel", None)
    assert cp.parse_dependency("transfem @ git+ssh://git@host:692/a/b.git@09e11f9") == (
        "transfem",
        "git+ssh://git@host:692/a/b.git@09e11f9",
    )
    with pytest.raises(ValueError):
        cp.parse_dependency("bad name")
    with pytest.raises(ValueError):
        cp.parse_dependency("pkg @ ")


def test_git_source():
    src = cp._parse_source("t", "git+ssh://git@host:692/a/t.git@feature/x#subdirectory=py", None)
    assert (src.location, src.ref, src.subdirectory) == ("ssh://git@host:692/a/t.git", "feature/x", "py")
    src = cp._parse_source("t", "git+https://host/a/t.git", None)
    assert (src.location, src.ref) == ("https://host/a/t.git", "")


def test_wheel_fits_python():
    fits = cp.wheel_fits_python
    assert fits("a-1-py3-none-any.whl", "3.14")
    assert fits("a-1-cp314-cp314-manylinux_2_28_x86_64.whl", "3.14")
    assert not fits("a-1-cp313-cp313-linux_x86_64.whl", "3.14")
    assert fits("a-1-cp310-abi3-linux_x86_64.whl", "3.14")
    assert not fits("a-1-cp314-cp314-win_amd64.whl", "3.14")
    assert not fits("a-1-cp314-cp314-macosx_11_0_arm64.whl", "3.14")


def test_check_layer_wheel():
    assert cp.check_layer_wheel("pkg-1.0-py3-none-any.whl", _wheel()) == []
    assert cp.check_layer_wheel("../pkg-1.0-py3-none-any.whl", _wheel())
    assert cp.check_layer_wheel("pkg.whl", _wheel())
    # like the transfem wheel of 2026-04: package under .data/data/lib/python3.13/site-packages
    name = "transfem-0.0.1-cp313-cp313-linux_x86_64.whl"
    data = _wheel(name, {"transfem-0.0.1.data/data/lib/python3.13/site-packages/transfem/__init__.py": ""})
    problems = cp.check_layer_wheel(name, data, "3.14")
    assert len(problems) == 2
    assert "does not fit python 3.14" in problems[0] and ".data/data" in problems[1]


def test_dependencies_are_zipped(layer):
    _package(layer, "cpkg_front", {"backend/solver.py": "x = 1"})
    _package(layer, "cpkg_pure", {"sub/mod.py": ""})
    config = _config(frontend_dependencies=["cpkg_front"], compute_dependencies=["cpkg_pure"])
    packages, digest = cp.build_compute_packages(config, {})
    assert [p.file_name for p in packages] == [
        "myapp-1-py3-none-any.whl",
        "cpkg_front.zip",
        "cpkg_pure.zip",
    ]
    with zipfile.ZipFile(io.BytesIO(packages[1].package)) as zf:
        assert "cpkg_front/backend/solver.py" in zf.namelist()  # compute side keeps backend modules
    assert cp.build_compute_packages(config, {})[1] == digest


def test_compiled_dependency_needs_source(layer):
    _package(layer, "cpkg_native", {"_core.cpython-314-x86_64-linux-gnu.so": ""})
    with pytest.raises(RuntimeError, match="compiled files.*cpkg_native @"):
        cp.build_compute_packages(_config(compute_dependencies=["cpkg_native"]), {})
    with pytest.raises(RuntimeError, match="is not installed"):
        cp.build_compute_packages(_config(compute_dependencies=["cpkg_missing"]), {})


def test_build_needs_python_of_env(layer, tmp_path):
    src = _package(tmp_path, "srca")
    config = _config(envs=[ComputeEnvironment(env_type="docker")], compute_dependencies=[f"srca @ {src}"])
    with pytest.raises(RuntimeError, match="set python"):
        cp.build_compute_packages(config, {})


def test_built_packages_kept_until_source_changes(layer, tmp_path, monkeypatch):
    monkeypatch.setattr(cp, "_BuildVenv", FakeVenv)
    a, b = _package(tmp_path, "srca", {"v": "a1"}), _package(tmp_path, "srcb", {"v": "b1"})
    config = _config(compute_dependencies=[f"srca @ {a}", f"srcb @ {b}"])

    def deploy(existing):
        FakeVenv.built = []
        packages, digest = cp.build_compute_packages(config, existing)
        stored = {
            p.file_name: {"hash": cp.calc_hash(p.package) if p.package else existing[p.file_name]["hash"], "build_key": p.build_key}
            for p in packages
        }
        return packages, digest, stored

    packages, digest, stored = deploy({})
    assert FakeVenv.built == ["srca", "srcb"]
    assert all(p.build_key for p in packages[1:])

    packages, digest2, stored = deploy(stored)
    assert FakeVenv.built == [] and digest2 == digest
    assert [p.package for p in packages[1:]] == [None, None]

    (b / "v").write_text("b2")  # srca is rebuilt too: srcb's build needs it in the venv
    packages, digest3, stored = deploy(stored)
    assert FakeVenv.built == ["srca", "srcb"] and digest3 != digest

    (a / "v").write_text("a2")  # a new srca invalidates the key of srcb as well
    keys = [p.build_key for p in packages]
    packages, _, stored = deploy(stored)
    assert FakeVenv.built == ["srca", "srcb"]
    assert all(k1 != k2 for k1, k2 in zip(keys[1:], [p.build_key for p in packages[1:]]))


def test_python_or_pins_change_the_key(layer, tmp_path, monkeypatch):
    monkeypatch.setattr(cp, "_BuildVenv", FakeVenv)
    a = _package(tmp_path, "srca", {"v": "a1"})

    def key(**env):
        env = ComputeEnvironment(env_type="docker", **({"python": "3.14"} | env))
        packages, _ = cp.build_compute_packages(_config(envs=[env], compute_dependencies=[f"srca @ {a}"]), {})
        return packages[-1].build_key

    assert key() == key()
    assert key() != key(python="3.13")
    assert key() != key(pip_dependencies=["ngsolve==6.2.2608"])


def test_provided_wheels(layer, tmp_path):
    wheels = tmp_path / "wheels"
    wheels.mkdir()
    name = "pkg-1.0-cp314-cp314-linux_x86_64.whl"
    (wheels / name).write_bytes(_wheel(name, requires=["ngsolve==6.2.2501"]))
    env = ComputeEnvironment(env_type="docker", python="3.14", pip_dependencies=["ngsolve==6.2.2608"])
    config = _config(envs=[env], compute_dependencies=["pkg @ /nonexistent"])
    with pytest.raises(RuntimeError, match="ngsolve==6.2.2608"):
        cp.build_compute_packages(config, {}, wheels)

    (wheels / name).write_bytes(_wheel(name, requires=["ngsolve==6.2.2608", "scipy"]))
    logs = []
    packages, _ = cp.build_compute_packages(config, {}, wheels, log=logs.append)
    assert [p.file_name for p in packages] == ["myapp-1-py3-none-any.whl", name]
    assert any("scipy" in line for line in logs)

    old = tmp_path / "dependencies"  # the former implicit wheel directory is only pointed out
    shutil.move(wheels, old)
    logs = []
    packages, _ = cp.build_compute_packages(_config(), {}, log=logs.append)
    assert len(packages) == 1 and "--wheels" in logs[0]


def test_build_env_drops_local_paths(monkeypatch):
    # a local ngsolve on PYTHONPATH shadowed the pip ngsolve of the build venv (segfault in cmake)
    monkeypatch.setenv("PYTHONPATH", "/opt/netgen/lib/python3.14/site-packages")
    monkeypatch.setenv("NETGENDIR", "/opt/netgen/bin")
    monkeypatch.setenv("CXX", "clang++")  # ngsolve's cmake config passes gcc flags
    monkeypatch.setenv("CMAKE_BUILD_PARALLEL_LEVEL", "6")
    env = cp._build_env()
    assert not {"PYTHONPATH", "NETGENDIR", "CXX"} & env.keys()
    assert env["CMAKE_BUILD_PARALLEL_LEVEL"] == "6"


@pytest.mark.skipif(shutil.which("uv") is None, reason="needs uv")
def test_build_in_venv(layer, tmp_path):
    """Real build of a local source in a fresh venv with the python of this process"""
    src = tmp_path / "srcpkg"
    _package(src, "cpkg_built", {"core.py": "VALUE = 42"})
    (src / "pyproject.toml").write_text(
        '[build-system]\nrequires = ["setuptools>=64"]\nbuild-backend = "setuptools.build_meta"\n'
        '[project]\nname = "cpkg-built"\nversion = "0.3"\n'
    )
    python = f"{sys.version_info[0]}.{sys.version_info[1]}"
    config = _config(
        envs=[ComputeEnvironment(env_type="docker", python=python)],
        compute_dependencies=[f"cpkg-built @ {src}"],
    )
    packages, _ = cp.build_compute_packages(config, {})
    wheel = packages[-1]
    assert wheel.file_name == "cpkg_built-0.3-py3-none-any.whl" and wheel.build_key
    with zipfile.ZipFile(io.BytesIO(wheel.package)) as zf:
        assert zf.read("cpkg_built/core.py") == b"VALUE = 42"
    assert not (src / "build").exists()  # built in a copy
