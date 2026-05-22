Observable
==========

The :mod:`ngapp.observable` module provides reactive state management for
ngapp applications.  An :class:`~ngapp.observable.Observable` holds a single
value and notifies registered listeners whenever the value changes.
Pass an ``Observable`` directly as a component prop (e.g.
``ui_model_value=my_observable``) for automatic two-way binding.

.. contents:: On this page
   :local:
   :depth: 2

Why Observable?
---------------

A common challenge in interactive applications is keeping multiple concerns
synchronised: a checkbox in the UI, a keyboard shortcut, a persistence
layer, and the underlying domain logic may all read or write the same piece
of state.  Without a shared mechanism, each pair requires manual glue code
and guard flags to prevent feedback loops.

``Observable`` solves this by providing a **single source of truth** that any
number of consumers can subscribe to.  When the value changes — regardless
of which consumer changed it — every other subscriber is notified.

Quick start
-----------

.. code-block:: python

   from ngapp.observable import Observable
   from ngapp.components import QCheckbox

   # 1. Declare an observable
   visible = Observable(True, "visible")

   # 2. React to changes
   visible.on_change(lambda new, old: print(f"visible: {old} -> {new}"))

   # 3. Pass it directly as a prop — two-way binding is automatic
   checkbox = QCheckbox("Show", ui_model_value=visible)

   # 4. Any mutation is propagated everywhere
   visible.value = False   # prints "visible: True -> False", unchecks the checkbox
   visible.toggle()        # prints "visible: False -> True", checks the checkbox

Creating an Observable
----------------------

.. code-block:: python

   from ngapp.observable import Observable

   # Required: initial value.  Optional: name for debugging / serialisation.
   scale = Observable(1.0, "scale")
   enabled = Observable(False, "enabled")
   items = Observable([], "items")

The *name* parameter has no functional effect at runtime.  It is used by
:func:`~ngapp.observable.snapshot` and :func:`~ngapp.observable.restore`
as the dictionary key, and appears in the ``repr()`` output.

Type coercion with ``converter``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pass a ``converter`` function to automatically coerce incoming values.
If the converter raises ``ValueError`` or ``TypeError``, the assignment
is silently ignored and the value stays unchanged:

.. code-block:: python

   scale = Observable(1.0, "scale", converter=float)

   scale.value = "3.14"   # converted to 3.14
   scale.value = "abc"    # silently ignored, value stays 3.14
   scale.value = 5        # converted to 5.0

This is especially useful with ``NumberInput`` (or any ``QInput`` with
``ui_type="number"``), where the widget emits string values:

.. code-block:: python

   scale = Observable(1.0, "scale", converter=float)
   inp = NumberInput(ui_model_value=scale, ui_label="Scale")
   # User types "2.5" → observable receives 2.5 as float

Display formatting with ``formatter``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pass a ``formatter`` function to control how the value is presented in UI
widgets.  The stored value is **not affected** — only the display
representation changes.  This is the counterpart to ``converter``:

- ``converter``: Widget → Observable (parse user input)
- ``formatter``: Observable → Widget (format for display)

.. code-block:: python

   colormap_min = Observable(
       0.000007957,
       "colormap_min",
       converter=float,
       formatter=lambda v: f"{v:.4g}",
   )

   colormap_min.value          # 7.957394756115198e-06 (raw float)
   colormap_min.display_value  # "7.957e-06" (formatted string)

   # Bind to a QInput — the widget shows "7.957e-06"
   inp = QInput(ui_model_value=colormap_min, ui_type="number")

   # When autoscale updates the value:
   colormap_min.value = 0.00000000123
   # Widget automatically shows "1.23e-09" (formatter applied)

   # When the user types "0.5" in the input:
   # converter parses it → stored as 0.5
   # formatter presents it → widget shows "0.5"

The ``display_value`` property is also available for manual use:

.. code-block:: python

   label.ui_children = [f"Range: {obs_min.display_value} – {obs_max.display_value}"]

Reading and writing
~~~~~~~~~~~~~~~~~~~

Read and write through the :attr:`~ngapp.observable.Observable.value`
property:

.. code-block:: python

   print(scale.value)    # 1.0
   scale.value = 2.5     # listeners are called
   scale.value = 2.5     # no notification (value unchanged)

The setter compares the new value to the current one with ``==``.  If they
are equal, no listeners are invoked.

Listening to changes
~~~~~~~~~~~~~~~~~~~~

Register a callback with :meth:`~ngapp.observable.Observable.on_change`.
The callback receives ``(new_value, old_value)``:

.. code-block:: python

   def on_scale(new, old):
       print(f"scale changed from {old} to {new}")

   dispose = scale.on_change(on_scale)

   scale.value = 3.0     # prints "scale changed from 2.5 to 3.0"

   dispose()             # removes the listener
   scale.value = 4.0     # on_scale is NOT called

``on_change`` returns a **dispose function**.  Call it to unsubscribe.
Calling dispose more than once is safe.

Multiple listeners are supported; they fire in registration order.

Toggling booleans
~~~~~~~~~~~~~~~~~

