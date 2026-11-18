Reactive UI
===========

An ngapp user interface is built once and then follows the data it shows.
Values that change are bound to the components that display them, and the
structure of the page changes only through three constructs that keep every
component they can keep. A parameter change then updates exactly the text
and props that depend on it: inputs keep their focus and cursor, plots and
viewers are not recreated, and the page does not jump.

.. contents:: On this page
   :local:
   :depth: 2

The authoring rule
------------------

.. important::

   Build components once. Show changing values by binding observables or
   :func:`~ngapp.observable.computed` values. Change structure only with
   :class:`~ngapp.components.reactive.Show`,
   :class:`~ngapp.components.reactive.For` or
   :class:`~ngapp.components.reactive.Dynamic`. Put imperative updates
   (figures, viewers) in :meth:`~ngapp.components.basecomponent.Component.effect`.
   Expensive content is built in ``on_mounted`` or ``effect``, never in a
   constructor.

Two further rules complete it:

* Constructors are cheap. The app constructor builds the whole component
  tree, including the content of ``Show``, ``For`` and ``Dynamic``, in every
  environment, also in compute jobs (see `Where code runs`_).
* Values in the case state are replaced, not mutated in place. After an
  in-place change, call :meth:`State.notify(key) <ngapp.state.State.notify>`.

The same rule ships with the package as ``ngapp/AGENTS.md``, a compact
reference for coding agents.

A complete example
------------------

The following app has three inputs bound to the case state, two labels with
derived values, a list of warnings, an optional input, a region whose
layout depends on a selection, and a plot.

.. code-block:: python

   import math

   from ngapp.app import App
   from ngapp.components import (
       Centered, Dynamic, For, Label, NumberInput, PlotlyComponent,
       QBtnToggle, QInput, Row, Show,
   )
   from ngapp.observable import computed


   def check(amplitude, frequency, points):
       warnings = []
       if amplitude > 10:
           warnings.append("Amplitude above 10")
       if frequency > 0 and points / frequency < 8:
           warnings.append("Fewer than 8 points per period")
       return warnings


   class SineApp(App):
       def __init__(self):
           super().__init__()
           s = self.state
           self.amplitude = s.ref("amplitude", 1.0, float)
           self.frequency = s.ref("frequency", 2.0, float)
           self.points = s.ref("points", 200, int)
           self.advanced = s.ref("advanced", False)
           self.view = s.ref("view", "summary")

           warnings = computed(
               lambda: check(
                   self.amplitude.value,
                   self.frequency.value,
                   self.points.value,
               )
           )

           self.plot = PlotlyComponent()
           self.plot.effect(self.draw)

           self.component = Centered(
               Row(
                   NumberInput(ui_label="Amplitude", ui_model_value=self.amplitude),
                   NumberInput(ui_label="Frequency", ui_model_value=self.frequency),
                   NumberInput(ui_label="Points", ui_model_value=self.points),
               ),
               QBtnToggle(
                   ui_model_value=self.advanced,
                   ui_options=[
                       {"label": "Basic", "value": False},
                       {"label": "Advanced", "value": True},
                   ],
               ),
               Show(self.advanced, lambda: QInput(ui_label="Note")),
               Label(computed(lambda: f"Peak to peak: {2 * self.amplitude.value:g}")),
               For(warnings, Label, otherwise=lambda: "No warnings"),
               QBtnToggle(
                   ui_model_value=self.view,
                   ui_options=[
                       {"label": "Summary", "value": "summary"},
                       {"label": "Samples", "value": "samples"},
                   ],
               ),
               Dynamic(self.details),
               self.plot,
           )

       def details(self):
           if self.view.value == "summary":
               return Label(computed(lambda: f"{self.points.value} points"))
           return [self.sample(x) for x in (0.0, 0.125, 0.25)]

       def sample(self, x):
           return Label(
               computed(
                   lambda: f"y({x:g}) = "
                   f"{self.amplitude.value * math.sin(2 * math.pi * self.frequency.value * x):+.3f}"
               )
           )

       def draw(self):
           import numpy as np
           import plotly.graph_objects as go

           x = np.linspace(0, 1, self.points.value)
           y = self.amplitude.value * np.sin(2 * np.pi * self.frequency.value * x)
           self.plot.draw(go.Figure(go.Scatter(x=x, y=y, mode="lines")))

