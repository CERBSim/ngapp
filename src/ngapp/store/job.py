"""Case store of a job process: the parts of CaseStore a job needs, on the job
side of the runner protocol

The client is a ngapp.job_client.JobClient (HTTP) or a SQLiteJobClient. The
state is the job's input revision, with restart "checkpoint" the tip of its
run branch. Commits go onto the run branch as checkpoints; a commit of kind
"final" is the final commit. Every commit carries the next sequence number of
the attempt; a commit retried with the same idempotency key keeps its number.
"""

import io
from typing import Callable

from .tree import ABSENT, Seq, flatten, is_under, is_value_path, materialize
from .types import (
    BlobRef,
    CaseInfo,
    CommitResult,
    Event,
    InvalidError,
    JobInfo,
    JobRequest,
    MissingResult,
    Op,
    RunInfo,
)


def apply_ops(flat: dict, ops: list[Op]) -> dict:
    """Apply operations to a flat state (path -> stored value or Seq)"""
    flat = dict(flat)
    for op in ops:
        path = tuple(op.path)
        if op.op == "delete":
            if is_value_path(path):
                flat.pop(path, None)
            else:
                for p in [p for p in flat if is_under(p, path)]:
                    del flat[p]
        elif op.op == "set":
            flat[path] = op.value
        else:
            seq = flat.get(path, ABSENT)
            if isinstance(seq, list):
                seq = Seq(seq)
            elif not isinstance(seq, Seq):
                seq = Seq()
            flat[path] = seq.appended(op.value)
    return flat


class JobStore:
    """CaseStore of one job attempt"""

    def __init__(self, client, job_input: dict | None = None):
        self.client = client
        self.input = client.get_input() if job_input is None else job_input
        self.case_id = self.input["case_id"]
        self.release_id = self.input.get("release_id")
        checkpoint = self.input.get("checkpoint")
        self.tip = (
            checkpoint["revision"]
            if checkpoint
            else self.input["input_revision"]
        )
        self.dropped: list = []
        self._seqs: dict[str, int] = {}
        client.seq = max(client.seq, self.input.get("commit_seq") or 0)

    def _check(self, case_id):
        if case_id != self.case_id:
            raise InvalidError(
                f"a job of case {self.case_id} cannot use case {case_id}"
            )

    def state(self, case_id: int, revision: int | None = None) -> dict:
        self._check(case_id)
        flat = flatten({"children": self.input["state"]})
        checkpoint = self.input.get("checkpoint")
        if checkpoint:
            flat = apply_ops(
                flat, [Op.from_json(op) for op in checkpoint["ops"]]
            )
        return materialize(flat, revision=self.tip, release=self.release_id)

    def case(self, case_id: int) -> CaseInfo:
        self._check(case_id)
        return CaseInfo(case_id, -1, "", "", self.tip, self.release_id)

    def changes(self, case_id: int, from_rev: int, to_rev: int) -> list[Op]:
        self._check(case_id)
        return []

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
        self._check(case_id)
        if idempotency_key is None:
            seq = self.client.seq + 1
        else:
            seq = self._seqs.setdefault(idempotency_key, self.client.seq + 1)
        answer = self.client.commit(
            list(ops),
            seq=seq,
            final=kind == "final",
            upload_session=upload_session,
        )
        self.tip = answer["revision"]
        self.dropped.extend(answer.get("dropped") or [])
        return CommitResult(self.tip, self.tip, [])

    def blobs_missing(
        self, case_id: int, blobs: list[BlobRef]
    ) -> MissingResult:
        self._check(case_id)
        answer = self.client.blobs_missing(list(blobs))
        return MissingResult(answer["missing"], answer["upload_session"])

    def upload(self, session: str, ref: BlobRef, data) -> None:
        if isinstance(data, io.IOBase):
            data = data.read()
        stored = self.client.upload(data, ref.enc)
        if stored.hash != ref.hash:
            raise InvalidError(f"content does not match {ref.hash}")

    def read_blob(
        self,
        case_id: int,
        ref: BlobRef,
        byte_range: tuple[int, int] | None = None,
    ) -> bytes:
        self._check(case_id)
        return self.client.read_blob(ref, byte_range)

    def subscribe(
        self,
        case_ids: list[int],
        last_seq: int,
        callback: Callable[[Event], None],
    ) -> Callable[[], None]:
        return lambda: None

    def runs(self, case_id: int, function=None) -> list[RunInfo]:
        return []

    def submit(self, case_id: int, request: JobRequest) -> JobInfo:
        raise InvalidError(
            "jobs cannot submit jobs; call the function directly"
        )

    def progress(self, fraction=None, text=None):
        return self.client.progress(fraction, text)

