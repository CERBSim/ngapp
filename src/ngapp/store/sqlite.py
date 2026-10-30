"""Case store on SQLite for the local app mode

SQLiteServer keeps cases, revisions, blobs, upload sessions, jobs, runs and
events of all principals in one database with the semantics of the server;
SQLiteStore is the CaseStore of one principal and SQLiteJobClient the job
side of one attempt. Several processes may use one database (the app, local job runners and jobs): WAL, one short
transaction per request, BEGIN IMMEDIATE for every change.

A revision holds the root of a tree of content-addressed nodes:
component nodes with their sections and children, values above 4 KB in value
nodes and sequences in pages of 1000 items, so that a commit stores only the
components it changed. Blob bytes are stored once per content in a directory
next to the database (<name>.blobs/sha256/<hex[0:2]>/<hex>), written to a
temporary file whose hash is checked before it is renamed into place; the
blob table records which scope holds a blob.

Events are rows of the database. Subscribers get the events of this process
after each change and those of other processes from a thread that polls the
database every poll_interval seconds (None: only on poll()).
"""

import contextlib
import dataclasses
import hashlib
import os
import sqlite3
import tempfile
import threading
import time
import uuid
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO, Callable

import orjson

from .encoding import canonical_json, iter_blob_refs, sha256
from .transfer import Source
from .tree import (
    ABSENT,
    CASE_NAME,
    Seq,
    is_under,
    is_value_path,
    materialize,
    stored_key,
)
from .types import (
    BaseGoneError,
    BlobRef,
    CaseDeletedError,
    CaseInfo,
    CommitResult,
    Conflict,
    ConflictError,
    Event,
    ForbiddenError,
    InvalidError,
    JobCancelledError,
    JobEndedError,
    JobInfo,
    JobRequest,
    MissingBlobsError,
    MissingResult,
    NotFoundError,
    Op,
    PossessionError,
    ReleaseTooOldError,
    RunInfo,
    StaleAttemptError,
)

VALUE_NODE = 4 * 1024
PAGE_ITEMS = 1000
LOG_LIMIT = 10 * 1024 * 1024
EVENT_RETENTION = 7 * 24 * 3600
SCHEMA_VERSION = "1"

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS node (hash TEXT PRIMARY KEY, body BLOB NOT NULL)
    WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT, app_id INTEGER NOT NULL,
    owner TEXT NOT NULL, name TEXT NOT NULL DEFAULT '', head INTEGER,
    created_at REAL NOT NULL, updated_at REAL NOT NULL,
    deleted INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS case_share (
    case_id INTEGER, user TEXT, write INTEGER, PRIMARY KEY (case_id, user));
CREATE TABLE IF NOT EXISTS case_blob (
    case_id INTEGER, hash TEXT, PRIMARY KEY (case_id, hash)) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS case_blob_hash ON case_blob (hash);
CREATE TABLE IF NOT EXISTS revision (
    id INTEGER PRIMARY KEY AUTOINCREMENT, case_id INTEGER NOT NULL,
    parent INTEGER, run_id INTEGER, root TEXT NOT NULL, kind TEXT NOT NULL,
    name TEXT, author TEXT NOT NULL, release_id INTEGER, ops BLOB NOT NULL,
    created_at REAL NOT NULL);
CREATE INDEX IF NOT EXISTS revision_line ON revision (case_id, run_id, id);
CREATE TABLE IF NOT EXISTS blob (
    scope TEXT, hash TEXT, size INTEGER, enc TEXT, state TEXT,
    created_at REAL, PRIMARY KEY (scope, hash)) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS upload_session (
    id TEXT PRIMARY KEY, principal TEXT, scope TEXT, created_at REAL);
CREATE INDEX IF NOT EXISTS upload_session_owner
    ON upload_session (principal, scope);
CREATE TABLE IF NOT EXISTS upload_item (
    session_id TEXT, hash TEXT, pin INTEGER,
    PRIMARY KEY (session_id, hash, pin)) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS job (
    id INTEGER PRIMARY KEY AUTOINCREMENT, case_id INTEGER NOT NULL,
    user TEXT NOT NULL, function TEXT NOT NULL, args BLOB, kwargs BLOB,
    input_revision INTEGER, release_id INTEGER, fingerprint TEXT, key TEXT,
    run_id INTEGER, resources BLOB, policy BLOB, depends_on BLOB,
    submitted INTEGER, status TEXT, attempt INTEGER, commit_seq INTEGER,
    started INTEGER, cancel_requested INTEGER, message TEXT,
    exit_code INTEGER, run_data BLOB, runner TEXT, log_bytes INTEGER,
    created_at REAL, started_at REAL, finished_at REAL);
CREATE INDEX IF NOT EXISTS job_case ON job (case_id, status);
CREATE INDEX IF NOT EXISTS job_status ON job (status);
CREATE TABLE IF NOT EXISTS job_result (
    job_id INTEGER, attempt INTEGER, seq INTEGER, result BLOB,
    PRIMARY KEY (job_id, attempt, seq));
CREATE TABLE IF NOT EXISTS job_event (
    job_id INTEGER, seq INTEGER, kind TEXT, payload BLOB, created_at REAL,
    PRIMARY KEY (job_id, seq));
CREATE TABLE IF NOT EXISTS run (
    id INTEGER PRIMARY KEY AUTOINCREMENT, case_id INTEGER NOT NULL,
    job_id INTEGER NOT NULL, function TEXT, input_revision INTEGER,
    tip_revision INTEGER, release_id INTEGER, fingerprint TEXT, status TEXT,
    kept INTEGER, closed INTEGER, created_at REAL);
CREATE INDEX IF NOT EXISTS run_case ON run (case_id, function);
CREATE TABLE IF NOT EXISTS event (
    seq INTEGER PRIMARY KEY AUTOINCREMENT, topic TEXT, type TEXT,
    payload BLOB, created_at REAL);
CREATE TABLE IF NOT EXISTS idempotency (
    principal TEXT, key TEXT, endpoint TEXT, result BLOB, created_at REAL,
    PRIMARY KEY (principal, key));
"""


def _wire(data):
    return orjson.loads(orjson.dumps(data))


def _wire_ops(ops) -> list[Op]:
    return [Op.from_json(op) for op in _wire([op.to_json() for op in ops])]


def _export(value):
    if value is ABSENT:
        return None
    if isinstance(value, Seq):
        return value.to_json()
    return value


def _diff_ops(a: dict, b: dict) -> list[Op]:
    """Operations turning flat state a into b; appends carry positions"""
    ops = []
    for p in sorted(set(a) | set(b)):
        old, new = a.get(p, ABSENT), b.get(p, ABSENT)
        if stored_key(old) == stored_key(new):
            continue
        if new is ABSENT:
            ops.append(Op("delete", p))
        elif isinstance(new, Seq):
            prefix = Seq(old) if isinstance(old, list) else old
            start = 0
            if (
                isinstance(prefix, Seq)
                and prefix.keys == new.keys[: len(prefix)]
            ):
                start = len(prefix)
            elif old is not ABSENT:
                ops.append(Op("delete", p))
            for i in range(start, len(new)):
                ops.append(Op("append", p, new.items[i], pos=i))
        else:
            ops.append(Op("set", p, new))
    return ops


@dataclass
class _Job:
    id: int
    case_id: int
    user: str
    function: str
    args: list
    kwargs: dict
    input_revision: int
    release_id: int | None
    fingerprint: str
    key: str
    run_id: int
    resources: dict
    policy: dict
    depends_on: list
    submitted: int
    status: str = "queued"
    attempt: int = 0
    commit_seq: int = 0
    started: bool = False
    cancel_requested: bool = False
    message: str = ""
    exit_code: int | None = None
    results: dict = field(default_factory=dict)
    events: list = field(default_factory=list)

    def info(self, reused_run=None) -> JobInfo:
        return JobInfo(
            self.id,
            self.case_id,
            self.function,
            self.status,
            self.input_revision,
            self.run_id,
            self.attempt,
            reused_run,
            self.message,
            self.cancel_requested,
            self.fingerprint,
            self.release_id,
            list(self.args),
            dict(self.kwargs),
            self.exit_code,
            extra={
                "resources": dict(self.resources),
                "policy": dict(self.policy),
            },
        )


@dataclass
class _Run:
    id: int
    case_id: int
    job_id: int
    function: str
    input_revision: int
    tip_revision: int
    release_id: int | None
    fingerprint: str
    status: str = "running"
    kept: bool = False
    closed: bool = False
    created_at: float | None = None
    started_at: float | None = None
    finished_at: float | None = None

    def info(self, **extra) -> RunInfo:
        return RunInfo(
            self.id,
            self.case_id,
            self.job_id,
            self.function,
            self.status,
            self.input_revision,
            self.tip_revision,
            self.fingerprint,
            self.release_id,
            kept=self.kept,
            extra={
                "created_at": _iso(self.created_at),
                "started_at": _iso(self.started_at),
                "finished_at": _iso(self.finished_at),
            },
            **extra,
        )


def _iso(t: float | None) -> str | None:
    if t is None:
        return None
    return datetime.fromtimestamp(t, timezone.utc).isoformat()


def _validate_ops(ops: list[Op]):
    for op in ops:
        path = op.path
        if not path or not all(isinstance(s, str) and s for s in path):
            raise InvalidError(f"invalid path {list(path)}")
        if is_value_path(path):
            key = path[-1]
            if key.startswith("$") and not key.startswith("$$"):
                raise InvalidError(f"key {key!r} is reserved")
            if op.op == "append" and path[-2] != "state":
                raise InvalidError("append is only allowed in section state")
        elif op.op != "delete" or path[0] == "__case__":
            raise InvalidError(f"{op.op} needs a value path, got {list(path)}")


def _merge(B, Bkeys, T, Tkeys, between: list[Op], ops: list[Op]):
    """Three-way merge per path; returns (state, keys, effective ops)"""
    written = {}
    subtree_deletes = []
    for op in ops:
        if op.op == "set":
            written[op.path] = op.value
        elif op.op == "delete" and is_value_path(op.path):
            written[op.path] = ABSENT
        elif op.op == "delete":
            subtree_deletes.append(op.path)
            for p in list(B) + list(written):
                if is_under(p, op.path):
                    written[p] = ABSENT
    delta = {p: v for p, v in written.items() if stored_key(v) != Bkeys.get(p)}
    deleted_between = [
        op.path
        for op in between
        if op.op == "delete" and not is_value_path(op.path)
    ]
    conflicts = []
    for p, v in delta.items():
        vkey = stored_key(v)
        bkey, tkey = Bkeys.get(p), Tkeys.get(p)
        if tkey == vkey:
            continue
        if tkey != bkey or (
            v is not ABSENT and any(is_under(p, d) for d in deleted_between)
        ):
            conflicts.append(
                Conflict(
                    p,
                    _export(B.get(p, ABSENT)),
                    _export(T.get(p, ABSENT)),
                    _export(v),
                )
            )
    conflict_paths = {c.path for c in conflicts}
    for prefix in subtree_deletes:
        for p in T:
            if (
                is_under(p, prefix)
                and p not in conflict_paths
                and Tkeys.get(p) != Bkeys.get(p)
            ):
                conflicts.append(
                    Conflict(p, _export(B.get(p, ABSENT)), _export(T[p]), None)
                )
    if conflicts:
        raise ConflictError(conflicts)

    M, Mkeys = dict(T), dict(Tkeys)
    effective = []
    for prefix in subtree_deletes:
        if any(is_under(p, prefix) for p in M):
            for p in [p for p in M if is_under(p, prefix)]:
                del M[p]
                del Mkeys[p]
            effective.append(Op("delete", prefix))
    for p, v in delta.items():
        if v is ABSENT:
            if p in M:
                del M[p]
                del Mkeys[p]
                effective.append(Op("delete", p))
        else:
            M[p] = v
            Mkeys[p] = stored_key(v)
            effective.append(Op("set", p, v))
    for op in ops:
        if op.op != "append":
            continue
        seq = M.get(op.path, ABSENT)
        if seq is ABSENT:
            seq = Seq()
        elif isinstance(seq, list):
            seq = Seq(seq)
        elif not isinstance(seq, Seq):
            raise InvalidError(f"append to a value at {list(op.path)}")
        M[op.path] = seq.appended(op.value)
        Mkeys[op.path] = M[op.path].key
        effective.append(Op("append", op.path, op.value, pos=len(seq)))
    return M, Mkeys, effective


def _dumps(value) -> bytes:
    return orjson.dumps(value, option=orjson.OPT_SORT_KEYS)


def _check_stored(value):
    """$node and $seq mark node references at the top of stored values"""
    if isinstance(value, dict) and ("$node" in value or "$seq" in value):
        raise InvalidError("keys $node and $seq are reserved")


class _LRU:
    def __init__(self, size: int):
        self.size = size
        self.data = OrderedDict()

    def get(self, key):
        value = self.data.get(key)
        if value is not None:
            self.data.move_to_end(key)
        return value

    def put(self, key, value):
        self.data[key] = value
        self.data.move_to_end(key)
        if len(self.data) > self.size:
            self.data.popitem(last=False)


@dataclass
class _Tree:
    """Flat state of a revision with its node layout: the form of every value
    in its component node (refs), the node hash of every component path
    (comps, the root at ()), child names and value paths per component and
    the pages of every sequence"""

    root: str = ""
    values: dict = field(default_factory=dict)
    keys: dict = field(default_factory=dict)
    refs: dict = field(default_factory=dict)
    comps: dict = field(default_factory=dict)
    kids: dict = field(default_factory=dict)
    index: dict = field(default_factory=dict)
    pages: dict = field(default_factory=dict)


@dataclass
class _Rev:
    id: int
    case_id: int
    parent: int | None
    run_id: int | None
    root: str
    kind: str
    author: str
    release_id: int | None


@dataclass
class _CaseRow:
    id: int
    app_id: int
    owner: str
    name: str
    head: int
    deleted: bool
    shares: dict


@dataclass
class _Subscription:
    principal: str
    case_ids: set
    callback: Callable[[Event], None]
    last: int = 0
    active: bool = True


def _process_tag(pid: int | None = None) -> str:
    """pid and start time of a process, so a reused pid is not mistaken"""
    pid = os.getpid() if pid is None else pid
    try:
        stat = Path(f"/proc/{pid}/stat").read_text()
        start = stat.rsplit(")", 1)[1].split()[19]
    except (OSError, IndexError):
        start = ""
    return f"{pid}:{start}"


def process_alive(tag: str | None) -> bool:
    if not tag:
        return False
    pid, _, start = tag.partition(":")
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return False
    except (PermissionError, ValueError):
        return True
    return not start or _process_tag(int(pid)) == tag


class SQLiteServer:
    """Database of the SQLite store, shared by the principals that use it

    path: the database file; blobs are stored in <stem>.blobs next to it.
    jobs: None (jobs wait until a runner claims them) or "process" (submit
    starts a detached local runner process); job_data is stored with every submitted job
    (app configuration, sys_path, cwd of the job process); max_jobs limits the
    jobs running at once.
    """

    def __init__(
        self,
        path,
        *,
        poll_interval: float | None = 0.1,
        jobs: str | None = None,
        job_data: dict | None = None,
        max_jobs: int = 2,
    ):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.blob_dir = self.path.with_name(self.path.stem + ".blobs")
        self.work_dir = self.path.with_name(self.path.stem + ".jobs")
        self.poll_interval = poll_interval
        self.jobs = jobs
        self.job_data = dict(job_data or {})
        self.max_jobs = max_jobs
        self._lock = threading.RLock()
        self._deliver_lock = threading.RLock()
        self._conn = self._connect()
        self._nodes = _LRU(20000)
        self._comps = _LRU(20000)
        self._pages = _LRU(2000)
        self._trees = _LRU(16)
        self._subs: list[_Subscription] = []
        self._delivered = 0
        self._poller = None
        self._stop = threading.Event()
        self._init_schema()
        self._empty = self._build(self._conn, _Tree(), {}, {}, [])

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(
            self.path,
            timeout=60,
            isolation_level=None,
            check_same_thread=False,
        )
        conn.execute("PRAGMA busy_timeout = 60000")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = FULL")
        return conn

    def _init_schema(self):
        with self._lock:
            self._conn.executescript(SCHEMA)
        with self._write() as c:
            version = self._meta(c, "schema")
            if version is None:
                self._set_meta(c, "schema", SCHEMA_VERSION)
            elif version != SCHEMA_VERSION:
                raise RuntimeError(
                    f"{self.path} has schema {version}, expected {SCHEMA_VERSION}"
                )
            cutoff = time.time() - EVENT_RETENTION
            old = c.execute(
                "SELECT MAX(seq) FROM event WHERE created_at < ?", (cutoff,)
            ).fetchone()[0]
            if old is not None:
                self._prune(c, old)
            self._delivered = self._top(c)

    def close(self):
        self._stop.set()
        if self._poller is not None:
            self._poller.join(timeout=5)
        with self._lock:
            self._conn.close()

    def client(
        self, user: str, *, release_id: int | None = None
    ) -> "SQLiteStore":
        return SQLiteStore(self, user, release_id)

    # -- transactions --

    @contextlib.contextmanager
    def _write(self):
        with self._lock:
            c = self._conn
            c.execute("BEGIN IMMEDIATE")
            try:
                yield c
                c.execute("COMMIT")
            except BaseException:
                if c.in_transaction:
                    c.execute("ROLLBACK")
                raise

    @contextlib.contextmanager
    def _read(self):
        with self._lock:
            c = self._conn
            c.execute("BEGIN")
            try:
                yield c
            finally:
                if c.in_transaction:
                    c.execute("COMMIT")

    def _meta(self, c, key):
        row = c.execute(
            "SELECT value FROM meta WHERE key = ?", (key,)
        ).fetchone()
        return None if row is None else row[0]

    def _set_meta(self, c, key, value):
        c.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
            (key, value),
        )

    def get_meta(self, key: str) -> str | None:
        with self._read() as c:
            return self._meta(c, key)

    def set_meta(self, key: str, value: str | None):
        with self._write() as c:
            if value is None:
                c.execute("DELETE FROM meta WHERE key = ?", (key,))
            else:
                self._set_meta(c, key, value)

    # -- nodes and trees --

    def _node(self, c, h: str) -> dict:
        node = self._nodes.get(h)
        if node is None:
            row = c.execute(
                "SELECT body FROM node WHERE hash = ?", (h,)
            ).fetchone()
            if row is None:
                raise RuntimeError(f"node {h} is missing in {self.path}")
            node = orjson.loads(row[0])
            self._nodes.put(h, node)
        return node

    def _put_node(self, c, node: dict) -> str:
        # always inserted: a cached node may stem from a rolled back change
        body = _dumps(node)
        h = sha256(body)
        c.execute(
            "INSERT OR IGNORE INTO node (hash, body) VALUES (?, ?)", (h, body)
        )
        self._nodes.put(h, node)
        return h

    def _page(self, c, h: str) -> tuple:
        page = self._pages.get(h)
        if page is None:
            node = self._node(c, h)
            items = []
            for ref in node["items"]:
                if isinstance(ref, dict) and "$node" in ref:
                    ref = self._node(c, ref["$node"])["v"]
                items.append(ref)
            page = (tuple(items), tuple(node["keys"]))
            self._pages.put(h, page)
        return page

    def _resolve(self, c, ref):
        """Value, content key and pages of the form of a value in its node"""
        if isinstance(ref, dict):
            if "$node" in ref:
                return self._node(c, ref["$node"])["v"], ref["key"], None
            if "$seq" in ref:
                pages = self._node(c, ref["$seq"])["pages"]
                items, keys = [], []
                for h, _ in pages:
                    page_items, page_keys = self._page(c, h)
                    items.extend(page_items)
                    keys.extend(page_keys)
                seq = Seq(items, keys)
                return seq, seq.key, pages
        return ref, stored_key(ref), None

    def _component(self, c, h: str) -> tuple:
        comp = self._comps.get(h)
        if comp is None:
            node = self._node(c, h)
            entries = []
            for section, values in node.items():
                if section in ("k", "children"):
                    continue
                for key, ref in values.items():
                    value, vkey, pages = self._resolve(c, ref)
                    entries.append((section, key, value, vkey, ref, pages))
            comp = (entries, dict(node.get("children") or {}))
            self._comps.put(h, comp)
        return comp

    def _tree(self, c, root: str) -> _Tree:
        tree = self._trees.get(root)
        if tree is not None:
            return tree
        tree = _Tree(root)

        def walk(h, path):
            tree.comps[path] = h
            entries, children = self._component(c, h)
            if children:
                tree.kids[path] = set(children)
            if entries:
                tree.index[path] = set()
            for section, key, value, vkey, ref, pages in entries:
                p = path + (section, key)
                tree.values[p] = value
                tree.keys[p] = vkey
                tree.refs[p] = ref
                tree.index[path].add(p)
                if pages is not None:
                    tree.pages[p] = pages
            for name, child in children.items():
                walk(child, path + (name,))

        walk(root, ())
        self._trees.put(root, tree)
        return tree

    def _value_ref(self, c, value, key):
        if len(orjson.dumps(value)) > VALUE_NODE:
            return {
                "$node": self._put_node(c, {"k": "value", "v": value}),
                "key": key,
            }
        return value

    def _seq_ref(self, c, seq: Seq, old, old_pages) -> tuple:
        """Pages of a sequence; full pages of a prefix it extends are kept"""
        pages, start = [], 0
        if (
            isinstance(old, Seq)
            and old_pages
            and seq.keys[: len(old)] == old.keys
        ):
            for h, n in old_pages:
                if n < PAGE_ITEMS:
                    break
                pages.append([h, n])
                start += n
        for i in range(start, len(seq), PAGE_ITEMS):
            stop = min(i + PAGE_ITEMS, len(seq))
            items = [
                self._value_ref(c, seq.items[j], seq.keys[j])
                for j in range(i, stop)
            ]
            node = {"k": "page", "items": items, "keys": list(seq.keys[i:stop])}
            pages.append([self._put_node(c, node), stop - i])
        return {"$seq": self._put_node(c, {"k": "seq", "pages": pages})}, pages

    def _build(self, c, T: _Tree, M: dict, Mkeys: dict, ops) -> _Tree:
        """Tree of the flat state M: the components the operations touched
        and their ancestors are stored again, the others are T's"""
        refs, comps, pages = dict(T.refs), dict(T.comps), dict(T.pages)
        kids, index = dict(T.kids), dict(T.index)
        copied = set()

        def mut(d, comp):
            key = (id(d), comp)
            if key not in copied or comp not in d:
                copied.add(key)
                d[comp] = set(d.get(comp, ()))
            return d[comp]

        dirty = {()}
        for op in ops:
            path = op.path
            comp = path[:-2] if is_value_path(path) else path
            dirty.update(comp[:i] for i in range(len(comp) + 1))
            if not is_value_path(path):
                for sub in [s for s in comps if is_under(s, path)]:
                    for p in index.pop(sub, ()):
                        refs.pop(p, None)
                        pages.pop(p, None)
                    kids.pop(sub, None)
                    comps.pop(sub, None)
                continue
            if path in M:
                value = M[path]
                if isinstance(value, Seq):
                    refs[path], pages[path] = self._seq_ref(
                        c, value, T.values.get(path), T.pages.get(path)
                    )
                else:
                    refs[path] = self._value_ref(c, value, Mkeys[path])
                    pages.pop(path, None)
                mut(index, comp).add(path)
            else:
                refs.pop(path, None)
                pages.pop(path, None)
                if path in index.get(comp, ()):
                    mut(index, comp).discard(path)
        for comp in sorted(dirty, key=len, reverse=True):
            values, names = index.get(comp) or (), kids.get(comp) or ()
            parent = comp[:-1]
            if comp and not values and not names:
                comps.pop(comp, None)
                index.pop(comp, None)
                kids.pop(comp, None)
                if comp[-1] in kids.get(parent, ()):
                    mut(kids, parent).discard(comp[-1])
                continue
            node = {"k": "component" if comp else "root"}
            if names:
                node["children"] = {n: comps[comp + (n,)] for n in names}
            for p in values:
                node.setdefault(p[-2], {})[p[-1]] = refs[p]
            comps[comp] = self._put_node(c, node)
            if comp and comp[-1] not in kids.get(parent, ()):
                mut(kids, parent).add(comp[-1])
        tree = _Tree(comps[()], M, Mkeys, refs, comps, kids, index, pages)
        self._trees.put(tree.root, tree)
        return tree

    # -- rows --

    def _top(self, c) -> int:
        return c.execute("SELECT COALESCE(MAX(seq), 0) FROM event").fetchone()[
            0
        ]

    def _rev(self, c, rev_id) -> _Rev | None:
        row = c.execute(
            "SELECT id, case_id, parent, run_id, root, kind, author, release_id"
            " FROM revision WHERE id = ?",
            (rev_id,),
        ).fetchone()
        return None if row is None else _Rev(*row)

    def _rev_tree(self, c, rev_id) -> _Tree:
        return self._tree(c, self._rev(c, rev_id).root)

    def _case_row(self, c, case_id) -> _CaseRow | None:
        row = c.execute(
            "SELECT id, app_id, owner, name, head, deleted FROM cases"
            " WHERE id = ?",
            (case_id,),
        ).fetchone()
        if row is None:
            return None
        shares = dict(
            c.execute(
                "SELECT user, write FROM case_share WHERE case_id = ?",
                (case_id,),
            ).fetchall()
        )
        return _CaseRow(
            *row[:5], bool(row[5]), {u: bool(w) for u, w in shares.items()}
        )

    def _users(self, case: _CaseRow):
        return [case.owner, *case.shares]

    def _may_read(self, case: _CaseRow, principal: str) -> bool:
        return principal == case.owner or principal in case.shares

    def _case(self, c, case_id, principal, write=False) -> _CaseRow:
        case = self._case_row(c, case_id)
        if case is None or not self._may_read(case, principal):
            raise NotFoundError(f"case {case_id}")
        if case.deleted:
            raise CaseDeletedError(f"case {case_id} was deleted")
        if write and principal != case.owner and not case.shares.get(principal):
            raise ForbiddenError(f"no write access to case {case_id}")
        return case

    def _on_line(self, c, case_id, rev_id) -> bool:
        return (
            c.execute(
                "SELECT 1 FROM revision WHERE id = ? AND case_id = ?"
                " AND run_id IS NULL",
                (rev_id, case_id),
            ).fetchone()
            is not None
        )

    def _readable(self, c, principal, h) -> bool:
        return (
            c.execute(
                "SELECT 1 FROM case_blob b JOIN cases c ON c.id = b.case_id"
                " WHERE b.hash = ? AND c.deleted = 0 AND (c.owner = ? OR"
                " EXISTS (SELECT 1 FROM case_share s WHERE s.case_id = c.id"
                " AND s.user = ?)) LIMIT 1",
                (h, principal, principal),
            ).fetchone()
            is not None
        )

    def _in_sessions(self, c, principal, scope, h) -> bool:
        return (
            c.execute(
                "SELECT 1 FROM upload_item i JOIN upload_session s"
                " ON s.id = i.session_id WHERE s.principal = ? AND s.scope = ?"
                " AND i.hash = ? LIMIT 1",
                (principal, scope, h),
            ).fetchone()
            is not None
        )

    def _in_session(self, c, session_id, h) -> bool:
        return (
            c.execute(
                "SELECT 1 FROM upload_item WHERE session_id = ? AND hash = ?"
                " LIMIT 1",
                (session_id, h),
            ).fetchone()
            is not None
        )

    def _case_has(self, c, case_id, h) -> bool:
        return (
            c.execute(
                "SELECT 1 FROM case_blob WHERE case_id = ? AND hash = ?",
                (case_id, h),
            ).fetchone()
            is not None
        )

    def _blob_state(self, c, scope, h):
        row = c.execute(
            "SELECT state FROM blob WHERE scope = ? AND hash = ?", (scope, h)
        ).fetchone()
        return None if row is None else row[0]

    def _session_row(self, c, session_id):
        return c.execute(
            "SELECT principal, scope FROM upload_session WHERE id = ?",
            (session_id,),
        ).fetchone()

    def _emit(self, c, topic: str, type_: str, payload: dict):
        c.execute(
            "INSERT INTO event (topic, type, payload, created_at)"
            " VALUES (?, ?, ?, ?)",
            (topic, type_, orjson.dumps(payload), time.time()),
        )

    def _link_blobs(self, c, case_id, hashes):
        c.executemany(
            "INSERT OR IGNORE INTO case_blob (case_id, hash) VALUES (?, ?)",
            [(case_id, h) for h in hashes],
        )

    # -- events --

    def _matches(self, sub: _Subscription, topic: str) -> bool:
        kind, _, ident = topic.partition(":")
        if kind == "case":
            return int(ident) in sub.case_ids
        return kind == "user" and ident == sub.principal

    def _call(self, sub, event):
        try:
            sub.callback(Event(event.seq, event.type, _wire(event.payload)))
        except Exception as e:  # a failing subscriber must not affect others
            print("Error in event callback:", repr(e))

    def _deliver(self):
        """Send the events after the last delivered one to the subscribers"""
        if not self._subs:
            return
        with self._deliver_lock:
            while True:
                with self._read() as c:
                    rows = c.execute(
                        "SELECT seq, topic, type, payload FROM event"
                        " WHERE seq > ? ORDER BY seq LIMIT 500",
                        (self._delivered,),
                    ).fetchall()
                if not rows:
                    return
                for seq, topic, type_, payload in rows:
                    self._delivered = max(self._delivered, seq)
                    event = Event(seq, type_, orjson.loads(payload))
                    for sub in list(self._subs):
                        if (
                            sub.active
                            and seq > sub.last
                            and self._matches(sub, topic)
                        ):
                            sub.last = seq
                            self._call(sub, event)

    def poll(self):
        """Deliver the events of other processes now"""
        self._deliver()

    def _poll_loop(self):
        conn = sqlite3.connect(self.path, timeout=60, check_same_thread=False)
        version = None
        try:
            while not self._stop.wait(self.poll_interval):
                if not self._subs:
                    continue
                try:
                    current = conn.execute("PRAGMA data_version").fetchone()[0]
                    if current != version:
                        version = current
                        self._deliver()
                except sqlite3.Error as e:
                    print("Polling events failed:", repr(e))
        finally:
            conn.close()

    def subscribe(self, principal, case_ids, last_seq, callback):
        with self._deliver_lock:
            with self._read() as c:
                for case_id in case_ids:
                    self._case(c, case_id, principal)
                sub = _Subscription(principal, set(case_ids), callback)
                top = self._top(c)
                pruned = int(self._meta(c, "pruned_seq") or 0)
                if last_seq is not None and (
                    last_seq < pruned or last_seq > top
                ):
                    replay = [Event(top, "resync", {})]
                else:
                    rows = c.execute(
                        "SELECT seq, topic, type, payload FROM event"
                        " WHERE seq > ? AND seq <= ? ORDER BY seq",
                        (top if last_seq is None else last_seq, top),
                    ).fetchall()
                    replay = [
                        Event(seq, type_, orjson.loads(payload))
                        for seq, topic, type_, payload in rows
                        if self._matches(sub, topic)
                    ]
            sub.last = top
            if not self._subs:
                self._delivered = top
            self._subs.append(sub)
            for event in replay:
                self._call(sub, event)
        if self.poll_interval is not None and self._poller is None:
            self._poller = threading.Thread(
                target=self._poll_loop, name="ngapp-sqlite-events", daemon=True
            )
            self._poller.start()

        def unsubscribe():
            sub.active = False
            self._subs = [s for s in self._subs if s is not sub]

        return unsubscribe

    # -- admin --

    def delete_case(self, case_id: int):
        """Soft delete; the case's unfinished jobs are cancelled"""
        with self._write() as c:
            case = self._case_row(c, case_id)
            if case is None:
                raise NotFoundError(f"case {case_id}")
            c.execute(
                "UPDATE cases SET deleted = 1, updated_at = ? WHERE id = ?",
                (time.time(), case_id),
            )
            for job in self._jobs_where(
                c,
                "case_id = ? AND status IN ('queued', 'assigned', 'running')",
                (case_id,),
            ):
                self._cancel_job(c, job, "the case was deleted")
            self._emit(
                c, f"case:{case_id}", "case.deleted", {"case_id": case_id}
            )
            for user in self._users(case):
                self._emit(
                    c, f"user:{user}", "cases.changed", {"case_id": case_id}
                )
        self._deliver()

    def _prune(self, c, up_to_seq):
        c.execute("DELETE FROM event WHERE seq <= ?", (up_to_seq,))
        pruned = int(self._meta(c, "pruned_seq") or 0)
        self._set_meta(c, "pruned_seq", str(max(pruned, up_to_seq)))

    # -- internals of commits --

    def _validate_ops(self, ops):
        _validate_ops(ops)
        for op in ops:
            if op.op != "delete":
                _check_stored(op.value)

    def _check_blobs(self, c, case: _CaseRow, principal, ops, session_id):
        refs = {}
        for op in ops:
            if op.op != "delete":
                for ref in iter_blob_refs(op.value):
                    refs[ref.hash] = ref
        if not refs:
            return set()
        scope = case.owner
        missing = [
            h
            for h in refs
            if self._blob_state(c, scope, h) in (None, "quarantined")
        ]
        if missing:
            raise MissingBlobsError(sorted(missing))
        session = self._session_row(c, session_id) if session_id else None
        own = session is not None and session[0] == principal
        foreign = [
            h
            for h in refs
            if not self._readable(c, principal, h)
            and not (own and self._in_session(c, session_id, h))
        ]
        if foreign:
            raise PossessionError(sorted(foreign))
        return set(refs)

    def _between(self, c, case_id, from_rev, to_rev) -> list[Op]:
        if not (
            self._on_line(c, case_id, from_rev)
            and self._on_line(c, case_id, to_rev)
        ):
            raise InvalidError("revision is not on the case line")
        if from_rev > to_rev:
            raise InvalidError("from_rev is newer than to_rev")
        ops = []
        for (data,) in c.execute(
            "SELECT ops FROM revision WHERE case_id = ? AND run_id IS NULL"
            " AND id > ? AND id <= ? ORDER BY id",
            (case_id, from_rev, to_rev),
        ):
            ops.extend(Op.from_json(op) for op in orjson.loads(data))
        return ops

    def _new_revision(
        self,
        c,
        case_id,
        parent,
        tree: _Tree,
        ops,
        *,
        kind,
        name,
        author,
        release_id,
        run_id=None,
    ) -> int:
        cur = c.execute(
            "INSERT INTO revision (case_id, parent, run_id, root, kind, name,"
            " author, release_id, ops, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                case_id,
                parent,
                run_id,
                tree.root,
                kind,
                name,
                author,
                release_id,
                orjson.dumps([op.to_json() for op in ops]),
                time.time(),
            ),
        )
        return cur.lastrowid

    def _after_commit(
        self, c, case: _CaseRow, rev_id, parent, kind, author, tree
    ):
        c.execute(
            "UPDATE cases SET head = ?, updated_at = ? WHERE id = ?",
            (rev_id, time.time(), case.id),
        )
        case.head = rev_id
        name = tree.values.get(CASE_NAME, ABSENT)
        name = name if isinstance(name, str) else ""
        kind_, _, ident = author.partition(":")
        self._emit(
            c,
            f"case:{case.id}",
            "case.head",
            {
                "case_id": case.id,
                "revision": rev_id,
                "parent": parent,
                "author": (
                    {"job": int(ident)}
                    if kind_ == "job" and ident
                    else {"user": author}
                ),
                "kind": kind,
            },
        )
        if name != case.name:
            case.name = name
            c.execute("UPDATE cases SET name = ? WHERE id = ?", (name, case.id))
            for user in self._users(case):
                self._emit(
                    c, f"user:{user}", "cases.changed", {"case_id": case.id}
                )

    def _info(self, c, case: _CaseRow, principal) -> CaseInfo:
        return CaseInfo(
            id=case.id,
            app_id=case.app_id,
            name=case.name,
            owner=case.owner,
            head=case.head,
            release_id=self._rev(c, case.head).release_id,
            write=principal == case.owner or bool(case.shares.get(principal)),
        )

    def _insert_case(self, c, principal, app_id):
        """A new case row (head set by the first revision)"""
        now = time.time()
        cur = c.execute(
            "INSERT INTO cases (app_id, owner, name, head, created_at,"
            " updated_at) VALUES (?, ?, '', NULL, ?, ?)",
            (app_id, principal, now, now),
        )
        return _CaseRow(cur.lastrowid, app_id, principal, "", None, False, {})

    # -- operations, called by SQLiteStore --

    def create_case(self, principal, release_id, app_id, name, ops):
        ops = list(ops)
        self._validate_ops(ops)
        with self._write() as c:
            case = self._insert_case(c, principal, app_id)
            if name:
                ops.insert(0, Op("set", CASE_NAME, name))
            refs = self._check_blobs(c, case, principal, ops, None)
            state, keys, effective = _merge({}, {}, {}, {}, [], ops)
            tree = self._build(c, self._empty, state, keys, effective)
            rev = self._new_revision(
                c,
                case.id,
                None,
                tree,
                effective,
                kind="system",
                name=None,
                author=principal,
                release_id=release_id,
            )
            self._link_blobs(c, case.id, refs)
            self._after_commit(c, case, rev, None, "system", principal, tree)
            self._emit(
                c, f"user:{principal}", "cases.changed", {"case_id": case.id}
            )
            info = self._info(c, case, principal)
        self._deliver()
        return info

    def commit(
        self,
        principal,
        release_id,
        case_id,
        base,
        ops,
        kind,
        name,
        upload_session,
        idempotency_key,
    ):
        self._validate_ops(ops)
        with self._write() as c:
            if idempotency_key:
                row = c.execute(
                    "SELECT endpoint, result FROM idempotency WHERE principal = ?"
                    " AND key = ?",
                    (principal, idempotency_key),
                ).fetchone()
                if row is not None:
                    if row[0] != f"commit:{case_id}":
                        raise InvalidError(
                            "idempotency key used for another request"
                        )
                    data = orjson.loads(row[1])
                    return CommitResult(
                        data["revision"],
                        data["head"],
                        [Op.from_json(op) for op in data["remote_ops"]],
                    )
            case = self._case(c, case_id, principal, write=True)
            head = self._rev(c, case.head)
            if (
                release_id is not None
                and head.release_id is not None
                and release_id < head.release_id
            ):
                raise ReleaseTooOldError(
                    f"release {release_id} is older than {head.release_id}"
                )
            if not self._on_line(c, case_id, base):
                raise InvalidError(f"revision {base} is not on the case line")
            refs = self._check_blobs(c, case, principal, ops, upload_session)
            between = self._between(c, case_id, base, case.head)
            B = self._rev_tree(c, base)
            T = self._tree(c, head.root)
            state, keys, effective = _merge(
                B.values, B.keys, T.values, T.keys, between, ops
            )
            tree = self._build(c, T, state, keys, effective)
            rev = self._new_revision(
                c,
                case.id,
                head.id,
                tree,
                effective,
                kind=kind,
                name=name,
                author=principal,
                release_id=release_id,
            )
            self._link_blobs(c, case.id, refs)
            if upload_session:
                self._drop_session(c, upload_session)
            self._after_commit(c, case, rev, head.id, kind, principal, tree)
            result = CommitResult(rev, rev, between)
            if idempotency_key:
                c.execute(
                    "INSERT INTO idempotency (principal, key, endpoint, result,"
                    " created_at) VALUES (?, ?, ?, ?, ?)",
                    (
                        principal,
                        idempotency_key,
                        f"commit:{case_id}",
                        orjson.dumps(
                            {
                                "revision": rev,
                                "head": rev,
                                "remote_ops": [op.to_json() for op in between],
                            }
                        ),
                        time.time(),
                    ),
                )
        self._deliver()
        return result

    def _drop_session(self, c, session_id):
        c.execute("DELETE FROM upload_item WHERE session_id = ?", (session_id,))
        c.execute("DELETE FROM upload_session WHERE id = ?", (session_id,))

    def state(self, principal, case_id, revision):
        with self._read() as c:
            event_seq = self._top(c)
            case = self._case(c, case_id, principal)
            revision = case.head if revision is None else revision
            rev = self._rev(c, revision)
            if rev is None or rev.case_id != case.id:
                raise NotFoundError(f"revision {revision}")
            tree = self._tree(c, rev.root)
            return materialize(
                tree.values,
                revision=rev.id,
                release=rev.release_id,
                event_seq=event_seq,
            )

    def changes(self, principal, case_id, from_rev, to_rev):
        with self._read() as c:
            self._case(c, case_id, principal)
            return self._between(c, case_id, from_rev, to_rev)

    def case(self, principal, case_id):
        with self._read() as c:
            return self._info(c, self._case(c, case_id, principal), principal)

    def cases_of(self, principal, app_id=None) -> list[CaseInfo]:
        """Cases the principal can read, most recently changed first"""
        with self._read() as c:
            ids = [
                row[0]
                for row in c.execute(
                    "SELECT id FROM cases WHERE deleted = 0 AND (owner = ? OR id IN"
                    " (SELECT case_id FROM case_share WHERE user = ?))"
                    " AND (? IS NULL OR app_id = ?) ORDER BY updated_at DESC, id DESC",
                    (principal, principal, app_id, app_id),
                )
            ]
            return [self._info(c, self._case_row(c, i), principal) for i in ids]

    def case_times(self, case_id) -> tuple[float, float]:
        with self._read() as c:
            row = c.execute(
                "SELECT created_at, updated_at FROM cases WHERE id = ?",
                (case_id,),
            ).fetchone()
        if row is None:
            raise NotFoundError(f"case {case_id}")
        return row

    # -- blobs --

    def blob_path(self, h: str) -> Path:
        hex_ = h.removeprefix("sha256:")
        if len(hex_) != 64 or not all(ch in "0123456789abcdef" for ch in hex_):
            raise InvalidError(f"invalid hash {h}")
        return self.blob_dir / "sha256" / hex_[:2] / hex_

    def _store_bytes(self, data, expect: str | None = None, size=None) -> tuple:
        """Write bytes, a file object or a file into the blob directory; the
        hash is computed while writing and checked before the rename"""
        src = data if isinstance(data, Source) else Source(data)
        tmp_dir = self.blob_dir / "tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=tmp_dir)
        try:
            digest = hashlib.sha256()
            with os.fdopen(fd, "wb") as f:
                for offset in range(0, src.size, Source.CHUNK):
                    chunk = src.read(offset, Source.CHUNK)
                    digest.update(chunk)
                    f.write(chunk)
                f.flush()
                os.fsync(f.fileno())
            h = "sha256:" + digest.hexdigest()
            if (expect is not None and h != expect) or (
                size is not None and src.size != size
            ):
                raise InvalidError(f"content does not match {expect}")
            path = self.blob_path(h)
            if path.exists() and path.stat().st_size == src.size:
                os.unlink(tmp)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                os.replace(tmp, path)
            tmp = None
            return h, src.size
        finally:
            if tmp is not None:
                with contextlib.suppress(OSError):
                    os.unlink(tmp)

    def _read_bytes(self, h, byte_range=None) -> bytes:
        try:
            with open(self.blob_path(h), "rb") as f:
                if byte_range is None:
                    return f.read()
                f.seek(byte_range[0])
                return f.read(max(0, byte_range[1] - byte_range[0]))
        except FileNotFoundError:
            raise NotFoundError(
                f"blob {h} is missing in {self.blob_dir}"
            ) from None

    def _put_blob(self, c, scope, h, size, enc):
        state = self._blob_state(c, scope, h)
        if state is None or state == "quarantined":
            c.execute(
                "INSERT OR REPLACE INTO blob (scope, hash, size, enc, state,"
                " created_at) VALUES (?, ?, ?, ?, 'verified', ?)",
                (scope, h, size, enc, time.time()),
            )

    def _new_session(self, c, principal, scope) -> str:
        session = str(uuid.uuid4())
        c.execute(
            "INSERT INTO upload_session (id, principal, scope, created_at)"
            " VALUES (?, ?, ?, ?)",
            (session, principal, scope, time.time()),
        )
        return session

    def _missing(self, c, scope, session, refs, available) -> list[str]:
        missing = []
        for ref in refs:
            state = self._blob_state(c, scope, ref.hash)
            if state not in (None, "quarantined") and available(ref.hash):
                c.execute(
                    "INSERT OR IGNORE INTO upload_item (session_id, hash, pin)"
                    " VALUES (?, ?, 1)",
                    (session, ref.hash),
                )
            else:
                missing.append(ref.hash)
        return missing

    def blobs_missing(self, principal, case_id, refs):
        with self._write() as c:
            case = self._case(c, case_id, principal, write=True)
            scope = case.owner
            session = self._new_session(c, principal, scope)
            missing = self._missing(
                c,
                scope,
                session,
                refs,
                lambda h: self._readable(c, principal, h)
                or self._in_sessions(c, principal, scope, h),
            )
            return MissingResult(missing, session)

    def upload(self, principal, session_id, ref, data):
        with self._read() as c:
            session = self._session_row(c, session_id)
        if session is None or session[0] != principal:
            raise NotFoundError(f"upload session {session_id}")
        h, size = self._store_bytes(data, ref.hash, ref.size)
        with self._write() as c:
            if self._session_row(c, session_id) is None:
                raise NotFoundError(f"upload session {session_id}")
            self._put_blob(c, session[1], h, size, ref.enc)
            c.execute(
                "INSERT OR IGNORE INTO upload_item (session_id, hash, pin)"
                " VALUES (?, ?, 0)",
                (session_id, h),
            )

    def read_blob(self, principal, case_id, ref, byte_range):
        with self._read() as c:
            case = self._case(c, case_id, principal)
            scope = case.owner
            visible = self._case_has(c, case.id, ref.hash) or self._in_sessions(
                c, principal, scope, ref.hash
            )
            if not visible or self._blob_state(c, scope, ref.hash) in (
                None,
                "quarantined",
            ):
                raise NotFoundError(f"blob {ref.hash}")
        return self._read_bytes(ref.hash, byte_range)

    # -- jobs and runs (user side) --

    def _fingerprint(self, tree: _Tree, function, args, release) -> str:
        """Conservative fingerprint: the inputs of the case line, function,
        arguments, release and image"""
        values = sorted(
            [list(p), k] for p, k in tree.keys.items() if p[-2] == "input"
        )
        return sha256(
            canonical_json(
                {
                    "values": values,
                    "function": function,
                    "args": args,
                    "release": release,
                    "image": None,
                }
            )
        )

    _JOB_COLUMNS = (
        "id, case_id, user, function, args, kwargs, input_revision, release_id,"
        " fingerprint, key, run_id, resources, policy, depends_on, submitted,"
        " status, attempt, commit_seq, started, cancel_requested, message,"
        " exit_code"
    )

    def _job_from(self, row) -> _Job:
        (
            id_,
            case_id,
            user,
            function,
            args,
            kwargs,
            input_revision,
            release_id,
            fingerprint,
            key,
            run_id,
            resources,
            policy,
            depends_on,
            submitted,
            status,
            attempt,
            commit_seq,
            started,
            cancel_requested,
            message,
            exit_code,
        ) = row
        return _Job(
            id_,
            case_id,
            user,
            function,
            orjson.loads(args),
            orjson.loads(kwargs),
            input_revision,
            release_id,
            fingerprint,
            key,
            run_id,
            orjson.loads(resources),
            orjson.loads(policy),
            orjson.loads(depends_on),
            submitted,
            status,
            attempt,
            commit_seq,
            bool(started),
            bool(cancel_requested),
            message or "",
            exit_code,
        )

    def _jobs_where(self, c, where, params=()) -> list[_Job]:
        return [
            self._job_from(row)
            for row in c.execute(
                f"SELECT {self._JOB_COLUMNS} FROM job WHERE {where} ORDER BY id",
                params,
            )
        ]

    def _job(self, c, job_id, principal=None, write=False) -> _Job:
        jobs = self._jobs_where(c, "id = ?", (job_id,))
        if not jobs:
            raise NotFoundError(f"job {job_id}")
        if principal is not None:
            self._case(c, jobs[0].case_id, principal, write=write)
        return jobs[0]

    def _save_job(self, c, job: _Job, **extra):
        columns = {
            "key": job.key,
            "submitted": job.submitted,
            "status": job.status,
            "attempt": job.attempt,
            "commit_seq": job.commit_seq,
            "started": int(job.started),
            "cancel_requested": int(job.cancel_requested),
            "message": job.message,
            "exit_code": job.exit_code,
            **extra,
        }
        c.execute(
            "UPDATE job SET "
            + ", ".join(f"{k} = ?" for k in columns)
            + " WHERE id = ?",
            (*columns.values(), job.id),
        )

    def _run_row(self, c, run_id) -> _Run | None:
        row = c.execute(
            "SELECT id, case_id, job_id, function, input_revision, tip_revision,"
            " release_id, fingerprint, status, kept, closed FROM run WHERE id = ?",
            (run_id,),
        ).fetchone()
        if row is None:
            return None
        return _Run(*row[:9], kept=bool(row[9]), closed=bool(row[10]))

    def _save_run(self, c, run: _Run):
        c.execute(
            "UPDATE run SET status = ?, tip_revision = ?, kept = ?, closed = ?"
            " WHERE id = ?",
            (
                run.status,
                run.tip_revision,
                int(run.kept),
                int(run.closed),
                run.id,
            ),
        )

    def _run(self, c, run_id, principal, write=False) -> _Run:
        run = self._run_row(c, run_id)
        if run is None:
            raise NotFoundError(f"run {run_id}")
        self._case(c, run.case_id, principal, write=write)
        return run

    def _job_status(self, c, job: _Job, message=""):
        self._emit(
            c,
            f"case:{job.case_id}",
            "job.status",
            {
                "case_id": job.case_id,
                "job_id": job.id,
                "status": job.status,
                "attempt": job.attempt,
                "message": message,
            },
        )

    def _run_status(self, c, run: _Run):
        self._emit(
            c,
            f"case:{run.case_id}",
            "run.status",
            {
                "case_id": run.case_id,
                "run_id": run.id,
                "job_id": run.job_id,
                "status": run.status,
                "tip_revision": run.tip_revision,
                "kept": run.kept,
            },
        )

    def _cancel_job(self, c, job: _Job, message: str):
        if job.status == "queued":
            job.status, job.message = "cancelled", message
            self._save_job(c, job, finished_at=time.time())
            self._job_status(c, job, message)
            run = self._run_row(c, job.run_id)
            run.status = "cancelled"
            self._save_run(c, run)
            self._run_status(c, run)
        elif (
            job.status in ("assigned", "running")
            and not job.cancel_requested
            and not self._run_row(c, job.run_id).closed
        ):
            # after the final commit the result is kept
            job.cancel_requested, job.message = True, message
            job.key = f"cancelled:{job.id}"
            self._save_job(c, job)
            self._job_status(c, job, "cancel requested")

    def _cancel_previous(self, c, case_id, function, keep=None):
        for job in self._jobs_where(
            c,
            "case_id = ? AND function = ? AND status IN"
            " ('queued', 'assigned', 'running')",
            (case_id, function),
        ):
            if job.id != keep:
                self._cancel_job(c, job, "cancelled by a newer submission")

    def _next_submission(self, c) -> int:
        return c.execute(
            "SELECT COALESCE(MAX(submitted), 0) + 1 FROM job"
        ).fetchone()[0]

    def submit(self, principal, case_id, request, job_data=None):
        with self._write() as c:
            case = self._case(c, case_id, principal, write=True)
            if not self._on_line(c, case_id, request.input_revision):
                raise InvalidError("input_revision is not on the case line")
            name = request.function_name
            rev = self._rev(c, request.input_revision)
            tree = self._tree(c, rev.root)
            call_args = _wire({"args": request.args, "kwargs": request.kwargs})
            policy = {
                "max_attempts": 1,
                "restart": "none",
                "timeout_s": 3600,
                "cancel_previous": False,
                "reuse": True,
                "priority": 0,
                "merge": True,
                **request.policy,
            }
            if policy["restart"] not in ("none", "checkpoint"):
                raise InvalidError("restart must be none or checkpoint")
            if not isinstance(policy["merge"], bool):
                raise InvalidError("merge must be a boolean")
            resources = _wire(request.resources)
            fp = self._fingerprint(tree, name, call_args, rev.release_id)
            key = sha256(canonical_json([name, fp, resources]))
            existing = [
                j
                for j in self._jobs_where(
                    c,
                    "case_id = ? AND key = ? AND status IN"
                    " ('queued', 'assigned', 'running')",
                    (case_id, key),
                )
                if not j.cancel_requested
            ]
            if existing:
                if policy["cancel_previous"]:
                    self._cancel_previous(c, case_id, name, keep=existing[0].id)
                info = existing[0].info()
            else:
                info = self._submit_new(
                    c,
                    principal,
                    case,
                    rev,
                    tree,
                    name,
                    call_args,
                    resources,
                    policy,
                    fp,
                    key,
                    request.depends_on,
                    job_data,
                )
        self._deliver()
        if info.status == "queued":
            self.start_jobs()
        return info

    def _submit_new(
        self,
        c,
        principal,
        case,
        rev,
        tree,
        name,
        call_args,
        resources,
        policy,
        fp,
        key,
        depends_on,
        job_data,
    ):
        if policy["reuse"]:
            done = [
                self._run_row(c, rid)
                for (rid,) in c.execute(
                    "SELECT id FROM run WHERE case_id = ? AND function = ? AND"
                    " fingerprint = ? AND status = 'succeeded' AND"
                    " tip_revision != input_revision ORDER BY id DESC LIMIT 1",
                    (case.id, name, fp),
                )
            ]
            if done:
                run = done[0]
                if policy["cancel_previous"]:
                    self._cancel_previous(c, case.id, name)
                job = self._job(c, run.job_id)
                job.submitted = self._next_submission(c)
                self._save_job(c, job)
                return job.info(reused_run=run.id)
        if policy["cancel_previous"]:
            self._cancel_previous(c, case.id, name)
        now = time.time()
        data = {**self.job_data, **(job_data or {})}
        job_id = c.execute(
            "INSERT INTO job (case_id, user, function, args, kwargs,"
            " input_revision, release_id, fingerprint, key, resources, policy,"
            " depends_on, submitted, status, attempt, commit_seq, started,"
            " cancel_requested, message, run_data, log_bytes, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'queued', 0, 0, 0,"
            " 0, '', ?, 0, ?)",
            (
                case.id,
                principal,
                name,
                orjson.dumps(call_args["args"]),
                orjson.dumps(call_args["kwargs"]),
                rev.id,
                rev.release_id,
                fp,
                key,
                orjson.dumps(resources),
                orjson.dumps(policy),
                orjson.dumps(list(depends_on)),
                self._next_submission(c),
                orjson.dumps(data),
                now,
            ),
        ).lastrowid
        run_id = c.execute(
            "INSERT INTO run (case_id, job_id, function, input_revision,"
            " tip_revision, release_id, fingerprint, status, kept, closed,"
            " created_at) VALUES (?, ?, ?, ?, ?, ?, ?, 'running', 0, 0, ?)",
            (case.id, job_id, name, rev.id, rev.id, rev.release_id, fp, now),
        ).lastrowid
        c.execute("UPDATE job SET run_id = ? WHERE id = ?", (run_id, job_id))
        job = self._job(c, job_id)
        self._job_status(c, job)
        self._run_status(c, self._run_row(c, run_id))
        return job.info()

    def job(self, principal, job_id):
        with self._read() as c:
            job = self._job(c, job_id, principal)
            info = job.info()
            if job.status == "queued":
                # 1 for the next job to be claimed
                order = (-job.policy.get("priority", 0), job.id)
                info.queue_position = 1 + sum(
                    1
                    for j in self._jobs_where(c, "status = 'queued'")
                    if (-j.policy.get("priority", 0), j.id) < order
                )
            elif job.status == "running":
                row = c.execute(
                    "SELECT payload FROM job_event WHERE job_id = ? AND"
                    " kind = 'progress' ORDER BY seq DESC LIMIT 1",
                    (job_id,),
                ).fetchone()
                if row is not None:
                    info.extra["progress"] = orjson.loads(row[0])
            return info

    def cancel(self, principal, job_id):
        with self._write() as c:
            self._cancel_job(
                c, self._job(c, job_id, principal, write=True), "cancelled"
            )
        self._deliver()

    def job_events(self, principal, job_id, after=0):
        with self._read() as c:
            self._job(c, job_id, principal)
            return [
                {"seq": seq, "kind": kind, "payload": orjson.loads(payload)}
                for seq, kind, payload in c.execute(
                    "SELECT seq, kind, payload FROM job_event WHERE job_id = ?"
                    " AND seq > ? ORDER BY seq",
                    (job_id, after),
                )
            ]

    def runs_of(self, principal, case_id, function):
        with self._read() as c:
            case = self._case(c, case_id, principal)
            head = self._rev(c, case.head)
            tree = self._tree(c, head.root)
            ids = [
                r
                for (r,) in c.execute(
                    "SELECT id FROM run WHERE case_id = ? AND (? IS NULL OR"
                    " function = ?) ORDER BY id",
                    (case_id, function, function),
                )
            ]
            out = []
            for run_id in ids:
                run = self._run_row(c, run_id)
                job = self._job(c, run.job_id)
                run.created_at, run.started_at, run.finished_at = c.execute(
                    "SELECT r.created_at, j.started_at, j.finished_at FROM run r"
                    " JOIN job j ON j.id = r.job_id WHERE r.id = ?",
                    (run_id,),
                ).fetchone()
                current = self._fingerprint(
                    tree,
                    run.function,
                    {"args": job.args, "kwargs": job.kwargs},
                    head.release_id,
                )
                out.append(
                    run.info(
                        outdated=current != run.fingerprint,
                        job_status=job.status,
                        attempt=job.attempt,
                    )
                )
            return out

    def run_changes(self, principal, run_id, from_rev=None, to_rev=None):
        with self._read() as c:
            run = self._run(c, run_id, principal)
            start, tip = run.input_revision, run.tip_revision
            a = self._rev(c, start if from_rev is None else from_rev)
            b = self._rev(c, tip if to_rev is None else to_rev)
            on_branch = all(
                r is not None and (r.id == start or r.run_id == run.id)
                for r in (a, b)
            )
            rev = b if on_branch else None
            while rev is not None and rev.id not in (a.id, start):
                rev = (
                    self._rev(c, rev.parent) if rev.parent is not None else None
                )
            if rev is None or rev.id != a.id:
                raise BaseGoneError(
                    "the revision is not on the run's branch", tip=tip
                )
            return _diff_ops(
                self._tree(c, a.root).values, self._tree(c, b.root).values
            )

    def keep(self, principal, run_id, kept=True):
        with self._write() as c:
            run = self._run(c, run_id, principal, write=True)
            if run.kept != kept:
                run.kept = kept
                self._save_run(c, run)
                self._run_status(c, run)
        self._deliver()

    def _blob_hashes(self, values) -> set:
        hashes = set()
        for value in values:
            items = value.items if isinstance(value, Seq) else (value,)
            for item in items:
                hashes |= {r.hash for r in iter_blob_refs(item)}
        return hashes

    def _create_from(self, c, principal, app_id, state, keys, release_id, kind):
        """New case with the flat state as its first revision"""
        case = self._insert_case(c, principal, app_id)
        ops = _diff_ops({}, state)
        tree = self._build(c, self._empty, state, keys, ops)
        rev = self._new_revision(
            c,
            case.id,
            None,
            tree,
            ops,
            kind=kind,
            name=None,
            author=principal,
            release_id=release_id,
        )
        self._link_blobs(c, case.id, self._blob_hashes(state.values()))
        self._after_commit(c, case, rev, None, kind, principal, tree)
        self._emit(
            c, f"user:{principal}", "cases.changed", {"case_id": case.id}
        )
        return case

    def copy_case(self, principal, case_id, revision, run_id, name):
        with self._write() as c:
            src = self._case(c, case_id, principal)
            if run_id is not None:
                if revision is not None:
                    raise InvalidError("give either a revision or a run")
                run = self._run_row(c, run_id)
                if run is None or run.case_id != src.id:
                    raise NotFoundError(f"run {run_id}")
                revision = run.tip_revision
            revision = src.head if revision is None else revision
            rev = self._rev(c, revision)
            if rev is None or rev.case_id != src.id:
                raise NotFoundError(f"revision {revision}")
            name = src.name if name is None else name
            tree = self._tree(c, rev.root)
            for h in self._blob_hashes(tree.values.values()):
                c.execute(
                    "INSERT OR IGNORE INTO blob (scope, hash, size, enc, state,"
                    " created_at) SELECT ?, hash, size, enc, state, ? FROM blob"
                    " WHERE scope = ? AND hash = ?",
                    (principal, time.time(), src.owner, h),
                )
            state, keys = dict(tree.values), dict(tree.keys)
            state[CASE_NAME], keys[CASE_NAME] = name, stored_key(name)
            case = self._create_from(
                c, principal, src.app_id, state, keys, rev.release_id, "import"
            )
            if run_id is not None and run.status == "succeeded":
                self._copy_run(c, run, case.id)
            info = self._info(c, case, principal)
        self._deliver()
        return info

    def _copy_run(self, c, src, case_id):
        """The run a case was copied from as a finished run of the copy, with
        the fingerprint of the copy's first revision"""
        head = self._rev(c, self._case_row(c, case_id).head)
        job = self._job(c, src.job_id)
        fp = self._fingerprint(
            self._tree(c, head.root),
            src.function,
            {"args": job.args, "kwargs": job.kwargs},
            head.release_id,
        )
        job_id = c.execute(
            "INSERT INTO job (case_id, user, function, args, kwargs,"
            " input_revision, release_id, fingerprint, key, resources, policy,"
            " depends_on, submitted, status, attempt, commit_seq, started,"
            " cancel_requested, message, exit_code, run_data, log_bytes,"
            " created_at, started_at, finished_at) SELECT ?, c.owner, j.function,"
            " j.args, j.kwargs, ?, ?, ?, ?, j.resources, j.policy, '[]',"
            " j.submitted, 'succeeded', j.attempt, 0, j.started, 0, ?,"
            " j.exit_code, '{}', 0, j.created_at, j.started_at, j.finished_at"
            " FROM job j, cases c WHERE j.id = ? AND c.id = ?",
            (
                case_id,
                head.id,
                head.release_id,
                fp,
                f"copy:{src.id}",
                f"copy of run {src.id} of case {src.case_id}",
                src.job_id,
                case_id,
            ),
        ).lastrowid
        run_id = c.execute(
            "INSERT INTO run (case_id, job_id, function, input_revision,"
            " tip_revision, release_id, fingerprint, status, kept, closed,"
            " created_at) SELECT ?, ?, function, ?, ?, ?, ?, 'succeeded', 0, 1,"
            " created_at FROM run WHERE id = ?",
            (case_id, job_id, head.id, head.id, head.release_id, fp, src.id),
        ).lastrowid
        c.execute("UPDATE job SET run_id = ? WHERE id = ?", (run_id, job_id))

    # -- export and import of cases --

    def export_case(self, principal, case_id) -> tuple[dict, dict]:
        """Head state and the latest succeeded run with data of every function
        whose jobs do not merge into the case, with the blobs they reference:
        (data, {hash: enc})"""
        with self._read() as c:
            case = self._case(c, case_id, principal)
            head = self._rev(c, case.head)
            tree = self._tree(c, head.root)
            runs = []
            hashes = self._blob_hashes(tree.values.values())
            for function, run_id in c.execute(
                "SELECT function, max(id) FROM run WHERE case_id = ?"
                " AND status = 'succeeded' AND tip_revision <> input_revision"
                " GROUP BY function ORDER BY function",
                (case_id,),
            ).fetchall():
                run = self._run_row(c, run_id)
                job = self._job(c, run.job_id)
                if job.policy.get("merge", True):
                    continue  # its results are in the case
                start = self._tree(c, self._rev(c, run.input_revision).root)
                tip = self._tree(c, self._rev(c, run.tip_revision).root)
                ops = _diff_ops(start.values, tip.values)
                hashes |= self._blob_hashes(
                    op.value for op in ops if op.op != "delete"
                )
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
            encs = {
                h: enc
                for h, enc in c.execute(
                    "SELECT hash, enc FROM blob WHERE scope = ?", (case.owner,)
                )
                if h in hashes
            }
            data = {
                "app_id": case.app_id,
                "name": case.name,
                "release_id": head.release_id,
                "state": materialize(tree.values)["children"],
                "runs": runs,
            }
        return _wire(data), encs

    def import_case(
        self, principal, data: dict, read_blob, *, app_id=None
    ) -> int:
        """Create a case from exported data; read_blob(hash) returns the bytes
        of a referenced blob or None; the exported runs become succeeded runs
        on branches of the new case's first revision"""
        from .tree import flatten

        state = flatten({"children": data.get("state") or {}})
        hashes = self._blob_hashes(state.values())
        run_ops = []
        for run in data.get("runs") or []:
            ops = [Op.from_json(op) for op in run.get("ops") or []]
            self._validate_ops(ops)
            run_ops.append((run, ops))
            hashes |= self._blob_hashes(
                op.value for op in ops if op.op != "delete"
            )
        missing, stored = [], {}
        for h in sorted(hashes):
            content = read_blob(h)
            if content is None:
                missing.append(h)
                continue
            stored[h] = self._store_bytes(content, h)[1]
        if missing:
            raise MissingBlobsError(missing, f"the file lacks blobs {missing}")
        encs = data.get("blobs") or {}
        keys = {p: stored_key(v) for p, v in state.items()}
        with self._write() as c:
            for h, size in stored.items():
                self._put_blob(c, principal, h, size, encs.get(h, "bytes"))
            case = self._create_from(
                c,
                principal,
                data.get("app_id", 0) if app_id is None else app_id,
                state,
                keys,
                data.get("release_id"),
                "import",
            )
            base = self._rev(c, case.head)
            T = self._tree(c, base.root)
            for run, ops in run_ops:
                self._import_run(c, principal, case, base, T, run, ops)
            self._link_blobs(c, case.id, hashes)
        self._deliver()
        return case.id

    def _import_run(self, c, principal, case, base, T, run, ops):
        function = run["function"]
        now = time.time()
        job_id = c.execute(
            "INSERT INTO job (case_id, user, function, args, kwargs,"
            " input_revision, release_id, fingerprint, key, resources, policy,"
            " depends_on, submitted, status, attempt, commit_seq, started,"
            " cancel_requested, message, exit_code, run_data, log_bytes,"
            " created_at, finished_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, '{}',"
            " '{\"merge\": false}', '[]', ?, 'succeeded', 0, 0, 1, 0, ?, 0, '{}',"
            " 0, ?, ?)",
            (
                case.id,
                principal,
                function,
                orjson.dumps(run.get("args") or []),
                orjson.dumps(run.get("kwargs") or {}),
                base.id,
                run.get("release_id"),
                run.get("fingerprint") or "",
                f"imported:{case.id}:{function}",
                self._next_submission(c),
                run.get("message") or "imported",
                now,
                now,
            ),
        ).lastrowid
        state, keys, effective = _merge(
            T.values, T.keys, T.values, T.keys, [], ops
        )
        tree = self._build(c, T, state, keys, effective)
        run_id = c.execute(
            "INSERT INTO run (case_id, job_id, function, input_revision,"
            " tip_revision, release_id, fingerprint, status, kept, closed,"
            " created_at) VALUES (?, ?, ?, ?, ?, ?, ?, 'succeeded', 0, 1, ?)",
            (
                case.id,
                job_id,
                function,
                base.id,
                base.id,
                run.get("release_id"),
                run.get("fingerprint") or "",
                now,
            ),
        ).lastrowid
        tip = self._new_revision(
            c,
            case.id,
            base.id,
            tree,
            effective,
            kind="import",
            name=None,
            author=f"job:{job_id}",
            release_id=run.get("release_id"),
            run_id=run_id,
        )
        c.execute("UPDATE job SET run_id = ? WHERE id = ?", (run_id, job_id))
        c.execute("UPDATE run SET tip_revision = ? WHERE id = ?", (tip, run_id))

    # -- jobs (runner and job side) --

    def _claimable(self, c) -> list[_Job]:
        jobs = []
        for job in self._jobs_where(c, "status = 'queued'"):
            deps = [self._jobs_where(c, "id = ?", (d,)) for d in job.depends_on]
            if all(not d or d[0].status == "succeeded" for d in deps):
                jobs.append(job)
        return jobs

    def claim(self, job_id=None, *, runner=None, limit=None) -> dict | None:
        """Assign the next queued job (or the given one) as a new attempt;
        returns what the runner passes to the job process. With limit, only if
        fewer jobs are assigned or running."""
        with self._write() as c:
            if limit is not None:
                active = c.execute(
                    "SELECT COUNT(*) FROM job WHERE status IN ('assigned', 'running')"
                ).fetchone()[0]
                if active >= limit:
                    return None
            queued = [j for j in self._claimable(c) if job_id in (None, j.id)]
            if not queued:
                return None
            job = min(
                queued, key=lambda j: (-j.policy.get("priority", 0), j.id)
            )
            job.attempt += 1
            job.status, job.commit_seq = "assigned", 0
            self._save_job(c, job, runner=runner)
            self._job_status(c, job)
            run_data = orjson.loads(
                c.execute(
                    "SELECT run_data FROM job WHERE id = ?", (job.id,)
                ).fetchone()[0]
                or b"{}"
            )
            data = {
                **run_data,
                "job_id": job.id,
                "attempt": job.attempt,
                "case_id": job.case_id,
                "function": job.function,
                "args": list(job.args),
                "kwargs": dict(job.kwargs),
                "release_id": job.release_id,
                "input_revision": job.input_revision,
                "restart": job.policy["restart"],
                "timeout": job.policy.get("timeout_s"),
            }
        self._deliver()
        return _wire(data)

    def job_client(self, job_id: int, attempt: int) -> "SQLiteJobClient":
        return SQLiteJobClient(self, job_id, attempt)

    def _active_job(self, c, job_id, attempt) -> _Job:
        job = self._job(c, job_id)
        case = self._case_row(c, job.case_id)
        if case.deleted:
            raise CaseDeletedError(f"case {case.id} was deleted")
        if job.attempt != attempt or job.status not in ("assigned", "running"):
            raise StaleAttemptError("the attempt is no longer active")
        return job

    def _started(self, c, job: _Job):
        if job.status == "assigned":
            job.status, job.started = "running", True
            self._save_job(c, job, started_at=time.time())
            self._job_status(c, job)

    def heartbeat(self, job_id: int, attempt: int) -> dict:
        """Runner heartbeat of a job: marks it running, returns the cancel flag"""
        with self._write() as c:
            job = self._active_job(c, job_id, attempt)
            self._started(c, job)
            cancel = job.cancel_requested
        self._deliver()
        return {"cancel": cancel}

    def cancel_requested(self, job_id: int, attempt: int) -> bool:
        """Cancel flag of an active attempt (a read, unlike heartbeat)"""
        with self._read() as c:
            return self._active_job(c, job_id, attempt).cancel_requested

    def job_input(self, job_id: int, attempt: int) -> dict:
        with self._read() as c:
            job = self._active_job(c, job_id, attempt)
            run = self._run_row(c, job.run_id)
            rev = self._rev(c, job.input_revision)
            tree = self._tree(c, rev.root)
            body = {
                "job_id": job.id,
                "attempt": job.attempt,
                "case_id": job.case_id,
                "function": job.function,
                "args": list(job.args),
                "kwargs": dict(job.kwargs),
                "release_id": job.release_id,
                "input_revision": rev.id,
                "run_id": run.id,
                "commit_seq": job.commit_seq,
                "state": materialize(tree.values)["children"],
                "checkpoint": None,
            }
            if (
                job.policy["restart"] == "checkpoint"
                and run.tip_revision != rev.id
            ):
                tip = self._rev_tree(c, run.tip_revision)
                body["checkpoint"] = {
                    "revision": run.tip_revision,
                    "ops": [
                        op.to_json()
                        for op in _diff_ops(tree.values, tip.values)
                    ],
                }
            return _wire(body)

    def job_blobs_missing(self, job_id, attempt, refs, session_id=None):
        with self._write() as c:
            job = self._active_job(c, job_id, attempt)
            case = self._case_row(c, job.case_id)
            principal = f"job:{job.id}:{attempt}"
            session = self._session_row(c, session_id) if session_id else None
            if session is None or session[0] != principal:
                session_id = self._new_session(c, principal, case.owner)
            missing = self._missing(
                c,
                case.owner,
                session_id,
                refs,
                lambda h: self._case_has(c, case.id, h)
                or self._in_sessions(c, principal, case.owner, h),
            )
            return {"missing": missing, "upload_session": session_id}

    def job_read_blob(self, job_id, attempt, ref, byte_range=None):
        with self._read() as c:
            job = self._active_job(c, job_id, attempt)
            case = self._case_row(c, job.case_id)
            visible = self._case_has(c, case.id, ref.hash) or self._in_sessions(
                c, f"job:{job.id}:{job.attempt}", case.owner, ref.hash
            )
            if not visible or self._blob_state(c, case.owner, ref.hash) in (
                None,
                "quarantined",
            ):
                raise NotFoundError(f"blob {ref.hash}")
        return self._read_bytes(ref.hash, byte_range)

    def _job_case_line(self, c, case: _CaseRow, job: _Job, ops, final):
        """Writes of a job with policy merge onto the head, except paths a user
        changed since the job's input revision, paths written by
        later-submitted jobs and writes into deleted components"""
        if not job.policy.get("merge", True):
            return None, []
        ui = [op for op in ops if is_value_path(op.path)]
        if not ui:
            return None, []
        head = self._rev(c, case.head)
        if (
            job.release_id is not None
            and head.release_id is not None
            and job.release_id < head.release_id
        ):
            return None, [list(op.path) for op in ui]
        H = self._tree(c, head.root)
        blocked, deleted = {}, set()
        for author, data in c.execute(
            "SELECT author, ops FROM revision WHERE case_id = ? AND run_id IS NULL"
            " AND id > ? ORDER BY id",
            (case.id, job.input_revision),
        ).fetchall():
            kind, _, ident = author.partition(":")
            by_user = kind != "job"
            if not by_user and int(ident) <= job.id:
                continue
            for op in orjson.loads(data):
                path = tuple(op["path"])
                if not is_value_path(path):
                    if by_user and op["op"] == "delete":
                        deleted.add(path)
                    continue
                mode = "append" if op["op"] == "append" else "write"
                if blocked.get(path) != "write":
                    blocked[path] = mode
        kept, dropped = [], []
        for op in ui:
            other = blocked.get(op.path)
            comp = op.path[:-2]
            gone = any(
                comp[:i] in deleted and comp[:i] not in H.comps
                for i in range(1, len(comp) + 1)
            )
            if (
                gone
                or other == "write"
                or (other == "append" and op.op != "append")
            ):
                dropped.append(list(op.path))
            else:
                kept.append(op)
        if not kept:
            return None, dropped
        state, keys, effective = _merge(
            H.values, H.keys, H.values, H.keys, [], kept
        )
        if not effective:
            return None, dropped
        author = f"job:{job.id}"
        kind = "job_result" if final else "job_checkpoint"
        tree = self._build(c, H, state, keys, effective)
        rev = self._new_revision(
            c,
            case.id,
            head.id,
            tree,
            effective,
            kind=kind,
            name=None,
            author=author,
            release_id=head.release_id,
        )
        self._after_commit(c, case, rev, head.id, kind, author, tree)
        return rev, dropped

    def _check_job_blobs(self, c, case, job, ops, session_id):
        refs = {}
        for op in ops:
            if op.op != "delete":
                for ref in iter_blob_refs(op.value):
                    refs[ref.hash] = ref
        if not refs:
            return set()
        missing = [
            h
            for h in refs
            if self._blob_state(c, case.owner, h) in (None, "quarantined")
        ]
        if missing:
            raise MissingBlobsError(sorted(missing))
        principal = f"job:{job.id}:{job.attempt}"
        foreign = [
            h
            for h in refs
            if not self._case_has(c, case.id, h)
            and not self._in_sessions(c, principal, case.owner, h)
        ]
        if foreign:
            raise PossessionError(sorted(foreign))
        return set(refs)

    def job_commit(self, job_id, attempt, seq, final, ops, upload_session=None):
        """Checkpoint or final commit of a job attempt onto its run branch;
        ui and slots operations also onto the case line"""
        ops = list(ops)
        self._validate_ops(ops)
        with self._write() as c:
            row = c.execute(
                "SELECT result FROM job_result WHERE job_id = ? AND attempt = ?"
                " AND seq = ?",
                (job_id, attempt, seq),
            ).fetchone()
            if row is not None:
                return orjson.loads(row[0])
            job = self._active_job(c, job_id, attempt)
            if job.cancel_requested:
                raise JobCancelledError(job.message or "the job was cancelled")
            if seq <= job.commit_seq:
                raise ConflictError([], "seq must exceed the last accepted one")
            run = self._run_row(c, job.run_id)
            if run.closed:
                raise ConflictError(
                    [], "the run branch was closed by a final commit"
                )
            case = self._case_row(c, job.case_id)
            refs = self._check_job_blobs(c, case, job, ops, upload_session)
            tip = self._rev(c, run.tip_revision)
            T = self._tree(c, tip.root)
            state, keys, effective = _merge(
                T.values, T.keys, T.values, T.keys, [], ops
            )
            branch = None
            if effective or final:
                tree = self._build(c, T, state, keys, effective)
                branch = self._new_revision(
                    c,
                    case.id,
                    tip.id,
                    tree,
                    effective,
                    kind="job_result" if final else "job_checkpoint",
                    name=None,
                    author=f"job:{job.id}",
                    release_id=job.release_id,
                    run_id=run.id,
                )
                run.tip_revision, run.closed = branch, final
                self._save_run(c, run)
            self._link_blobs(c, case.id, refs)
            case_rev, dropped = self._job_case_line(c, case, job, ops, final)
            job.commit_seq = seq
            self._save_job(c, job)
            self._started(c, job)
            if branch is not None:
                self._run_status(c, run)
            result = {
                "seq": seq,
                "final": final,
                "revision": run.tip_revision,
                "case_revision": case_rev,
                "head": case.head,
                "dropped": dropped,
            }
            c.execute(
                "INSERT INTO job_result (job_id, attempt, seq, result)"
                " VALUES (?, ?, ?, ?)",
                (job_id, attempt, seq, orjson.dumps(result)),
            )
        self._deliver()
        return _wire(result)

    def _job_event(self, c, job_id, kind, payload):
        seq = c.execute(
            "SELECT COALESCE(MAX(seq), 0) + 1 FROM job_event WHERE job_id = ?",
            (job_id,),
        ).fetchone()[0]
        c.execute(
            "INSERT INTO job_event (job_id, seq, kind, payload, created_at)"
            " VALUES (?, ?, ?, ?, ?)",
            (job_id, seq, kind, orjson.dumps(payload), time.time()),
        )

    def job_event(self, job_id, attempt, kind, payload):
        with self._write() as c:
            job = self._active_job(c, job_id, attempt)
            if kind == "progress":
                payload = {
                    "fraction": payload.get("fraction"),
                    "text": str(payload.get("text") or ""),
                }
                self._emit(
                    c,
                    f"case:{job.case_id}",
                    "job.progress",
                    {"case_id": job.case_id, "job_id": job.id, **payload},
                )
            self._job_event(c, job.id, kind, {**payload, "attempt": attempt})
        self._deliver()
        return {}

    def job_log(self, job_id, attempt, stream: str, data: str):
        """Output of the job process (runner side), at most 10 MB per job"""
        with self._write() as c:
            row = c.execute(
                "SELECT log_bytes FROM job WHERE id = ?", (job_id,)
            ).fetchone()
            if row is None:
                raise NotFoundError(f"job {job_id}")
            size = len(data.encode())
            if row[0] + size > LOG_LIMIT:
                return
            c.execute(
                "UPDATE job SET log_bytes = log_bytes + ? WHERE id = ?",
                (size, job_id),
            )
            self._job_event(
                c,
                job_id,
                "log",
                {"stream": stream, "data": data, "attempt": attempt},
            )

    def _end(self, c, job: _Job, status, message="", exit_code=None):
        job.status, job.message, job.exit_code = status, message, exit_code
        self._save_job(c, job, finished_at=time.time())
        self._job_status(c, job, message)
        run = self._run_row(c, job.run_id)
        run.status = {"timed_out": "failed"}.get(status, status)
        self._save_run(c, run)
        self._run_status(c, run)

    def _requeue(self, c, job: _Job, reason):
        job.status, job.message, job.commit_seq = "queued", reason, 0
        run = self._run_row(c, job.run_id)
        if (
            job.started
            and job.policy["restart"] == "none"
            and run.tip_revision != run.input_revision
        ):
            run.tip_revision = run.input_revision
            self._save_run(c, run)
            self._run_status(c, run)
        job.started = False
        self._save_job(c, job, runner=None)
        self._job_status(c, job, reason)

    def finish(self, job_id, attempt, status, exit_code=None, message=""):
        """End of an attempt reported by the runner; the server decides"""
        with self._write() as c:
            job = self._job(c, job_id)
            if job.attempt != attempt or job.status not in (
                "assigned",
                "running",
            ):
                raise StaleAttemptError("the attempt is no longer active")
            run = self._run_row(c, job.run_id)
            if job.cancel_requested:
                status, message = "cancelled", job.message or "cancelled"
            elif run.closed:
                if status != "succeeded" or exit_code:
                    message = f"{message or status} after the final commit"
                status = "succeeded"
            elif status == "succeeded":
                status = "failed"
                message = message or (
                    f"exit code {exit_code}"
                    if exit_code
                    else "the job ended without a final commit"
                )
            if (
                status == "failed"
                and job.started
                and attempt < job.policy["max_attempts"]
            ):
                self._requeue(c, job, f"attempt {attempt} failed: {message}")
            else:
                self._end(c, job, status, message, exit_code)
            answer = {"status": job.status}
        self._deliver()
        return answer

    def expire(self, job_id):
        """The attempt's runner is gone (the local form of a lease expiry)"""
        with self._write() as c:
            job = self._job(c, job_id)
            if job.status not in ("assigned", "running"):
                return job.status
            run = self._run_row(c, job.run_id)
            reason = "runner lost"
            if job.cancel_requested:
                self._end(c, job, "cancelled", job.message or "cancelled")
            elif run.closed:
                self._end(
                    c, job, "succeeded", f"{reason} after the final commit"
                )
            elif not job.started or job.attempt < job.policy["max_attempts"]:
                self._requeue(c, job, reason)
            else:
                self._end(c, job, "failed", reason)
            status = job.status
        self._deliver()
        return status

    # -- local runners --

    def recover(self) -> list[int]:
        """End the attempts whose runner process is gone"""
        with self._read() as c:
            rows = c.execute(
                "SELECT id, runner FROM job WHERE status IN ('assigned', 'running')"
                " AND runner IS NOT NULL"
            ).fetchall()
        lost = [job_id for job_id, runner in rows if not process_alive(runner)]
        for job_id in lost:
            self.expire(job_id)
        return lost

    def pending_jobs(self) -> tuple[int, int]:
        """Claimable queued jobs and jobs assigned or running"""
        with self._read() as c:
            active = c.execute(
                "SELECT COUNT(*) FROM job WHERE status IN ('assigned', 'running')"
            ).fetchone()[0]
            return len(self._claimable(c)), active

    def start_jobs(self):
        """Start a local runner if jobs wait and the limit allows (jobs
        option); called after submissions and when a case is opened"""
        if self.jobs is None:
            return
        from .local_jobs import spawn_runner

        self.recover()
        queued, active = self.pending_jobs()
        if not queued or active >= self.max_jobs:
            return
        spawn_runner(self.path, self.max_jobs)


