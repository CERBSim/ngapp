Parametric Sine Wave
====================

In this tutorial we create an app that plots a sine wave whose amplitude,
phase, frequency and number of points are set by the user. It shows the
reactive style that every ngapp app should follow (see :doc:`../reactivity`):
the components are built once, the inputs are bound to the case state, and
everything that depends on the inputs follows by itself.

First, we create a new app, following the steps in the
:doc:`Getting Started <../getting_started>` tutorial.

Imports
-------

.. code-block:: python

   from ngapp.app import App
   from ngapp.components import (
       Centered, Heading, Label, NumberInput, PlotlyComponent, Row, Show,
   )
   from ngapp.observable import computed

Note that neither ``numpy`` nor ``plotly`` is imported here: they are only
needed to draw the plot, which happens in the browser session. They are
imported where the figure is built, so the constructor of the app stays
cheap. The constructor also runs in compute jobs, where nothing is drawn.

Parameters in the case state
----------------------------

The parameters are part of the case: they are saved, loaded and shared with
the case. ``self.state.ref(key, default, converter)`` gives an observable
view of one state key. Its value is the value of the key, or the default
while the key is not set; assigning it stores ``converter(value)``.

.. code-block:: python

   class ParametricSine(App):
       def __init__(self):
           super().__init__()
           s = self.state
           self.amplitude = s.ref("amplitude", 2.0, float)
           self.phase = s.ref("phase", 0.0, float)
           self.frequency = s.ref("frequency", 5.0, float)
           self.nr_points = s.ref("nr_points", 500, int)

Inputs
------

Passing a ref as ``ui_model_value`` binds an input to the state key in both
directions: typing stores the value, and loading another case updates the
input.

.. code-block:: python

           inputs = Row(
               NumberInput(ui_label="Amplitude", ui_model_value=self.amplitude),
               NumberInput(ui_label="Phase", ui_model_value=self.phase),
               NumberInput(ui_label="Frequency", ui_model_value=self.frequency),
               NumberInput(ui_label="Nr Points", ui_model_value=self.nr_points),
           )

The ``converter`` of each ref turns the text of the input into a number. A
value that cannot be converted (an empty field) is ignored.

Derived values
--------------

A text that depends on the parameters is a
:func:`~ngapp.observable.computed` value. Used as text of a ``Label``, it is
updated in place whenever one of the values it reads changes:

.. code-block:: python

           self.points_per_period = computed(
               lambda: self.nr_points.value / max(self.frequency.value, 1e-12)
           )
           info = Label(
               computed(
                   lambda: f"{self.points_per_period.value:.0f} points per period"
               )
           )

A hint that is only needed for some parameter values is wrapped in
:class:`~ngapp.components.reactive.Show`. Its content is built the first
time the condition holds and only hidden afterwards:

.. code-block:: python

           hint = Show(
               lambda: self.points_per_period.value < 10,
               lambda: Label(
                   "Increase the number of points for a smooth curve",
                   ui_class="text-negative",
               ),
           )

The plot
--------

Drawing a Plotly figure is an imperative update of the browser. It belongs
in an effect of the plot component: the effect runs when the plot is shown
and again whenever a value it read changes.

.. code-block:: python

           self.plot = PlotlyComponent()
           self.plot.effect(self.draw)

           self.component = Centered(
               Heading("Parametric Sine"),
               inputs,
               info,
               hint,
               Row(self.plot),
           )

       def draw(self):
           import numpy as np
           import plotly.graph_objects as go

           amplitude = self.amplitude.value
           phase = self.phase.value
           frequency = self.frequency.value
           x = np.linspace(0, 1, max(self.nr_points.value, 2))
           y = amplitude * np.sin(2 * np.pi * frequency * x + phase)
           fig = go.Figure(go.Scatter(x=x, y=y, mode="lines"))
           fig.update_layout(
               title=f"Sine Wave f={frequency}, phi={phase}, A={amplitude}",
               xaxis_title="x",
               yaxis_title="Amplitude",
           )
           self.plot.draw(fig)

The figure is built with Plotly as usual and passed to the component with
``draw``. The effect reads the four parameters, so a change of any of them
redraws the plot; no event handler is registered.

It is important to set ``self.component``: it is the root of the page.

What happens on a change
------------------------

When the user types a new frequency:

* the input writes the state key ``frequency``;
* the label with the points per period gets its new text, and the hint
  appears or disappears;
* the effect draws the plot again.

The new label text and the hint reach the browser in one update message,
followed by the call that redraws the plot. No component is created or
removed, so the inputs keep focus and the page does not move.

Final State
-----------

The final state of the app should look like this:

.. image:: /_static/images/parametric_sine.png
    :width: 600px
    :align: center

The full code can be found in `parametric_sine <https://github.com/CERBSim/ngapp_demo_apps/tree/main/parametricsine>`_.
