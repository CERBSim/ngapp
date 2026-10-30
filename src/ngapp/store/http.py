"""Case store on the HTTP API v2 of the backend

HTTPStore talks to the backend with urllib3, so it also runs in pyodide, where
urllib3 uses the browser (no threads needed there). Base URL, token and client
id are read at every request, by default from the Environment, so a token
refreshed by the frontend needs no reopen. Every mutating request carries an
Idempotency-Key, and transient failures are retried with the same key. Error
answers raise the exceptions of ngapp.store.

A store without a release id commits with the release of the case head it saw
first, so a client never overwrites a case saved by a newer release.

Events: in pyodide the browser's main thread owns the websocket and forwards
the events of the open case and of the user's jobs to deliver_events().
Elsewhere subscribe() opens its own websocket (optional package websockets) or
polls the head of the subscribed cases.
"""

import contextlib
import dataclasses
import logging
import threading
import time
import uuid
from typing import BinaryIO, Callable
from urllib.parse import urlencode

import orjson
import urllib3

from .transfer import RETRY_STATUS, Source, Uploads, error_from, json_default
from .types import (
    BlobRef,
    CaseDeletedError,
    CaseInfo,
    CommitResult,
    Event,
    InvalidError,
    JobInfo,
    JobRequest,
    MissingResult,
    NotFoundError,
    Op,
    RateLimitedError,
    RunInfo,
    StoreError,
    TransientStoreError,
    UnauthorizedError,
)

logger = logging.getLogger("ngapp.store.http")

_NAMESPACE = uuid.UUID("2b0f4b6e-58d4-4c8e-9a51-6f1e0c7d3a92")
_MUTATING = ("POST", "PUT", "PATCH", "DELETE")
_REDIRECT = (301, 302, 303, 307, 308)
# events of the user's topic, delivered to every subscription
_USER_EVENTS = ("cases.changed", "app.release")


def _idempotency_key(key) -> str:
    """The backend takes UUIDs; other keys are mapped to one"""
    if key is None:
        return str(uuid.uuid4())
    try:
        return str(uuid.UUID(str(key)))
    except ValueError:
        return str(uuid.uuid5(_NAMESPACE, str(key)))


def _bearer(token: str) -> str:
    return token if token.lower().startswith("bearer ") else f"Bearer {token}"


def _parse(cls, data: dict, **renamed):
    """Dataclass from JSON; unknown fields go to extra"""
    names = {f.name for f in dataclasses.fields(cls)}
    values = {renamed.get(k, k): v for k, v in data.items()}
    known = {k: v for k, v in values.items() if k in names and k != "extra"}
    extra = {k: v for k, v in data.items() if renamed.get(k, k) not in names}
    if "extra" in names:
        return cls(**known, extra=extra)
    obj = cls(**known)
    obj.extra = extra
    return obj


def _case_info(data: dict) -> CaseInfo:
    info = _parse(
        CaseInfo,
        {k: v for k, v in data.items() if k != "access"},
        owner_id="owner",
        head_revision="head",
    )
    info.name = info.name or ""
    info.write = data.get("access", "owner") in ("owner", "write")
    return info


def _ops(data) -> list[Op]:
    return [Op.from_json(op) for op in data]


def _client_state(data: dict) -> dict:
    """Materialised state of the server (sequences marked) in the form of
    the store interface: {"revision", "release", "children"}"""

    def component(node: dict) -> dict:
        out = {}
        for key, value in node.items():
            if key == "children":
                if value:
                    out["children"] = {
                        c: component(n) for c, n in value.items()
                    }
            elif value:
                out[key] = value
        return out

    return {
        "revision": data["revision"],
        "release": data.get("release_id"),
        "event_seq": data.get("event_seq"),
        "children": {c: component(n) for c, n in data["state"].items()},
    }


