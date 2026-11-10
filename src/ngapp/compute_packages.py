"""Packages of the compute layer of an app.

The runner extracts the layer as is (no pip): the app wheel, zips of pure python
dependencies and wheels that put their package at the archive root. Dependencies
with compiled code are built from source in a venv with the python version and the
pip_dependencies of the compute environments; the backend keeps a built wheel
together with its build key, so it is only rebuilt when the key changes.
"""

import email.parser
import hashlib
import importlib.metadata
import importlib.util
import io
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import zipfile
from dataclasses import dataclass
from pathlib import Path

from .utils import calc_hash, zip_modules

_KEY_VERSION = 1
_NATIVE = re.compile(r"\.(so|pyd|dll|dylib)(\.[0-9]+)*$")
_GIT_SHA = re.compile(r"[0-9a-f]{7,40}")
_FILE_NAME = re.compile(r"[A-Za-z0-9_.+-]+\.(whl|zip)")
_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
_COPY_SKIP = {"build", "dist", ".venv", "__pycache__"}
# variables of the deploy machine that leak into builds (PYTHONPATH with a local
# ngsolve next to the pip ngsolve of the venv, library and cmake search paths,
# compiler choice: the pip ngsolve is built with gcc and passes gcc flags)
_LEAKING_ENV = {
    "LD_LIBRARY_PATH", "LD_PRELOAD", "CMAKE_PREFIX_PATH", "NETGENDIR", "NETGEN_DIR",
    "VIRTUAL_ENV", "CONDA_PREFIX", "CC", "CXX", "CFLAGS", "CXXFLAGS", "CPPFLAGS", "LDFLAGS",
}

_REQUIRES_SCRIPT = """
import build, json, sys
builder = build.ProjectBuilder(sys.argv[1])
requires = set(builder.build_system_requires)
if sys.argv[2] == "1":
    requires |= set(builder.get_requires_for_build("wheel"))
print(json.dumps(sorted(requires)))
"""


def normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "_", name).lower()


def parse_dependency(spec: str) -> tuple[str, str | None]:
    """'name' or 'name @ source' -> (name, source or None)"""
    name, sep, source = spec.partition("@")
    name = name.strip()
    if not _NAME.fullmatch(name) or (sep and not source.strip()):
        raise ValueError(f"invalid compute dependency '{spec}'")
    return name, source.strip() if sep else None


def wheel_tags(file_name: str):
    """(name, version, python tags, abi tags, platform tags) of a wheel file name"""
    parts = file_name.removesuffix(".whl").split("-")
    if not file_name.endswith(".whl") or len(parts) not in (5, 6):
        raise ValueError(f"invalid wheel file name {file_name}")
    return (
        parts[0],
        parts[1],
        parts[-3].split("."),
        parts[-2].split("."),
        parts[-1].split("."),
    )


def wheel_fits_python(file_name: str, python: str) -> bool:
    """Can CPython ``python`` ("3.14") on linux import the wheel"""
    _, _, pythons, abis, platforms = wheel_tags(file_name)
    if not all(p == "any" or "linux" in p for p in platforms):
        return False
    major, minor = python.split(".")[:2]
    cp = f"cp{major}{minor}"
    for tag in pythons:
        if tag in ("py3", f"py{major}{minor}", cp) and ("none" in abis or cp in abis):
            return True
        m = re.fullmatch(r"cp(\d)(\d+)", tag)
        if m and "abi3" in abis and m[1] == major and int(m[2]) <= int(minor):
            return True
    return False


def check_layer_wheel(file_name: str, data: bytes, python: str = "") -> list[str]:
    """Problems that keep a wheel from working when the runner extracts it as is"""
    if not _FILE_NAME.fullmatch(file_name):
        return [f"invalid package file name {file_name}"]
    try:
        wheel_tags(file_name)
    except ValueError as e:
        return [str(e)]
    problems = []
    if python and not wheel_fits_python(file_name, python):
        problems.append(f"{file_name} does not fit python {python} on linux")
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            names = zf.namelist()
    except zipfile.BadZipFile:
        return problems + [f"{file_name} is not a zip archive"]
    schemes = sorted(
        {
            m[1]
            for n in names
            if (m := re.match(r"[^/]+\.data/(purelib|platlib|data)/", n))
        }
    )
    if schemes:
        problems.append(
            f"{file_name} installs files through .data/{', .data/'.join(schemes)}, "
            "the runner only extracts the archive root (install the package "
            "directly into site-packages)"
        )
    return problems


