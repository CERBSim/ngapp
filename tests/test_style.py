from ngapp.style import Style, Theme, CssClass, StyleSheet


def test_style_snake_to_kebab():
    """Underscore keys must become hyphenated CSS properties."""
    assert "font-size: 14px;" in str(Style(font_size="14px"))
    assert "border-radius: 8px;" in str(Style(border_radius="8px"))


def test_style_merge_right_wins():
    """| must override left with right, and None must remove."""
    base = Style(color="red", padding="8px", margin="4px")
    merged = base | Style(color="blue", padding=None)
    result = str(merged)
    assert "color: blue;" in result
    assert "margin: 4px;" in result
    assert "padding" not in result
    assert "red" not in result


def test_cssclass_composition_with_strings():
    """+ must work: CssClass+CssClass, CssClass+str, str+CssClass."""
    a = CssClass("ngs0")
    b = CssClass("ngs1")
    assert str(a + b) == "ngs0 ngs1"
    assert str(a + "q-pa-md") == "ngs0 q-pa-md"
    assert str("q-pa-md" + a) == "q-pa-md ngs0"


def test_stylesheet_renders_valid_css():
    """add() → render() must produce .className { props } rules."""
    css = StyleSheet()
    c0 = css.add(Style(color="red", font_size="14px"))
    c1 = css.add(Style(display="none"))
    rendered = css._render()
    assert f".{c0} {{ color: red; font-size: 14px; }}" in rendered
    assert f".{c1} {{ display: none; }}" in rendered


def test_theme_spacing():
    """sp() must return the indexed spacing value as px string."""
    theme = Theme(spacing=(0, 4, 8, 12, 16))
    assert theme.sp(0) == "0px"
    assert theme.sp(2) == "8px"
    assert theme.sp(4) == "16px"
