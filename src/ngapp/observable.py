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

:func:`computed` derives a read-only observable from others with automatic
dependency tracking, :func:`effect` runs a function again after what it read
has changed, and :func:`batch` groups changes so that derived values and
effects update once.

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

import itertools
import logging
import threading
import time
from contextvars import ContextVar
from typing import Any, Callable, Generic, TypeVar
from weakref import WeakSet

T = TypeVar("T")

_logger = logging.getLogger("ngapp.observable")

# protects subscriptions, dirty marks and the pending queues, never held
# while user code runs
_lock = threading.RLock()

# dict {source: version seen} of the running computed/reaction, None outside
_tracker: ContextVar[dict | None] = ContextVar("ngapp_tracker", default=None)
_scope: ContextVar["Batch | None"] = ContextVar("ngapp_batch", default=None)

# numbers of running trackers and open scopes in all threads: the hot paths
# look at the context variables only when these are not zero
_n_trackers = 0
_n_scopes = 0
_count_lock = threading.Lock()

SYNC = 0
EFFECT = 1
_FLUSH_LIMIT = 100

_seq = itertools.count()
_flush_hooks: tuple[list[Callable[[], None]], list[Callable[[], None]]] = (
    [],
    [],
)


def _report(ex) -> None:
    try:
        from .utils import print_exception
    except Exception:
        import traceback

        traceback.print_exc()
        return
    print_exception(ex)


def safe_equal(a, b) -> bool:
    """``a is b or a == b`` where an exception or an ambiguous result (numpy
    arrays, ...) counts as not equal"""
    if a is b:
        return True
    try:
        return bool(a == b)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Dependency tracking
# ---------------------------------------------------------------------------


def _track_begin(reads: dict):
    global _n_trackers
    with _count_lock:
        _n_trackers += 1
    return _tracker.set(reads)


def _track_done() -> None:
    # after the reads were committed, see Observable.value setter
    global _n_trackers
    with _count_lock:
        _n_trackers -= 1


def current_tracker() -> dict | None:
    """The read set of the running computed or reaction, None outside"""
    return _tracker.get() if _n_trackers else None


def is_tracking() -> bool:
    return bool(_n_trackers) and _tracker.get() is not None


class _Untracked:
    __slots__ = ("_tokens",)

    def __init__(self):
        self._tokens = []

    def __enter__(self):
        self._tokens.append(_tracker.set(None))
        return self

    def __exit__(self, *exc):
        _tracker.reset(self._tokens.pop())
        return False


def untracked(fn: Callable | None = None, /, *args, **kwargs):
    """Read observables without registering a dependency.

    ``with untracked(): ...`` or ``untracked(fn, *args)``, which returns the
    result of *fn*.
    """
    if fn is None:
        return _Untracked()
    token = _tracker.set(None)
    try:
        return fn(*args, **kwargs)
    finally:
        _tracker.reset(token)


def _current(reads: dict) -> bool:
    """False when a source changed since it was read (lock held)"""
    for s, version in reads.items():
        if s._version != version or (s._dirty and s._valid):
            return False
    return True


def _resubscribe(node, reads: dict) -> None:
    """Replace the sources of node (lock held)"""
    old = node._sources
    if old:
        for s in old:
            if s not in reads:
                subs = s._subs
                if subs is not None:
                    subs.discard(node)
                    if not subs:
                        s._subs = None
    for s in reads:
        if old is None or s not in old:
            subs = s._subs
            if subs is None:
                subs = s._subs = WeakSet()
            subs.add(node)
    node._sources = reads


def _mark_subs(source, root: "Batch") -> None:
    # lock held; WeakSet.data is the set of weak references
    subs = source._subs
    if subs:
        for ref in tuple(subs.data):
            d = ref()
            if d is not None:
                d._mark(root)


