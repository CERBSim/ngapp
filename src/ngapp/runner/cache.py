"""Local caches of a runner: environment images (SIF) and app package layers under one size
limit, and the blob cache of the jobs.

The runner pins what its running jobs and services use (images, layers, case directories of
the blob cache); eviction never removes pinned entries, a pin waits for an eviction in
progress.
"""

import fcntl
import os
import shutil
import tempfile
import threading
import zipfile
from contextlib import contextmanager
from pathlib import Path

from .client import BackendClient


def _remove(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
    else:
        path.unlink(missing_ok=True)


def _tree_size(path: Path) -> int:
    total = 0
    for root, _, files in os.walk(path):
        for name in files:
            try:
                total += os.lstat(os.path.join(root, name)).st_size
            except OSError:
                pass
    return total


class JobBlobCache:
    """Blobs of the jobs, one directory per case: <case dir>/sha256/<hex[0:2]>/<hex>. Job
    processes download into <case dir>/tmp, verify and rename into place; the sandbox of a job
    sees only the directory of its case. The directories of the cases of running jobs are
    pinned; above the size limit the least recently used files of other cases are removed."""

    def __init__(self, root: Path, max_bytes: int):
        self.root = root
        self.max_bytes = max_bytes
        root.mkdir(parents=True, exist_ok=True)

    def case_dir(self, case_id: int) -> Path:
        d = self.root / f"case-{int(case_id)}"
        (d / "sha256").mkdir(parents=True, exist_ok=True)
        (d / "tmp").mkdir(exist_ok=True)
        (d / ".used").touch()
        return d

    def used(self, case_id: int) -> None:
        try:
            (self.root / f"case-{int(case_id)}" / ".used").touch()
        except FileNotFoundError:
            pass

    def _cases(self):
        for d in self.root.glob("case-*"):
            try:
                yield int(d.name[5:]), d
            except ValueError:
                continue

    def clean_tmp(self, pinned: set[int] = frozenset()) -> int:
        """Partial downloads of jobs that ended (all of them at the start of the runner)"""
        removed = 0
        for case_id, d in self._cases():
            if case_id in pinned:
                continue
            for f in (d / "tmp").glob("*"):
                _remove(f)
                removed += 1
        return removed

    def size(self) -> int:
        return sum(_tree_size(d) for _, d in self._cases())

    def prune(self, pinned: set[int], log=print) -> list[Path]:
        """Remove least recently used files of unpinned cases until the cache fits"""
        self.clean_tmp(pinned)
        entries, total = [], 0
        for case_id, d in self._cases():
            marker = d / ".used"
            try:
                used = marker.stat().st_mtime
            except FileNotFoundError:
                used = 0
            for root, _, files in os.walk(d):
                for name in files:
                    f = Path(root) / name
                    try:
                        st = f.lstat()
                    except FileNotFoundError:
                        continue
                    total += st.st_size
                    if case_id not in pinned and f.parent.parent.name == "sha256":
                        entries.append((max(st.st_atime, st.st_mtime, used), st.st_size, f))
        removed = []
        for _, size, f in sorted(entries):
            if total <= self.max_bytes:
                break
            f.unlink(missing_ok=True)
            total -= size
            removed.append(f)
        if removed:
            log(f"job blob cache: removed {len(removed)} files")
        for case_id, d in self._cases():
            if case_id not in pinned and not any(f.is_file() for f in (d / "sha256").rglob("*")):
                shutil.rmtree(d, ignore_errors=True)
        return removed


class Cache:
    def __init__(self, root: Path, job_cache_size: int = 0):
        self.root = root
        self.envs = root / "envs"
        self.apps = root / "apps"
        self.locks = root / "locks"
        for d in (self.envs, self.apps, self.locks):
            d.mkdir(parents=True, exist_ok=True)
        self.jobs = JobBlobCache(root / "blobs", job_cache_size) if job_cache_size > 0 else None
        self._mutex = threading.RLock()
        self._pins: dict[object, dict[str, set]] = {}

    @contextmanager
    def lock(self, name: str):
        path = self.locks / f"{name}.lock"
        with open(path, "w") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

    # pins

    def pin(self, owner, images=(), layers=(), cases=()) -> None:
        """What a job or service uses, replacing earlier pins of the owner; waits for an
        eviction in progress"""
        with self._mutex:
            self._pins[owner] = {
                "images": {i for i in images if i},
                "layers": {lh for lh in layers if lh},
                "cases": {int(c) for c in cases if c is not None},
            }

    def unpin(self, owner) -> None:
        with self._mutex:
            pins = self._pins.pop(owner, None)
        if pins and self.jobs:
            for case_id in pins["cases"]:
                self.jobs.used(case_id)

    def pinned(self, kind: str) -> set:
        with self._mutex:
            return set().union(*(p[kind] for p in self._pins.values()))

    def start(self, log=print) -> None:
        """At the start of the runner no job runs: partial job downloads are leftovers"""
        if self.jobs:
            removed = self.jobs.clean_tmp()
            if removed:
                log(f"job blob cache: removed {removed} partial downloads")

    def job_dir(self, case_id: int) -> Path | None:
        """Blob cache directory of a job's case (NGAPP_JOB_CACHE_DIR), None without a cache"""
        return self.jobs.case_dir(case_id) if self.jobs else None

    # images

    def image_path(self, sif_hash: str) -> Path:
        return self.envs / f"{sif_hash}.sif"

    def cached_envs(self) -> list[str]:
        return sorted(p.stem for p in self.envs.glob("*.sif"))

    def ensure_image(self, client: BackendClient, env: dict, log=print) -> Path:
        path = self.image_path(env["sif_hash"])
        if path.exists():
            path.touch()
            return path
        with self.lock(env["sif_hash"]):
            if path.exists():
                return path
            log(f"downloading image {env['sif_hash'][:12]} for compute environment {env['id']}")
            client.download(env["image_url"], path, sha256=env["sif_hash"])
        return path

    # layers (app wheels + ngapp on top of the image)

    def layer_path(self, lhash: str) -> Path:
        return self.apps / lhash

    def ensure_layer(self, client: BackendClient, layer: dict, log=print) -> Path:
        """Wheels (pure python) and package zips are simply extracted, no pip involved"""
        target = self.layer_path(layer["hash"])
        done = target / ".complete"
        if done.exists():
            done.touch()
            return target
        with self.lock("layer-" + layer["hash"]):
            if done.exists():
                return target
            log(f"installing app package layer {layer['hash'][:12]}")
            if target.exists():
                shutil.rmtree(target)
            target.mkdir(parents=True)
            with tempfile.TemporaryDirectory() as tmp:
                archive = Path(tmp) / "layer.zip"
                archive.write_bytes(client.get_bytes(layer["url"]))
                with zipfile.ZipFile(archive) as zf:
                    zf.extractall(tmp)
                archives = sorted((Path(tmp) / "packages").glob("*.zip"))
                archives += sorted((Path(tmp) / "wheels").glob("*.whl"))
                for archive in archives:
                    with zipfile.ZipFile(archive) as zf:
                        zf.extractall(target)
            (target / ".size").write_text(str(_tree_size(target)))
            done.touch()
        return target

    # housekeeping

    def _entries(self) -> list[tuple[float, int, Path, str]]:
        """(last use, size, path, hash) of images, partial image downloads and layers"""
        entries = []
        for p in self.envs.iterdir():
            if p.name.endswith(".sif") or p.name.endswith(".sif.part"):
                st = p.stat()
                entries.append((st.st_mtime, st.st_size, p, p.name.split(".")[0]))
        for d in self.apps.iterdir():
            if not d.is_dir():
                continue
            done = d / ".complete"
            try:
                size = int((d / ".size").read_text())
            except (OSError, ValueError):
                size = _tree_size(d)
            used = done.stat().st_mtime if done.exists() else d.stat().st_mtime
            entries.append((used, size, d, d.name))
        return entries

    def prune(self, max_bytes: int, log=print) -> list[Path]:
        """Drop least recently used images and layers above max_bytes, never one that a job or
        service uses"""
        removed = []
        with self._mutex:
            images, layers = self.pinned("images"), self.pinned("layers")
            entries = self._entries()
            total = sum(e[1] for e in entries)
            for _, size, path, name in sorted(entries):
                if total <= max_bytes:
                    break
                if name in (layers if path.parent == self.apps else images):
                    continue
                log(f"cache: removing {path.name}")
                _remove(path)
                total -= size
                removed.append(path)
        return removed

    def prune_jobs(self, log=print) -> list[Path]:
        """Eviction of the job blob cache above its size limit"""
        if not self.jobs:
            return []
        with self._mutex:
            return self.jobs.prune(self.pinned("cases"), log=log)