def _wheel_requires(data: bytes) -> list[str]:
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for n in zf.namelist():
            if re.fullmatch(r"[^/]+\.dist-info/METADATA", n):
                meta = email.parser.Parser().parsestr(zf.read(n).decode())
                return meta.get_all("Requires-Dist") or []
    return []


def _check_requirements(requires: dict, envs, available: set, log):
    """Compare Requires-Dist of layer packages with the pip_dependencies of the
    environments: missing ones are reported, conflicting pins are an error"""
    from packaging.requirements import InvalidRequirement, Requirement

    def parse(text):
        try:
            return Requirement(text)
        except InvalidRequirement:
            return None

    names, pins = set(available) | {"ngapp"}, {}
    for env in envs:
        for req in filter(None, map(parse, env.pip_dependencies)):
            names.add(normalize(req.name))
            for spec in req.specifier:
                if spec.operator == "==" and "*" not in spec.version:
                    pins[normalize(req.name)] = spec.version
    errors = []
    for package, texts in requires.items():
        for req in filter(None, map(parse, texts)):
            if req.marker and not req.marker.evaluate({"extra": ""}):
                continue
            name = normalize(req.name)
            if name not in names:
                log(
                    f"warning: {package} requires '{req}', which is not in the "
                    "pip_dependencies of the compute environments"
                )
            elif name in pins and not req.specifier.contains(
                pins[name], prereleases=True
            ):
                errors.append(
                    f"{package} requires '{req}', the compute environments "
                    f"install {req.name}=={pins[name]}"
                )
    if errors:
        raise RuntimeError("\n".join(errors))


def _call(cmd, cwd=None, env=None):
    cmd = [str(c) for c in cmd]
    try:
        subprocess.run(cmd, cwd=cwd, env=env, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"command failed with exit status {e.returncode}: {shlex.join(cmd)}"
        ) from None


def _output(cmd, cwd=None, env=None) -> bytes:
    return subprocess.run(
        [str(c) for c in cmd], cwd=cwd, env=env, check=True, capture_output=True
    ).stdout


def _build_env() -> dict:
    return {
        k: v
        for k, v in os.environ.items()
        if not k.startswith("PYTHON") and k not in _LEAKING_ENV
    }


def _package_dir(name: str) -> Path | None:
    """Directory of an importable package, None if it is not installed"""
    try:
        spec = importlib.util.find_spec(name.replace("-", "_"))
    except (ImportError, ValueError):
        return None
    if spec is None:
        return None
    if not spec.submodule_search_locations:
        raise RuntimeError(f"{name} is a single module, only packages are supported")
    return Path(list(spec.submodule_search_locations)[0])


def _native_files(path: Path) -> list[str]:
    return sorted(
        str(Path(root, f).relative_to(path))
        for root, _, files in os.walk(path)
        for f in files
        if _NATIVE.search(f)
    )


def _distribution(name: str):
    try:
        return importlib.metadata.distribution(name)
    except importlib.metadata.PackageNotFoundError:
        names = importlib.metadata.packages_distributions().get(name.replace("-", "_"))
        return importlib.metadata.distribution(names[0]) if names else None


def _editable_source(name: str) -> str | None:
    """Source directory of a package installed with pip install -e"""
    dist = _distribution(name)
    text = dist.read_text("direct_url.json") if dist else None
    if not text:
        return None
    info = json.loads(text)
    if "dir_info" in info and info.get("url", "").startswith("file://"):
        return info["url"]
    return None


def _distribution_requires(name: str) -> list[str]:
    dist = _distribution(name)
    return (dist.requires or []) if dist else []


@dataclass
class _Source:
    name: str
    kind: str  # "git" or "path"
    location: str  # git url or directory
    ref: str = ""
    subdirectory: str = ""
    commit: str = ""  # resolved git commit

    def describe(self) -> str:
        if self.kind == "git":
            return f"{self.location}@{self.commit or self.ref or 'HEAD'}"
        return self.location


