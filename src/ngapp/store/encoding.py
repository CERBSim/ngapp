"""Value encoding of the state tree

Python values are encoded once into their stored JSON form:

- JSON values as is, user keys starting with ``$`` escaped by doubling it,
- bytes, npy arrays and pickles up to the inline limit as
  ``{"$bytes": <base64>, "enc": ...}``, above it as blob references
  ``{"$blob": "sha256:...", "size": n, "enc": ...}``,
- numpy arrays above the artifact limit as ``ngapp.array/1`` artifacts.

Values are compared by their content key, never with ``==``. The content key
does not depend on whether a value is stored inline or as a blob.
"""

import base64
import functools
import hashlib
import io
import json.encoder
import math
import pickle as pickle_module
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Callable

import numpy as np
import orjson

from .types import BlobRef

INLINE_LIMIT = 32 * 1024
NODE_LIMIT = 64 * 1024
ARTIFACT_LIMIT = 32 * 1024 * 1024
CHUNK_BYTES = 8 * 1024 * 1024
MIN_CHUNK_BYTES = 1024 * 1024

ARRAY_ARTIFACT = "ngapp.array/1"
CHUNK_ENCODING = "artifact-chunk"

_encode_string = json.encoder.encode_basestring


def sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def escape_key(key: str) -> str:
    return "$" + key if key.startswith("$") else key


def unescape_key(key: str) -> str:
    return key[1:] if key.startswith("$$") else key


def _number(x: float) -> str:
    """ECMAScript Number::toString, as required by RFC 8785"""
    if math.isnan(x) or math.isinf(x):
        raise ValueError(f"{x} is not a valid JSON number")
    if x == 0:
        return "0"
    r = repr(x)
    if "e" not in r and "E" not in r:
        return r[:-2] if r.endswith(".0") else r
    sign = "-" if x < 0 else ""
    _, digits, exponent = Decimal(r.lstrip("-")).as_tuple()
    digits = "".join(map(str, digits))
    stripped = digits.rstrip("0")
    exponent += len(digits) - len(stripped)
    digits = stripped
    k = len(digits)
    n = exponent + k
    if k <= n <= 21:
        s = digits + "0" * (n - k)
    elif 0 < n <= 21:
        s = digits[:n] + "." + digits[n:]
    elif -6 < n <= 0:
        s = "0." + "0" * (-n) + digits
    else:
        e = n - 1
        mantissa = digits if k == 1 else digits[0] + "." + digits[1:]
        s = mantissa + "e" + ("+" if e >= 0 else "-") + str(abs(e))
    return sign + s


def _utf16(key: str) -> bytes:
    return key.encode("utf-16-be")


def _canonical(value, out: list):
    if value is None:
        out.append("null")
    elif value is True:
        out.append("true")
    elif value is False:
        out.append("false")
    elif isinstance(value, str):
        out.append(_encode_string(value))
    elif isinstance(value, int):
        out.append(str(int(value)))
    elif isinstance(value, float):
        out.append(_number(value))
    elif isinstance(value, dict):
        for key in value:
            if not isinstance(key, str):
                raise TypeError(
                    f"JSON object keys must be strings, got {key!r}"
                )
        out.append("{")
        first = True
        for key in sorted(value, key=_utf16):
            if not first:
                out.append(",")
            first = False
            out.append(_encode_string(key))
            out.append(":")
            _canonical(value[key], out)
        out.append("}")
    elif isinstance(value, (list, tuple)):
        out.append("[")
        for i, item in enumerate(value):
            if i:
                out.append(",")
            _canonical(item, out)
        out.append("]")
    else:
        raise TypeError(f"{type(value).__name__} is not a JSON value")


def canonical_json(value) -> bytes:
    """Canonical JSON (RFC 8785) of a JSON value"""
    out = []
    _canonical(value, out)
    return "".join(out).encode("utf-8")


