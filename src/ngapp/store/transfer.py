"""HTTP transport shared by the case store client and the job client

Error answers (problem+json with a code) map to the exceptions of
ngapp.store. Blob uploads: ask which blobs are missing, start the
upload, transfer it (streamed through the backend, or presigned single or
multipart uploads to object storage) and complete it. After a lost connection
the upload asks again before it resumes, so a blob completed meanwhile is not
sent again.
"""

import base64
import hashlib
import os
import time
from pathlib import Path

import urllib3

from .types import (
    ERRORS,
    BlobRef,
    Conflict,
    ConflictError,
    InvalidError,
    MissingBlobsError,
    NotFoundError,
    Op,
    RateLimitedError,
    StoreError,
    TransientStoreError,
)

RETRY_STATUS = (429, 500, 502, 503, 504)


def retry_after(data: dict, headers) -> float:
    for value in (data.get("retry_after"), headers.get("Retry-After")):
        try:
            return max(0.0, float(value))
        except (TypeError, ValueError):
            pass
    return 1.0


def _conflict(data) -> Conflict | dict:
    if not isinstance(data, dict) or "path" not in data:
        return data
    return Conflict(
        tuple(data["path"]),
        data.get("base"),
        data.get("head"),
        data.get("mine"),
    )


def error_from(status: int, data: dict, headers=None) -> StoreError:
    """Exception of an error answer"""
    code = data.get("code", "error")
    cls = ERRORS.get(code, StoreError)
    if status >= 500 and cls is StoreError:
        cls = TransientStoreError
    err = cls.__new__(cls)
    StoreError.__init__(err, data.get("detail", "") or f"HTTP {status}", **data)
    if isinstance(err, MissingBlobsError):
        err.hashes = data.get("hashes", [])
    if isinstance(err, ConflictError):
        err.conflicts = [_conflict(c) for c in data.get("conflicts", [])]
    if isinstance(err, RateLimitedError):
        err.retry_after = retry_after(data, headers or {})
    return err


def json_default(value):
    if isinstance(value, (Op, BlobRef)):
        return value.to_json()
    raise TypeError(f"{type(value).__name__} is not JSON serializable")


def checksum(data: bytes) -> str:
    return base64.b64encode(hashlib.sha256(data).digest()).decode()


class Source:
    """Bytes, a binary file object or the path of a file to upload"""

    CHUNK = 8 * 1024 * 1024

    def __init__(self, data):
        self.path = self.view = self.file = None
        if isinstance(data, (str, os.PathLike)):
            self.path = Path(data)
            self.size = self.path.stat().st_size
        elif hasattr(data, "read"):
            if getattr(data, "seekable", lambda: False)():
                self.file, self.start = data, data.tell()
                self.size = data.seek(0, os.SEEK_END) - self.start
                data.seek(self.start)
            else:
                self.view = memoryview(data.read()).cast("B")
                self.size = len(self.view)
        else:
            self.view = memoryview(data).cast("B")
            self.size = len(self.view)

    def read(self, offset: int, size: int) -> bytes:
        if self.view is not None:
            return bytes(self.view[offset : offset + size])
        if self.file is not None:
            self.file.seek(self.start + offset)
            return self.file.read(size)
        with open(self.path, "rb") as f:
            f.seek(offset)
            return f.read(size)

    def hash(self) -> str:
        h = hashlib.sha256()
        for offset in range(0, self.size, self.CHUNK):
            h.update(self.read(offset, self.CHUNK))
        return "sha256:" + h.hexdigest()


class _Expired(Exception):
    """Object storage refused a presigned URL; start again with new ones"""


