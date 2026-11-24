# pylint: disable=protected-access
"""Structural components: content that follows observables, computed values
and state keys without an element of its own in the browser"""

from typing import Callable, Iterable

from .. import observable as _observable
from .. import state as state_module
from .. import utils
from ..observable import Observable, Reaction, computed, safe_equal, untracked
from ..utils import print_exception
from . import basecomponent as _basecomponent
from .basecomponent import Component, creating_ui
from .helper_components import Span

__all__ = ["Fragment", "Show", "For", "Dynamic"]


class Fragment(Component):
    """Children without an element of their own: they appear in the slot of
    the parent of the fragment, at its position.

    The fragment is a component of the tree (ids, namespaces and compute
    functions of its children work), but it is never mounted:
    ``on_mounted`` and ``effect`` belong on its children.
    """

    _transparent = True

    def __init__(self, *children: Component | str):
        super().__init__("fragment", *children)

    def _set_slot(self, key: str, value):
        if isinstance(value, list):
            value = self._wrap_children(value)
        old = self.ui_slots.get(key)
        self.ui_slots[key] = value
        if _basecomponent._slot_recorder is not None:
            _basecomponent._slot_recorder(self, key, old, value)
        if not isinstance(value, list):
            return
        for comp in value:
            if isinstance(comp, Component):
                comp._set_parent_recursive(self)
        owners = self.__dict__.get("_hidden_by")
        if owners:
            # hidden as a whole
            for comp in old or ():
                if isinstance(comp, Component) and comp not in value:
                    for owner in owners:
                        comp._hide_by(owner, False)
            for comp in value:
                if isinstance(comp, Component):
                    for owner in owners:
                        comp._hide_by(owner, True)
        if self._parent is not None:
            self._parent._resend_slot_of(self)

    def _hide_by(self, owner, hide: bool):
        owners = self.__dict__.get("_hidden_by")
        if owners is None:
            owners = self._hidden_by = set()
        if hide:
            owners.add(owner)
        else:
            owners.discard(owner)
        for comp in self.ui_slots["default"]:
            if isinstance(comp, Component):
                comp._hide_by(owner, hide)

    def on_mounted(self, func, arg=None):
        raise TypeError(
            f"{type(self).__name__} has no element in the browser and is "
            "never mounted: use on_mounted of a component inside"
        )

    def on_unmount(self, func, arg=None):
        raise TypeError(
            f"{type(self).__name__} has no element in the browser and is "
            "never mounted: use on_unmount of a component inside"
        )

    def effect(self, fn, name=""):
        raise TypeError(
            f"{type(self).__name__} has no element in the browser and is "
            "never mounted: use effect of a component inside"
        )


def _as_items(content) -> list:
    """Result of a build function as list of components: texts and
    observables get a Span (it can be hidden and moved)"""
    if content is None:
        return []
    if not isinstance(content, (list, tuple)):
        content = (content,)
    items = []
    for item in content:
        if isinstance(item, Component):
            items.append(item)
        elif isinstance(item, (str, Observable)):
            items.append(Span(item))
        elif item is not None:
            raise TypeError(
                "Expected a component, a text, an observable or a list of "
                f"these, got {type(item).__name__}"
            )
    return items


def _has_id(items: Iterable) -> bool:
    for comp in items:
        if not isinstance(comp, Component):
            continue
        if comp._id:
            return True
        for slot in comp.ui_slots.values():
            if isinstance(slot, list) and _has_id(slot):
                return True
    return False


# apps that got new components with an id in the running flush
_changed_apps = []


def _bind_new_components():
    """Flush hook: new components get their stored case data before the
    effects run"""
    if not _changed_apps:
        return
    apps = _changed_apps[:]
    del _changed_apps[:]
    bind = getattr(state_module, "bind_new_components", None)
    if bind is None:
        return
    for app in apps:
        bind(app)


_observable.add_flush_hook(_bind_new_components, "sync")


class _Structural(Fragment):
    """A fragment whose content is kept up to date by a reaction, in every
    environment and whether it is shown or not"""

    def __init__(self):
        super().__init__()
        self._reaction = None

    def _start(self, update: Callable):
        def run():
            try:
                with creating_ui():
                    update()
            except Exception as e:
                # the content stays as it is
                print_exception(e)

        self._reaction = Reaction(
            run, _observable.SYNC, type(self).__name__, start=False
        )
        self._reaction.owner = self
        self._reaction.resume()

    def _set_content(self, items: list):
        old = self.ui_slots["default"]
        if len(old) == len(items) and all(a is b for a, b in zip(old, items)):
            return
        self._set_slot("default", list(items))
        ctx = self.context
        app = ctx.app if ctx is not None else None
        if (
            app is not None
            and getattr(app, "case_session", None) is not None
            and app not in _changed_apps
            and _has_id(c for c in items if all(c is not o for o in old))
        ):
            _changed_apps.append(app)


