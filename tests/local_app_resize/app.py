"""A plot and a canvas in a container that can be hidden and resized."""

import numpy as np

from ngapp.app import App
from ngapp.components import Div
from ngapp.components.visualization import PlotlyComponent, WebgpuComponent
from ngapp.observable import Observable, computed


class ResizeApp(App):
    def __init__(self):
        super().__init__()
        self.hidden = Observable(False)
        self.width = Observable(600)
        self.n = Observable(1)
        self.plot = PlotlyComponent(ui_style="width: 100%; height: 200px;", ui_class="t-plot")
        self.plot.effect(lambda: self.plot.draw({"data": [{"y": [0, self.n.value, 0]}]}))
        self.canvas = WebgpuComponent(width="100%", height="200px", ui_class="t-canvas")
        self.canvas.on_mounted(self._draw)
        self.component = Div(self.plot, self.canvas,
                             ui_style=computed(lambda: f"width: {self.width.value}px;"),
                             ui_hidden=self.hidden)

    def _draw(self):
        from webgpu.triangles import TriangulationRenderer

        points = np.array([[-1, -1, 0], [1, -1, 0], [0, 1, 0]], dtype=np.float32)
        self.canvas.draw([TriangulationRenderer(points, color=(0.2, 0.6, 1.0, 1.0))])
