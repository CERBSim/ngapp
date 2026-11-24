# Writing ngapp apps

Notes for coding agents and authors of ngapp apps. Full documentation: the
"Reactive UI" page of the ngapp docs (`docs/reactivity.rst`).

## The rule

> Build components once. Show changing values by binding observables or
> `computed` values. Change structure only with `Show`, `For` or `Dynamic`.
> Put imperative updates (figures, viewers) in `effect`. Expensive content is
> built in `on_mounted` or `effect`, never in a constructor.

What follows from it:

- The constructor of the app builds the whole component tree, including the
  content of `Show`, `For` and `Dynamic`. It runs in every environment, also
  in compute jobs, where compute functions are found by component path. Keep
  it cheap: no meshes, figures, solves, file or network access. A constructor
  that takes longer than 0.1 s (own time) or an app constructor that takes
  longer than 1 s logs a `Slow constructor` warning.
- Only what happens on mount is skipped in jobs: `on_mounted`,
  `component.effect` and the evaluation of props and text children bound to
  a `computed`. Those are evaluated when a browser shows the component.
- Keep the case data in `self.state` and read it inside `computed`, `Show`,
  `For`, `Dynamic` and `effect`: they follow the keys they read, whoever
  changes them (the user, a loaded case, a job result, another tab).
- State values are replaced, not mutated: `state["items"] = [*items, new]`.
  After an in-place change call `state.notify("items")`.
- Never write `ui_children = [...]` or create components in an event handler
  to show new values. Never toggle visibility with
  `ui_style="display: none"`.

## API

```python
from ngapp.app import App
from ngapp.components import Show, For, Dynamic, Label, QInput
from ngapp.observable import Observable, computed, effect, untracked, batch
from ngapp import flush_updates
```

| Name | Use |
|---|---|
| `Observable(value, name="", converter=None, formatter=None)` | a value with listeners; `.value`, `.peek()`, `.on_change(cb(new, old))` |
| `computed(fn, name="", equal=None)` | read-only derived value; lazy, follows what `fn` reads, notifies only when the result changed |
| `self.state.ref(key, default=None, converter=None)` | observable view of a state key; as `ui_model_value` it binds an input two-way to the key |
| `self.state[key]`, `self.state.get(key, default)` | tracked reads inside computed, structures and effects |
| `self.state.notify(key)` | report an in-place change of a value |
| `class S(StateModel): x: float = 1.0`, `class MyApp(App[S])` | typed `self.state`: fields validated by pydantic, reads followed like keys |
| `ref(lambda: s.x)` / `s.ref("x")` | `state.ref` of a field with its validation; `.error` holds why an input value was rejected |
| `ui_<prop>=observable_or_computed` | bound prop; a plain `Observable` on `ui_model_value` is two-way |
| `Label(computed(...))`, `Div("x = ", obs)` | bound text, updated in place |
| `Show(when, build, otherwise=None, keep=True)` | conditional content; with `keep=True` it is hidden, not destroyed |
| `For(items, render, key=None, otherwise=None, reactive=False)` | keyed list; rows of keys that stay keep their components |
| `Dynamic(build)` | region rebuilt when what `build` read changed |
| `component.effect(fn) -> dispose` | runs on mount and after its dependencies changed, while mounted; never in jobs |
| `untracked(fn)` / `with untracked():` | read without creating a dependency |
| `batch()` | group changes made outside an event handler; handlers are batched already |
| `flush_updates()` | send pending updates now (progress inside a long handler) |

- `when`, `items` and `build` accept an observable or a function. `build`,
  `render` and `otherwise` return a component, a string, an observable or a
  list of these.
- `For` keys default to the item (must be hashable). Components with an `id`
  inside a row need an id unique per row, for example a row component with
  `namespace=True` and `id=<key>`.
- Assigning a plain value to a prop bound to a `computed` removes the
  binding and logs a warning.

## Typed state

Declare the case data in a `StateModel` (`from ngapp.state_model import
StateModel, ref`) and use it as `App[MyState]` / `Component[MyState]`;
`self.state` is then typed:

```python
class TankState(StateModel):
    radius: Annotated[float, Gt(0)] = 1.0         # pydantic constraints
    layers: int = Field(3, ge=1, title="Layers")  # or pydantic.Field
    curves: dict[str, Curve] = {}                 # TypedDict values stay dicts

class Tank(App[TankState]):
    def __init__(self):
        super().__init__()
        s = self.state
        radius = ref(lambda: s.radius)
        QInput(ui_model_value=radius,
               ui_error=computed(lambda: bool(radius.error.value)),
               ui_error_message=radius.error)
```

- Every field needs a default; a key that is not set reads as its default,
  so there is no need to write the defaults into the state.
- Use types the case store saves (numbers, strings, lists, dicts,
  `TypedDict`, `Literal`); values are stored as validated.
- Setting an invalid value raises `ValueError`; setting an attribute that is
  no field raises `AttributeError`. An invalid stored value (an old case) is
  read as the default and logged.
- Input text that does not validate is not stored, so the state never holds
  half-typed text. Show `ref.error` at the input and treat it as an error of
  the input (block runs on it).
- Replace values, do not change them in place:
  `s.curves = {**s.curves, key: curve}`.
- Model functions take the state (`def params(c: Case)`); jobs get the same
  typed state. `state.dump()` gives all fields (for fingerprints of inputs:
  undeclared keys never end up in them).
- A field typed with another `StateModel` (`wall: Wall`, no default) is a
  nested state stored in the namespace `wall/`; every nested field is
  followed on its own. Use it for groups of inputs; lists of records stay
  plain values (`list[MyTypedDict]`) or rows of components with their own
  `Component[RowState]`. Turning an existing field into a nested state
  changes where it is stored (old cases read the defaults).
- Field names must not be names of state methods (`get`, `keys`, `ns`,
  `ref`, `dump`, ...); the class raises `TypeError` otherwise.

## Before and after

Before (rebuilds on every keystroke, flickers, loses focus):

```python
class Tank(App):
    def __init__(self):
        super().__init__()
        self.radius = QInput(ui_label="Radius", ui_model_value=1.0)
        self.radius.on_update_model_value(self.refresh)
        self.body = Div()
        self.plot = PlotlyComponent()
        self.component = Div(self.radius, self.body, self.plot)
        self.refresh()

    def refresh(self):
        r = float(self.radius.ui_model_value)
        warnings = check(r)
        self.body.ui_children = [
            Label(f"Volume: {volume(r):.3g}"),
            Div(*[Label(w) for w in warnings]),
        ]
        self.plot.draw(profile(r))
```

After:

```python
class Tank(App):
    def __init__(self):
        super().__init__()
        radius = self.state.ref("radius", 1.0, float)
        warnings = computed(lambda: check(radius.value))
        plot = PlotlyComponent()
        plot.effect(lambda: plot.draw(profile(radius.value)))
        self.radius_input = QInput(ui_label="Radius", ui_model_value=radius)
        self.component = Div(
            self.radius_input,
            Label(computed(lambda: f"Volume: {volume(radius.value):.3g}")),
            For(warnings, Label, otherwise=lambda: "No warnings"),
            plot,
        )
```

A complete reference app: `tests/local_app_reactive/app.py` in the ngapp
repository.

## Testing

```python
from ngapp.test_utils import assert_stable, mount, standalone_app_test

@standalone_app_test
def test_radius():
    app = Tank()
    fe = mount(app)              # browser stand-in speaking the real protocol
    fe.messages.clear()
    with assert_stable(app):     # fails if components were recreated
        fe.event(app.radius_input, "update:model-value", "2")
    assert len(fe.messages) == 1 # one update message per event
```

- `fe.props(comp)`, `fe.children(comp)` (components and texts),
  `fe.mounted`, `fe.unmount(comp)`, `fe.mount(comp)`, `fe.calls` show what
  the browser would see.
- `fe.event` takes the browser's event name: `"update:model-value"` for
  inputs, `"click.stop"` for `on_click`; `fe.events(comp)` lists them.
- `assert_stable(app, allow=(panel,))` lets components inside `panel`
  (components or ids) be recreated. Content of `Show`, `For` and `Dynamic`
  is not checked; adding or removing components alone does not fail.

## Warnings

Logged on logger `ngapp.components`, once per class and creation site:

- `Slow constructor: ...`: move the work into `on_mounted` or an `effect`.
  Limits: `NGAPP_SLOW_INIT` (default 0.1 s), `NGAPP_SLOW_APP_INIT` (default
  1 s), `0` disables.
- `<Class>.ui_children replaced <n> times within 2 s with the same component
  types`: bind the changing values or use `Show` / `For` / `Dynamic`.
- `Handler of <Class> '<event>' created <n> components`: a parameter change
  should update values, not rebuild the UI. Content built by `Show`, `For`
  and `Dynamic` does not count; a handler that opens new UI on purpose (a
  view, a dialog) creates it inside `with creating_ui():`.
- `<Class>.<prop> bound to a computed was overwritten with a plain value`.

`NGAPP_DEV_WARNINGS=0` disables the last three. `NGAPP_BATCH_UPDATES=0`
sends every update at once instead of one message per event (debugging).
