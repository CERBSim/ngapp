"""Reactive observable values with change notification and two-way widget binding.

This module provides :class:`Observable`, a generic container that holds a
single typed value and notifies registered listeners whenever that value
changes.  It serves as a single source of truth for application state that
may be read or written by multiple consumers (UI widgets, keyboard shortcuts,
programmatic logic, persistence layers, etc.).

The companion :func:`bind` function establishes a two-way connection between
an :class:`Observable` and an ngapp :class:`~ngapp.components.Component`
widget, keeping the two in sync with a built-in re-entrancy guard.

:func:`observable_batch` allows grouping multiple value changes so that
listeners are invoked only once per observable after all changes are applied.

Example
-------
::

    from ngapp.observable import Observable, bind, observable_batch

    visible = Observable(True, "visible")
    visible.on_change(lambda new, old: scene.render())

    checkbox = QCheckbox("Visible", ui_model_value=visible.value)
    bind(visible, checkbox)

    # Any source can change the value; all listeners and the widget
    # are updated automatically.
    visible.toggle()
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Callable, Generic, TypeVar

T = TypeVar("T")

# ---------------------------------------------------------------------------
# Batching support
# ---------------------------------------------------------------------------

_batch_depth: int = 0
_batch_pending: list[tuple[Callable, Any, Any]] = []


@contextmanager
def observable_batch():
    """Defer :class:`Observable` listener invocations until the block exits.

    Within the managed block, setting :attr:`Observable.value` records
    pending notifications instead of dispatching them immediately.  When
    the outermost block exits, every recorded callback is invoked exactly
    once in the order it was queued.  Batches may be nested; listeners
    fire only when the outermost batch completes.

    This is useful when multiple observables must be updated atomically
    to avoid redundant or intermediate side-effects.

    Example
    -------
    ::

        with observable_batch():
            position.value = (1.0, 2.0, 3.0)
            scale.value = 0.5
        # All listeners are called here, once per changed observable.
    """
    global _batch_depth
    _batch_depth += 1
    try:
        yield
    finally:
        _batch_depth -= 1
        if _batch_depth == 0:
            pending = _batch_pending.copy()
            _batch_pending.clear()
            for cb, new, old in pending:
                cb(new, old)


# ---------------------------------------------------------------------------
# Observable
# ---------------------------------------------------------------------------


class Observable(Generic[T]):
    """A single observable value with change notification.

    :class:`Observable` wraps a value of type *T* and maintains a list of
    listener callbacks.  Assigning to :attr:`value` compares the new value
    against the current one (using ``==``); if they differ, every registered
    listener is called with ``(new_value, old_value)``.

    Parameters
    ----------
    default : T
        The initial value.
    name : str, optional
        A descriptive name used for debugging and serialisation keys.
    converter : callable, optional
        A function applied to every incoming value before it is stored.
        If the converter raises ``ValueError`` or ``TypeError``, the
        assignment is silently ignored (the value stays unchanged).
        Useful for type coercion, e.g. ``converter=float``.
    formatter : callable, optional
        A function applied to the stored value when presenting it to
        UI widgets (via :attr:`display_value`).  The raw :attr:`value`
        is unaffected.  Useful for number formatting, e.g.
        ``formatter=lambda v: f"{v:.4g}"``.

    Attributes
    ----------
    value : T
        The current value.  Setting this property triggers change
        notification when the new value differs from the old one.
    display_value
        The formatted value for display.  If no *formatter* is set,
        this is identical to :attr:`value`.

    Example
    -------
    ::

        enabled = Observable(False, "enabled")

        dispose = enabled.on_change(lambda new, old: print(f"{old} -> {new}"))
        enabled.value = True   # prints: False -> True
        enabled.value = True   # no output (value unchanged)
        enabled.toggle()       # prints: True -> False

        dispose()              # removes the listener

        # Formatter example:
        temp = Observable(0.000123, "temp", converter=float,
                          formatter=lambda v: f"{v:.4g}")
        temp.display_value     # "0.000123" → "0.000123" wait no "1.23e-04"
    """

    __slots__ = ("_name", "_value", "_listeners", "_converter", "_formatter")

    def __init__(
        self, default: T, name: str = "", converter: Callable | None = None,
        formatter: Callable | None = None,
    ):
        self._name: str = name
        self._converter = converter
        self._formatter = formatter
        self._value: T = converter(default) if converter else default
        self._listeners: list[Callable[[T, T], None]] = []

    # -- value access -------------------------------------------------------

    @property
    def value(self) -> T:
        """The current value."""
        return self._value

    @property
    def display_value(self):
        """The value formatted for display in UI widgets.

        If a *formatter* was provided, returns ``formatter(value)``.
        Otherwise returns :attr:`value` unchanged.
        """
        if self._formatter is not None:
            return self._formatter(self._value)
        return self._value

    @value.setter
    def value(self, new: T) -> None:
        if self._converter is not None:
            try:
                new = self._converter(new)
            except (ValueError, TypeError):
                return
        old = self._value
        if old == new:
            return
        self._value = new
        if _batch_depth > 0:
            for cb in self._listeners:
                _batch_pending.append((cb, new, old))
        else:
            for cb in self._listeners:
                cb(new, old)

    # -- subscription -------------------------------------------------------

    def on_change(self, cb: Callable[[T, T], None]) -> Callable[[], None]:
        """Register a listener that is called on every value change.

        Parameters
        ----------
        cb : callable(new_value, old_value)
            The callback to invoke when :attr:`value` changes.

        Returns
        -------
        callable
            A dispose function.  Calling it removes *cb* from the
            listener list.  Calling it more than once is safe.
        """
        self._listeners.append(cb)

        def dispose() -> None:
            try:
                self._listeners.remove(cb)
            except ValueError:
                pass

        return dispose

    # -- helpers ------------------------------------------------------------

    def toggle(self) -> None:
        """Invert the current value.  Intended for boolean observables."""
        self.value = not self.value  # type: ignore[assignment]

    def __repr__(self) -> str:
        return f"Observable({self._name!r}, {self._value!r})"


# ---------------------------------------------------------------------------
# Two-way widget binding
# ---------------------------------------------------------------------------


def bind(
    prop: Observable,
    widget,
    widget_attr: str = "ui_model_value",
    event: str = "on_update_model_value",
) -> Callable[[], None]:
    """Establish a two-way binding between an :class:`Observable` and a widget.

    The binding synchronises the observable and the widget in both
    directions:

    * **Observable -> Widget:** When the observable value changes, the
      widget attribute *widget_attr* is updated.
    * **Widget -> Observable:** When the widget emits the event registered
      via *event*, the observable value is updated.

    An internal re-entrancy guard ensures that a change originating on one
    side does not bounce back and cause an infinite loop.

    Parameters
    ----------
    prop : Observable
        The observable to bind.
    widget : Component
        An ngapp component instance (e.g. ``QCheckbox``, ``QSlider``).
    widget_attr : str, optional
        The widget attribute to read/write.  Defaults to
        ``"ui_model_value"``.
    event : str, optional
        The name of the widget method used to register an event handler.
        Defaults to ``"on_update_model_value"``.

    Returns
    -------
    callable
        A dispose function that removes the observable-to-widget listener.
    """
    _syncing = False

    def prop_to_widget(val: Any, _old: Any) -> None:
        nonlocal _syncing
        if _syncing:
            return
        _syncing = True
        try:
            setattr(widget, widget_attr, prop.display_value)
        finally:
            _syncing = False

    def widget_to_prop(event_obj: Any) -> None:
        nonlocal _syncing
        if _syncing:
            return
        _syncing = True
        try:
            prop.value = event_obj.value
        finally:
            _syncing = False

    dispose_obs = prop.on_change(prop_to_widget)
    getattr(widget, event)(widget_to_prop)

    def dispose() -> None:
        dispose_obs()

    return dispose


# ---------------------------------------------------------------------------
# Collection helpers
# ---------------------------------------------------------------------------


def collect_observables(obj) -> dict[str, Observable]:
    """Return a ``{name: observable}`` dict of all :class:`Observable` attributes on *obj*.

    Inspects ``obj.__dict__`` and returns every value that is an
    :class:`Observable` instance, keyed by :attr:`Observable._name`.

    Parameters
    ----------
    obj : object
        The object to inspect.

    Returns
    -------
    dict[str, Observable]
        Mapping from observable name to instance.
    """
    return {v._name: v for v in vars(obj).values() if isinstance(v, Observable)}


def snapshot(obj) -> dict[str, Any]:
    """Return a plain ``{name: value}`` dict of all :class:`Observable` values on *obj*.

    This is the serialisation counterpart of :func:`restore`.

    Parameters
    ----------
    obj : object
        The object whose observables should be snapshotted.

    Returns
    -------
    dict[str, Any]
        Mapping from observable name to its current value.
    """
    return {
        v._name: v.value
        for v in vars(obj).values()
        if isinstance(v, Observable)
    }


def restore(obj, data: dict[str, Any]) -> None:
    """Restore :class:`Observable` values on *obj* from *data*.

    For every observable on *obj* whose :attr:`~Observable._name` appears
    in *data*, the value is set (triggering listeners as usual).  Unknown
    keys in *data* are silently ignored.

    Parameters
    ----------
    obj : object
        The object whose observables should be restored.
    data : dict[str, Any]
        Mapping from observable name to value, as produced by
        :func:`snapshot`.
    """
    for v in vars(obj).values():
        if isinstance(v, Observable) and v._name in data:
            v.value = data[v._name]
