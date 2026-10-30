"""Entry point used by ngapp.runner inside the sandbox: run one job attempt.

The runner passes the job description (job.json) as argument and the protocol settings in
NGAPP_JOB_* environment variables (see ngapp.job_client). A local runner of the SQLite store
sets NGAPP_JOB_DB instead of NGAPP_JOB_API (ngapp.store.local_jobs).
"""

import json
import os
import sys
from pathlib import Path

from ..job_client import JobClient
from ..store import CaseDeletedError, JobEndedError
from ..utils import print_exception

EXIT_ENDED = 3

_ended: list = []


def _on_ended(error):
    """A checkpoint in a timer thread learned that the attempt ended"""
    from ..jobs import interrupt_main

    _ended.append(error)
    interrupt_main(error)


def _client():
    if os.environ.get("NGAPP_JOB_DB"):
        from ..store.sqlite import SQLiteJobClient

        return SQLiteJobClient.from_env()
    return JobClient.from_env()


def main():
    from ..jobs import job_environment, run_job

    data = json.loads(Path(sys.argv[1]).read_text())
    client = _client()
    print(
        f"STATUS: job {client.job_id} attempt {client.attempt} started ({data['function']})",
        flush=True,
    )
    job_environment()
    try:
        run_job(client, data, on_ended=_on_ended)
    except (JobEndedError, CaseDeletedError) as e:
        # the backend ended the attempt (stale, cancelled, case deleted): stop at once
        print(f"STATUS: {e}", flush=True)
        sys.exit(EXIT_ENDED)
    except KeyboardInterrupt:
        if not _ended:
            raise
        print(f"STATUS: {_ended[0]}", flush=True)
        sys.exit(EXIT_ENDED)
    except Exception as e:
        print_exception(e)
        try:  # shown by the job controls of the app
            client.message(f"{type(e).__name__}: {e}"[:2000], "error")
        except Exception:
            pass
        sys.exit(1)
    print(f"STATUS: job {client.job_id} finished", flush=True)


if __name__ == "__main__":
    main()
