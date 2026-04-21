Probe VTK
====================

In this tutorial, we will create a web application that visualizes VTK files with unstructured data and allows probing of values at specific points.
The full code for this tutotial can be found in `probe vtk <https://github.com/CERBSim/ngapp_demo_apps/tree/main/probevtk>`_ .

We follow the steps in the :doc:`Getting Started <../getting_started>` tutorial to create a new app.

Components and Layout
------------------------------------

Then, we import the necessary libraries and components

.. code-block:: python

    import numpy as np
    from ngapp.app import App
    from ngapp.components import *
        
Since we want import VTK files, we can use the QFile component  check the :py:class:`~ngapp.components.qcomponents.QFile` documentation

.. code-block:: python

    self.file_upload = QFile(
        id="file_upload",
        ui_label="Upload VTU File",
        ui_accept=".vtu",
        ui_multiple=False,
        ui_clearable=True,
        ui_outlined=True,
        ui_bg_color="blue",
    )
    self.file_upload.on_update_model_value(self._on_updataed_file)
    self.file_upload.on_rejected(self._on_rejected)
    
The _on_rejected method displays an error message when the uploaded file is not accepted

.. code-block:: python

    def _on_rejected(self):
        self.quasar.dialog(
            {"title": "File not supported", "message": "Only .vtu files are accepted"}
        )

We will implement the _on_updataed_file method to handle the uploaded file later.
Next, we add the FileUpload component to a Toolbar for better layout, check the :py:class:`~ngapp.components.helper_component.ToolBar` documentation

.. code-block:: python

    self.toolbar = ToolBar(
        app=self,
        app_name="ProbeVTK",
        ui_class="text-white bg-primary",
        buttons=[self.file_upload, QSpace(), QSpace()],
    )
    
We add :py:class:`~ngapp.components.helper_component.NumberInput` components to allow users to specify the probe point coordinates

.. code-block:: python

    self.point1_x = NumberInput(
        ui_label="Point 1 X", ui_model_value=0
    )
    self.point1_y = NumberInput(
        ui_label="Point 1 Y", ui_model_value=0
    )
    self.point1_z = NumberInput(
        ui_label="Point 1 Z", ui_model_value=0
    )

The same for point 2.
Furthermore, we add a NumberInput to specify the number of samples along the probe line.

.. code-block:: python


    self.number_of_samples = NumberInput(
        ui_label="Number of Samples", ui_model_value=50
    )
    

Finally, we add a PlotlyComponent to visualize the probed values and a VTK component which will render the VTK file.

.. code-block:: python

    self.plot = PlotlyComponent()
    self.vtk_component = VtkComponent(self)
    
    
We arrange all components in a layout using Column and Row components, see the :py:class:`~ngapp.components.helper_component.Col` and :py:class:`~ngapp.components.helper_component.Row` documentation.
Using weights, we can control the relative sizes of the columns and rows.

.. code-block:: python

    self.component = Div(
        self.toolbar,
        Row(
            Col(self.vtk_component),
            Col(
                QCard(
                    QCardSection(
                        Row(
                            Heading("Probe Points", level=5, ui_style="padding-right:50px"),
                            Heading("Pick Point 1 with Shift+Click and Point 2 with Alt+Click", level=6),
                        ),
                        Row(
                            self.point1_x,
                            self.point1_y,
                            self.point1_z,
                            weights=[4, 4, 4],
                        ),
                        Row(
                            self.point2_x,
                            self.point2_y,
                            self.point2_z,
                            weights=[4, 4, 4],
                        ),
                        Row(
                            self.number_of_samples,
                        ),
                        Heading("Probe Options", level=5),
                    ),
                    ui_flat=True,
                ),
                QCard(QCardSection(self.plot), ui_flat=True),
                weights=[6, 6],
                ui_style="height: 100%;",
            ),
            weights=[6, 6],
        ),
        id="main_component",
    )


    
VTK Component
--------------------
The VTK component is responsible for rendering the VTK file and probing the values at specified points.
We define the VtkComponent class inheriting from BaseVtkComponent, check the :py:class:`~ngapp.components.vtk_component.BaseVtkComponent` documentation

.. code-block:: python

    class VtkComponent(BaseVtkComponent):
        def __init__(self, app, *args, **kwargs):
            self._on_click_callbacks = []
            self.probed_points_array = None
            self.probed_values_array = None
            self.app = app
            self.point_actors = []
            self.line_actor = None
            self.picker = None
            super().__init__(*args, **kwargs)
            
        def on_click(self, callback):
            self._on_click_callbacks.append(callback)
            
A class inheriting from BaseVtkComponent must implement a draw method, which is responsible for rendering.
To load vtu files, we use the vtkXMLUnstructuredGridReader from the Python VTK package.
The point data is then extracted and converted to vtk.js objects for rendering.

