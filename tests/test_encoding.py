import json
import pickle
import sys

import numpy as np
import pytest

from ngapp.store import encoding
from ngapp.store.encoding import (
    ARTIFACT_LIMIT,
    INLINE_LIMIT,
    canonical_json,
    decode_value,
    encode_array_artifact,
    encode_value,
    escape_key,
    iter_blob_refs,
    read_array_artifact,
    sha256,
    unescape_key,
    value_key,
)


def roundtrip(value, **kwargs):
    ev = encode_value(value, **kwargs)
    blobs = {h: data for h, (ref, data) in ev.blobs.items()}
    # the stored form crosses the wire as JSON
    stored = json.loads(json.dumps(ev.stored))
    return ev, decode_value(stored, lambda ref: blobs[ref.hash])


@pytest.mark.parametrize(
    "number, expected",
    [
        (0.0, "0"),
        (-0.0, "0"),
        (1.0, "1"),
        (-1.5, "-1.5"),
        (1e21, "1e+21"),
        (1e20, "100000000000000000000"),
        (123456789012345680000.0, "123456789012345680000"),
        (1e-7, "1e-7"),
        (1e-6, "0.000001"),
        (0.000001234, "0.000001234"),
        (5e-324, "5e-324"),
        (1.7976931348623157e308, "1.7976931348623157e+308"),
        (333333333.33333329, "333333333.3333333"),
        (4.5, "4.5"),
        (2e-3, "0.002"),
        (1e-27, "1e-27"),
        (1.5e300, "1.5e+300"),
        (12345.678e10, "123456780000000"),
    ],
)
def test_canonical_numbers(number, expected):
    assert canonical_json(number) == expected.encode()


def test_canonical_rfc8785_example():
    euro, bs, quote = chr(0x20AC), chr(0x5C), chr(0x22)
    value = {
        "numbers": [333333333.33333329, 1e30, 4.50, 2e-3, 1e-27],
        "string": euro
        + "$"
        + chr(0x0F)
        + chr(0x0A)
        + "A'B"
        + quote
        + bs
        + bs
        + quote
        + "/",
        "literals": [None, True, False],
    }
    expected = (
        '{"literals":[null,true,false],"numbers":[333333333.3333333,1e+30,'
        '4.5,0.002,1e-27],"string":"'
        + euro
        + "$"
        + bs
        + "u000f"
        + bs
        + "nA'B"
        + bs
        + quote
        + bs
        + bs
        + bs
        + bs
        + bs
        + quote
        + '/"}'
    )
    assert canonical_json(value) == expected.encode("utf-8")


def test_canonical_key_order_utf16():
    value = {
        chr(0x20AC): "Euro Sign",
        chr(0x0D): "Carriage Return",
        chr(0xFB33): "Hebrew Letter Dalet With Dagesh",
        "1": "One",
        chr(0x1F600): "Emoji: Grinning Face",
        chr(0x80): "Control",
        chr(0xF6): "Latin Small Letter O With Diaeresis",
    }
    keys = list(json.loads(canonical_json(value)))
    assert [value[k] for k in keys] == [
        "Carriage Return",
        "One",
        "Control",
        "Latin Small Letter O With Diaeresis",
        "Euro Sign",
        "Emoji: Grinning Face",
        "Hebrew Letter Dalet With Dagesh",
    ]


def test_canonical_rejects_non_json():
    with pytest.raises(ValueError):
        canonical_json(float("nan"))
    with pytest.raises(TypeError):
        canonical_json({1: 2})
    with pytest.raises(TypeError):
        canonical_json(object())


def test_escape_keys():
    for key in ["a", "$a", "$$a", "", "a$"]:
        assert unescape_key(escape_key(key)) == key
    assert escape_key("$blob") == "$$blob"
    value = {"$blob": 1, "$$x": {"$bytes": "no"}, "y": [{"$seq": 2}]}
    ev, back = roundtrip(value)
    assert back == value
    assert set(ev.stored) == {"$$blob", "$$$x", "y"}