def _parse_source(name: str, source: str, base_dir: Path) -> _Source:
    if source.startswith("git+"):
        parts = urllib.parse.urlsplit(source[4:])
        path, ref = parts.path, ""
        if "@" in path:
            path, ref = path.split("@", 1)
        subdirectory = urllib.parse.parse_qs(parts.fragment).get("subdirectory", [""])[0]
        url = urllib.parse.urlunsplit((parts.scheme, parts.netloc, path, parts.query, ""))
        return _Source(name, "git", url, ref, subdirectory)
    if source.startswith("file://"):
        source = urllib.parse.unquote(urllib.parse.urlsplit(source).path)
    path = Path(base_dir, os.path.expanduser(source))
    if not path.is_dir():
        raise RuntimeError(f"source of {name} not found: {path}")
    return _Source(name, "path", str(path.resolve()))


def _git_commit(url: str, ref: str) -> str:
    if ref and _GIT_SHA.fullmatch(ref):
        return ref
    lines = _output(["git", "ls-remote", url, ref or "HEAD"]).decode().splitlines()
    refs = {r: sha for sha, r in (line.split("\t", 1) for line in lines if "\t" in line)}
    for candidate in (f"refs/tags/{ref}^{{}}", f"refs/tags/{ref}", f"refs/heads/{ref}"):
        if ref and candidate in refs:
            return refs[candidate]
    if not lines:
        raise RuntimeError(f"'{ref or 'HEAD'}' not found in {url}")
    return lines[0].split("\t")[0]


def _tree_hash(path: Path) -> str:
    digest = hashlib.sha256()
    for root, dirs, files in os.walk(path):
        dirs[:] = sorted(
            d for d in dirs if d not in _COPY_SKIP | {".git"} and not d.endswith(".egg-info")
        )
        for f in sorted(files):
            p = Path(root, f)
            digest.update(str(p.relative_to(path)).encode() + b"\0")
            digest.update(p.read_bytes())
    return digest.hexdigest()


def _local_identity(path: str) -> str:
    """Git commit + hash of uncommitted changes, hash of all files outside of git"""
    try:
        head = _output(["git", "rev-parse", "HEAD"], cwd=path).decode().strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "tree:" + _tree_hash(Path(path))
    digest = hashlib.sha256(_output(["git", "diff", "HEAD", "--binary", "--", "."], cwd=path))
    untracked = _output(
        ["git", "ls-files", "--others", "--exclude-standard", "-z", "--", "."], cwd=path
    )
    for f in filter(None, untracked.decode().split("\0")):
        digest.update(f.encode() + b"\0")
        digest.update(Path(path, f).read_bytes())
    return f"git:{head}:{digest.hexdigest()}"


@dataclass
class _Target:
    python: str
    pip_dependencies: list[str]


def _union(envs) -> list[str]:
    return list(dict.fromkeys(d for env in envs for d in env.pip_dependencies))


def _image_envs(config):
    return [e for e in config.compute_environments if e.env_type != "local"]


def _image_python(config) -> str:
    """Python version shared by all image environments, "" if unknown"""
    pythons = {e.python for e in _image_envs(config)}
    return pythons.pop() if len(pythons) == 1 else ""


def _build_target(config) -> _Target:
    envs = _image_envs(config)
    if not envs:
        python = f"{sys.version_info[0]}.{sys.version_info[1]}"
        return _Target(python, _union(config.compute_environments))
    missing = [e.name for e in envs if not e.python]
    if missing:
        raise RuntimeError(
            f"compute environment(s) {', '.join(missing)}: set python (e.g. "
            "python=\"3.14\") to build compute_dependencies from source"
        )
    pythons = sorted({e.python for e in envs})
    if len(pythons) > 1:
        raise RuntimeError(
            "compute_dependencies built from source need one python version in "
            f"all compute environments, found {', '.join(pythons)}"
        )
    return _Target(pythons[0], _union(envs))


def _build_key(source: _Source, target: _Target, previous: str) -> str:
    if source.kind == "git":
        source.commit = _git_commit(source.location, source.ref)
        identity = f"git:{source.location}@{source.commit}#{source.subdirectory}"
    else:
        identity = _local_identity(source.location)
    data = [
        _KEY_VERSION,
        normalize(source.name),
        identity,
        target.python,
        sorted(target.pip_dependencies),
        previous,  # builds may link against the dependencies built before them
    ]
    return hashlib.sha256(json.dumps(data).encode()).hexdigest()[:40]


