"""Client of a job process for the job side of the runner protocol

The runner starts the job process with the environment

    NGAPP_JOB_API          api base url, e.g. https://host/api
    NGAPP_JOB_ID           job id
    NGAPP_JOB_ATTEMPT      attempt number
    NGAPP_JOB_TOKEN_FILE   file with the current job token, renewed by the runner's heartbeats
    NGAPP_JOB_TOKEN        initial job token (used if the file is missing)
    NGAPP_JOB_CACHE_DIR    blob cache of the runner (optional): <dir>/sha256/<hex[0:2]>/<hex>

Requests are retried with backoff while the backend is unreachable or answers 5xx, after
the time a 429 answer names, and after a 401 once the runner has renewed the token. A
request that fails on a pooled connection the server closed meanwhile is sent
again at once (uploads ask again instead). Progress is retried for a few seconds only; the last progress is
sent again before the final commit if it was not delivered. Commits
carry an idempotency key derived from job, attempt and seq, so a retried commit returns the
revision of the first one. When the backend says that the attempt ended (409 stale_attempt)
or the job was cancelled (409 cancelled), the client raises JobEndedError (StaleAttemptError,
JobCancelledError) and refuses every later request, so that the job process ends.

upload() stores data as a blob of the job's case: it asks the backend which
blobs are missing, transfers them (streamed through the backend, or presigned single or
multipart uploads to object storage) and completes them. After a lost connection it asks
again before it resumes, so a blob completed meanwhile is not sent again. The upload
session, owned by the job attempt, goes with the following commits.

read_blob() reads a blob of the job's case. With a blob cache, complete blobs are read from it
and downloads are added to it (download to <dir>/tmp, verify the hash, rename into place,
existing files are kept); cached files are never modified.
"""

import base64
import hashlib
import json
import os
import re
import tempfile
import time
import uuid
from pathlib import Path

import urllib3

from .store.transfer import RETRY_STATUS as _RETRY_STATUS
from .store.transfer import Source as _Data
from .store.transfer import Uploads
from .store.transfer import error_from as _error
from .store.transfer import json_default as _json_default
from .store.types import (
    BlobRef,
    JobEndedError,
    RateLimitedError,
    StoreError,
    TransientStoreError,
)

_REDIRECT = (301, 302, 303, 307, 308)

_NAMESPACE = uuid.UUID("6c1d3f0e-9a0b-4e4f-8a77-0c5b3f1f2a10")