.. code-block:: python

    def draw(self):
        if self.app.file == {}:
            return
        vtkCellPicker = self.vtk.Rendering.Core.vtkCellPicker.newInstance
        self.picker = vtkCellPicker()
        self.picker.setTolerance(0.001)
        self.picker.setPickFromList(True)
        self.renderWindow.render()
        try:
            self._load_data_file()
        except Exception as e:
            print(f"Error loading VTK file: {e}")
            
    def _load_data_file(self):
        """Try to load VTI or VTU file using Python VTK"""
        self.renderer.removeAllViewProps()
        try:
            import vtk as pyVTK

            with temp_dir_with_files(self.app.file, return_list=False) as file_path:
                reader = pyVTK.vtkXMLUnstructuredGridReader()
                reader.SetFileName(file_path)
                reader.Update()
                data = reader.GetOutput()
                self._visualize_unstructured_grid(data)
        except ImportError:
            raise
            
    def _visualize_unstructured_grid(self, py_data):
        """Simplified VTU visualization - convert Python VTK to vtk.js polydata"""
        import vtk as pyVTK

        # Extract surface geometry
        geometryFilter = pyVTK.vtkGeometryFilter()
        geometryFilter.SetInputData(py_data)
        geometryFilter.Update()
        surface = geometryFilter.GetOutput()

        # Get bounds for probe initialization
        bounds = surface.GetBounds()
        self.app.point1_x.ui_model_value = bounds[0]
        self.app.point1_y.ui_model_value = bounds[2]
        self.app.point1_z.ui_model_value = bounds[4]
        self.app.point2_x.ui_model_value = bounds[1]
        self.app.point2_y.ui_model_value = bounds[3]
        self.app.point2_z.ui_model_value = bounds[5]

        # Extract point coordinates
        nr_points = surface.GetNumberOfPoints()
        points_flat = []
        for i in range(nr_points):
            pt = surface.GetPoints().GetPoint(i)
            points_flat.extend(pt)

        # Extract cell connectivity
        cells_flat = []
        for i in range(surface.GetNumberOfCells()):
            cell = surface.GetCell(i)
            num_cell_pts = cell.GetNumberOfPoints()
            cells_flat.append(num_cell_pts)
            for j in range(num_cell_pts):
                cells_flat.append(cell.GetPointId(j))

        # Extract scalars
        py_scalars = surface.GetPointData().GetArray(0)
        scalar_values = [
            py_scalars.GetValue(i) for i in range(py_scalars.GetNumberOfTuples())
        ]

        # Store the original Python VTK dataset for probing
        self.py_dataset = py_data

        # Now create vtk.js objects
        vtk = self.vtk
        vtkPolyData = vtk.Common.DataModel.vtkPolyData
        vtkDataArray = vtk.Common.Core.vtkDataArray
        vtkMapper = vtk.Rendering.Core.vtkMapper.newInstance
        vtkActor = vtk.Rendering.Core.vtkActor.newInstance

        # Create polydata
        polyData = vtkPolyData.newInstance()

        # Set points using macro
        polyData.getPoints().setNumberOfComponents(3)
        polyData.getPoints().setData(self.js.Float64Array._new(points_flat), 3)

        # Set cells using macro
        polyData.getPolys().setData(self.js.Int32Array._new(cells_flat))

        # Set scalars
        polyData.getPointData().setScalars(
            vtkDataArray.newInstance(
                {
                    "name": "scalars",
                    "values": self.js.Float64Array._new(scalar_values),
                }
            )
        )

        # Create mapper and actor
        mapper = vtkMapper()
        mapper.setInputData(polyData)
        mapper.setScalarRange(min(scalar_values), max(scalar_values))
        actor = vtkActor()
        actor.setMapper(mapper)

        # Configure actor properties for visibility
        actor.getProperty().setEdgeVisibility(False)
        self.actor = actor
        self.picker.addPickList(self.actor)
        self.renderer.addActor(actor)
        self.renderer.resetCamera()
        self.renderWindow.render()

The temp_dir_with_files, see :py:func:`~ngapp.utils.temp_dir_with_files`, is a utility function that creates a temporary directory to store the uploaded file for reading with VTK, since VTK readers typically read from file paths.
We still need to implement the data extraction from the uploaded file in the _on_updataed_file method.
The filename and file can be accessed from the event object passed to the method.

.. code-block:: python

    def _on_updataed_file(self, event):
        value = event.value
        if value == None:
            self.file = {}
            self.vtk_component.renderer.removeAllViewProps()
            if self.vtk_component.picker:
                self.vtk_component.picker.initializePickList()
            self.vtk_component.renderWindow.render()
        else:
            self.file = {value.name: value.arrayBuffer()}
            self.vtk_component.draw()

        