def value_key(stored) -> str:
    """Content key of a stored value: encoding and hash of the content"""
    if isinstance(stored, dict):
        if "$blob" in stored:
            return f"{stored.get('enc', 'bytes')}:{stored['$blob']}"
        if "$bytes" in stored:
            data = base64.b64decode(stored["$bytes"])
            return f"{stored.get('enc', 'bytes')}:{sha256(data)}"
    return "json:" + sha256(canonical_json(stored))


def iter_blob_refs(stored):
    """Blob references inside a stored value, including artifact chunks"""
    if isinstance(stored, dict):
        if "$blob" in stored:
            yield BlobRef(
                stored["$blob"], stored.get("size"), stored.get("enc", "bytes")
            )
            return
        if "$artifact" in stored:
            for chunk in stored.get("chunks", []):
                yield BlobRef(chunk, None, CHUNK_ENCODING)
        for v in stored.values():
            if isinstance(v, (dict, list)):
                yield from iter_blob_refs(v)
    elif isinstance(stored, list):
        for v in stored:
            if isinstance(v, (dict, list)):
                yield from iter_blob_refs(v)


@dataclass
class EncodedValue:
    """A value in its stored form, with the blobs it needs uploaded"""

    stored: Any
    key: str
    blobs: dict[str, tuple[BlobRef, bytes]] = field(default_factory=dict)
    large: bool = False


def _bytes_form(data: bytes, enc: str, lazy, inline_limit, blobs) -> tuple:
    """Stored form of encoded bytes: inline or blob reference"""
    h = sha256(data)
    inline = len(data) <= inline_limit if lazy is None else not lazy
    if inline:
        if len(data) > NODE_LIMIT:
            raise ValueError(
                f"Value of {len(data)} bytes is too large to be stored inline"
            )
        stored = {"$bytes": base64.b64encode(data).decode("ascii")}
        if enc != "bytes":
            stored["enc"] = enc
        return stored, f"{enc}:{h}", False
    ref = BlobRef(h, len(data), enc)
    blobs[h] = (ref, data)
    return ref.to_json(), f"{enc}:{h}", True


def npy_bytes(array: np.ndarray) -> bytes:
    buf = io.BytesIO()
    np.save(buf, array, allow_pickle=False)
    return buf.getvalue()


def _artifact_dtype(array: np.ndarray):
    if array.dtype.kind not in "biufc" or array.dtype.fields is not None:
        return None
    return array.dtype.newbyteorder("<")


def _to_json(value, blobs, inline_limit):
    if value is None or isinstance(value, (bool, str)):
        return value
    if isinstance(value, int):
        return int(value)
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            raise ValueError(f"{value} cannot be stored as JSON number")
        return float(value)
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            if not isinstance(k, str):
                raise TypeError(
                    f"Cannot encode dict with key {k!r}, keys must be strings "
                    "(use pickle=True)"
                )
            out[escape_key(k)] = _to_json(v, blobs, inline_limit)
        return out
    if isinstance(value, (list, tuple)):
        return [_to_json(v, blobs, inline_limit) for v in value]
    if isinstance(value, np.generic):
        return _to_json(value.item(), blobs, inline_limit)
    if isinstance(value, (bytes, bytearray, memoryview)):
        return _bytes_form(bytes(value), "bytes", None, inline_limit, blobs)[0]
    if isinstance(value, np.ndarray) and value.dtype != object:
        return _bytes_form(npy_bytes(value), "npy", None, inline_limit, blobs)[
            0
        ]
    raise TypeError(
        f"Cannot encode value of type {type(value).__name__} (use pickle=True)"
    )


