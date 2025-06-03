# pylint: disable=import-outside-toplevel
"""Components for data visualization"""
import asyncio
import base64
import os
from typing import Any, Callable

import numpy as np

from ..utils import read_file, write_file
from .basecomponent import Component
from .helper_components import Col, Div, Event, NumberInput, Row
from .qcomponents import QBtn, QBtnGroup, QInput, QSlider, QToggle, QTooltip


class WebguiComponent(Component):
    """Webgui component"""

    changed: bool = False

    def __init__(
        self,
        id: str = "",
        caption: str | None = None,
        webgui_data: dict[str, Any] | None = None,
        **kwargs,
    ):
        super().__init__(id=id, component="WebguiComponent", **kwargs)

        self.changed = False
        self._canvas_buttons = []
        self._caption = caption
        self._canvas_buttons_callbacks = []
        self._webgui_data = webgui_data or {}

        self._settings = {}
        self._default_settings = {}

        self._props["style"] = "min-width: 500px; height: 500px"

        self.on("mounted", self.__on_mounted)
        self.on("load", self.__on_load)
        self.on("update_settings", self.update_settings)

    async def _create_screenshot(self, width: int, height: int) -> None:
        filename = self._fullid
        screenshot = await _generate_webgui_screenshot(
            filename, self.webgui_data, width, height
        )
        self.storage.set("screenshot", screenshot)
        self.storage.save()
        self._update_frontend()

    def create_screenshot(self, width: int = 1042, height: int = 852) -> None:
        """
        Create a screenshot of the webgui. The image is stored in the storage as a base64 encoded string.

        :param width: (int) Width of the screenshot. Defaults to 1042.
        :param height: (int) Height of the screenshot. Defaults to 852.
        :param depends_on: (list[str] | None) List of job IDs that this job depends on.
        """
        asyncio.run(self._create_screenshot(width=width, height=height))

    @property
    def screenshot(self):
        """Get the webgui screenshot"""
        return self.storage.get("screenshot")

    @property
    def webgui_data(self) -> dict[str, Any]:
        """get webgui data (either from file, input or dynamic data)"""
        data = self._webgui_data
        if "gui_settings" not in data:
            data["gui_settings"] = {}
        data["gui_settings"].update(self._settings)
        return data

    @property
    def radius(self) -> QInput:
        return self._webgui_data.get("mesh_radius", 1.0)

    def update_settings(self, event: Event) -> None:
        try:
            normal_settings = event.value["settings"]
            default_settings = event.value.get("default_settings", None)
            self._settings.update(normal_settings)
            if default_settings is not None:
                self._default_settings.update(default_settings)
        except Exception as e:
            print("error in WebguiComponent.update_settings", type(e), str(e))

    def on_click(self, callback):
        self.on("clickWebgui", callback)

    def __on_load(self):
        self._webgui_data = self.storage.get("webgui_data") or {}
        self._settings = self.storage.get("settings") or {}
        if self._webgui_data:
            self._update_frontend(method="Redraw", data=self.webgui_data)

    def __on_mounted(self) -> None:
        if self._webgui_data:
            self._update_frontend(method="Redraw", data=self.webgui_data)

    @staticmethod
    def canvas_button(
        ui_icon: str = "",
        ui_label: str = "",
        ui_tooltip: str = "",
        on_click: Callable[[Any], None] | None = None,
        **kwargs,
    ) -> QBtn:
        """
        Create a canvas button

        :param ui_icon: Icon name
        :param ui_label: Button label
        :param ui_tooltip: Tooltip text
        :param on_click: Callback function
        :param kwargs: Additional arguments for QBtn
        """
        kwargs["ui_dense"] = kwargs.get("ui_dense", True)
        kwargs["ui_size"] = kwargs.get("ui_size", "12px")
        kwargs["ui_flat"] = kwargs.get("ui_flat", True)
        kwargs["ui_color"] = kwargs.get("ui_color", "secondary")
        kwargs["ui_icon"] = ui_icon
        kwargs["ui_label"] = ui_label
        button = QBtn(QTooltip(ui_tooltip), **kwargs)
        if on_click is not None:
            return button.on_click(on_click)
        return button

    @property
    def slot_buttons(self) -> list[Component]:
        """Get custom components to webgui buttons"""
        return self.ui_slots.get("buttons", [])

    @slot_buttons.setter
    def slot_buttons(self, components: list[Component]) -> None:
        self._set_slot("buttons", components)

    @property
    def slot_canvas(self) -> list[Component]:
        """Get custom components to webgui canvas"""
        return self.ui_slots.get("canvas_components", [])

    @slot_canvas.setter
    def slot_canvas(self, components: list[Component]) -> None:
        self._set_slot("canvas_components", components)

    def clear(self):
        """Clear webgui canvas"""
        self._update_frontend(method="Clear")

    def draw(
        self, *args, data: dict | None = None, redraw=False, **kwargs
    ) -> dict:
        """draw object (arguments compatible with netgen.webgui.Draw)"""
        from netgen.webgui import Draw

        if data is None:
            scene = Draw(*args, **kwargs)
            data = scene.GetData()

        self._settings = data["gui_settings"]
        self._webgui_data = data
        self.storage.set("settings", self._settings)
        self.storage.set("webgui_data", self._webgui_data)
        self.changed = True
        method = "Redraw" if redraw else "Draw"
        self._update_frontend(method=method, data=data)
        self._handle("draw")
        return self._webgui_data

    def toggle_fullscreen(self) -> None:
        """Toggle fullscreen"""
        self._update_frontend({}, "ToggleFullScreen")

    def toggle_mesh(self) -> None:
        """Toggle mesh"""
        self._update_frontend({}, "ToggleMesh")

    def set_camera(self, data: dict = {}) -> None:
        """Set camera"""
        self._update_frontend(data, "SetCamera")

    def set_colormap(self, data: dict = {}) -> None:
        """Set colormap"""
        self._update_frontend(data, "SetColormap")

    def set_clipping_plane(self, data: dict) -> None:
        """Set clipping plane"""
        self._update_frontend(data, "SetClippingPlane")

    def set_color(
        self,
        *,
        faces: dict[int, list[float]] | list[float] | None = None,
        edges: dict[int, list[float]] | list[list[float]] | None = None,
    ) -> None:
        """Set color of faces and edges"""
        data = {}
        if faces is not None:
            data["faces"] = faces
        if edges is not None:
            data["edges"] = edges
        self._update_frontend(data, "SetColor")

    def update_camera_settings(self):
        """Update camera settings

        :param callback: Callback function to call after settings are updated
        """
        self._update_frontend({}, "GetCameraSettings")

    def on_draw(self, callback: Callable) -> None:
        """Set callback for draw event"""
        self.on("draw", callback)


