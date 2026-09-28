import argparse
import os

from redis import Redis
from rq import Queue, Worker
from rq.utils import now, utcformat

from .. import api
from .run import RunData


class WebappWorker(Worker):
    """rq worker that records slurm job, node and idle time in its redis hash (used by the admin compute dashboard)"""

    def __init__(self, *args, max_idle_time: int | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_idle_time = max_idle_time

    def register_birth(self):
        super().register_birth()
        data = {"max_idle_time": self.max_idle_time or 0}
        if os.environ.get("SLURM_JOB_ID"):
            data["slurm_job_id"] = os.environ["SLURM_JOB_ID"]
            data["node"] = os.environ.get("SLURMD_NODENAME", "")
        self.connection.hset(self.key, mapping=data)

    def dequeue_job_and_maintain_ttl(self, timeout, max_idle_time=None):
        self.connection.hset(self.key, "idle_since", utcformat(now()))
        result = super().dequeue_job_and_maintain_ttl(timeout, max_idle_time)
        if result is not None:
            self.connection.hdel(self.key, "idle_since")
        return result


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
    parser.add_argument(
        "--max-idle-time",
        help="Exit after being idle for this many seconds",
        type=int,
        default=1800,
    )

    args = parser.parse_args()
    host, port = args.redis.split(":")
    port = int(port)

    print("connect to redis", host, port, args.redis_user, args.redis_pass)
    redis = Redis(
        host=host, port=port, username=args.redis_user, password=args.redis_pass
    )
    print("attach to queue", args.queue_name)
    queue = Queue(args.queue_name, connection=redis)

    # name workers after their slurm job to link them to the slurm node
    name = None
    if os.environ.get("SLURM_JOB_ID") and os.environ.get("SLURMD_NODENAME"):
        name = f"{os.environ['SLURMD_NODENAME']}.{os.environ['SLURM_JOB_ID']}"

    worker = WebappWorker(
        [queue], connection=redis, name=name, max_idle_time=args.max_idle_time
    )
    worker.work(logging_level="WARNING", max_idle_time=args.max_idle_time)


if __name__ == "__main__":
    main()