def _checkout(source: _Source, root: Path) -> Path:
    target = root / f"src-{normalize(source.name)}"
    if source.kind == "git":
        _call(["git", "clone", "-q", "--filter=blob:none", source.location, target])
        _call(
            ["git", "-c", "advice.detachedHead=false", "checkout", "-q", source.commit],
            cwd=target,
        )
        if (target / ".gitmodules").exists():
            _call(["git", "submodule", "-q", "update", "--init", "--recursive"], cwd=target)
        return target / source.subdirectory if source.subdirectory else target

    top = source.location

    def ignore(directory, names):
        skip = _COPY_SKIP if directory == top else {"__pycache__"}
        return [n for n in names if n in skip or n.endswith(".egg-info")]

    shutil.copytree(top, target, symlinks=True, ignore=ignore)
    return target


class _BuildVenv:
    """venv with the python version and pip_dependencies of the compute environments"""

    def __init__(self, target: _Target, root: Path, log):
        self.dir = root / "venv"
        self.python = self.dir / "bin" / "python"
        self.pins = list(target.pip_dependencies)
        self.env = _build_env()
        log(f"creating build venv (python {target.python})")
        uv = shutil.which("uv")
        if uv:
            _call(
                [uv, "venv", "-q", "--python-preference", "system"]
                + ["--python", target.python, self.dir],
                env=self.env,
            )
            self._pip = [uv, "pip", "install", "-q", "--python", self.python]
        else:
            interpreter = shutil.which(f"python{target.python}")
            if interpreter is None:
                raise RuntimeError(
                    f"python{target.python} not found, install it or uv to build "
                    "compute_dependencies"
                )
            _call([interpreter, "-m", "venv", self.dir], env=self.env)
            self._pip = [self.python, "-m", "pip", "install", "-q"]
        self.install("build", *self.pins)

    def install(self, *requirements, deps=True):
        _call(self._pip + ([] if deps else ["--no-deps"]) + list(requirements), env=self.env)

    def _requires(self, src: Path, dynamic: bool) -> list[str]:
        out = _output(
            [self.python, "-c", _REQUIRES_SCRIPT, src, "1" if dynamic else "0"],
            env=self.env,
        )
        return json.loads(out.decode().strip().splitlines()[-1])

    def build(self, src: Path, out: Path) -> Path:
        for dynamic in (False, True):
            requires = self._requires(src, dynamic)
            if requires:
                self.install(*requires, *self.pins)
        before = set(out.glob("*.whl"))
        _call(
            [self.python, "-m", "build", "--wheel", "--no-isolation"]
            + ["--outdir", out, src],
            env=self.env,
        )
        wheels = sorted(set(out.glob("*.whl")) - before)
        if len(wheels) != 1:
            raise RuntimeError(f"building {src} gave {len(wheels)} wheels")
        return wheels[0]


def _app_source_dir(package_name: str) -> Path:
    origin = Path(importlib.util.find_spec(package_name).origin).parent
    for path in [origin, *origin.parents][:3]:
        if (path / "pyproject.toml").exists() or (path / "setup.py").exists():
            return path
    raise RuntimeError(f"Could not find source directory for package {package_name}")


def _app_wheel(src_dir: Path):
    from .app import PythonPackage

    with tempfile.TemporaryDirectory() as out:
        _call([sys.executable, "-m", "build", "-n", "-w", "-o", out, src_dir])
        (wheel,) = Path(out).glob("*.whl")
        return PythonPackage(file_name=wheel.name, package=wheel.read_bytes())


