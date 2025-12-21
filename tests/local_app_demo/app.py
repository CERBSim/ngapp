from __future__ import annotations

"""Small demo app used in tests for the local standalone runner.

The UI mimics a very small engineering app: two numeric inputs (``Length``
and ``Width``) and a ``Solve`` button. When the button is clicked, the app
computes the rectangle area and updates a result label. This is used by
end-to-end tests to verify that:

* events from the browser reach the Python app,
* Python-side computation runs based on the current input values, and
* the computed result is reflected back into the UI.
"""

from ngapp.app import App
from ngapp.components import Col, Label, QBtn, QInput


class InputChangeApp(App):
    """Small area calculation demo app.

    The user enters a length and width. When the ``Solve`` button is clicked,
    the app computes ``area = length * width`` and shows the result in a
    label. This pattern mirrors many ngapp tutorials where a few parameters
    drive a small computation and a result is displayed.
    """

    def __init__(self):
        self.length = QInput(
            ui_label="Length (m)",
            ui_model_value=5,
            ui_name="length",
        )
        self.width = QInput(
            ui_label="Width (m)",
            ui_model_value=3,
            ui_name="width",
        )
        self.button = QBtn(ui_label="Solve", ui_color="primary")
        self.result_label = Label("Result: waiting")

        self.button.on_click(self._on_click)

        root = Col(self.length, self.width, self.button, self.result_label)
        super().__init__(component=root, name="Local area demo")

    def _on_click(self):
        """Handle button clicks by computing and displaying the area."""

        try:
            length = float(self.length.ui_model_value or 0)
            width = float(self.width.ui_model_value or 0)
        except (TypeError, ValueError):
            self.result_label.text = "Result: invalid input"
            return

        area = length * width
        self.result_label.text = f"Area: {area} m^2"