def _propagate(source, scope: "Batch | None") -> None:
    """Mark the dependents of source, queue reactions in the scope (or flush
    at once without one)"""
    if scope is not None:
        root = scope.root
        with _lock:
            if root.open:
                _mark_subs(source, root)
                return
    with Batch(False) as root:
        with _lock:
            _mark_subs(source, root)


class Signal:
    """Dependency source without a value, for data that is not stored in an
    :class:`Observable`.

    ``track()`` registers the signal with the running computed or reaction,
    ``changed()`` invalidates everything that tracked it.
    """

    __slots__ = ("_version", "_subs", "__weakref__")

    _dirty = False

    def __init__(self):
        self._version = 0
        self._subs = None

    def track(self) -> None:
        if _n_trackers:
            t = _tracker.get()
            if t is not None:
                t.setdefault(self, self._version)

    def changed(self) -> None:
        self._version += 1
        if self._subs is not None:
            _propagate(self, current_batch())


# ---------------------------------------------------------------------------
# Batching support
# ---------------------------------------------------------------------------


class Batch:
    """Scope that defers reactions (and optionally plain listeners), see
    :func:`batch`. Other modules may store their own attributes on it."""

    def __init__(self, defer_listeners: bool = True):
        self.defer_listeners = defer_listeners
        self.open = False
        self.parent: Batch | None = None
        self.root: Batch = self
        self.created = 0.0
        self._ldefer: Batch | None = None
        self._listeners: list[tuple[Callable, Any, Any]] = []
        self._pending: tuple[dict, dict] = ({}, {})
        self._in_hooks = [False, False]
        self._token = None

    def __enter__(self) -> "Batch":
        global _n_scopes
        with _count_lock:
            _n_scopes += 1
        parent = _scope.get()
        if parent is not None and not parent.open:
            parent = None
        self.parent = parent
        if parent is None:
            self.created = time.monotonic()
            if self.defer_listeners:
                self._ldefer = self
        else:
            self.root = parent.root
            self.created = parent.created
            self._ldefer = parent._ldefer or (
                self if self.defer_listeners else None
            )
        self.open = True
        self._token = _scope.set(self)
        return self

    def __exit__(self, *exc):
        global _n_scopes
        try:
            if self._ldefer is self:
                self._ldefer = None
                self._run_listeners()
        finally:
            try:
                if self.root is self:
                    self._close()
            finally:
                self.open = False
                self._ldefer = None
                try:
                    _scope.reset(self._token)
                except ValueError:
                    pass
                self._token = None
                with _count_lock:
                    _n_scopes -= 1
        return False

    # -- queue --------------------------------------------------------------

    def has_pending(self, priority: int | None = None) -> bool:
        p = self.root._pending
        if priority is None:
            return bool(p[SYNC] or p[EFFECT])
        return bool(p[priority])

    def _run_listeners(self) -> None:
        pending = self._listeners
        if pending:
            self._listeners = []
            token = _tracker.set(None)
            try:
                for cb, new, old in pending:
                    cb(new, old)
            finally:
                _tracker.reset(token)

    def _run(self, priority: int) -> None:
        queue = self._pending[priority]
        with _lock:
            items = list(queue.values())
            queue.clear()
            for r in items:
                r._queued = False
        if len(items) > 1:
            items.sort(key=_by_seq)
        for r in items:
            r._flush_run()

    def _hooks(self, stage: int) -> None:
        if self._in_hooks[stage]:
            return
        self._in_hooks[stage] = True
        try:
            for hook in tuple(_flush_hooks[stage]):
                try:
                    hook()
                except Exception as ex:
                    _report(ex)
        finally:
            self._in_hooks[stage] = False

    def _flush(self, effects: bool, ld: "Batch | None" = None) -> None:
        """Deferred listeners of ld, SYNC reactions, sync hooks, then
        EFFECT reactions and effect hooks if requested (root only)"""
        pending = self._pending
        passes = 0
        token = _tracker.set(None) if _n_trackers else None
        try:
            while True:
                if ld is not None and ld._listeners:
                    ld._run_listeners()
                if pending[SYNC]:
                    passes += 1
                    if passes > _FLUSH_LIMIT:
                        self._overflow()
                        break
                    self._run(SYNC)
                    continue
                self._hooks(SYNC)
                if pending[SYNC] or (ld is not None and ld._listeners):
                    continue
                if not effects:
                    break
                if pending[EFFECT]:
                    passes += 1
                    if passes > _FLUSH_LIMIT:
                        self._overflow()
                        break
                    self._run(EFFECT)
                    continue
                self._hooks(EFFECT)
                if not (pending[SYNC] or pending[EFFECT]):
                    break
                passes += 1
                if passes > _FLUSH_LIMIT:
                    self._overflow()
                    break
        finally:
            if token is not None:
                _tracker.reset(token)

    def _overflow(self) -> None:
        with _lock:
            names = []
            for queue in self._pending:
                for r in queue.values():
                    r._queued = False
                    names.append(r.name or repr(r._fn))
                queue.clear()
        _logger.error(
            "Reactions did not settle after %d passes (a reaction changes "
            "its own dependencies?), dropped: %s",
            _FLUSH_LIMIT,
            ", ".join(names[:10]),
        )

    def _close(self) -> None:
        pending = self._pending
        for _ in range(_FLUSH_LIMIT):
            self._flush(True)
            with _lock:
                if not (pending[SYNC] or pending[EFFECT]):
                    self.open = False
                    return
        self._overflow()
        self.open = False