def encode_value(
    value,
    *,
    pickle: bool = False,
    lazy: bool | None = None,
    inline_limit: int = INLINE_LIMIT,
    artifact_limit: int = ARTIFACT_LIMIT,
    codec: str | None = None,
) -> EncodedValue:
    """Encode a Python value into its stored form

    lazy=None decides by size, True always stores a blob (fetched on first
    access), False always stores inline (up to the node limit).
    """
    blobs = {}
    if pickle:
        data = pickle_module.dumps(value, protocol=5)
        stored, key, large = _bytes_form(
            data, "pickle", lazy, inline_limit, blobs
        )
        return EncodedValue(stored, key, blobs, large)
    if isinstance(value, np.ndarray) and value.dtype != object:
        if (
            lazy is not False
            and value.nbytes > artifact_limit
            and _artifact_dtype(value) is not None
        ):
            manifest, blobs = encode_array_artifact(value, codec=codec)
            return EncodedValue(manifest, value_key(manifest), blobs, True)
        stored, key, large = _bytes_form(
            npy_bytes(value), "npy", lazy, inline_limit, blobs
        )
        return EncodedValue(stored, key, blobs, large)
    if isinstance(value, (bytes, bytearray, memoryview)):
        stored, key, large = _bytes_form(
            bytes(value), "bytes", lazy, inline_limit, blobs
        )
        return EncodedValue(stored, key, blobs, large)
    stored = _to_json(value, blobs, inline_limit)
    data = canonical_json(stored)
    key = "json:" + sha256(data)
    # nested references stay visible to the server, so such values stay inline
    if not blobs and (lazy or (lazy is None and len(data) > inline_limit)):
        ref = BlobRef(key[5:], len(data), "json")
        return EncodedValue(ref.to_json(), key, {ref.hash: (ref, data)}, True)
    if lazy is False and len(data) > NODE_LIMIT:
        raise ValueError(
            f"Value of {len(data)} bytes is too large to be stored inline"
        )
    return EncodedValue(stored, key, blobs, False)


def _from_json(stored, read_blob):
    if isinstance(stored, dict):
        if "$blob" in stored or "$bytes" in stored or "$artifact" in stored:
            return decode_value(stored, read_blob)
        return {
            unescape_key(k): _from_json(v, read_blob) for k, v in stored.items()
        }
    if isinstance(stored, list):
        return [_from_json(v, read_blob) for v in stored]
    return stored


def decode_bytes(data: bytes, enc: str, read_blob=None):
    if enc == "bytes":
        return data
    if enc == "npy":
        return np.load(io.BytesIO(data), allow_pickle=False)
    if enc == "pickle":
        return pickle_module.loads(data)
    if enc == "json":
        return _from_json(orjson.loads(data), read_blob)
    raise ValueError(f"Unknown encoding {enc!r}")


def decode_value(stored, read_blob: Callable[[BlobRef], bytes] | None = None):
    """Decode a stored value; read_blob fetches the bytes of a blob reference"""
    if isinstance(stored, dict):
        if "$blob" in stored:
            ref = BlobRef.from_json(stored)
            if read_blob is None:
                raise RuntimeError(
                    f"Cannot load blob {ref.hash} without a store"
                )
            data = read_blob(ref)
            if sha256(data) != ref.hash:
                raise ValueError(f"Blob {ref.hash} has wrong content")
            return decode_bytes(data, ref.enc, read_blob)
        if "$bytes" in stored:
            data = base64.b64decode(stored["$bytes"])
            return decode_bytes(data, stored.get("enc", "bytes"), read_blob)
        if "$artifact" in stored:
            if stored["$artifact"].split("/")[0] == "ngapp.array":
                return read_array_artifact(stored, read_blob)
            return stored
    return _from_json(stored, read_blob)


