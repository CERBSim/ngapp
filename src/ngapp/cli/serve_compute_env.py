"""command line interface for webapp to serve a compute environment"""

import asyncio
import ssl
import threading

import certifi
import orjson
import websockets

from ..utils import EnvironmentType, get_environment, set_environment
from .run import RunData, run_compute_function
from .serve_in_venv import get_args_parser

set_environment(EnvironmentType.COMPUTE, True)


def handle_task(data_string):
    data = RunData.load(data_string)
    print(
        f"handle task, file_id={data.file_id}, func={data.func_name}",
        flush=True,
    )
    data.use_venv = False
    data.capture_output = False
    run_compute_function(data)


async def main(arg):
    app_id = int(args.app_id)
    ws_url = args.backend_url + "/ws/connect"
    ws_url = ws_url.replace("https://", "wss://")
    ws_url = ws_url.replace("http://", "ws://")
    ssl_context = None
    if ws_url.startswith("wss://"):
        ssl_context = ssl.create_default_context(cafile=certifi.where())

    while True:
        try:
            async with websockets.connect(ws_url, ssl=ssl_context) as websocket:
                await websocket.send(
                    orjson.dumps(
                        {
                            "token": args.token,
                            "type": "compute_env",
                            "app_id": app_id,
                        }
                    )
                )
                while True:
                    msg = await websocket.recv()
                    thread = threading.Thread(target=handle_task, args=(msg,))
                    thread.start()
                    thread.join()
        except KeyboardInterrupt:
            break
        except Exception as e:
            print("Error", e)


if __name__ == "__main__":
    parser = get_args_parser(
        description="Serve an app frontend and compute node from local machine"
    )
    args = parser.parse_args()

    env = get_environment()
    env.set_backend(args.backend_url, args.token)

    try:
        asyncio.run(main(args))
    except KeyboardInterrupt:
        print("Shutting down compute env")