There is no refresh function and no event handler. Typing an amplitude
writes the state key ``amplitude``; the peak-to-peak label, the warning list,
the sample labels (when shown) and the plot follow. The other components are
not touched. The ngapp repository contains this app in a slightly larger
form as ``tests/local_app_reactive``.

Where code runs
---------------

ngapp builds the app in the browser session and also in every compute job,
where compute functions are addressed by their path in the component tree.
Code is therefore divided into two groups:

Runs in every environment
   Constructors of the app and of all components, and the content of
   ``Show``, ``For`` and ``Dynamic``, which is built and kept up to date
   whether a browser shows it or not. The component tree in a job is the
   same as in the browser, so a compute function inside a ``For`` row is
   found.

Runs only where a browser shows the component
   ``on_mounted`` handlers, ``component.effect`` functions and the
   evaluation of props and text children bound to a ``computed``. They run
   when the component is mounted (or serialised for the browser), never in
   a compute job.

Constructors must be cheap. A meshing step, a figure, a solve, a file or
network access in a constructor runs in every job. ngapp logs a warning on
logger ``ngapp.components`` when the constructor of a component takes longer
than ``NGAPP_SLOW_INIT`` seconds of its own time (default ``0.1``, without
the constructors of nested components) or the app constructor takes longer
than ``NGAPP_SLOW_APP_INIT`` seconds in total (default ``1.0``):

.. code-block:: text

   Slow constructor: MeshView took 840 ms (own time, limit 100 ms), created at
   app.py:42. Constructors also run in compute jobs: build expensive content
   in on_mounted or in an effect.

Both variables are read when ngapp is imported; ``0`` disables the
corresponding warning.

Derived values: ``computed``
----------------------------

:func:`~ngapp.observable.computed` creates a read-only observable whose value
is computed by a function:

.. code-block:: python

   from ngapp.observable import Observable, computed

   radius = Observable(1.0)
   height = Observable(2.0)
   volume = computed(lambda: math.pi * radius.value**2 * height.value)
   label = computed(lambda: f"Volume: {volume.value:.3g} m³")

* Every observable, computed value and state key read inside the function is
  a dependency. Dependencies are recorded on each evaluation, so a branch
  that is not taken creates none.
* Evaluation is lazy: on the first read and on the next read after a
  dependency changed. A computed that nothing reads is never evaluated.
* Dependents are notified only when the result changed. Results are
  compared by identity, then with ``==``; a comparison that raises or is
  ambiguous (numpy arrays) counts as a change. Pass ``equal=`` for another
  comparison.
* An exception in the function propagates to the reader, and the value is
  computed again on the next read.
* Assigning ``.value`` raises :class:`AttributeError`.
* ``on_change(cb)`` calls ``cb(new, old)`` after the result changed.

Inside one event each computed is evaluated at most once, however many of its
dependencies changed.

Binding props and text
----------------------

Any ``ui_*`` prop accepts an observable or a computed value:

.. code-block:: python

   QBtn(ui_label=computed(lambda: f"Run {n.value} cases"),
        ui_disable=computed(lambda: n.value == 0))
   Div(ui_class=computed(lambda: "text-negative" if error.value else ""))

* A plain :class:`~ngapp.observable.Observable` on ``ui_model_value`` is
  bound in both directions. When the value the user typed converts to the
  value already stored, nothing is sent back, so typing ``3.`` into an input
  bound to a float stays ``3.``.
* A prop bound to a computed is evaluated when the component is shown in a
  browser and updated in place afterwards. It is never stored in the case.
* Assigning a plain value to a prop bound to a computed removes the binding
  and logs a warning. A prop bound to a plain observable keeps its binding:
  a plain value assigned to it is shown until the observable changes again.
  Write the observable instead.