class Clipping(Col):
    """Clipping component"""

    def __init__(self, webgui: WebguiComponent, *args, **kwargs):
        self._webgui = webgui
        label = Div("Clip", ui_class="q-mx-xs")
        self.switch = QToggle(
            id="clippingenable", ui_model_value=False, ui_dense=True
        ).on_update_model_value(self._clippingenable)
        self.buttons = QBtnGroup(
            QBtn(
                ui_label="XY",
                ui_disable=True,
            ).on_click(self.__on_button_click),
            QBtn(
                ui_label="XZ",
                ui_disable=True,
            ).on_click(self.__on_button_click),
            QBtn(
                ui_label="YZ",
                ui_disable=True,
            ).on_click(self.__on_button_click),
        )

        self.slider = QSlider(
            id="clippingslider",
            ui_step=0.001,
            ui_min=0,
            ui_max=1,
            ui_model_value=0.5,
            ui_disable=True,
            ui_style="width: 150px;",
        ).on_update_model_value(self._on_slider_change)
        ui_class = kwargs.pop("ui_class", "")
        ui_class = f"q-ma-sm {ui_class}"
        super().__init__(
            Row(label, self.switch),
            self.buttons,
            Col(self.slider),
            ui_class=ui_class,
            *args,
            **kwargs,
        )

    def __on_button_click(self, args: dict[str, Any]) -> None:
        plane = args["comp"].ui_label
        clip_dir = {"XY": 2, "XZ": 1, "YZ": 0}.get(plane, 2)
        clip = self._webgui._settings["Clipping"]
        n_current = np.array(
            [clip["x"], clip["y"], clip["z"]], dtype=np.float64
        )
        n_new = np.array([0.0, 0.0, 0.0], dtype=np.float64)
        n_new[clip_dir] = 1.0
        if np.dot(n_current, n_new) > 0.5:
            n_new = -n_new

        self._webgui.set_clipping_plane({"vec": list(n_new)})

    def _on_slider_change(self, args: dict[str, Any]) -> None:
        comp = args["comp"]
        clip = self._webgui._settings["Clipping"]
        n = np.array(
            [
                clip["x"],
                clip["y"],
                clip["z"],
            ],
            dtype=np.float64,
        )
        r = self._webgui.radius
        p0 = -r * n
        p1 = r * n
        d0 = np.dot(n, p0)
        d1 = np.dot(n, p1)
        dist = d0 + comp.ui_model_value * (d1 - d0)
        self._webgui.set_clipping_plane({"dist": dist})

    def _clippingenable(self, args: dict[str, Any]) -> None:
        enable = args["comp"].ui_model_value
        self._webgui.set_clipping_plane({"enable": enable})
        self.slider.ui_disable = not enable
        for button in self.buttons.ui_children:
            button.ui_disable = not enable


