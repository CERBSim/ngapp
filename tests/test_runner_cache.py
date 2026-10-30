"""Caches of the runner: job blob cache and the image and layer cache under one
limit; eviction never removes what a running job or service uses"""

import hashlib
import os
import threading
import time
import uuid

from ngapp.runner.cache import Cache, JobBlobCache


def _blob(case_dir, data: bytes) -> str:
    """Write like a job process: tmp, then rename into place"""
    hexd = hashlib.sha256(data).hexdigest()
    target = case_dir / "sha256" / hexd[:2] / hexd
    if target.exists():
        return hexd
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = case_dir / "tmp" / uuid.uuid4().hex
    tmp.write_bytes(data)
    os.rename(tmp, target)
    return hexd


def _age(path, seconds):
    t = time.time() - seconds
    os.utime(path, (t, t))


def test_job_cache_layout_and_lru(tmp_path):
    cache = JobBlobCache(tmp_path / "blobs", max_bytes=3000)
    old, new = cache.case_dir(1), cache.case_dir(2)
    a = _blob(old, b"a" * 1000)
    b = _blob(new, b"b" * 1000)
    c = _blob(new, b"c" * 1000)
    assert (old / "sha256" / a[:2] / a).read_bytes() == b"a" * 1000
    for f in (old / "sha256").rglob("*"):
        _age(f, 3600)
    _age(old / ".used", 3600)
    assert cache.prune(set()) == []
    _blob(new, b"d" * 1000)
    removed = cache.prune(set())
    assert [p.name for p in removed] == [a]
    assert not old.exists()  # empty case directories go
    assert {p.name for p in (new / "sha256").rglob("*") if p.is_file()} >= {
        b,
        c,
    }


def test_job_cache_pins_and_tmp(tmp_path):
    cache = JobBlobCache(tmp_path / "blobs", max_bytes=0)
    running, ended = cache.case_dir(7), cache.case_dir(8)
    kept = _blob(running, b"x" * 100)
    _blob(ended, b"y" * 100)
    (running / "tmp" / "partial").write_bytes(b"p")
    (ended / "tmp" / "partial").write_bytes(b"p")
    cache.prune({7})
    assert (running / "sha256" / kept[:2] / kept).exists()
    assert (
        running / "tmp" / "partial"
    ).exists()  # a running job may still write it
    assert not ended.exists()
    assert cache.clean_tmp() == 1  # at the start of the runner


def test_image_and_layer_limit_with_pins(tmp_path):
    cache = Cache(tmp_path / "cache")
    for i, name in enumerate(("img-old", "img-used", "img-new")):
        path = cache.image_path(name)
        path.write_bytes(b"i" * 1000)
        _age(path, 1000 - i)
    layer = cache.layer_path("layer-old")
    layer.mkdir()
    (layer / "pkg.py").write_bytes(b"l" * 1000)
    (layer / ".size").write_text("1000")
    (layer / ".complete").touch()
    _age(layer / ".complete", 5000)
    (cache.envs / "img-part.sif.part").write_bytes(b"p" * 1000)
    _age(cache.envs / "img-part.sif.part", 2000)

    cache.pin(("job", 1), images=["img-used", "img-part"], layers=["layer-old"])
    removed = {p.name for p in cache.prune(4000, log=lambda m: None)}
    assert removed == {
        "img-old.sif"
    }  # img-used, the download and the layer are pinned
    assert cache.cached_envs() == ["img-new", "img-used"]

    cache.unpin(("job", 1))
    removed = {p.name for p in cache.prune(1000, log=lambda m: None)}
    assert removed == {"layer-old", "img-part.sif.part", "img-used.sif"}
    assert cache.cached_envs() == ["img-new"]


def test_pin_waits_for_prune(tmp_path):
    """A job pinning an image while an eviction runs either keeps it or finds it gone"""
    cache = Cache(tmp_path / "cache")
    for round_ in range(50):
        path = cache.image_path("shared")
        path.write_bytes(b"s" * 100)
        _age(path, 100)
        seen = {}

        def job():
            cache.pin("job", images=["shared"])
            seen["exists"] = path.exists()

        t = threading.Thread(target=job)
        t.start()
        cache.prune(0, log=lambda m: None)
        t.join()
        if seen["exists"]:
            assert path.exists(), round_
        cache.unpin("job")