def _chunk_shape(shape, itemsize, chunk_bytes):
    """Largest C-order block of at most chunk_bytes that splits one axis"""
    chunk = list(shape)
    for axis in range(len(shape)):
        rest = itemsize * math.prod(shape[axis + 1 :])
        if rest * shape[axis] <= chunk_bytes:
            break
        if rest <= chunk_bytes:
            chunk[axis] = max(1, chunk_bytes // rest)
            break
        chunk[axis] = 1
    return chunk


def _chunk_slices(shape, chunk_shape):
    grid = [-(-s // c) if c else 0 for s, c in zip(shape, chunk_shape)]
    for index in np.ndindex(*grid):
        yield tuple(
            slice(i * c, min((i + 1) * c, s))
            for i, c, s in zip(index, chunk_shape, shape)
        )


class _Zstd:
    """zstd frames with the standard library (Python 3.14, also in pyodide)
    or the optional package zstandard"""

    def __init__(self):
        try:
            from compression import zstd

            self.compress = lambda data: zstd.compress(data, level=3)
            self.decompress = zstd.decompress
            return
        except ImportError:
            pass
        try:
            import zstandard
        except ImportError as e:
            raise RuntimeError(
                "Codec zstd needs Python 3.14 or the optional dependency "
                "zstandard"
            ) from e
        self.compress = zstandard.ZstdCompressor(level=3).compress
        self.decompress = zstandard.ZstdDecompressor().decompress


@functools.cache
def _zstd() -> _Zstd:
    return _Zstd()


def default_codec() -> str:
    try:
        _zstd()
    except RuntimeError:
        return "none"
    return "zstd"


def encode_array_artifact(
    array: np.ndarray,
    *,
    codec: str | None = None,
    chunk_bytes: int = CHUNK_BYTES,
    attrs: dict | None = None,
):
    """Split an array into chunks; returns the manifest and the chunk blobs"""
    dtype = _artifact_dtype(array)
    if dtype is None:
        raise TypeError(
            f"dtype {array.dtype} cannot be stored as array artifact"
        )
    codec = codec or default_codec()
    if codec not in ("none", "zstd"):
        raise ValueError(f"Unknown codec {codec!r}")
    array = np.ascontiguousarray(array, dtype=dtype)
    shape = list(array.shape)
    chunk_shape = _chunk_shape(shape, dtype.itemsize, chunk_bytes)
    compressor = _zstd().compress if codec == "zstd" else None
    chunks = []
    blobs = {}
    for slices in _chunk_slices(shape, chunk_shape):
        data = array[slices].tobytes(order="C")
        if compressor is not None:
            data = compressor(data)
        h = sha256(data)
        chunks.append(h)
        blobs[h] = (BlobRef(h, len(data), CHUNK_ENCODING), data)
    manifest = {
        "$artifact": ARRAY_ARTIFACT,
        "dtype": dtype.name,
        "shape": shape,
        "chunk_shape": chunk_shape,
        "order": "C",
        "codec": codec,
        "chunks": chunks,
    }
    if attrs:
        manifest["attrs"] = attrs
    return manifest, blobs


def read_array_artifact(manifest: dict, read_blob) -> np.ndarray:
    """Assemble an ngapp.array/1 artifact; unknown fields are ignored"""
    name, _, major = manifest["$artifact"].partition("/")
    if name != "ngapp.array" or major != "1":
        raise ValueError(f"Unsupported artifact {manifest['$artifact']!r}")
    if manifest.get("order", "C") != "C":
        raise ValueError(f"Unsupported order {manifest['order']!r}")
    codec = manifest.get("codec", "none")
    if codec not in ("none", "zstd"):
        raise ValueError(f"Unknown codec {codec!r}")
    if read_blob is None:
        raise RuntimeError("Cannot load array artifact without a store")
    dtype = np.dtype(manifest["dtype"]).newbyteorder("<")
    shape = tuple(manifest["shape"])
    chunk_shape = manifest["chunk_shape"]
    decompress = _zstd().decompress if codec == "zstd" else None
    out = np.empty(shape, dtype=dtype)
    slices_list = list(_chunk_slices(shape, chunk_shape))
    if len(slices_list) != len(manifest["chunks"]):
        raise ValueError("Number of chunks does not match the chunk grid")
    for h, slices in zip(manifest["chunks"], slices_list):
        data = read_blob(BlobRef(h, None, CHUNK_ENCODING))
        if sha256(data) != h:
            raise ValueError(f"Chunk {h} has wrong content")
        if decompress is not None:
            data = decompress(data)
        block = tuple(s.stop - s.start for s in slices)
        out[slices] = np.frombuffer(data, dtype=dtype).reshape(block)
    return out