class CameraView(Col):
    """Camera view component"""

    def __init__(
        self,
        webgui: WebguiComponent,
        *args,
        **kwargs,
    ):

        self._webgui = webgui
        self.buttons = QBtnGroup(
            QBtn(
                id="cameraplane_xy",
                ui_label="XY",
            ).on_click(self.__cameraplane),
            QBtn(
                id="cameraplane_xz",
                ui_label="XZ",
            ).on_click(self.__cameraplane),
            QBtn(
                id="cameraplane_yz",
                ui_label="YZ",
            ).on_click(self.__cameraplane),
        )
        ui_class = kwargs.pop("ui_class", "")
        ui_class = f"q-ma-sm {ui_class}"
        super().__init__(
            Div("View", ui_class="q-mx-xs"),
            self.buttons,
            ui_class=ui_class,
            *args,
            **kwargs,
        )

    def __cameraplane(self, args: dict[str, Any]) -> None:
        plane = args["comp"].ui_label
        transformations = []
        if plane == "XZ":
            transformations = [
                {
                    "type": "rotateX",
                    "angle": -90,
                }
            ]
        if plane == "YZ":
            transformations = [
                {
                    "type": "rotateY",
                    "angle": 90,
                }
            ]
        self._webgui.set_camera(
            {"reset": True, "transformations": transformations}
        )


class Colormap(Col):
    """Colormap component"""

    def __init__(self, webgui: WebguiComponent, *args, **kwargs):

        self._webgui = webgui
        self._webgui.on("mounted", self._update_colormap_from_webgui)
        self.colormap_min = NumberInput(
            id="colormap_min",
            ui_label="Colormap Min",
            ui_model_value=0.0,
            ui_dense=True,
            ui_style="width: 150px;",
            ui_class="",
        ).on_update_model_value(self._update_colormap)
        self.colormap_max = NumberInput(
            id="colormap_max",
            ui_label="Colormap Max",
            ui_model_value=1.0,
            ui_dense=True,
            ui_style="width: 150px;",
            ui_class="",
        ).on_update_model_value(self._update_colormap)
        ui_class = kwargs.pop("ui_class", "")
        ui_class = f"q-ma-sm {ui_class}"
        super().__init__(
            self.colormap_min,
            self.colormap_max,
            ui_class=ui_class,
            *args,
            **kwargs,
        )
        self._webgui.on_draw(self._update_colormap_from_webgui)
        self._webgui.on_mounted(self._update_colormap)

    def _update_colormap(self) -> None:
        self._webgui.set_colormap(
            {
                "min": self.colormap_min.ui_model_value,
                "max": self.colormap_max.ui_model_value,
            }
        )

    def _update_colormap_from_webgui(self) -> None:
        if "funcmin" not in self._webgui._webgui_data:
            return
        colormap_min = self._webgui._webgui_data["funcmin"]
        colormap_max = self._webgui._webgui_data["funcmax"]

        cmin = self.colormap_min
        if cmin.ui_model_value != colormap_min:
            cmin.ui_model_value = round(colormap_min, 4)

        cmax = self.colormap_max
        if cmax.ui_model_value != colormap_max:
            cmax.ui_model_value = round(colormap_max, 4)

    def set_colormap(self, min: float | None = None, max: float | None = None):
        if min is not None:
            self.colormap_min.ui_model_value = min
        if max is not None:
            self.colormap_max.ui_model_value = max

        if min or max is not None:
            self._update_colormap()

        if min is None and max is None:
            default_colormap = self._webgui.webgui_data
            self.colormap_min.ui_model_value = round(
                default_colormap["funcmin"], 4
            )
            self.colormap_max.ui_model_value = round(
                default_colormap["funcmax"], 4
            )
            self._update_colormap()


