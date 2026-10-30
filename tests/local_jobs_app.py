"""App of the tests of local jobs on the SQLite store (test_sqlite_jobs.py);
the job processes import it from the tests directory"""

import os
import time

import numpy as np

from ngapp.app import App, AppConfig
from ngapp.components import QInput
from ngapp.components.basecomponent import Component
from ngapp.jobs import compute, progress


class Solver(Component):
    def __init__(self):
        super().__init__("div", id="solver")
        self.maxh = QInput(id="maxh", ui_model_value=0.25)
        self.result = QInput(id="result", ui_label="no result")
        self.ui_children = [self.maxh, self.result]

    @compute(timeout=120)
    def mesh(self, order=1):
        geometry = self.app.state.geometry
        n = int(round(1 / self.maxh.ui_model_value)) * 5000
        self.result.ui_label = "meshing"
        self.state.mesh = np.arange(n, dtype=np.float64) * order + geometry[0]
        self.state.n = n
        self.result.ui_label = f"{n} elements"

    @compute(timeout=120)
    def steps(self, n=3, delay=0.0, crash_at=None, fail_at=None):
        done = len(self.state.list("log"))
        for i in range(done, n):
            if i == crash_at:
                os._exit(9)
            if i == fail_at:
                raise RuntimeError(f"failed at step {i}")
            self.state.list("log").append(i)
            progress((i + 1) / n, f"step {i}")
            time.sleep(delay)
        self.state.done = n

    @compute(timeout=1)
    def slow(self):
        time.sleep(60)


class JobsApp(App):
    def __init__(self):
        super().__init__()
        self.solver = Solver()
        self.component = self.solver


config = AppConfig(JobsApp, name="local jobs", version="1")
