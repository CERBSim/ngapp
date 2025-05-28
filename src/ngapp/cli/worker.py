import argparse

from redis import Redis
from rq import Queue, Worker

from .. import api
from .run import RunData


def job_on_stopped_callback(job, connection):
    """Callback that is executed when a worker receives a command to stop a job that is currently executing"""
    data = RunData.load(job.args[0])
    api.set_access(data.api_url, data.api_token)
    api_url = f"/job/{data.job_id}"
    api.put(api_url, {"status": "Stopped"})
    api.put(f"{api_url}/stderr", "\nSTATUS: Job stopped by user\n")


def main():
    parser = argparse.ArgumentParser(description="Webapp client worker")
    parser.add_argument("queue_name", help="Name of job queue", type=str)
    parser.add_argument("--redis", help="Redis host:port", type=str)
    parser.add_argument("--redis-user", help="Redis user name", type=str)
    parser.add_argument("--redis-pass", help="Redis password", type=str)

    args = parser.parse_args()
    host, port = args.redis.split(":")
    port = int(port)

    print("connect to redis", host, port, args.redis_user, args.redis_pass)
    redis = Redis(
        host=host, port=port, username=args.redis_user, password=args.redis_pass
    )
    print("attach to queue", args.queue_name)
    queue = Queue(args.queue_name, connection=redis)

    worker = Worker([queue], connection=redis)
    worker.work(logging_level="WARNING", max_idle_time=1800)


if __name__ == "__main__":
    main()