class GeometryWebgui(Row):
    """Geometry webgui component"""

    def __init__(
        self,
        id: str = "",
        caption: str | None = None,
        namespace: bool = True,
        **kwargs,
    ):

        self._webgui = WebguiComponent(id="webgui", caption=caption, **kwargs)
        self._webgui.slot_buttons = [
            WebguiComponent.canvas_button(
                ui_icon="mdi-fullscreen",
                ui_tooltip="Fullscreen",
                on_click=lambda _: self._webgui.toggle_fullscreen(),
            ),
            WebguiComponent.canvas_button(
                ui_icon="mdi-eye-refresh-outline",
                ui_tooltip="Reset View",
                on_click=lambda _: self._webgui.set_camera(),
            ),
        ]
        super().__init__(
            self._webgui,
            Col(CameraView(self._webgui), Clipping(self._webgui)),
            id=id,
            namespace=namespace,
            **kwargs,
        )

    async def _get_markdown(self) -> str:
        return await self._webgui._get_markdown()

    def __getattr__(self, name):
        return getattr(self._webgui, name)


def _webgui_default_settings(webgui, colormap):
    webgui.set_camera()
    colormap.set_colormap()


class SolutionWebgui(Row):
    """Solution webgui component"""

    def __init__(
        self,
        id: str = "",
        caption: str | None = None,
        namespace: bool = True,
        show_clipping: bool = True,
        show_view: bool = True,
        **kwargs,
    ):

        self._webgui = WebguiComponent(id="webgui", caption=caption, **kwargs)
        self._colormap = Colormap(self._webgui, id="colormap")
        self._cameraview = CameraView(self._webgui)
        self._clipping = Clipping(self._webgui)
        self._cameraview.ui_hidden = not show_view
        self._clipping.ui_hidden = not show_clipping
        self._webgui.slot_buttons = [
            WebguiComponent.canvas_button(
                ui_icon="mdi-fullscreen",
                ui_tooltip="Fullscreen",
                on_click=lambda _: self._webgui.toggle_fullscreen(),
            ),
            WebguiComponent.canvas_button(
                ui_icon="mdi-eye-refresh-outline",
                ui_tooltip="Reset View",
                on_click=lambda _: self._webgui.set_camera(),
            ),
            WebguiComponent.canvas_button(
                ui_icon="mdi-grid",
                ui_tooltip="Show Mesh",
                on_click=lambda _: self._webgui.toggle_mesh(),
            ),
            WebguiComponent.canvas_button(
                ui_icon="mdi-format-color-fill",
                ui_tooltip="Reset Colormap",
                on_click=lambda _: self._colormap.set_colormap(),
            ),
            WebguiComponent.canvas_button(
                ui_icon="mdi-arrow-left-right",
                ui_tooltip="Reset To Default Settings",
                on_click=lambda _: _webgui_default_settings(
                    self._webgui, self._colormap
                ),
            ),
        ]

        super().__init__(
            self._webgui,
            Col(
                self._colormap,
                self._cameraview,
                self._clipping,
            ),
            id=id,
            namespace=namespace,
            **kwargs,
        )

    def clear(self):
        self._webgui.clear()

    def draw(self, *args, data: dict | None = None, **kwargs) -> None:
        if data is None:
            import ngsolve.webgui

            data = ngsolve.webgui.Draw(*args, **kwargs).GetData()
        self._webgui.draw(*args, data=data, **kwargs)

    def __getattr__(self, name):
        return getattr(self._webgui, name)

    async def _get_markdown(self) -> str:
        return "solution webgui:\n\n" + await self._webgui._get_markdown()

    async def generate_markdown(self) -> str:
        return await self._get_markdown()


