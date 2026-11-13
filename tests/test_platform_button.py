from ngapp.components import PlatformButton


def test_platform_button_markup():
    """A link to cerbsim.com with the logo shown and the menu icon hidden: the
    platform's frame swaps them by its css and handles the click"""
    b = PlatformButton(ui_class="extra", ui_style="margin: 2px;")
    assert b._props["class"] == "ngapp-platform-button extra"
    assert b._props["href"] == "https://cerbsim.com" and b._props["target"] == "_blank"
    assert "color: inherit;" in b._props["style"] and "margin: 2px;" in b._props["style"]
    logo, menu = b.ui_children
    assert logo._props["class"] == "ngapp-platform-logo"
    assert all(p._props["fill"] == "currentColor" for p in logo.ui_children)
    assert menu._props["class"] == "ngapp-platform-menu"
    assert menu._props["style"] == "display: none;"