class HTTPStore(Uploads):
    """CaseStore of the user of the token on the backend's HTTP API v2

    api_url, token and client_id are values or callables; None reads them from
    the Environment (backend_api_url, backend_api_token,
    backend_api_client_id). events: "auto", "deliver" (pyodide),
    "websocket" or "poll". retry_for: seconds transient failures are retried
    with backoff (default 10, 0 in pyodide, where the caller retries without
    blocking the worker).
    """

    def __init__(
        self,
        api_url=None,
        token=None,
        *,
        client_id=None,
        release_id: int | None = None,
        events: str = "auto",
        retry_for: float | None = None,
        backoff_max: float = 2.0,
        timeout: float = 60.0,
        poll_interval: float = 2.0,
        http=None,
    ):
        self._api_url = api_url
        self._token = token
        self._client_id = client_id
        self.release_id = release_id
        self.events = events
        if retry_for is None:
            retry_for = 0.0 if _is_pyodide() else 10.0
        self.retry_for = retry_for
        self.backoff_max = backoff_max
        self.timeout = timeout
        self.poll_interval = poll_interval
        self.http = http or urllib3.PoolManager()
        self._releases: dict[int, int | None] = {}
        self._sessions: dict[str, int] = {}
        self._renamed: dict[str, str] = {}
        self._presigned: dict[tuple[int, str], tuple[str, float]] = {}

    @classmethod
    def from_environment(cls, **options) -> "HTTPStore":
        return cls(None, None, **options)

    # -- connection --

    @staticmethod
    def _env(name: str) -> str:
        from ..utils import Environment, get_environment

        try:
            return getattr(get_environment(), name)
        except RuntimeError:
            return getattr(Environment, name)

    def _value(self, value, env_name: str) -> str:
        if value is None:
            return self._env(env_name) or ""
        return (value() if callable(value) else value) or ""

    @property
    def api_url(self) -> str:
        return self._value(self._api_url, "backend_api_url").rstrip("/")

    @property
    def token(self) -> str:
        return self._value(self._token, "backend_api_token")

    @property
    def client_id(self) -> str:
        return self._value(self._client_id, "backend_api_client_id")

    def _request(
        self,
        method: str,
        path: str,
        body=None,
        *,
        key=None,
        retry=True,
        raw: bytes | None = None,
        params: dict | None = None,
        headers: dict | None = None,
        response=False,
    ):
        """JSON answer of a request, or the response itself with response=True
        (also for redirects). Transient failures are retried until retry_for
        has passed, a 429 only if its Retry-After fits into that time; a 401
        once if the token was refreshed meanwhile."""
        url = self.api_url + path
        if params:
            query = {k: v for k, v in params.items() if v is not None}
            url += "?" + urlencode(query)
        data = raw
        if body is not None:
            data = orjson.dumps(body, default=json_default)
        if method in _MUTATING and not path.startswith("/v2/uploads/"):
            key = _idempotency_key(key)
        deadline = time.monotonic() + (self.retry_for if retry else 0.0)
        delay = 0.2
        renewed = False
        while True:
            token = self.token
            h = {"Authorization": _bearer(token)}
            if self.client_id:
                h["X-Client-Id"] = self.client_id
            if raw is not None:
                h["Content-Type"] = "application/octet-stream"
            elif data is not None:
                h["Content-Type"] = "application/json"
            if key is not None:
                h["Idempotency-Key"] = key
            h.update(headers or {})
            try:
                r = self.http.request(
                    method,
                    url,
                    body=data,
                    headers=h,
                    timeout=self.timeout,
                    retries=False,
                    redirect=False,
                )
            except urllib3.exceptions.HTTPError as exc:
                error: StoreError = TransientStoreError(str(exc))
            else:
                if r.status < 300 or (response and r.status in _REDIRECT):
                    if response:
                        return r
                    return orjson.loads(r.data) if r.data else {}
                error = error_from(r.status, _problem(r), r.headers)
                if r.status == 401:
                    if not renewed and self.token != token:
                        renewed = True  # refreshed meanwhile
                        continue
                    raise error
                if r.status not in RETRY_STATUS:
                    raise error
            left = deadline - time.monotonic()
            if isinstance(error, RateLimitedError):
                if error.retry_after > left:
                    raise error
                self._sleep(error.retry_after)
                continue
            if left <= 0:
                raise error
            self._sleep(min(delay, left))
            delay = min(delay * 2, self.backoff_max)

    # -- cases and state --

    def create_case(
        self, app_id: int, name: str, ops: list[Op] = ()
    ) -> CaseInfo:
        body = {
            "app_id": app_id,
            "name": name,
            "ops": [op.to_json() for op in ops],
        }
        if self.release_id is not None:
            body["release_id"] = self.release_id
        info = _case_info(self._request("POST", "/v2/cases", body))
        self._releases.setdefault(info.id, info.release_id)
        return info

    def case(self, case_id: int) -> CaseInfo:
        info = _case_info(self._request("GET", f"/v2/cases/{case_id}"))
        self._releases.setdefault(case_id, info.release_id)
        return info

    def state(self, case_id: int, revision: int | None = None) -> dict:
        data = self._request(
            "GET",
            f"/v2/cases/{case_id}/state",
            params={"revision": revision, "mark_seq": "true"},
        )
        if revision is None:
            self._releases.setdefault(case_id, data.get("release_id"))
        return _client_state(data)

    def changes(self, case_id: int, from_rev: int, to_rev: int) -> list[Op]:
        data = self._request(
            "GET",
            f"/v2/cases/{case_id}/changes",
            params={"from": from_rev, "to": to_rev},
        )
        return _ops(data["ops"])

    def _release(self, case_id: int) -> int | None:
        """The store's release, else the release of the head first seen"""
        if self.release_id is not None:
            return self.release_id
        if self._releases.get(case_id) is None:
            self.case(case_id)
        return self._releases.get(case_id)

    def commit(
        self,
        case_id: int,
        base: int,
        ops: list[Op],
        *,
        kind="autosave",
        name=None,
        upload_session=None,
        idempotency_key=None,
    ) -> CommitResult:
        body = {
            "base_revision": base,
            "release_id": self._release(case_id),
            "kind": kind,
            "name": name,
            "upload_session": self._renamed.get(upload_session, upload_session),
            "ops": [op.to_json() for op in ops],
        }
        data = self._request(
            "POST",
            f"/v2/cases/{case_id}/revisions",
            body,
            key=idempotency_key,
        )
        return CommitResult(
            data["revision"], data["head"], _ops(data.get("remote_ops", []))
        )

    def copy_case(
        self,
        case_id: int,
        *,
        revision: int | None = None,
        run_id: int | None = None,
        name: str | None = None,
    ) -> CaseInfo:
        body = {"revision": revision, "run": run_id, "name": name}
        info = _case_info(
            self._request("POST", f"/v2/cases/{case_id}/copy", body)
        )
        self._releases.setdefault(info.id, info.release_id)
        return info

    # -- blobs --

    def blobs_missing(
        self, case_id: int, blobs: list[BlobRef]
    ) -> MissingResult:
        body = {
            "case_id": case_id,
            "blobs": [
                {"hash": b.hash, "size": b.size, "enc": b.enc} for b in blobs
            ],
        }
        data = self._request("POST", "/v2/blobs/missing", body)
        self._sessions[data["upload_session"]] = case_id
        return MissingResult(list(data["missing"]), data["upload_session"])

    def upload(self, session: str, ref: BlobRef, data: BinaryIO) -> None:
        """Upload a blob reported missing in the session; an interrupted
        transfer resumes after asking again. If the session expired
        meanwhile, later commits use the new one."""
        current = self._renamed.get(session, session)
        case_id = self._sessions.get(current)
        if case_id is None:
            raise InvalidError(f"unknown upload session {session}")
        src = Source(data)
        if ref.size is not None and ref.size != src.size:
            raise InvalidError(f"content does not match {ref.hash}")
        new = self._upload_blob(case_id, ref, src, current, asked=True)
        if new != current:
            self._sessions[new] = case_id
            self._renamed[session] = new

    def _presigned_get(self, url: str, headers: dict):
        """GET of a presigned URL, without the token"""
        try:
            return self.http.request(
                "GET",
                url,
                headers=headers,
                timeout=self.timeout,
                retries=False,
                redirect=False,
            )
        except urllib3.exceptions.HTTPError as exc:
            raise TransientStoreError(str(exc)) from exc

    def read_blob(
        self,
        case_id: int,
        ref: BlobRef,
        byte_range: tuple[int, int] | None = None,
    ) -> bytes:
        """Bytes of a blob (half-open byte range); a redirect to object
        storage is followed without the token"""
        headers = {}
        if byte_range is not None:
            start, stop = byte_range
            if stop <= start:
                return b""
            headers["Range"] = f"bytes={start}-{stop - 1}"
        r = None
        cached = self._presigned.get((case_id, ref.hash))
        if cached is not None and cached[1] > time.monotonic():
            r = self._presigned_get(cached[0], headers)
            if r.status >= 300:
                del self._presigned[(case_id, ref.hash)]
                r = None
        if r is None:
            r = self._request(
                "GET",
                f"/v2/cases/{case_id}/blobs/{ref.hash}",
                headers=headers,
                response=True,
            )
            if r.status in _REDIRECT:
                url = r.headers["Location"]
                age = _max_age(r.headers.get("Cache-Control", ""))
                if age:
                    self._presigned[(case_id, ref.hash)] = (
                        url,
                        time.monotonic() + age,
                    )
                r = self._presigned_get(url, headers)
                if r.status >= 300:
                    raise error_from(r.status, _problem(r), r.headers)
        data = r.data
        if byte_range is not None and r.status == 200:
            data = data[byte_range[0] : byte_range[1]]
        return data

    def prefetch(self, case_id: int, refs: list[BlobRef]) -> None:
        """Presigned download URLs for many blobs with one request; later
        reads go to object storage directly (and hit the browser cache)"""
        hashes = [
            r.hash for r in refs if (case_id, r.hash) not in self._presigned
        ]
        if not hashes:
            return
        data = self._request(
            "POST", f"/v2/cases/{case_id}/blobs/presign", {"hashes": hashes}
        )
        if data.get("expires_at") is None:
            return  # file system: the URLs need the token
        end = time.monotonic() + max(
            0.0, _seconds_until(data["expires_at"]) - 5
        )
        for h, url in data["urls"].items():
            self._presigned[(case_id, h)] = (url, end)

    # -- jobs and runs --

    def _job(self, data: dict) -> JobInfo:
        return _parse(JobInfo, data)

    def submit(self, case_id: int, request: JobRequest) -> JobInfo:
        """The job runs with the store's release (the code of this client)"""
        body = dataclasses.asdict(request)
        if body.get("release_id") is None:
            body["release_id"] = self.release_id
        data = self._request("POST", f"/v2/cases/{case_id}/jobs", body)
        job = self._job(data["job"])
        if data.get("reused_run") is not None:
            job.reused_run = data["reused_run"]
        if data.get("run"):
            job.extra.setdefault("run", data["run"])
        return job

    def job(self, job_id: int) -> JobInfo:
        return self._job(self._request("GET", f"/v2/jobs/{job_id}"))

    def cancel(self, job_id: int) -> None:
        self._request("POST", f"/v2/jobs/{job_id}/cancel")

    def job_events(self, job_id: int, after: int = 0) -> list[dict]:
        data = self._request(
            "GET", f"/v2/jobs/{job_id}/events", params={"after": after}
        )
        return data["events"]

    def runs(self, case_id: int, function=None) -> list[RunInfo]:
        data = self._request(
            "GET", f"/v2/cases/{case_id}/runs", params={"function": function}
        )
        return [_parse(RunInfo, r) for r in data["runs"]]

    def run_changes(
        self,
        run_id: int,
        from_revision: int | None = None,
        to_revision: int | None = None,
    ) -> list[Op]:
        data = self._request(
            "GET",
            f"/v2/runs/{run_id}/changes",
            params={"from": from_revision, "to": to_revision},
        )
        return _ops(data["ops"])

    def keep(self, run_id: int) -> None:
        self._request("POST", f"/v2/runs/{run_id}/keep", {"kept": True})

    # -- events --

    def subscribe(
        self,
        case_ids: list[int],
        last_seq: int,
        callback: Callable[[Event], None],
    ) -> Callable[[], None]:
        mode = self.events
        if mode == "auto":
            if _is_pyodide():
                mode = "deliver"
            else:
                mode = "websocket" if _have_websockets() else "poll"
        if mode == "deliver":
            sub = _Delivery(case_ids, last_seq, callback)
            _deliveries.append(sub)
            _subscriptions_changed()
            return sub.close
        if mode == "websocket":
            sub = _Socket(self, case_ids, last_seq, callback)
        elif mode == "poll":
            sub = _Poller(self, case_ids, callback, self.poll_interval)
        else:
            raise ValueError(f"unknown event mode {mode!r}")
        sub.start()
        return sub.close


