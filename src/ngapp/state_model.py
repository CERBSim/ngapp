"""Typed state of a component: a StateModel declares the keys with their
types and defaults, values are validated by pydantic when they are set and
when they are read from the case.

>>> class TankState(StateModel):
...     radius: Annotated[float, Gt(0)] = 1.0
...     studies: list[str] = []
>>> class Tank(App[TankState]):
...     def __init__(self):
...         super().__init__()
...         s = self.state                     # a TankState
...         s.radius = 2                       # stored as 2.0
...         QInput(ui_model_value=ref(lambda: s.radius))
"""

import copy
import logging
import typing
from typing import Annotated, Any, Callable, TypeVar

import pydantic
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

from .observable import Observable, untracked
from .state import StateBase, StateRef

__all__ = ["StateModel", "ref"]

T = TypeVar("T")
logger = logging.getLogger("ngapp.state")
_MISSING = object()
# (state, name) of the fields read while ref() runs its function
_reads: list | None = None


class _Field:
    def __init__(self, name: str, annotation, info: FieldInfo):
        self.name = name
        self.info = info
        if info.metadata:
            annotation = Annotated[(annotation, *info.metadata)]
        self.adapter = pydantic.TypeAdapter(annotation)

    def default(self):
        return copy.deepcopy(self.info.get_default(call_default_factory=True))

    def validate(self, value):
        return self.adapter.validate_python(value)

    def __get__(self, state, owner=None):
        if state is None:
            return self
        if _reads is not None:
            _reads.append((state, self.name))
        raw = StateBase.get(state, self.name, _MISSING)
        if raw is _MISSING:
            return self.default()
        hit = state._cache.get(self.name)
        if hit is not None and hit[0] is raw:
            return hit[1]
        try:
            value = self.validate(raw)
        except ValueError as e:
            logger.warning(
                "state key %r: stored value %r is invalid, using the default (%s)",
                self.name, raw, e,
            )
            value = self.default()
        state._cache[self.name] = (raw, value)
        return value

    def __set__(self, state, value):
        state.set(self.name, value)


class StateModel(StateBase):
    """State with declared keys: use it as ``App[MyState]`` or
    ``Component[MyState]``, ``self.state`` is then a MyState. Every field
    needs a default.

    Reading a field returns the stored value validated (the default while
    the key is not set or its value is invalid); setting a field, or the key
    with ``state[key] = ...``, validates the value. Defaults are plain values
    or ``pydantic.Field(...)`` (constraints, title, json_schema_extra). Types
    are anything pydantic validates; values are stored as validated, so use
    types the case store saves (numbers, strings, lists, dicts, TypedDict,
    Literal).

    Everything else of the state works as before: keys that are not fields
    (``state[key]``), ``ns``, ``notify``, ``on_change``. Reads of fields are
    followed like reads of keys; values are replaced, not changed in
    place."""

    _fields: dict[str, _Field] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        fields = dict(cls._fields)
        for name, annotation in typing.get_type_hints(cls, include_extras=True).items():
            if name.startswith("_") or typing.get_origin(annotation) is typing.ClassVar:
                continue
            if name in fields and name not in cls.__dict__:
                continue
            if hasattr(StateModel, name):
                raise TypeError(
                    f"{cls.__name__}.{name}: the name is a method of the state"
                )
            default = cls.__dict__.get(name, PydanticUndefined)
            info = default if isinstance(default, FieldInfo) else pydantic.Field(default)
            if info.is_required():
                raise TypeError(f"{cls.__name__}.{name} needs a default")
            fields[name] = _Field(name, annotation, info)
            setattr(cls, name, fields[name])
        cls._fields = fields

    def __init__(self, component, prefix: str = ""):
        super().__init__(component, prefix)
        object.__setattr__(self, "_cache", {})

    def __setattr__(self, name: str, value: Any) -> None:
        if name not in self._fields:
            raise AttributeError(f"{type(self).__name__} has no field {name!r}")
        object.__setattr__(self, name, value)

    @classmethod
    def defaults(cls) -> dict:
        """{name: default} of all fields"""
        return {name: f.default() for name, f in cls._fields.items()}

    @classmethod
    def field_info(cls) -> dict[str, FieldInfo]:
        """{name: pydantic FieldInfo} of all fields, in declaration order"""
        return {name: f.info for name, f in cls._fields.items()}

    def dump(self) -> dict:
        """{name: value} of all fields"""
        return {name: getattr(self, name) for name in self._fields}

    def get(self, key: str, default=None, *, cache=True) -> Any:
        if key in self._fields:
            return getattr(self, key)
        return super().get(key, default, cache=cache)

    def set(self, key: str, value: Any, **kwargs) -> None:
        f = self._fields.get(key)
        if f is not None:
            value = f.validate(value)
        super().set(key, value, **kwargs)
        if f is not None:
            self._cache[key] = (value, value)

    def ref(self, key: str, default=None, converter=None) -> StateRef:
        """state.ref of a key; for a field with its default and validation
        (see :func:`ref`)"""
        f = self._fields.get(key)
        if f is not None:
            return super().ref(key, f.default(), f.validate)
        return super().ref(key, default, converter)


def ref(read: Callable[[], T]) -> Observable[T]:
    """Observable of the field that ``read`` returns, bound two-way to its
    state key when used as ``ui_model_value``:
    ``QInput(ui_model_value=ref(lambda: s.radius))``.

    A value from the input that does not validate is not stored; the
    observable's ``error`` holds the reason until a value of the key is
    stored."""
    global _reads
    outer, _reads = _reads, []
    try:
        with untracked():
            read()
        reads = _reads
    finally:
        _reads = outer
    if not reads:
        raise ValueError("ref(): the function reads no field of a StateModel")
    state, name = reads[-1]
    return state.ref(name)