* ``ui_style``, ``ui_class``, ``ui_hidden`` and ``ui_invisible`` accept
  observables as well.

Observables in a child list become text nodes that are updated in place:

.. code-block:: python

   Label(computed(lambda: f"Volume: {volume.value:.3g} m³"))
   Div("Height: ", computed(lambda: f"{height.value:g} m"))

``Label.text`` accepts a plain string or an observable.

Case state
----------

``self.state`` of the app or of a component holds the data of the case.
Reading a key inside a computed, a structure or an effect makes the key a
dependency. A change of the key from any source notifies its dependents: a
local assignment, a loaded case, a pulled revision of another tab, a merged
job result, a restored revision.

.. code-block:: python

   s = self.state
   self.lsc = computed(lambda: inductance(s["winding"], s.get("gap", 0.1)))
   Label(computed(lambda: f"L = {self.lsc.value * 1e3:.4g} mH"))

:meth:`State.ref(key, default=None, converter=None) <ngapp.state.State.ref>`
returns an observable view of one key (the same object for each call with
the same key). Its value is the value of the key, or ``default`` while the
key is not set. Assigning it sets the key to ``converter(value)``; a
converter that raises :class:`ValueError` or :class:`TypeError` ignores the
assignment. As ``ui_model_value`` it binds an input to the key:

.. code-block:: python

   QInput(ui_label="Frequency", ui_suffix="Hz",
          ui_model_value=self.state.ref("frequency", 50.0, float))

Opening a case whose inputs are bound with ``state.ref`` does not create an
edit.

The state detects changes by assignment. A value mutated in place is not
seen:

.. code-block:: python

   s["layers"] = [*s["layers"], new_layer]   # notifies

   s["layers"].append(new_layer)             # not seen ...
   s.notify("layers")                        # ... until notified

:meth:`~ngapp.state.State.notify` updates the dependents of the key and
stores the value with the next autosave. Append-only lists created with
``state.list(key)`` notify on ``append``.

Typed state
-----------

A :class:`~ngapp.state_model.StateModel` declares the keys of a state with
their types and defaults. With ``App[TankState]`` (or
``Component[TankState]``) ``self.state`` is a ``TankState``: fields are read
and set as attributes, with type checking and completion in the editor, and
every value is validated by pydantic when it is set and when it is read from
a case (a stored ``50`` is read as ``50.0`` for a ``float`` field, an invalid
stored value as the default). A key that is not set reads as its default.

.. code-block:: python

   from typing import Annotated
   from annotated_types import Gt
   from pydantic import Field
   from ngapp.state_model import StateModel, ref

   class TankState(StateModel):
       radius: Annotated[float, Gt(0)] = 1.0
       layers: int = Field(3, ge=1, title="Layers")
       names: list[str] = []

   class Tank(App[TankState]):
       def __init__(self):
           super().__init__()
           s = self.state
           area = computed(lambda: 3.14 * s.radius**2)
           radius = ref(lambda: s.radius)
           self.component = Div(
               QInput(ui_model_value=radius, ui_error=computed(lambda: bool(radius.error.value)),
                      ui_error_message=radius.error),
               Label(computed(lambda: f"A = {area.value:.3g}")))

Reads of fields are followed like reads of keys. :func:`~ngapp.state_model.ref`
returns the ``state.ref`` of the field its function reads, with the field's
validation as converter: a value from the input that does not validate is
not stored, and the ref's ``error`` holds the reason until a value of the
key is stored. ``state.ref(name)`` does the same by name, for code that
loops over fields. Everything else of the state works as before
(``state[key]``, ``ns``, ``notify``); field names must not be names of
these methods. Values are replaced, not changed in place.

Structure: ``Show``, ``For``, ``Dynamic``
-----------------------------------------

The three constructs are components without an element of their own: their
content appears in the parent at their position. They build their content in
the constructor and keep it up to date in every environment.

``build``, ``render`` and ``otherwise`` functions may return a component, a
string, an observable or a list of these. They run without tracking, so
values they read do not rebuild the content; values that change belong in
bindings inside the content.

