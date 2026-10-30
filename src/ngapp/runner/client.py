"""HTTP client for the backend's runner API (/api/v2/runner)"""

import hashlib
import uuid
from pathlib import Path

import httpx

_NAMESPACE = uuid.UUID("0f5e3a8c-2d41-4c63-9b1e-7a6d5c4b3a21")


class JobLost(Exception):
    """The backend no longer considers this attempt ours (requeued, ended or unknown)"""


class BackendUnavailable(Exception):
    """Backend not reachable or answering 5xx; the request may be retried"""


class Unauthorized(Exception):
    """The backend refuses the runner: unknown token (401) or no access (403)"""


def _detail(r: httpx.Response) -> str:
    try:
        return r.json().get("detail") or r.text[:200]
    except ValueError:
        return r.text[:200]


def _problem(r: httpx.Response) -> str:
    """Status, code and detail of an error answer (409 stale_attempt: ...)"""
    try:
        code = r.json().get("code") or ""
    except ValueError:
        code = ""
    return " ".join(str(p) for p in (r.status_code, code) if p) + f": {_detail(r)}"


def api_base(host: str) -> str:
    base = host if "://" in host else f"https://{host}"
    base = base.rstrip("/")
    if not base.endswith("/api"):
        base += "/api"
    return base


class BackendClient:
    def __init__(self, host: str, token: str, timeout: float = 60):
        self.base = api_base(host)
        self.token = token
        self.client = httpx.Client(
            base_url=self.base,
            headers={"X-Runner-Token": token},
            timeout=httpx.Timeout(timeout),
            follow_redirects=True,
        )

    def _post(self, url: str, body: dict, timeout: float | None = None, headers=None):
        try:
            r = self.client.post(
                "/v2/runner" + url,
                json=body,
                timeout=httpx.USE_CLIENT_DEFAULT if timeout is None else timeout,
                headers=headers,
            )
        except httpx.TransportError as e:
            raise BackendUnavailable(str(e)) from e
        if r.status_code in (404, 409, 410) and url.startswith("/jobs/"):
            raise JobLost(_problem(r))
        if r.status_code in (401, 403):
            raise Unauthorized(f"HTTP {r.status_code}: {_detail(r)}")
        if r.status_code >= 500 or r.status_code == 429:
            raise BackendUnavailable(f"HTTP {r.status_code}: {r.text[:200]}")
        r.raise_for_status()
        return r

    def request_job(self, state: dict, wait: int) -> dict | None:
        r = self._post("/request", {**state, "wait": wait}, timeout=wait + 30)
        if r.status_code == 204:
            return None
        return r.json()

    def heartbeat(
        self, state: dict, running_jobs: list[int], stopping=False, timeout: float | None = None
    ) -> dict:
        """stopping=True announces the shutdown: the backend ends the runner's long poll"""
        body = {**state, "running_jobs": running_jobs, "stopping": stopping}
        return self._post("/heartbeat", body, timeout=timeout).json()

    def job_heartbeat(
        self,
        job_id: int,
        attempt: int,
        peak_memory_mb: int | None = None,
        starting=False,
    ) -> dict:
        """Answer: cancel, lease_until and a renewed job token. starting=True keeps the lease
        during preparation without marking the job running."""
        body = {"attempt": attempt, "peak_memory_mb": peak_memory_mb, "starting": starting}
        return self._post(f"/jobs/{job_id}/heartbeat", body).json()

    def job_log(self, job_id: int, attempt: int, stream: str, data: str):
        self._post(f"/jobs/{job_id}/log", {"attempt": attempt, "stream": stream, "data": data})

    def job_finish(
        self,
        job_id: int,
        attempt: int,
        status: str,
        exit_code: int | None = None,
        peak_memory_mb: int | None = None,
        message: str = "",
        resource_seconds: float | None = None,
    ) -> dict:
        """status: succeeded, failed, cancelled, timed_out, or returned (an assignment that was not
        started goes back to the queue, not counted after the shutdown announcement); retried with
        the same key"""
        key = str(uuid.uuid5(_NAMESPACE, f"finish:{job_id}:{attempt}"))
        return self._post(
            f"/jobs/{job_id}/finish",
            {
                "attempt": attempt,
                "status": status,
                "exit_code": exit_code,
                "peak_memory_mb": peak_memory_mb,
                "resource_seconds": resource_seconds,
                "message": message[-2000:],
            },
            headers={"Idempotency-Key": key},
        ).json()

    def rotate_token(self) -> str:
        """Exchange the token for a new one; the old one is invalid afterwards"""
        token = self._post("/token/rotate", {}).json()["token"]
        self.token = token
        self.client.headers["X-Runner-Token"] = token
        return token

    def get_bytes(self, url: str) -> bytes:
        r = self.client.get(url, timeout=300)
        r.raise_for_status()
        return r.content

    def download(self, url: str, dest: Path, sha256: str | None = None, progress=None):
        """Resumable download to dest, verified against sha256 if given"""
        part = dest.with_suffix(dest.suffix + ".part")
        dest.parent.mkdir(parents=True, exist_ok=True)
        offset = part.stat().st_size if part.exists() else 0
        headers = {"Range": f"bytes={offset}-"} if offset else {}
        with self.client.stream("GET", url, headers=headers, timeout=600) as r:
            if r.status_code == 416:
                # already complete
                pass
            else:
                r.raise_for_status()
                mode = "ab" if r.status_code == 206 else "wb"
                total = int(r.headers.get("content-length", 0)) + (offset if mode == "ab" else 0)
                done = offset if mode == "ab" else 0
                with open(part, mode) as f:
                    for chunk in r.iter_bytes(1 << 20):
                        f.write(chunk)
                        done += len(chunk)
                        if progress:
                            progress(done, total)
        if sha256:
            digest = hashlib.sha256()
            with open(part, "rb") as f:
                for chunk in iter(lambda: f.read(1 << 20), b""):
                    digest.update(chunk)
            if digest.hexdigest() != sha256:
                part.unlink()
                raise RuntimeError(f"checksum mismatch for {url}")
        part.replace(dest)