For boolean observables, :meth:`~ngapp.observable.Observable.toggle` is a
shorthand for inverting the current value:

.. code-block:: python

   enabled = Observable(False, "enabled")
   enabled.toggle()      # enabled.value is now True
   enabled.toggle()      # enabled.value is now False

Widget binding
--------------

Direct prop binding
~~~~~~~~~~~~~~~~~~~

Pass an ``Observable`` directly as any component prop.  For
``ui_model_value``, binding is **two-way**: changes to the observable
update the widget, and user interaction updates the observable.  For all
other props, binding is **one-way** (observable → widget).

.. code-block:: python

   from ngapp.observable import Observable
   from ngapp.components import QSlider, QBtn

   opacity = Observable(1.0, "opacity")
   color = Observable("primary", "color")

   # Two-way: dragging the slider updates opacity.value, and vice versa
   slider = QSlider(ui_model_value=opacity, ui_min=0.0, ui_max=1.0, ui_step=0.01)

   # One-way: changing color.value updates the button color
   btn = QBtn(ui_label="Click", ui_color=color)

   opacity.value = 0.5   # slider moves to 0.5
   color.value = "red"   # button turns red

Assigning an ``Observable`` to a prop after construction also works:

.. code-block:: python

   slider.ui_model_value = another_observable

The previous binding is automatically disposed and the new one takes effect.

Explicit binding with ``bind()``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For non-standard widget attributes or events, use
:func:`~ngapp.observable.bind` to wire an ``Observable`` to any attribute
and event pair:

.. code-block:: python

   from ngapp.observable import bind

   bind(my_obs, widget, widget_attr="ui_label", event="on_change")

``bind`` returns a dispose function:

.. code-block:: python

   dispose = bind(opacity, slider)
   # later…
   dispose()

Batching changes
----------------

When multiple observables must be updated together,
:func:`~ngapp.observable.observable_batch` defers all listener calls until
the block exits.  This avoids redundant intermediate work (for example,
multiple render calls):

.. code-block:: python

   from ngapp.observable import observable_batch

   with observable_batch():
       position.value = (1.0, 2.0, 3.0)
       scale.value = 0.5
       enabled.value = True
   # All listeners are called here, once per changed observable.

Batches can be nested.  Listeners fire only when the outermost batch
completes.

Serialisation helpers
---------------------

Three functions make it easy to save and restore observable state without
writing per-field boilerplate.

:func:`~ngapp.observable.snapshot`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Collect all ``Observable`` values on an object into a plain dictionary,
keyed by their *name*:

.. code-block:: python

   class MyComponent:
       def __init__(self):
           self.scale = Observable(1.0, "scale")
           self.visible = Observable(True, "visible")

   comp = MyComponent()
   data = snapshot(comp)
   # {"scale": 1.0, "visible": True}

:func:`~ngapp.observable.restore`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Write values from a dictionary back into the matching observables.
Unknown keys are silently ignored:

.. code-block:: python

   restore(comp, {"scale": 2.5, "visible": False})
   # comp.scale.value == 2.5
   # comp.visible.value == False

Because ``restore`` sets each ``.value``, all listeners fire as usual.

:func:`~ngapp.observable.collect_observables`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Return a ``{name: Observable}`` mapping for programmatic access:

.. code-block:: python

   obs = collect_observables(comp)
   for name, o in obs.items():
       print(f"{name} = {o.value}")

Typical usage patterns
----------------------

Reactive side-effects
~~~~~~~~~~~~~~~~~~~~~

Wire domain logic to observables so that any change — from the UI, a
keyboard shortcut, or code — triggers the correct response:

.. code-block:: python

   class Viewer:
       def __init__(self):
           self.wireframe = Observable(True, "wireframe")
           self.wireframe.on_change(self._apply_wireframe)

       def _apply_wireframe(self, val, _old):
           self.renderer.show_wireframe = val
           self.scene.render()

       def toggle_wireframe(self):
           self.wireframe.toggle()   # one line — side-effects handled

Component with bound UI
~~~~~~~~~~~~~~~~~~~~~~~~

Declare observables in a component, bind them to widgets in a settings
panel:

.. code-block:: python

   # Component
   class SimView:
       def __init__(self, saved_settings):
           self.resolution = Observable(
               saved_settings.get("resolution", 256), "resolution"
           )
           self.resolution.on_change(self._on_resolution)

       def _on_resolution(self, val, _old):
           self.solver.set_resolution(val)
           self.solver.run()

   # Settings panel
   class SimSettings:
       def __init__(self, comp):
           slider = QSlider(
               ui_model_value=comp.resolution,
               ui_min=64, ui_max=1024, ui_step=64,
           )

Save and restore
~~~~~~~~~~~~~~~~

Persist the full observable state at save time, restore it when loading:

.. code-block:: python

   from ngapp.observable import snapshot, restore

   # Save
   settings = snapshot(comp)
   storage.save("settings", settings)

   # Restore (on next launch)
   saved = storage.load("settings")
   restore(comp, saved)

API reference
-------------

.. automodule:: ngapp.observable
   :members: Observable, bind, observable_batch, collect_observables, snapshot, restore
   :undoc-members:
