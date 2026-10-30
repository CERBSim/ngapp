"""State paths and the flat and materialised forms of a state

A flat state maps paths (tuples of segments) to stored values or Seq. The
materialised state mirrors the node layout of the server:

    {"revision": 7, "release": 41,
     "children": {"mesher": {"input": {"maxh": 0.1},
                             "state": {"lines": {"$seq": ["a", "b"]}},
                             "children": {...}},
                  "__case__": {"meta": {"name": "Case 1"}}}}
"""

from .encoding import sha256, value_key
from .types import Path

SECTIONS = ("ui", "input", "state", "slots")
APP_PATH = ("__app__",)
CASE_PATH = ("__case__",)
CASE_NAME = ("__case__", "meta", "name")


def is_value_path(path: Path) -> bool:
    if len(path) < 3:
        return False
    if path[-2] in SECTIONS:
        return True
    return len(path) == 3 and path[:2] == ("__case__", "meta")


def is_under(path: Path, prefix: Path) -> bool:
    return path[: len(prefix)] == prefix


class Seq:
    """Stored sequence (state.list); items are stored values"""

    __slots__ = ("items", "keys", "_key")

    def __init__(self, items=(), keys=None):
        self.items = tuple(items)
        self.keys = (
            tuple(keys)
            if keys is not None
            else tuple(value_key(v) for v in self.items)
        )
        self._key = None

    def appended(self, value, key=None) -> "Seq":
        return Seq(
            self.items + (value,), self.keys + (key or value_key(value),)
        )

    @property
    def key(self) -> str:
        if self._key is None:
            self._key = "seq:" + sha256("\n".join(self.keys).encode())
        return self._key

    def to_json(self) -> dict:
        return {"$seq": list(self.items)}

    def __len__(self):
        return len(self.items)


class _Absent:
    def __repr__(self):
        return "ABSENT"

    def __bool__(self):
        return False


ABSENT = _Absent()


def stored_key(value) -> str | None:
    """Content key of a stored value or Seq, None for ABSENT"""
    if value is ABSENT:
        return None
    if isinstance(value, Seq):
        return value.key
    return value_key(value)


def flatten(materialized: dict) -> dict:
    flat = {}

    def walk(node, prefix):
        for k, v in node.items():
            if k == "children":
                for cid, child in v.items():
                    walk(child, prefix + (cid,))
            elif k in SECTIONS or (k == "meta" and prefix == CASE_PATH):
                for key, value in v.items():
                    if isinstance(value, dict) and "$seq" in value:
                        value = Seq(value["$seq"])
                    flat[prefix + (k, key)] = value

    walk({"children": materialized.get("children", {})}, ())
    return flat


def materialize(flat: dict, **root) -> dict:
    out = dict(root)
    out["children"] = {}
    for path in sorted(flat):
        value = flat[path]
        node = out
        for seg in path[:-2]:
            node = node.setdefault("children", {}).setdefault(seg, {})
        node.setdefault(path[-2], {})[path[-1]] = (
            value.to_json() if isinstance(value, Seq) else value
        )
    return out
