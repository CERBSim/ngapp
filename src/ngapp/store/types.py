"""Types and protocol of the case store"""

from dataclasses import dataclass, field, fields
from typing import Any, BinaryIO, Callable, Protocol

Path = tuple[str, ...]


@dataclass(frozen=True)
class BlobRef:
    hash: str
    size: int | None = None
    enc: str = "bytes"

    def to_json(self) -> dict:
        return {"$blob": self.hash, "size": self.size, "enc": self.enc}

    @classmethod
    def from_json(cls, data: dict) -> "BlobRef":
        return cls(data["$blob"], data.get("size"), data.get("enc", "bytes"))


OP_TYPES = ("set", "delete", "append")


@dataclass
class Op:
    """State operation; pos is assigned by the server for appends"""

    op: str
    path: Path
    value: Any = None
    pos: int | None = None

    def __post_init__(self):
        if self.op not in OP_TYPES:
            raise ValueError(f"Unknown operation {self.op!r}")
        self.path = tuple(self.path)

    def to_json(self) -> dict:
        data = {"op": self.op, "path": list(self.path)}
        if self.op != "delete":
            data["value"] = self.value
        if self.pos is not None:
            data["pos"] = self.pos
        return data

    @classmethod
    def from_json(cls, data: dict) -> "Op":
        return cls(data["op"], data["path"], data.get("value"), data.get("pos"))


@dataclass
class Conflict:
    path: Path
    base: Any
    head: Any
    mine: Any

    def to_json(self) -> dict:
        return {
            "path": list(self.path),
            "base": self.base,
            "head": self.head,
            "mine": self.mine,
        }

    @classmethod
    def from_json(cls, data: dict) -> "Conflict":
        return cls(
            tuple(data["path"]), data["base"], data["head"], data["mine"]
        )


@dataclass
class CommitResult:
    revision: int
    head: int
    remote_ops: list[Op] = field(default_factory=list)


@dataclass
class MissingResult:
    missing: list[str]
    upload_session: str


@dataclass
class CaseInfo:
    id: int
    app_id: int
    name: str
    owner: str
    head: int
    release_id: int | None = None
    write: bool = True


def _split_known(cls, data: dict) -> tuple[dict, dict]:
    """Known fields of a dataclass and the rest (kept in extra)"""
    names = {f.name for f in fields(cls)} - {"extra"}
    known = {k: v for k, v in data.items() if k in names}
    extra = {k: v for k, v in data.items() if k not in names}
    return known, extra


@dataclass
class JobRequest:
    function: dict
    input_revision: int
    args: list = field(default_factory=list)
    kwargs: dict = field(default_factory=dict)
    compute_env: str = "default"
    resources: dict = field(default_factory=dict)
    policy: dict = field(default_factory=dict)
    depends_on: list[int] = field(default_factory=list)
    # release of the submitting client (the store's when None)
    release_id: int | None = None

    @property
    def function_name(self) -> str:
        return ".".join([*self.function["component"], self.function["method"]])

    def to_json(self) -> dict:
        return {
            "function": self.function,
            "args": self.args,
            "kwargs": self.kwargs,
            "input_revision": self.input_revision,
            "compute_env": self.compute_env,
            "resources": self.resources,
            "policy": self.policy,
            "depends_on": self.depends_on,
            **(
                {"release_id": self.release_id}
                if self.release_id is not None
                else {}
            ),
        }


JOB_TERMINAL = ("succeeded", "failed", "cancelled", "timed_out")


@dataclass
class JobInfo:
    """Job as answered by GET /jobs/{id}; reused_run is set when a submission
    reused the succeeded run of an identical one"""

    id: int
    case_id: int
    function: str
    status: str
    input_revision: int
    run_id: int | None = None
    attempt: int = 0
    reused_run: int | None = None
    message: str = ""
    cancel_requested: bool = False
    fingerprint: str = ""
    release_id: int | None = None
    args: list = field(default_factory=list)
    kwargs: dict = field(default_factory=dict)
    exit_code: int | None = None
    queue_position: int | None = None
    extra: dict = field(default_factory=dict)

    @property
    def done(self) -> bool:
        return self.status in JOB_TERMINAL

    @classmethod
    def from_json(cls, data: dict, reused_run: int | None = None) -> "JobInfo":
        known, extra = _split_known(cls, data)
        known["message"] = known.get("message") or ""
        if reused_run is not None:
            known["reused_run"] = reused_run
        return cls(**known, extra=extra)


@dataclass
class RunInfo:
    id: int
    case_id: int
    job_id: int
    function: str
    status: str
    input_revision: int
    tip_revision: int
    fingerprint: str = ""
    release_id: int | None = None
    outdated: bool = False
    kept: bool = False
    image_hash: str | None = None
    job_status: str | None = None
    attempt: int = 0
    extra: dict = field(default_factory=dict)

    @classmethod
    def from_json(cls, data: dict) -> "RunInfo":
        known, extra = _split_known(cls, data)
        return cls(**known, extra=extra)


@dataclass
class Event:
    seq: int
    type: str
    payload: dict = field(default_factory=dict)


class StoreError(Exception):
    """Error answer of a store, mirrors the problem+json answers of the API"""

    status = 500
    code = "error"

    def __init__(self, message: str = "", **data):
        super().__init__(message or self.code)
        self.data = data


class InvalidError(StoreError):
    status, code = 400, "invalid"


class UnauthorizedError(StoreError):
    """Missing, invalid or expired token"""

    status, code = 401, "unauthorized"


class ForbiddenError(StoreError):
    status, code = 403, "forbidden"


class NotFoundError(StoreError):
    status, code = 404, "not_found"


class ConflictError(StoreError):
    status, code = 409, "conflict"

    def __init__(self, conflicts: list[Conflict], message: str = ""):
        super().__init__(message or f"{len(conflicts)} conflicting paths")
        self.conflicts = conflicts


class JobEndedError(StoreError):
    """The job attempt has ended for the backend: the job process should stop"""

    status = 409


class StaleAttemptError(JobEndedError):
    """The attempt ended or was superseded by another one"""

    code = "stale_attempt"


class JobCancelledError(JobEndedError):
    """The job was cancelled; its commits are refused"""

    code = "cancelled"


class BaseGoneError(StoreError):
    """The base revision was dropped by retention; reload the head"""

    status, code = 409, "base_gone"


class ReleaseTooOldError(StoreError):
    status, code = 409, "release_too_old"


class CaseDeletedError(StoreError):
    status, code = 410, "case_deleted"


class MissingBlobsError(StoreError):
    status, code = 422, "missing_blobs"

    def __init__(self, hashes: list[str], message: str = ""):
        super().__init__(message or f"missing blobs: {hashes}", hashes=hashes)
        self.hashes = hashes


class PossessionError(MissingBlobsError):
    status, code = 422, "possession"


class IdempotencyMismatchError(StoreError):
    """An Idempotency-Key was reused with another request body"""

    status, code = 422, "idempotency_mismatch"


class RateLimitedError(StoreError):
    status, code = 429, "rate_limited"

    def __init__(self, retry_after: float = 1.0, message: str = ""):
        super().__init__(message, retry_after=retry_after)
        self.retry_after = retry_after


class TransientStoreError(StoreError):
    """Connection lost or backend unavailable; the request may be retried"""

    status, code = 503, "unavailable"


ERRORS = {
    cls.code: cls
    for cls in (
        InvalidError,
        UnauthorizedError,
        ForbiddenError,
        NotFoundError,
        ConflictError,
        StaleAttemptError,
        JobCancelledError,
        BaseGoneError,
        ReleaseTooOldError,
        CaseDeletedError,
        MissingBlobsError,
        PossessionError,
        IdempotencyMismatchError,
        RateLimitedError,
        TransientStoreError,
    )
}


class CaseStore(Protocol):
    def create_case(
        self, app_id: int, name: str, ops: list[Op] = ()
    ) -> CaseInfo: ...

    def case(self, case_id: int) -> CaseInfo: ...

    def state(self, case_id: int, revision: int | None = None) -> dict:
        """{"revision", "release", "children", "event_seq"}: event_seq is the
        event position read before the state; subscribing from it misses no
        later change"""

    def changes(self, case_id: int, from_rev: int, to_rev: int) -> list[Op]: ...

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
    ) -> CommitResult: ...

    def blobs_missing(
        self, case_id: int, blobs: list[BlobRef]
    ) -> MissingResult: ...

    def upload(self, session: str, ref: BlobRef, data: BinaryIO) -> None: ...

    def read_blob(
        self,
        case_id: int,
        ref: BlobRef,
        byte_range: tuple[int, int] | None = None,
    ) -> bytes: ...

    def submit(self, case_id: int, request: JobRequest) -> JobInfo: ...

    def job(self, job_id: int) -> JobInfo: ...

    def cancel(self, job_id: int) -> None: ...

    def job_events(self, job_id: int, after: int = 0) -> list[dict]: ...

    def runs(self, case_id: int, function=None) -> list[RunInfo]: ...

    def run_changes(
        self,
        run_id: int,
        from_revision: int | None = None,
        to_revision: int | None = None,
    ) -> list[Op]:
        """Operations of the run's branch from from_revision (default the
        input revision) to to_revision (default the tip); BaseGoneError if
        from_revision is not an ancestor of to_revision"""

    def keep(self, run_id: int) -> None: ...

    def copy_case(
        self,
        case_id: int,
        *,
        revision: int | None = None,
        run_id: int | None = None,
        name: str | None = None,
    ) -> CaseInfo: ...

    def subscribe(
        self,
        case_ids: list[int],
        last_seq: int,
        callback: Callable[[Event], None],
    ) -> Callable[[], None]: ...