class SQLiteStore:
    """CaseStore of one principal on a SQLiteServer"""

    def __init__(
        self, server: SQLiteServer, user: str, release_id: int | None = None
    ):
        self.server = server
        self.user = user
        self.release_id = release_id

    def create_case(
        self, app_id: int, name: str, ops: list[Op] = ()
    ) -> CaseInfo:
        return self.server.create_case(
            self.user, self.release_id, app_id, name, _wire_ops(ops)
        )

    def case(self, case_id: int) -> CaseInfo:
        return self.server.case(self.user, case_id)

    def state(self, case_id: int, revision: int | None = None) -> dict:
        return _wire(self.server.state(self.user, case_id, revision))

    def changes(self, case_id: int, from_rev: int, to_rev: int) -> list[Op]:
        return _wire_ops(
            self.server.changes(self.user, case_id, from_rev, to_rev)
        )

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
        try:
            result = self.server.commit(
                self.user,
                self.release_id,
                case_id,
                base,
                _wire_ops(ops),
                kind,
                name,
                upload_session,
                idempotency_key,
            )
        except ConflictError as e:
            raise ConflictError(
                [
                    Conflict.from_json(c)
                    for c in _wire([c.to_json() for c in e.conflicts])
                ]
            ) from None
        return CommitResult(
            result.revision, result.head, _wire_ops(result.remote_ops)
        )

    def blobs_missing(
        self, case_id: int, blobs: list[BlobRef]
    ) -> MissingResult:
        return self.server.blobs_missing(self.user, case_id, list(blobs))

    def upload(self, session: str, ref: BlobRef, data: BinaryIO) -> None:
        self.server.upload(self.user, session, ref, data)

    def cases(self, app_id: int | None = None) -> list[CaseInfo]:
        return self.server.cases_of(self.user, app_id)

    def read_blob(
        self,
        case_id: int,
        ref: BlobRef,
        byte_range: tuple[int, int] | None = None,
    ) -> bytes:
        return self.server.read_blob(self.user, case_id, ref, byte_range)

    def submit(self, case_id: int, request: JobRequest) -> JobInfo:
        if request.release_id is None and self.release_id is not None:
            request = dataclasses.replace(request, release_id=self.release_id)
        return self.server.submit(self.user, case_id, request)

    def job(self, job_id: int) -> JobInfo:
        return self.server.job(self.user, job_id)

    def cancel(self, job_id: int) -> None:
        self.server.cancel(self.user, job_id)

    def job_events(self, job_id: int, after: int = 0) -> list[dict]:
        return self.server.job_events(self.user, job_id, after)

    def runs(self, case_id: int, function=None) -> list[RunInfo]:
        return self.server.runs_of(self.user, case_id, function)

    def run_changes(
        self,
        run_id: int,
        from_revision: int | None = None,
        to_revision: int | None = None,
    ) -> list[Op]:
        return _wire_ops(
            self.server.run_changes(
                self.user, run_id, from_revision, to_revision
            )
        )

    def keep(self, run_id: int) -> None:
        self.server.keep(self.user, run_id)

    def copy_case(
        self,
        case_id: int,
        *,
        revision: int | None = None,
        run_id: int | None = None,
        name: str | None = None,
    ) -> CaseInfo:
        return self.server.copy_case(self.user, case_id, revision, run_id, name)

    def subscribe(
        self,
        case_ids: list[int],
        last_seq: int,
        callback: Callable[[Event], None],
    ) -> Callable[[], None]:
        return self.server.subscribe(
            self.user, list(case_ids), last_seq, callback
        )


