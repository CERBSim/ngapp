"""Command line interface of the compute runner"""

import argparse
import os
import platform
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

from .cache import Cache
from .client import BackendClient
from .execute import ApptainerSandbox, NoSandbox
from .runner import Runner


def parse_memory(value: str) -> int:
    """'32GB', '32G', '512M', '2048' (MB) -> MB"""
    v = value.strip().upper().replace("B", "")
    units = {"K": 1 / 1024, "M": 1, "G": 1024, "T": 1024 * 1024}
    if v and v[-1] in units:
        return int(float(v[:-1]) * units[v[-1]])
    return int(v)


def total_memory_mb() -> int:
    try:
        return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") // (1024 * 1024)
    except (ValueError, OSError):
        return 4096


def default_cache_dir() -> Path:
    try:
        import platformdirs

        return Path(platformdirs.user_cache_dir("ngapp-runner"))
    except ImportError:
        return Path.home() / ".cache" / "ngapp-runner"


def get_parser():
    parser = argparse.ArgumentParser(
        prog="python -m ngapp.runner",
        description="Run compute jobs of a webapp backend on this machine",
    )
    parser.add_argument("command", nargs="?", choices=["run", "install-service"], default="run")
    parser.add_argument("--host", required=True, help="backend host, e.g. webapp.cerbsim.com or http://localhost:5001")
    parser.add_argument("--token", default=os.environ.get("NGAPP_RUNNER_TOKEN"), help="runner token (or env NGAPP_RUNNER_TOKEN)")
    parser.add_argument("--token-file", type=Path, default=None, help="file holding the runner token (instead of --token)")
    parser.add_argument(
        "--rotate-token", action="store_true",
        help="exchange the token for a new one at start and store it in --token-file (one-time bootstrap tokens)",
    )
    parser.add_argument("--name", default=platform.node(), help="display name of this runner")
    parser.add_argument("--cpus", type=int, default=os.cpu_count() or 1, help="cpus offered to jobs (default: all)")
    parser.add_argument("--memory", default=f"{total_memory_mb()}M", help="memory offered to jobs, e.g. 32GB (default: all)")
    parser.add_argument("--gpus", type=int, default=0, help="gpus offered to jobs (device indices 0..n-1)")
    parser.add_argument("--gpu-type", default="", help="gpu type name jobs can ask for, e.g. h100")
    parser.add_argument("--scratch", type=int, default=0, help="scratch space offered to jobs in GB")
    parser.add_argument("--sandbox", choices=["apptainer", "none"], default="apptainer")
    parser.add_argument("--no-limits", action="store_true", help="do not apply cgroup cpu/memory limits (apptainer)")
    parser.add_argument("--cache", type=Path, default=default_cache_dir(), help="cache directory for images and app packages")
    parser.add_argument("--cache-size", default="0", help="prune images and app layers above this size, e.g. 20GB (0 = never)")
    parser.add_argument(
        "--job-cache-size", default="10GB",
        help="size of the blob cache of the jobs (<cache>/blobs), least recently used blobs are evicted (0 = no cache)",
    )
    parser.add_argument("--work", type=Path, default=None, help="work directory for running jobs (default <cache>/work)")
    parser.add_argument("--poll", type=int, default=30, help="long-poll seconds per request")
    parser.add_argument("--no-self-update", action="store_true")
    return parser


def log(message: str):
    print(time.strftime("%H:%M:%S"), message, flush=True)


def install_service(args, argv: list[str]):
    """systemd user unit that keeps the runner alive"""
    unit_dir = Path.home() / ".config" / "systemd" / "user"
    unit_dir.mkdir(parents=True, exist_ok=True)
    run_args = [a for a in argv if a != "install-service"]
    exec_start = " ".join([sys.executable, "-m", "ngapp.runner", *run_args])
    unit = unit_dir / "ngapp-runner.service"
    unit.write_text(
        "[Unit]\n"
        "Description=ngapp compute runner\n"
        "After=network-online.target\n\n"
        "[Service]\n"
        f"ExecStart={exec_start}\n"
        "Restart=always\n"
        "RestartSec=10\n\n"
        "[Install]\n"
        "WantedBy=default.target\n"
    )
    print(f"wrote {unit}")
    if shutil.which("systemctl"):
        subprocess.call(["systemctl", "--user", "daemon-reload"])
        subprocess.call(["systemctl", "--user", "enable", "--now", "ngapp-runner.service"])
        print("service enabled and started (systemctl --user status ngapp-runner)")
        print(f"to keep it running without a login session: loginctl enable-linger {os.environ.get('USER', '')}")


def write_token(path: Path, token: str):
    tmp = path.with_suffix(".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(token + "\n")
    os.replace(tmp, path)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    args = get_parser().parse_args(argv)
    if args.token_file and args.token_file.exists():
        args.token = args.token_file.read_text().strip()
    if not args.token:
        print("a runner token is required (--token, --token-file or NGAPP_RUNNER_TOKEN)", file=sys.stderr)
        sys.exit(2)
    if args.rotate_token and not args.token_file:
        print("--rotate-token needs --token-file", file=sys.stderr)
        sys.exit(2)
    if args.command == "install-service":
        install_service(args, argv)
        return

    sandbox = NoSandbox() if args.sandbox == "none" else ApptainerSandbox(limits=not args.no_limits)
    cache = Cache(args.cache, job_cache_size=parse_memory(args.job_cache_size) * 1024 * 1024)
    work = args.work or args.cache / "work"
    work.mkdir(parents=True, exist_ok=True)
    client = BackendClient(args.host, args.token)
    if args.rotate_token:
        write_token(args.token_file, client.rotate_token())
        log("runner token exchanged")
    runner = Runner(
        client,
        cache,
        sandbox,
        cpus=args.cpus,
        memory=parse_memory(args.memory),
        name=args.name,
        work_root=work,
        poll_wait=args.poll,
        self_update=not args.no_self_update,
        cache_size=parse_memory(args.cache_size) * 1024 * 1024,
        log=log,
        gpus=args.gpus,
        gpu_type=args.gpu_type,
        scratch_gb=args.scratch,
    )
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: runner.shutdown())
    runner.run()