class Uploads:
    """Blob uploads on top of _request(method, path, body, *, key, retry, raw);
    needs the attributes http, timeout, retry_for and backoff_max"""

    def _sleep(self, seconds: float):
        time.sleep(seconds)

    def _upload_blob(
        self,
        case_id: int,
        ref: BlobRef,
        src: Source,
        session: str | None,
        asked: bool = False,
    ) -> str:
        """Upload one blob unless the case or the session holds it already;
        returns the upload session that holds it. asked: the session reported
        it missing just now."""
        deadline = time.monotonic() + self.retry_for
        delay = 0.2
        restarts = 0
        while restarts < 3:
            if not asked:
                body = {
                    "case_id": case_id,
                    "blobs": [{"hash": ref.hash, "size": ref.size}],
                    "upload_session": session,
                }
                answer = self._request("POST", "/v2/blobs/missing", body)
                session = answer["upload_session"]
                if ref.hash not in answer["missing"]:
                    return session
            asked = False
            try:
                if self._transfer(session, ref, src):
                    return session
            except NotFoundError:
                session = None  # the session ended, start a new one
            except (TransientStoreError, RateLimitedError) as exc:
                if time.monotonic() >= deadline:
                    raise
                if isinstance(exc, RateLimitedError):
                    self._sleep(exc.retry_after)
                else:
                    self._sleep(delay)
                    delay = min(delay * 2, self.backoff_max)
                continue
            restarts += 1
        raise StoreError(f"upload of {ref.hash} did not complete")

    def _transfer(self, sid: str, ref: BlobRef, src: Source) -> bool:
        """Start, send and complete one upload; False if it has to start
        again. Transient errors are not retried here but raised."""
        path = f"/v2/uploads/{sid}/blobs"
        start = {"hash": ref.hash, "size": ref.size, "enc": ref.enc}
        answer = self._request("POST", path, start, retry=False)
        parts = None
        if not answer["uploaded"]:
            method = answer["method"]
            try:
                if method == "stream":
                    self._stream(f"{path}/{ref.hash}", src, answer)
                elif method == "s3-single":
                    self._send_parts(src, answer)
                else:
                    size = answer["part_size"]
                    sums = [
                        checksum(src.read(offset, size))
                        for offset in range(0, src.size, size)
                    ]
                    answer = self._request(
                        "POST",
                        path,
                        {**start, "part_size": size, "part_checksums": sums},
                        retry=False,
                    )
                    parts = answer.get("done_parts", []) + self._send_parts(
                        src, answer
                    )
                    parts.sort(key=lambda p: p["number"])
            except _Expired:
                return False
        try:
            self._request(
                "POST",
                f"{path}/{ref.hash}/complete",
                {"parts": parts} if parts else {},
                retry=False,
            )
        except StoreError as exc:
            if exc.code == "conflict":
                return False  # incomplete or a concurrent upload, resume
            raise
        return True

    def _stream(self, path: str, src: Source, answer: dict):
        offset, size = answer["offset"], answer["part_size"]
        if src.size == 0:
            self._request("PUT", f"{path}?offset=0", raw=b"", retry=False)
        while offset < src.size:
            chunk = src.read(offset, size)
            try:
                answer = self._request(
                    "PUT", f"{path}?offset={offset}", raw=chunk, retry=False
                )
            except StoreError as exc:
                if exc.code != "conflict" or "offset" not in exc.data:
                    raise
                answer = exc.data  # gap: continue at the confirmed offset
            offset = answer["offset"]

    def _send_parts(self, src: Source, answer: dict) -> list[dict]:
        """PUT the parts to their presigned URLs, without the API token"""
        size = answer["part_size"]
        done = []
        for part in answer["parts"]:
            n = part["number"]
            chunk = src.read((n - 1) * size, size)
            etag = self._put_presigned(part["url"], part["headers"], chunk)
            done.append(
                {
                    "number": n,
                    "etag": etag,
                    "checksum": part["headers"].get("x-amz-checksum-sha256"),
                }
            )
        return done

    def _put_presigned(self, url: str, headers: dict, data: bytes) -> str:
        try:
            r = self.http.request(
                "PUT",
                url,
                body=data,
                headers=headers,
                timeout=self.timeout,
                retries=False,
            )
        except urllib3.exceptions.HTTPError as exc:
            raise TransientStoreError(str(exc)) from exc
        if r.status < 300:
            return r.headers.get("ETag", "")
        message = f"object storage answered {r.status}"
        if r.status >= 500:
            raise TransientStoreError(message)
        if r.status == 403:
            raise _Expired(message)
        if r.status == 400:
            raise InvalidError(f"{message}: content does not match")
        raise StoreError(message)
