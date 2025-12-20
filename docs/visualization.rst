
Visualization
=============

ngapp provides powerful components for interactive scientific visualization.
Two of the most important are
:class:`~ngapp.components.visualization.PlotlyComponent` and
:class:`~ngapp.components.visualization.WebgpuComponent`. For a full
reference of all visualization helpers, see :doc:`api_components`.

PlotlyComponent
---------------

The :class:`~ngapp.components.visualization.PlotlyComponent` lets you
embed interactive `Plotly <https://plotly.com/python/>`_ figures inside
your ngapp application. You can use the full Plotly Python API
(`graph_objects <https://plotly.com/python/graph-objects/>`_ or
`express <https://plotly.com/python/plotly-express/>`_) to construct
figures in Python and then render them as live, zoomable, pannable
plots in the browser.

Plotly supports a wide range of visualizations (2D/3D scatter, surface
plots, contour plots, maps, histograms, subplots, animations, etc.),
all of which can be displayed through this component.

**Example:**

.. code-block:: python

   import plotly.graph_objects as go
   from ngapp.components.visualization import PlotlyComponent

   fig = go.Figure(go.Scatter(y=[2, 1, 4, 3]))
   plot = PlotlyComponent()
   plot.draw(fig)

**Key features:**

- Supports all Plotly figures (2D/3D, scatter, surface, contour,
    volume, maps, etc.)
- Fully interactive in the browser (zoom, pan, hover tooltips,
    legends, saving as PNG from the mode bar)
- Works with both :mod:`plotly.graph_objects` and
    :mod:`plotly.express` figures
- Embeddable in any ngapp layout alongside other components

For more details on what you can build with Plotly, see the official
Python documentation:

- Getting started guide:
    https://plotly.com/python/getting-started/
- Figure structure and layout system:
    https://plotly.com/python/renderers/
- Gallery of example charts:
    https://plotly.com/python/

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


Using NGSolve solution fields
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The `ngsolve_webgpu <https://github.com/CERBSim/ngsolve_webgpu>`_
package provides ready-made WebGPU renderers for NGSolve meshes and
CoefficientFunctions. You can combine these renderers with
``WebgpuComponent`` to display finite element solution fields directly
inside an ngapp UI.

**Basic example (2D scalar CoefficientFunction):**

.. code-block:: python

     from ngsolve import Mesh, H1, GridFunction, unit_square
     from ngsolve_webgpu.mesh import MeshData
     from ngsolve_webgpu.cf import FunctionData, CFRenderer
     from webgpu.colormap import Colorbar
     from webgpu import Scene

     from ngapp.components.visualization import WebgpuComponent

     # Build an NGSolve mesh and solution
     mesh = Mesh(unit_square.GenerateMesh(maxh=0.1))
     V = H1(mesh, order=2)
     u = GridFunction(V)
     u.Set(x * y)  # example solution field

     # Convert to WebGPU renderers using ngsolve_webgpu
     mesh_data = MeshData(mesh)
     func_data = FunctionData(mesh_data, u, order=2)
     cf_renderer = CFRenderer(func_data)
     colorbar = Colorbar(colormap=cf_renderer.colormap)

     # Create a webgpu.Scene and attach it to WebgpuComponent
     scene = Scene([cf_renderer, colorbar])
     canvas = WebgpuComponent(width="800px", height="600px")
     canvas.draw(scene)

This draws the scalar field ``u`` on the mesh with an interactive
WebGPU renderer and a linked colorbar, all embedded as an ngapp
component.

For more advanced examples of visualizing NGSolve solution fields with
WebGPU, see the tutorials in the ngsolve_webgpu repository:

- Function visualization examples:
    https://github.com/CERBSim/ngsolve_webgpu/blob/main/docs/functions.ipynb
- Extended WebGPU demo notebook (geometry, functions, clipping, etc.):
    https://github.com/CERBSim/ngsolve_webgpu/blob/main/webgpu.ipynb


VtkComponent
------------

The :class:`~ngapp.components.visualization.BaseVtkComponent` allows you to embed interactive 3D visualizations using the VTK.js framework, directly from Python. To use it, you should subclass `BaseVtkComponent` and implement your own drawing logic using the `vtk` interface provided by the component. This gives you full access to VTK.js features for scientific and engineering visualization in the browser.


**How to use:**

1. **Subclass BaseVtkComponent**
2. **Implement a draw method** where you create and configure your VTK pipeline using the ``self.vtk`` object (which exposes the VTK.js API in Python).
3. **Connect events** using ``self.create_event_handler`` to bridge VTK.js events to Python callbacks.

**Example: Interactive Cone Picker**

.. code-block:: python

   from ngapp.components.visualization import BaseVtkComponent

   class ConePickerComponent(BaseVtkComponent):
       def __init__(self, *args, **kwargs):
           super().__init__(*args, **kwargs)
           self._on_click_callbacks = []

       def on_click(self, callback):
           """Register a callback for picking events. Callback receives (pickedActor, cellId)."""
           self._on_click_callbacks.append(callback)

       def draw(self):
           vtk = self.vtk
           vtkConeSource = vtk.Filters.Sources.vtkConeSource.newInstance
           vtkMapper = vtk.Rendering.Core.vtkMapper.newInstance
           vtkActor = vtk.Rendering.Core.vtkActor.newInstance
           vtkCellPicker = vtk.Rendering.Core.vtkCellPicker.newInstance
           renderer = self.renderer
           interactor = self.renderWindow.getInteractor()

           # Create a cone
           coneSource = vtkConeSource({"resolution": 20})
           mapper = vtkMapper()
           mapper.setInputConnection(coneSource.getOutputPort())
           actor = vtkActor()
           actor.setMapper(mapper)
           renderer.addActor(actor)
           renderer.resetCamera()
           self.renderWindow.render()

           # Picker for mouse events
           self.picker = vtkCellPicker()
           self.picker.setTolerance(0.001)

           # Connect VTK.js event to Python using create_event_handler
           interactor.onLeftButtonPress(
               self.create_event_handler(self._handle_left_button_press)
           )

       def _handle_left_button_press(self, callData):
           pos = callData.position
           self.picker.pick([pos.x, pos.y, 0], self.renderer)
           cellId = self.picker.getCellId()
           actors = self.picker.getActors()
           if actors and cellId >= 0:
               pickedActor = actors[0]
               for callback in self._on_click_callbacks:
                   callback(pickedActor, cellId)

**How event handling works:**

- Use ``self.create_event_handler(python_callback)`` to wrap a Python function so it can be called from VTK.js events (like mouse clicks).
- Register the handler with VTK.js event methods (e.g., ``interactor.onLeftButtonPress``).
- Your callback will receive event data (e.g., picked actor and cell id) and can update the UI or trigger other logic in Python.

**Key points:**
- The ``vtk`` attribute gives you access to the full VTK.js API from Python.
- Use ``self.renderer`` and ``self.renderWindow`` to manage the scene and rendering.
- Use ``self.create_event_handler`` to bridge VTK.js events to Python callbacks.
- You can implement picking and other interactions for interactive visualization.
- See the VTK.js documentation for available sources, mappers, actors, and interaction patterns: https://kitware.github.io/vtk-js/docs/

This approach lets you build highly interactive, browser-based 3D visualizations with the full power of VTK, but using Python code.