class JobClient(Uploads):
    """get_input, commit(ops, seq, final), upload and progress for one job attempt"""

    def __init__(
        self,
        api_url: str,
        job_id: int,
        attempt: int,
        token: str | None = None,
        token_file: str | os.PathLike | None = None,
        *,
        case_id: int | None = None,
        retry_for: float = 24 * 3600,
        backoff_max: float = 10,
        timeout: float = 120,
        token_wait: float = 60,
        cache_dir: str | os.PathLike | None = None,
        progress_retry_for: float = 5,
    ):
        self.api_url = api_url.rstrip("/")
        self.job_id = int(job_id)
        self.attempt = int(attempt)
        self._token = token
        self.token_file = Path(token_file) if token_file else None
        self.retry_for = retry_for
        self.backoff_max = backoff_max
        self.timeout = timeout
        self.token_wait = token_wait
        self.progress_retry_for = progress_retry_for
        self._undelivered_progress: dict | None = None
        self.ended: JobEndedError | None = None
        self.seq = 0
        self.upload_session: str | None = None
        self._case_id = case_id
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.http = urllib3.PoolManager()

    @classmethod
    def from_env(cls, env=None, **kwargs) -> "JobClient":
        env = os.environ if env is None else env
        return cls(
            env["NGAPP_JOB_API"],
            int(env["NGAPP_JOB_ID"]),
            int(env["NGAPP_JOB_ATTEMPT"]),
            token=env.get("NGAPP_JOB_TOKEN"),
            token_file=env.get("NGAPP_JOB_TOKEN_FILE"),
            cache_dir=env.get("NGAPP_JOB_CACHE_DIR") or None,
            **kwargs,
        )

    @property
    def token(self) -> str:
        if self.token_file is not None:
            try:
                text = self.token_file.read_text().strip()
                if text:
                    return text
            except OSError:
                pass
        return self._token or ""

    @property
    def case_id(self) -> int:
        """The job's case, from the claims of the job token unless given"""
        if self._case_id is None:
            claims = self.token.split(".")[1]
            claims += "=" * (-len(claims) % 4)
            self._case_id = int(
                json.loads(base64.urlsafe_b64decode(claims))["case"]
            )
        return self._case_id

    def _renewed(self, sent: str, wait: float) -> bool:
        """The runner renewed the sent token; waits at most wait seconds"""
        if self.token_file is None:
            return False
        end = time.monotonic() + wait
        while self.token == sent:
            if time.monotonic() >= end:
                return False
            time.sleep(0.2)
        return True

    def _ended(self, error: JobEndedError) -> JobEndedError:
        """Remember the end of the attempt; later requests raise at once"""
        if self.ended is None:
            job = f"job {self.job_id} attempt {self.attempt}"
            message = f"{job} ended ({error.code}): {error}"
            self.ended = type(error)(message, **error.data)
        return type(self.ended)(str(self.ended), **self.ended.data)

    def _request(
        self,
        method: str,
        path: str,
        body=None,
        *,
        key: str | None = None,
        retry: bool | float = True,
        raw: bytes | None = None,
        headers: dict | None = None,
        binary: bool = False,
    ):
        """JSON answer of a request; with binary, the bytes of the answer,
        following a redirect without the token. retry: True retries for
        retry_for seconds, a number for that many seconds"""
        if self.ended is not None:
            raise self._ended(self.ended)
        if isinstance(retry, bool):
            retry = self.retry_for if retry else 0
        deadline = time.monotonic() + retry
        delay = 0.2
        stale = False
        data = raw
        if body is not None:
            data = json.dumps(body, default=_json_default).encode()
        while True:
            token = self.token
            send = {"Authorization": f"Bearer {token}", **(headers or {})}
            if raw is not None:
                send["Content-Type"] = "application/octet-stream"
            elif data is not None:
                send["Content-Type"] = "application/json"
            if key is not None:
                send["Idempotency-Key"] = key
            try:
                r = self.http.request(
                    method,
                    self.api_url + path,
                    body=data,
                    headers=send,
                    timeout=self.timeout,
                    retries=False,
                    redirect=False,
                )
                if binary and r.status in _REDIRECT:
                    r = self.http.request(
                        "GET",
                        r.headers["Location"],
                        headers=headers or {},
                        timeout=self.timeout,
                        retries=False,
                    )
                    if r.status >= 300:
                        raise urllib3.exceptions.HTTPError(
                            f"object storage answered {r.status}"
                        )
            except urllib3.exceptions.HTTPError as exc:
                stale_conn = isinstance(exc, urllib3.exceptions.ProtocolError)
                if stale_conn and raw is None and not stale:
                    # a pooled connection closed by the server's keep-alive timeout;
                    # an interrupted upload asks again instead
                    stale = True
                    continue
                error: StoreError = TransientStoreError(str(exc))
            else:
                if binary and r.status < 300:
                    return r.data
                try:
                    payload = json.loads(r.data) if r.data else {}
                except ValueError:
                    payload = {}
                if r.status < 300:
                    return payload
                error = _error(
                    r.status,
                    payload if isinstance(payload, dict) else {},
                    r.headers,
                )
                if isinstance(error, JobEndedError):
                    raise self._ended(error)
                if r.status == 401:
                    # expired token: retried only with a renewed one
                    wait = self.token_wait if retry else 0
                    if (
                        self._renewed(token, wait)
                        and time.monotonic() < deadline
                    ):
                        continue
                    raise error
                if r.status not in _RETRY_STATUS:
                    raise error
            if time.monotonic() >= deadline:
                raise error
            if isinstance(error, RateLimitedError):
                left = max(0.0, deadline - time.monotonic())
                time.sleep(min(error.retry_after, left))
                continue
            time.sleep(delay)
            delay = min(delay * 2, self.backoff_max)

    def get_input(self) -> dict:
        """Materialised input state, arguments, release; with restart "checkpoint" also the
        operations of the previous attempts (key "checkpoint")"""
        data = self._request("GET", f"/v2/jobs/{self.job_id}/input")
        self._case_id = data.get("case_id", self._case_id)
        return data

    def commit(
        self,
        ops: list,
        seq: int | None = None,
        final: bool = False,
        upload_session: str | None = None,
    ) -> dict:
        """Checkpoint (final=False) or final commit; seq defaults to the next number, the
        upload session to the one of upload()"""
        seq = self.seq + 1 if seq is None else seq
        if final and self._undelivered_progress is not None:
            try:
                self._event(self._undelivered_progress, retry=True)
            except JobEndedError:
                raise
            except StoreError:
                pass
            self._undelivered_progress = None
        body = {
            "seq": seq,
            "final": final,
            "ops": list(ops),
            "upload_session": upload_session or self.upload_session,
        }
        key = str(uuid.uuid5(_NAMESPACE, f"{self.job_id}:{self.attempt}:{seq}"))
        result = self._request(
            "POST",
            f"/v2/jobs/{self.job_id}/attempts/{self.attempt}/commits",
            body,
            key=key,
        )
        self.seq = max(self.seq, seq)
        return result

    def blobs_missing(self, refs: list[BlobRef]) -> dict:
        """Which of the blobs the job's case lacks; pins the present ones in
        the attempt's upload session"""
        body = {
            "case_id": self.case_id,
            "blobs": [{"hash": r.hash, "size": r.size} for r in refs],
            "upload_session": self.upload_session,
        }
        answer = self._request("POST", "/v2/blobs/missing", body)
        self.upload_session = answer["upload_session"]
        return answer

    def _cache_path(self, ref: BlobRef) -> Path | None:
        hex_ = ref.hash.removeprefix("sha256:")
        if self.cache_dir is None or not re.fullmatch("[0-9a-f]{64}", hex_):
            return None
        return self.cache_dir / "sha256" / hex_[:2] / hex_

    def _cache_put(self, path: Path, data: bytes):
        """Add a verified download; a read-only cache is left alone"""
        tmp = None
        try:
            tmp_dir = self.cache_dir / "tmp"
            tmp_dir.mkdir(parents=True, exist_ok=True)
            path.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=tmp_dir)
            with os.fdopen(fd, "wb") as f:
                f.write(data)
            if not path.exists():
                os.rename(tmp, path)
                tmp = None
        except OSError:
            pass
        if tmp is not None:
            try:
                os.unlink(tmp)
            except OSError:
                pass

    def read_blob(
        self, ref: BlobRef, byte_range: tuple[int, int] | None = None
    ) -> bytes:
        """Bytes of a blob of the job's case (byte_range half-open)"""
        path = self._cache_path(ref)
        if path is not None:
            try:
                with open(path, "rb") as f:
                    if byte_range is not None:
                        f.seek(byte_range[0])
                    data = f.read(
                        -1 if byte_range is None else byte_range[1] - byte_range[0]
                    )
                    try:
                        os.utime(path, (time.time(), os.fstat(f.fileno()).st_mtime))
                    except OSError:
                        pass
                return data
            except OSError:
                pass
        headers = {}
        if byte_range is not None:
            headers["Range"] = f"bytes={byte_range[0]}-{byte_range[1] - 1}"
        data = self._request(
            "GET",
            f"/v2/cases/{self.case_id}/blobs/{ref.hash}",
            headers=headers,
            binary=True,
        )
        if byte_range is None:
            if "sha256:" + hashlib.sha256(data).hexdigest() != ref.hash:
                raise TransientStoreError(f"download of {ref.hash} is corrupt")
            if path is not None:
                self._cache_put(path, data)
        elif ref.size is not None and len(data) == ref.size:
            data = data[byte_range[0] : byte_range[1]]
        return data

    def upload(self, data, enc: str = "bytes") -> BlobRef:
        """Store data (bytes or the path of a file) as a blob of the job's
        case, unless the case or the upload session holds it already; returns
        the reference for commits. A transfer interrupted by a lost connection
        resumes after asking again, so a blob completed meanwhile is skipped."""
        src = _Data(data)
        ref = BlobRef(src.hash(), src.size, enc)
        self.upload_session = self._upload_blob(
            self.case_id, ref, src, self.upload_session
        )
        return ref

    def _event(self, body: dict, retry: bool | float = False):
        try:
            return self._request(
                "POST",
                f"/v2/jobs/{self.job_id}/attempts/{self.attempt}/events",
                body,
                retry=retry,
            )
        except JobEndedError:
            raise
        except StoreError as exc:
            if exc.code in (
                "conflict",
                "case_deleted",
                "not_found",
                "forbidden",
            ):
                raise
            return None

    def progress(self, fraction: float | None = None, text: str | None = None):
        """Progress shown by clients, not stored in the case; dropped while
        the backend is down, except the last one, which is sent again before
        the final commit"""
        body = {"kind": "progress", "fraction": fraction, "text": text}
        retry = min(self.progress_retry_for, self.retry_for)
        answer = self._event(body, retry=retry)
        self._undelivered_progress = body if answer is None else None
        return answer

    def message(self, text: str, level: str = "info"):
        return self._event({"kind": "message", "text": text, "level": level})