class PlotlyComponent(Component):
    """Plotly plot component"""

    def __init__(
        self,
        id: str = "",
        filename: str = "",
        **kwargs,
    ):
        id = id or filename
        super().__init__(id=id, component="PlotlyComponent", **kwargs)
        self.filename = filename
        self.data = None
        self._props["style"] = "width: 100%; height: 480px"

    def draw(self, figure) -> None:
        if self.filename:
            self.data = None
            figure.write_image(f"{self.filename}.png")
            write_file(self.filename, figure.to_json())
        else:
            self.data = figure.to_dict()
            self.data["config"] = {"responsive": False, "displaylogo": False}
            from plotly.io.json import to_json_plotly

            self._update_frontend(
                method="draw",
                data={"id": self._id, "data": to_json_plotly(self.data)},
            )

    def _get_markdown(self) -> str:
        markdown = ""
        if self._id:
            markdown += f"![{self._id}]({self._id + '.png'})\n"
        return markdown


canvas_counter = 0


class WebgpuComponent(Component):
    def __init__(self, id=""):
        global canvas_counter
        super().__init__(
            "canvas", id=id or "webgpu_canvas" + str(canvas_counter)
        )
        self.ui_style = "width:800px; height:600px;"
        canvas_counter += 1
        # scene must be set in draw
        self.scene = None
        self.canvas = None
        self.on("mounted", self.connect_webgpu)
        self.on("unmount", self._on_unmount)
        self.on_load(self.__on_load)

    def __on_load(self):
        scene = self.storage.get("scene")
        if scene is not None:
            self.draw(scene)

    def _on_unmount(self):
        if self.scene is not None:
            self.scene.input_handler.unregister_callbacks()
        if self.canvas is not None:
            self.canvas.context.unconfigure()

    def connect_webgpu(self):
        from webgpu import canvas, utils

        if self.canvas:
            return self._reconfigure_canvas()

        html_canvas = self._js_component
        utils.init_device_sync()
        self.canvas = canvas.Canvas(utils.get_device(), html_canvas)

        scene = self.storage.get("scene")
        if self.scene is not None:
            self.draw(self.scene)
        elif scene is not None:
            self.draw(scene)

    def _reconfigure_canvas(self):
        """Reconfigure the canvas with the current HTML canvas element. This is necessary when the HTML canvas element changes, disappears (e.g. when switching a tab) and appears again."""
        html_canvas = self._js_component
        from webgpu.webgpu_api import TextureUsage, toJS
        if self.scene is not None:
            self.scene.input_handler.unregister_callbacks()
        self.canvas.canvas = html_canvas
        self.canvas.context = html_canvas.getContext("webgpu")
        self.canvas.context.configure(
            toJS(
                {
                    "device": self.canvas.device.handle,
                    "format": self.canvas.format,
                    "alphaMode": "premultiplied",
                    "sampleCount": self.canvas.multisample.count,
                    "usage": TextureUsage.RENDER_ATTACHMENT
                    | TextureUsage.COPY_DST,
                }
            )
        )
        if self.scene is not None:
            self.scene.init(self.canvas)
        self.canvas.width = 0  # force resize
        self.canvas.resize()

    def draw(self, scene, store=False):
        from webgpu import draw

        if store:
            self.storage.set("scene", scene, use_pickle=True)

        if self.canvas is not None:
            if self.scene is not None:
                self.scene.cleanup()
            self.scene = draw.Draw(scene, self.canvas, lilgui=False)
            self.scene.input_handler.on_mousedown(self.mousedown)
            self.scene.input_handler.on_mouseup(self.mouseup)
            self.scene.input_handler.on_mouseout(self.mouseout)
        else:
            if isinstance(scene, draw.BaseRenderer):
                scene = draw.Scene([scene])
            elif isinstance(scene, list):
                scene = draw.Scene(scene)
            self.scene = scene
        return self.scene

    def mousedown(self, event):
        pass

    def mouseup(self, event):
        pass

    def mouseout(self, event):
        pass

    def screenshot(self):
        from webgpu import utils

        return utils.read_texture(self.canvas.target_texture)

    def screenshot_as_data_url(self, format="image/png"):
        from webgpu import platform

        data = self.screenshot()
        canvas = platform.js.document.createElement("canvas")
        canvas.width = self.canvas.width
        canvas.height = self.canvas.height
        ctx = canvas.getContext("2d")
        u8 = platform.js.Uint8ClampedArray._new(data.tobytes())
        image_data = platform.js.ImageData._new(
            u8, self.canvas.width, self.canvas.height
        )
        ctx.putImageData(image_data, 0, 0)
        canvas.remove()
        return canvas.toDataURL(format)