def _problem(r) -> dict:
    try:
        data = orjson.loads(r.data) if r.data else {}
    except orjson.JSONDecodeError:
        data = {}
    return data if isinstance(data, dict) else {}


def _max_age(cache_control: str) -> int:
    for part in cache_control.split(","):
        name, _, value = part.strip().partition("=")
        if name == "max-age" and value.isdigit():
            return int(value)
    return 0


def _seconds_until(iso: str) -> float:
    from datetime import datetime, timezone

    end = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return (end - datetime.now(timezone.utc)).total_seconds()


def _is_pyodide() -> bool:
    from ..utils import is_pyodide

    return is_pyodide()


def _have_websockets() -> bool:
    try:
        import websockets.sync.client  # noqa: F401
    except ImportError:
        return False
    return True


def _call(callback, event: Event):
    try:
        callback(event)
    except Exception as e:  # a failing subscriber must not affect others
        logger.exception("Error in event callback: %r", e)


# -- events forwarded by the browser (pyodide) --

_deliveries: list["_Delivery"] = []
on_subscriptions: list[Callable[[list[int]], None]] = []
"""Called with the subscribed case ids whenever they change, e.g. by the
frontend to subscribe them on its websocket"""


class _Delivery:
    def __init__(self, case_ids, last_seq, callback):
        self.case_ids = set(case_ids)
        self.last = last_seq or 0
        self.callback = callback
        self.active = True

    def close(self):
        self.active = False
        if self in _deliveries:
            _deliveries.remove(self)
            _subscriptions_changed()

    def wants(self, event: dict) -> bool:
        topic = event.get("topic")
        if topic:
            kind, _, ident = topic.partition(":")
            return kind != "case" or int(ident) in self.case_ids
        if event.get("type") in _USER_EVENTS:
            return True
        # events of a case topic name their case
        case_id = (event.get("payload") or {}).get("case_id")
        return case_id is None or case_id in self.case_ids


