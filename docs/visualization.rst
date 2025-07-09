
Visualization
=============

NGApp provides powerful components for interactive scientific visualization. Two of the most important are :class:`~ngapp.components.visualization.PlotlyComponent` and :class:`~ngapp.components.visualization.WebgpuComponent`.

PlotlyComponent
---------------

The :class:`~ngapp.components.visualization.PlotlyComponent` lets you embed interactive Plotly plots in your NGApp application. It supports both static and dynamic plots, and can save images automatically if a filename is provided.

**Example:**

.. code-block:: python

   import plotly.graph_objects as go
   from ngapp.components.visualization import PlotlyComponent

   fig = go.Figure(go.Scatter(y=[2, 1, 4, 3]))
   plot = PlotlyComponent()
   plot.draw(fig)

**Key features:**

- Supports all Plotly figures (2D/3D, scatter, surface, etc.)
- Responsive and embeddable in any NGApp layout

WebgpuComponent
---------------

The :class:`~ngapp.components.visualization.WebgpuComponent` provides a GPU-accelerated 3D canvas for advanced scientific visualization. It uses the `webgpu Python package <https://github.com/CERBSim/webgpu>`_ to render custom 3D scenes directly in the browser, supporting real-time updates and user interaction.

**Example:**

.. code-block:: python

   from ngapp.components.visualization import WebgpuComponent
   webgpu = WebgpuComponent()
   # ... create a webgpu scene ...
   webgpu.draw(scene)

**Key features:**

- High-performance 3D rendering in the browser
- Integrates with the Python webgpu ecosystem
- Custom event handling for mouse and interaction events
- Can capture screenshots as images or data URLs

Have a look at the webgpu documentation for hwo to build scenes or at the `ngsolve_webgpu documentation <https://github.com/CERBSim/ngsolve_webgpu>`_ for examples of using the finite element framework NGSolve with WebGPU.