def build_compute_packages(config, existing: dict, wheels_dir=None, log=print):
    """(packages, hash) of the compute layer; ``existing`` maps the file names of the
    packages on the backend to their metadata (hash, build_key), packages with an
    unchanged build key are returned with package=None and kept by the backend"""
    from .app import PythonPackage

    if not config.compute_environments:
        return [], ""

    src_dir = _app_source_dir(config.python_package_name)
    packages = [_app_wheel(src_dir)]
    requires = {}  # file name -> Requires-Dist of packages built for the layer
    image_python = _image_python(config)

    provided = {}
    if wheels_dir is not None:
        for path in sorted(Path(wheels_dir).glob("*.whl")):
            data = path.read_bytes()
            problems = check_layer_wheel(path.name, data, image_python)
            if problems:
                raise RuntimeError("\n".join(problems))
            provided[normalize(wheel_tags(path.name)[0])] = path.name
            packages.append(PythonPackage(file_name=path.name, package=data))
            requires[path.name] = _wheel_requires(data)
    elif any((src_dir / "dependencies").glob("*.whl")):
        log(
            f"note: the wheels in {src_dir / 'dependencies'} are not uploaded, use "
            "compute_dependencies or pass the directory with --wheels"
        )

    def zipped(name):
        return PythonPackage(
            file_name=f"{normalize(name)}.zip",
            package=zip_modules([name.replace("-", "_")], dist_info=True, exclude_backend=False),
        )

    seen = set(provided)
    for module in config.frontend_dependencies:
        if normalize(module) in seen:
            continue
        seen.add(normalize(module))
        path = _package_dir(module)
        if path is None:
            raise ModuleNotFoundError(f"frontend dependency {module} is not installed")
        native = _native_files(path)
        if native:
            log(f"warning: frontend dependency {module} contains compiled files ({native[0]})")
        packages.append(zipped(module))

    sources = []
    for spec in config.compute_dependencies:
        name, source = parse_dependency(spec)
        if normalize(name) in seen:
            continue
        seen.add(normalize(name))
        if source is None:
            path = _package_dir(name)
            native = _native_files(path) if path else []
            if path is not None and not native:
                packages.append(zipped(name))
                requires[packages[-1].file_name] = _distribution_requires(name)
                continue
            source = _editable_source(name)
            if source is None:
                problem = f"contains compiled files ({native[0]})" if native else "is not installed"
                raise RuntimeError(
                    f"compute dependency {name} {problem}, give its source to build it: "
                    f"'{name} @ git+ssh://host/repo.git@<commit>' or '{name} @ /path/to/checkout'"
                )
        sources.append(_parse_source(name, source, src_dir))

    if sources:
        target = _build_target(config)
        keys, previous = [], ""
        for source in sources:
            previous = _build_key(source, target, previous)
            keys.append(previous)
        kept = {
            key: next(
                (
                    name
                    for name, md in existing.items()
                    if md.get("build_key") == key
                    and name.endswith(".whl")
                    and normalize(name.split("-")[0]) == normalize(source.name)
                ),
                None,
            )
            for source, key in zip(sources, keys)
        }
        # a build needs the packages built before it installed in the venv
        last = max((i for i, key in enumerate(keys) if kept[key] is None), default=-1)
        built = {}
        if last >= 0:
            with tempfile.TemporaryDirectory(prefix="ngapp-build-") as root:
                root = Path(root)
                out = root / "wheels"
                out.mkdir()
                venv = _BuildVenv(target, root, log)
                for source, key in zip(sources[: last + 1], keys):
                    log(f"building {source.name} from {source.describe()}")
                    wheel = venv.build(_checkout(source, root), out)
                    data = wheel.read_bytes()
                    problems = check_layer_wheel(wheel.name, data, target.python)
                    if problems:
                        raise RuntimeError("\n".join(problems))
                    venv.install(wheel, deps=False)
                    built[key] = (wheel.name, data)
        for source, key in zip(sources, keys):
            if key in built:
                name, data = built[key]
                packages.append(PythonPackage(file_name=name, package=data, build_key=key))
                requires[name] = _wheel_requires(data)
            else:
                log(f"{source.name}: keeping {kept[key]} (same source and environment)")
                packages.append(PythonPackage(file_name=kept[key], package=None, build_key=key))

    names = [p.file_name for p in packages]
    if len(set(names)) != len(names):
        raise RuntimeError(f"duplicate package file names: {names}")
    available = {normalize(n.split("-")[0].removesuffix(".zip")) for n in names}
    _check_requirements(requires, _image_envs(config) or config.compute_environments, available, log)

    digest = hashlib.sha256()
    for p in packages:
        content_hash = calc_hash(p.package) if p.package is not None else existing[p.file_name]["hash"]
        digest.update(f"{p.file_name}:{content_hash}\n".encode())
    return packages, digest.hexdigest()