def subscribed_cases() -> list[int]:
    return sorted(set().union(*(d.case_ids for d in _deliveries)))


def subscribed_from() -> int | None:
    """Oldest event position a subscription waits for (the replay start of
    the frontend's websocket), None without subscriptions"""
    return min((d.last for d in _deliveries), default=None)


def _subscriptions_changed():
    cases = subscribed_cases()
    for callback in list(on_subscriptions):
        try:
            callback(cases)
        except Exception as e:
            logger.exception("Error in subscription callback: %r", e)


def deliver_events(events) -> None:
    """Events of the backend's websocket (the JSON objects as sent by the
    server, or a JSON string of their list), forwarded by the frontend: each
    subscription gets the events of its cases and of the user in seq order,
    once. A resync message goes to every subscription.

    Events wait while an app is created (held_events) and, in the browser,
    until an entry point that can block calls the callbacks: these may read
    blobs, which needs stack switching (JSPI)."""
    if isinstance(events, (str, bytes)):
        events = orjson.loads(events)
    elif hasattr(events, "to_py"):
        events = events.to_py()
    if isinstance(events, dict):
        events = [events]
    with _queue_lock:
        _queue.extend(e for e in events if isinstance(e, dict))
    _drain()


_queue: list[dict] = []
_queue_lock = threading.Lock()
_holds = 0
_draining = False
_deferred = False


