"""Job client and runner reporting against a fake backend: retries while the backend is
unreachable, renewed tokens, idempotency keys, error mapping, blob uploads"""

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from ngapp.job_client import JobClient
from ngapp.runner.client import (
    BackendClient,
    BackendUnavailable,
)
from ngapp.runner.execute import JobExecution, LogPump
from ngapp.runner.runner import Runner
from ngapp.store import (
    BaseGoneError,
    ConflictError,
    IdempotencyMismatchError,
    JobCancelledError,
    StaleAttemptError,
)


class Fake:
    """Answers from a list of (status, body) per path; records requests"""

    def __init__(self):
        self.answers = {}
        self.requests = []
        handler = self._handler()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}/api"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def _handler(self):
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def _answer(self):
                length = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(length) if length else None
                octets = self.headers.get("Content-Type", "").endswith("stream")
                if body is not None and not octets:
                    body = json.loads(body)
                path = self.path.removeprefix("/api")
                fake.requests.append(
                    (
                        self.command,
                        path,
                        {k.lower(): v for k, v in self.headers.items()},
                        body,
                    )
                )
                queue = fake.answers.get(path.split("?")[0], [])
                answer = (
                    queue.pop(0)
                    if len(queue) > 1
                    else (queue[0] if queue else (404, {}))
                )
                status, data, *extra = (
                    answer(self.headers) if callable(answer) else answer
                )
                raw = (
                    data
                    if isinstance(data, bytes)
                    else json.dumps(data).encode()
                )
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                for name, value in (extra[0] if extra else {}).items():
                    self.send_header(name, value)
                self.end_headers()
                self.wfile.write(raw)

            do_GET = do_POST = do_PUT = _answer

            def log_message(self, *a):
                pass

        return Handler

    def close(self):
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
            self.server = None


@pytest.fixture
def fake():
    f = Fake()
    yield f
    f.close()


def test_errors_are_mapped(fake):
    client = JobClient(
        fake.url, 1, 1, token="t", retry_for=0.2, backoff_max=0.05
    )
    path = "/v2/jobs/1/attempts/1/commits"
    fake.answers[path] = [
        (409, {"code": "conflict", "detail": "seq", "last_seq": 4})
    ]
    with pytest.raises(ConflictError) as exc:
        client.commit([], seq=2)
    assert exc.value.data["last_seq"] == 4
    for code, cls in (
        ("stale_attempt", StaleAttemptError),
        ("cancelled", JobCancelledError),
    ):
        ended = JobClient(fake.url, 1, 1, token="t", retry_for=0.2)
        fake.answers[path] = [(409, {"code": code, "detail": "gone"})]
        with pytest.raises(cls):
            ended.commit([])
    # progress is best effort while the backend is down
    fake.answers["/v2/jobs/1/attempts/1/events"] = [(503, {})]
    assert client.progress(0.5, "x") is None
    fake.answers["/v2/jobs/1/input"] = [(200, {"state": {}})]
    assert client.get_input() == {"state": {}}
    fresh = JobClient.from_env(
        {
            "NGAPP_JOB_API": fake.url,
            "NGAPP_JOB_ID": "1",
            "NGAPP_JOB_ATTEMPT": "1",
            "NGAPP_JOB_TOKEN": "t",
        }
    )
    assert fresh.token == "t"


class KeepAlive(Fake):
    """HTTP/1.1 with keep-alive; drops the n-th request of a connection unanswered, as when
    the server closes an idle connection while the client sends on it"""

    def __init__(self, drop_at=None):
        self.drop_at = drop_at
        super().__init__()

    def _handler(self):
        base = super()._handler()
        fake = self

        class Handler(base):
            protocol_version = "HTTP/1.1"
            served = 0

            def _answer(self):
                self.served += 1
                if self.served == fake.drop_at:
                    self.rfile.read(
                        int(self.headers.get("Content-Length") or 0)
                    )
                    self.close_connection = True
                    return
                super()._answer()

            do_GET = do_POST = do_PUT = _answer

        return Handler


def test_stale_connection_and_last_progress():
    fake = KeepAlive(drop_at=2)
    try:
        events = "/v2/jobs/1/attempts/1/events"
        commits = "/v2/jobs/1/attempts/1/commits"
        fake.answers[events] = [(200, {"seq": 1})]
        fake.answers[commits] = [(201, {"revision": 3})]
        # no retries at all: the request on the dropped pooled connection is sent again once
        client = JobClient(
            fake.url, 1, 1, token="t", retry_for=0, backoff_max=0.05
        )
        assert client.progress(0.1, "a") == {"seq": 1}
        assert client.progress(0.2, "b") == {"seq": 1}
        assert [r[3]["text"] for r in fake.requests] == ["a", "b"]
        assert client.commit([], seq=1)["revision"] == 3

        # the last progress, lost while the backend was down, goes before the final commit
        fake.drop_at = None
        client = JobClient(
            fake.url, 1, 1, token="t", progress_retry_for=0.2, backoff_max=0.05
        )
        fake.answers[events] = [
            (503, {}),
            (503, {}),
            (503, {}),
            (503, {}),
            (503, {}),
            (200, {}),
        ]
        assert client.progress(1.0, "last") is None
        fake.answers[events] = [(200, {"seq": 2})]
        fake.requests.clear()
        client.commit([], final=True)
        assert [r[1] for r in fake.requests] == [events, commits]
        assert fake.requests[0][3]["text"] == "last"
        client.commit([], seq=5, final=True)
        assert [r[1] for r in fake.requests] == [events, commits, commits]
    finally:
        fake.close()


