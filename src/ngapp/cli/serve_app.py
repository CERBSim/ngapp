"""Command line interface for webapp to serve an app"""

import asyncio
import importlib
import sys

import jwt

from .. import __version__, api
from ..utils import EnvironmentType, set_environment
from .serve_in_venv import get_args_parser


async def run_process(command):
    process = await asyncio.create_subprocess_exec(*command)
    return await process.communicate()


async def run_serve_process(command, args_object):
    args = [
        sys.executable,
        "-m",
        command,
        args_object.backend_url,
        args_object.token,
        str(args_object.app_id),
        args_object.python_package,
    ]
    if args_object.local_compute_env:
        args.append("--local_compute_env")
    if args_object.build_backend_packages:
        args.append("--build_backend_packages")
    if args_object.deploy:
        args.append("--deploy")
    return await run_process(args)


async def main():
    parser = get_args_parser(
        description="Serve an app frontend and compute node from local machine"
    )

    parser.add_argument(
        "--update_ngapp",
        help="Check version of ngapp and update if necessary",
        action="store_true",
        required=False,
    )

    args = parser.parse_args()

    if args.deploy:
        args.build_backend_packages = True

    set_environment(EnvironmentType.COMPUTE, have_backend=True).set_backend(
        args.backend_url, args.token
    )

    try:
        importlib.import_module(args.python_package)
    except ImportError:
        raise RuntimeError(
            f"Cannot import python package {args.python_package}. Did you install it running 'pip install -e .' inside the app directory?"
        )

    try:
        config = importlib.import_module(args.python_package).config
    except ImportError:
        raise RuntimeError(f"Cannot import config from {args.python_package}")

    client_version = api.get("/pyodide/client_version/ngapp")
    if args.update_ngapp and client_version != __version__:
        # update ngapp, then run myself again with same argument
        # (this time without the need to update ngapp)
        client = api.get("/pyodide/client_package/ngapp")
        wheel_name = f"ngapp-{client_version}-py3-none-any.whl"
        with open(wheel_name, "wb") as f:
            f.write(client)

        await run_process([sys.executable, "-m", "pip", "install", wheel_name])
        await run_serve_process("ngapp.cli.serve_app", args)
        return

    tasks = [run_serve_process("ngapp.cli.serve_in_venv", args)]

    if args.rq:
        compute_envs = api.post(
            f"/app_admin/app_compute_environments/{args.app_id}", {}
        )
        for compute_env in compute_envs:
            compute_env_id = compute_env["id"]
            data = jwt.decode(args.token, verify=False, algorithms=["HS256"])
            redis_data = data["redis"][str(compute_env_id)]
            cmd = [
                sys.executable,
                "-m",
                "ngapp.cli.worker",
                f"compute_env_{compute_env_id}",
                "--redis",
                "localhost:6379",
                "--redis-user",
                redis_data["user"],
                "--redis-pass",
                redis_data["pass"],
            ]
            args.local_compute_env = False
            tasks.append(run_process(cmd))
    elif (
        config.compute_environments
        and args.local_compute_env
        and not args.deploy
    ):
        print("Serve local compute environment")
        tasks.append(run_serve_process("ngapp.cli.serve_compute_env", args))
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down serve_app")
