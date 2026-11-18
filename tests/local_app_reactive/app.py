"""Reference app in the reactive style.

Inputs are bound to keys of the case state, labels show computed values, the
warning list is a keyed ``For``, an optional input sits in a ``Show``, the
detail region is a ``Dynamic`` and the plot is drawn in an effect. The
constructor only builds components; nothing derived is evaluated before the
app is shown in a browser.

The "Rebuild panel" button replaces the children of a panel imperatively, the
way older apps update their UI.
"""

import math

from ngapp.app import App
from ngapp.components import (
    Centered,
    Col,
    Div,
    Dynamic,
    For,
    Heading,
    Label,
    NumberInput,
    PlotlyComponent,
    QBtn,
    QBtnToggle,
    QInput,
    Row,
    Show,
)
from ngapp.observable import computed


def check(amplitude, frequency, points):
    warnings = []
    if amplitude > 10:
        warnings.append("Amplitude above 10")
    if frequency <= 0:
        warnings.append("Frequency must be positive")
    elif points / frequency < 8:
        warnings.append("Fewer than 8 points per period")
    if points > 5000:
        warnings.append("More than 5000 points")
    return warnings


class ReactiveSineApp(App):
    def __init__(self):
        super().__init__()
        s = self.state
        self.amplitude = s.ref("amplitude", 1.0, float)
        self.frequency = s.ref("frequency", 2.0, float)
        self.phase = s.ref("phase", 0.0, float)
        self.points = s.ref("points", 200, lambda v: max(2, int(float(v))))
        self.advanced = s.ref("advanced", False, bool)
        self.view = s.ref("view", "summary")

        self.period = computed(
            lambda: (
                1 / self.frequency.value
                if self.frequency.value > 0
                else math.inf
            )
        )
        self.warnings = computed(
            lambda: check(
                self.amplitude.value,
                self.frequency.value,
                self.points.value,
            )
        )

        self.plot = PlotlyComponent(ui_style="width: 100%; height: 360px")
        self.plot.effect(self.draw)

        self.panel = Div(Label("Panel not built yet"), ui_class="q-pa-sm")
        self.builds = 0

        self.component = Centered(
            Heading("Reactive sine", level=4),
            Row(
                NumberInput(ui_label="Amplitude", ui_model_value=self.amplitude),
                NumberInput(ui_label="Frequency", ui_model_value=self.frequency),
                NumberInput(ui_label="Points", ui_model_value=self.points),
                QBtnToggle(
                    ui_model_value=self.advanced,
                    ui_options=[
                        {"label": "Basic", "value": False},
                        {"label": "Advanced", "value": True},
                    ],
                ),
            ),
            Show(
                self.advanced,
                lambda: Row(
                    NumberInput(ui_label="Phase", ui_model_value=self.phase),
                    QInput(ui_label="Note"),
                ),
            ),
            Label(
                computed(
                    lambda: f"Peak to peak: {2 * abs(self.amplitude.value):g}"
                )
            ),
            Label(computed(lambda: f"Period: {self.period.value:.4g}")),
            For(
                self.warnings,
                lambda w: Label(w, ui_class="text-negative"),
                otherwise=lambda: Label("No warnings", ui_class="text-positive"),
            ),
            QBtnToggle(
                ui_model_value=self.view,
                ui_options=[
                    {"label": "Summary", "value": "summary"},
                    {"label": "Samples", "value": "samples"},
                ],
            ),
            Dynamic(self.details),
            self.plot,
            Row(
                QBtn(ui_label="Rebuild panel", ui_color="primary").on_click(
                    self.rebuild_panel
                ),
                self.panel,
            ),
        )

    def details(self):
        if self.view.value == "summary":
            return Label(
                computed(
                    lambda: f"{self.points.value} points, "
                    f"{len(self.warnings.value)} warnings"
                )
            )
        return Col(*[self.sample(x) for x in (0.0, 0.125, 0.25, 0.375)])

    def value_at(self, x):
        return self.amplitude.value * math.sin(
            2 * math.pi * self.frequency.value * x + self.phase.value
        )

    def sample(self, x):
        return Label(computed(lambda: f"y({x:g}) = {self.value_at(x):+.3f}"))

    def draw(self):
        import numpy as np
        import plotly.graph_objects as go

        x = np.linspace(0, 1, self.points.value)
        y = self.amplitude.value * np.sin(
            2 * np.pi * self.frequency.value * x + self.phase.value
        )
        fig = go.Figure(go.Scatter(x=x, y=y, mode="lines"))
        fig.update_layout(xaxis_title="x", yaxis_title="y")
        self.plot.draw(fig)

    def rebuild_panel(self):
        self.builds += 1
        self.panel.ui_children = [
            Col(
                Label(f"Panel built {self.builds} times"),
                Row(*[Label(f"item {i}", ui_class="q-mr-sm") for i in range(5)]),
            )
        ]