def _can_block() -> bool:
    if not _is_pyodide():
        return True
    try:
        from pyodide.ffi import can_run_sync
    except ImportError:
        return True
    return can_run_sync()


def _defer(fn) -> None:
    """fn from an asyncio task: a promising entry point in pyodide"""
    import asyncio

    async def run():
        fn()

    asyncio.get_event_loop().create_task(run())


def _deferred_drain():
    global _deferred
    with _queue_lock:
        _deferred = False
    _drain()


def _drain() -> None:
    global _draining, _deferred
    with _queue_lock:
        if _draining or _holds or not _queue:
            return
        if not _can_block():
            if not _deferred:
                _deferred = True
                _defer(_deferred_drain)
            return
        _draining = True
    try:
        while True:
            with _queue_lock:
                batch = _queue[:]
                _queue.clear()
                if not batch:
                    _draining = False
                    return
            _deliver(batch)
    except BaseException:
        with _queue_lock:
            _draining = False
        raise


@contextlib.contextmanager
def held_events():
    """Events delivered meanwhile wait until the block is left"""
    global _holds
    with _queue_lock:
        _holds += 1
    try:
        yield
    finally:
        with _queue_lock:
            _holds -= 1
        _drain()


def _deliver(events: list[dict]) -> None:
    events.sort(key=lambda e: -1 if e.get("seq") is None else e["seq"])
    for event in events:
        kind = event.get("type")
        seq = event.get("seq")
        for sub in list(_deliveries):
            if not sub.active:
                continue
            if kind == "resync":
                sub.last = 0
                _call(sub.callback, Event(0, "resync", {}))
            elif seq is not None and seq > sub.last and sub.wants(event):
                sub.last = seq
                _call(
                    sub.callback, Event(seq, kind, event.get("payload") or {})
                )


# -- events outside pyodide --