def _by_seq(r):
    return r._seq


def batch(defer_listeners: bool = True) -> Batch:
    """Group changes: reactions (computed listeners, bindings, effects) and
    frontend updates run once when the outermost block exits.

    With ``defer_listeners=True`` plain :meth:`Observable.on_change`
    listeners are deferred to the end of this block too, with ``False``
    they stay synchronous (the scope the framework opens around event
    handlers).
    """
    return Batch(defer_listeners)


def current_batch() -> Batch | None:
    """The innermost open batch scope of this context, or None"""
    scope = _scope.get()
    if scope is not None and scope.open:
        return scope
    return None


def in_batch() -> bool:
    return current_batch() is not None


def flush() -> None:
    """Run deferred listeners, pending SYNC reactions and the sync flush
    hooks now, also inside an open batch scope"""
    scope = current_batch()
    if scope is None:
        with Batch(False):
            pass
        return
    scope.root._flush(False, scope._ldefer)


def add_flush_hook(fn: Callable[[], None], stage: str = "sync") -> None:
    """Call fn() in every flush: after the SYNC reactions (``stage="sync"``,
    again after effects ran) or at the very end (``stage="effect"``)"""
    hooks = _flush_hooks[EFFECT if stage == "effect" else SYNC]
    if fn not in hooks:
        hooks.append(fn)


def remove_flush_hook(fn: Callable[[], None]) -> None:
    for hooks in _flush_hooks:
        try:
            hooks.remove(fn)
        except ValueError:
            pass


def observable_batch() -> Batch:
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
    return Batch(True)


# ---------------------------------------------------------------------------
# Observable
# ---------------------------------------------------------------------------


