"""Command line of the runner: resource defaults; peak memory units"""

import os

from ngapp.runner import cli


class FakeRunner:
    created = []

    def __init__(self, client, cache, sandbox, **kwargs):
        self.kwargs = kwargs
        FakeRunner.created.append(self)

    def run(self):
        pass

    def shutdown(self):
        pass


def test_normal_runner_defaults(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "Runner", FakeRunner)
    base = [
        "--host",
        "http://localhost:1",
        "--token",
        "t",
        "--cache",
        str(tmp_path),
        "--sandbox",
        "none",
    ]
    cli.main(base)
    kw = FakeRunner.created.pop().kwargs
    assert (
        kw["cpus"] == (os.cpu_count() or 1)
        and kw["memory"] == cli.total_memory_mb()
    )
    assert (kw["gpus"], kw["gpu_type"]) == (0, "")

    cli.main(
        [
            *base,
            "--cpus",
            "3",
            "--memory",
            "2G",
            "--gpus",
            "1",
            "--gpu-type",
            "h100",
        ]
    )
    kw = FakeRunner.created.pop().kwargs
    assert (kw["cpus"], kw["memory"], kw["gpus"], kw["gpu_type"]) == (
        3,
        2048,
        1,
        "h100",
    )


def test_peak_memory_units():
    from ngapp.runner.execute import maxrss_mb

    assert maxrss_mb(2048 * 1024, "linux") == 2048
    assert maxrss_mb(2048 * 1024 * 1024, "darwin") == 2048
