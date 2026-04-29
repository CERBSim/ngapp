from __future__ import annotations

import numpy as np

from ngapp.app import App
from ngapp.components import Col
from ngapp.components.visualization import WebgpuComponent


class WebgpuDemoApp(App):
    """Minimal app that renders a 3D triangle on a WebgpuComponent."""

    def __init__(self):
        super().__init__()
        self.canvas = WebgpuComponent(width="400px", height="400px", id="gpu")
        self.canvas.on_mounted(self._draw)
        self.component = Col(self.canvas)

    def _draw(self):
        from webgpu.triangles import TriangulationRenderer

        points = np.array(
            [[-1, -1, 0], [1, -1, 0], [0, 1, 0]],
            dtype=np.float32,
        )
        renderer = TriangulationRenderer(
            points, color=(0.2, 0.6, 1.0, 1.0), label="triangle"
        )
        self.canvas.draw([renderer])