class Show(_Structural):
    """Content that is shown while a condition holds.

    Args:
        when: an observable (usually a computed value) or a function; the
            observables and state keys a function reads are followed.
        build: function returning the content (a component, a text, an
            observable or a list of these); called when the condition is
            true for the first time.
        otherwise: the same for the content shown while the condition is
            false.
        keep: the content stays in the page and is only hidden while it is
            not shown, so inputs, scroll positions and expensive content
            survive. With False it is removed and built again.

    >>> Show(computed(lambda: self.state["mode"] == "expert"),
    ...      lambda: Div(QInput(ui_label="Tolerance")))
    """

    def __init__(
        self,
        when: Observable | Callable[[], object],
        build: Callable[[], object],
        otherwise: Callable[[], object] | None = None,
        keep: bool = True,
    ):
        super().__init__()
        if not isinstance(when, Observable):
            condition = when
            when = computed(lambda: bool(condition()), "Show.when")
        self._when = when
        self._builders = (otherwise, build)
        self._keep = keep
        self._built = [None, None]
        self._shown = None
        self._start(self._update)

    def _update(self):
        shown = bool(self._when.value)
        if shown == self._shown:
            return
        with untracked():
            self._switch(shown)

    def _switch(self, shown: bool):
        builder = self._builders[shown]
        if not self._keep:
            content = _as_items(builder()) if builder else []
        else:
            built = self._built
            if built[shown] is None:
                built[shown] = _as_items(builder()) if builder else []
            for comp in built[not shown] or ():
                comp._hide_by(self, True)
            for comp in built[shown]:
                comp._hide_by(self, False)
            content = (built[True] or []) + (built[False] or [])
        self._shown = shown
        self._set_content(content)


class For(_Structural):
    """A list of rows that follows a list of items: rows of items that stay
    keep their components.

    Args:
        items: an observable (usually a computed value) or a function
            returning the items; the observables and state keys a function
            reads are followed.
        render: function returning the content of one row (a component, a
            text, an observable or a list of these).
        key: function returning the identity of an item (hashable), the
            item itself by default. Rows are kept per key and moved when
            the order changes.
        otherwise: function returning the content for an empty list.
        reactive: ``render`` gets an observable of the item, which is
            updated when the item of the key changes, so the row is never
            built again. Without it ``render`` gets the item and a row
            whose item changed is built again.

    Components with an id inside a row need an id that is unique per row
    (or a row component with ``namespace=True`` and a unique id).

    >>> For(computed(lambda: check(self.state["radius"])),
    ...     lambda warning: Label(warning))
    """

    def __init__(
        self,
        items: Observable | Callable[[], Iterable],
        render: Callable[[object], object],
        key: Callable[[object], object] | None = None,
        otherwise: Callable[[], object] | None = None,
        reactive: bool = False,
    ):
        super().__init__()
        if isinstance(items, Observable):
            source = items
            items = lambda: source.value
        self._items = items
        self._render = render
        self._key = key
        self._otherwise = otherwise
        self._reactive = reactive
        # (key, occurrence) -> [item or its observable, components]
        self._rows = {}
        self._empty = None
        self._start(self._update)

    def _update(self):
        items = self._items()
        items = [] if items is None else list(items)
        with untracked():
            self._reconcile(items)

    def _reconcile(self, items: list):
        old = self._rows
        rows = {}
        content = []
        count = {}
        for item in items:
            key = self._key(item) if self._key else item
            try:
                n = count.get(key, 0)
            except TypeError:
                raise TypeError(
                    f"For: the key of an item must be hashable, got "
                    f"{type(key).__name__}: pass key=..."
                ) from None
            count[key] = n + 1
            row = old.get((key, n))
            if self._reactive:
                if row is None:
                    value = Observable(item)
                    row = [value, _as_items(self._render(value))]
                else:
                    row[0].value = item
            elif row is None or not safe_equal(row[0], item):
                row = [item, _as_items(self._render(item))]
            rows[(key, n)] = row
            content.extend(row[1])
        if not items and self._otherwise is not None:
            if self._empty is None:
                self._empty = _as_items(self._otherwise())
            content = self._empty
        self._rows = rows
        self._set_content(content)


class Dynamic(_Structural):
    """A region that is built by a function and built again when an
    observable, computed value or state key the function read has changed.

    For structure that does not fit :class:`Show` or :class:`For`. Values
    that only change what the components show are better bound inside them
    (or read with ``untracked``), so the region is not built again.

    >>> Dynamic(lambda: Plot() if self.state["kind"] == "plot" else Table())
    """

    def __init__(self, build: Callable[[], object]):
        super().__init__()
        self._build = build
        self._start(self._update)

    def _update(self):
        content = _as_items(self._build())
        with untracked():
            self._set_content(content)
