"""The button of the platform for the top left corner of the app's header.

In the platform it opens the platform's menu (apps, account, groups, admin)
and the platform leaves out its own header for the app. Elsewhere (local
mode, static sites) it is the cerbsim logo, linking to cerbsim.com.
"""

from .basecomponent import Component
from .qcomponents import QIcon

__all__ = ["PlatformButton"]

_LOGO_PATHS = (
    "M 1095.92,843.281 1402.01,2649.03 3363.98,74.1602 Z M 126.914,131.289 "
    "1330.74,2560.39 1039.1,839.879 Z M 1069.86,793.559 3247.52,55.0898 H 119.203 Z "
    "M 1375.43,2775.39 0,0 H 3490.16 L 1375.43,2775.39",
    "m 1957.57,2536.14 c 39.46,232.74 71.19,419.93 82.25,485.16 12.73,-17.01 "
    "20.99,-27.97 20.99,-27.97 0,0 1695.81,-2250.799 2003.77,-2659.541 -278.64,94.543 "
    "-2345.48,795.441 -2345.48,795.441 0,0 142.21,839.03 238.47,1406.91",
)


def _attrs(comp: Component, **attrs) -> Component:
    for key, value in attrs.items():
        comp._props[key.replace("_", "-")] = value
    return comp


def _logo(height: str) -> Component:
    paths = [
        _attrs(
            Component("path"),
            d=d,
            fill="currentColor",
            transform="matrix(0.13333333,0,0,-0.13333333,0,402.84)",
        )
        for d in _LOGO_PATHS
    ]
    return _attrs(
        Component("svg", *paths, ui_class="ngapp-platform-logo",
                  ui_style=f"height: {height}; width: auto; display: block;"),
        viewBox="0 0 541.94 402.84",
        role="img",
        aria_label="cerbsim",
    )


class PlatformButton(Component):
    """The platform's menu button, or the cerbsim logo outside the platform;
    it takes the colour of the text around it"""

    def __init__(self, logo_height: str = "26px", **kwargs):
        menu = QIcon(ui_name="mdi-menu", ui_size="24px", ui_class="ngapp-platform-menu",
                     ui_style="display: none;")
        ui_class = " ".join(filter(None, ["ngapp-platform-button", kwargs.pop("ui_class", "")]))
        style = "display: inline-flex; align-items: center; color: inherit; text-decoration: none;"
        ui_style = " ".join(filter(None, [style, kwargs.pop("ui_style", "")]))
        super().__init__("a", _logo(logo_height), menu, ui_class=ui_class, ui_style=ui_style,
                         **kwargs)
        _attrs(self, href="https://cerbsim.com", target="_blank", rel="noopener")