class Observable(Signal, Generic[T]):
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

    read_only = False

    def __init__(
        self,
        default: T,
        name: str = "",
        converter: Callable | None = None,
        formatter: Callable | None = None,
    ):
        self._name: str = name
        self._converter = converter
        self._formatter = formatter
        self._value: T = converter(default) if converter else default
        self._listeners: list[Callable[[T, T], None]] = []
        self._version = 0
        self._subs = None

    # -- value access -------------------------------------------------------

    @property
    def value(self) -> T:
        """The current value."""
        if _n_trackers:
            t = _tracker.get()
            if t is not None:
                t.setdefault(self, self._version)
        return self._value

    @property
    def display_value(self):
        """The value formatted for display in UI widgets.

        If a *formatter* was provided, returns ``formatter(value)``.
        Otherwise returns :attr:`value` unchanged.
        """
        value = self.value
        if self._formatter is not None:
            return self._formatter(value)
        return value

    def peek(self) -> T:
        """The current value, read without registering a dependency"""
        token = _tracker.set(None)
        try:
            return self.value
        finally:
            _tracker.reset(token)

    @value.setter
    def value(self, new: T) -> None:
        if self._converter is not None:
            try:
                new = self._converter(new)
            except (ValueError, TypeError):
                return
        old = self._value
        if old is new:
            return
        try:
            if old == new:
                return
        except Exception:
            pass
        self._value = new
        # the version is needed only by dependents and running trackers
        # (checked after the value is stored)
        if not _n_trackers and self._subs is None:
            listeners = self._listeners
            if listeners:
                if _n_scopes:
                    self._dispatch(new, old)
                else:
                    for cb in listeners:
                        cb(new, old)
            return
        self._version += 1
        self._dispatch(new, old)

    def _notify(self, new: T, old: T) -> None:
        """Report a change: invalidates dependents and calls the listeners
        (deferred in a deferring batch scope)"""
        self._version += 1
        self._dispatch(new, old)

    def _dispatch(self, new, old) -> None:
        scope = _scope.get()
        if scope is not None and not scope.open:
            scope = None
        if self._subs is not None:
            if scope is None:
                with Batch(False) as scope:
                    _propagate(self, scope)
                    self._call_listeners(new, old, scope)
                return
            _propagate(self, scope)
        self._call_listeners(new, old, scope)

    def _call_listeners(self, new, old, scope) -> None:
        listeners = self._listeners
        if not listeners:
            return
        ld = scope._ldefer if scope is not None else None
        if ld is not None:
            pending = ld._listeners
            for cb in listeners:
                pending.append((cb, new, old))
            return
        if _tracker.get() is None:
            for cb in listeners:
                cb(new, old)
            return
        token = _tracker.set(None)
        try:
            for cb in listeners:
                cb(new, old)
        finally:
            _tracker.reset(token)

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
# Computed values
# ---------------------------------------------------------------------------


