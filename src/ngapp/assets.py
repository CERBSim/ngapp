"""Assets: datasets of an app that cases refer to, e.g. measured surfaces, materials or geometries

An asset is a case of kind "asset" on the backend with a type given by the app, a small meta
(shown in lists and usable as filter, keep it below 64 KB) and named values as content (large
values are stored as blobs). Every change of the content is a new version (revision); a case
stores the reference (id and revision) to reproduce its results with the same data.

Assets are private to their owner until shared: with users and groups like cases (also with
write access), read-only with all users of an app by an admin of the app. Jobs read the assets of
their app with the job token. Needs a backend: no assets in local mode.
"""

import os
from dataclasses import dataclass, field

import orjson

from .store.encoding import decode_value, encode_value
from .store.http import HTTPStore
from .store.types import BlobRef

KIND = "asset"
COMPONENT = "asset"
SECTION = "input"


@dataclass
class Asset:
    id: int
    revision: int
    name: str
    type: str
    meta: dict = field(default_factory=dict)
    apps: list[int] = field(default_factory=list)
    access: str = "read"
    owner_id: str = ""
    owner_name: str = ""
    app_id: int | None = None
    modified_at: str | None = None
    # the user administers the app of the asset: may share it with the app's users
    app_admin: bool = False

    @property
    def ref(self) -> dict:
        """Reference to store in a case"""
        return {"id": self.id, "revision": self.revision}

    @property
    def writable(self) -> bool:
        return self.access in ("owner", "write")


def _asset(data: dict) -> Asset:
    return Asset(
        id=data["id"],
        revision=data["head_revision"],
        name=data.get("name", ""),
        type=data.get("type") or "",
        meta=data.get("meta") or {},
        apps=data.get("apps") or [],
        access=data.get("access", "read"),
        owner_id=data.get("owner_id", ""),
        owner_name=data.get("owner_name", ""),
        app_id=data.get("app_id"),
        modified_at=data.get("modified_at"),
        app_admin=bool(data.get("app_admin")),
    )


def _job_token() -> str:
    path = os.environ.get("NGAPP_JOB_TOKEN_FILE")
    if path:
        try:
            with open(path) as f:
                token = f.read().strip()
            if token:
                return token
        except OSError:
            pass
    return os.environ.get("NGAPP_JOB_TOKEN", "")


_store: HTTPStore | None = None


def store() -> HTTPStore:
    """Store of the user of the app, in a job process the one with the job token"""
    global _store
    if _store is None:
        if os.environ.get("NGAPP_JOB_API"):
            _store = HTTPStore(os.environ["NGAPP_JOB_API"], _job_token)
        else:
            _store = HTTPStore.from_environment()
    return _store


def list_assets(app_id: int, type: str, meta: dict | None = None) -> list[Asset]:
    """Assets of the type the user reads: own, shared with the user and shared with the app;
    meta: only those whose meta contains it"""
    params = {"app_id": app_id, "kind": KIND, "type": type}
    if meta:
        params["meta"] = orjson.dumps(meta).decode()
    return [_asset(a) for a in store()._request("GET", "/v2/cases", params=params)]


def get(asset_id: int) -> Asset:
    return _asset(store()._request("GET", f"/v2/cases/{asset_id}"))


def create(app_id: int, type: str, name: str, data: dict, meta: dict | None = None) -> Asset:
    """New private asset of the user with the values of data as first version"""
    body = {"app_id": app_id, "name": name, "kind": KIND, "type": type, "meta": meta or {}}
    asset = _asset(store()._request("POST", "/v2/cases", body))
    try:
        return update(asset.id, data, note="Version 1", base=asset.revision)
    except Exception:
        delete(asset.id)
        raise


def update(
    asset_id: int,
    data: dict,
    meta: dict | None = None,
    note: str | None = None,
    base: int | None = None,
) -> Asset:
    """New version with the values of data (replacing all values) and meta if given; note
    names the version (default "Version n")"""
    s = store()
    if base is None:
        base = get(asset_id).revision
    if note is None:
        note = f"Version {len(versions(asset_id)) + 1}"
    ops = [{"op": "delete", "path": [COMPONENT]}]
    blobs: dict[str, tuple[BlobRef, bytes]] = {}
    for key, value in data.items():
        encoded = encode_value(value)
        blobs.update(encoded.blobs)
        ops.append({"op": "set", "path": [COMPONENT, SECTION, key], "value": encoded.stored})
    session = None
    if blobs:
        missing = s.blobs_missing(asset_id, [ref for ref, _ in blobs.values()])
        session = missing.upload_session
        for h in missing.missing:
            ref, raw = blobs[h]
            s.upload(session, ref, raw)
        session = s._renamed.get(session, session)
    body = {
        "base_revision": base,
        "release_id": s._release(asset_id),
        "kind": "named_version",
        "name": note,
        "upload_session": session,
        "ops": ops,
        "meta": meta,
    }
    s._request("POST", f"/v2/cases/{asset_id}/revisions", body)
    return get(asset_id)


def load(asset_id: int, revision: int | None = None) -> dict:
    """Values of a version (default: the latest)"""
    s = store()
    state = s.state(asset_id, revision)
    values = state["children"].get(COMPONENT, {}).get(SECTION, {})
    return {
        k: decode_value(v, lambda ref: s.read_blob(asset_id, ref)) for k, v in values.items()
    }


def versions(asset_id: int) -> list[dict]:
    """{"id", "name", "author", "created_at"} of the versions, newest first"""
    data = store()._request(
        "GET", f"/v2/cases/{asset_id}/revisions", params={"kind": "named_version"}
    )
    return data["revisions"]


def share_app(asset_id: int, app_id: int) -> None:
    """Read access for all users of the app (needs an admin of the app)"""
    store()._request("PUT", f"/v2/cases/{asset_id}/shares/apps/{app_id}")


def unshare_app(asset_id: int, app_id: int) -> None:
    store()._request("DELETE", f"/v2/cases/{asset_id}/shares/apps/{app_id}")


def rename(asset_id: int, name: str) -> None:
    """New name; the content stays"""
    s = store()
    body = {
        "base_revision": get(asset_id).revision,
        "release_id": s._release(asset_id),
        "kind": "autosave",
        "ops": [{"op": "set", "path": ["__case__", "meta", "name"], "value": name}],
    }
    s._request("POST", f"/v2/cases/{asset_id}/revisions", body)


def delete(asset_id: int) -> None:
    store()._request("DELETE", f"/v2/cases/{asset_id}")
