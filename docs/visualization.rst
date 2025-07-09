
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