``Show``
~~~~~~~~

:class:`Show(when, build, otherwise=None, keep=True) <ngapp.components.reactive.Show>`
shows content while a condition holds. ``when`` is an observable or a
function.

.. code-block:: python

   Show(lambda: s.get("mode") == "expert",
        lambda: Row(QInput(ui_label="Tolerance"), QInput(ui_label="Note")),
        otherwise=lambda: Label("Expert settings hidden"))

``build`` runs the first time the condition is true. With ``keep=True`` the
content is hidden, not removed, while the condition is false: typed text,
scroll positions and expensive content survive. With ``keep=False`` the
content is removed and built again next time, for large content that is
rarely shown. ``Show`` replaces visibility toggles written as
``ui_style="display: none"``.

``For``
~~~~~~~

:class:`For(items, render, key=None, otherwise=None, reactive=False) <ngapp.components.reactive.For>`
shows one row per item of a list. ``items`` is an observable or a function
returning an iterable.

.. code-block:: python

   For(computed(lambda: check(s["radius"], s["height"])),
       lambda warning: Label(warning, ui_class="text-negative"),
       otherwise=lambda: "No warnings")

   For(lambda: s.get("studies", []),
       lambda study: StudyCard(study),
       key=lambda study: study["name"])

* Rows are identified by ``key(item)``, the item itself by default (it must
  be hashable). Rows of keys that stay keep their components and are moved
  when the order changes; only new keys call ``render``.
* Without ``reactive``, ``render`` receives the item, and a row whose item
  changed (by ``==``) under the same key is rendered again.
* With ``reactive=True``, ``render`` receives an observable of the item, which
  is updated in place; the row is never rendered again. Bind the row's
  content to it:

  .. code-block:: python

     For(lambda: s.get("studies", []),
         lambda study: Row(Label(computed(lambda: study.value["name"])),
                           Label(computed(lambda: study.value["status"]))),
         key=lambda study: study["name"], reactive=True)

* ``otherwise`` builds the content shown for an empty list.
* Components with an ``id`` inside a row need an id unique per row, for
  example a row component with ``namespace=True`` and ``id=<key>``.

``Dynamic``
~~~~~~~~~~~

:class:`Dynamic(build) <ngapp.components.reactive.Dynamic>` builds a region
with a function and builds it again when a dependency of that function
changes. It covers structure that does not fit ``Show`` or ``For``:

.. code-block:: python

   Dynamic(lambda: ResultTable(s) if s.get("view") == "table" else ResultPlot(s))

Unlike the other two constructs, ``build`` runs tracked. Values that only
change what the components show are bound inside them or read with
:func:`~ngapp.observable.untracked`, so the region is not built again.

``Fragment``
~~~~~~~~~~~~

:class:`~ngapp.components.reactive.Fragment` is the base of the three: a
component whose children appear in the slot of its parent. A fragment is
never mounted, so ``on_mounted`` and ``effect`` belong on its children.

Effects
-------

Some updates cannot be expressed as bound props: drawing a Plotly figure,
updating a 3D viewer, scrolling a row into view.
:meth:`component.effect(fn) <ngapp.components.basecomponent.Component.effect>`
runs ``fn`` when the component is mounted and again after a dependency read
in ``fn`` changed, while the component stays mounted:

.. code-block:: python

   plot = PlotlyComponent()
   plot.effect(lambda: plot.draw(profile_figure(s["radius"], s["height"])))

* Effects run after the bindings of the same event were updated, once per
  event.
* An effect runs again on every mount, since a new browser element needs its
  content again. While the component is unmounted it does not run.
* Effects never run in a compute job.
* ``effect`` returns a function that removes the effect.

:func:`ngapp.observable.effect` is the same without a component: it runs at
once and after each change until the returned function is called.

``on_mounted`` keeps working and is the place for one-time setup that does
not depend on observables.

Untracked reads
---------------

:func:`~ngapp.observable.untracked` reads values without creating a
dependency, as call ``untracked(fn, *args)`` or as context manager.
``Observable.peek()`` reads one value untracked:

.. code-block:: python

   def draw():
       fig = profile(s["radius"])                    # redraw on radius changes
       fig.update_layout(title=untracked(lambda: s.get("title", "")))
       plot.draw(fig)

Events, batching and updates
----------------------------

ngapp groups the work of one event. While an event handler runs (a click,
an input, a state change applied from another tab or a job), changed values
are collected. At the end the dependents are updated once and the browser
receives the changed props and children of all components in one message;
then the effects run, and what they change (props, JavaScript calls such as
drawing a figure) follows. A
component created and removed in the same handler is never sent. New
components arrive together with their content, so a rebuilt panel renders
in one step.

Plain :meth:`~ngapp.observable.Observable.on_change` listeners stay
synchronous inside event handlers.

Outside of event handlers (timers, threads, scripts) each change is applied
at once. :func:`~ngapp.observable.batch` groups several changes there:

.. code-block:: python

   from ngapp.observable import batch

   with batch():
       a.value = 1
       b.value = 2
   # listeners, computed values and the browser update once here

:func:`ngapp.flush_updates` sends the collected updates immediately, for
example to show progress inside a long handler or before a JavaScript call
that relies on the updated page. In a local app, updates of a handler that
runs longer than 50 ms are sent as they occur; in the browser (pyodide)
setup a synchronous handler cannot be interrupted, so ``flush_updates()`` is
needed there.

``NGAPP_BATCH_UPDATES=0`` sends every update at once, which helps when
debugging the order of messages.

Imperative code
---------------

Imperative updates keep working: ``label.text = ...``,
``comp.ui_children = [...]``, ``on_update_model_value`` handlers. They can be
mixed with bindings and migrated piece by piece. Replacing children
recreates components, though: focus, scroll positions and the content of
plots and viewers in the replaced part are lost.

Development warnings
--------------------

ngapp logs warnings on logger ``ngapp.components`` for patterns that work
against the rule, once per component class and code location. Each message
names the line that assigned the children or registered the handler.

``<Class>.ui_children replaced <n> times within 2 s with the same component types``
   A child list was replaced four times within two seconds by new
   components of the same types. Bind the changing values, or use ``Show``,
   ``For`` or ``Dynamic``.

``Handler of <Class> '<event>' created <n> components``
   One event handler created more than 100 components. A parameter change
   should update values, not rebuild the user interface.

``<Class>.<prop> bound to a computed was overwritten with a plain value``
   The binding is removed. Usually a leftover imperative update.

``NGAPP_DEV_WARNINGS=0`` disables these warnings; they are never emitted in
compute jobs. The slow-constructor warning (see `Where code runs`_) is
controlled by ``NGAPP_SLOW_INIT`` and ``NGAPP_SLOW_APP_INIT``.

Testing
-------

:func:`ngapp.test_utils.mount` shows an app in a browser stand-in that speaks
the real protocol, and :func:`ngapp.test_utils.assert_stable` fails when
components were recreated:

.. code-block:: python

   from ngapp.test_utils import assert_stable, mount, standalone_app_test

   @standalone_app_test
   def test_amplitude_updates_in_place():
       app = SineApp()
       fe = mount(app)
       fe.messages.clear()
       with assert_stable(app):
           app.amplitude.value = 3.0
       assert len(fe.messages) == 1

See :doc:`testing` for details.

API reference
-------------

.. automodule:: ngapp.components.reactive
   :members: Show, For, Dynamic, Fragment

.. autofunction:: ngapp.observable.computed
   :no-index:

.. autofunction:: ngapp.observable.effect
   :no-index:

.. autofunction:: ngapp.observable.untracked
   :no-index:

.. autofunction:: ngapp.observable.batch
   :no-index:

.. autofunction:: ngapp.flush_updates

.. automethod:: ngapp.components.basecomponent.Component.effect
   :no-index:

.. automethod:: ngapp.state.State.ref

.. automethod:: ngapp.state.State.notify

.. autoclass:: ngapp.state_model.StateModel
   :members: defaults, field_info, dump

.. autofunction:: ngapp.state_model.ref