class Computed(Observable[T]):
    """Read-only observable derived from other observables, see
    :func:`computed`."""

    __slots__ = (
        "_fn",
        "_equal",
        "_sources",
        "_dirty",
        "_error",
        "_valid",
        "_marks",
        "_evaluating",
        "_watchers",
    )

    read_only = True

    def __init__(
        self,
        fn: Callable[[], T],
        name: str = "",
        equal: Callable[[Any, Any], bool] | None = None,
        formatter: Callable | None = None,
    ):
        self._name = name
        self._converter = None
        self._formatter = formatter
        self._value = None  # type: ignore[assignment]
        self._listeners = []
        self._version = 0
        self._subs = None
        self._fn = fn
        self._equal = equal
        self._sources: dict | None = None
        self._dirty = True
        self._valid = False
        self._marks = 0
        self._evaluating = None
        self._error = None
        self._watchers: list[Reaction] | None = None

    @property
    def value(self) -> T:
        """The current value, evaluated if a dependency changed."""
        t = _tracker.get() if _n_trackers else None
        if t is None:
            if self._dirty:
                self._refresh()
            return self._value
        try:
            if self._dirty:
                self._refresh()
        finally:
            t.setdefault(self, self._version)
        return self._value

    @value.setter
    def value(self, new: T) -> None:
        raise AttributeError(f"computed value {self._name!r} is read-only")

    def _mark(self, root: Batch) -> None:
        self._marks += 1
        if not self._dirty or not self._valid:
            self._dirty = True
            _mark_subs(self, root)

    def _refresh(self) -> None:
        ident = threading.get_ident()
        if self._evaluating == ident:
            raise RuntimeError(
                f"computed value {self._name!r} depends on itself"
            )
        marks = self._marks
        version0 = self._version
        error = self._error
        if error is not None:
            # raised before and no dependency changed since
            with _lock:
                same = error[1] == marks and _current(self._sources or {})
            if same:
                raise error[0]
            self._error = None
        if self._valid:
            for s, version in self._sources.items():  # type: ignore[union-attr]
                if s._dirty:
                    try:
                        s._refresh()
                    except Exception:
                        # evaluated below: fn raises and invalidates self
                        break
                if s._version != version:
                    break
            else:
                with _lock:
                    if self._marks == marks:
                        self._dirty = False
                return
        reads: dict = {}
        self._evaluating = ident
        token = _track_begin(reads)
        try:
            try:
                new = self._fn()
            except BaseException as ex:
                with _lock:
                    if self._dirty:
                        _resubscribe(self, reads)
                        self._valid = False
                        self._error = (ex, marks)
                raise
            finally:
                _tracker.reset(token)
                self._evaluating = None
            if self._valid:
                equal = self._equal or safe_equal
                try:
                    changed = not equal(new, self._value)
                except Exception:
                    changed = True
            else:
                changed = True
            with _lock:
                current = self._marks == marks and _current(reads)
                if not current and not self._dirty:
                    # another thread stored a newer result meanwhile
                    return
                _resubscribe(self, reads)
                if changed or self._version != version0 or not self._valid:
                    self._value = new
                    self._version += 1
                self._valid = True
                if current:
                    self._dirty = False
        finally:
            _track_done()

    def on_change(self, cb: Callable[[T, T], None]) -> Callable[[], None]:
        """Register a listener ``cb(new, old)``. It is called from the
        reaction flush (end of the batch) when the value really changed.

        Evaluates the computed value to find its dependencies. The listener
        lives as long as the computed value.
        """
        seen: list = []
        equal = self._equal or safe_equal

        def check():
            new = self.value
            if not seen:
                seen.append(new)
                return
            old = seen[0]
            if equal(new, old):
                return
            seen[0] = new
            untracked(cb, new, old)

        r = Reaction(check, SYNC, self._name, start=False)
        r.owner = self
        if self._watchers is None:
            self._watchers = []
        self._watchers.append(r)
        try:
            r.resume()
        except Exception as ex:
            _report(ex)

        def dispose() -> None:
            r.dispose()
            try:
                self._watchers.remove(r)  # type: ignore[union-attr]
            except ValueError:
                pass

        return dispose

    def __repr__(self) -> str:
        if self._dirty:
            return f"Computed({self._name!r}, <not evaluated>)"
        return f"Computed({self._name!r}, {self._value!r})"


def computed(
    fn: Callable[[], T],
    name: str = "",
    equal: Callable[[Any, Any], bool] | None = None,
) -> Computed[T]:
    """Derived read-only observable.

    *fn* is evaluated lazily on the first read and again on a read after one
    of the observables (or state keys) it read has changed. Dependents are
    notified only when the result changed: ``equal(new, old)`` if given,
    else identity or ``==``.

    Example
    -------
    ::

        radius = Observable(1.0, "radius")
        area = computed(lambda: math.pi * radius.value**2)
        Label(computed(lambda: f"Area: {area.value:.3g}"))
    """
    return Computed(fn, name, equal)


# ---------------------------------------------------------------------------
# Reactions
# ---------------------------------------------------------------------------