Probing Values
------------------------------
To probe values at specific points, we implement the _handle_probe method.
Here, we create a line source between the two specified points and use vtkProbeFilter to interpolate scalar values along the line.
Finally, we store the probed points and values in numpy arrays for easy plotting.

.. code-block:: python

    def _handle_probe(self):
        """Probe scalar values along line using Python VTK vtkProbeFilter for interpolation"""
        import vtk as pyVTK
    
        point1 = [self.app.point1_x.ui_model_value, self.app.point1_y.ui_model_value, self.app.point1_z.ui_model_value]
        point2 = [self.app.point2_x.ui_model_value, self.app.point2_y.ui_model_value, self.app.point2_z.ui_model_value]
    
        # Check if probe points are valid
        if None in point1 or None in point2:
            return
    
        num_samples = int(self.app.number_of_samples.ui_model_value)
        # Create a line source with many points for probing
        lineSource = pyVTK.vtkLineSource()
        lineSource.SetPoint1(point1)
        lineSource.SetPoint2(point2)
        lineSource.SetResolution(num_samples)
        lineSource.Update()
    
        # Use vtkResampleWithDataSet for interpolated probing
        probe = pyVTK.vtkResampleWithDataSet()
        probe.SetInputConnection(lineSource.GetOutputPort())
        probe.SetSourceData(self.py_dataset)
        probe.Update()
    
        # Get the probed data
        probed_data = probe.GetOutput()
        num_points = probed_data.GetNumberOfPoints()
        scalars = probed_data.GetPointData().GetArray(0)
    
        probed_points = [list(probed_data.GetPoint(i)) for i in range(num_points)]
        probed_values = [scalars.GetValue(i) for i in range(num_points)]
        self.probed_points_array = np.array(probed_points)
        self.probed_values_array = np.array(probed_values)
    
        # Update plot
        self.app.draw_plotly()
    
        
Having the probed points and values stored in numpy arrays allows us to easily create plots using the PlotlyComponent.
We implement the draw_plotly method in the main app class to create a line plot of the probed values.

.. code-block:: python

    def draw_plotly(self):
        import plotly.graph_objects as go
    
        points = self.vtk_component.probed_points_array
        values = self.vtk_component.probed_values_array
    
        if points is None or len(points) == 0:
            return
    
        # Compute distance along the probe line using numpy
        deltas = np.diff(points, axis=0)
        segment_lengths = np.sqrt(np.sum(deltas**2, axis=1))
        distances = np.concatenate([[0], np.cumsum(segment_lengths)])
    
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=distances, y=values, mode="lines+markers"))
        fig.update_layout(title="Probed Scalar Values Along Line", xaxis_title="Distance along probe line", yaxis_title="Scalar Value")
        self.plot.draw(fig)


Since we want to have interactive probing, we register the _handle_probe method to be called whenever the probe point coordinates or number of samples change.
To do this, we use the on_update_model_value method of the NumberInput components.

.. code-block:: python

    self.app.point1_x.on_update_model_value(self.vtk_component._handle_probe)
    self.app.point1_y.on_update_model_value(self.vtk_component._handle_probe)
    self.app.point1_z.on_update_model_value(self.vtk_component._handle_probe)
    self.app.point2_x.on_update_model_value(self.vtk_component._handle_probe)
    self.app.point2_y.on_update_model_value(self.vtk_component._handle_probe)
    self.app.point2_z.on_update_model_value(self.vtk_component._handle_probe)
    self.app.number_of_samples.on_update_model_value(self.vtk_component._handle_probe)


We also want to handle mouse clicks to probe values at specific points.
We implement the _handle_left_button_press method to achieve this.
To pick the first or second probe point, the user can hold the Shift or Alt key while clicking.

.. code-block:: python

    def _handle_left_button_press(self, callData):
        pos = callData.position
        self.picker.pick([pos.x, pos.y, 0], self.renderer)
        if callData.shiftKey:
            x, y, z = self.picker.getPickPosition()
            self.app.point1_x.ui_model_value = round(x, 3)
            self.app.point1_y.ui_model_value = round(y, 3)
            self.app.point1_z.ui_model_value = round(z, 3)
            self._handle_probe()
        if callData.altKey:
            x, y, z = self.picker.getPickPosition()
            self.app.point2_x.ui_model_value = round(x, 3)
            self.app.point2_y.ui_model_value = round(y, 3)
            self.app.point2_z.ui_model_value = round(z, 3)
            self._handle_probe()
        
    # add this to draw method
    def draw(self):
        ...
        interactor = self.renderWindow.getInteractor()
        interactor.onLeftButtonPress(
            self.create_event_handler(
                self._handle_left_button_press, prevent_default=False
            )
        )
    
The final version of the app should look like this:

.. image:: ../_static/images/probe_vtk.png
   :align: center
   :width: 800px