class _Socket:
    """Own websocket of a subscription; reconnects with the last seq seen.
    start() returns after the replay, or raises if the server refused the
    hello or a case is not readable."""

    def __init__(self, store: HTTPStore, case_ids, last_seq, callback):
        self.store = store
        self.case_ids = set(case_ids)
        self.last = last_seq
        self.callback = callback
        self.closed = False
        self.error: Exception | None = None
        self.ready = threading.Event()
        self.ws = None
        self.thread = threading.Thread(
            target=self._run, daemon=True, name="ngapp-events"
        )

    def start(self, timeout: float = 30.0):
        self.thread.start()
        if not self.ready.wait(timeout):
            logger.warning("Event stream not ready after %s s", timeout)
        if self.error is not None:
            self.close()
            raise self.error

    def close(self):
        self.closed = True
        ws = self.ws
        if ws is not None:
            try:
                ws.close()
            except Exception:
                pass
        if threading.current_thread() is not self.thread:
            self.thread.join(5)

    def _url(self) -> str:
        url = self.store.api_url
        if url.startswith("http"):
            url = "ws" + url[4:]
        return url + "/v2/ws"

    def _fail(self, error: Exception):
        """Errors before the first ready end the subscription"""
        if not self.ready.is_set():
            self.error = error
            self.closed = True
            self.ready.set()
        else:
            logger.info("Event stream: %r", error)

    def _run(self):
        from websockets.exceptions import ConnectionClosed, WebSocketException
        from websockets.sync.client import connect

        delay = 0.5
        while not self.closed:
            try:
                with connect(
                    self._url(), open_timeout=10, close_timeout=1, max_size=None
                ) as ws:
                    self.ws = ws
                    hello = {
                        "type": "hello",
                        "token": self.store.token,
                        "last_seq": self.last,
                        "cases": sorted(self.case_ids),
                    }
                    ws.send(orjson.dumps(hello).decode())
                    while not self.closed:
                        try:
                            raw = ws.recv(timeout=1.0)
                        except TimeoutError:
                            continue
                        self._message(orjson.loads(raw))
                        delay = 0.5
            except ConnectionClosed as exc:
                code = exc.rcvd.code if exc.rcvd is not None else None
                if code == 1008:
                    self._fail(
                        UnauthorizedError("event stream refused the hello")
                    )
            except (OSError, TimeoutError, WebSocketException) as exc:
                self._fail(TransientStoreError(f"event stream: {exc}"))
            finally:
                self.ws = None
            end = time.monotonic() + delay
            while not self.closed and time.monotonic() < end:
                time.sleep(0.1)
            delay = min(delay * 2, 30.0)

    def _message(self, msg: dict):
        kind = msg.get("type")
        seq = msg.get("seq")
        if kind == "ready":
            if not self.ready.is_set():
                missing = self.case_ids - set(msg.get("cases") or [])
                if missing:
                    self._fail(NotFoundError(f"cases {sorted(missing)}"))
                    return
            self.last = max(self.last or 0, seq or 0)
            self.ready.set()
        elif kind == "resync":
            self.last = 0
            if not self.closed:
                _call(self.callback, Event(0, "resync", {}))
        elif kind == "error":
            self._fail(error_from(400, msg))
        elif seq is not None and seq > (self.last or 0) and not self.closed:
            self.last = seq
            _call(self.callback, Event(seq, kind, msg.get("payload") or {}))


class _Poller:
    """Fallback without websocket: polls the head of the cases and reports
    changes as case.head events (without seq). The first poll reports the
    current heads, since a change between a client's state read and the
    subscription has no event to replay."""

    def __init__(self, store: HTTPStore, case_ids, callback, interval):
        self.store = store
        self.callback = callback
        self.interval = interval
        self.heads = {c: None for c in case_ids}
        self.stop = threading.Event()
        self.thread = threading.Thread(
            target=self._run, daemon=True, name="ngapp-poll"
        )

    def start(self):
        for case_id in self.heads:
            self.store.case(case_id)  # readable
        self.thread.start()

    def close(self):
        self.stop.set()

    def _run(self):
        while not self.stop.wait(self.interval):
            for case_id, head in list(self.heads.items()):
                try:
                    info = self.store.case(case_id)
                except CaseDeletedError:
                    del self.heads[case_id]
                    event = Event(0, "case.deleted", {"case_id": case_id})
                    _call(self.callback, event)
                    continue
                except StoreError:
                    continue
                if info.head != head and not self.stop.is_set():
                    self.heads[case_id] = info.head
                    payload = {"case_id": case_id, "revision": info.head}
                    _call(self.callback, Event(0, "case.head", payload))