class Reaction:
    """Runs fn, records what it read and runs it again in the flush after one
    of these changed. Held weakly by its sources: the owner keeps it alive."""

    __slots__ = (
        "_fn",
        "priority",
        "name",
        "owner",
        "active",
        "disposed",
        "_seq",
        "_sources",
        "_queued",
        "_running",
        "_rerun",
        "_force",
        "__weakref__",
    )

    def __init__(
        self,
        fn: Callable[[], Any],
        priority: int = SYNC,
        name: str = "",
        start: bool = True,
    ):
        self._fn = fn
        self.priority = priority
        self.name = name
        self.owner = None
        self.active = False
        self.disposed = False
        self._seq = next(_seq)
        self._sources: dict | None = None
        self._queued = False
        self._running = False
        self._rerun = False
        self._force = False
        if start:
            self.resume()

    def run(self):
        """Run fn now (tracked) and return its result. Exceptions propagate."""
        if self.disposed:
            return None
        if current_batch() is None:
            with Batch(False):
                return self._run()
        return self._run()

    def schedule(self) -> None:
        """Run in the next flush (end of the current batch scope, at once
        without one), whether a dependency changed or not"""
        if self.disposed or not self.active:
            return
        self._force = True
        self._enqueue()

    def suspend(self) -> None:
        """Stop reacting and release the dependencies"""
        with _lock:
            self.active = False
            _resubscribe(self, {})
            self._sources = None

    def resume(self, run: bool = True) -> None:
        """Activate. Runs now, or with ``run=False`` in the next flush"""
        if self.disposed:
            return
        self.active = True
        if run:
            self.run()
        else:
            self.schedule()

    def dispose(self) -> None:
        with _lock:
            self.disposed = True
            self.active = False
            _resubscribe(self, {})
            self._sources = None
        self._fn = None  # type: ignore[assignment]

    # -- internals ----------------------------------------------------------

    def _mark(self, root: Batch) -> None:
        if not self._queued and self.active:
            self._queued = True
            root._pending[self.priority][self._seq] = self

    def _enqueue(self) -> None:
        scope = current_batch()
        if scope is not None:
            root = scope.root
            with _lock:
                if root.open:
                    self._mark(root)
                    return
        with Batch(False) as root:
            with _lock:
                self._mark(root)

    def _stale(self) -> bool:
        sources = self._sources
        if sources is None:
            return True
        try:
            for s, version in sources.items():
                if s._dirty:
                    s._refresh()
                if s._version != version:
                    return True
        except Exception:
            return True
        return False

    def _flush_run(self) -> None:
        if self.disposed or not self.active:
            return
        if not self._force and not self._stale():
            return
        try:
            self._run()
        except Exception as ex:
            _report(ex)

    def _run(self):
        with _lock:
            if self._running:
                self._rerun = True
                return None
            self._running = True
            self._force = False
        fn = self._fn
        reads: dict = {}
        token = _track_begin(reads)
        try:
            if fn is not None:
                return fn()
        finally:
            _tracker.reset(token)
            try:
                with _lock:
                    if self.active:
                        again = not _current(reads)
                        _resubscribe(self, reads)
                    else:
                        _resubscribe(self, {})
                        self._sources = None
                        again = False
                    self._running = False
                    if self._rerun:
                        self._rerun = False
                        again = self.active
            finally:
                _track_done()
            if again:
                self._enqueue()

    def __repr__(self) -> str:
        kind = "EFFECT" if self.priority == EFFECT else "SYNC"
        return f"Reaction({self.name!r}, {kind})"


_effects: set[Reaction] = set()


def effect(fn: Callable[[], Any], name: str = "") -> Callable[[], None]:
    """Run *fn* now and again after an observable it read has changed (at the
    end of the batch, after bindings were updated).

    Returns a dispose function, the effect lives until it is called. For
    work that belongs to a component use ``component.effect``.
    """
    r = Reaction(fn, EFFECT, name, start=False)
    _effects.add(r)

    def dispose() -> None:
        r.dispose()
        _effects.discard(r)

    try:
        r.resume()
    except BaseException:
        dispose()
        raise
    return dispose


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
    Computed values are skipped (also by :func:`snapshot` and
    :func:`restore`).

    Parameters
    ----------
    obj : object
        The object to inspect.

    Returns
    -------
    dict[str, Observable]
        Mapping from observable name to instance.
    """
    return {
        v._name: v
        for v in vars(obj).values()
        if isinstance(v, Observable) and not v.read_only
    }


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
        if isinstance(v, Observable) and not v.read_only
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
        if isinstance(v, Observable) and not v.read_only and v._name in data:
            v.value = data[v._name]
