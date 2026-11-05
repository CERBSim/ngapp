"""Local test app of the page connection: on_load reports whether
the browser is connected (WebGPU views need it), an input is autosaved"""

from ngapp.app import App, AppConfig
from ngapp.components import Col, Label, QInput


class PagesApp(App):
    autosave = True

    def __init__(self):
        super().__init__()
        self.text = QInput(id="text", ui_label="Text", ui_model_value="")
        self.loaded = Label("not loaded", id="loaded")
        self.on_load(self._loaded)
        self.component = Col(self.text, self.loaded)

    def _loaded(self):
        from webgpu import platform

        self.loaded.text = f"browser connected: {platform.js is not None}"


config = AppConfig(
    python_class=PagesApp,
    name="Local pages demo",
    version="0.0.1",
    frontend_dependencies=[],
    frontend_pip_dependencies=[],
)
