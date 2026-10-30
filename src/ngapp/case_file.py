"""A case as one file (ngapp.case/1) on any CaseStore

The format of the local app mode (ngapp.local_cases): a zip with case.json
(head state, the latest succeeded run of every function whose jobs do not
merge into the case, as operations from its input to its tip, blob
encodings) and blobs/<hex>. Here it is written and read through the
store interface, so that FULL mode (HTTP store) exports and imports the same
files. Imported runs become values of the new case: a store client cannot
create runs.
"""

import datetime
import io
import json
import zipfile

from .store.encoding import iter_blob_refs
from .store.tree import CASE_NAME, Seq, flatten, materialize
from .store.types import BlobRef, MissingBlobsError, Op

CASE_FORMAT = "ngapp.case/1"
CASE_SUFFIX = ".ngcase"


def _hex(h: str) -> str:
    return h.removeprefix("sha256:")


def _refs(values) -> dict[str, BlobRef]:
    refs = {}
    for value in values:
        items = value.items if isinstance(value, Seq) else (value,)
        for item in items:
            for ref in iter_blob_refs(item):
                refs.setdefault(ref.hash, ref)
    return refs


def export_case(store, case_id: int, app: dict | None = None) -> bytes:
    """The head state and the results of a case that are not in it (latest
    runs of functions without merge) with their blobs"""
    info = store.case(case_id)
    flat = flatten(store.state(case_id))
    runs, values = [], list(flat.values())
    latest = {}
    for run in store.runs(case_id):
        if run.status == "succeeded" and run.tip_revision != run.input_revision:
            latest[run.function] = run
    for function, run in sorted(latest.items()):
        job = store.job(run.job_id)
        if job.extra.get("policy", {}).get("merge", True):
            continue  # its results are in the case
        ops = store.run_changes(run.id)
        values += [op.value for op in ops if op.op != "delete"]
        runs.append(
            {
                "function": function,
                "status": run.status,
                "fingerprint": run.fingerprint,
                "release_id": run.release_id,
                "args": job.args,
                "kwargs": job.kwargs,
                "message": job.message,
                "ops": [op.to_json() for op in ops],
            }
        )
    refs = _refs(values)
    manifest = {
        "format": CASE_FORMAT,
        "app": dict(app or {}),
        "exported_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "app_id": info.app_id,
        "name": info.name,
        "release_id": info.release_id,
        "state": materialize(flat)["children"],
        "runs": runs,
        "blobs": {h: ref.enc for h, ref in refs.items()},
    }
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(
            "case.json",
            json.dumps(manifest),
            compress_type=zipfile.ZIP_DEFLATED,
        )
        for h, ref in sorted(refs.items()):
            zf.writestr(f"blobs/{_hex(h)}", store.read_blob(case_id, ref))
    return buf.getvalue()


def import_case(store, app_id: int, data: bytes, name: str | None = None):
    """A new case of the app from a case file; the data of its runs is
    applied to the case's values. Returns the case info."""
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        manifest = json.loads(zf.read("case.json"))
        fmt, _, major = str(manifest.get("format", "")).partition("/")
        if fmt != "ngapp.case" or major != "1":
            raise ValueError(
                f"unsupported case file {manifest.get('format')!r}"
            )
        flat = flatten({"children": manifest.get("state") or {}})
        flat.pop(CASE_NAME, None)
        ops = [Op("set", path, value) for path, value in sorted(flat.items())]
        for run in manifest.get("runs") or []:
            ops += [Op.from_json(op) for op in run.get("ops") or []]
        refs = _refs(op.value for op in ops if op.op != "delete")
        encs = manifest.get("blobs") or {}
        names = set(zf.namelist())
        missing = [h for h in refs if f"blobs/{_hex(h)}" not in names]
        if missing:
            raise MissingBlobsError(missing, f"the file lacks blobs {missing}")
        name = name or manifest.get("name") or "imported"
        case = store.create_case(app_id, name, [])
        session = None
        if refs:
            refs = {
                h: BlobRef(h, ref.size, encs.get(h, ref.enc))
                for h, ref in refs.items()
            }
            result = store.blobs_missing(case.id, list(refs.values()))
            session = result.upload_session
            for h in result.missing:
                content = zf.read(f"blobs/{_hex(h)}")
                ref = refs[h]
                store.upload(
                    session,
                    BlobRef(h, len(content), ref.enc),
                    io.BytesIO(content),
                )
    if ops:
        store.commit(
            case.id, case.head, ops, kind="import", upload_session=session
        )
    return store.case(case.id)