def test_log_pump_keeps_data_while_backend_is_down():
    sent = []
    fail = [True]

    def send(data):
        if fail[0]:
            raise BackendUnavailable("down")
        sent.append(data)

    pump = LogPump(None, send)
    pump.buffer, pump.size = ["a\n", "b\n"], 4
    pump.flush()
    assert sent == [] and "".join(pump.buffer) == "a\nb\n"
    fail[0] = False
    pump.buffer.append("c\n")
    pump.flush()
    assert sent == ["a\nb\nc\n"]


def _execution(fake, tmp_path, logs, job_id=6):
    assignment = {
        "job_id": job_id,
        "attempt": 1,
        "cpus": 1,
        "memory_mb": 10,
        "lease_s": 0.3,
        "token": "t",
    }
    job = JobExecution(
        assignment,
        BackendClient(fake.url, "ngr_x"),
        None,
        None,
        tmp_path,
        lambda j: None,
        log=logs.append,
    )
    job.work.mkdir(parents=True)
    return job


def test_heartbeat_failures_logged_per_state_change(fake, tmp_path):
    """Failing heartbeats keep the job and are logged when the state changes,
    a refusal (403) is no unreachable backend"""
    logs = []
    job = _execution(fake, tmp_path, logs)
    path = "/v2/runner/jobs/6/heartbeat"
    fake.answers[path] = [(503, {})]
    for _ in range(5):
        assert job._heartbeat(force=True) is False
    fake.answers[path] = [(403, {"code": "forbidden", "detail": "no access"})]
    for _ in range(5):
        assert job._heartbeat(force=True) is False
    fake.answers[path] = [(200, {"cancel": False, "token": "renewed"})]
    for _ in range(3):
        assert job._heartbeat(force=True) is True
    assert len(logs) == 3, logs
    assert "503" in logs[0] and "no access" in logs[1] and "again" in logs[2]
    assert not job.cancelled and not job.lost


class _Client:
    """Runner client whose job requests fail with the given exceptions"""

    def __init__(self, runner_holder, errors):
        self.base = "fake"
        self.errors = errors
        self.holder = runner_holder

    def request_job(self, state, wait):
        if not self.errors:
            self.holder[0].stop.set()
            return None
        raise self.errors.pop(0)

    def heartbeat(self, state, running, stopping=False, timeout=None):
        return {}


def test_reported_capacity(tmp_path):
    """The report: totals offered to jobs (without the reservations of services)
    and the capacity free of running processes; a job whose process ended does
    not count, the backend counts it until its finish"""
    runner = Runner(
        None,
        None,
        None,
        cpus=8,
        memory=1000,
        name="t",
        work_root=tmp_path,
        gpus=2,
        scratch_gb=10,
    )
    runner.cache = type("C", (), {"cached_envs": lambda self: []})()
    runner.sandbox = type("S", (), {"name": "none"})()
    runner.services = type("V", (), {"reserved": lambda self: (1, 200)})()

    def job(cpus, memory, gpus, scratch_gb):
        fields = {"cpus": cpus, "memory": memory, "gpus": gpus}
        return type("J", (), {**fields, "scratch_gb": scratch_gb})()

    runner.jobs[6] = job(2, 100, [0], 3)
    runner.reporting[7] = job(1, 50, [1], 2)
    state = runner.state()
    assert (state["cpus"], state["memory"]) == (7, 800)
    assert (state["free_cpus"], state["free_memory"]) == (5, 700)
    assert (state["free_gpus"], state["free_scratch_gb"]) == (1, 7)
    assert runner.free() == (5, 700) and runner.free_gpus() == [1]
    assert sorted(runner.running_jobs()) == [6, 7]


def test_new_error_codes(fake, monkeypatch):
    """idempotency_mismatch and base_gone are raised, rate_limited waits as
    long as Retry-After says"""
    client = JobClient(fake.url, 5, 1, token="t", retry_for=60)
    path = "/v2/jobs/5/attempts/1/commits"
    fake.answers[path] = [
        (422, {"code": "idempotency_mismatch", "detail": "other body"})
    ]
    with pytest.raises(IdempotencyMismatchError):
        client.commit([])
    fake.answers[path] = [(409, {"code": "base_gone", "detail": "dropped"})]
    with pytest.raises(BaseGoneError, match="dropped"):
        client.commit([])
    assert len([r for r in fake.requests if r[1] == path]) == 2
    waits = []
    sleep = time.sleep
    monkeypatch.setattr(time, "sleep", lambda t: waits.append(t) or sleep(0))
    fake.answers[path] = [
        (429, {"code": "rate_limited"}, {"Retry-After": "7"}),
        (429, {"code": "rate_limited", "retry_after": 3}, {"Retry-After": "3"}),
        (201, {"revision": 9}),
    ]
    assert client.commit([])["revision"] == 9
    assert waits == [7, 3]


def _stream_answers(fake, h, size, offset=0):
    fake.answers["/v2/uploads/s1/blobs"] = [
        (
            200,
            {
                "hash": h,
                "uploaded": False,
                "method": "stream",
                "part_size": 1000,
                "offset": offset,
            },
        )
    ]
    fake.answers[f"/v2/uploads/s1/blobs/{h}/complete"] = [
        (200, {"hash": h, "state": "verified"})
    ]


def test_fenced_finish_is_logged(fake, tmp_path):
    """An attempt fenced while its finish is retried says so in the log"""
    logs = []
    job = _execution(fake, tmp_path, logs, job_id=8)
    fake.answers["/v2/runner/jobs/8/finish"] = [(503, {})]
    detail = "the attempt is no longer active"
    fake.answers["/v2/runner/jobs/8/heartbeat"] = [
        (409, {"code": "stale_attempt", "detail": detail})
    ]
    job._report("succeeded", 0, "", 1.0)
    assert f"[job 8] finish rejected: 409 stale_attempt: {detail}" in logs, logs