@pytest.mark.parametrize(
    "value",
    [
        None,
        True,
        3,
        2.5,
        "text",
        [1, "a", None, [2.5]],
        {"a": {"b": [1, 2]}, "c": "d"},
        {"nested": {"x": chr(0x20AC) + " " + chr(0x1F600)}},
    ],
)
def test_json_roundtrip(value):
    ev, back = roundtrip(value)
    assert back == value
    assert not ev.blobs
    assert ev.key == "json:" + sha256(canonical_json(value))


def test_numpy_scalars_and_tuples_are_json():
    ev, back = roundtrip({"a": np.float32(1.5), "b": np.int64(3), "c": (1, 2)})
    assert back == {"a": 1.5, "b": 3, "c": [1, 2]}


def test_bytes_inline_and_blob():
    small = b"\x00\x01" * 100
    ev, back = roundtrip(small)
    assert back == small and "$bytes" in ev.stored and not ev.blobs
    large = bytes(range(256)) * (INLINE_LIMIT // 256 + 1)
    ev2, back2 = roundtrip(large)
    assert back2 == large and ev2.stored["$blob"] == sha256(large)
    assert ev2.stored["enc"] == "bytes" and ev2.stored["size"] == len(large)
    assert ev2.large


def test_inline_and_blob_have_the_same_key():
    value = {"rows": list(range(100))}
    inline = encode_value(value)
    blob = encode_value(value, lazy=True)
    assert "$blob" in blob.stored and "$blob" not in inline.stored
    assert (
        inline.key
        == blob.key
        == value_key(inline.stored)
        == value_key(blob.stored)
    )
    data = b"x" * 10
    assert encode_value(data).key == encode_value(data, lazy=True).key


def test_large_json_becomes_blob():
    value = ["x" * 100] * (INLINE_LIMIT // 100)
    ev, back = roundtrip(value)
    assert ev.stored["enc"] == "json" and back == value
    with pytest.raises(ValueError):
        encode_value(["x" * 1000] * 100, lazy=False)


def test_equality_by_hash_not_by_value():
    assert (
        encode_value({"a": 1, "b": 2}).key == encode_value({"b": 2, "a": 1}).key
    )
    assert encode_value(1.0).key == encode_value(1).key
    assert encode_value([1]).key != encode_value(b"[1]").key
    a = np.arange(5.0)
    assert encode_value(a).key == encode_value(a.copy()).key
    assert encode_value(a).key != encode_value(a.astype(np.float32)).key


def test_npy_roundtrip():
    for array in [
        np.arange(12, dtype=np.int32).reshape(3, 4),
        np.array([1.5, np.nan]),
        np.zeros((0, 3)),
        np.array(True),
        np.linspace(0, 1, 10000),
    ]:
        ev, back = roundtrip(array)
        assert ev.key.startswith("npy:")
        assert back.dtype == array.dtype and back.shape == array.shape
        np.testing.assert_array_equal(back, array)
    assert "$bytes" in encode_value(np.arange(3)).stored
    assert "$blob" in encode_value(np.arange(10000)).stored


def test_nested_arrays_and_bytes():
    value = {"small": np.arange(3), "big": np.arange(10000.0), "raw": b"abc"}
    ev, back = roundtrip(value)
    # nested references keep the value inline, so they stay visible
    assert "$blob" not in ev.stored and "$blob" in ev.stored["big"]
    assert [r.hash for r in iter_blob_refs(ev.stored)] == list(ev.blobs)
    np.testing.assert_array_equal(back["big"], value["big"])
    assert back["raw"] == b"abc"


class Custom:
    def __init__(self, x):
        self.x = x

    def __eq__(self, other):
        return isinstance(other, Custom) and other.x == self.x


def test_pickle_only_on_request():
    with pytest.raises(TypeError):
        encode_value(Custom(1))
    with pytest.raises(TypeError):
        encode_value({"a": Custom(1)})
    ev, back = roundtrip(Custom(2), pickle=True)
    assert back == Custom(2) and ev.key.startswith("pickle:")
    ev, back = roundtrip({1: "int keys"}, pickle=True)
    assert back == {1: "int keys"}
    big = Custom("x" * 100000)
    ev, back = roundtrip(big, pickle=True)
    assert ev.stored["enc"] == "pickle" and back == big
    assert pickle.loads(next(iter(ev.blobs.values()))[1]) == big


@pytest.mark.parametrize("codec", ["none", "zstd"])
@pytest.mark.parametrize(
    "shape, dtype, chunk_bytes",
    [
        ((1000, 3), np.float32, 4000),
        ((7, 5, 3), np.int16, 40),
        ((3, 1000), np.float64, 1000),
        ((10,), np.complex128, 48),
        ((50,), ">f8", 64),
        ((4, 4), np.bool_, 5),
    ],
)
def test_array_artifact_roundtrip(codec, shape, dtype, chunk_bytes):
    array = (np.arange(int(np.prod(shape))) % 7).reshape(shape).astype(dtype)
    manifest, blobs = encode_array_artifact(
        array, codec=codec, chunk_bytes=chunk_bytes
    )
    assert (
        manifest["$artifact"] == "ngapp.array/1" and manifest["codec"] == codec
    )
    assert manifest["order"] == "C" and manifest["shape"] == list(shape)
    assert len(manifest["chunks"]) > 1
    assert all(len(data) == ref.size for ref, data in blobs.values())
    manifest = json.loads(json.dumps(manifest))
    back = read_array_artifact(manifest, lambda ref: blobs[ref.hash][1])
    assert back.dtype == np.dtype(dtype).newbyteorder("<")
    np.testing.assert_array_equal(back, array)
    refs = list(iter_blob_refs(manifest))
    assert [r.hash for r in refs] == manifest["chunks"]
    assert all(r.enc == "artifact-chunk" for r in refs)


@pytest.mark.parametrize("writer", ["stdlib", "zstandard"])
def test_array_artifact_zstd_without_zstandard(monkeypatch, writer):
    """Readers support both codecs without the zstandard package (pyodide)"""
    if writer == "stdlib":
        pytest.importorskip("compression.zstd")
    else:
        pytest.importorskip("zstandard")
    array = np.arange(3000.0).reshape(100, 30)
    encoding._zstd.cache_clear()
    if writer == "stdlib":
        monkeypatch.setitem(sys.modules, "zstandard", None)
    else:
        monkeypatch.setitem(sys.modules, "compression.zstd", None)
    manifest, blobs = encode_array_artifact(array, chunk_bytes=8000)
    assert manifest["codec"] == "zstd"
    monkeypatch.undo()
    pytest.importorskip("compression.zstd")
    monkeypatch.setitem(sys.modules, "zstandard", None)
    encoding._zstd.cache_clear()
    try:
        back = read_array_artifact(manifest, lambda ref: blobs[ref.hash][1])
    finally:
        encoding._zstd.cache_clear()
    np.testing.assert_array_equal(back, array)


def test_array_artifact_reader_checks():
    array = np.arange(100.0)
    manifest, blobs = encode_array_artifact(
        array, codec="none", chunk_bytes=160
    )
    read = lambda ref: blobs[ref.hash][1]
    extended = dict(manifest, future_field={"x": 1}, attrs={"unit": "m"})
    np.testing.assert_array_equal(read_array_artifact(extended, read), array)
    with pytest.raises(ValueError):
        read_array_artifact(
            dict(manifest, **{"$artifact": "ngapp.array/2"}), read
        )
    corrupt = {
        h: (ref, data[:-1] + b"\x00") for h, (ref, data) in blobs.items()
    }
    with pytest.raises(ValueError):
        read_array_artifact(manifest, lambda ref: corrupt[ref.hash][1])


def test_large_arrays_become_artifacts():
    array = np.zeros(ARTIFACT_LIMIT // 8 + 1)
    array[::1000] = np.arange(len(array[::1000]))
    ev, back = roundtrip(array)
    assert ev.stored["$artifact"] == "ngapp.array/1" and ev.large
    assert (
        1024 * 1024
        <= len(array) * 8 // len(ev.stored["chunks"])
        <= 8 * 1024 * 1024
    )
    np.testing.assert_array_equal(back, array)
    # the reader handles both forms
    small_ev, small_back = roundtrip(array[:10000])
    assert small_ev.stored["enc"] == "npy"
    np.testing.assert_array_equal(small_back, array[:10000])