def _encode_b64(data=None, file=None):
    """Encodes the given data or file as base64 for webgui."""
    if data is None:
        data = read_file(file)
    if isinstance(data, str):
        data = data.encode("utf-8")
    return base64.b64encode(data).decode("utf-8")


_webgui_js_code = None


def _get_webgui_js_code():
    global _webgui_js_code
    if _webgui_js_code is None:
        import urllib.request

        with urllib.request.urlopen(
            "https://cdn.jsdelivr.net/npm/webgui@0.2.37/dist/webgui.js"
        ) as f:
            _webgui_js_code = f.read().decode("utf-8")
    return _webgui_js_code


def generate_webgui_html(data, filename):
    """Generates an html file with the given webgui data."""
    template = _HTML_TEMPLATE.replace(
        "{{webgui_code}}",
        _encode_b64(_get_webgui_js_code()),
    )
    html = template.replace("{render}", f"var render_data = {data}\n")
    write_file(filename, html)


async def _make_html_screenshot(html_file, width=800, height=600):
    """Uses playwright to make a screenshot of the given html file."""
    # pylint: disable=import-outside-toplevel
    from playwright.async_api import async_playwright

    async with async_playwright() as play:
        browser = await play.chromium.launch()
        page = await browser.new_page(
            viewport={"width": width, "height": height}
        )
        await page.goto(f"file://{os.path.abspath(html_file)}")
        # wait a second for the page to load
        await page.wait_for_timeout(1000)
        await page.locator("canvas").wait_for(state="attached")
        await page.screenshot(path=html_file.replace(".html", ".png"))
        await browser.close()

    with open(html_file.replace(".html", ".png"), "rb") as f:
        return f.read()


async def _generate_webgui_screenshot(name, data, width, height):
    """Generates a screenshot for the given webgui data file."""
    html_file = name + ".html"
    data["on_init"] = "scene.gui.hide()"
    import numpy
    import orjson

    def default(obj):
        if isinstance(obj, numpy.float64):
            return float(obj)
        raise TypeError

    generate_webgui_html(
        orjson.dumps(data, default=default).decode(), html_file
    )
    return await _make_html_screenshot(html_file, width=width, height=height)


_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
    <head>
        <title>NGSolve WebGUI</title>
        <meta name='viewport' content='width=device-width, user-scalable=no' charset='utf-8'/>
        <style>
            body{
                margin:0;
                overflow:hidden;
            }
            canvas{
                cursor:grab;
                cursor:-webkit-grab;
                cursor:-moz-grab;
            }
            canvas:active{
                cursor:grabbing;
                cursor:-webkit-grabbing;
                cursor:-moz-grabbing;
            }
        </style>
    </head>
    <body>
          <script>
            const webgui_code = atob("{{webgui_code}}")
            const func = Function("module", "exports", webgui_code)
            let module = {exports: {}};
            func.call(module, module, module.exports);
            const webgui =  module.exports;
            {render}
            const scene = new webgui.Scene();
            scene.init(document.body, render_data, {preserveDrawingBuffer: true});
            scene.camera = scene.orthographic_camera;
          </script>
    </body>
</html>
"""