class SQLiteJobClient:
    """Job side of one attempt on a SQLiteServer (the job process of a local
    runner), with the interface of ngapp.job_client.JobClient: once the server ends
    the attempt, every later request raises JobEndedError"""

    def __init__(self, server: SQLiteServer, job_id: int, attempt: int):
        self.server = server
        self.job_id = job_id
        self.attempt = attempt
        with server._read() as c:
            self.case_id = server._job(c, job_id).case_id
        self.seq = 0
        self.upload_session: str | None = None
        self.ended = None

    @classmethod
    def from_env(cls, env=None) -> "SQLiteJobClient":
        """NGAPP_JOB_DB, NGAPP_JOB_ID and NGAPP_JOB_ATTEMPT of a local runner"""
        env = os.environ if env is None else env
        server = SQLiteServer(env["NGAPP_JOB_DB"], poll_interval=None)
        return cls(
            server, int(env["NGAPP_JOB_ID"]), int(env["NGAPP_JOB_ATTEMPT"])
        )

    def _call(self, fn, *args):
        if self.ended is not None:
            raise type(self.ended)(str(self.ended))
        try:
            return fn(*args)
        except JobEndedError as e:
            self.ended = e
            raise

    def get_input(self) -> dict:
        return self._call(self.server.job_input, self.job_id, self.attempt)

    def commit(self, ops, seq=None, final=False, upload_session=None) -> dict:
        seq = self.seq + 1 if seq is None else seq
        ops = [op if isinstance(op, Op) else Op.from_json(op) for op in ops]
        result = self._call(
            self.server.job_commit,
            self.job_id,
            self.attempt,
            seq,
            final,
            _wire_ops(ops),
            upload_session or self.upload_session,
        )
        self.seq = max(self.seq, seq)
        return result

    def blobs_missing(self, refs: list[BlobRef]) -> dict:
        answer = self._call(
            self.server.job_blobs_missing,
            self.job_id,
            self.attempt,
            list(refs),
            self.upload_session,
        )
        self.upload_session = answer["upload_session"]
        return answer

    def upload(self, data, enc: str = "bytes") -> BlobRef:
        src = Source(data)
        ref = BlobRef(src.hash(), src.size, enc)
        if ref.hash in self.blobs_missing([ref])["missing"]:
            self._call(
                self.server.upload,
                f"job:{self.job_id}:{self.attempt}",
                self.upload_session,
                ref,
                src,
            )
        return ref

    def read_blob(self, ref: BlobRef, byte_range=None) -> bytes:
        return self._call(
            self.server.job_read_blob,
            self.job_id,
            self.attempt,
            ref,
            byte_range,
        )

    def progress(self, fraction=None, text=None):
        return self._call(
            self.server.job_event,
            self.job_id,
            self.attempt,
            "progress",
            {"fraction": fraction, "text": text},
        )

    def message(self, text: str, level: str = "info"):
        return self._call(
            self.server.job_event,
            self.job_id,
            self.attempt,
            "message",
            {"text": text, "level": level},
        )
