import re
from typing import Any, Callable
from .basecomponent import Component, Event
from ..utils import print_exception


class QAjaxBar(Component):
    """
    Quasar Component: `QAjaxBar <https://v2.quasar.dev/vue-components/ajax-bar>`__

    :param ui_position: Position within window of where QAjaxBar should be displayed
    :param ui_size:
    :param ui_color:
    :param ui_reverse: Reverse direction of progress
    :param ui_skip_hijack: Skip Ajax hijacking (not a reactive prop)
    :param ui_hijack_filter: Filter which URL should trigger start() + stop()
    """

    def __init__(
        self,
        *children,
        ui_position: str | None = None,
        ui_size: Any | None = None,
        ui_color: Any | None = None,
        ui_reverse: bool | None = None,
        ui_skip_hijack: bool | None = None,
        ui_hijack_filter: Callable | None = None,
        **kwargs,
    ):
        super().__init__("QAjaxBar", *children, **kwargs)
        if ui_position is not None:
            self._props["position"] = ui_position
        if ui_size is not None:
            self._props["size"] = ui_size
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_reverse is not None:
            self._props["reverse"] = ui_reverse
        if ui_skip_hijack is not None:
            self._props["skip-hijack"] = ui_skip_hijack
        if ui_hijack_filter is not None:
            self._props["hijack-filter"] = ui_hijack_filter

    @property
    def ui_position(self):
        """Position within window of where QAjaxBar should be displayed"""
        return self._props.get("position")

    @ui_position.setter
    def ui_position(self, value):
        self._set_prop("position", value)

    @property
    def ui_size(self):
        return self._props.get("size")

    @ui_size.setter
    def ui_size(self, value):
        self._set_prop("size", value)

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_reverse(self):
        """Reverse direction of progress"""
        return self._props.get("reverse")

    @ui_reverse.setter
    def ui_reverse(self, value):
        self._set_prop("reverse", value)

    @property
    def ui_skip_hijack(self):
        """Skip Ajax hijacking (not a reactive prop)"""
        return self._props.get("skip-hijack")

    @ui_skip_hijack.setter
    def ui_skip_hijack(self, value):
        self._set_prop("skip-hijack", value)

    @property
    def ui_hijack_filter(self):
        """Filter which URL should trigger start() + stop()"""
        return self._props.get("hijack-filter")

    @ui_hijack_filter.setter
    def ui_hijack_filter(self, value):
        self._set_prop("hijack-filter", value)

    def on_start(self, handler: Callable, arg: object = None):
        """
        Emitted when bar is triggered to appear

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("start", handler, arg)

    def on_stop(self, handler: Callable, arg: object = None):
        """
        Emitted when bar has finished its job

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("stop", handler, arg)

    def ui_increment(self, ui_amount=None):
        """Manually trigger a bar progress increment"""
        kwargs = {}
        if ui_amount is not None:
            kwargs["amount"] = ui_amount
        self._js_call_method("increment", [kwargs])

    def ui_start(self, ui_speed=None):
        """Notify bar you are waiting for a new process to finish"""
        kwargs = {}
        if ui_speed is not None:
            kwargs["speed"] = ui_speed
        self._js_call_method("start", [kwargs])

    def ui_stop(self):
        """Notify bar that one process you were waiting has finished"""
        self._js_call_method("stop")

    def _get_js_methods(self):
        return ["increment", "start", "stop"]


class QAvatar(Component):
    """
    Quasar Component: `QAvatar <https://v2.quasar.dev/vue-components/avatar>`__

    :param ui_font_size: The size in CSS units, including unit name, of the content (icon, text)
    :param ui_color:
    :param ui_text_color:
    :param ui_icon:
    :param ui_square:
    :param ui_rounded:
    :param ui_size: Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)
    """

    def __init__(
        self,
        *children,
        ui_font_size: str | None = None,
        ui_color: Any | None = None,
        ui_text_color: Any | None = None,
        ui_icon: Any | None = None,
        ui_square: Any | None = None,
        ui_rounded: Any | None = None,
        ui_size: str | None = None,
        **kwargs,
    ):
        super().__init__("QAvatar", *children, **kwargs)
        if ui_font_size is not None:
            self._props["font-size"] = ui_font_size
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_text_color is not None:
            self._props["text-color"] = ui_text_color
        if ui_icon is not None:
            self._props["icon"] = ui_icon
        if ui_square is not None:
            self._props["square"] = ui_square
        if ui_rounded is not None:
            self._props["rounded"] = ui_rounded
        if ui_size is not None:
            self._props["size"] = ui_size

    @property
    def ui_font_size(self):
        """The size in CSS units, including unit name, of the content (icon, text)"""
        return self._props.get("font-size")

    @ui_font_size.setter
    def ui_font_size(self, value):
        self._set_prop("font-size", value)

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_text_color(self):
        return self._props.get("text-color")

    @ui_text_color.setter
    def ui_text_color(self, value):
        self._set_prop("text-color", value)

    @property
    def ui_icon(self):
        return self._props.get("icon")

    @ui_icon.setter
    def ui_icon(self, value):
        self._set_prop("icon", value)

    @property
    def ui_square(self):
        return self._props.get("square")

    @ui_square.setter
    def ui_square(self, value):
        self._set_prop("square", value)

    @property
    def ui_rounded(self):
        return self._props.get("rounded")

    @ui_rounded.setter
    def ui_rounded(self, value):
        self._set_prop("rounded", value)

    @property
    def ui_size(self):
        """Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)"""
        return self._props.get("size")

    @ui_size.setter
    def ui_size(self, value):
        self._set_prop("size", value)

    def _get_js_methods(self):
        return []


class QBadge(Component):
    """
    Quasar Component: `QBadge <https://v2.quasar.dev/vue-components/badge>`__

    :param ui_color:
    :param ui_text_color:
    :param ui_floating: Tell QBadge if it should float to the top right side of the relative positioned parent element or not
    :param ui_transparent: Applies a 0.8 opacity; Useful especially for floating QBadge
    :param ui_multi_line: Content can wrap to multiple lines
    :param ui_label: Badge's content as string; overrides default slot if specified
    :param ui_align: Sets vertical-align CSS prop
    :param ui_outline: Use 'outline' design (colored text and borders only)
    :param ui_rounded: Makes a rounded shaped badge
    """

    def __init__(
        self,
        *children,
        ui_color: Any | None = None,
        ui_text_color: Any | None = None,
        ui_floating: bool | None = None,
        ui_transparent: bool | None = None,
        ui_multi_line: bool | None = None,
        ui_label: str | float | None = None,
        ui_align: str | None = None,
        ui_outline: bool | None = None,
        ui_rounded: bool | None = None,
        **kwargs,
    ):
        super().__init__("QBadge", *children, **kwargs)
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_text_color is not None:
            self._props["text-color"] = ui_text_color
        if ui_floating is not None:
            self._props["floating"] = ui_floating
        if ui_transparent is not None:
            self._props["transparent"] = ui_transparent
        if ui_multi_line is not None:
            self._props["multi-line"] = ui_multi_line
        if ui_label is not None:
            self._props["label"] = ui_label
        if ui_align is not None:
            self._props["align"] = ui_align
        if ui_outline is not None:
            self._props["outline"] = ui_outline
        if ui_rounded is not None:
            self._props["rounded"] = ui_rounded

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_text_color(self):
        return self._props.get("text-color")

    @ui_text_color.setter
    def ui_text_color(self, value):
        self._set_prop("text-color", value)

    @property
    def ui_floating(self):
        """Tell QBadge if it should float to the top right side of the relative positioned parent element or not"""
        return self._props.get("floating")

    @ui_floating.setter
    def ui_floating(self, value):
        self._set_prop("floating", value)

    @property
    def ui_transparent(self):
        """Applies a 0.8 opacity; Useful especially for floating QBadge"""
        return self._props.get("transparent")

    @ui_transparent.setter
    def ui_transparent(self, value):
        self._set_prop("transparent", value)

    @property
    def ui_multi_line(self):
        """Content can wrap to multiple lines"""
        return self._props.get("multi-line")

    @ui_multi_line.setter
    def ui_multi_line(self, value):
        self._set_prop("multi-line", value)

    @property
    def ui_label(self):
        """Badge's content as string; overrides default slot if specified"""
        return self._props.get("label")

    @ui_label.setter
    def ui_label(self, value):
        self._set_prop("label", value)

    @property
    def ui_align(self):
        """Sets vertical-align CSS prop"""
        return self._props.get("align")

    @ui_align.setter
    def ui_align(self, value):
        self._set_prop("align", value)

    @property
    def ui_outline(self):
        """Use 'outline' design (colored text and borders only)"""
        return self._props.get("outline")

    @ui_outline.setter
    def ui_outline(self, value):
        self._set_prop("outline", value)

    @property
    def ui_rounded(self):
        """Makes a rounded shaped badge"""
        return self._props.get("rounded")

    @ui_rounded.setter
    def ui_rounded(self, value):
        self._set_prop("rounded", value)

    def _get_js_methods(self):
        return []


class QBanner(Component):
    """
    Quasar Component: `QBanner <https://v2.quasar.dev/vue-components/banner>`__

    :param ui_inline_actions: Display actions on same row as content
    :param ui_dense:
    :param ui_rounded:
    :param ui_dark:
    """

    def __init__(
        self,
        *children,
        ui_inline_actions: bool | None = None,
        ui_dense: Any | None = None,
        ui_rounded: Any | None = None,
        ui_dark: Any | None = None,
        **kwargs,
    ):
        super().__init__("QBanner", *children, **kwargs)
        if ui_inline_actions is not None:
            self._props["inline-actions"] = ui_inline_actions
        if ui_dense is not None:
            self._props["dense"] = ui_dense
        if ui_rounded is not None:
            self._props["rounded"] = ui_rounded
        if ui_dark is not None:
            self._props["dark"] = ui_dark

    @property
    def ui_inline_actions(self):
        """Display actions on same row as content"""
        return self._props.get("inline-actions")

    @ui_inline_actions.setter
    def ui_inline_actions(self, value):
        self._set_prop("inline-actions", value)

    @property
    def ui_dense(self):
        return self._props.get("dense")

    @ui_dense.setter
    def ui_dense(self, value):
        self._set_prop("dense", value)

    @property
    def ui_rounded(self):
        return self._props.get("rounded")

    @ui_rounded.setter
    def ui_rounded(self, value):
        self._set_prop("rounded", value)

    @property
    def ui_dark(self):
        return self._props.get("dark")

    @ui_dark.setter
    def ui_dark(self, value):
        self._set_prop("dark", value)

    @property
    def ui_slot_action(self):
        """Slot for Banner action (suggestions: QBtn)"""
        return self.ui_slots.get("action", [])

    @ui_slot_action.setter
    def ui_slot_action(self, value):
        self._set_slot("action", value)

    @property
    def ui_slot_avatar(self):
        """Slot for displaying an avatar (suggestions: QIcon, QAvatar)"""
        return self.ui_slots.get("avatar", [])

    @ui_slot_avatar.setter
    def ui_slot_avatar(self, value):
        self._set_slot("avatar", value)

    def _get_js_methods(self):
        return []


class QBar(Component):
    """
    Quasar Component: `QBar <https://v2.quasar.dev/vue-components/bar>`__

    :param ui_dense:
    :param ui_dark: The component background color lights up the parent's background (as opposed to default behavior which is to darken it); Works unless you specify a CSS background color for it
    """

    def __init__(
        self,
        *children,
        ui_dense: Any | None = None,
        ui_dark: Any | None = None,
        **kwargs,
    ):
        super().__init__("QBar", *children, **kwargs)
        if ui_dense is not None:
            self._props["dense"] = ui_dense
        if ui_dark is not None:
            self._props["dark"] = ui_dark

    @property
    def ui_dense(self):
        return self._props.get("dense")

    @ui_dense.setter
    def ui_dense(self, value):
        self._set_prop("dense", value)

    @property
    def ui_dark(self):
        """The component background color lights up the parent's background (as opposed to default behavior which is to darken it); Works unless you specify a CSS background color for it"""
        return self._props.get("dark")

    @ui_dark.setter
    def ui_dark(self, value):
        self._set_prop("dark", value)

    def _get_js_methods(self):
        return []


class QBreadcrumbsEl(Component):
    """
    Quasar Component: `QBreadcrumbsEl <https://v2.quasar.dev/vue-components/breadcrumbs>`__

    :param ui_label: The label text for the breadcrumb
    :param ui_icon:
    :param ui_tag:
    :param ui_to: Equivalent to Vue Router <router-link> 'to' property; Superseded by 'href' prop if used
    :param ui_exact: Equivalent to Vue Router <router-link> 'exact' property; Superseded by 'href' prop if used
    :param ui_replace: Equivalent to Vue Router <router-link> 'replace' property; Superseded by 'href' prop if used
    :param ui_active_class: Equivalent to Vue Router <router-link> 'active-class' property; Superseded by 'href' prop if used
    :param ui_exact_active_class: Equivalent to Vue Router <router-link> 'active-class' property; Superseded by 'href' prop if used
    :param ui_href: Native <a> link href attribute; Has priority over the 'to'/'exact'/'replace'/'active-class'/'exact-active-class' props
    :param ui_target: Native <a> link target attribute; Use it only along with 'href' prop; Has priority over the 'to'/'exact'/'replace'/'active-class'/'exact-active-class' props
    :param ui_disable:
    """

    def __init__(
        self,
        *children,
        ui_label: str | None = None,
        ui_icon: Any | None = None,
        ui_tag: Any | None = None,
        ui_to: str | dict | None = None,
        ui_exact: bool | None = None,
        ui_replace: bool | None = None,
        ui_active_class: str | None = None,
        ui_exact_active_class: str | None = None,
        ui_href: str | None = None,
        ui_target: str | None = None,
        ui_disable: Any | None = None,
        **kwargs,
    ):
        super().__init__("QBreadcrumbsEl", *children, **kwargs)
        if ui_label is not None:
            self._props["label"] = ui_label
        if ui_icon is not None:
            self._props["icon"] = ui_icon
        if ui_tag is not None:
            self._props["tag"] = ui_tag
        if ui_to is not None:
            self._props["to"] = ui_to
        if ui_exact is not None:
            self._props["exact"] = ui_exact
        if ui_replace is not None:
            self._props["replace"] = ui_replace
        if ui_active_class is not None:
            self._props["active-class"] = ui_active_class
        if ui_exact_active_class is not None:
            self._props["exact-active-class"] = ui_exact_active_class
        if ui_href is not None:
            self._props["href"] = ui_href
        if ui_target is not None:
            self._props["target"] = ui_target
        if ui_disable is not None:
            self._props["disable"] = ui_disable

    @property
    def ui_label(self):
        """The label text for the breadcrumb"""
        return self._props.get("label")

    @ui_label.setter
    def ui_label(self, value):
        self._set_prop("label", value)

    @property
    def ui_icon(self):
        return self._props.get("icon")

    @ui_icon.setter
    def ui_icon(self, value):
        self._set_prop("icon", value)

    @property
    def ui_tag(self):
        return self._props.get("tag")

    @ui_tag.setter
    def ui_tag(self, value):
        self._set_prop("tag", value)

    @property
    def ui_to(self):
        """Equivalent to Vue Router <router-link> 'to' property; Superseded by 'href' prop if used"""
        return self._props.get("to")

    @ui_to.setter
    def ui_to(self, value):
        self._set_prop("to", value)

    @property
    def ui_exact(self):
        """Equivalent to Vue Router <router-link> 'exact' property; Superseded by 'href' prop if used"""
        return self._props.get("exact")

    @ui_exact.setter
    def ui_exact(self, value):
        self._set_prop("exact", value)

    @property
    def ui_replace(self):
        """Equivalent to Vue Router <router-link> 'replace' property; Superseded by 'href' prop if used"""
        return self._props.get("replace")

    @ui_replace.setter
    def ui_replace(self, value):
        self._set_prop("replace", value)

    @property
    def ui_active_class(self):
        """Equivalent to Vue Router <router-link> 'active-class' property; Superseded by 'href' prop if used"""
        return self._props.get("active-class")

    @ui_active_class.setter
    def ui_active_class(self, value):
        self._set_prop("active-class", value)

    @property
    def ui_exact_active_class(self):
        """Equivalent to Vue Router <router-link> 'active-class' property; Superseded by 'href' prop if used"""
        return self._props.get("exact-active-class")

    @ui_exact_active_class.setter
    def ui_exact_active_class(self, value):
        self._set_prop("exact-active-class", value)

    @property
    def ui_href(self):
        """Native <a> link href attribute; Has priority over the 'to'/'exact'/'replace'/'active-class'/'exact-active-class' props"""
        return self._props.get("href")

    @ui_href.setter
    def ui_href(self, value):
        self._set_prop("href", value)

    @property
    def ui_target(self):
        """Native <a> link target attribute; Use it only along with 'href' prop; Has priority over the 'to'/'exact'/'replace'/'active-class'/'exact-active-class' props"""
        return self._props.get("target")

    @ui_target.setter
    def ui_target(self, value):
        self._set_prop("target", value)

    @property
    def ui_disable(self):
        return self._props.get("disable")

    @ui_disable.setter
    def ui_disable(self, value):
        self._set_prop("disable", value)

    def on_click(self, handler: Callable, arg: object = None):
        """
        Emitted when the component is clicked

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("click.stop", handler, arg)

    def _get_js_methods(self):
        return []


class QBreadcrumbs(Component):
    """
    Quasar Component: `QBreadcrumbs <https://v2.quasar.dev/vue-components/breadcrumbs>`__

    :param ui_separator: The string used to separate the breadcrumbs
    :param ui_active_color: The color of the active breadcrumb, which can be any color from the Quasar Color Palette
    :param ui_gutter: The gutter value allows you control over the space between the breadcrumb elements.
    :param ui_separator_color: The color used to color the separator, which can be any color from the Quasar Color Palette
    :param ui_align: Specify how to align the breadcrumbs horizontally
    """

    def __init__(
        self,
        *children,
        ui_separator: str | None = None,
        ui_active_color: Any | None = None,
        ui_gutter: str | None = None,
        ui_separator_color: Any | None = None,
        ui_align: str | None = None,
        **kwargs,
    ):
        super().__init__("QBreadcrumbs", *children, **kwargs)
        if ui_separator is not None:
            self._props["separator"] = ui_separator
        if ui_active_color is not None:
            self._props["active-color"] = ui_active_color
        if ui_gutter is not None:
            self._props["gutter"] = ui_gutter
        if ui_separator_color is not None:
            self._props["separator-color"] = ui_separator_color
        if ui_align is not None:
            self._props["align"] = ui_align

    @property
    def ui_separator(self):
        """The string used to separate the breadcrumbs"""
        return self._props.get("separator")

    @ui_separator.setter
    def ui_separator(self, value):
        self._set_prop("separator", value)

    @property
    def ui_active_color(self):
        """The color of the active breadcrumb, which can be any color from the Quasar Color Palette"""
        return self._props.get("active-color")

    @ui_active_color.setter
    def ui_active_color(self, value):
        self._set_prop("active-color", value)

    @property
    def ui_gutter(self):
        """The gutter value allows you control over the space between the breadcrumb elements."""
        return self._props.get("gutter")

    @ui_gutter.setter
    def ui_gutter(self, value):
        self._set_prop("gutter", value)

    @property
    def ui_separator_color(self):
        """The color used to color the separator, which can be any color from the Quasar Color Palette"""
        return self._props.get("separator-color")

    @ui_separator_color.setter
    def ui_separator_color(self, value):
        self._set_prop("separator-color", value)

    @property
    def ui_align(self):
        """Specify how to align the breadcrumbs horizontally"""
        return self._props.get("align")

    @ui_align.setter
    def ui_align(self, value):
        self._set_prop("align", value)

    @property
    def ui_slot_separator(self):
        """HTML or component you can slot in to separate the breadcrumbs"""
        return self.ui_slots.get("separator", [])

    @ui_slot_separator.setter
    def ui_slot_separator(self, value):
        self._set_slot("separator", value)

    def _get_js_methods(self):
        return []


class QBtn(Component):
    """
    Quasar Component: `QBtn <https://v2.quasar.dev/vue-components/button>`__

    :param ui_round: Makes a circle shaped button
    :param ui_percentage: Percentage (0.0 < x < 100.0); To be used along 'loading' prop; Display a progress bar on the background
    :param ui_dark_percentage: Progress bar on the background should have dark color; To be used along with 'percentage' and 'loading' props
    :param ui_type: 1) Define the button native type attribute (submit, reset, button) or 2) render component with <a> tag so you can access events even if disable or 3) Use 'href' prop and specify 'type' as a media tag
    :param ui_to: Equivalent to Vue Router <router-link> 'to' property; Superseded by 'href' prop if used
    :param ui_replace: Equivalent to Vue Router <router-link> 'replace' property; Superseded by 'href' prop if used
    :param ui_href: Native <a> link href attribute; Has priority over the 'to' and 'replace' props
    :param ui_target: Native <a> link target attribute; Use it only with 'to' or 'href' props
    :param ui_label: The text that will be shown on the button
    :param ui_icon:
    :param ui_icon_right:
    :param ui_outline: Use 'outline' design
    :param ui_flat: Use 'flat' design
    :param ui_unelevated: Remove shadow
    :param ui_rounded: Applies a more prominent border-radius for a squared shape button
    :param ui_push: Use 'push' design
    :param ui_square:
    :param ui_glossy: Applies a glossy effect
    :param ui_fab: Makes button size and shape to fit a Floating Action Button
    :param ui_fab_mini: Makes button size and shape to fit a small Floating Action Button
    :param ui_padding: Apply custom padding (vertical [horizontal]); Size in CSS units, including unit name or standard size name (none|xs|sm|md|lg|xl); Also removes the min width and height when set
    :param ui_color:
    :param ui_text_color:
    :param ui_no_caps: Avoid turning label text into caps (which happens by default)
    :param ui_no_wrap: Avoid label text wrapping
    :param ui_dense:
    :param ui_ripple:
    :param ui_tabindex:
    :param ui_align: Label or content alignment
    :param ui_stack: Stack icon and label vertically instead of on same line (like it is by default)
    :param ui_stretch: When used on flexbox parent, button will stretch to parent's height
    :param ui_loading: Put button into loading state (displays a QSpinner -- can be overridden by using a 'loading' slot)
    :param ui_disable:
    :param ui_size: Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)
    """

    def __init__(
        self,
        *children,
        ui_round: bool | None = None,
        ui_percentage: float | None = None,
        ui_dark_percentage: bool | None = None,
        ui_type: str | None = None,
        ui_to: str | dict | None = None,
        ui_replace: bool | None = None,
        ui_href: str | None = None,
        ui_target: str | None = None,
        ui_label: str | float | None = None,
        ui_icon: Any | None = None,
        ui_icon_right: Any | None = None,
        ui_outline: bool | None = None,
        ui_flat: bool | None = None,
        ui_unelevated: bool | None = None,
        ui_rounded: bool | None = None,
        ui_push: bool | None = None,
        ui_square: Any | None = None,
        ui_glossy: bool | None = None,
        ui_fab: bool | None = None,
        ui_fab_mini: bool | None = None,
        ui_padding: str | None = None,
        ui_color: Any | None = None,
        ui_text_color: Any | None = None,
        ui_no_caps: bool | None = None,
        ui_no_wrap: bool | None = None,
        ui_dense: Any | None = None,
        ui_ripple: Any | None = None,
        ui_tabindex: Any | None = None,
        ui_align: str | None = None,
        ui_stack: bool | None = None,
        ui_stretch: bool | None = None,
        ui_loading: bool | None = None,
        ui_disable: Any | None = None,
        ui_size: str | None = None,
        **kwargs,
    ):
        super().__init__("QBtn", *children, **kwargs)
        if ui_round is not None:
            self._props["round"] = ui_round
        if ui_percentage is not None:
            self._props["percentage"] = ui_percentage
        if ui_dark_percentage is not None:
            self._props["dark-percentage"] = ui_dark_percentage
        if ui_type is not None:
            self._props["type"] = ui_type
        if ui_to is not None:
            self._props["to"] = ui_to
        if ui_replace is not None:
            self._props["replace"] = ui_replace
        if ui_href is not None:
            self._props["href"] = ui_href
        if ui_target is not None:
            self._props["target"] = ui_target
        if ui_label is not None:
            self._props["label"] = ui_label
        if ui_icon is not None:
            self._props["icon"] = ui_icon
        if ui_icon_right is not None:
            self._props["icon-right"] = ui_icon_right
        if ui_outline is not None:
            self._props["outline"] = ui_outline
        if ui_flat is not None:
            self._props["flat"] = ui_flat
        if ui_unelevated is not None:
            self._props["unelevated"] = ui_unelevated
        if ui_rounded is not None:
            self._props["rounded"] = ui_rounded
        if ui_push is not None:
            self._props["push"] = ui_push
        if ui_square is not None:
            self._props["square"] = ui_square
        if ui_glossy is not None:
            self._props["glossy"] = ui_glossy
        if ui_fab is not None:
            self._props["fab"] = ui_fab
        if ui_fab_mini is not None:
            self._props["fab-mini"] = ui_fab_mini
        if ui_padding is not None:
            self._props["padding"] = ui_padding
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_text_color is not None:
            self._props["text-color"] = ui_text_color
        if ui_no_caps is not None:
            self._props["no-caps"] = ui_no_caps
        if ui_no_wrap is not None:
            self._props["no-wrap"] = ui_no_wrap
        if ui_dense is not None:
            self._props["dense"] = ui_dense
        if ui_ripple is not None:
            self._props["ripple"] = ui_ripple
        if ui_tabindex is not None:
            self._props["tabindex"] = ui_tabindex
        if ui_align is not None:
            self._props["align"] = ui_align
        if ui_stack is not None:
            self._props["stack"] = ui_stack
        if ui_stretch is not None:
            self._props["stretch"] = ui_stretch
        if ui_loading is not None:
            self._props["loading"] = ui_loading
        if ui_disable is not None:
            self._props["disable"] = ui_disable
        if ui_size is not None:
            self._props["size"] = ui_size

    @property
    def ui_round(self):
        """Makes a circle shaped button"""
        return self._props.get("round")

    @ui_round.setter
    def ui_round(self, value):
        self._set_prop("round", value)

    @property
    def ui_percentage(self):
        """Percentage (0.0 < x < 100.0); To be used along 'loading' prop; Display a progress bar on the background"""
        return self._props.get("percentage")

    @ui_percentage.setter
    def ui_percentage(self, value):
        self._set_prop("percentage", value)

    @property
    def ui_dark_percentage(self):
        """Progress bar on the background should have dark color; To be used along with 'percentage' and 'loading' props"""
        return self._props.get("dark-percentage")

    @ui_dark_percentage.setter
    def ui_dark_percentage(self, value):
        self._set_prop("dark-percentage", value)

    @property
    def ui_type(self):
        """1) Define the button native type attribute (submit, reset, button) or 2) render component with <a> tag so you can access events even if disable or 3) Use 'href' prop and specify 'type' as a media tag"""
        return self._props.get("type")

    @ui_type.setter
    def ui_type(self, value):
        self._set_prop("type", value)

    @property
    def ui_to(self):
        """Equivalent to Vue Router <router-link> 'to' property; Superseded by 'href' prop if used"""
        return self._props.get("to")

    @ui_to.setter
    def ui_to(self, value):
        self._set_prop("to", value)

    @property
    def ui_replace(self):
        """Equivalent to Vue Router <router-link> 'replace' property; Superseded by 'href' prop if used"""
        return self._props.get("replace")

    @ui_replace.setter
    def ui_replace(self, value):
        self._set_prop("replace", value)

    @property
    def ui_href(self):
        """Native <a> link href attribute; Has priority over the 'to' and 'replace' props"""
        return self._props.get("href")

    @ui_href.setter
    def ui_href(self, value):
        self._set_prop("href", value)

    @property
    def ui_target(self):
        """Native <a> link target attribute; Use it only with 'to' or 'href' props"""
        return self._props.get("target")

    @ui_target.setter
    def ui_target(self, value):
        self._set_prop("target", value)

    @property
    def ui_label(self):
        """The text that will be shown on the button"""
        return self._props.get("label")

    @ui_label.setter
    def ui_label(self, value):
        self._set_prop("label", value)

    @property
    def ui_icon(self):
        return self._props.get("icon")

    @ui_icon.setter
    def ui_icon(self, value):
        self._set_prop("icon", value)

    @property
    def ui_icon_right(self):
        return self._props.get("icon-right")

    @ui_icon_right.setter
    def ui_icon_right(self, value):
        self._set_prop("icon-right", value)

    @property
    def ui_outline(self):
        """Use 'outline' design"""
        return self._props.get("outline")

    @ui_outline.setter
    def ui_outline(self, value):
        self._set_prop("outline", value)

    @property
    def ui_flat(self):
        """Use 'flat' design"""
        return self._props.get("flat")

    @ui_flat.setter
    def ui_flat(self, value):
        self._set_prop("flat", value)

    @property
    def ui_unelevated(self):
        """Remove shadow"""
        return self._props.get("unelevated")

    @ui_unelevated.setter
    def ui_unelevated(self, value):
        self._set_prop("unelevated", value)

    @property
    def ui_rounded(self):
        """Applies a more prominent border-radius for a squared shape button"""
        return self._props.get("rounded")

    @ui_rounded.setter
    def ui_rounded(self, value):
        self._set_prop("rounded", value)

    @property
    def ui_push(self):
        """Use 'push' design"""
        return self._props.get("push")

    @ui_push.setter
    def ui_push(self, value):
        self._set_prop("push", value)

    @property
    def ui_square(self):
        return self._props.get("square")

    @ui_square.setter
    def ui_square(self, value):
        self._set_prop("square", value)

    @property
    def ui_glossy(self):
        """Applies a glossy effect"""
        return self._props.get("glossy")

    @ui_glossy.setter
    def ui_glossy(self, value):
        self._set_prop("glossy", value)

    @property
    def ui_fab(self):
        """Makes button size and shape to fit a Floating Action Button"""
        return self._props.get("fab")

    @ui_fab.setter
    def ui_fab(self, value):
        self._set_prop("fab", value)

    @property
    def ui_fab_mini(self):
        """Makes button size and shape to fit a small Floating Action Button"""
        return self._props.get("fab-mini")

    @ui_fab_mini.setter
    def ui_fab_mini(self, value):
        self._set_prop("fab-mini", value)

    @property
    def ui_padding(self):
        """Apply custom padding (vertical [horizontal]); Size in CSS units, including unit name or standard size name (none|xs|sm|md|lg|xl); Also removes the min width and height when set"""
        return self._props.get("padding")

    @ui_padding.setter
    def ui_padding(self, value):
        self._set_prop("padding", value)

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_text_color(self):
        return self._props.get("text-color")

    @ui_text_color.setter
    def ui_text_color(self, value):
        self._set_prop("text-color", value)

    @property
    def ui_no_caps(self):
        """Avoid turning label text into caps (which happens by default)"""
        return self._props.get("no-caps")

    @ui_no_caps.setter
    def ui_no_caps(self, value):
        self._set_prop("no-caps", value)

    @property
    def ui_no_wrap(self):
        """Avoid label text wrapping"""
        return self._props.get("no-wrap")

    @ui_no_wrap.setter
    def ui_no_wrap(self, value):
        self._set_prop("no-wrap", value)

    @property
    def ui_dense(self):
        return self._props.get("dense")

    @ui_dense.setter
    def ui_dense(self, value):
        self._set_prop("dense", value)

    @property
    def ui_ripple(self):
        return self._props.get("ripple")

    @ui_ripple.setter
    def ui_ripple(self, value):
        self._set_prop("ripple", value)

    @property
    def ui_tabindex(self):
        return self._props.get("tabindex")

    @ui_tabindex.setter
    def ui_tabindex(self, value):
        self._set_prop("tabindex", value)

    @property
    def ui_align(self):
        """Label or content alignment"""
        return self._props.get("align")

    @ui_align.setter
    def ui_align(self, value):
        self._set_prop("align", value)

    @property
    def ui_stack(self):
        """Stack icon and label vertically instead of on same line (like it is by default)"""
        return self._props.get("stack")

    @ui_stack.setter
    def ui_stack(self, value):
        self._set_prop("stack", value)

    @property
    def ui_stretch(self):
        """When used on flexbox parent, button will stretch to parent's height"""
        return self._props.get("stretch")

    @ui_stretch.setter
    def ui_stretch(self, value):
        self._set_prop("stretch", value)

    @property
    def ui_loading(self):
        """Put button into loading state (displays a QSpinner -- can be overridden by using a 'loading' slot)"""
        return self._props.get("loading")

    @ui_loading.setter
    def ui_loading(self, value):
        self._set_prop("loading", value)

    @property
    def ui_disable(self):
        return self._props.get("disable")

    @ui_disable.setter
    def ui_disable(self, value):
        self._set_prop("disable", value)

    @property
    def ui_size(self):
        """Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)"""
        return self._props.get("size")

    @ui_size.setter
    def ui_size(self, value):
        self._set_prop("size", value)

    @property
    def ui_slot_loading(self):
        """Override the default QSpinner when in 'loading' state"""
        return self.ui_slots.get("loading", [])

    @ui_slot_loading.setter
    def ui_slot_loading(self, value):
        self._set_slot("loading", value)

    def on_click(self, handler: Callable, arg: object = None):
        """
        Emitted when the component is clicked

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("click.stop", handler, arg)

    def on_keydown(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("keydown", handler, arg)

    def on_keyup(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("keyup", handler, arg)

    def on_mousedown(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("mousedown", handler, arg)

    def on_touchstart(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("touchstart", handler, arg)

    def ui_click(self, ui_evt=None):
        """Emulate click on QBtn"""
        kwargs = {}
        if ui_evt is not None:
            kwargs["evt"] = ui_evt
        self._js_call_method("click", [kwargs])

    def _get_js_methods(self):
        return ["click"]


class QBtnDropdown(Component):
    """
    Quasar Component: `QBtnDropdown <https://v2.quasar.dev/vue-components/button-dropdown>`__

    :param ui_model_value: Model of the component defining shown/hidden state; Either use this property (along with a listener for 'update:model-value' event) OR use v-model directive
    :param ui_split: Split dropdown icon into its own button
    :param ui_dropdown_icon:
    :param ui_disable_main_btn: Disable main button (useful along with 'split' prop)
    :param ui_disable_dropdown: Disables dropdown (dropdown button if using along 'split' prop)
    :param ui_no_icon_animation: Disables the rotation of the dropdown icon when state is toggled
    :param ui_content_style: Style definitions to be attributed to the menu
    :param ui_content_class: Class definitions to be attributed to the menu
    :param ui_cover: Allows the menu to cover the button. When used, the 'menu-self' and 'menu-fit' props are no longer effective
    :param ui_persistent: Allows the menu to not be dismissed by a click/tap outside of the menu or by hitting the ESC key; Also, an app route change won't dismiss it
    :param ui_no_route_dismiss: Changing route app won't dismiss the popup; No need to set it if 'persistent' prop is also set
    :param ui_auto_close: Allows any click/tap in the menu to close it; Useful instead of attaching events to each menu item that should close the menu on click/tap
    :param ui_menu_anchor: Two values setting the starting position or anchor point of the menu relative to its target
    :param ui_menu_self: Two values setting the menu's own position relative to its target
    :param ui_menu_offset: An array of two numbers to offset the menu horizontally and vertically in pixels
    :param ui_toggle_aria_label: aria-label to be used on the dropdown toggle element
    :param ui_type: 1) Define the button native type attribute (submit, reset, button) or 2) render component with <a> tag so you can access events even if disable or 3) Use 'href' prop and specify 'type' as a media tag
    :param ui_to: Equivalent to Vue Router <router-link> 'to' property; Superseded by 'href' prop if used
    :param ui_replace: Equivalent to Vue Router <router-link> 'replace' property; Superseded by 'href' prop if used
    :param ui_href: Native <a> link href attribute; Has priority over the 'to' and 'replace' props
    :param ui_target: Native <a> link target attribute; Use it only with 'to' or 'href' props
    :param ui_label: The text that will be shown on the button
    :param ui_icon:
    :param ui_icon_right:
    :param ui_outline: Use 'outline' design
    :param ui_flat: Use 'flat' design
    :param ui_unelevated: Remove shadow
    :param ui_rounded: Applies a more prominent border-radius for a squared shape button
    :param ui_push: Use 'push' design
    :param ui_square:
    :param ui_glossy: Applies a glossy effect
    :param ui_fab: Makes button size and shape to fit a Floating Action Button
    :param ui_fab_mini: Makes button size and shape to fit a small Floating Action Button
    :param ui_padding: Apply custom padding (vertical [horizontal]); Size in CSS units, including unit name or standard size name (none|xs|sm|md|lg|xl); Also removes the min width and height when set
    :param ui_color:
    :param ui_text_color:
    :param ui_no_caps: Avoid turning label text into caps (which happens by default)
    :param ui_no_wrap: Avoid label text wrapping
    :param ui_dense:
    :param ui_ripple:
    :param ui_tabindex:
    :param ui_align: Label or content alignment
    :param ui_stack: Stack icon and label vertically instead of on same line (like it is by default)
    :param ui_stretch: When used on flexbox parent, button will stretch to parent's height
    :param ui_loading: Put button into loading state (displays a QSpinner -- can be overridden by using a 'loading' slot)
    :param ui_disable:
    :param ui_size: Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)
    :param ui_transition_show:
    :param ui_transition_hide:
    :param ui_transition_duration: Transition duration (in milliseconds, without unit)
    """

    def __init__(
        self,
        *children,
        ui_model_value: bool | None = None,
        ui_split: bool | None = None,
        ui_dropdown_icon: Any | None = None,
        ui_disable_main_btn: bool | None = None,
        ui_disable_dropdown: bool | None = None,
        ui_no_icon_animation: bool | None = None,
        ui_content_style: str | list | dict | None = None,
        ui_content_class: str | list | dict | None = None,
        ui_cover: bool | None = None,
        ui_persistent: bool | None = None,
        ui_no_route_dismiss: bool | None = None,
        ui_auto_close: bool | None = None,
        ui_menu_anchor: str | None = None,
        ui_menu_self: str | None = None,
        ui_menu_offset: list | None = None,
        ui_toggle_aria_label: str | None = None,
        ui_type: str | None = None,
        ui_to: str | dict | None = None,
        ui_replace: bool | None = None,
        ui_href: str | None = None,
        ui_target: str | None = None,
        ui_label: str | float | None = None,
        ui_icon: Any | None = None,
        ui_icon_right: Any | None = None,
        ui_outline: bool | None = None,
        ui_flat: bool | None = None,
        ui_unelevated: bool | None = None,
        ui_rounded: bool | None = None,
        ui_push: bool | None = None,
        ui_square: Any | None = None,
        ui_glossy: bool | None = None,
        ui_fab: bool | None = None,
        ui_fab_mini: bool | None = None,
        ui_padding: str | None = None,
        ui_color: Any | None = None,
        ui_text_color: Any | None = None,
        ui_no_caps: bool | None = None,
        ui_no_wrap: bool | None = None,
        ui_dense: Any | None = None,
        ui_ripple: Any | None = None,
        ui_tabindex: Any | None = None,
        ui_align: str | None = None,
        ui_stack: bool | None = None,
        ui_stretch: bool | None = None,
        ui_loading: bool | None = None,
        ui_disable: Any | None = None,
        ui_size: str | None = None,
        ui_transition_show: Any | None = None,
        ui_transition_hide: Any | None = None,
        ui_transition_duration: str | float | None = None,
        **kwargs,
    ):
        super().__init__("QBtnDropdown", *children, **kwargs)
        self.on("update:model-value", self.__update_model_value)

        if ui_model_value is not None:
            self._props["model-value"] = ui_model_value
        if ui_split is not None:
            self._props["split"] = ui_split
        if ui_dropdown_icon is not None:
            self._props["dropdown-icon"] = ui_dropdown_icon
        if ui_disable_main_btn is not None:
            self._props["disable-main-btn"] = ui_disable_main_btn
        if ui_disable_dropdown is not None:
            self._props["disable-dropdown"] = ui_disable_dropdown
        if ui_no_icon_animation is not None:
            self._props["no-icon-animation"] = ui_no_icon_animation
        if ui_content_style is not None:
            self._props["content-style"] = ui_content_style
        if ui_content_class is not None:
            self._props["content-class"] = ui_content_class
        if ui_cover is not None:
            self._props["cover"] = ui_cover
        if ui_persistent is not None:
            self._props["persistent"] = ui_persistent
        if ui_no_route_dismiss is not None:
            self._props["no-route-dismiss"] = ui_no_route_dismiss
        if ui_auto_close is not None:
            self._props["auto-close"] = ui_auto_close
        if ui_menu_anchor is not None:
            self._props["menu-anchor"] = ui_menu_anchor
        if ui_menu_self is not None:
            self._props["menu-self"] = ui_menu_self
        if ui_menu_offset is not None:
            self._props["menu-offset"] = ui_menu_offset
        if ui_toggle_aria_label is not None:
            self._props["toggle-aria-label"] = ui_toggle_aria_label
        if ui_type is not None:
            self._props["type"] = ui_type
        if ui_to is not None:
            self._props["to"] = ui_to
        if ui_replace is not None:
            self._props["replace"] = ui_replace
        if ui_href is not None:
            self._props["href"] = ui_href
        if ui_target is not None:
            self._props["target"] = ui_target
        if ui_label is not None:
            self._props["label"] = ui_label
        if ui_icon is not None:
            self._props["icon"] = ui_icon
        if ui_icon_right is not None:
            self._props["icon-right"] = ui_icon_right
        if ui_outline is not None:
            self._props["outline"] = ui_outline
        if ui_flat is not None:
            self._props["flat"] = ui_flat
        if ui_unelevated is not None:
            self._props["unelevated"] = ui_unelevated
        if ui_rounded is not None:
            self._props["rounded"] = ui_rounded
        if ui_push is not None:
            self._props["push"] = ui_push
        if ui_square is not None:
            self._props["square"] = ui_square
        if ui_glossy is not None:
            self._props["glossy"] = ui_glossy
        if ui_fab is not None:
            self._props["fab"] = ui_fab
        if ui_fab_mini is not None:
            self._props["fab-mini"] = ui_fab_mini
        if ui_padding is not None:
            self._props["padding"] = ui_padding
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_text_color is not None:
            self._props["text-color"] = ui_text_color
        if ui_no_caps is not None:
            self._props["no-caps"] = ui_no_caps
        if ui_no_wrap is not None:
            self._props["no-wrap"] = ui_no_wrap
        if ui_dense is not None:
            self._props["dense"] = ui_dense
        if ui_ripple is not None:
            self._props["ripple"] = ui_ripple
        if ui_tabindex is not None:
            self._props["tabindex"] = ui_tabindex
        if ui_align is not None:
            self._props["align"] = ui_align
        if ui_stack is not None:
            self._props["stack"] = ui_stack
        if ui_stretch is not None:
            self._props["stretch"] = ui_stretch
        if ui_loading is not None:
            self._props["loading"] = ui_loading
        if ui_disable is not None:
            self._props["disable"] = ui_disable
        if ui_size is not None:
            self._props["size"] = ui_size
        if ui_transition_show is not None:
            self._props["transition-show"] = ui_transition_show
        if ui_transition_hide is not None:
            self._props["transition-hide"] = ui_transition_hide
        if ui_transition_duration is not None:
            self._props["transition-duration"] = ui_transition_duration

    def __update_model_value(self, event: Event):
        self._set_prop("model-value", event.value)

    @property
    def ui_model_value(self):
        """Model of the component defining shown/hidden state; Either use this property (along with a listener for 'update:model-value' event) OR use v-model directive"""
        return self._props.get("model-value")

    @ui_model_value.setter
    def ui_model_value(self, value):
        self._set_prop("model-value", value)

    @property
    def ui_split(self):
        """Split dropdown icon into its own button"""
        return self._props.get("split")

    @ui_split.setter
    def ui_split(self, value):
        self._set_prop("split", value)

    @property
    def ui_dropdown_icon(self):
        return self._props.get("dropdown-icon")

    @ui_dropdown_icon.setter
    def ui_dropdown_icon(self, value):
        self._set_prop("dropdown-icon", value)

    @property
    def ui_disable_main_btn(self):
        """Disable main button (useful along with 'split' prop)"""
        return self._props.get("disable-main-btn")

    @ui_disable_main_btn.setter
    def ui_disable_main_btn(self, value):
        self._set_prop("disable-main-btn", value)

    @property
    def ui_disable_dropdown(self):
        """Disables dropdown (dropdown button if using along 'split' prop)"""
        return self._props.get("disable-dropdown")

    @ui_disable_dropdown.setter
    def ui_disable_dropdown(self, value):
        self._set_prop("disable-dropdown", value)

    @property
    def ui_no_icon_animation(self):
        """Disables the rotation of the dropdown icon when state is toggled"""
        return self._props.get("no-icon-animation")

    @ui_no_icon_animation.setter
    def ui_no_icon_animation(self, value):
        self._set_prop("no-icon-animation", value)

    @property
    def ui_content_style(self):
        """Style definitions to be attributed to the menu"""
        return self._props.get("content-style")

    @ui_content_style.setter
    def ui_content_style(self, value):
        self._set_prop("content-style", value)

    @property
    def ui_content_class(self):
        """Class definitions to be attributed to the menu"""
        return self._props.get("content-class")

    @ui_content_class.setter
    def ui_content_class(self, value):
        self._set_prop("content-class", value)

    @property
    def ui_cover(self):
        """Allows the menu to cover the button. When used, the 'menu-self' and 'menu-fit' props are no longer effective"""
        return self._props.get("cover")

    @ui_cover.setter
    def ui_cover(self, value):
        self._set_prop("cover", value)

    @property
    def ui_persistent(self):
        """Allows the menu to not be dismissed by a click/tap outside of the menu or by hitting the ESC key; Also, an app route change won't dismiss it"""
        return self._props.get("persistent")

    @ui_persistent.setter
    def ui_persistent(self, value):
        self._set_prop("persistent", value)

    @property
    def ui_no_route_dismiss(self):
        """Changing route app won't dismiss the popup; No need to set it if 'persistent' prop is also set"""
        return self._props.get("no-route-dismiss")

    @ui_no_route_dismiss.setter
    def ui_no_route_dismiss(self, value):
        self._set_prop("no-route-dismiss", value)

    @property
    def ui_auto_close(self):
        """Allows any click/tap in the menu to close it; Useful instead of attaching events to each menu item that should close the menu on click/tap"""
        return self._props.get("auto-close")

    @ui_auto_close.setter
    def ui_auto_close(self, value):
        self._set_prop("auto-close", value)

    @property
    def ui_menu_anchor(self):
        """Two values setting the starting position or anchor point of the menu relative to its target"""
        return self._props.get("menu-anchor")

    @ui_menu_anchor.setter
    def ui_menu_anchor(self, value):
        self._set_prop("menu-anchor", value)

    @property
    def ui_menu_self(self):
        """Two values setting the menu's own position relative to its target"""
        return self._props.get("menu-self")

    @ui_menu_self.setter
    def ui_menu_self(self, value):
        self._set_prop("menu-self", value)

    @property
    def ui_menu_offset(self):
        """An array of two numbers to offset the menu horizontally and vertically in pixels"""
        return self._props.get("menu-offset")

    @ui_menu_offset.setter
    def ui_menu_offset(self, value):
        self._set_prop("menu-offset", value)

    @property
    def ui_toggle_aria_label(self):
        """aria-label to be used on the dropdown toggle element"""
        return self._props.get("toggle-aria-label")

    @ui_toggle_aria_label.setter
    def ui_toggle_aria_label(self, value):
        self._set_prop("toggle-aria-label", value)

    @property
    def ui_type(self):
        """1) Define the button native type attribute (submit, reset, button) or 2) render component with <a> tag so you can access events even if disable or 3) Use 'href' prop and specify 'type' as a media tag"""
        return self._props.get("type")

    @ui_type.setter
    def ui_type(self, value):
        self._set_prop("type", value)

    @property
    def ui_to(self):
        """Equivalent to Vue Router <router-link> 'to' property; Superseded by 'href' prop if used"""
        return self._props.get("to")

    @ui_to.setter
    def ui_to(self, value):
        self._set_prop("to", value)

    @property
    def ui_replace(self):
        """Equivalent to Vue Router <router-link> 'replace' property; Superseded by 'href' prop if used"""
        return self._props.get("replace")

    @ui_replace.setter
    def ui_replace(self, value):
        self._set_prop("replace", value)

    @property
    def ui_href(self):
        """Native <a> link href attribute; Has priority over the 'to' and 'replace' props"""
        return self._props.get("href")

    @ui_href.setter
    def ui_href(self, value):
        self._set_prop("href", value)

    @property
    def ui_target(self):
        """Native <a> link target attribute; Use it only with 'to' or 'href' props"""
        return self._props.get("target")

    @ui_target.setter
    def ui_target(self, value):
        self._set_prop("target", value)

    @property
    def ui_label(self):
        """The text that will be shown on the button"""
        return self._props.get("label")

    @ui_label.setter
    def ui_label(self, value):
        self._set_prop("label", value)

    @property
    def ui_icon(self):
        return self._props.get("icon")

    @ui_icon.setter
    def ui_icon(self, value):
        self._set_prop("icon", value)

    @property
    def ui_icon_right(self):
        return self._props.get("icon-right")

    @ui_icon_right.setter
    def ui_icon_right(self, value):
        self._set_prop("icon-right", value)

    @property
    def ui_outline(self):
        """Use 'outline' design"""
        return self._props.get("outline")

    @ui_outline.setter
    def ui_outline(self, value):
        self._set_prop("outline", value)

    @property
    def ui_flat(self):
        """Use 'flat' design"""
        return self._props.get("flat")

    @ui_flat.setter
    def ui_flat(self, value):
        self._set_prop("flat", value)

    @property
    def ui_unelevated(self):
        """Remove shadow"""
        return self._props.get("unelevated")

    @ui_unelevated.setter
    def ui_unelevated(self, value):
        self._set_prop("unelevated", value)

    @property
    def ui_rounded(self):
        """Applies a more prominent border-radius for a squared shape button"""
        return self._props.get("rounded")

    @ui_rounded.setter
    def ui_rounded(self, value):
        self._set_prop("rounded", value)

    @property
    def ui_push(self):
        """Use 'push' design"""
        return self._props.get("push")

    @ui_push.setter
    def ui_push(self, value):
        self._set_prop("push", value)

    @property
    def ui_square(self):
        return self._props.get("square")

    @ui_square.setter
    def ui_square(self, value):
        self._set_prop("square", value)

    @property
    def ui_glossy(self):
        """Applies a glossy effect"""
        return self._props.get("glossy")

    @ui_glossy.setter
    def ui_glossy(self, value):
        self._set_prop("glossy", value)

    @property
    def ui_fab(self):
        """Makes button size and shape to fit a Floating Action Button"""
        return self._props.get("fab")

    @ui_fab.setter
    def ui_fab(self, value):
        self._set_prop("fab", value)

    @property
    def ui_fab_mini(self):
        """Makes button size and shape to fit a small Floating Action Button"""
        return self._props.get("fab-mini")

    @ui_fab_mini.setter
    def ui_fab_mini(self, value):
        self._set_prop("fab-mini", value)

    @property
    def ui_padding(self):
        """Apply custom padding (vertical [horizontal]); Size in CSS units, including unit name or standard size name (none|xs|sm|md|lg|xl); Also removes the min width and height when set"""
        return self._props.get("padding")

    @ui_padding.setter
    def ui_padding(self, value):
        self._set_prop("padding", value)

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_text_color(self):
        return self._props.get("text-color")

    @ui_text_color.setter
    def ui_text_color(self, value):
        self._set_prop("text-color", value)

    @property
    def ui_no_caps(self):
        """Avoid turning label text into caps (which happens by default)"""
        return self._props.get("no-caps")

    @ui_no_caps.setter
    def ui_no_caps(self, value):
        self._set_prop("no-caps", value)

    @property
    def ui_no_wrap(self):
        """Avoid label text wrapping"""
        return self._props.get("no-wrap")

    @ui_no_wrap.setter
    def ui_no_wrap(self, value):
        self._set_prop("no-wrap", value)

    @property
    def ui_dense(self):
        return self._props.get("dense")

    @ui_dense.setter
    def ui_dense(self, value):
        self._set_prop("dense", value)

    @property
    def ui_ripple(self):
        return self._props.get("ripple")

    @ui_ripple.setter
    def ui_ripple(self, value):
        self._set_prop("ripple", value)

    @property
    def ui_tabindex(self):
        return self._props.get("tabindex")

    @ui_tabindex.setter
    def ui_tabindex(self, value):
        self._set_prop("tabindex", value)

    @property
    def ui_align(self):
        """Label or content alignment"""
        return self._props.get("align")

    @ui_align.setter
    def ui_align(self, value):
        self._set_prop("align", value)

    @property
    def ui_stack(self):
        """Stack icon and label vertically instead of on same line (like it is by default)"""
        return self._props.get("stack")

    @ui_stack.setter
    def ui_stack(self, value):
        self._set_prop("stack", value)

    @property
    def ui_stretch(self):
        """When used on flexbox parent, button will stretch to parent's height"""
        return self._props.get("stretch")

    @ui_stretch.setter
    def ui_stretch(self, value):
        self._set_prop("stretch", value)

    @property
    def ui_loading(self):
        """Put button into loading state (displays a QSpinner -- can be overridden by using a 'loading' slot)"""
        return self._props.get("loading")

    @ui_loading.setter
    def ui_loading(self, value):
        self._set_prop("loading", value)

    @property
    def ui_disable(self):
        return self._props.get("disable")

    @ui_disable.setter
    def ui_disable(self, value):
        self._set_prop("disable", value)

    @property
    def ui_size(self):
        """Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)"""
        return self._props.get("size")

    @ui_size.setter
    def ui_size(self, value):
        self._set_prop("size", value)

    @property
    def ui_transition_show(self):
        return self._props.get("transition-show")

    @ui_transition_show.setter
    def ui_transition_show(self, value):
        self._set_prop("transition-show", value)

    @property
    def ui_transition_hide(self):
        return self._props.get("transition-hide")

    @ui_transition_hide.setter
    def ui_transition_hide(self, value):
        self._set_prop("transition-hide", value)

    @property
    def ui_transition_duration(self):
        """Transition duration (in milliseconds, without unit)"""
        return self._props.get("transition-duration")

    @ui_transition_duration.setter
    def ui_transition_duration(self, value):
        self._set_prop("transition-duration", value)

    @property
    def ui_slot_label(self):
        """Customize main button's content through this slot, unless you're using the 'icon' and 'label' props"""
        return self.ui_slots.get("label", [])

    @ui_slot_label.setter
    def ui_slot_label(self, value):
        self._set_slot("label", value)

    @property
    def ui_slot_loading(self):
        """Override the default QSpinner when in 'loading' state"""
        return self.ui_slots.get("loading", [])

    @ui_slot_loading.setter
    def ui_slot_loading(self, value):
        self._set_slot("loading", value)

    def on_before_hide(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("before-hide", handler, arg)

    def on_before_show(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("before-show", handler, arg)

    def on_click(self, handler: Callable, arg: object = None):
        """
        Emitted when user clicks/taps on the main button (not the icon one, if using 'split')

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("click.stop", handler, arg)

    def on_hide(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("hide", handler, arg)

    def on_show(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("show", handler, arg)

    def on_update_model_value(self, handler: Callable, arg: object = None):
        """
        Emitted when showing/hidden state changes; Is also used by v-model

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("update:model-value", handler, arg)

    def ui_hide(self):
        self._js_call_method("hide")

    def ui_show(self):
        self._js_call_method("show")

    def ui_toggle(self):
        self._js_call_method("toggle")

    def _get_js_methods(self):
        return ["hide", "show", "toggle"]


class QBtnGroup(Component):
    """
    Quasar Component: `QBtnGroup <https://v2.quasar.dev/vue-components/button-group>`__

    :param ui_spread: Spread horizontally to all available space
    :param ui_outline: Use 'outline' design for buttons
    :param ui_flat: Use 'flat' design for buttons
    :param ui_unelevated: Remove shadow on buttons
    :param ui_rounded: Applies a more prominent border-radius for squared shape buttons
    :param ui_square:
    :param ui_push: Use 'push' design for buttons
    :param ui_stretch: When used on flexbox parent, buttons will stretch to parent's height
    :param ui_glossy: Applies a glossy effect
    """

    def __init__(
        self,
        *children,
        ui_spread: bool | None = None,
        ui_outline: bool | None = None,
        ui_flat: bool | None = None,
        ui_unelevated: bool | None = None,
        ui_rounded: bool | None = None,
        ui_square: Any | None = None,
        ui_push: bool | None = None,
        ui_stretch: bool | None = None,
        ui_glossy: bool | None = None,
        **kwargs,
    ):
        super().__init__("QBtnGroup", *children, **kwargs)
        if ui_spread is not None:
            self._props["spread"] = ui_spread
        if ui_outline is not None:
            self._props["outline"] = ui_outline
        if ui_flat is not None:
            self._props["flat"] = ui_flat
        if ui_unelevated is not None:
            self._props["unelevated"] = ui_unelevated
        if ui_rounded is not None:
            self._props["rounded"] = ui_rounded
        if ui_square is not None:
            self._props["square"] = ui_square
        if ui_push is not None:
            self._props["push"] = ui_push
        if ui_stretch is not None:
            self._props["stretch"] = ui_stretch
        if ui_glossy is not None:
            self._props["glossy"] = ui_glossy

    @property
    def ui_spread(self):
        """Spread horizontally to all available space"""
        return self._props.get("spread")

    @ui_spread.setter
    def ui_spread(self, value):
        self._set_prop("spread", value)

    @property
    def ui_outline(self):
        """Use 'outline' design for buttons"""
        return self._props.get("outline")

    @ui_outline.setter
    def ui_outline(self, value):
        self._set_prop("outline", value)

    @property
    def ui_flat(self):
        """Use 'flat' design for buttons"""
        return self._props.get("flat")

    @ui_flat.setter
    def ui_flat(self, value):
        self._set_prop("flat", value)

    @property
    def ui_unelevated(self):
        """Remove shadow on buttons"""
        return self._props.get("unelevated")

    @ui_unelevated.setter
    def ui_unelevated(self, value):
        self._set_prop("unelevated", value)

    @property
    def ui_rounded(self):
        """Applies a more prominent border-radius for squared shape buttons"""
        return self._props.get("rounded")

    @ui_rounded.setter
    def ui_rounded(self, value):
        self._set_prop("rounded", value)

    @property
    def ui_square(self):
        return self._props.get("square")

    @ui_square.setter
    def ui_square(self, value):
        self._set_prop("square", value)

    @property
    def ui_push(self):
        """Use 'push' design for buttons"""
        return self._props.get("push")

    @ui_push.setter
    def ui_push(self, value):
        self._set_prop("push", value)

    @property
    def ui_stretch(self):
        """When used on flexbox parent, buttons will stretch to parent's height"""
        return self._props.get("stretch")

    @ui_stretch.setter
    def ui_stretch(self, value):
        self._set_prop("stretch", value)

    @property
    def ui_glossy(self):
        """Applies a glossy effect"""
        return self._props.get("glossy")

    @ui_glossy.setter
    def ui_glossy(self, value):
        self._set_prop("glossy", value)

    def _get_js_methods(self):
        return []


class QBtnToggle(Component):
    """
    Quasar Component: `QBtnToggle <https://v2.quasar.dev/vue-components/button-toggle>`__

    :param ui_model_value: Model of the component; Either use this property (along with a listener for 'update:modelValue' event) OR use v-model directive
    :param ui_options: Array of Objects defining each option
    :param ui_color:
    :param ui_text_color:
    :param ui_toggle_color:
    :param ui_toggle_text_color:
    :param ui_spread: Spread horizontally to all available space
    :param ui_outline: Use 'outline' design
    :param ui_flat: Use 'flat' design
    :param ui_unelevated: Remove shadow
    :param ui_rounded: Applies a more prominent border-radius for a squared shape button
    :param ui_push: Use 'push' design
    :param ui_glossy: Applies a glossy effect
    :param ui_size: Button size name or a CSS unit including unit name
    :param ui_padding: Apply custom padding (vertical [horizontal]); Size in CSS units, including unit name or standard size name (none|xs|sm|md|lg|xl); Also removes the min width and height when set
    :param ui_no_caps: Avoid turning label text into caps (which happens by default)
    :param ui_no_wrap: Avoid label text wrapping
    :param ui_ripple:
    :param ui_dense:
    :param ui_readonly:
    :param ui_disable:
    :param ui_stack: Stack icon and label vertically instead of on same line (like it is by default)
    :param ui_stretch: When used on flexbox parent, button will stretch to parent's height
    :param ui_clearable: Clears model on click of the already selected button
    :param ui_name: Used to specify the name of the control; Useful if dealing with forms submitted directly to a URL
    """

    def __init__(
        self,
        *children,
        ui_model_value: Any | None = None,
        ui_options: list | None = None,
        ui_color: Any | None = None,
        ui_text_color: Any | None = None,
        ui_toggle_color: Any | None = None,
        ui_toggle_text_color: Any | None = None,
        ui_spread: bool | None = None,
        ui_outline: bool | None = None,
        ui_flat: bool | None = None,
        ui_unelevated: bool | None = None,
        ui_rounded: bool | None = None,
        ui_push: bool | None = None,
        ui_glossy: bool | None = None,
        ui_size: str | None = None,
        ui_padding: str | None = None,
        ui_no_caps: bool | None = None,
        ui_no_wrap: bool | None = None,
        ui_ripple: Any | None = None,
        ui_dense: Any | None = None,
        ui_readonly: Any | None = None,
        ui_disable: Any | None = None,
        ui_stack: bool | None = None,
        ui_stretch: bool | None = None,
        ui_clearable: bool | None = None,
        ui_name: str | None = None,
        **kwargs,
    ):
        super().__init__("QBtnToggle", *children, **kwargs)
        self.on("update:model-value", self.__update_model_value)

        if ui_model_value is not None:
            self._props["model-value"] = ui_model_value
        if ui_options is not None:
            self._props["options"] = ui_options
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_text_color is not None:
            self._props["text-color"] = ui_text_color
        if ui_toggle_color is not None:
            self._props["toggle-color"] = ui_toggle_color
        if ui_toggle_text_color is not None:
            self._props["toggle-text-color"] = ui_toggle_text_color
        if ui_spread is not None:
            self._props["spread"] = ui_spread
        if ui_outline is not None:
            self._props["outline"] = ui_outline
        if ui_flat is not None:
            self._props["flat"] = ui_flat
        if ui_unelevated is not None:
            self._props["unelevated"] = ui_unelevated
        if ui_rounded is not None:
            self._props["rounded"] = ui_rounded
        if ui_push is not None:
            self._props["push"] = ui_push
        if ui_glossy is not None:
            self._props["glossy"] = ui_glossy
        if ui_size is not None:
            self._props["size"] = ui_size
        if ui_padding is not None:
            self._props["padding"] = ui_padding
        if ui_no_caps is not None:
            self._props["no-caps"] = ui_no_caps
        if ui_no_wrap is not None:
            self._props["no-wrap"] = ui_no_wrap
        if ui_ripple is not None:
            self._props["ripple"] = ui_ripple
        if ui_dense is not None:
            self._props["dense"] = ui_dense
        if ui_readonly is not None:
            self._props["readonly"] = ui_readonly
        if ui_disable is not None:
            self._props["disable"] = ui_disable
        if ui_stack is not None:
            self._props["stack"] = ui_stack
        if ui_stretch is not None:
            self._props["stretch"] = ui_stretch
        if ui_clearable is not None:
            self._props["clearable"] = ui_clearable
        if ui_name is not None:
            self._props["name"] = ui_name

    def __update_model_value(self, event: Event):
        self._set_prop("model-value", event.value)

    @property
    def ui_model_value(self):
        """Model of the component; Either use this property (along with a listener for 'update:modelValue' event) OR use v-model directive"""
        return self._props.get("model-value")

    @ui_model_value.setter
    def ui_model_value(self, value):
        self._set_prop("model-value", value)

    @property
    def ui_options(self):
        """Array of Objects defining each option"""
        return self._props.get("options")

    @ui_options.setter
    def ui_options(self, value):
        self._set_prop("options", value)

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_text_color(self):
        return self._props.get("text-color")

    @ui_text_color.setter
    def ui_text_color(self, value):
        self._set_prop("text-color", value)

    @property
    def ui_toggle_color(self):
        return self._props.get("toggle-color")

    @ui_toggle_color.setter
    def ui_toggle_color(self, value):
        self._set_prop("toggle-color", value)

    @property
    def ui_toggle_text_color(self):
        return self._props.get("toggle-text-color")

    @ui_toggle_text_color.setter
    def ui_toggle_text_color(self, value):
        self._set_prop("toggle-text-color", value)

    @property
    def ui_spread(self):
        """Spread horizontally to all available space"""
        return self._props.get("spread")

    @ui_spread.setter
    def ui_spread(self, value):
        self._set_prop("spread", value)

    @property
    def ui_outline(self):
        """Use 'outline' design"""
        return self._props.get("outline")

    @ui_outline.setter
    def ui_outline(self, value):
        self._set_prop("outline", value)

    @property
    def ui_flat(self):
        """Use 'flat' design"""
        return self._props.get("flat")

    @ui_flat.setter
    def ui_flat(self, value):
        self._set_prop("flat", value)

    @property
    def ui_unelevated(self):
        """Remove shadow"""
        return self._props.get("unelevated")

    @ui_unelevated.setter
    def ui_unelevated(self, value):
        self._set_prop("unelevated", value)

    @property
    def ui_rounded(self):
        """Applies a more prominent border-radius for a squared shape button"""
        return self._props.get("rounded")

    @ui_rounded.setter
    def ui_rounded(self, value):
        self._set_prop("rounded", value)

    @property
    def ui_push(self):
        """Use 'push' design"""
        return self._props.get("push")

    @ui_push.setter
    def ui_push(self, value):
        self._set_prop("push", value)

    @property
    def ui_glossy(self):
        """Applies a glossy effect"""
        return self._props.get("glossy")

    @ui_glossy.setter
    def ui_glossy(self, value):
        self._set_prop("glossy", value)

    @property
    def ui_size(self):
        """Button size name or a CSS unit including unit name"""
        return self._props.get("size")

    @ui_size.setter
    def ui_size(self, value):
        self._set_prop("size", value)

    @property
    def ui_padding(self):
        """Apply custom padding (vertical [horizontal]); Size in CSS units, including unit name or standard size name (none|xs|sm|md|lg|xl); Also removes the min width and height when set"""
        return self._props.get("padding")

    @ui_padding.setter
    def ui_padding(self, value):
        self._set_prop("padding", value)

    @property
    def ui_no_caps(self):
        """Avoid turning label text into caps (which happens by default)"""
        return self._props.get("no-caps")

    @ui_no_caps.setter
    def ui_no_caps(self, value):
        self._set_prop("no-caps", value)

    @property
    def ui_no_wrap(self):
        """Avoid label text wrapping"""
        return self._props.get("no-wrap")

    @ui_no_wrap.setter
    def ui_no_wrap(self, value):
        self._set_prop("no-wrap", value)

    @property
    def ui_ripple(self):
        return self._props.get("ripple")

    @ui_ripple.setter
    def ui_ripple(self, value):
        self._set_prop("ripple", value)

    @property
    def ui_dense(self):
        return self._props.get("dense")

    @ui_dense.setter
    def ui_dense(self, value):
        self._set_prop("dense", value)

    @property
    def ui_readonly(self):
        return self._props.get("readonly")

    @ui_readonly.setter
    def ui_readonly(self, value):
        self._set_prop("readonly", value)

    @property
    def ui_disable(self):
        return self._props.get("disable")

    @ui_disable.setter
    def ui_disable(self, value):
        self._set_prop("disable", value)

    @property
    def ui_stack(self):
        """Stack icon and label vertically instead of on same line (like it is by default)"""
        return self._props.get("stack")

    @ui_stack.setter
    def ui_stack(self, value):
        self._set_prop("stack", value)

    @property
    def ui_stretch(self):
        """When used on flexbox parent, button will stretch to parent's height"""
        return self._props.get("stretch")

    @ui_stretch.setter
    def ui_stretch(self, value):
        self._set_prop("stretch", value)

    @property
    def ui_clearable(self):
        """Clears model on click of the already selected button"""
        return self._props.get("clearable")

    @ui_clearable.setter
    def ui_clearable(self, value):
        self._set_prop("clearable", value)

    @property
    def ui_name(self):
        """Used to specify the name of the control; Useful if dealing with forms submitted directly to a URL"""
        return self._props.get("name")

    @ui_name.setter
    def ui_name(self, value):
        self._set_prop("name", value)

    def set_dynamic_slot(self, name: str, items: list[Component]):
        """Any other dynamic slots to be used with 'slot' property of the 'options' prop"""
        self._set_slot(name, items)

    def on_clear(self, handler: Callable, arg: object = None):
        """
        When using the 'clearable' property, this event is emitted when the already selected button is clicked

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("clear", handler, arg)

    def on_click(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("click.stop", handler, arg)

    def on_update_model_value(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("update:model-value", handler, arg)

    def _get_js_methods(self):
        return []


class QCardActions(Component):
    """
    Quasar Component: `QCardActions <https://v2.quasar.dev/vue-components/card>`__

    :param ui_align: Specify how to align the actions; For horizontal mode, the default is 'left', while for vertical mode, the default is 'stretch'
    :param ui_vertical: Display actions one below the other
    """

    def __init__(
        self,
        *children,
        ui_align: str | None = None,
        ui_vertical: bool | None = None,
        **kwargs,
    ):
        super().__init__("QCardActions", *children, **kwargs)
        if ui_align is not None:
            self._props["align"] = ui_align
        if ui_vertical is not None:
            self._props["vertical"] = ui_vertical

    @property
    def ui_align(self):
        """Specify how to align the actions; For horizontal mode, the default is 'left', while for vertical mode, the default is 'stretch'"""
        return self._props.get("align")

    @ui_align.setter
    def ui_align(self, value):
        self._set_prop("align", value)

    @property
    def ui_vertical(self):
        """Display actions one below the other"""
        return self._props.get("vertical")

    @ui_vertical.setter
    def ui_vertical(self, value):
        self._set_prop("vertical", value)

    def _get_js_methods(self):
        return []


class QCard(Component):
    """
    Quasar Component: `QCard <https://v2.quasar.dev/vue-components/card>`__

    :param ui_dark:
    :param ui_square:
    :param ui_flat:
    :param ui_bordered:
    :param ui_tag:
    """

    def __init__(
        self,
        *children,
        ui_dark: Any | None = None,
        ui_square: Any | None = None,
        ui_flat: Any | None = None,
        ui_bordered: Any | None = None,
        ui_tag: Any | None = None,
        **kwargs,
    ):
        super().__init__("QCard", *children, **kwargs)
        if ui_dark is not None:
            self._props["dark"] = ui_dark
        if ui_square is not None:
            self._props["square"] = ui_square
        if ui_flat is not None:
            self._props["flat"] = ui_flat
        if ui_bordered is not None:
            self._props["bordered"] = ui_bordered
        if ui_tag is not None:
            self._props["tag"] = ui_tag

    @property
    def ui_dark(self):
        return self._props.get("dark")

    @ui_dark.setter
    def ui_dark(self, value):
        self._set_prop("dark", value)

    @property
    def ui_square(self):
        return self._props.get("square")

    @ui_square.setter
    def ui_square(self, value):
        self._set_prop("square", value)

    @property
    def ui_flat(self):
        return self._props.get("flat")

    @ui_flat.setter
    def ui_flat(self, value):
        self._set_prop("flat", value)

    @property
    def ui_bordered(self):
        return self._props.get("bordered")

    @ui_bordered.setter
    def ui_bordered(self, value):
        self._set_prop("bordered", value)

    @property
    def ui_tag(self):
        return self._props.get("tag")

    @ui_tag.setter
    def ui_tag(self, value):
        self._set_prop("tag", value)

    def _get_js_methods(self):
        return []


class QCardSection(Component):
    """
    Quasar Component: `QCardSection <https://v2.quasar.dev/vue-components/card>`__

    :param ui_horizontal: Display a horizontal section (will have no padding and can contain other QCardSection)
    :param ui_tag:
    """

    def __init__(
        self,
        *children,
        ui_horizontal: bool | None = None,
        ui_tag: Any | None = None,
        **kwargs,
    ):
        super().__init__("QCardSection", *children, **kwargs)
        if ui_horizontal is not None:
            self._props["horizontal"] = ui_horizontal
        if ui_tag is not None:
            self._props["tag"] = ui_tag

    @property
    def ui_horizontal(self):
        """Display a horizontal section (will have no padding and can contain other QCardSection)"""
        return self._props.get("horizontal")

    @ui_horizontal.setter
    def ui_horizontal(self, value):
        self._set_prop("horizontal", value)

    @property
    def ui_tag(self):
        return self._props.get("tag")

    @ui_tag.setter
    def ui_tag(self, value):
        self._set_prop("tag", value)

    def _get_js_methods(self):
        return []


class QCarousel(Component):
    """
    Quasar Component: `QCarousel <https://v2.quasar.dev/vue-components/carousel>`__

    :param ui_dark:
    :param ui_height: Height of Carousel in CSS units, including unit name
    :param ui_padding: Applies a default padding to each slide, according to the usage of 'arrows' and 'navigation' props
    :param ui_control_color: Color name for QCarousel button controls (arrows, navigation) from the Quasar Color Palette
    :param ui_control_text_color: Color name for text color of QCarousel button controls (arrows, navigation) from the Quasar Color Palette
    :param ui_control_type: Type of button to use for controls (arrows, navigation)
    :param ui_autoplay: Jump to next slide (if 'true' or val > 0) or previous slide (if val < 0) at fixed time intervals (in milliseconds); 'false' disables autoplay, 'true' enables it for 5000ms intervals
    :param ui_arrows: Show navigation arrow buttons
    :param ui_prev_icon:
    :param ui_next_icon:
    :param ui_navigation: Show navigation dots
    :param ui_navigation_position: Side to stick navigation to
    :param ui_navigation_icon:
    :param ui_navigation_active_icon: Icon name following Quasar convention for the active (current slide) navigation icon; Make sure you have the icon library installed unless you are using 'img:' prefix
    :param ui_thumbnails: Show thumbnails
    :param ui_transition_prev: One of Quasar's embedded transitions (has effect only if 'animated' prop is set)
    :param ui_transition_next: One of Quasar's embedded transitions (has effect only if 'animated' prop is set)
    :param ui_model_value: Model of the component defining the current panel's name; If a Number is used, it does not define the panel's index, but rather the panel's name which can also be an Integer; Either use this property (along with a listener for 'update:model-value' event) OR use the v-model directive.
    :param ui_keep_alive: Equivalent to using Vue's native <keep-alive> component on the content
    :param ui_keep_alive_include: Equivalent to using Vue's native include prop for <keep-alive>; Values must be valid Vue component names
    :param ui_keep_alive_exclude: Equivalent to using Vue's native exclude prop for <keep-alive>; Values must be valid Vue component names
    :param ui_keep_alive_max: Equivalent to using Vue's native max prop for <keep-alive>
    :param ui_animated: Enable transitions between panel (also see 'transition-prev' and 'transition-next' props)
    :param ui_infinite: Makes component appear as infinite (when reaching last panel, next one will become the first one)
    :param ui_swipeable: Enable swipe events (may interfere with content's touch/mouse events)
    :param ui_vertical: Default transitions and swipe actions will be on the vertical axis
    :param ui_transition_duration: Transition duration (in milliseconds, without unit)
    :param ui_fullscreen: Fullscreen mode
    :param ui_no_route_fullscreen_exit: Changing route app won't exit fullscreen
    """

    def __init__(
        self,
        *children,
        ui_dark: Any | None = None,
        ui_height: Any | None = None,
        ui_padding: bool | None = None,
        ui_control_color: Any | None = None,
        ui_control_text_color: Any | None = None,
        ui_control_type: str | None = None,
        ui_autoplay: float | bool | None = None,
        ui_arrows: bool | None = None,
        ui_prev_icon: Any | None = None,
        ui_next_icon: Any | None = None,
        ui_navigation: bool | None = None,
        ui_navigation_position: str | None = None,
        ui_navigation_icon: Any | None = None,
        ui_navigation_active_icon: Any | None = None,
        ui_thumbnails: bool | None = None,
        ui_transition_prev: Any | None = None,
        ui_transition_next: Any | None = None,
        ui_model_value: Any | None = None,
        ui_keep_alive: bool | None = None,
        ui_keep_alive_include: str | list | re.Pattern | None = None,
        ui_keep_alive_exclude: str | list | re.Pattern | None = None,
        ui_keep_alive_max: float | None = None,
        ui_animated: bool | None = None,
        ui_infinite: bool | None = None,
        ui_swipeable: bool | None = None,
        ui_vertical: bool | None = None,
        ui_transition_duration: str | float | None = None,
        ui_fullscreen: bool | None = None,
        ui_no_route_fullscreen_exit: bool | None = None,
        **kwargs,
    ):
        super().__init__("QCarousel", *children, **kwargs)
        self.on("update:model-value", self.__update_model_value)

        if ui_dark is not None:
            self._props["dark"] = ui_dark
        if ui_height is not None:
            self._props["height"] = ui_height
        if ui_padding is not None:
            self._props["padding"] = ui_padding
        if ui_control_color is not None:
            self._props["control-color"] = ui_control_color
        if ui_control_text_color is not None:
            self._props["control-text-color"] = ui_control_text_color
        if ui_control_type is not None:
            self._props["control-type"] = ui_control_type
        if ui_autoplay is not None:
            self._props["autoplay"] = ui_autoplay
        if ui_arrows is not None:
            self._props["arrows"] = ui_arrows
        if ui_prev_icon is not None:
            self._props["prev-icon"] = ui_prev_icon
        if ui_next_icon is not None:
            self._props["next-icon"] = ui_next_icon
        if ui_navigation is not None:
            self._props["navigation"] = ui_navigation
        if ui_navigation_position is not None:
            self._props["navigation-position"] = ui_navigation_position
        if ui_navigation_icon is not None:
            self._props["navigation-icon"] = ui_navigation_icon
        if ui_navigation_active_icon is not None:
            self._props["navigation-active-icon"] = ui_navigation_active_icon
        if ui_thumbnails is not None:
            self._props["thumbnails"] = ui_thumbnails
        if ui_transition_prev is not None:
            self._props["transition-prev"] = ui_transition_prev
        if ui_transition_next is not None:
            self._props["transition-next"] = ui_transition_next
        if ui_model_value is not None:
            self._props["model-value"] = ui_model_value
        if ui_keep_alive is not None:
            self._props["keep-alive"] = ui_keep_alive
        if ui_keep_alive_include is not None:
            self._props["keep-alive-include"] = ui_keep_alive_include
        if ui_keep_alive_exclude is not None:
            self._props["keep-alive-exclude"] = ui_keep_alive_exclude
        if ui_keep_alive_max is not None:
            self._props["keep-alive-max"] = ui_keep_alive_max
        if ui_animated is not None:
            self._props["animated"] = ui_animated
        if ui_infinite is not None:
            self._props["infinite"] = ui_infinite
        if ui_swipeable is not None:
            self._props["swipeable"] = ui_swipeable
        if ui_vertical is not None:
            self._props["vertical"] = ui_vertical
        if ui_transition_duration is not None:
            self._props["transition-duration"] = ui_transition_duration
        if ui_fullscreen is not None:
            self._props["fullscreen"] = ui_fullscreen
        if ui_no_route_fullscreen_exit is not None:
            self._props["no-route-fullscreen-exit"] = (
                ui_no_route_fullscreen_exit
            )

    def __update_model_value(self, event: Event):
        self._set_prop("model-value", event.value)

    @property
    def ui_dark(self):
        return self._props.get("dark")

    @ui_dark.setter
    def ui_dark(self, value):
        self._set_prop("dark", value)

    @property
    def ui_height(self):
        """Height of Carousel in CSS units, including unit name"""
        return self._props.get("height")

    @ui_height.setter
    def ui_height(self, value):
        self._set_prop("height", value)

    @property
    def ui_padding(self):
        """Applies a default padding to each slide, according to the usage of 'arrows' and 'navigation' props"""
        return self._props.get("padding")

    @ui_padding.setter
    def ui_padding(self, value):
        self._set_prop("padding", value)

    @property
    def ui_control_color(self):
        """Color name for QCarousel button controls (arrows, navigation) from the Quasar Color Palette"""
        return self._props.get("control-color")

    @ui_control_color.setter
    def ui_control_color(self, value):
        self._set_prop("control-color", value)

    @property
    def ui_control_text_color(self):
        """Color name for text color of QCarousel button controls (arrows, navigation) from the Quasar Color Palette"""
        return self._props.get("control-text-color")

    @ui_control_text_color.setter
    def ui_control_text_color(self, value):
        self._set_prop("control-text-color", value)

    @property
    def ui_control_type(self):
        """Type of button to use for controls (arrows, navigation)"""
        return self._props.get("control-type")

    @ui_control_type.setter
    def ui_control_type(self, value):
        self._set_prop("control-type", value)

    @property
    def ui_autoplay(self):
        """Jump to next slide (if 'true' or val > 0) or previous slide (if val < 0) at fixed time intervals (in milliseconds); 'false' disables autoplay, 'true' enables it for 5000ms intervals"""
        return self._props.get("autoplay")

    @ui_autoplay.setter
    def ui_autoplay(self, value):
        self._set_prop("autoplay", value)

    @property
    def ui_arrows(self):
        """Show navigation arrow buttons"""
        return self._props.get("arrows")

    @ui_arrows.setter
    def ui_arrows(self, value):
        self._set_prop("arrows", value)

    @property
    def ui_prev_icon(self):
        return self._props.get("prev-icon")

    @ui_prev_icon.setter
    def ui_prev_icon(self, value):
        self._set_prop("prev-icon", value)

    @property
    def ui_next_icon(self):
        return self._props.get("next-icon")

    @ui_next_icon.setter
    def ui_next_icon(self, value):
        self._set_prop("next-icon", value)

    @property
    def ui_navigation(self):
        """Show navigation dots"""
        return self._props.get("navigation")

    @ui_navigation.setter
    def ui_navigation(self, value):
        self._set_prop("navigation", value)

    @property
    def ui_navigation_position(self):
        """Side to stick navigation to"""
        return self._props.get("navigation-position")

    @ui_navigation_position.setter
    def ui_navigation_position(self, value):
        self._set_prop("navigation-position", value)

    @property
    def ui_navigation_icon(self):
        return self._props.get("navigation-icon")

    @ui_navigation_icon.setter
    def ui_navigation_icon(self, value):
        self._set_prop("navigation-icon", value)

    @property
    def ui_navigation_active_icon(self):
        """Icon name following Quasar convention for the active (current slide) navigation icon; Make sure you have the icon library installed unless you are using 'img:' prefix"""
        return self._props.get("navigation-active-icon")

    @ui_navigation_active_icon.setter
    def ui_navigation_active_icon(self, value):
        self._set_prop("navigation-active-icon", value)

    @property
    def ui_thumbnails(self):
        """Show thumbnails"""
        return self._props.get("thumbnails")

    @ui_thumbnails.setter
    def ui_thumbnails(self, value):
        self._set_prop("thumbnails", value)

    @property
    def ui_transition_prev(self):
        """One of Quasar's embedded transitions (has effect only if 'animated' prop is set)"""
        return self._props.get("transition-prev")

    @ui_transition_prev.setter
    def ui_transition_prev(self, value):
        self._set_prop("transition-prev", value)

    @property
    def ui_transition_next(self):
        """One of Quasar's embedded transitions (has effect only if 'animated' prop is set)"""
        return self._props.get("transition-next")

    @ui_transition_next.setter
    def ui_transition_next(self, value):
        self._set_prop("transition-next", value)

    @property
    def ui_model_value(self):
        """Model of the component defining the current panel's name; If a Number is used, it does not define the panel's index, but rather the panel's name which can also be an Integer; Either use this property (along with a listener for 'update:model-value' event) OR use the v-model directive."""
        return self._props.get("model-value")

    @ui_model_value.setter
    def ui_model_value(self, value):
        self._set_prop("model-value", value)

    @property
    def ui_keep_alive(self):
        """Equivalent to using Vue's native <keep-alive> component on the content"""
        return self._props.get("keep-alive")

    @ui_keep_alive.setter
    def ui_keep_alive(self, value):
        self._set_prop("keep-alive", value)

    @property
    def ui_keep_alive_include(self):
        """Equivalent to using Vue's native include prop for <keep-alive>; Values must be valid Vue component names"""
        return self._props.get("keep-alive-include")

    @ui_keep_alive_include.setter
    def ui_keep_alive_include(self, value):
        self._set_prop("keep-alive-include", value)

    @property
    def ui_keep_alive_exclude(self):
        """Equivalent to using Vue's native exclude prop for <keep-alive>; Values must be valid Vue component names"""
        return self._props.get("keep-alive-exclude")

    @ui_keep_alive_exclude.setter
    def ui_keep_alive_exclude(self, value):
        self._set_prop("keep-alive-exclude", value)

    @property
    def ui_keep_alive_max(self):
        """Equivalent to using Vue's native max prop for <keep-alive>"""
        return self._props.get("keep-alive-max")

    @ui_keep_alive_max.setter
    def ui_keep_alive_max(self, value):
        self._set_prop("keep-alive-max", value)

    @property
    def ui_animated(self):
        """Enable transitions between panel (also see 'transition-prev' and 'transition-next' props)"""
        return self._props.get("animated")

    @ui_animated.setter
    def ui_animated(self, value):
        self._set_prop("animated", value)

    @property
    def ui_infinite(self):
        """Makes component appear as infinite (when reaching last panel, next one will become the first one)"""
        return self._props.get("infinite")

    @ui_infinite.setter
    def ui_infinite(self, value):
        self._set_prop("infinite", value)

    @property
    def ui_swipeable(self):
        """Enable swipe events (may interfere with content's touch/mouse events)"""
        return self._props.get("swipeable")

    @ui_swipeable.setter
    def ui_swipeable(self, value):
        self._set_prop("swipeable", value)

    @property
    def ui_vertical(self):
        """Default transitions and swipe actions will be on the vertical axis"""
        return self._props.get("vertical")

    @ui_vertical.setter
    def ui_vertical(self, value):
        self._set_prop("vertical", value)

    @property
    def ui_transition_duration(self):
        """Transition duration (in milliseconds, without unit)"""
        return self._props.get("transition-duration")

    @ui_transition_duration.setter
    def ui_transition_duration(self, value):
        self._set_prop("transition-duration", value)

    @property
    def ui_fullscreen(self):
        """Fullscreen mode"""
        return self._props.get("fullscreen")

    @ui_fullscreen.setter
    def ui_fullscreen(self, value):
        self._set_prop("fullscreen", value)

    @property
    def ui_no_route_fullscreen_exit(self):
        """Changing route app won't exit fullscreen"""
        return self._props.get("no-route-fullscreen-exit")

    @ui_no_route_fullscreen_exit.setter
    def ui_no_route_fullscreen_exit(self, value):
        self._set_prop("no-route-fullscreen-exit", value)

    @property
    def ui_slot_control(self):
        """Slot specific for QCarouselControl"""
        return self.ui_slots.get("control", [])

    @ui_slot_control.setter
    def ui_slot_control(self, value):
        self._set_slot("control", value)

    @property
    def ui_slot_navigation_icon(self):
        """Slot for navigation icon/btn; Suggestion: QBtn"""
        return self.ui_slots.get("navigation-icon", [])

    @ui_slot_navigation_icon.setter
    def ui_slot_navigation_icon(self, value):
        self._set_slot("navigation-icon", value)

    def on_before_transition(self, handler: Callable, arg: object = None):
        """
        Emitted before transitioning to a new panel

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("before-transition", handler, arg)

    def on_fullscreen(self, handler: Callable, arg: object = None):
        """
        Emitted when fullscreen state changes

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("fullscreen", handler, arg)

    def on_transition(self, handler: Callable, arg: object = None):
        """
        Emitted after component transitioned to a new panel

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("transition", handler, arg)

    def on_update_fullscreen(self, handler: Callable, arg: object = None):
        """
        Used by Vue on 'v-model:fullscreen' prop for updating its value

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("update:fullscreen", handler, arg)

    def on_update_model_value(self, handler: Callable, arg: object = None):
        """
        Emitted when the component changes the model; This event isn't fired if the model is changed externally; Is also used by v-model

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("update:model-value", handler, arg)

    def ui_exitFullscreen(self):
        """Leave the fullscreen view"""
        self._js_call_method("exitFullscreen")

    def ui_goTo(self, ui_panelName):
        """Go to specific panel"""
        kwargs = {}
        if ui_panelName is not None:
            kwargs["panelName"] = ui_panelName
        self._js_call_method("goTo", [kwargs])

    def ui_next(self):
        """Go to next panel"""
        self._js_call_method("next")

    def ui_previous(self):
        """Go to previous panel"""
        self._js_call_method("previous")

    def ui_setFullscreen(self):
        """Enter the fullscreen view"""
        self._js_call_method("setFullscreen")

    def ui_toggleFullscreen(self):
        """Toggle the view to be fullscreen or not fullscreen"""
        self._js_call_method("toggleFullscreen")

    def _get_js_methods(self):
        return [
            "exitFullscreen",
            "goTo",
            "next",
            "previous",
            "setFullscreen",
            "toggleFullscreen",
        ]


class QCarouselSlide(Component):
    """
    Quasar Component: `QCarouselSlide <https://v2.quasar.dev/vue-components/carousel>`__

    :param ui_name: Panel name
    :param ui_img_src: URL pointing to a slide background image (use public folder)
    :param ui_disable:
    """

    def __init__(
        self,
        *children,
        ui_name: Any | None = None,
        ui_img_src: str | None = None,
        ui_disable: Any | None = None,
        **kwargs,
    ):
        super().__init__("QCarouselSlide", *children, **kwargs)
        if ui_name is not None:
            self._props["name"] = ui_name
        if ui_img_src is not None:
            self._props["img-src"] = ui_img_src
        if ui_disable is not None:
            self._props["disable"] = ui_disable

    @property
    def ui_name(self):
        """Panel name"""
        return self._props.get("name")

    @ui_name.setter
    def ui_name(self, value):
        self._set_prop("name", value)

    @property
    def ui_img_src(self):
        """URL pointing to a slide background image (use public folder)"""
        return self._props.get("img-src")

    @ui_img_src.setter
    def ui_img_src(self, value):
        self._set_prop("img-src", value)

    @property
    def ui_disable(self):
        return self._props.get("disable")

    @ui_disable.setter
    def ui_disable(self, value):
        self._set_prop("disable", value)

    def _get_js_methods(self):
        return []


class QCarouselControl(Component):
    """
    Quasar Component: `QCarouselControl <https://v2.quasar.dev/vue-components/carousel>`__

    :param ui_position: Side/corner to stick to
    :param ui_offset: An array of two numbers to offset the component horizontally and vertically (in pixels)
    """

    def __init__(
        self,
        *children,
        ui_position: str | None = None,
        ui_offset: list | None = None,
        **kwargs,
    ):
        super().__init__("QCarouselControl", *children, **kwargs)
        if ui_position is not None:
            self._props["position"] = ui_position
        if ui_offset is not None:
            self._props["offset"] = ui_offset

    @property
    def ui_position(self):
        """Side/corner to stick to"""
        return self._props.get("position")

    @ui_position.setter
    def ui_position(self, value):
        self._set_prop("position", value)

    @property
    def ui_offset(self):
        """An array of two numbers to offset the component horizontally and vertically (in pixels)"""
        return self._props.get("offset")

    @ui_offset.setter
    def ui_offset(self, value):
        self._set_prop("offset", value)

    def _get_js_methods(self):
        return []


class QChatMessage(Component):
    """
    Quasar Component: `QChatMessage <https://v2.quasar.dev/vue-components/chat>`__

    :param ui_sent: Render as a sent message (so from current user)
    :param ui_label: Renders a label header/section only
    :param ui_bg_color: Color name (from the Quasar Color Palette) for chat bubble background
    :param ui_text_color: Color name (from the Quasar Color Palette) for chat bubble text
    :param ui_name: Author's name
    :param ui_avatar: URL to the avatar image of the author
    :param ui_text: Array of strings that are the message body. Strings are not sanitized (see details in docs)
    :param ui_stamp: Creation timestamp
    :param ui_size: 1-12 out of 12 (same as col-\\*)
    :param ui_label_html: Render the label as HTML; This can lead to XSS attacks so make sure that you sanitize the message first
    :param ui_name_html: Render the name as HTML; This can lead to XSS attacks so make sure that you sanitize the message first
    :param ui_text_html: Render the text as HTML; This can lead to XSS attacks so make sure that you sanitize the message first
    :param ui_stamp_html: Render the stamp as HTML; This can lead to XSS attacks so make sure that you sanitize the message first
    """

    def __init__(
        self,
        *children,
        ui_sent: bool | None = None,
        ui_label: str | None = None,
        ui_bg_color: Any | None = None,
        ui_text_color: Any | None = None,
        ui_name: str | None = None,
        ui_avatar: str | None = None,
        ui_text: list | None = None,
        ui_stamp: str | None = None,
        ui_size: str | None = None,
        ui_label_html: Any | None = None,
        ui_name_html: Any | None = None,
        ui_text_html: Any | None = None,
        ui_stamp_html: Any | None = None,
        **kwargs,
    ):
        super().__init__("QChatMessage", *children, **kwargs)
        if ui_sent is not None:
            self._props["sent"] = ui_sent
        if ui_label is not None:
            self._props["label"] = ui_label
        if ui_bg_color is not None:
            self._props["bg-color"] = ui_bg_color
        if ui_text_color is not None:
            self._props["text-color"] = ui_text_color
        if ui_name is not None:
            self._props["name"] = ui_name
        if ui_avatar is not None:
            self._props["avatar"] = ui_avatar
        if ui_text is not None:
            self._props["text"] = ui_text
        if ui_stamp is not None:
            self._props["stamp"] = ui_stamp
        if ui_size is not None:
            self._props["size"] = ui_size
        if ui_label_html is not None:
            self._props["label-html"] = ui_label_html
        if ui_name_html is not None:
            self._props["name-html"] = ui_name_html
        if ui_text_html is not None:
            self._props["text-html"] = ui_text_html
        if ui_stamp_html is not None:
            self._props["stamp-html"] = ui_stamp_html

    @property
    def ui_sent(self):
        """Render as a sent message (so from current user)"""
        return self._props.get("sent")

    @ui_sent.setter
    def ui_sent(self, value):
        self._set_prop("sent", value)

    @property
    def ui_label(self):
        """Renders a label header/section only"""
        return self._props.get("label")

    @ui_label.setter
    def ui_label(self, value):
        self._set_prop("label", value)

    @property
    def ui_bg_color(self):
        """Color name (from the Quasar Color Palette) for chat bubble background"""
        return self._props.get("bg-color")

    @ui_bg_color.setter
    def ui_bg_color(self, value):
        self._set_prop("bg-color", value)

    @property
    def ui_text_color(self):
        """Color name (from the Quasar Color Palette) for chat bubble text"""
        return self._props.get("text-color")

    @ui_text_color.setter
    def ui_text_color(self, value):
        self._set_prop("text-color", value)

    @property
    def ui_name(self):
        """Author's name"""
        return self._props.get("name")

    @ui_name.setter
    def ui_name(self, value):
        self._set_prop("name", value)

    @property
    def ui_avatar(self):
        """URL to the avatar image of the author"""
        return self._props.get("avatar")

    @ui_avatar.setter
    def ui_avatar(self, value):
        self._set_prop("avatar", value)

    @property
    def ui_text(self):
        """Array of strings that are the message body. Strings are not sanitized (see details in docs)"""
        return self._props.get("text")

    @ui_text.setter
    def ui_text(self, value):
        self._set_prop("text", value)

    @property
    def ui_stamp(self):
        """Creation timestamp"""
        return self._props.get("stamp")

    @ui_stamp.setter
    def ui_stamp(self, value):
        self._set_prop("stamp", value)

    @property
    def ui_size(self):
        """1-12 out of 12 (same as col-\\*)"""
        return self._props.get("size")

    @ui_size.setter
    def ui_size(self, value):
        self._set_prop("size", value)

    @property
    def ui_label_html(self):
        """Render the label as HTML; This can lead to XSS attacks so make sure that you sanitize the message first"""
        return self._props.get("label-html")

    @ui_label_html.setter
    def ui_label_html(self, value):
        self._set_prop("label-html", value)

    @property
    def ui_name_html(self):
        """Render the name as HTML; This can lead to XSS attacks so make sure that you sanitize the message first"""
        return self._props.get("name-html")

    @ui_name_html.setter
    def ui_name_html(self, value):
        self._set_prop("name-html", value)

    @property
    def ui_text_html(self):
        """Render the text as HTML; This can lead to XSS attacks so make sure that you sanitize the message first"""
        return self._props.get("text-html")

    @ui_text_html.setter
    def ui_text_html(self, value):
        self._set_prop("text-html", value)

    @property
    def ui_stamp_html(self):
        """Render the stamp as HTML; This can lead to XSS attacks so make sure that you sanitize the message first"""
        return self._props.get("stamp-html")

    @ui_stamp_html.setter
    def ui_stamp_html(self, value):
        self._set_prop("stamp-html", value)

    @property
    def ui_slot_avatar(self):
        """Slot for avatar; Suggestion: QAvatar, img"""
        return self.ui_slots.get("avatar", [])

    @ui_slot_avatar.setter
    def ui_slot_avatar(self, value):
        self._set_slot("avatar", value)

    @property
    def ui_slot_label(self):
        """Slot for label; Overrides the 'label' prop"""
        return self.ui_slots.get("label", [])

    @ui_slot_label.setter
    def ui_slot_label(self, value):
        self._set_slot("label", value)

    @property
    def ui_slot_name(self):
        """Slot for name; Overrides the 'name' prop"""
        return self.ui_slots.get("name", [])

    @ui_slot_name.setter
    def ui_slot_name(self, value):
        self._set_slot("name", value)

    @property
    def ui_slot_stamp(self):
        """Slot for stamp; Overrides the 'stamp' prop"""
        return self.ui_slots.get("stamp", [])

    @ui_slot_stamp.setter
    def ui_slot_stamp(self, value):
        self._set_slot("stamp", value)

    def _get_js_methods(self):
        return []


class QCheckbox(Component):
    """
    Quasar Component: `QCheckbox <https://v2.quasar.dev/vue-components/checkbox>`__

    :param ui_checked_icon: The icon to be used when the model is truthy (instead of the default design)
    :param ui_unchecked_icon: The icon to be used when the toggle is falsy (instead of the default design)
    :param ui_indeterminate_icon: The icon to be used when the model is indeterminate (instead of the default design)
    :param ui_model_value:
    :param ui_val: Works when model ('value') is Array. It tells the component which value should add/remove when ticked/unticked
    :param ui_true_value: What model value should be considered as checked/ticked/on?
    :param ui_false_value: What model value should be considered as unchecked/unticked/off?
    :param ui_indeterminate_value: What model value should be considered as 'indeterminate'?
    :param ui_toggle_order: Determines toggle order of the two states ('t' stands for state of true, 'f' for state of false); If 'toggle-indeterminate' is true, then the order is: indet -> first state -> second state -> indet (and repeat), otherwise: indet -> first state -> second state -> first state -> second state -> ...
    :param ui_toggle_indeterminate: When user clicks/taps on the component, should we toggle through the indeterminate state too?
    :param ui_label: Label to display along the component (or use the default slot instead of this prop)
    :param ui_left_label: Label (if any specified) should be displayed on the left side of the component
    :param ui_color:
    :param ui_keep_color: Should the color (if specified any) be kept when the component is unticked/ off?
    :param ui_dark:
    :param ui_dense:
    :param ui_disable:
    :param ui_tabindex:
    :param ui_size: Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)
    :param ui_name: Used to specify the name of the control; Useful if dealing with forms submitted directly to a URL
    """

    def __init__(
        self,
        *children,
        ui_checked_icon: str | None = None,
        ui_unchecked_icon: str | None = None,
        ui_indeterminate_icon: str | None = None,
        ui_model_value: Any | list | None = None,
        ui_val: Any | None = None,
        ui_true_value: Any | None = None,
        ui_false_value: Any | None = None,
        ui_indeterminate_value: Any | None = None,
        ui_toggle_order: str | None = None,
        ui_toggle_indeterminate: bool | None = None,
        ui_label: str | None = None,
        ui_left_label: bool | None = None,
        ui_color: Any | None = None,
        ui_keep_color: bool | None = None,
        ui_dark: Any | None = None,
        ui_dense: Any | None = None,
        ui_disable: Any | None = None,
        ui_tabindex: Any | None = None,
        ui_size: str | None = None,
        ui_name: str | None = None,
        **kwargs,
    ):
        super().__init__("QCheckbox", *children, **kwargs)
        self.on("update:model-value", self.__update_model_value)

        if ui_checked_icon is not None:
            self._props["checked-icon"] = ui_checked_icon
        if ui_unchecked_icon is not None:
            self._props["unchecked-icon"] = ui_unchecked_icon
        if ui_indeterminate_icon is not None:
            self._props["indeterminate-icon"] = ui_indeterminate_icon
        if ui_model_value is not None:
            self._props["model-value"] = ui_model_value
        if ui_val is not None:
            self._props["val"] = ui_val
        if ui_true_value is not None:
            self._props["true-value"] = ui_true_value
        if ui_false_value is not None:
            self._props["false-value"] = ui_false_value
        if ui_indeterminate_value is not None:
            self._props["indeterminate-value"] = ui_indeterminate_value
        if ui_toggle_order is not None:
            self._props["toggle-order"] = ui_toggle_order
        if ui_toggle_indeterminate is not None:
            self._props["toggle-indeterminate"] = ui_toggle_indeterminate
        if ui_label is not None:
            self._props["label"] = ui_label
        if ui_left_label is not None:
            self._props["left-label"] = ui_left_label
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_keep_color is not None:
            self._props["keep-color"] = ui_keep_color
        if ui_dark is not None:
            self._props["dark"] = ui_dark
        if ui_dense is not None:
            self._props["dense"] = ui_dense
        if ui_disable is not None:
            self._props["disable"] = ui_disable
        if ui_tabindex is not None:
            self._props["tabindex"] = ui_tabindex
        if ui_size is not None:
            self._props["size"] = ui_size
        if ui_name is not None:
            self._props["name"] = ui_name

    def __update_model_value(self, event: Event):
        self._set_prop("model-value", event.value)

    @property
    def ui_checked_icon(self):
        """The icon to be used when the model is truthy (instead of the default design)"""
        return self._props.get("checked-icon")

    @ui_checked_icon.setter
    def ui_checked_icon(self, value):
        self._set_prop("checked-icon", value)

    @property
    def ui_unchecked_icon(self):
        """The icon to be used when the toggle is falsy (instead of the default design)"""
        return self._props.get("unchecked-icon")

    @ui_unchecked_icon.setter
    def ui_unchecked_icon(self, value):
        self._set_prop("unchecked-icon", value)

    @property
    def ui_indeterminate_icon(self):
        """The icon to be used when the model is indeterminate (instead of the default design)"""
        return self._props.get("indeterminate-icon")

    @ui_indeterminate_icon.setter
    def ui_indeterminate_icon(self, value):
        self._set_prop("indeterminate-icon", value)

    @property
    def ui_model_value(self):
        return self._props.get("model-value")

    @ui_model_value.setter
    def ui_model_value(self, value):
        self._set_prop("model-value", value)

    @property
    def ui_val(self):
        """Works when model ('value') is Array. It tells the component which value should add/remove when ticked/unticked"""
        return self._props.get("val")

    @ui_val.setter
    def ui_val(self, value):
        self._set_prop("val", value)

    @property
    def ui_true_value(self):
        """What model value should be considered as checked/ticked/on?"""
        return self._props.get("true-value")

    @ui_true_value.setter
    def ui_true_value(self, value):
        self._set_prop("true-value", value)

    @property
    def ui_false_value(self):
        """What model value should be considered as unchecked/unticked/off?"""
        return self._props.get("false-value")

    @ui_false_value.setter
    def ui_false_value(self, value):
        self._set_prop("false-value", value)

    @property
    def ui_indeterminate_value(self):
        """What model value should be considered as 'indeterminate'?"""
        return self._props.get("indeterminate-value")

    @ui_indeterminate_value.setter
    def ui_indeterminate_value(self, value):
        self._set_prop("indeterminate-value", value)

    @property
    def ui_toggle_order(self):
        """Determines toggle order of the two states ('t' stands for state of true, 'f' for state of false); If 'toggle-indeterminate' is true, then the order is: indet -> first state -> second state -> indet (and repeat), otherwise: indet -> first state -> second state -> first state -> second state -> ..."""
        return self._props.get("toggle-order")

    @ui_toggle_order.setter
    def ui_toggle_order(self, value):
        self._set_prop("toggle-order", value)

    @property
    def ui_toggle_indeterminate(self):
        """When user clicks/taps on the component, should we toggle through the indeterminate state too?"""
        return self._props.get("toggle-indeterminate")

    @ui_toggle_indeterminate.setter
    def ui_toggle_indeterminate(self, value):
        self._set_prop("toggle-indeterminate", value)

    @property
    def ui_label(self):
        """Label to display along the component (or use the default slot instead of this prop)"""
        return self._props.get("label")

    @ui_label.setter
    def ui_label(self, value):
        self._set_prop("label", value)

    @property
    def ui_left_label(self):
        """Label (if any specified) should be displayed on the left side of the component"""
        return self._props.get("left-label")

    @ui_left_label.setter
    def ui_left_label(self, value):
        self._set_prop("left-label", value)

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_keep_color(self):
        """Should the color (if specified any) be kept when the component is unticked/ off?"""
        return self._props.get("keep-color")

    @ui_keep_color.setter
    def ui_keep_color(self, value):
        self._set_prop("keep-color", value)

    @property
    def ui_dark(self):
        return self._props.get("dark")

    @ui_dark.setter
    def ui_dark(self, value):
        self._set_prop("dark", value)

    @property
    def ui_dense(self):
        return self._props.get("dense")

    @ui_dense.setter
    def ui_dense(self, value):
        self._set_prop("dense", value)

    @property
    def ui_disable(self):
        return self._props.get("disable")

    @ui_disable.setter
    def ui_disable(self, value):
        self._set_prop("disable", value)

    @property
    def ui_tabindex(self):
        return self._props.get("tabindex")

    @ui_tabindex.setter
    def ui_tabindex(self, value):
        self._set_prop("tabindex", value)

    @property
    def ui_size(self):
        """Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)"""
        return self._props.get("size")

    @ui_size.setter
    def ui_size(self, value):
        self._set_prop("size", value)

    @property
    def ui_name(self):
        """Used to specify the name of the control; Useful if dealing with forms submitted directly to a URL"""
        return self._props.get("name")

    @ui_name.setter
    def ui_name(self, value):
        self._set_prop("name", value)

    def on_update_model_value(self, handler: Callable, arg: object = None):
        """
        Emitted when the component needs to change the model; Is also used by v-model

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("update:model-value", handler, arg)

    def ui_toggle(self):
        """Toggle the state (of the model)"""
        self._js_call_method("toggle")

    def _get_js_methods(self):
        return ["toggle"]


class QChip(Component):
    """
    Quasar Component: `QChip <https://v2.quasar.dev/vue-components/chip>`__

    :param ui_dense:
    :param ui_size: QChip size name or a CSS unit including unit name
    :param ui_dark:
    :param ui_icon:
    :param ui_icon_right:
    :param ui_icon_remove:
    :param ui_icon_selected:
    :param ui_label: Chip's content as string; overrides default slot if specified
    :param ui_color:
    :param ui_text_color:
    :param ui_model_value: Model of the component determining if QChip should be rendered or not
    :param ui_selected: Model for QChip if it's selected or not
    :param ui_square: Sets a low value for border-radius instead of the default one, making it close to a square
    :param ui_outline: Display using the 'outline' design
    :param ui_clickable: Is QChip clickable? If it's the case, then it will add hover effects and emit 'click' events
    :param ui_removable: If set, then it displays a 'remove' icon that when clicked the QChip emits 'remove' event
    :param ui_ripple:
    :param ui_remove_aria_label: aria-label to be used on the remove icon
    :param ui_tabindex:
    :param ui_disable:
    """

    def __init__(
        self,
        *children,
        ui_dense: Any | None = None,
        ui_size: str | None = None,
        ui_dark: Any | None = None,
        ui_icon: Any | None = None,
        ui_icon_right: Any | None = None,
        ui_icon_remove: Any | None = None,
        ui_icon_selected: Any | None = None,
        ui_label: str | float | None = None,
        ui_color: Any | None = None,
        ui_text_color: Any | None = None,
        ui_model_value: bool | None = None,
        ui_selected: bool | None = None,
        ui_square: Any | None = None,
        ui_outline: bool | None = None,
        ui_clickable: bool | None = None,
        ui_removable: bool | None = None,
        ui_ripple: Any | None = None,
        ui_remove_aria_label: str | None = None,
        ui_tabindex: Any | None = None,
        ui_disable: Any | None = None,
        **kwargs,
    ):
        super().__init__("QChip", *children, **kwargs)
        self.on("update:model-value", self.__update_model_value)

        if ui_dense is not None:
            self._props["dense"] = ui_dense
        if ui_size is not None:
            self._props["size"] = ui_size
        if ui_dark is not None:
            self._props["dark"] = ui_dark
        if ui_icon is not None:
            self._props["icon"] = ui_icon
        if ui_icon_right is not None:
            self._props["icon-right"] = ui_icon_right
        if ui_icon_remove is not None:
            self._props["icon-remove"] = ui_icon_remove
        if ui_icon_selected is not None:
            self._props["icon-selected"] = ui_icon_selected
        if ui_label is not None:
            self._props["label"] = ui_label
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_text_color is not None:
            self._props["text-color"] = ui_text_color
        if ui_model_value is not None:
            self._props["model-value"] = ui_model_value
        if ui_selected is not None:
            self._props["selected"] = ui_selected
        if ui_square is not None:
            self._props["square"] = ui_square
        if ui_outline is not None:
            self._props["outline"] = ui_outline
        if ui_clickable is not None:
            self._props["clickable"] = ui_clickable
        if ui_removable is not None:
            self._props["removable"] = ui_removable
        if ui_ripple is not None:
            self._props["ripple"] = ui_ripple
        if ui_remove_aria_label is not None:
            self._props["remove-aria-label"] = ui_remove_aria_label
        if ui_tabindex is not None:
            self._props["tabindex"] = ui_tabindex
        if ui_disable is not None:
            self._props["disable"] = ui_disable

    def __update_model_value(self, event: Event):
        self._set_prop("model-value", event.value)

    @property
    def ui_dense(self):
        return self._props.get("dense")

    @ui_dense.setter
    def ui_dense(self, value):
        self._set_prop("dense", value)

    @property
    def ui_size(self):
        """QChip size name or a CSS unit including unit name"""
        return self._props.get("size")

    @ui_size.setter
    def ui_size(self, value):
        self._set_prop("size", value)

    @property
    def ui_dark(self):
        return self._props.get("dark")

    @ui_dark.setter
    def ui_dark(self, value):
        self._set_prop("dark", value)

    @property
    def ui_icon(self):
        return self._props.get("icon")

    @ui_icon.setter
    def ui_icon(self, value):
        self._set_prop("icon", value)

    @property
    def ui_icon_right(self):
        return self._props.get("icon-right")

    @ui_icon_right.setter
    def ui_icon_right(self, value):
        self._set_prop("icon-right", value)

    @property
    def ui_icon_remove(self):
        return self._props.get("icon-remove")

    @ui_icon_remove.setter
    def ui_icon_remove(self, value):
        self._set_prop("icon-remove", value)

    @property
    def ui_icon_selected(self):
        return self._props.get("icon-selected")

    @ui_icon_selected.setter
    def ui_icon_selected(self, value):
        self._set_prop("icon-selected", value)

    @property
    def ui_label(self):
        """Chip's content as string; overrides default slot if specified"""
        return self._props.get("label")

    @ui_label.setter
    def ui_label(self, value):
        self._set_prop("label", value)

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_text_color(self):
        return self._props.get("text-color")

    @ui_text_color.setter
    def ui_text_color(self, value):
        self._set_prop("text-color", value)

    @property
    def ui_model_value(self):
        """Model of the component determining if QChip should be rendered or not"""
        return self._props.get("model-value")

    @ui_model_value.setter
    def ui_model_value(self, value):
        self._set_prop("model-value", value)

    @property
    def ui_selected(self):
        """Model for QChip if it's selected or not"""
        return self._props.get("selected")

    @ui_selected.setter
    def ui_selected(self, value):
        self._set_prop("selected", value)

    @property
    def ui_square(self):
        """Sets a low value for border-radius instead of the default one, making it close to a square"""
        return self._props.get("square")

    @ui_square.setter
    def ui_square(self, value):
        self._set_prop("square", value)

    @property
    def ui_outline(self):
        """Display using the 'outline' design"""
        return self._props.get("outline")

    @ui_outline.setter
    def ui_outline(self, value):
        self._set_prop("outline", value)

    @property
    def ui_clickable(self):
        """Is QChip clickable? If it's the case, then it will add hover effects and emit 'click' events"""
        return self._props.get("clickable")

    @ui_clickable.setter
    def ui_clickable(self, value):
        self._set_prop("clickable", value)

    @property
    def ui_removable(self):
        """If set, then it displays a 'remove' icon that when clicked the QChip emits 'remove' event"""
        return self._props.get("removable")

    @ui_removable.setter
    def ui_removable(self, value):
        self._set_prop("removable", value)

    @property
    def ui_ripple(self):
        return self._props.get("ripple")

    @ui_ripple.setter
    def ui_ripple(self, value):
        self._set_prop("ripple", value)

    @property
    def ui_remove_aria_label(self):
        """aria-label to be used on the remove icon"""
        return self._props.get("remove-aria-label")

    @ui_remove_aria_label.setter
    def ui_remove_aria_label(self, value):
        self._set_prop("remove-aria-label", value)

    @property
    def ui_tabindex(self):
        return self._props.get("tabindex")

    @ui_tabindex.setter
    def ui_tabindex(self, value):
        self._set_prop("tabindex", value)

    @property
    def ui_disable(self):
        return self._props.get("disable")

    @ui_disable.setter
    def ui_disable(self, value):
        self._set_prop("disable", value)

    def on_click(self, handler: Callable, arg: object = None):
        """
        Emitted on QChip click if 'clickable' property is set

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("click.stop", handler, arg)

    def on_remove(self, handler: Callable, arg: object = None):
        """
        Works along with 'value' and 'removable' prop. Emitted when toggling rendering state of the QChip

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("remove", handler, arg)

    def on_update_model_value(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("update:model-value", handler, arg)

    def on_update_selected(self, handler: Callable, arg: object = None):
        """
        Used by Vue on 'v-model:selected' for updating its value

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("update:selected", handler, arg)

    def _get_js_methods(self):
        return []


class QCircularProgress(Component):
    """
    Quasar Component: `QCircularProgress <https://v2.quasar.dev/vue-components/circular-progress>`__

    :param ui_value: Current progress (must be between min/max)
    :param ui_min: Minimum value defining 'no progress' (must be lower than 'max')
    :param ui_max: Maximum value defining 100% progress made (must be higher than 'min')
    :param ui_color: Color name for the arc progress from the Quasar Color Palette
    :param ui_center_color: Color name for the center part of the component from the Quasar Color Palette
    :param ui_track_color: Color name for the track of the component from the Quasar Color Palette
    :param ui_font_size: Size of text in CSS units, including unit name. Suggestion: use 'em' units to sync with component size
    :param ui_rounded: Rounding the arc of progress
    :param ui_thickness: Thickness of progress arc as a ratio (0.0 < x < 1.0) of component size
    :param ui_angle: Angle to rotate progress arc by
    :param ui_indeterminate: Put component into 'indeterminate' state; Ignores 'value' prop
    :param ui_show_value: Enables the default slot and uses it (if available), otherwise it displays the 'value' prop as text; Make sure the text has enough space to be displayed inside the component
    :param ui_reverse: Reverses the direction of progress; Only for determined state
    :param ui_instant_feedback: No animation when model changes
    :param ui_animation_speed:
    :param ui_size: Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)
    """

    def __init__(
        self,
        *children,
        ui_value: float | None = None,
        ui_min: float | None = None,
        ui_max: float | None = None,
        ui_color: Any | None = None,
        ui_center_color: Any | None = None,
        ui_track_color: Any | None = None,
        ui_font_size: str | None = None,
        ui_rounded: bool | None = None,
        ui_thickness: float | None = None,
        ui_angle: float | None = None,
        ui_indeterminate: bool | None = None,
        ui_show_value: bool | None = None,
        ui_reverse: bool | None = None,
        ui_instant_feedback: bool | None = None,
        ui_animation_speed: Any | None = None,
        ui_size: str | None = None,
        **kwargs,
    ):
        super().__init__("QCircularProgress", *children, **kwargs)
        if ui_value is not None:
            self._props["value"] = ui_value
        if ui_min is not None:
            self._props["min"] = ui_min
        if ui_max is not None:
            self._props["max"] = ui_max
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_center_color is not None:
            self._props["center-color"] = ui_center_color
        if ui_track_color is not None:
            self._props["track-color"] = ui_track_color
        if ui_font_size is not None:
            self._props["font-size"] = ui_font_size
        if ui_rounded is not None:
            self._props["rounded"] = ui_rounded
        if ui_thickness is not None:
            self._props["thickness"] = ui_thickness
        if ui_angle is not None:
            self._props["angle"] = ui_angle
        if ui_indeterminate is not None:
            self._props["indeterminate"] = ui_indeterminate
        if ui_show_value is not None:
            self._props["show-value"] = ui_show_value
        if ui_reverse is not None:
            self._props["reverse"] = ui_reverse
        if ui_instant_feedback is not None:
            self._props["instant-feedback"] = ui_instant_feedback
        if ui_animation_speed is not None:
            self._props["animation-speed"] = ui_animation_speed
        if ui_size is not None:
            self._props["size"] = ui_size

    @property
    def ui_value(self):
        """Current progress (must be between min/max)"""
        return self._props.get("value")

    @ui_value.setter
    def ui_value(self, value):
        self._set_prop("value", value)

    @property
    def ui_min(self):
        """Minimum value defining 'no progress' (must be lower than 'max')"""
        return self._props.get("min")

    @ui_min.setter
    def ui_min(self, value):
        self._set_prop("min", value)

    @property
    def ui_max(self):
        """Maximum value defining 100% progress made (must be higher than 'min')"""
        return self._props.get("max")

    @ui_max.setter
    def ui_max(self, value):
        self._set_prop("max", value)

    @property
    def ui_color(self):
        """Color name for the arc progress from the Quasar Color Palette"""
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_center_color(self):
        """Color name for the center part of the component from the Quasar Color Palette"""
        return self._props.get("center-color")

    @ui_center_color.setter
    def ui_center_color(self, value):
        self._set_prop("center-color", value)

    @property
    def ui_track_color(self):
        """Color name for the track of the component from the Quasar Color Palette"""
        return self._props.get("track-color")

    @ui_track_color.setter
    def ui_track_color(self, value):
        self._set_prop("track-color", value)

    @property
    def ui_font_size(self):
        """Size of text in CSS units, including unit name. Suggestion: use 'em' units to sync with component size"""
        return self._props.get("font-size")

    @ui_font_size.setter
    def ui_font_size(self, value):
        self._set_prop("font-size", value)

    @property
    def ui_rounded(self):
        """Rounding the arc of progress"""
        return self._props.get("rounded")

    @ui_rounded.setter
    def ui_rounded(self, value):
        self._set_prop("rounded", value)

    @property
    def ui_thickness(self):
        """Thickness of progress arc as a ratio (0.0 < x < 1.0) of component size"""
        return self._props.get("thickness")

    @ui_thickness.setter
    def ui_thickness(self, value):
        self._set_prop("thickness", value)

    @property
    def ui_angle(self):
        """Angle to rotate progress arc by"""
        return self._props.get("angle")

    @ui_angle.setter
    def ui_angle(self, value):
        self._set_prop("angle", value)

    @property
    def ui_indeterminate(self):
        """Put component into 'indeterminate' state; Ignores 'value' prop"""
        return self._props.get("indeterminate")

    @ui_indeterminate.setter
    def ui_indeterminate(self, value):
        self._set_prop("indeterminate", value)

    @property
    def ui_show_value(self):
        """Enables the default slot and uses it (if available), otherwise it displays the 'value' prop as text; Make sure the text has enough space to be displayed inside the component"""
        return self._props.get("show-value")

    @ui_show_value.setter
    def ui_show_value(self, value):
        self._set_prop("show-value", value)

    @property
    def ui_reverse(self):
        """Reverses the direction of progress; Only for determined state"""
        return self._props.get("reverse")

    @ui_reverse.setter
    def ui_reverse(self, value):
        self._set_prop("reverse", value)

    @property
    def ui_instant_feedback(self):
        """No animation when model changes"""
        return self._props.get("instant-feedback")

    @ui_instant_feedback.setter
    def ui_instant_feedback(self, value):
        self._set_prop("instant-feedback", value)

    @property
    def ui_animation_speed(self):
        return self._props.get("animation-speed")

    @ui_animation_speed.setter
    def ui_animation_speed(self, value):
        self._set_prop("animation-speed", value)

    @property
    def ui_size(self):
        """Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)"""
        return self._props.get("size")

    @ui_size.setter
    def ui_size(self, value):
        self._set_prop("size", value)

    @property
    def ui_slot_internal(self):
        """Used by QKnob internally"""
        return self.ui_slots.get("internal", [])

    @ui_slot_internal.setter
    def ui_slot_internal(self, value):
        self._set_slot("internal", value)

    def _get_js_methods(self):
        return []


class QColor(Component):
    """
    Quasar Component: `QColor <https://v2.quasar.dev/vue-components/color-picker>`__

    :param ui_model_value:
    :param ui_default_value: The default value to show when the model doesn't have one
    :param ui_default_view: The default view of the picker
    :param ui_format_model: Forces a certain model format upon the model
    :param ui_palette: Use a custom palette of colors for the palette tab
    :param ui_square:
    :param ui_flat:
    :param ui_bordered:
    :param ui_no_header: Do not render header
    :param ui_no_header_tabs: Do not render header tabs (only the input)
    :param ui_no_footer: Do not render footer; Useful when you want a specific view ('default-view' prop) and don't want the user to be able to switch it
    :param ui_disable:
    :param ui_readonly:
    :param ui_dark:
    :param ui_name: Used to specify the name of the control; Useful if dealing with forms submitted directly to a URL
    """

    def __init__(
        self,
        *children,
        ui_model_value: str | None | Any = None,
        ui_default_value: str | None = None,
        ui_default_view: str | None = None,
        ui_format_model: str | None = None,
        ui_palette: list | None = None,
        ui_square: Any | None = None,
        ui_flat: Any | None = None,
        ui_bordered: Any | None = None,
        ui_no_header: bool | None = None,
        ui_no_header_tabs: bool | None = None,
        ui_no_footer: bool | None = None,
        ui_disable: Any | None = None,
        ui_readonly: Any | None = None,
        ui_dark: Any | None = None,
        ui_name: str | None = None,
        **kwargs,
    ):
        super().__init__("QColor", *children, **kwargs)
        self.on("update:model-value", self.__update_model_value)

        if ui_model_value is not None:
            self._props["model-value"] = ui_model_value
        if ui_default_value is not None:
            self._props["default-value"] = ui_default_value
        if ui_default_view is not None:
            self._props["default-view"] = ui_default_view
        if ui_format_model is not None:
            self._props["format-model"] = ui_format_model
        if ui_palette is not None:
            self._props["palette"] = ui_palette
        if ui_square is not None:
            self._props["square"] = ui_square
        if ui_flat is not None:
            self._props["flat"] = ui_flat
        if ui_bordered is not None:
            self._props["bordered"] = ui_bordered
        if ui_no_header is not None:
            self._props["no-header"] = ui_no_header
        if ui_no_header_tabs is not None:
            self._props["no-header-tabs"] = ui_no_header_tabs
        if ui_no_footer is not None:
            self._props["no-footer"] = ui_no_footer
        if ui_disable is not None:
            self._props["disable"] = ui_disable
        if ui_readonly is not None:
            self._props["readonly"] = ui_readonly
        if ui_dark is not None:
            self._props["dark"] = ui_dark
        if ui_name is not None:
            self._props["name"] = ui_name

    def __update_model_value(self, event: Event):
        self._set_prop("model-value", event.value)

    @property
    def ui_model_value(self):
        return self._props.get("model-value")

    @ui_model_value.setter
    def ui_model_value(self, value):
        self._set_prop("model-value", value)

    @property
    def ui_default_value(self):
        """The default value to show when the model doesn't have one"""
        return self._props.get("default-value")

    @ui_default_value.setter
    def ui_default_value(self, value):
        self._set_prop("default-value", value)

    @property
    def ui_default_view(self):
        """The default view of the picker"""
        return self._props.get("default-view")

    @ui_default_view.setter
    def ui_default_view(self, value):
        self._set_prop("default-view", value)

    @property
    def ui_format_model(self):
        """Forces a certain model format upon the model"""
        return self._props.get("format-model")

    @ui_format_model.setter
    def ui_format_model(self, value):
        self._set_prop("format-model", value)

    @property
    def ui_palette(self):
        """Use a custom palette of colors for the palette tab"""
        return self._props.get("palette")

    @ui_palette.setter
    def ui_palette(self, value):
        self._set_prop("palette", value)

    @property
    def ui_square(self):
        return self._props.get("square")

    @ui_square.setter
    def ui_square(self, value):
        self._set_prop("square", value)

    @property
    def ui_flat(self):
        return self._props.get("flat")

    @ui_flat.setter
    def ui_flat(self, value):
        self._set_prop("flat", value)

    @property
    def ui_bordered(self):
        return self._props.get("bordered")

    @ui_bordered.setter
    def ui_bordered(self, value):
        self._set_prop("bordered", value)

    @property
    def ui_no_header(self):
        """Do not render header"""
        return self._props.get("no-header")

    @ui_no_header.setter
    def ui_no_header(self, value):
        self._set_prop("no-header", value)

    @property
    def ui_no_header_tabs(self):
        """Do not render header tabs (only the input)"""
        return self._props.get("no-header-tabs")

    @ui_no_header_tabs.setter
    def ui_no_header_tabs(self, value):
        self._set_prop("no-header-tabs", value)

    @property
    def ui_no_footer(self):
        """Do not render footer; Useful when you want a specific view ('default-view' prop) and don't want the user to be able to switch it"""
        return self._props.get("no-footer")

    @ui_no_footer.setter
    def ui_no_footer(self, value):
        self._set_prop("no-footer", value)

    @property
    def ui_disable(self):
        return self._props.get("disable")

    @ui_disable.setter
    def ui_disable(self, value):
        self._set_prop("disable", value)

    @property
    def ui_readonly(self):
        return self._props.get("readonly")

    @ui_readonly.setter
    def ui_readonly(self, value):
        self._set_prop("readonly", value)

    @property
    def ui_dark(self):
        return self._props.get("dark")

    @ui_dark.setter
    def ui_dark(self, value):
        self._set_prop("dark", value)

    @property
    def ui_name(self):
        """Used to specify the name of the control; Useful if dealing with forms submitted directly to a URL"""
        return self._props.get("name")

    @ui_name.setter
    def ui_name(self, value):
        self._set_prop("name", value)

    def on_change(self, handler: Callable, arg: object = None):
        """
        Emitted on lazy model value change (after user finishes selecting a color)

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("change", handler, arg)

    def on_update_model_value(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("update:model-value", handler, arg)

    def _get_js_methods(self):
        return []


class QDate(Component):
    """
    Quasar Component: `QDate <https://v2.quasar.dev/vue-components/date>`__

    :param ui_model_value: Date(s) of the component; Must be Array if using 'multiple' prop; Either use this property (along with a listener for 'update:model-value' event) OR use v-model directive
    :param ui_title: When specified, it overrides the default header title; Makes sense when not in 'minimal' mode
    :param ui_subtitle: When specified, it overrides the default header subtitle; Makes sense when not in 'minimal' mode
    :param ui_default_year_month: The default year and month to display (in YYYY/MM format) when model is unfilled (undefined or null); Please ensure it is within the navigation min/max year-month (if using them)
    :param ui_mask: Mask (formatting string) used for parsing and formatting value
    :param ui_default_view: The view which will be displayed by default
    :param ui_years_in_month_view: Show the years selector in months view
    :param ui_events: A list of events to highlight on the calendar; If using a function, it receives the date as a String and must return a Boolean (matches or not); If using a function then for best performance, reference it from your scope and do not define it inline
    :param ui_event_color: Color name (from the Quasar Color Palette); If using a function, it receives the date as a String and must return a String (color for the received date); If using a function then for best performance, reference it from your scope and do not define it inline
    :param ui_options: Optionally configure the days that are selectable; If using a function, it receives the date as a String and must return a Boolean (is date acceptable or not); If using a function then for best performance, reference it from your scope and do not define it inline; Incompatible with 'range' prop
    :param ui_navigation_min_year_month: Lock user from navigating below a specific year+month (in YYYY/MM format); This prop is not used to correct the model; You might want to also use 'default-year-month' prop
    :param ui_navigation_max_year_month: Lock user from navigating above a specific year+month (in YYYY/MM format); This prop is not used to correct the model; You might want to also use 'default-year-month' prop
    :param ui_no_unset: Remove ability to unselect a date; It does not apply to selecting a range over already selected dates
    :param ui_first_day_of_week: Sets the day of the week that is considered the first day (0 - Sunday, 1 - Monday, ...); This day will show in the left-most column of the calendar
    :param ui_today_btn: Display a button that selects the current day
    :param ui_minimal: Don’t display the header
    :param ui_multiple: Allow multiple selection; Model must be Array
    :param ui_range: Allow range selection; Partial compatibility with 'options' prop: selected ranges might also include 'unselectable' days
    :param ui_emit_immediately: Emit model when user browses month and year too; ONLY for single selection (non-multiple, non-range)
    :param ui_landscape: Display the component in landscape mode
    :param ui_locale: Locale formatting options
    :param ui_calendar: Specify calendar type
    :param ui_color:
    :param ui_text_color:
    :param ui_dark:
    :param ui_square:
    :param ui_flat:
    :param ui_bordered:
    :param ui_readonly:
    :param ui_disable:
    :param ui_name: Used to specify the name of the control; Useful if dealing with forms submitted directly to a URL
    """

    def __init__(
        self,
        *children,
        ui_model_value: str | list | dict | None | Any = None,
        ui_title: str | None = None,
        ui_subtitle: str | None = None,
        ui_default_year_month: str | None = None,
        ui_mask: str | None = None,
        ui_default_view: str | None = None,
        ui_years_in_month_view: bool | None = None,
        ui_events: list | Callable | None = None,
        ui_event_color: str | Callable | None = None,
        ui_options: list | Callable | None = None,
        ui_navigation_min_year_month: str | None = None,
        ui_navigation_max_year_month: str | None = None,
        ui_no_unset: bool | None = None,
        ui_first_day_of_week: str | float | None = None,
        ui_today_btn: bool | None = None,
        ui_minimal: bool | None = None,
        ui_multiple: bool | None = None,
        ui_range: bool | None = None,
        ui_emit_immediately: bool | None = None,
        ui_landscape: bool | None = None,
        ui_locale: dict | None = None,
        ui_calendar: str | None = None,
        ui_color: Any | None = None,
        ui_text_color: Any | None = None,
        ui_dark: Any | None = None,
        ui_square: Any | None = None,
        ui_flat: Any | None = None,
        ui_bordered: Any | None = None,
        ui_readonly: Any | None = None,
        ui_disable: Any | None = None,
        ui_name: str | None = None,
        **kwargs,
    ):
        super().__init__("QDate", *children, **kwargs)
        self.on("update:model-value", self.__update_model_value)

        if ui_model_value is not None:
            self._props["model-value"] = ui_model_value
        if ui_title is not None:
            self._props["title"] = ui_title
        if ui_subtitle is not None:
            self._props["subtitle"] = ui_subtitle
        if ui_default_year_month is not None:
            self._props["default-year-month"] = ui_default_year_month
        if ui_mask is not None:
            self._props["mask"] = ui_mask
        if ui_default_view is not None:
            self._props["default-view"] = ui_default_view
        if ui_years_in_month_view is not None:
            self._props["years-in-month-view"] = ui_years_in_month_view
        if ui_events is not None:
            self._props["events"] = ui_events
        if ui_event_color is not None:
            self._props["event-color"] = ui_event_color
        if ui_options is not None:
            self._props["options"] = ui_options
        if ui_navigation_min_year_month is not None:
            self._props["navigation-min-year-month"] = (
                ui_navigation_min_year_month
            )
        if ui_navigation_max_year_month is not None:
            self._props["navigation-max-year-month"] = (
                ui_navigation_max_year_month
            )
        if ui_no_unset is not None:
            self._props["no-unset"] = ui_no_unset
        if ui_first_day_of_week is not None:
            self._props["first-day-of-week"] = ui_first_day_of_week
        if ui_today_btn is not None:
            self._props["today-btn"] = ui_today_btn
        if ui_minimal is not None:
            self._props["minimal"] = ui_minimal
        if ui_multiple is not None:
            self._props["multiple"] = ui_multiple
        if ui_range is not None:
            self._props["range"] = ui_range
        if ui_emit_immediately is not None:
            self._props["emit-immediately"] = ui_emit_immediately
        if ui_landscape is not None:
            self._props["landscape"] = ui_landscape
        if ui_locale is not None:
            self._props["locale"] = ui_locale
        if ui_calendar is not None:
            self._props["calendar"] = ui_calendar
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_text_color is not None:
            self._props["text-color"] = ui_text_color
        if ui_dark is not None:
            self._props["dark"] = ui_dark
        if ui_square is not None:
            self._props["square"] = ui_square
        if ui_flat is not None:
            self._props["flat"] = ui_flat
        if ui_bordered is not None:
            self._props["bordered"] = ui_bordered
        if ui_readonly is not None:
            self._props["readonly"] = ui_readonly
        if ui_disable is not None:
            self._props["disable"] = ui_disable
        if ui_name is not None:
            self._props["name"] = ui_name

    def __update_model_value(self, event: Event):
        self._set_prop("model-value", event.value)

    @property
    def ui_model_value(self):
        """Date(s) of the component; Must be Array if using 'multiple' prop; Either use this property (along with a listener for 'update:model-value' event) OR use v-model directive"""
        return self._props.get("model-value")

    @ui_model_value.setter
    def ui_model_value(self, value):
        self._set_prop("model-value", value)

    @property
    def ui_title(self):
        """When specified, it overrides the default header title; Makes sense when not in 'minimal' mode"""
        return self._props.get("title")

    @ui_title.setter
    def ui_title(self, value):
        self._set_prop("title", value)

    @property
    def ui_subtitle(self):
        """When specified, it overrides the default header subtitle; Makes sense when not in 'minimal' mode"""
        return self._props.get("subtitle")

    @ui_subtitle.setter
    def ui_subtitle(self, value):
        self._set_prop("subtitle", value)

    @property
    def ui_default_year_month(self):
        """The default year and month to display (in YYYY/MM format) when model is unfilled (undefined or null); Please ensure it is within the navigation min/max year-month (if using them)"""
        return self._props.get("default-year-month")

    @ui_default_year_month.setter
    def ui_default_year_month(self, value):
        self._set_prop("default-year-month", value)

    @property
    def ui_mask(self):
        """Mask (formatting string) used for parsing and formatting value"""
        return self._props.get("mask")

    @ui_mask.setter
    def ui_mask(self, value):
        self._set_prop("mask", value)

    @property
    def ui_default_view(self):
        """The view which will be displayed by default"""
        return self._props.get("default-view")

    @ui_default_view.setter
    def ui_default_view(self, value):
        self._set_prop("default-view", value)

    @property
    def ui_years_in_month_view(self):
        """Show the years selector in months view"""
        return self._props.get("years-in-month-view")

    @ui_years_in_month_view.setter
    def ui_years_in_month_view(self, value):
        self._set_prop("years-in-month-view", value)

    @property
    def ui_events(self):
        """A list of events to highlight on the calendar; If using a function, it receives the date as a String and must return a Boolean (matches or not); If using a function then for best performance, reference it from your scope and do not define it inline"""
        return self._props.get("events")

    @ui_events.setter
    def ui_events(self, value):
        self._set_prop("events", value)

    @property
    def ui_event_color(self):
        """Color name (from the Quasar Color Palette); If using a function, it receives the date as a String and must return a String (color for the received date); If using a function then for best performance, reference it from your scope and do not define it inline"""
        return self._props.get("event-color")

    @ui_event_color.setter
    def ui_event_color(self, value):
        self._set_prop("event-color", value)

    @property
    def ui_options(self):
        """Optionally configure the days that are selectable; If using a function, it receives the date as a String and must return a Boolean (is date acceptable or not); If using a function then for best performance, reference it from your scope and do not define it inline; Incompatible with 'range' prop"""
        return self._props.get("options")

    @ui_options.setter
    def ui_options(self, value):
        self._set_prop("options", value)

    @property
    def ui_navigation_min_year_month(self):
        """Lock user from navigating below a specific year+month (in YYYY/MM format); This prop is not used to correct the model; You might want to also use 'default-year-month' prop"""
        return self._props.get("navigation-min-year-month")

    @ui_navigation_min_year_month.setter
    def ui_navigation_min_year_month(self, value):
        self._set_prop("navigation-min-year-month", value)

    @property
    def ui_navigation_max_year_month(self):
        """Lock user from navigating above a specific year+month (in YYYY/MM format); This prop is not used to correct the model; You might want to also use 'default-year-month' prop"""
        return self._props.get("navigation-max-year-month")

    @ui_navigation_max_year_month.setter
    def ui_navigation_max_year_month(self, value):
        self._set_prop("navigation-max-year-month", value)

    @property
    def ui_no_unset(self):
        """Remove ability to unselect a date; It does not apply to selecting a range over already selected dates"""
        return self._props.get("no-unset")

    @ui_no_unset.setter
    def ui_no_unset(self, value):
        self._set_prop("no-unset", value)

    @property
    def ui_first_day_of_week(self):
        """Sets the day of the week that is considered the first day (0 - Sunday, 1 - Monday, ...); This day will show in the left-most column of the calendar"""
        return self._props.get("first-day-of-week")

    @ui_first_day_of_week.setter
    def ui_first_day_of_week(self, value):
        self._set_prop("first-day-of-week", value)

    @property
    def ui_today_btn(self):
        """Display a button that selects the current day"""
        return self._props.get("today-btn")

    @ui_today_btn.setter
    def ui_today_btn(self, value):
        self._set_prop("today-btn", value)

    @property
    def ui_minimal(self):
        """Don’t display the header"""
        return self._props.get("minimal")

    @ui_minimal.setter
    def ui_minimal(self, value):
        self._set_prop("minimal", value)

    @property
    def ui_multiple(self):
        """Allow multiple selection; Model must be Array"""
        return self._props.get("multiple")

    @ui_multiple.setter
    def ui_multiple(self, value):
        self._set_prop("multiple", value)

    @property
    def ui_range(self):
        """Allow range selection; Partial compatibility with 'options' prop: selected ranges might also include 'unselectable' days"""
        return self._props.get("range")

    @ui_range.setter
    def ui_range(self, value):
        self._set_prop("range", value)

    @property
    def ui_emit_immediately(self):
        """Emit model when user browses month and year too; ONLY for single selection (non-multiple, non-range)"""
        return self._props.get("emit-immediately")

    @ui_emit_immediately.setter
    def ui_emit_immediately(self, value):
        self._set_prop("emit-immediately", value)

    @property
    def ui_landscape(self):
        """Display the component in landscape mode"""
        return self._props.get("landscape")

    @ui_landscape.setter
    def ui_landscape(self, value):
        self._set_prop("landscape", value)

    @property
    def ui_locale(self):
        """Locale formatting options"""
        return self._props.get("locale")

    @ui_locale.setter
    def ui_locale(self, value):
        self._set_prop("locale", value)

    @property
    def ui_calendar(self):
        """Specify calendar type"""
        return self._props.get("calendar")

    @ui_calendar.setter
    def ui_calendar(self, value):
        self._set_prop("calendar", value)

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_text_color(self):
        return self._props.get("text-color")

    @ui_text_color.setter
    def ui_text_color(self, value):
        self._set_prop("text-color", value)

    @property
    def ui_dark(self):
        return self._props.get("dark")

    @ui_dark.setter
    def ui_dark(self, value):
        self._set_prop("dark", value)

    @property
    def ui_square(self):
        return self._props.get("square")

    @ui_square.setter
    def ui_square(self, value):
        self._set_prop("square", value)

    @property
    def ui_flat(self):
        return self._props.get("flat")

    @ui_flat.setter
    def ui_flat(self, value):
        self._set_prop("flat", value)

    @property
    def ui_bordered(self):
        return self._props.get("bordered")

    @ui_bordered.setter
    def ui_bordered(self, value):
        self._set_prop("bordered", value)

    @property
    def ui_readonly(self):
        return self._props.get("readonly")

    @ui_readonly.setter
    def ui_readonly(self, value):
        self._set_prop("readonly", value)

    @property
    def ui_disable(self):
        return self._props.get("disable")

    @ui_disable.setter
    def ui_disable(self, value):
        self._set_prop("disable", value)

    @property
    def ui_name(self):
        """Used to specify the name of the control; Useful if dealing with forms submitted directly to a URL"""
        return self._props.get("name")

    @ui_name.setter
    def ui_name(self, value):
        self._set_prop("name", value)

    def on_navigation(self, handler: Callable, arg: object = None):
        """
        Emitted when user navigates to a different month or year (and even when the model changes from an outside source)

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("navigation", handler, arg)

    def on_range_end(self, handler: Callable, arg: object = None):
        """
        User has ended a range selection

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("range-end", handler, arg)

    def on_range_start(self, handler: Callable, arg: object = None):
        """
        User has started a range selection

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("range-start", handler, arg)

    def on_update_model_value(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("update:model-value", handler, arg)

    def ui_offsetCalendar(self, ui_type, ui_descending=None):
        """Increment or decrement calendar view's month or year"""
        kwargs = {}
        if ui_type is not None:
            kwargs["type"] = ui_type
        if ui_descending is not None:
            kwargs["descending"] = ui_descending
        self._js_call_method("offsetCalendar", [kwargs])

    def ui_setCalendarTo(self, ui_year=None, ui_month=None):
        """Change current year and month of the Calendar view; It gets corrected if using navigation-min/max-year-month and sets the current view to Calendar"""
        kwargs = {}
        if ui_year is not None:
            kwargs["year"] = ui_year
        if ui_month is not None:
            kwargs["month"] = ui_month
        self._js_call_method("setCalendarTo", [kwargs])

    def ui_setEditingRange(self, ui_from=None, ui_to=None):
        """Configure the current editing range"""
        kwargs = {}
        if ui_from is not None:
            kwargs["from"] = ui_from
        if ui_to is not None:
            kwargs["to"] = ui_to
        self._js_call_method("setEditingRange", [kwargs])

    def ui_setToday(self):
        """Change model to today"""
        self._js_call_method("setToday")

    def ui_setView(self, ui_view):
        """Change current view"""
        kwargs = {}
        if ui_view is not None:
            kwargs["view"] = ui_view
        self._js_call_method("setView", [kwargs])

    def _get_js_methods(self):
        return [
            "offsetCalendar",
            "setCalendarTo",
            "setEditingRange",
            "setToday",
            "setView",
        ]


class QDialog(Component):
    """
    Quasar Component: `QDialog <https://v2.quasar.dev/vue-components/dialog>`__

    :param ui_persistent: User cannot dismiss Dialog if clicking outside of it or hitting ESC key; Also, an app route change won't dismiss it
    :param ui_no_esc_dismiss: User cannot dismiss Dialog by hitting ESC key; No need to set it if 'persistent' prop is also set
    :param ui_no_backdrop_dismiss: User cannot dismiss Dialog by clicking outside of it; No need to set it if 'persistent' prop is also set
    :param ui_no_route_dismiss: Changing route app won't dismiss Dialog; No need to set it if 'persistent' prop is also set
    :param ui_auto_close: Any click/tap inside of the dialog will close it
    :param ui_seamless: Put Dialog into seamless mode; Does not use a backdrop so user is able to interact with the rest of the page too
    :param ui_backdrop_filter: Apply a backdrop filter; The value needs to be the same as in the CSS specs for backdrop-filter; The examples are not an exhaustive list
    :param ui_maximized: Put Dialog into maximized mode
    :param ui_full_width: Dialog will try to render with same width as the window
    :param ui_full_height: Dialog will try to render with same height as the window
    :param ui_position: Stick dialog to one of the sides (top, right, bottom or left)
    :param ui_square: Forces content to have squared borders
    :param ui_no_refocus: (Accessibility) When Dialog gets hidden, do not refocus on the DOM element that previously had focus
    :param ui_no_focus: (Accessibility) When Dialog gets shown, do not switch focus on it
    :param ui_no_shake: Do not shake up the Dialog to catch user's attention
    :param ui_allow_focus_outside: Allow elements outside of the Dialog to be focusable; By default, for accessibility reasons, QDialog does not allow outer focus
    :param ui_transition_show:
    :param ui_transition_hide:
    :param ui_model_value: Model of the component defining shown/hidden state; Either use this property (along with a listener for 'update:model-value' event) OR use v-model directive
    :param ui_transition_duration: Transition duration (in milliseconds, without unit)
    """

    def __init__(
        self,
        *children,
        ui_persistent: bool | None = None,
        ui_no_esc_dismiss: bool | None = None,
        ui_no_backdrop_dismiss: bool | None = None,
        ui_no_route_dismiss: bool | None = None,
        ui_auto_close: bool | None = None,
        ui_seamless: bool | None = None,
        ui_backdrop_filter: str | None = None,
        ui_maximized: bool | None = None,
        ui_full_width: bool | None = None,
        ui_full_height: bool | None = None,
        ui_position: str | None = None,
        ui_square: bool | None = None,
        ui_no_refocus: bool | None = None,
        ui_no_focus: bool | None = None,
        ui_no_shake: bool | None = None,
        ui_allow_focus_outside: bool | None = None,
        ui_transition_show: Any | None = None,
        ui_transition_hide: Any | None = None,
        ui_model_value: bool | None = None,
        ui_transition_duration: str | float | None = None,
        **kwargs,
    ):
        super().__init__("QDialog", *children, **kwargs)
        self.on("update:model-value", self.__update_model_value)

        if ui_persistent is not None:
            self._props["persistent"] = ui_persistent
        if ui_no_esc_dismiss is not None:
            self._props["no-esc-dismiss"] = ui_no_esc_dismiss
        if ui_no_backdrop_dismiss is not None:
            self._props["no-backdrop-dismiss"] = ui_no_backdrop_dismiss
        if ui_no_route_dismiss is not None:
            self._props["no-route-dismiss"] = ui_no_route_dismiss
        if ui_auto_close is not None:
            self._props["auto-close"] = ui_auto_close
        if ui_seamless is not None:
            self._props["seamless"] = ui_seamless
        if ui_backdrop_filter is not None:
            self._props["backdrop-filter"] = ui_backdrop_filter
        if ui_maximized is not None:
            self._props["maximized"] = ui_maximized
        if ui_full_width is not None:
            self._props["full-width"] = ui_full_width
        if ui_full_height is not None:
            self._props["full-height"] = ui_full_height
        if ui_position is not None:
            self._props["position"] = ui_position
        if ui_square is not None:
            self._props["square"] = ui_square
        if ui_no_refocus is not None:
            self._props["no-refocus"] = ui_no_refocus
        if ui_no_focus is not None:
            self._props["no-focus"] = ui_no_focus
        if ui_no_shake is not None:
            self._props["no-shake"] = ui_no_shake
        if ui_allow_focus_outside is not None:
            self._props["allow-focus-outside"] = ui_allow_focus_outside
        if ui_transition_show is not None:
            self._props["transition-show"] = ui_transition_show
        if ui_transition_hide is not None:
            self._props["transition-hide"] = ui_transition_hide
        if ui_model_value is not None:
            self._props["model-value"] = ui_model_value
        if ui_transition_duration is not None:
            self._props["transition-duration"] = ui_transition_duration

    def __update_model_value(self, event: Event):
        self._set_prop("model-value", event.value)

    @property
    def ui_persistent(self):
        """User cannot dismiss Dialog if clicking outside of it or hitting ESC key; Also, an app route change won't dismiss it"""
        return self._props.get("persistent")

    @ui_persistent.setter
    def ui_persistent(self, value):
        self._set_prop("persistent", value)

    @property
    def ui_no_esc_dismiss(self):
        """User cannot dismiss Dialog by hitting ESC key; No need to set it if 'persistent' prop is also set"""
        return self._props.get("no-esc-dismiss")

    @ui_no_esc_dismiss.setter
    def ui_no_esc_dismiss(self, value):
        self._set_prop("no-esc-dismiss", value)

    @property
    def ui_no_backdrop_dismiss(self):
        """User cannot dismiss Dialog by clicking outside of it; No need to set it if 'persistent' prop is also set"""
        return self._props.get("no-backdrop-dismiss")

    @ui_no_backdrop_dismiss.setter
    def ui_no_backdrop_dismiss(self, value):
        self._set_prop("no-backdrop-dismiss", value)

    @property
    def ui_no_route_dismiss(self):
        """Changing route app won't dismiss Dialog; No need to set it if 'persistent' prop is also set"""
        return self._props.get("no-route-dismiss")

    @ui_no_route_dismiss.setter
    def ui_no_route_dismiss(self, value):
        self._set_prop("no-route-dismiss", value)

    @property
    def ui_auto_close(self):
        """Any click/tap inside of the dialog will close it"""
        return self._props.get("auto-close")

    @ui_auto_close.setter
    def ui_auto_close(self, value):
        self._set_prop("auto-close", value)

    @property
    def ui_seamless(self):
        """Put Dialog into seamless mode; Does not use a backdrop so user is able to interact with the rest of the page too"""
        return self._props.get("seamless")

    @ui_seamless.setter
    def ui_seamless(self, value):
        self._set_prop("seamless", value)

    @property
    def ui_backdrop_filter(self):
        """Apply a backdrop filter; The value needs to be the same as in the CSS specs for backdrop-filter; The examples are not an exhaustive list"""
        return self._props.get("backdrop-filter")

    @ui_backdrop_filter.setter
    def ui_backdrop_filter(self, value):
        self._set_prop("backdrop-filter", value)

    @property
    def ui_maximized(self):
        """Put Dialog into maximized mode"""
        return self._props.get("maximized")

    @ui_maximized.setter
    def ui_maximized(self, value):
        self._set_prop("maximized", value)

    @property
    def ui_full_width(self):
        """Dialog will try to render with same width as the window"""
        return self._props.get("full-width")

    @ui_full_width.setter
    def ui_full_width(self, value):
        self._set_prop("full-width", value)

    @property
    def ui_full_height(self):
        """Dialog will try to render with same height as the window"""
        return self._props.get("full-height")

    @ui_full_height.setter
    def ui_full_height(self, value):
        self._set_prop("full-height", value)

    @property
    def ui_position(self):
        """Stick dialog to one of the sides (top, right, bottom or left)"""
        return self._props.get("position")

    @ui_position.setter
    def ui_position(self, value):
        self._set_prop("position", value)

    @property
    def ui_square(self):
        """Forces content to have squared borders"""
        return self._props.get("square")

    @ui_square.setter
    def ui_square(self, value):
        self._set_prop("square", value)

    @property
    def ui_no_refocus(self):
        """(Accessibility) When Dialog gets hidden, do not refocus on the DOM element that previously had focus"""
        return self._props.get("no-refocus")

    @ui_no_refocus.setter
    def ui_no_refocus(self, value):
        self._set_prop("no-refocus", value)

    @property
    def ui_no_focus(self):
        """(Accessibility) When Dialog gets shown, do not switch focus on it"""
        return self._props.get("no-focus")

    @ui_no_focus.setter
    def ui_no_focus(self, value):
        self._set_prop("no-focus", value)

    @property
    def ui_no_shake(self):
        """Do not shake up the Dialog to catch user's attention"""
        return self._props.get("no-shake")

    @ui_no_shake.setter
    def ui_no_shake(self, value):
        self._set_prop("no-shake", value)

    @property
    def ui_allow_focus_outside(self):
        """Allow elements outside of the Dialog to be focusable; By default, for accessibility reasons, QDialog does not allow outer focus"""
        return self._props.get("allow-focus-outside")

    @ui_allow_focus_outside.setter
    def ui_allow_focus_outside(self, value):
        self._set_prop("allow-focus-outside", value)

    @property
    def ui_transition_show(self):
        return self._props.get("transition-show")

    @ui_transition_show.setter
    def ui_transition_show(self, value):
        self._set_prop("transition-show", value)

    @property
    def ui_transition_hide(self):
        return self._props.get("transition-hide")

    @ui_transition_hide.setter
    def ui_transition_hide(self, value):
        self._set_prop("transition-hide", value)

    @property
    def ui_model_value(self):
        """Model of the component defining shown/hidden state; Either use this property (along with a listener for 'update:model-value' event) OR use v-model directive"""
        return self._props.get("model-value")

    @ui_model_value.setter
    def ui_model_value(self, value):
        self._set_prop("model-value", value)

    @property
    def ui_transition_duration(self):
        """Transition duration (in milliseconds, without unit)"""
        return self._props.get("transition-duration")

    @ui_transition_duration.setter
    def ui_transition_duration(self, value):
        self._set_prop("transition-duration", value)

    def on_before_hide(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("before-hide", handler, arg)

    def on_before_show(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("before-show", handler, arg)

    def on_click(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("click.stop", handler, arg)

    def on_escape_key(self, handler: Callable, arg: object = None):
        """
        Emitted when ESC key is pressed; Does not get emitted if Dialog is 'persistent' or it has 'no-esc-key' set

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("escape-key", handler, arg)

    def on_hide(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("hide", handler, arg)

    def on_shake(self, handler: Callable, arg: object = None):
        """
        Emitted when the Dialog shakes in order to catch user's attention, unless the 'no-shake' property is set

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("shake", handler, arg)

    def on_show(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("show", handler, arg)

    def on_update_model_value(self, handler: Callable, arg: object = None):
        """
        Emitted when showing/hidden state changes; Is also used by v-model

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("update:model-value", handler, arg)

    def ui_focus(self, ui_selector=None):
        """Focus dialog; if you have content with autofocus attribute, it will directly focus it"""
        kwargs = {}
        if ui_selector is not None:
            kwargs["selector"] = ui_selector
        self._js_call_method("focus", [kwargs])

    def ui_hide(self):
        self._js_call_method("hide")

    def ui_shake(self, ui_focusTarget=None):
        """Shakes dialog"""
        kwargs = {}
        if ui_focusTarget is not None:
            kwargs["focusTarget"] = ui_focusTarget
        self._js_call_method("shake", [kwargs])

    def ui_show(self):
        self._js_call_method("show")

    def ui_toggle(self):
        self._js_call_method("toggle")

    def _get_js_methods(self):
        return ["focus", "hide", "shake", "show", "toggle"]


class QDrawer(Component):
    """
    Quasar Component: `QDrawer <https://v2.quasar.dev/layout/drawer>`__

    :param ui_side: Side to attach to
    :param ui_overlay: Puts drawer into overlay mode (does not occupy space on screen, narrowing the page)
    :param ui_width: Width of drawer (in pixels)
    :param ui_mini: Puts drawer into mini mode
    :param ui_mini_width: Width of drawer (in pixels) when in mini mode
    :param ui_mini_to_overlay: Mini mode will expand as an overlay
    :param ui_no_mini_animation: Disables animation of the drawer when toggling mini mode
    :param ui_dark:
    :param ui_breakpoint: Breakpoint (in pixels) of layout width up to which mobile mode is used
    :param ui_behavior: Overrides the default dynamic mode into which the drawer is put on
    :param ui_bordered:
    :param ui_elevated: Adds a default shadow to the header
    :param ui_persistent: Prevents drawer from auto-closing when app's route changes; Also, an app route change won't hide it
    :param ui_show_if_above: Forces drawer to be shown on screen on initial render if the layout width is above breakpoint, regardless of v-model; This is the default behavior when SSR is taken over by client on initial render
    :param ui_no_swipe_open: Disables the default behavior where drawer can be swiped into view; Useful for iOS platforms where it might interfere with Safari's 'swipe to go to previous/next page' feature
    :param ui_no_swipe_close: Disables the default behavior where drawer can be swiped out of view (applies to drawer content only); Useful for iOS platforms where it might interfere with Safari's 'swipe to go to previous/next page' feature
    :param ui_no_swipe_backdrop: Disables the default behavior where drawer backdrop can be swiped
    :param ui_model_value: Model of the component defining shown/hidden state; Either use this property (along with a listener for 'update:model-value' event) OR use v-model directive
    """

    def __init__(
        self,
        *children,
        ui_side: str | None = None,
        ui_overlay: bool | None = None,
        ui_width: float | None = None,
        ui_mini: bool | None = None,
        ui_mini_width: float | None = None,
        ui_mini_to_overlay: bool | None = None,
        ui_no_mini_animation: bool | None = None,
        ui_dark: Any | None = None,
        ui_breakpoint: float | None = None,
        ui_behavior: str | None = None,
        ui_bordered: Any | None = None,
        ui_elevated: bool | None = None,
        ui_persistent: bool | None = None,
        ui_show_if_above: bool | None = None,
        ui_no_swipe_open: bool | None = None,
        ui_no_swipe_close: bool | None = None,
        ui_no_swipe_backdrop: bool | None = None,
        ui_model_value: bool | None = None,
        **kwargs,
    ):
        super().__init__("QDrawer", *children, **kwargs)
        self.on("update:model-value", self.__update_model_value)

        if ui_side is not None:
            self._props["side"] = ui_side
        if ui_overlay is not None:
            self._props["overlay"] = ui_overlay
        if ui_width is not None:
            self._props["width"] = ui_width
        if ui_mini is not None:
            self._props["mini"] = ui_mini
        if ui_mini_width is not None:
            self._props["mini-width"] = ui_mini_width
        if ui_mini_to_overlay is not None:
            self._props["mini-to-overlay"] = ui_mini_to_overlay
        if ui_no_mini_animation is not None:
            self._props["no-mini-animation"] = ui_no_mini_animation
        if ui_dark is not None:
            self._props["dark"] = ui_dark
        if ui_breakpoint is not None:
            self._props["breakpoint"] = ui_breakpoint
        if ui_behavior is not None:
            self._props["behavior"] = ui_behavior
        if ui_bordered is not None:
            self._props["bordered"] = ui_bordered
        if ui_elevated is not None:
            self._props["elevated"] = ui_elevated
        if ui_persistent is not None:
            self._props["persistent"] = ui_persistent
        if ui_show_if_above is not None:
            self._props["show-if-above"] = ui_show_if_above
        if ui_no_swipe_open is not None:
            self._props["no-swipe-open"] = ui_no_swipe_open
        if ui_no_swipe_close is not None:
            self._props["no-swipe-close"] = ui_no_swipe_close
        if ui_no_swipe_backdrop is not None:
            self._props["no-swipe-backdrop"] = ui_no_swipe_backdrop
        if ui_model_value is not None:
            self._props["model-value"] = ui_model_value

    def __update_model_value(self, event: Event):
        self._set_prop("model-value", event.value)

    @property
    def ui_side(self):
        """Side to attach to"""
        return self._props.get("side")

    @ui_side.setter
    def ui_side(self, value):
        self._set_prop("side", value)

    @property
    def ui_overlay(self):
        """Puts drawer into overlay mode (does not occupy space on screen, narrowing the page)"""
        return self._props.get("overlay")

    @ui_overlay.setter
    def ui_overlay(self, value):
        self._set_prop("overlay", value)

    @property
    def ui_width(self):
        """Width of drawer (in pixels)"""
        return self._props.get("width")

    @ui_width.setter
    def ui_width(self, value):
        self._set_prop("width", value)

    @property
    def ui_mini(self):
        """Puts drawer into mini mode"""
        return self._props.get("mini")

    @ui_mini.setter
    def ui_mini(self, value):
        self._set_prop("mini", value)

    @property
    def ui_mini_width(self):
        """Width of drawer (in pixels) when in mini mode"""
        return self._props.get("mini-width")

    @ui_mini_width.setter
    def ui_mini_width(self, value):
        self._set_prop("mini-width", value)

    @property
    def ui_mini_to_overlay(self):
        """Mini mode will expand as an overlay"""
        return self._props.get("mini-to-overlay")

    @ui_mini_to_overlay.setter
    def ui_mini_to_overlay(self, value):
        self._set_prop("mini-to-overlay", value)

    @property
    def ui_no_mini_animation(self):
        """Disables animation of the drawer when toggling mini mode"""
        return self._props.get("no-mini-animation")

    @ui_no_mini_animation.setter
    def ui_no_mini_animation(self, value):
        self._set_prop("no-mini-animation", value)

    @property
    def ui_dark(self):
        return self._props.get("dark")

    @ui_dark.setter
    def ui_dark(self, value):
        self._set_prop("dark", value)

    @property
    def ui_breakpoint(self):
        """Breakpoint (in pixels) of layout width up to which mobile mode is used"""
        return self._props.get("breakpoint")

    @ui_breakpoint.setter
    def ui_breakpoint(self, value):
        self._set_prop("breakpoint", value)

    @property
    def ui_behavior(self):
        """Overrides the default dynamic mode into which the drawer is put on"""
        return self._props.get("behavior")

    @ui_behavior.setter
    def ui_behavior(self, value):
        self._set_prop("behavior", value)

    @property
    def ui_bordered(self):
        return self._props.get("bordered")

    @ui_bordered.setter
    def ui_bordered(self, value):
        self._set_prop("bordered", value)

    @property
    def ui_elevated(self):
        """Adds a default shadow to the header"""
        return self._props.get("elevated")

    @ui_elevated.setter
    def ui_elevated(self, value):
        self._set_prop("elevated", value)

    @property
    def ui_persistent(self):
        """Prevents drawer from auto-closing when app's route changes; Also, an app route change won't hide it"""
        return self._props.get("persistent")

    @ui_persistent.setter
    def ui_persistent(self, value):
        self._set_prop("persistent", value)

    @property
    def ui_show_if_above(self):
        """Forces drawer to be shown on screen on initial render if the layout width is above breakpoint, regardless of v-model; This is the default behavior when SSR is taken over by client on initial render"""
        return self._props.get("show-if-above")

    @ui_show_if_above.setter
    def ui_show_if_above(self, value):
        self._set_prop("show-if-above", value)

    @property
    def ui_no_swipe_open(self):
        """Disables the default behavior where drawer can be swiped into view; Useful for iOS platforms where it might interfere with Safari's 'swipe to go to previous/next page' feature"""
        return self._props.get("no-swipe-open")

    @ui_no_swipe_open.setter
    def ui_no_swipe_open(self, value):
        self._set_prop("no-swipe-open", value)

    @property
    def ui_no_swipe_close(self):
        """Disables the default behavior where drawer can be swiped out of view (applies to drawer content only); Useful for iOS platforms where it might interfere with Safari's 'swipe to go to previous/next page' feature"""
        return self._props.get("no-swipe-close")

    @ui_no_swipe_close.setter
    def ui_no_swipe_close(self, value):
        self._set_prop("no-swipe-close", value)

    @property
    def ui_no_swipe_backdrop(self):
        """Disables the default behavior where drawer backdrop can be swiped"""
        return self._props.get("no-swipe-backdrop")

    @ui_no_swipe_backdrop.setter
    def ui_no_swipe_backdrop(self, value):
        self._set_prop("no-swipe-backdrop", value)

    @property
    def ui_model_value(self):
        """Model of the component defining shown/hidden state; Either use this property (along with a listener for 'update:model-value' event) OR use v-model directive"""
        return self._props.get("model-value")

    @ui_model_value.setter
    def ui_model_value(self, value):
        self._set_prop("model-value", value)

    @property
    def ui_slot_mini(self):
        """Content to show when in mini mode (overrides 'default' slot)"""
        return self.ui_slots.get("mini", [])

    @ui_slot_mini.setter
    def ui_slot_mini(self, value):
        self._set_slot("mini", value)

    def on_before_hide(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("before-hide", handler, arg)

    def on_before_show(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("before-show", handler, arg)

    def on_click(self, handler: Callable, arg: object = None):
        """
        Emitted when user clicks/taps on the component; Useful for when taking a decision to toggle mini mode

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("click.stop", handler, arg)

    def on_hide(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("hide", handler, arg)

    def on_mini_state(self, handler: Callable, arg: object = None):
        """
        Emitted when drawer changes the mini-mode state (sometimes it is forced to do so)

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("mini-state", handler, arg)

    def on_mouseout(self, handler: Callable, arg: object = None):
        """
        Emitted when user moves mouse cursor out of the component; Useful for when taking a decision to toggle mini mode

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("mouseout", handler, arg)

    def on_mouseover(self, handler: Callable, arg: object = None):
        """
        Emitted when user moves mouse cursor over the component; Useful for when taking a decision to toggle mini mode

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("mouseover", handler, arg)

    def on_on_layout(self, handler: Callable, arg: object = None):
        """
        Emitted when drawer toggles between occupying space on page or not

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("on-layout", handler, arg)

    def on_show(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("show", handler, arg)

    def on_update_model_value(self, handler: Callable, arg: object = None):
        """
        Emitted when showing/hidden state changes; Is also used by v-model

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("update:model-value", handler, arg)

    def ui_hide(self):
        self._js_call_method("hide")

    def ui_show(self):
        self._js_call_method("show")

    def ui_toggle(self):
        self._js_call_method("toggle")

    def _get_js_methods(self):
        return ["hide", "show", "toggle"]


class QEditor(Component):
    """
    Quasar Component: `QEditor <https://v2.quasar.dev/vue-components/editor>`__

    :param ui_model_value: Model of the component; Either use this property (along with a listener for 'update:modelValue' event) OR use v-model directive
    :param ui_readonly:
    :param ui_square:
    :param ui_flat: Applies a 'flat' design (no borders)
    :param ui_dense: Dense mode; toolbar buttons are shown on one-line only
    :param ui_dark:
    :param ui_disable:
    :param ui_min_height: CSS unit for the minimum height of the editable area
    :param ui_max_height: CSS unit for maximum height of the input area
    :param ui_height: CSS value to set the height of the editable area
    :param ui_definitions: Definition of commands and their buttons to be included in the 'toolbar' prop
    :param ui_fonts: Object with definitions of fonts
    :param ui_toolbar: An array of arrays of Objects/Strings that you use to define the construction of the elements and commands available in the toolbar
    :param ui_toolbar_color: Font color (from the Quasar Palette) of buttons and text in the toolbar
    :param ui_toolbar_text_color: Text color (from the Quasar Palette) of toolbar commands
    :param ui_toolbar_toggle_color: Choose the active color (from the Quasar Palette) of toolbar commands button
    :param ui_toolbar_bg: Toolbar background color (from Quasar Palette)
    :param ui_toolbar_outline: Toolbar buttons are rendered "outlined"
    :param ui_toolbar_push: Toolbar buttons are rendered as a "push-button" type
    :param ui_toolbar_rounded: Toolbar buttons are rendered "rounded"
    :param ui_paragraph_tag: Paragraph tag to be used
    :param ui_content_style: Object with CSS properties and values for styling the container of QEditor
    :param ui_content_class: CSS classes for the input area
    :param ui_placeholder: Text to display as placeholder
    :param ui_fullscreen: Fullscreen mode
    :param ui_no_route_fullscreen_exit: Changing route app won't exit fullscreen
    """

    def __init__(
        self,
        *children,
        ui_model_value: str | None = None,
        ui_readonly: Any | None = None,
        ui_square: Any | None = None,
        ui_flat: Any | None = None,
        ui_dense: Any | None = None,
        ui_dark: Any | None = None,
        ui_disable: Any | None = None,
        ui_min_height: str | None = None,
        ui_max_height: str | None = None,
        ui_height: str | None = None,
        ui_definitions: dict | None = None,
        ui_fonts: dict | None = None,
        ui_toolbar: list | None = None,
        ui_toolbar_color: Any | None = None,
        ui_toolbar_text_color: Any | None = None,
        ui_toolbar_toggle_color: str | None = None,
        ui_toolbar_bg: str | None = None,
        ui_toolbar_outline: bool | None = None,
        ui_toolbar_push: bool | None = None,
        ui_toolbar_rounded: bool | None = None,
        ui_paragraph_tag: str | None = None,
        ui_content_style: dict | None = None,
        ui_content_class: str | list | dict | None = None,
        ui_placeholder: str | None = None,
        ui_fullscreen: bool | None = None,
        ui_no_route_fullscreen_exit: bool | None = None,
        **kwargs,
    ):
        super().__init__("QEditor", *children, **kwargs)
        self.on("update:model-value", self.__update_model_value)

        if ui_model_value is not None:
            self._props["model-value"] = ui_model_value
        if ui_readonly is not None:
            self._props["readonly"] = ui_readonly
        if ui_square is not None:
            self._props["square"] = ui_square
        if ui_flat is not None:
            self._props["flat"] = ui_flat
        if ui_dense is not None:
            self._props["dense"] = ui_dense
        if ui_dark is not None:
            self._props["dark"] = ui_dark
        if ui_disable is not None:
            self._props["disable"] = ui_disable
        if ui_min_height is not None:
            self._props["min-height"] = ui_min_height
        if ui_max_height is not None:
            self._props["max-height"] = ui_max_height
        if ui_height is not None:
            self._props["height"] = ui_height
        if ui_definitions is not None:
            self._props["definitions"] = ui_definitions
        if ui_fonts is not None:
            self._props["fonts"] = ui_fonts
        if ui_toolbar is not None:
            self._props["toolbar"] = ui_toolbar
        if ui_toolbar_color is not None:
            self._props["toolbar-color"] = ui_toolbar_color
        if ui_toolbar_text_color is not None:
            self._props["toolbar-text-color"] = ui_toolbar_text_color
        if ui_toolbar_toggle_color is not None:
            self._props["toolbar-toggle-color"] = ui_toolbar_toggle_color
        if ui_toolbar_bg is not None:
            self._props["toolbar-bg"] = ui_toolbar_bg
        if ui_toolbar_outline is not None:
            self._props["toolbar-outline"] = ui_toolbar_outline
        if ui_toolbar_push is not None:
            self._props["toolbar-push"] = ui_toolbar_push
        if ui_toolbar_rounded is not None:
            self._props["toolbar-rounded"] = ui_toolbar_rounded
        if ui_paragraph_tag is not None:
            self._props["paragraph-tag"] = ui_paragraph_tag
        if ui_content_style is not None:
            self._props["content-style"] = ui_content_style
        if ui_content_class is not None:
            self._props["content-class"] = ui_content_class
        if ui_placeholder is not None:
            self._props["placeholder"] = ui_placeholder
        if ui_fullscreen is not None:
            self._props["fullscreen"] = ui_fullscreen
        if ui_no_route_fullscreen_exit is not None:
            self._props["no-route-fullscreen-exit"] = (
                ui_no_route_fullscreen_exit
            )

    def __update_model_value(self, event: Event):
        self._set_prop("model-value", event.value)

    @property
    def ui_model_value(self):
        """Model of the component; Either use this property (along with a listener for 'update:modelValue' event) OR use v-model directive"""
        return self._props.get("model-value")

    @ui_model_value.setter
    def ui_model_value(self, value):
        self._set_prop("model-value", value)

    @property
    def ui_readonly(self):
        return self._props.get("readonly")

    @ui_readonly.setter
    def ui_readonly(self, value):
        self._set_prop("readonly", value)

    @property
    def ui_square(self):
        return self._props.get("square")

    @ui_square.setter
    def ui_square(self, value):
        self._set_prop("square", value)

    @property
    def ui_flat(self):
        """Applies a 'flat' design (no borders)"""
        return self._props.get("flat")

    @ui_flat.setter
    def ui_flat(self, value):
        self._set_prop("flat", value)

    @property
    def ui_dense(self):
        """Dense mode; toolbar buttons are shown on one-line only"""
        return self._props.get("dense")

    @ui_dense.setter
    def ui_dense(self, value):
        self._set_prop("dense", value)

    @property
    def ui_dark(self):
        return self._props.get("dark")

    @ui_dark.setter
    def ui_dark(self, value):
        self._set_prop("dark", value)

    @property
    def ui_disable(self):
        return self._props.get("disable")

    @ui_disable.setter
    def ui_disable(self, value):
        self._set_prop("disable", value)

    @property
    def ui_min_height(self):
        """CSS unit for the minimum height of the editable area"""
        return self._props.get("min-height")

    @ui_min_height.setter
    def ui_min_height(self, value):
        self._set_prop("min-height", value)

    @property
    def ui_max_height(self):
        """CSS unit for maximum height of the input area"""
        return self._props.get("max-height")

    @ui_max_height.setter
    def ui_max_height(self, value):
        self._set_prop("max-height", value)

    @property
    def ui_height(self):
        """CSS value to set the height of the editable area"""
        return self._props.get("height")

    @ui_height.setter
    def ui_height(self, value):
        self._set_prop("height", value)

    @property
    def ui_definitions(self):
        """Definition of commands and their buttons to be included in the 'toolbar' prop"""
        return self._props.get("definitions")

    @ui_definitions.setter
    def ui_definitions(self, value):
        self._set_prop("definitions", value)

    @property
    def ui_fonts(self):
        """Object with definitions of fonts"""
        return self._props.get("fonts")

    @ui_fonts.setter
    def ui_fonts(self, value):
        self._set_prop("fonts", value)

    @property
    def ui_toolbar(self):
        """An array of arrays of Objects/Strings that you use to define the construction of the elements and commands available in the toolbar"""
        return self._props.get("toolbar")

    @ui_toolbar.setter
    def ui_toolbar(self, value):
        self._set_prop("toolbar", value)

    @property
    def ui_toolbar_color(self):
        """Font color (from the Quasar Palette) of buttons and text in the toolbar"""
        return self._props.get("toolbar-color")

    @ui_toolbar_color.setter
    def ui_toolbar_color(self, value):
        self._set_prop("toolbar-color", value)

    @property
    def ui_toolbar_text_color(self):
        """Text color (from the Quasar Palette) of toolbar commands"""
        return self._props.get("toolbar-text-color")

    @ui_toolbar_text_color.setter
    def ui_toolbar_text_color(self, value):
        self._set_prop("toolbar-text-color", value)

    @property
    def ui_toolbar_toggle_color(self):
        """Choose the active color (from the Quasar Palette) of toolbar commands button"""
        return self._props.get("toolbar-toggle-color")

    @ui_toolbar_toggle_color.setter
    def ui_toolbar_toggle_color(self, value):
        self._set_prop("toolbar-toggle-color", value)

    @property
    def ui_toolbar_bg(self):
        """Toolbar background color (from Quasar Palette)"""
        return self._props.get("toolbar-bg")

    @ui_toolbar_bg.setter
    def ui_toolbar_bg(self, value):
        self._set_prop("toolbar-bg", value)

    @property
    def ui_toolbar_outline(self):
        """Toolbar buttons are rendered "outlined" """
        return self._props.get("toolbar-outline")

    @ui_toolbar_outline.setter
    def ui_toolbar_outline(self, value):
        self._set_prop("toolbar-outline", value)

    @property
    def ui_toolbar_push(self):
        """Toolbar buttons are rendered as a "push-button" type"""
        return self._props.get("toolbar-push")

    @ui_toolbar_push.setter
    def ui_toolbar_push(self, value):
        self._set_prop("toolbar-push", value)

    @property
    def ui_toolbar_rounded(self):
        """Toolbar buttons are rendered "rounded" """
        return self._props.get("toolbar-rounded")

    @ui_toolbar_rounded.setter
    def ui_toolbar_rounded(self, value):
        self._set_prop("toolbar-rounded", value)

    @property
    def ui_paragraph_tag(self):
        """Paragraph tag to be used"""
        return self._props.get("paragraph-tag")

    @ui_paragraph_tag.setter
    def ui_paragraph_tag(self, value):
        self._set_prop("paragraph-tag", value)

    @property
    def ui_content_style(self):
        """Object with CSS properties and values for styling the container of QEditor"""
        return self._props.get("content-style")

    @ui_content_style.setter
    def ui_content_style(self, value):
        self._set_prop("content-style", value)

    @property
    def ui_content_class(self):
        """CSS classes for the input area"""
        return self._props.get("content-class")

    @ui_content_class.setter
    def ui_content_class(self, value):
        self._set_prop("content-class", value)

    @property
    def ui_placeholder(self):
        """Text to display as placeholder"""
        return self._props.get("placeholder")

    @ui_placeholder.setter
    def ui_placeholder(self, value):
        self._set_prop("placeholder", value)

    @property
    def ui_fullscreen(self):
        """Fullscreen mode"""
        return self._props.get("fullscreen")

    @ui_fullscreen.setter
    def ui_fullscreen(self, value):
        self._set_prop("fullscreen", value)

    @property
    def ui_no_route_fullscreen_exit(self):
        """Changing route app won't exit fullscreen"""
        return self._props.get("no-route-fullscreen-exit")

    @ui_no_route_fullscreen_exit.setter
    def ui_no_route_fullscreen_exit(self, value):
        self._set_prop("no-route-fullscreen-exit", value)

    def ui_slot_command(self, command, value):
        """Content for the given command in the toolbar"""
        self._set_slot("" + command, value)

    def on_blur(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("blur", handler, arg)

    def on_click(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("click.stop", handler, arg)

    def on_dropdown_before_hide(self, handler: Callable, arg: object = None):
        """
        Emitted when a dropdown in the toolbar triggers hide() but before it finishes doing it

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("dropdown-before-hide", handler, arg)

    def on_dropdown_before_show(self, handler: Callable, arg: object = None):
        """
        Emitted when a dropdown in the toolbar triggers show() but before it finishes doing it

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("dropdown-before-show", handler, arg)

    def on_dropdown_hide(self, handler: Callable, arg: object = None):
        """
        Emitted after a dropdown in the toolbar has triggered hide()

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("dropdown-hide", handler, arg)

    def on_dropdown_show(self, handler: Callable, arg: object = None):
        """
        Emitted after a dropdown in the toolbar has triggered show()

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("dropdown-show", handler, arg)

    def on_focus(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("focus", handler, arg)

    def on_fullscreen(self, handler: Callable, arg: object = None):
        """
        Emitted when fullscreen state changes

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("fullscreen", handler, arg)

    def on_keydown(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("keydown", handler, arg)

    def on_link_hide(self, handler: Callable, arg: object = None):
        """
        Emitted when the toolbar for editing a link is hidden

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("link-hide", handler, arg)

    def on_link_show(self, handler: Callable, arg: object = None):
        """
        Emitted when the toolbar for editing a link is shown

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("link-show", handler, arg)

    def on_update_fullscreen(self, handler: Callable, arg: object = None):
        """
        Used by Vue on 'v-model:fullscreen' prop for updating its value

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("update:fullscreen", handler, arg)

    def on_update_model_value(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("update:model-value", handler, arg)

    def ui_exitFullscreen(self):
        """Leave the fullscreen view"""
        self._js_call_method("exitFullscreen")

    def ui_focus(self):
        """Focus on the contentEditable at saved cursor position"""
        self._js_call_method("focus")

    def ui_getContentEl(self):
        """Retrieve the content of the Editor"""
        self._js_call_method("getContentEl")

    def ui_refreshToolbar(self):
        """Hide the link editor if visible and force the instance to re-render"""
        self._js_call_method("refreshToolbar")

    def ui_runCmd(self, ui_cmd, ui_param=None, ui_update=None):
        """Run contentEditable command at caret position and range"""
        kwargs = {}
        if ui_cmd is not None:
            kwargs["cmd"] = ui_cmd
        if ui_param is not None:
            kwargs["param"] = ui_param
        if ui_update is not None:
            kwargs["update"] = ui_update
        self._js_call_method("runCmd", [kwargs])

    def ui_setFullscreen(self):
        """Enter the fullscreen view"""
        self._js_call_method("setFullscreen")

    def ui_toggleFullscreen(self):
        """Toggle the view to be fullscreen or not fullscreen"""
        self._js_call_method("toggleFullscreen")

    def _get_js_methods(self):
        return [
            "exitFullscreen",
            "focus",
            "getContentEl",
            "refreshToolbar",
            "runCmd",
            "setFullscreen",
            "toggleFullscreen",
        ]


class QExpansionItem(Component):
    """
    Quasar Component: `QExpansionItem <https://v2.quasar.dev/vue-components/expansion-item>`__

    :param ui_icon:
    :param ui_expand_icon:
    :param ui_expanded_icon: Expand icon name (following Quasar convention) for when QExpansionItem is expanded; When used, it also disables the rotation animation of the expand icon; Make sure you have the icon library installed unless you are using 'img:' prefix
    :param ui_expand_icon_class: Apply custom class(es) to the expand icon item section
    :param ui_toggle_aria_label: aria-label to be used on the expansion toggle element
    :param ui_label: Header label (unless using 'header' slot)
    :param ui_label_lines: Apply ellipsis when there's not enough space to render on the specified number of lines; If more than one line specified, then it will only work on webkit browsers because it uses the '-webkit-line-clamp' CSS property!
    :param ui_caption: Header sub-label (unless using 'header' slot)
    :param ui_caption_lines: Apply ellipsis when there's not enough space to render on the specified number of lines; If more than one line specified, then it will only work on webkit browsers because it uses the '-webkit-line-clamp' CSS property!
    :param ui_dark:
    :param ui_dense:
    :param ui_duration: Animation duration (in milliseconds)
    :param ui_header_inset_level: Apply an inset to header (unless using 'header' slot); Useful when header avatar/left side is missing but you want to align content with other items that do have a left side, or when you're building a menu
    :param ui_content_inset_level: Apply an inset to content (changes content padding)
    :param ui_expand_separator: Apply a top and bottom separator when expansion item is opened
    :param ui_default_opened: Puts expansion item into open state on initial render; Overridden by v-model if used
    :param ui_hide_expand_icon: Do not show the expand icon
    :param ui_expand_icon_toggle: Applies the expansion events to the expand icon only and not to the whole header
    :param ui_switch_toggle_side: Switch expand icon side (from default 'right' to 'left')
    :param ui_dense_toggle: Use dense mode for expand icon
    :param ui_group: Register expansion item into a group (unique name that must be applied to all expansion items in that group) for coordinated open/close state within the group a.k.a. 'accordion mode'
    :param ui_popup: Put expansion list into 'popup' mode
    :param ui_header_style: Apply custom style to the header
    :param ui_header_class: Apply custom class(es) to the header
    :param ui_model_value: Model of the component defining shown/hidden state; Either use this property (along with a listener for 'update:model-value' event) OR use v-model directive
    :param ui_to: Equivalent to Vue Router <router-link> 'to' property; Superseded by 'href' prop if used
    :param ui_exact: Equivalent to Vue Router <router-link> 'exact' property; Superseded by 'href' prop if used
    :param ui_replace: Equivalent to Vue Router <router-link> 'replace' property; Superseded by 'href' prop if used
    :param ui_active_class: Equivalent to Vue Router <router-link> 'active-class' property; Superseded by 'href' prop if used
    :param ui_exact_active_class: Equivalent to Vue Router <router-link> 'active-class' property; Superseded by 'href' prop if used
    :param ui_href: Native <a> link href attribute; Has priority over the 'to'/'exact'/'replace'/'active-class'/'exact-active-class' props
    :param ui_target: Native <a> link target attribute; Use it only along with 'href' prop; Has priority over the 'to'/'exact'/'replace'/'active-class'/'exact-active-class' props
    :param ui_disable:
    """

    def __init__(
        self,
        *children,
        ui_icon: Any | None = None,
        ui_expand_icon: Any | None = None,
        ui_expanded_icon: Any | None = None,
        ui_expand_icon_class: str | list | dict | None = None,
        ui_toggle_aria_label: str | None = None,
        ui_label: str | None = None,
        ui_label_lines: float | str | None = None,
        ui_caption: str | None = None,
        ui_caption_lines: float | str | None = None,
        ui_dark: Any | None = None,
        ui_dense: Any | None = None,
        ui_duration: float | None = None,
        ui_header_inset_level: float | None = None,
        ui_content_inset_level: float | None = None,
        ui_expand_separator: bool | None = None,
        ui_default_opened: bool | None = None,
        ui_hide_expand_icon: bool | None = None,
        ui_expand_icon_toggle: bool | None = None,
        ui_switch_toggle_side: bool | None = None,
        ui_dense_toggle: bool | None = None,
        ui_group: str | None = None,
        ui_popup: bool | None = None,
        ui_header_style: str | list | dict | None = None,
        ui_header_class: str | list | dict | None = None,
        ui_model_value: bool | None = None,
        ui_to: str | dict | None = None,
        ui_exact: bool | None = None,
        ui_replace: bool | None = None,
        ui_active_class: str | None = None,
        ui_exact_active_class: str | None = None,
        ui_href: str | None = None,
        ui_target: str | None = None,
        ui_disable: Any | None = None,
        **kwargs,
    ):
        super().__init__("QExpansionItem", *children, **kwargs)
        self.on("update:model-value", self.__update_model_value)

        if ui_icon is not None:
            self._props["icon"] = ui_icon
        if ui_expand_icon is not None:
            self._props["expand-icon"] = ui_expand_icon
        if ui_expanded_icon is not None:
            self._props["expanded-icon"] = ui_expanded_icon
        if ui_expand_icon_class is not None:
            self._props["expand-icon-class"] = ui_expand_icon_class
        if ui_toggle_aria_label is not None:
            self._props["toggle-aria-label"] = ui_toggle_aria_label
        if ui_label is not None:
            self._props["label"] = ui_label
        if ui_label_lines is not None:
            self._props["label-lines"] = ui_label_lines
        if ui_caption is not None:
            self._props["caption"] = ui_caption
        if ui_caption_lines is not None:
            self._props["caption-lines"] = ui_caption_lines
        if ui_dark is not None:
            self._props["dark"] = ui_dark
        if ui_dense is not None:
            self._props["dense"] = ui_dense
        if ui_duration is not None:
            self._props["duration"] = ui_duration
        if ui_header_inset_level is not None:
            self._props["header-inset-level"] = ui_header_inset_level
        if ui_content_inset_level is not None:
            self._props["content-inset-level"] = ui_content_inset_level
        if ui_expand_separator is not None:
            self._props["expand-separator"] = ui_expand_separator
        if ui_default_opened is not None:
            self._props["default-opened"] = ui_default_opened
        if ui_hide_expand_icon is not None:
            self._props["hide-expand-icon"] = ui_hide_expand_icon
        if ui_expand_icon_toggle is not None:
            self._props["expand-icon-toggle"] = ui_expand_icon_toggle
        if ui_switch_toggle_side is not None:
            self._props["switch-toggle-side"] = ui_switch_toggle_side
        if ui_dense_toggle is not None:
            self._props["dense-toggle"] = ui_dense_toggle
        if ui_group is not None:
            self._props["group"] = ui_group
        if ui_popup is not None:
            self._props["popup"] = ui_popup
        if ui_header_style is not None:
            self._props["header-style"] = ui_header_style
        if ui_header_class is not None:
            self._props["header-class"] = ui_header_class
        if ui_model_value is not None:
            self._props["model-value"] = ui_model_value
        if ui_to is not None:
            self._props["to"] = ui_to
        if ui_exact is not None:
            self._props["exact"] = ui_exact
        if ui_replace is not None:
            self._props["replace"] = ui_replace
        if ui_active_class is not None:
            self._props["active-class"] = ui_active_class
        if ui_exact_active_class is not None:
            self._props["exact-active-class"] = ui_exact_active_class
        if ui_href is not None:
            self._props["href"] = ui_href
        if ui_target is not None:
            self._props["target"] = ui_target
        if ui_disable is not None:
            self._props["disable"] = ui_disable

    def __update_model_value(self, event: Event):
        self._set_prop("model-value", event.value)

    @property
    def ui_icon(self):
        return self._props.get("icon")

    @ui_icon.setter
    def ui_icon(self, value):
        self._set_prop("icon", value)

    @property
    def ui_expand_icon(self):
        return self._props.get("expand-icon")

    @ui_expand_icon.setter
    def ui_expand_icon(self, value):
        self._set_prop("expand-icon", value)

    @property
    def ui_expanded_icon(self):
        """Expand icon name (following Quasar convention) for when QExpansionItem is expanded; When used, it also disables the rotation animation of the expand icon; Make sure you have the icon library installed unless you are using 'img:' prefix"""
        return self._props.get("expanded-icon")

    @ui_expanded_icon.setter
    def ui_expanded_icon(self, value):
        self._set_prop("expanded-icon", value)

    @property
    def ui_expand_icon_class(self):
        """Apply custom class(es) to the expand icon item section"""
        return self._props.get("expand-icon-class")

    @ui_expand_icon_class.setter
    def ui_expand_icon_class(self, value):
        self._set_prop("expand-icon-class", value)

    @property
    def ui_toggle_aria_label(self):
        """aria-label to be used on the expansion toggle element"""
        return self._props.get("toggle-aria-label")

    @ui_toggle_aria_label.setter
    def ui_toggle_aria_label(self, value):
        self._set_prop("toggle-aria-label", value)

    @property
    def ui_label(self):
        """Header label (unless using 'header' slot)"""
        return self._props.get("label")

    @ui_label.setter
    def ui_label(self, value):
        self._set_prop("label", value)

    @property
    def ui_label_lines(self):
        """Apply ellipsis when there's not enough space to render on the specified number of lines; If more than one line specified, then it will only work on webkit browsers because it uses the '-webkit-line-clamp' CSS property!"""
        return self._props.get("label-lines")

    @ui_label_lines.setter
    def ui_label_lines(self, value):
        self._set_prop("label-lines", value)

    @property
    def ui_caption(self):
        """Header sub-label (unless using 'header' slot)"""
        return self._props.get("caption")

    @ui_caption.setter
    def ui_caption(self, value):
        self._set_prop("caption", value)

    @property
    def ui_caption_lines(self):
        """Apply ellipsis when there's not enough space to render on the specified number of lines; If more than one line specified, then it will only work on webkit browsers because it uses the '-webkit-line-clamp' CSS property!"""
        return self._props.get("caption-lines")

    @ui_caption_lines.setter
    def ui_caption_lines(self, value):
        self._set_prop("caption-lines", value)

    @property
    def ui_dark(self):
        return self._props.get("dark")

    @ui_dark.setter
    def ui_dark(self, value):
        self._set_prop("dark", value)

    @property
    def ui_dense(self):
        return self._props.get("dense")

    @ui_dense.setter
    def ui_dense(self, value):
        self._set_prop("dense", value)

    @property
    def ui_duration(self):
        """Animation duration (in milliseconds)"""
        return self._props.get("duration")

    @ui_duration.setter
    def ui_duration(self, value):
        self._set_prop("duration", value)

    @property
    def ui_header_inset_level(self):
        """Apply an inset to header (unless using 'header' slot); Useful when header avatar/left side is missing but you want to align content with other items that do have a left side, or when you're building a menu"""
        return self._props.get("header-inset-level")

    @ui_header_inset_level.setter
    def ui_header_inset_level(self, value):
        self._set_prop("header-inset-level", value)

    @property
    def ui_content_inset_level(self):
        """Apply an inset to content (changes content padding)"""
        return self._props.get("content-inset-level")

    @ui_content_inset_level.setter
    def ui_content_inset_level(self, value):
        self._set_prop("content-inset-level", value)

    @property
    def ui_expand_separator(self):
        """Apply a top and bottom separator when expansion item is opened"""
        return self._props.get("expand-separator")

    @ui_expand_separator.setter
    def ui_expand_separator(self, value):
        self._set_prop("expand-separator", value)

    @property
    def ui_default_opened(self):
        """Puts expansion item into open state on initial render; Overridden by v-model if used"""
        return self._props.get("default-opened")

    @ui_default_opened.setter
    def ui_default_opened(self, value):
        self._set_prop("default-opened", value)

    @property
    def ui_hide_expand_icon(self):
        """Do not show the expand icon"""
        return self._props.get("hide-expand-icon")

    @ui_hide_expand_icon.setter
    def ui_hide_expand_icon(self, value):
        self._set_prop("hide-expand-icon", value)

    @property
    def ui_expand_icon_toggle(self):
        """Applies the expansion events to the expand icon only and not to the whole header"""
        return self._props.get("expand-icon-toggle")

    @ui_expand_icon_toggle.setter
    def ui_expand_icon_toggle(self, value):
        self._set_prop("expand-icon-toggle", value)

    @property
    def ui_switch_toggle_side(self):
        """Switch expand icon side (from default 'right' to 'left')"""
        return self._props.get("switch-toggle-side")

    @ui_switch_toggle_side.setter
    def ui_switch_toggle_side(self, value):
        self._set_prop("switch-toggle-side", value)

    @property
    def ui_dense_toggle(self):
        """Use dense mode for expand icon"""
        return self._props.get("dense-toggle")

    @ui_dense_toggle.setter
    def ui_dense_toggle(self, value):
        self._set_prop("dense-toggle", value)

    @property
    def ui_group(self):
        """Register expansion item into a group (unique name that must be applied to all expansion items in that group) for coordinated open/close state within the group a.k.a. 'accordion mode'"""
        return self._props.get("group")

    @ui_group.setter
    def ui_group(self, value):
        self._set_prop("group", value)

    @property
    def ui_popup(self):
        """Put expansion list into 'popup' mode"""
        return self._props.get("popup")

    @ui_popup.setter
    def ui_popup(self, value):
        self._set_prop("popup", value)

    @property
    def ui_header_style(self):
        """Apply custom style to the header"""
        return self._props.get("header-style")

    @ui_header_style.setter
    def ui_header_style(self, value):
        self._set_prop("header-style", value)

    @property
    def ui_header_class(self):
        """Apply custom class(es) to the header"""
        return self._props.get("header-class")

    @ui_header_class.setter
    def ui_header_class(self, value):
        self._set_prop("header-class", value)

    @property
    def ui_model_value(self):
        """Model of the component defining shown/hidden state; Either use this property (along with a listener for 'update:model-value' event) OR use v-model directive"""
        return self._props.get("model-value")

    @ui_model_value.setter
    def ui_model_value(self, value):
        self._set_prop("model-value", value)

    @property
    def ui_to(self):
        """Equivalent to Vue Router <router-link> 'to' property; Superseded by 'href' prop if used"""
        return self._props.get("to")

    @ui_to.setter
    def ui_to(self, value):
        self._set_prop("to", value)

    @property
    def ui_exact(self):
        """Equivalent to Vue Router <router-link> 'exact' property; Superseded by 'href' prop if used"""
        return self._props.get("exact")

    @ui_exact.setter
    def ui_exact(self, value):
        self._set_prop("exact", value)

    @property
    def ui_replace(self):
        """Equivalent to Vue Router <router-link> 'replace' property; Superseded by 'href' prop if used"""
        return self._props.get("replace")

    @ui_replace.setter
    def ui_replace(self, value):
        self._set_prop("replace", value)

    @property
    def ui_active_class(self):
        """Equivalent to Vue Router <router-link> 'active-class' property; Superseded by 'href' prop if used"""
        return self._props.get("active-class")

    @ui_active_class.setter
    def ui_active_class(self, value):
        self._set_prop("active-class", value)

    @property
    def ui_exact_active_class(self):
        """Equivalent to Vue Router <router-link> 'active-class' property; Superseded by 'href' prop if used"""
        return self._props.get("exact-active-class")

    @ui_exact_active_class.setter
    def ui_exact_active_class(self, value):
        self._set_prop("exact-active-class", value)

    @property
    def ui_href(self):
        """Native <a> link href attribute; Has priority over the 'to'/'exact'/'replace'/'active-class'/'exact-active-class' props"""
        return self._props.get("href")

    @ui_href.setter
    def ui_href(self, value):
        self._set_prop("href", value)

    @property
    def ui_target(self):
        """Native <a> link target attribute; Use it only along with 'href' prop; Has priority over the 'to'/'exact'/'replace'/'active-class'/'exact-active-class' props"""
        return self._props.get("target")

    @ui_target.setter
    def ui_target(self, value):
        self._set_prop("target", value)

    @property
    def ui_disable(self):
        return self._props.get("disable")

    @ui_disable.setter
    def ui_disable(self, value):
        self._set_prop("disable", value)

    @property
    def ui_slot_header(self):
        """Slot used for overriding default header"""
        return self.ui_slots.get("header", [])

    @ui_slot_header.setter
    def ui_slot_header(self, value):
        self._set_slot("header", value)

    def on_after_hide(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("after-hide", handler, arg)

    def on_after_show(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("after-show", handler, arg)

    def on_before_hide(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("before-hide", handler, arg)

    def on_before_show(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("before-show", handler, arg)

    def on_click(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("click.stop", handler, arg)

    def on_hide(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("hide", handler, arg)

    def on_show(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("show", handler, arg)

    def on_update_model_value(self, handler: Callable, arg: object = None):
        """
        Emitted when showing/hidden state changes; Is also used by v-model

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("update:model-value", handler, arg)

    def ui_hide(self):
        self._js_call_method("hide")

    def ui_show(self):
        self._js_call_method("show")

    def ui_toggle(self):
        self._js_call_method("toggle")

    def _get_js_methods(self):
        return ["hide", "show", "toggle"]


class QFab(Component):
    """
    Quasar Component: `QFab <https://v2.quasar.dev/vue-components/floating-action-button>`__

    :param ui_model_value: Model of the component defining shown/hidden state; Either use this property (along with a listener for 'update:model-value' event) OR use v-model directive
    :param ui_icon:
    :param ui_active_icon:
    :param ui_hide_label: Hide the label; Useful for animation purposes where you toggle the visibility of the label
    :param ui_hide_icon: Hide the icon (don't use any)
    :param ui_direction: Direction to expand Fab Actions to
    :param ui_vertical_actions_align: The side of the Fab where Fab Actions will expand (only when direction is 'up' or 'down')
    :param ui_persistent: By default, Fab Actions are hidden when user navigates to another route and this prop disables this behavior
    :param ui_type: Define the button HTML DOM type
    :param ui_outline: Use 'outline' design for Fab button
    :param ui_push: Use 'push' design for Fab button
    :param ui_flat: Use 'flat' design for Fab button
    :param ui_unelevated: Remove shadow
    :param ui_padding: Apply custom padding (vertical [horizontal]); Size in CSS units, including unit name or standard size name (none|xs|sm|md|lg|xl); Also removes the min width and height when set
    :param ui_color:
    :param ui_text_color:
    :param ui_glossy: Apply the glossy effect over the button
    :param ui_external_label: Display label besides the FABs, as external content
    :param ui_label: The label that will be shown when Fab is extended
    :param ui_label_position: Position of the label around the icon
    :param ui_label_class: Class definitions to be attributed to the label container
    :param ui_label_style: Style definitions to be attributed to the label container
    :param ui_square: Apply a rectangle aspect to the FAB
    :param ui_disable:
    :param ui_tabindex:
    """

    def __init__(
        self,
        *children,
        ui_model_value: bool | None = None,
        ui_icon: Any | None = None,
        ui_active_icon: Any | None = None,
        ui_hide_label: bool | None = None,
        ui_hide_icon: bool | None = None,
        ui_direction: str | None = None,
        ui_vertical_actions_align: str | None = None,
        ui_persistent: bool | None = None,
        ui_type: str | None = None,
        ui_outline: bool | None = None,
        ui_push: bool | None = None,
        ui_flat: bool | None = None,
        ui_unelevated: bool | None = None,
        ui_padding: str | None = None,
        ui_color: Any | None = None,
        ui_text_color: Any | None = None,
        ui_glossy: bool | None = None,
        ui_external_label: bool | None = None,
        ui_label: str | float | None = None,
        ui_label_position: str | None = None,
        ui_label_class: str | list | dict | None = None,
        ui_label_style: str | list | dict | None = None,
        ui_square: bool | None = None,
        ui_disable: Any | None = None,
        ui_tabindex: Any | None = None,
        **kwargs,
    ):
        super().__init__("QFab", *children, **kwargs)
        self.on("update:model-value", self.__update_model_value)

        if ui_model_value is not None:
            self._props["model-value"] = ui_model_value
        if ui_icon is not None:
            self._props["icon"] = ui_icon
        if ui_active_icon is not None:
            self._props["active-icon"] = ui_active_icon
        if ui_hide_label is not None:
            self._props["hide-label"] = ui_hide_label
        if ui_hide_icon is not None:
            self._props["hide-icon"] = ui_hide_icon
        if ui_direction is not None:
            self._props["direction"] = ui_direction
        if ui_vertical_actions_align is not None:
            self._props["vertical-actions-align"] = ui_vertical_actions_align
        if ui_persistent is not None:
            self._props["persistent"] = ui_persistent
        if ui_type is not None:
            self._props["type"] = ui_type
        if ui_outline is not None:
            self._props["outline"] = ui_outline
        if ui_push is not None:
            self._props["push"] = ui_push
        if ui_flat is not None:
            self._props["flat"] = ui_flat
        if ui_unelevated is not None:
            self._props["unelevated"] = ui_unelevated
        if ui_padding is not None:
            self._props["padding"] = ui_padding
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_text_color is not None:
            self._props["text-color"] = ui_text_color
        if ui_glossy is not None:
            self._props["glossy"] = ui_glossy
        if ui_external_label is not None:
            self._props["external-label"] = ui_external_label
        if ui_label is not None:
            self._props["label"] = ui_label
        if ui_label_position is not None:
            self._props["label-position"] = ui_label_position
        if ui_label_class is not None:
            self._props["label-class"] = ui_label_class
        if ui_label_style is not None:
            self._props["label-style"] = ui_label_style
        if ui_square is not None:
            self._props["square"] = ui_square
        if ui_disable is not None:
            self._props["disable"] = ui_disable
        if ui_tabindex is not None:
            self._props["tabindex"] = ui_tabindex

    def __update_model_value(self, event: Event):
        self._set_prop("model-value", event.value)

    @property
    def ui_model_value(self):
        """Model of the component defining shown/hidden state; Either use this property (along with a listener for 'update:model-value' event) OR use v-model directive"""
        return self._props.get("model-value")

    @ui_model_value.setter
    def ui_model_value(self, value):
        self._set_prop("model-value", value)

    @property
    def ui_icon(self):
        return self._props.get("icon")

    @ui_icon.setter
    def ui_icon(self, value):
        self._set_prop("icon", value)

    @property
    def ui_active_icon(self):
        return self._props.get("active-icon")

    @ui_active_icon.setter
    def ui_active_icon(self, value):
        self._set_prop("active-icon", value)

    @property
    def ui_hide_label(self):
        """Hide the label; Useful for animation purposes where you toggle the visibility of the label"""
        return self._props.get("hide-label")

    @ui_hide_label.setter
    def ui_hide_label(self, value):
        self._set_prop("hide-label", value)

    @property
    def ui_hide_icon(self):
        """Hide the icon (don't use any)"""
        return self._props.get("hide-icon")

    @ui_hide_icon.setter
    def ui_hide_icon(self, value):
        self._set_prop("hide-icon", value)

    @property
    def ui_direction(self):
        """Direction to expand Fab Actions to"""
        return self._props.get("direction")

    @ui_direction.setter
    def ui_direction(self, value):
        self._set_prop("direction", value)

    @property
    def ui_vertical_actions_align(self):
        """The side of the Fab where Fab Actions will expand (only when direction is 'up' or 'down')"""
        return self._props.get("vertical-actions-align")

    @ui_vertical_actions_align.setter
    def ui_vertical_actions_align(self, value):
        self._set_prop("vertical-actions-align", value)

    @property
    def ui_persistent(self):
        """By default, Fab Actions are hidden when user navigates to another route and this prop disables this behavior"""
        return self._props.get("persistent")

    @ui_persistent.setter
    def ui_persistent(self, value):
        self._set_prop("persistent", value)

    @property
    def ui_type(self):
        """Define the button HTML DOM type"""
        return self._props.get("type")

    @ui_type.setter
    def ui_type(self, value):
        self._set_prop("type", value)

    @property
    def ui_outline(self):
        """Use 'outline' design for Fab button"""
        return self._props.get("outline")

    @ui_outline.setter
    def ui_outline(self, value):
        self._set_prop("outline", value)

    @property
    def ui_push(self):
        """Use 'push' design for Fab button"""
        return self._props.get("push")

    @ui_push.setter
    def ui_push(self, value):
        self._set_prop("push", value)

    @property
    def ui_flat(self):
        """Use 'flat' design for Fab button"""
        return self._props.get("flat")

    @ui_flat.setter
    def ui_flat(self, value):
        self._set_prop("flat", value)

    @property
    def ui_unelevated(self):
        """Remove shadow"""
        return self._props.get("unelevated")

    @ui_unelevated.setter
    def ui_unelevated(self, value):
        self._set_prop("unelevated", value)

    @property
    def ui_padding(self):
        """Apply custom padding (vertical [horizontal]); Size in CSS units, including unit name or standard size name (none|xs|sm|md|lg|xl); Also removes the min width and height when set"""
        return self._props.get("padding")

    @ui_padding.setter
    def ui_padding(self, value):
        self._set_prop("padding", value)

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_text_color(self):
        return self._props.get("text-color")

    @ui_text_color.setter
    def ui_text_color(self, value):
        self._set_prop("text-color", value)

    @property
    def ui_glossy(self):
        """Apply the glossy effect over the button"""
        return self._props.get("glossy")

    @ui_glossy.setter
    def ui_glossy(self, value):
        self._set_prop("glossy", value)

    @property
    def ui_external_label(self):
        """Display label besides the FABs, as external content"""
        return self._props.get("external-label")

    @ui_external_label.setter
    def ui_external_label(self, value):
        self._set_prop("external-label", value)

    @property
    def ui_label(self):
        """The label that will be shown when Fab is extended"""
        return self._props.get("label")

    @ui_label.setter
    def ui_label(self, value):
        self._set_prop("label", value)

    @property
    def ui_label_position(self):
        """Position of the label around the icon"""
        return self._props.get("label-position")

    @ui_label_position.setter
    def ui_label_position(self, value):
        self._set_prop("label-position", value)

    @property
    def ui_label_class(self):
        """Class definitions to be attributed to the label container"""
        return self._props.get("label-class")

    @ui_label_class.setter
    def ui_label_class(self, value):
        self._set_prop("label-class", value)

    @property
    def ui_label_style(self):
        """Style definitions to be attributed to the label container"""
        return self._props.get("label-style")

    @ui_label_style.setter
    def ui_label_style(self, value):
        self._set_prop("label-style", value)

    @property
    def ui_square(self):
        """Apply a rectangle aspect to the FAB"""
        return self._props.get("square")

    @ui_square.setter
    def ui_square(self, value):
        self._set_prop("square", value)

    @property
    def ui_disable(self):
        return self._props.get("disable")

    @ui_disable.setter
    def ui_disable(self, value):
        self._set_prop("disable", value)

    @property
    def ui_tabindex(self):
        return self._props.get("tabindex")

    @ui_tabindex.setter
    def ui_tabindex(self, value):
        self._set_prop("tabindex", value)

    @property
    def ui_slot_active_icon(self):
        """Slot for icon shown when FAB is opened; Suggestion: QIcon"""
        return self.ui_slots.get("active-icon", [])

    @ui_slot_active_icon.setter
    def ui_slot_active_icon(self, value):
        self._set_slot("active-icon", value)

    @property
    def ui_slot_icon(self):
        """Slot for icon shown when FAB is closed; Suggestion: QIcon"""
        return self.ui_slots.get("icon", [])

    @ui_slot_icon.setter
    def ui_slot_icon(self, value):
        self._set_slot("icon", value)

    @property
    def ui_slot_label(self):
        """Slot for label"""
        return self.ui_slots.get("label", [])

    @ui_slot_label.setter
    def ui_slot_label(self, value):
        self._set_slot("label", value)

    @property
    def ui_slot_tooltip(self):
        """Slot specifically designed for a QTooltip"""
        return self.ui_slots.get("tooltip", [])

    @ui_slot_tooltip.setter
    def ui_slot_tooltip(self, value):
        self._set_slot("tooltip", value)

    def on_before_hide(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("before-hide", handler, arg)

    def on_before_show(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("before-show", handler, arg)

    def on_hide(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("hide", handler, arg)

    def on_show(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("show", handler, arg)

    def on_update_model_value(self, handler: Callable, arg: object = None):
        """
        Emitted when showing/hidden state changes; Is also used by v-model

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("update:model-value", handler, arg)

    def ui_hide(self):
        """Collapses fab actions list"""
        self._js_call_method("hide")

    def ui_show(self):
        """Expands fab actions list"""
        self._js_call_method("show")

    def ui_toggle(self):
        self._js_call_method("toggle")

    def _get_js_methods(self):
        return ["hide", "show", "toggle"]


class QFabAction(Component):
    """
    Quasar Component: `QFabAction <https://v2.quasar.dev/vue-components/floating-action-button>`__

    :param ui_icon:
    :param ui_anchor: How to align the Fab Action relative to Fab expand side; By default it uses the align specified in QFab
    :param ui_to: Equivalent to Vue Router <router-link> 'to' property
    :param ui_replace: Equivalent to Vue Router <router-link> 'replace' property
    :param ui_type: Define the button HTML DOM type
    :param ui_outline: Use 'outline' design for Fab button
    :param ui_push: Use 'push' design for Fab button
    :param ui_flat: Use 'flat' design for Fab button
    :param ui_unelevated: Remove shadow
    :param ui_padding: Apply custom padding (vertical [horizontal]); Size in CSS units, including unit name or standard size name (none|xs|sm|md|lg|xl); Also removes the min width and height when set
    :param ui_color:
    :param ui_text_color:
    :param ui_glossy: Apply the glossy effect over the button
    :param ui_external_label: Display label besides the FABs, as external content
    :param ui_label: The label that will be shown when Fab is extended
    :param ui_label_position: Position of the label around the icon
    :param ui_hide_label: Hide the label; Useful for animation purposes where you toggle the visibility of the label
    :param ui_label_class: Class definitions to be attributed to the label container
    :param ui_label_style: Style definitions to be attributed to the label container
    :param ui_square: Apply a rectangle aspect to the FAB
    :param ui_disable:
    :param ui_tabindex:
    """

    def __init__(
        self,
        *children,
        ui_icon: Any | None = None,
        ui_anchor: str | None = None,
        ui_to: str | dict | None = None,
        ui_replace: bool | None = None,
        ui_type: str | None = None,
        ui_outline: bool | None = None,
        ui_push: bool | None = None,
        ui_flat: bool | None = None,
        ui_unelevated: bool | None = None,
        ui_padding: str | None = None,
        ui_color: Any | None = None,
        ui_text_color: Any | None = None,
        ui_glossy: bool | None = None,
        ui_external_label: bool | None = None,
        ui_label: str | float | None = None,
        ui_label_position: str | None = None,
        ui_hide_label: bool | None = None,
        ui_label_class: str | list | dict | None = None,
        ui_label_style: str | list | dict | None = None,
        ui_square: bool | None = None,
        ui_disable: Any | None = None,
        ui_tabindex: Any | None = None,
        **kwargs,
    ):
        super().__init__("QFabAction", *children, **kwargs)
        if ui_icon is not None:
            self._props["icon"] = ui_icon
        if ui_anchor is not None:
            self._props["anchor"] = ui_anchor
        if ui_to is not None:
            self._props["to"] = ui_to
        if ui_replace is not None:
            self._props["replace"] = ui_replace
        if ui_type is not None:
            self._props["type"] = ui_type
        if ui_outline is not None:
            self._props["outline"] = ui_outline
        if ui_push is not None:
            self._props["push"] = ui_push
        if ui_flat is not None:
            self._props["flat"] = ui_flat
        if ui_unelevated is not None:
            self._props["unelevated"] = ui_unelevated
        if ui_padding is not None:
            self._props["padding"] = ui_padding
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_text_color is not None:
            self._props["text-color"] = ui_text_color
        if ui_glossy is not None:
            self._props["glossy"] = ui_glossy
        if ui_external_label is not None:
            self._props["external-label"] = ui_external_label
        if ui_label is not None:
            self._props["label"] = ui_label
        if ui_label_position is not None:
            self._props["label-position"] = ui_label_position
        if ui_hide_label is not None:
            self._props["hide-label"] = ui_hide_label
        if ui_label_class is not None:
            self._props["label-class"] = ui_label_class
        if ui_label_style is not None:
            self._props["label-style"] = ui_label_style
        if ui_square is not None:
            self._props["square"] = ui_square
        if ui_disable is not None:
            self._props["disable"] = ui_disable
        if ui_tabindex is not None:
            self._props["tabindex"] = ui_tabindex

    @property
    def ui_icon(self):
        return self._props.get("icon")

    @ui_icon.setter
    def ui_icon(self, value):
        self._set_prop("icon", value)

    @property
    def ui_anchor(self):
        """How to align the Fab Action relative to Fab expand side; By default it uses the align specified in QFab"""
        return self._props.get("anchor")

    @ui_anchor.setter
    def ui_anchor(self, value):
        self._set_prop("anchor", value)

    @property
    def ui_to(self):
        """Equivalent to Vue Router <router-link> 'to' property"""
        return self._props.get("to")

    @ui_to.setter
    def ui_to(self, value):
        self._set_prop("to", value)

    @property
    def ui_replace(self):
        """Equivalent to Vue Router <router-link> 'replace' property"""
        return self._props.get("replace")

    @ui_replace.setter
    def ui_replace(self, value):
        self._set_prop("replace", value)

    @property
    def ui_type(self):
        """Define the button HTML DOM type"""
        return self._props.get("type")

    @ui_type.setter
    def ui_type(self, value):
        self._set_prop("type", value)

    @property
    def ui_outline(self):
        """Use 'outline' design for Fab button"""
        return self._props.get("outline")

    @ui_outline.setter
    def ui_outline(self, value):
        self._set_prop("outline", value)

    @property
    def ui_push(self):
        """Use 'push' design for Fab button"""
        return self._props.get("push")

    @ui_push.setter
    def ui_push(self, value):
        self._set_prop("push", value)

    @property
    def ui_flat(self):
        """Use 'flat' design for Fab button"""
        return self._props.get("flat")

    @ui_flat.setter
    def ui_flat(self, value):
        self._set_prop("flat", value)

    @property
    def ui_unelevated(self):
        """Remove shadow"""
        return self._props.get("unelevated")

    @ui_unelevated.setter
    def ui_unelevated(self, value):
        self._set_prop("unelevated", value)

    @property
    def ui_padding(self):
        """Apply custom padding (vertical [horizontal]); Size in CSS units, including unit name or standard size name (none|xs|sm|md|lg|xl); Also removes the min width and height when set"""
        return self._props.get("padding")

    @ui_padding.setter
    def ui_padding(self, value):
        self._set_prop("padding", value)

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_text_color(self):
        return self._props.get("text-color")

    @ui_text_color.setter
    def ui_text_color(self, value):
        self._set_prop("text-color", value)

    @property
    def ui_glossy(self):
        """Apply the glossy effect over the button"""
        return self._props.get("glossy")

    @ui_glossy.setter
    def ui_glossy(self, value):
        self._set_prop("glossy", value)

    @property
    def ui_external_label(self):
        """Display label besides the FABs, as external content"""
        return self._props.get("external-label")

    @ui_external_label.setter
    def ui_external_label(self, value):
        self._set_prop("external-label", value)

    @property
    def ui_label(self):
        """The label that will be shown when Fab is extended"""
        return self._props.get("label")

    @ui_label.setter
    def ui_label(self, value):
        self._set_prop("label", value)

    @property
    def ui_label_position(self):
        """Position of the label around the icon"""
        return self._props.get("label-position")

    @ui_label_position.setter
    def ui_label_position(self, value):
        self._set_prop("label-position", value)

    @property
    def ui_hide_label(self):
        """Hide the label; Useful for animation purposes where you toggle the visibility of the label"""
        return self._props.get("hide-label")

    @ui_hide_label.setter
    def ui_hide_label(self, value):
        self._set_prop("hide-label", value)

    @property
    def ui_label_class(self):
        """Class definitions to be attributed to the label container"""
        return self._props.get("label-class")

    @ui_label_class.setter
    def ui_label_class(self, value):
        self._set_prop("label-class", value)

    @property
    def ui_label_style(self):
        """Style definitions to be attributed to the label container"""
        return self._props.get("label-style")

    @ui_label_style.setter
    def ui_label_style(self, value):
        self._set_prop("label-style", value)

    @property
    def ui_square(self):
        """Apply a rectangle aspect to the FAB"""
        return self._props.get("square")

    @ui_square.setter
    def ui_square(self, value):
        self._set_prop("square", value)

    @property
    def ui_disable(self):
        return self._props.get("disable")

    @ui_disable.setter
    def ui_disable(self, value):
        self._set_prop("disable", value)

    @property
    def ui_tabindex(self):
        return self._props.get("tabindex")

    @ui_tabindex.setter
    def ui_tabindex(self, value):
        self._set_prop("tabindex", value)

    @property
    def ui_slot_icon(self):
        """Slot for icon; Suggestion: QIcon"""
        return self.ui_slots.get("icon", [])

    @ui_slot_icon.setter
    def ui_slot_icon(self, value):
        self._set_slot("icon", value)

    @property
    def ui_slot_label(self):
        """Slot for label"""
        return self.ui_slots.get("label", [])

    @ui_slot_label.setter
    def ui_slot_label(self, value):
        self._set_slot("label", value)

    def on_click(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("click.stop", handler, arg)

    def ui_click(self, ui_evt=None):
        """Emulate click on QFabAction"""
        kwargs = {}
        if ui_evt is not None:
            kwargs["evt"] = ui_evt
        self._js_call_method("click", [kwargs])

    def _get_js_methods(self):
        return ["click"]


class QField(Component):
    """
    Quasar Component: `QField <https://v2.quasar.dev/vue-components/field>`__

    :param ui_maxlength: Specify a max length of model
    :param ui_tag:
    :param ui_label: A text label that will “float” up above the input field, once the field gets focus
    :param ui_stack_label: Label will be always shown above the field regardless of field content (if any)
    :param ui_hint: Helper (hint) text which gets placed below your wrapped form component
    :param ui_hide_hint: Hide the helper (hint) text when field doesn't have focus
    :param ui_prefix: Prefix
    :param ui_suffix: Suffix
    :param ui_label_color: Color name for the label from the Quasar Color Palette; Overrides the 'color' prop; The difference from 'color' prop is that the label will always have this color, even when field is not focused
    :param ui_color:
    :param ui_bg_color:
    :param ui_dark:
    :param ui_loading: Signals the user a process is in progress by displaying a spinner; Spinner can be customized by using the 'loading' slot.
    :param ui_clearable: Appends clearable icon when a value (not undefined or null) is set; When clicked, model becomes null
    :param ui_clear_icon: Custom icon to use for the clear button when using along with 'clearable' prop
    :param ui_filled: Use 'filled' design for the field
    :param ui_outlined: Use 'outlined' design for the field
    :param ui_borderless: Use 'borderless' design for the field
    :param ui_standout: Use 'standout' design for the field; Specifies classes to be applied when focused (overriding default ones)
    :param ui_label_slot: Enables label slot; You need to set it to force use of the 'label' slot if the 'label' prop is not set
    :param ui_bottom_slots: Enables bottom slots ('error', 'hint', 'counter')
    :param ui_hide_bottom_space: Do not reserve space for hint/error/counter anymore when these are not used; As a result, it also disables the animation for those; It also allows the hint/error area to stretch vertically based on its content
    :param ui_counter: Show an automatic counter on bottom right
    :param ui_rounded:
    :param ui_square: Remove border-radius so borders are squared; Overrides 'rounded' prop
    :param ui_dense:
    :param ui_item_aligned: Match inner content alignment to that of QItem
    :param ui_disable:
    :param ui_readonly:
    :param ui_autofocus: Focus field on initial component render
    :param ui_for: Used to specify the 'id' of the control and also the 'for' attribute of the label that wraps it; If no 'name' prop is specified, then it is used for this attribute as well
    :param ui_model_value: Model of the component; Either use this property (along with a listener for 'update:model-value' event) OR use v-model directive
    :param ui_error: Does field have validation errors?
    :param ui_error_message: Validation error message (gets displayed only if 'error' is set to 'true')
    :param ui_no_error_icon: Hide error icon when there is an error
    :param ui_rules: Array of Functions/Strings; If String, then it must be a name of one of the embedded validation rules
    :param ui_reactive_rules: By default a change in the rules does not trigger a new validation until the model changes; If set to true then a change in the rules will trigger a validation; Has a performance penalty, so use it only when you really need it
    :param ui_lazy_rules: If set to boolean true then it checks validation status against the 'rules' only after field loses focus for first time; If set to 'ondemand' then it will trigger only when component's validate() method is manually called or when the wrapper QForm submits itself
    """

    def __init__(
        self,
        *children,
        ui_maxlength: str | float | None = None,
        ui_tag: Any | None = None,
        ui_label: str | None = None,
        ui_stack_label: bool | None = None,
        ui_hint: str | None = None,
        ui_hide_hint: bool | None = None,
        ui_prefix: str | None = None,
        ui_suffix: str | None = None,
        ui_label_color: Any | None = None,
        ui_color: Any | None = None,
        ui_bg_color: Any | None = None,
        ui_dark: Any | None = None,
        ui_loading: bool | None = None,
        ui_clearable: bool | None = None,
        ui_clear_icon: str | None = None,
        ui_filled: bool | None = None,
        ui_outlined: bool | None = None,
        ui_borderless: bool | None = None,
        ui_standout: bool | str | None = None,
        ui_label_slot: bool | None = None,
        ui_bottom_slots: bool | None = None,
        ui_hide_bottom_space: bool | None = None,
        ui_counter: bool | None = None,
        ui_rounded: Any | None = None,
        ui_square: bool | None = None,
        ui_dense: Any | None = None,
        ui_item_aligned: bool | None = None,
        ui_disable: Any | None = None,
        ui_readonly: Any | None = None,
        ui_autofocus: bool | None = None,
        ui_for: str | None = None,
        ui_model_value: Any | None = None,
        ui_error: bool | None = None,
        ui_error_message: str | None = None,
        ui_no_error_icon: bool | None = None,
        ui_rules: list | None = None,
        ui_reactive_rules: bool | None = None,
        ui_lazy_rules: bool | str | None = None,
        **kwargs,
    ):
        super().__init__("QField", *children, **kwargs)
        self.on("update:model-value", self.__update_model_value)

        if ui_maxlength is not None:
            self._props["maxlength"] = ui_maxlength
        if ui_tag is not None:
            self._props["tag"] = ui_tag
        if ui_label is not None:
            self._props["label"] = ui_label
        if ui_stack_label is not None:
            self._props["stack-label"] = ui_stack_label
        if ui_hint is not None:
            self._props["hint"] = ui_hint
        if ui_hide_hint is not None:
            self._props["hide-hint"] = ui_hide_hint
        if ui_prefix is not None:
            self._props["prefix"] = ui_prefix
        if ui_suffix is not None:
            self._props["suffix"] = ui_suffix
        if ui_label_color is not None:
            self._props["label-color"] = ui_label_color
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_bg_color is not None:
            self._props["bg-color"] = ui_bg_color
        if ui_dark is not None:
            self._props["dark"] = ui_dark
        if ui_loading is not None:
            self._props["loading"] = ui_loading
        if ui_clearable is not None:
            self._props["clearable"] = ui_clearable
        if ui_clear_icon is not None:
            self._props["clear-icon"] = ui_clear_icon
        if ui_filled is not None:
            self._props["filled"] = ui_filled
        if ui_outlined is not None:
            self._props["outlined"] = ui_outlined
        if ui_borderless is not None:
            self._props["borderless"] = ui_borderless
        if ui_standout is not None:
            self._props["standout"] = ui_standout
        if ui_label_slot is not None:
            self._props["label-slot"] = ui_label_slot
        if ui_bottom_slots is not None:
            self._props["bottom-slots"] = ui_bottom_slots
        if ui_hide_bottom_space is not None:
            self._props["hide-bottom-space"] = ui_hide_bottom_space
        if ui_counter is not None:
            self._props["counter"] = ui_counter
        if ui_rounded is not None:
            self._props["rounded"] = ui_rounded
        if ui_square is not None:
            self._props["square"] = ui_square
        if ui_dense is not None:
            self._props["dense"] = ui_dense
        if ui_item_aligned is not None:
            self._props["item-aligned"] = ui_item_aligned
        if ui_disable is not None:
            self._props["disable"] = ui_disable
        if ui_readonly is not None:
            self._props["readonly"] = ui_readonly
        if ui_autofocus is not None:
            self._props["autofocus"] = ui_autofocus
        if ui_for is not None:
            self._props["for"] = ui_for
        if ui_model_value is not None:
            self._props["model-value"] = ui_model_value
        if ui_error is not None:
            self._props["error"] = ui_error
        if ui_error_message is not None:
            self._props["error-message"] = ui_error_message
        if ui_no_error_icon is not None:
            self._props["no-error-icon"] = ui_no_error_icon

        self._rules = [] if ui_rules is None else ui_rules
        self._rules_registered = False
        if self._rules:
            self._rules_registered = True
            self.on_update_model_value(self._validate_rules)

        if ui_reactive_rules is not None:
            self._props["reactive-rules"] = ui_reactive_rules
        if ui_lazy_rules is not None:
            self._props["lazy-rules"] = ui_lazy_rules

    def __update_model_value(self, event: Event):
        self._set_prop("model-value", event.value)

    @property
    def ui_maxlength(self):
        """Specify a max length of model"""
        return self._props.get("maxlength")

    @ui_maxlength.setter
    def ui_maxlength(self, value):
        self._set_prop("maxlength", value)

    @property
    def ui_tag(self):
        return self._props.get("tag")

    @ui_tag.setter
    def ui_tag(self, value):
        self._set_prop("tag", value)

    @property
    def ui_label(self):
        """A text label that will “float” up above the input field, once the field gets focus"""
        return self._props.get("label")

    @ui_label.setter
    def ui_label(self, value):
        self._set_prop("label", value)

    @property
    def ui_stack_label(self):
        """Label will be always shown above the field regardless of field content (if any)"""
        return self._props.get("stack-label")

    @ui_stack_label.setter
    def ui_stack_label(self, value):
        self._set_prop("stack-label", value)

    @property
    def ui_hint(self):
        """Helper (hint) text which gets placed below your wrapped form component"""
        return self._props.get("hint")

    @ui_hint.setter
    def ui_hint(self, value):
        self._set_prop("hint", value)

    @property
    def ui_hide_hint(self):
        """Hide the helper (hint) text when field doesn't have focus"""
        return self._props.get("hide-hint")

    @ui_hide_hint.setter
    def ui_hide_hint(self, value):
        self._set_prop("hide-hint", value)

    @property
    def ui_prefix(self):
        """Prefix"""
        return self._props.get("prefix")

    @ui_prefix.setter
    def ui_prefix(self, value):
        self._set_prop("prefix", value)

    @property
    def ui_suffix(self):
        """Suffix"""
        return self._props.get("suffix")

    @ui_suffix.setter
    def ui_suffix(self, value):
        self._set_prop("suffix", value)

    @property
    def ui_label_color(self):
        """Color name for the label from the Quasar Color Palette; Overrides the 'color' prop; The difference from 'color' prop is that the label will always have this color, even when field is not focused"""
        return self._props.get("label-color")

    @ui_label_color.setter
    def ui_label_color(self, value):
        self._set_prop("label-color", value)

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_bg_color(self):
        return self._props.get("bg-color")

    @ui_bg_color.setter
    def ui_bg_color(self, value):
        self._set_prop("bg-color", value)

    @property
    def ui_dark(self):
        return self._props.get("dark")

    @ui_dark.setter
    def ui_dark(self, value):
        self._set_prop("dark", value)

    @property
    def ui_loading(self):
        """Signals the user a process is in progress by displaying a spinner; Spinner can be customized by using the 'loading' slot."""
        return self._props.get("loading")

    @ui_loading.setter
    def ui_loading(self, value):
        self._set_prop("loading", value)

    @property
    def ui_clearable(self):
        """Appends clearable icon when a value (not undefined or null) is set; When clicked, model becomes null"""
        return self._props.get("clearable")

    @ui_clearable.setter
    def ui_clearable(self, value):
        self._set_prop("clearable", value)

    @property
    def ui_clear_icon(self):
        """Custom icon to use for the clear button when using along with 'clearable' prop"""
        return self._props.get("clear-icon")

    @ui_clear_icon.setter
    def ui_clear_icon(self, value):
        self._set_prop("clear-icon", value)

    @property
    def ui_filled(self):
        """Use 'filled' design for the field"""
        return self._props.get("filled")

    @ui_filled.setter
    def ui_filled(self, value):
        self._set_prop("filled", value)

    @property
    def ui_outlined(self):
        """Use 'outlined' design for the field"""
        return self._props.get("outlined")

    @ui_outlined.setter
    def ui_outlined(self, value):
        self._set_prop("outlined", value)

    @property
    def ui_borderless(self):
        """Use 'borderless' design for the field"""
        return self._props.get("borderless")

    @ui_borderless.setter
    def ui_borderless(self, value):
        self._set_prop("borderless", value)

    @property
    def ui_standout(self):
        """Use 'standout' design for the field; Specifies classes to be applied when focused (overriding default ones)"""
        return self._props.get("standout")

    @ui_standout.setter
    def ui_standout(self, value):
        self._set_prop("standout", value)

    @property
    def ui_label_slot(self):
        """Enables label slot; You need to set it to force use of the 'label' slot if the 'label' prop is not set"""
        return self._props.get("label-slot")

    @ui_label_slot.setter
    def ui_label_slot(self, value):
        self._set_prop("label-slot", value)

    @property
    def ui_bottom_slots(self):
        """Enables bottom slots ('error', 'hint', 'counter')"""
        return self._props.get("bottom-slots")

    @ui_bottom_slots.setter
    def ui_bottom_slots(self, value):
        self._set_prop("bottom-slots", value)

    @property
    def ui_hide_bottom_space(self):
        """Do not reserve space for hint/error/counter anymore when these are not used; As a result, it also disables the animation for those; It also allows the hint/error area to stretch vertically based on its content"""
        return self._props.get("hide-bottom-space")

    @ui_hide_bottom_space.setter
    def ui_hide_bottom_space(self, value):
        self._set_prop("hide-bottom-space", value)

    @property
    def ui_counter(self):
        """Show an automatic counter on bottom right"""
        return self._props.get("counter")

    @ui_counter.setter
    def ui_counter(self, value):
        self._set_prop("counter", value)

    @property
    def ui_rounded(self):
        return self._props.get("rounded")

    @ui_rounded.setter
    def ui_rounded(self, value):
        self._set_prop("rounded", value)

    @property
    def ui_square(self):
        """Remove border-radius so borders are squared; Overrides 'rounded' prop"""
        return self._props.get("square")

    @ui_square.setter
    def ui_square(self, value):
        self._set_prop("square", value)

    @property
    def ui_dense(self):
        return self._props.get("dense")

    @ui_dense.setter
    def ui_dense(self, value):
        self._set_prop("dense", value)

    @property
    def ui_item_aligned(self):
        """Match inner content alignment to that of QItem"""
        return self._props.get("item-aligned")

    @ui_item_aligned.setter
    def ui_item_aligned(self, value):
        self._set_prop("item-aligned", value)

    @property
    def ui_disable(self):
        return self._props.get("disable")

    @ui_disable.setter
    def ui_disable(self, value):
        self._set_prop("disable", value)

    @property
    def ui_readonly(self):
        return self._props.get("readonly")

    @ui_readonly.setter
    def ui_readonly(self, value):
        self._set_prop("readonly", value)

    @property
    def ui_autofocus(self):
        """Focus field on initial component render"""
        return self._props.get("autofocus")

    @ui_autofocus.setter
    def ui_autofocus(self, value):
        self._set_prop("autofocus", value)

    @property
    def ui_for(self):
        """Used to specify the 'id' of the control and also the 'for' attribute of the label that wraps it; If no 'name' prop is specified, then it is used for this attribute as well"""
        return self._props.get("for")

    @ui_for.setter
    def ui_for(self, value):
        self._set_prop("for", value)

    @property
    def ui_model_value(self):
        """Model of the component; Either use this property (along with a listener for 'update:model-value' event) OR use v-model directive"""
        return self._props.get("model-value")

    @ui_model_value.setter
    def ui_model_value(self, value):
        self._set_prop("model-value", value)

    @property
    def ui_error(self):
        """Does field have validation errors?"""
        return self._props.get("error")

    @ui_error.setter
    def ui_error(self, value):
        self._set_prop("error", value)

    @property
    def ui_error_message(self):
        """Validation error message (gets displayed only if 'error' is set to 'true')"""
        return self._props.get("error-message")

    @ui_error_message.setter
    def ui_error_message(self, value):
        self._set_prop("error-message", value)

    @property
    def ui_no_error_icon(self):
        """Hide error icon when there is an error"""
        return self._props.get("no-error-icon")

    @ui_no_error_icon.setter
    def ui_no_error_icon(self, value):
        self._set_prop("no-error-icon", value)

    @property
    def ui_rules(self):
        """Array of Functions/Strings; If String, then it must be a name of one of the embedded validation rules"""
        return self._rules

    @ui_rules.setter
    def ui_rules(self, value):
        self._rules = value
        if self._rules and not self._rules_registered:
            self._rules_registered = True
            self.on_update_model_value(self._validate_rules)

    def _validate_rules(self):
        for rule in self.ui_rules:
            value = rule(self.ui_model_value)
            if isinstance(value, str) and value != "":
                self.ui_error_message = value
                self.ui_error = True
                return
        self.ui_error = None

    @property
    def ui_reactive_rules(self):
        """By default a change in the rules does not trigger a new validation until the model changes; If set to true then a change in the rules will trigger a validation; Has a performance penalty, so use it only when you really need it"""
        return self._props.get("reactive-rules")

    @ui_reactive_rules.setter
    def ui_reactive_rules(self, value):
        self._set_prop("reactive-rules", value)

    @property
    def ui_lazy_rules(self):
        """If set to boolean true then it checks validation status against the 'rules' only after field loses focus for first time; If set to 'ondemand' then it will trigger only when component's validate() method is manually called or when the wrapper QForm submits itself"""
        return self._props.get("lazy-rules")

    @ui_lazy_rules.setter
    def ui_lazy_rules(self, value):
        self._set_prop("lazy-rules", value)

    @property
    def ui_slot_after(self):
        """Append outer field; Suggestions: QIcon, QBtn"""
        return self.ui_slots.get("after", [])

    @ui_slot_after.setter
    def ui_slot_after(self, value):
        self._set_slot("after", value)

    @property
    def ui_slot_append(self):
        """Append to inner field; Suggestions: QIcon, QBtn"""
        return self.ui_slots.get("append", [])

    @ui_slot_append.setter
    def ui_slot_append(self, value):
        self._set_slot("append", value)

    @property
    def ui_slot_before(self):
        """Prepend outer field; Suggestions: QIcon, QBtn"""
        return self.ui_slots.get("before", [])

    @ui_slot_before.setter
    def ui_slot_before(self, value):
        self._set_slot("before", value)

    @property
    def ui_slot_control(self):
        """Slot for controls; Suggestion QSlider, QRange, QKnob, ..."""
        return self.ui_slots.get("control", [])

    @ui_slot_control.setter
    def ui_slot_control(self, value):
        self._set_slot("control", value)

    @property
    def ui_slot_counter(self):
        """Slot for counter text; Enabled only if 'bottom-slots' prop is used; Suggestion: <div>"""
        return self.ui_slots.get("counter", [])

    @ui_slot_counter.setter
    def ui_slot_counter(self, value):
        self._set_slot("counter", value)

    @property
    def ui_slot_error(self):
        """Slot for errors; Enabled only if 'bottom-slots' prop is used; Suggestion: <div>"""
        return self.ui_slots.get("error", [])

    @ui_slot_error.setter
    def ui_slot_error(self, value):
        self._set_slot("error", value)

    @property
    def ui_slot_hint(self):
        """Slot for hint text; Enabled only if 'bottom-slots' prop is used; Suggestion: <div>"""
        return self.ui_slots.get("hint", [])

    @ui_slot_hint.setter
    def ui_slot_hint(self, value):
        self._set_slot("hint", value)

    @property
    def ui_slot_label(self):
        """Slot for label; Used only if 'label-slot' prop is set or the 'label' prop is set; When it is used the text in the 'label' prop is ignored"""
        return self.ui_slots.get("label", [])

    @ui_slot_label.setter
    def ui_slot_label(self, value):
        self._set_slot("label", value)

    @property
    def ui_slot_loading(self):
        """Override default spinner when component is in loading mode; Use in conjunction with 'loading' prop"""
        return self.ui_slots.get("loading", [])

    @ui_slot_loading.setter
    def ui_slot_loading(self, value):
        self._set_slot("loading", value)

    @property
    def ui_slot_prepend(self):
        """Prepend inner field; Suggestions: QIcon, QBtn"""
        return self.ui_slots.get("prepend", [])

    @ui_slot_prepend.setter
    def ui_slot_prepend(self, value):
        self._set_slot("prepend", value)

    @property
    def ui_slot_rawControl(self):
        return self.ui_slots.get("rawControl", [])

    @ui_slot_rawControl.setter
    def ui_slot_rawControl(self, value):
        self._set_slot("rawControl", value)

    def on_blur(self, handler: Callable, arg: object = None):
        """
        Emitted when component loses focus

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("blur", handler, arg)

    def on_clear(self, handler: Callable, arg: object = None):
        """
        When using the 'clearable' property, this event is emitted when the clear icon is clicked

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("clear", handler, arg)

    def on_focus(self, handler: Callable, arg: object = None):
        """
        Emitted when component gets focused

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("focus", handler, arg)

    def on_update_model_value(self, handler: Callable, arg: object = None):
        """
        Emitted when the model changes, only when used with 'clearable' or the 'control' scoped slot.

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("update:model-value", handler, arg)

    def ui_blur(self):
        """Blur component (lose focus)"""
        self._js_call_method("blur")

    def ui_focus(self):
        """Focus component"""
        self._js_call_method("focus")

    def ui_resetValidation(self):
        """Reset validation status"""
        self._js_call_method("resetValidation")

    def ui_validate(self, ui_value=None):
        """Trigger a validation"""
        kwargs = {}
        if ui_value is not None:
            kwargs["value"] = ui_value
        self._js_call_method("validate", [kwargs])

    def _get_js_methods(self):
        return ["blur", "focus", "resetValidation", "validate"]


class QFile(Component):
    """
    Quasar Component: `QFile <https://v2.quasar.dev/vue-components/file>`__

    :param ui_model_value: Model of the component; Either use this property (along with a listener for 'update:model-value' event) OR use v-model directive
    :param ui_append: Append file(s) to current model rather than replacing them; Has effect only when using 'multiple' mode
    :param ui_display_value: Override default selection string, if not using 'file' or 'selected' scoped slots and if not using 'use-chips' prop
    :param ui_use_chips: Use QChip to show picked files
    :param ui_counter_label: Label for the counter; The 'counter' prop is necessary to enable this one
    :param ui_tabindex:
    :param ui_input_class: Class definitions to be attributed to the underlying selection container
    :param ui_input_style: Style definitions to be attributed to the underlying selection container
    :param ui_name: Used to specify the name of the control; Useful if dealing with forms submitted directly to a URL
    :param ui_label: A text label that will “float” up above the input field, once the field gets focus
    :param ui_stack_label: Label will be always shown above the field regardless of field content (if any)
    :param ui_hint: Helper (hint) text which gets placed below your wrapped form component
    :param ui_hide_hint: Hide the helper (hint) text when field doesn't have focus
    :param ui_prefix: Prefix
    :param ui_suffix: Suffix
    :param ui_label_color: Color name for the label from the Quasar Color Palette; Overrides the 'color' prop; The difference from 'color' prop is that the label will always have this color, even when field is not focused
    :param ui_color:
    :param ui_bg_color:
    :param ui_dark:
    :param ui_loading: Signals the user a process is in progress by displaying a spinner; Spinner can be customized by using the 'loading' slot.
    :param ui_clearable: Appends clearable icon when a value (not undefined or null) is set; When clicked, model becomes null
    :param ui_clear_icon: Custom icon to use for the clear button when using along with 'clearable' prop
    :param ui_filled: Use 'filled' design for the field
    :param ui_outlined: Use 'outlined' design for the field
    :param ui_borderless: Use 'borderless' design for the field
    :param ui_standout: Use 'standout' design for the field; Specifies classes to be applied when focused (overriding default ones)
    :param ui_label_slot: Enables label slot; You need to set it to force use of the 'label' slot if the 'label' prop is not set
    :param ui_bottom_slots: Enables bottom slots ('error', 'hint', 'counter')
    :param ui_hide_bottom_space: Do not reserve space for hint/error/counter anymore when these are not used; As a result, it also disables the animation for those; It also allows the hint/error area to stretch vertically based on its content
    :param ui_counter: Show an automatic counter on bottom right
    :param ui_rounded:
    :param ui_square: Remove border-radius so borders are squared; Overrides 'rounded' prop
    :param ui_dense:
    :param ui_item_aligned: Match inner content alignment to that of QItem
    :param ui_disable:
    :param ui_readonly:
    :param ui_autofocus: Focus field on initial component render
    :param ui_for: Used to specify the 'id' of the control and also the 'for' attribute of the label that wraps it; If no 'name' prop is specified, then it is used for this attribute as well
    :param ui_error: Does field have validation errors?
    :param ui_error_message: Validation error message (gets displayed only if 'error' is set to 'true')
    :param ui_no_error_icon: Hide error icon when there is an error
    :param ui_rules: Array of Functions/Strings; If String, then it must be a name of one of the embedded validation rules
    :param ui_reactive_rules: By default a change in the rules does not trigger a new validation until the model changes; If set to true then a change in the rules will trigger a validation; Has a performance penalty, so use it only when you really need it
    :param ui_lazy_rules: If set to boolean true then it checks validation status against the 'rules' only after field loses focus for first time; If set to 'ondemand' then it will trigger only when component's validate() method is manually called or when the wrapper QForm submits itself
    :param ui_multiple: Allow multiple file uploads
    :param ui_accept: Comma separated list of unique file type specifiers. Maps to 'accept' attribute of native input type=file element
    :param ui_capture: Optionally, specify that a new file should be captured, and which device should be used to capture that new media of a type defined by the 'accept' prop. Maps to 'capture' attribute of native input type=file element
    :param ui_max_file_size: Maximum size of individual file in bytes
    :param ui_max_total_size: Maximum size of all files combined in bytes
    :param ui_max_files: Maximum number of files to contain
    :param ui_filter: Custom filter for added files; Only files that pass this filter will be added to the queue and uploaded; For best performance, reference it from your scope and do not define it inline
    """

    def __init__(
        self,
        *children,
        ui_model_value: Any | None = None,
        ui_append: bool | None = None,
        ui_display_value: float | str | None = None,
        ui_use_chips: bool | None = None,
        ui_counter_label: Callable | None = None,
        ui_tabindex: Any | None = None,
        ui_input_class: str | list | dict | None = None,
        ui_input_style: str | list | dict | None = None,
        ui_name: str | None = None,
        ui_label: str | None = None,
        ui_stack_label: bool | None = None,
        ui_hint: str | None = None,
        ui_hide_hint: bool | None = None,
        ui_prefix: str | None = None,
        ui_suffix: str | None = None,
        ui_label_color: Any | None = None,
        ui_color: Any | None = None,
        ui_bg_color: Any | None = None,
        ui_dark: Any | None = None,
        ui_loading: bool | None = None,
        ui_clearable: bool | None = None,
        ui_clear_icon: str | None = None,
        ui_filled: bool | None = None,
        ui_outlined: bool | None = None,
        ui_borderless: bool | None = None,
        ui_standout: bool | str | None = None,
        ui_label_slot: bool | None = None,
        ui_bottom_slots: bool | None = None,
        ui_hide_bottom_space: bool | None = None,
        ui_counter: bool | None = None,
        ui_rounded: Any | None = None,
        ui_square: bool | None = None,
        ui_dense: Any | None = None,
        ui_item_aligned: bool | None = None,
        ui_disable: Any | None = None,
        ui_readonly: Any | None = None,
        ui_autofocus: bool | None = None,
        ui_for: str | None = None,
        ui_error: bool | None = None,
        ui_error_message: str | None = None,
        ui_no_error_icon: bool | None = None,
        ui_rules: list | None = None,
        ui_reactive_rules: bool | None = None,
        ui_lazy_rules: bool | str | None = None,
        ui_multiple: bool | None = None,
        ui_accept: str | None = None,
        ui_capture: str | None = None,
        ui_max_file_size: float | str | None = None,
        ui_max_total_size: float | str | None = None,
        ui_max_files: float | str | None = None,
        ui_filter: Callable | None = None,
        **kwargs,
    ):
        super().__init__("QFile", *children, **kwargs)
        self.on("update:model-value", self.__update_model_value)

        if ui_model_value is not None:
            self._props["model-value"] = ui_model_value
        if ui_append is not None:
            self._props["append"] = ui_append
        if ui_display_value is not None:
            self._props["display-value"] = ui_display_value
        if ui_use_chips is not None:
            self._props["use-chips"] = ui_use_chips
        if ui_counter_label is not None:
            self._props["counter-label"] = ui_counter_label
        if ui_tabindex is not None:
            self._props["tabindex"] = ui_tabindex
        if ui_input_class is not None:
            self._props["input-class"] = ui_input_class
        if ui_input_style is not None:
            self._props["input-style"] = ui_input_style
        if ui_name is not None:
            self._props["name"] = ui_name
        if ui_label is not None:
            self._props["label"] = ui_label
        if ui_stack_label is not None:
            self._props["stack-label"] = ui_stack_label
        if ui_hint is not None:
            self._props["hint"] = ui_hint
        if ui_hide_hint is not None:
            self._props["hide-hint"] = ui_hide_hint
        if ui_prefix is not None:
            self._props["prefix"] = ui_prefix
        if ui_suffix is not None:
            self._props["suffix"] = ui_suffix
        if ui_label_color is not None:
            self._props["label-color"] = ui_label_color
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_bg_color is not None:
            self._props["bg-color"] = ui_bg_color
        if ui_dark is not None:
            self._props["dark"] = ui_dark
        if ui_loading is not None:
            self._props["loading"] = ui_loading
        if ui_clearable is not None:
            self._props["clearable"] = ui_clearable
        if ui_clear_icon is not None:
            self._props["clear-icon"] = ui_clear_icon
        if ui_filled is not None:
            self._props["filled"] = ui_filled
        if ui_outlined is not None:
            self._props["outlined"] = ui_outlined
        if ui_borderless is not None:
            self._props["borderless"] = ui_borderless
        if ui_standout is not None:
            self._props["standout"] = ui_standout
        if ui_label_slot is not None:
            self._props["label-slot"] = ui_label_slot
        if ui_bottom_slots is not None:
            self._props["bottom-slots"] = ui_bottom_slots
        if ui_hide_bottom_space is not None:
            self._props["hide-bottom-space"] = ui_hide_bottom_space
        if ui_counter is not None:
            self._props["counter"] = ui_counter
        if ui_rounded is not None:
            self._props["rounded"] = ui_rounded
        if ui_square is not None:
            self._props["square"] = ui_square
        if ui_dense is not None:
            self._props["dense"] = ui_dense
        if ui_item_aligned is not None:
            self._props["item-aligned"] = ui_item_aligned
        if ui_disable is not None:
            self._props["disable"] = ui_disable
        if ui_readonly is not None:
            self._props["readonly"] = ui_readonly
        if ui_autofocus is not None:
            self._props["autofocus"] = ui_autofocus
        if ui_for is not None:
            self._props["for"] = ui_for
        if ui_error is not None:
            self._props["error"] = ui_error
        if ui_error_message is not None:
            self._props["error-message"] = ui_error_message
        if ui_no_error_icon is not None:
            self._props["no-error-icon"] = ui_no_error_icon

        self._rules = [] if ui_rules is None else ui_rules
        self._rules_registered = False
        if self._rules:
            self._rules_registered = True
            self.on_update_model_value(self._validate_rules)

        if ui_reactive_rules is not None:
            self._props["reactive-rules"] = ui_reactive_rules
        if ui_lazy_rules is not None:
            self._props["lazy-rules"] = ui_lazy_rules
        if ui_multiple is not None:
            self._props["multiple"] = ui_multiple
        if ui_accept is not None:
            self._props["accept"] = ui_accept
        if ui_capture is not None:
            self._props["capture"] = ui_capture
        if ui_max_file_size is not None:
            self._props["max-file-size"] = ui_max_file_size
        if ui_max_total_size is not None:
            self._props["max-total-size"] = ui_max_total_size
        if ui_max_files is not None:
            self._props["max-files"] = ui_max_files
        if ui_filter is not None:
            self._props["filter"] = ui_filter

    def __update_model_value(self, event: Event):
        self._set_prop("model-value", event.value)

    @property
    def ui_model_value(self):
        """Model of the component; Either use this property (along with a listener for 'update:model-value' event) OR use v-model directive"""
        return self._props.get("model-value")

    @ui_model_value.setter
    def ui_model_value(self, value):
        self._set_prop("model-value", value)

    @property
    def ui_append(self):
        """Append file(s) to current model rather than replacing them; Has effect only when using 'multiple' mode"""
        return self._props.get("append")

    @ui_append.setter
    def ui_append(self, value):
        self._set_prop("append", value)

    @property
    def ui_display_value(self):
        """Override default selection string, if not using 'file' or 'selected' scoped slots and if not using 'use-chips' prop"""
        return self._props.get("display-value")

    @ui_display_value.setter
    def ui_display_value(self, value):
        self._set_prop("display-value", value)

    @property
    def ui_use_chips(self):
        """Use QChip to show picked files"""
        return self._props.get("use-chips")

    @ui_use_chips.setter
    def ui_use_chips(self, value):
        self._set_prop("use-chips", value)

    @property
    def ui_counter_label(self):
        """Label for the counter; The 'counter' prop is necessary to enable this one"""
        return self._props.get("counter-label")

    @ui_counter_label.setter
    def ui_counter_label(self, value):
        self._set_prop("counter-label", value)

    @property
    def ui_tabindex(self):
        return self._props.get("tabindex")

    @ui_tabindex.setter
    def ui_tabindex(self, value):
        self._set_prop("tabindex", value)

    @property
    def ui_input_class(self):
        """Class definitions to be attributed to the underlying selection container"""
        return self._props.get("input-class")

    @ui_input_class.setter
    def ui_input_class(self, value):
        self._set_prop("input-class", value)

    @property
    def ui_input_style(self):
        """Style definitions to be attributed to the underlying selection container"""
        return self._props.get("input-style")

    @ui_input_style.setter
    def ui_input_style(self, value):
        self._set_prop("input-style", value)

    @property
    def ui_name(self):
        """Used to specify the name of the control; Useful if dealing with forms submitted directly to a URL"""
        return self._props.get("name")

    @ui_name.setter
    def ui_name(self, value):
        self._set_prop("name", value)

    @property
    def ui_label(self):
        """A text label that will “float” up above the input field, once the field gets focus"""
        return self._props.get("label")

    @ui_label.setter
    def ui_label(self, value):
        self._set_prop("label", value)

    @property
    def ui_stack_label(self):
        """Label will be always shown above the field regardless of field content (if any)"""
        return self._props.get("stack-label")

    @ui_stack_label.setter
    def ui_stack_label(self, value):
        self._set_prop("stack-label", value)

    @property
    def ui_hint(self):
        """Helper (hint) text which gets placed below your wrapped form component"""
        return self._props.get("hint")

    @ui_hint.setter
    def ui_hint(self, value):
        self._set_prop("hint", value)

    @property
    def ui_hide_hint(self):
        """Hide the helper (hint) text when field doesn't have focus"""
        return self._props.get("hide-hint")

    @ui_hide_hint.setter
    def ui_hide_hint(self, value):
        self._set_prop("hide-hint", value)

    @property
    def ui_prefix(self):
        """Prefix"""
        return self._props.get("prefix")

    @ui_prefix.setter
    def ui_prefix(self, value):
        self._set_prop("prefix", value)

    @property
    def ui_suffix(self):
        """Suffix"""
        return self._props.get("suffix")

    @ui_suffix.setter
    def ui_suffix(self, value):
        self._set_prop("suffix", value)

    @property
    def ui_label_color(self):
        """Color name for the label from the Quasar Color Palette; Overrides the 'color' prop; The difference from 'color' prop is that the label will always have this color, even when field is not focused"""
        return self._props.get("label-color")

    @ui_label_color.setter
    def ui_label_color(self, value):
        self._set_prop("label-color", value)

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_bg_color(self):
        return self._props.get("bg-color")

    @ui_bg_color.setter
    def ui_bg_color(self, value):
        self._set_prop("bg-color", value)

    @property
    def ui_dark(self):
        return self._props.get("dark")

    @ui_dark.setter
    def ui_dark(self, value):
        self._set_prop("dark", value)

    @property
    def ui_loading(self):
        """Signals the user a process is in progress by displaying a spinner; Spinner can be customized by using the 'loading' slot."""
        return self._props.get("loading")

    @ui_loading.setter
    def ui_loading(self, value):
        self._set_prop("loading", value)

    @property
    def ui_clearable(self):
        """Appends clearable icon when a value (not undefined or null) is set; When clicked, model becomes null"""
        return self._props.get("clearable")

    @ui_clearable.setter
    def ui_clearable(self, value):
        self._set_prop("clearable", value)

    @property
    def ui_clear_icon(self):
        """Custom icon to use for the clear button when using along with 'clearable' prop"""
        return self._props.get("clear-icon")

    @ui_clear_icon.setter
    def ui_clear_icon(self, value):
        self._set_prop("clear-icon", value)

    @property
    def ui_filled(self):
        """Use 'filled' design for the field"""
        return self._props.get("filled")

    @ui_filled.setter
    def ui_filled(self, value):
        self._set_prop("filled", value)

    @property
    def ui_outlined(self):
        """Use 'outlined' design for the field"""
        return self._props.get("outlined")

    @ui_outlined.setter
    def ui_outlined(self, value):
        self._set_prop("outlined", value)

    @property
    def ui_borderless(self):
        """Use 'borderless' design for the field"""
        return self._props.get("borderless")

    @ui_borderless.setter
    def ui_borderless(self, value):
        self._set_prop("borderless", value)

    @property
    def ui_standout(self):
        """Use 'standout' design for the field; Specifies classes to be applied when focused (overriding default ones)"""
        return self._props.get("standout")

    @ui_standout.setter
    def ui_standout(self, value):
        self._set_prop("standout", value)

    @property
    def ui_label_slot(self):
        """Enables label slot; You need to set it to force use of the 'label' slot if the 'label' prop is not set"""
        return self._props.get("label-slot")

    @ui_label_slot.setter
    def ui_label_slot(self, value):
        self._set_prop("label-slot", value)

    @property
    def ui_bottom_slots(self):
        """Enables bottom slots ('error', 'hint', 'counter')"""
        return self._props.get("bottom-slots")

    @ui_bottom_slots.setter
    def ui_bottom_slots(self, value):
        self._set_prop("bottom-slots", value)

    @property
    def ui_hide_bottom_space(self):
        """Do not reserve space for hint/error/counter anymore when these are not used; As a result, it also disables the animation for those; It also allows the hint/error area to stretch vertically based on its content"""
        return self._props.get("hide-bottom-space")

    @ui_hide_bottom_space.setter
    def ui_hide_bottom_space(self, value):
        self._set_prop("hide-bottom-space", value)

    @property
    def ui_counter(self):
        """Show an automatic counter on bottom right"""
        return self._props.get("counter")

    @ui_counter.setter
    def ui_counter(self, value):
        self._set_prop("counter", value)

    @property
    def ui_rounded(self):
        return self._props.get("rounded")

    @ui_rounded.setter
    def ui_rounded(self, value):
        self._set_prop("rounded", value)

    @property
    def ui_square(self):
        """Remove border-radius so borders are squared; Overrides 'rounded' prop"""
        return self._props.get("square")

    @ui_square.setter
    def ui_square(self, value):
        self._set_prop("square", value)

    @property
    def ui_dense(self):
        return self._props.get("dense")

    @ui_dense.setter
    def ui_dense(self, value):
        self._set_prop("dense", value)

    @property
    def ui_item_aligned(self):
        """Match inner content alignment to that of QItem"""
        return self._props.get("item-aligned")

    @ui_item_aligned.setter
    def ui_item_aligned(self, value):
        self._set_prop("item-aligned", value)

    @property
    def ui_disable(self):
        return self._props.get("disable")

    @ui_disable.setter
    def ui_disable(self, value):
        self._set_prop("disable", value)

    @property
    def ui_readonly(self):
        return self._props.get("readonly")

    @ui_readonly.setter
    def ui_readonly(self, value):
        self._set_prop("readonly", value)

    @property
    def ui_autofocus(self):
        """Focus field on initial component render"""
        return self._props.get("autofocus")

    @ui_autofocus.setter
    def ui_autofocus(self, value):
        self._set_prop("autofocus", value)

    @property
    def ui_for(self):
        """Used to specify the 'id' of the control and also the 'for' attribute of the label that wraps it; If no 'name' prop is specified, then it is used for this attribute as well"""
        return self._props.get("for")

    @ui_for.setter
    def ui_for(self, value):
        self._set_prop("for", value)

    @property
    def ui_error(self):
        """Does field have validation errors?"""
        return self._props.get("error")

    @ui_error.setter
    def ui_error(self, value):
        self._set_prop("error", value)

    @property
    def ui_error_message(self):
        """Validation error message (gets displayed only if 'error' is set to 'true')"""
        return self._props.get("error-message")

    @ui_error_message.setter
    def ui_error_message(self, value):
        self._set_prop("error-message", value)

    @property
    def ui_no_error_icon(self):
        """Hide error icon when there is an error"""
        return self._props.get("no-error-icon")

    @ui_no_error_icon.setter
    def ui_no_error_icon(self, value):
        self._set_prop("no-error-icon", value)

    @property
    def ui_rules(self):
        """Array of Functions/Strings; If String, then it must be a name of one of the embedded validation rules"""
        return self._rules

    @ui_rules.setter
    def ui_rules(self, value):
        self._rules = value
        if self._rules and not self._rules_registered:
            self._rules_registered = True
            self.on_update_model_value(self._validate_rules)

    def _validate_rules(self):
        for rule in self.ui_rules:
            value = rule(self.ui_model_value)
            if isinstance(value, str) and value != "":
                self.ui_error_message = value
                self.ui_error = True
                return
        self.ui_error = None

    @property
    def ui_reactive_rules(self):
        """By default a change in the rules does not trigger a new validation until the model changes; If set to true then a change in the rules will trigger a validation; Has a performance penalty, so use it only when you really need it"""
        return self._props.get("reactive-rules")

    @ui_reactive_rules.setter
    def ui_reactive_rules(self, value):
        self._set_prop("reactive-rules", value)

    @property
    def ui_lazy_rules(self):
        """If set to boolean true then it checks validation status against the 'rules' only after field loses focus for first time; If set to 'ondemand' then it will trigger only when component's validate() method is manually called or when the wrapper QForm submits itself"""
        return self._props.get("lazy-rules")

    @ui_lazy_rules.setter
    def ui_lazy_rules(self, value):
        self._set_prop("lazy-rules", value)

    @property
    def ui_multiple(self):
        """Allow multiple file uploads"""
        return self._props.get("multiple")

    @ui_multiple.setter
    def ui_multiple(self, value):
        self._set_prop("multiple", value)

    @property
    def ui_accept(self):
        """Comma separated list of unique file type specifiers. Maps to 'accept' attribute of native input type=file element"""
        return self._props.get("accept")

    @ui_accept.setter
    def ui_accept(self, value):
        self._set_prop("accept", value)

    @property
    def ui_capture(self):
        """Optionally, specify that a new file should be captured, and which device should be used to capture that new media of a type defined by the 'accept' prop. Maps to 'capture' attribute of native input type=file element"""
        return self._props.get("capture")

    @ui_capture.setter
    def ui_capture(self, value):
        self._set_prop("capture", value)

    @property
    def ui_max_file_size(self):
        """Maximum size of individual file in bytes"""
        return self._props.get("max-file-size")

    @ui_max_file_size.setter
    def ui_max_file_size(self, value):
        self._set_prop("max-file-size", value)

    @property
    def ui_max_total_size(self):
        """Maximum size of all files combined in bytes"""
        return self._props.get("max-total-size")

    @ui_max_total_size.setter
    def ui_max_total_size(self, value):
        self._set_prop("max-total-size", value)

    @property
    def ui_max_files(self):
        """Maximum number of files to contain"""
        return self._props.get("max-files")

    @ui_max_files.setter
    def ui_max_files(self, value):
        self._set_prop("max-files", value)

    @property
    def ui_filter(self):
        """Custom filter for added files; Only files that pass this filter will be added to the queue and uploaded; For best performance, reference it from your scope and do not define it inline"""
        return self._props.get("filter")

    @ui_filter.setter
    def ui_filter(self, value):
        self._set_prop("filter", value)

    @property
    def ui_slot_after(self):
        """Append outer field; Suggestions: QIcon, QBtn"""
        return self.ui_slots.get("after", [])

    @ui_slot_after.setter
    def ui_slot_after(self, value):
        self._set_slot("after", value)

    @property
    def ui_slot_append(self):
        """Append to inner field; Suggestions: QIcon, QBtn"""
        return self.ui_slots.get("append", [])

    @ui_slot_append.setter
    def ui_slot_append(self, value):
        self._set_slot("append", value)

    @property
    def ui_slot_before(self):
        """Prepend outer field; Suggestions: QIcon, QBtn"""
        return self.ui_slots.get("before", [])

    @ui_slot_before.setter
    def ui_slot_before(self, value):
        self._set_slot("before", value)

    @property
    def ui_slot_counter(self):
        """Slot for counter text; Enabled only if 'bottom-slots' prop is used; Suggestion: <div>"""
        return self.ui_slots.get("counter", [])

    @ui_slot_counter.setter
    def ui_slot_counter(self, value):
        self._set_slot("counter", value)

    @property
    def ui_slot_error(self):
        """Slot for errors; Enabled only if 'bottom-slots' prop is used; Suggestion: <div>"""
        return self.ui_slots.get("error", [])

    @ui_slot_error.setter
    def ui_slot_error(self, value):
        self._set_slot("error", value)

    @property
    def ui_slot_file(self):
        """Override default node to render a file from the user picked list"""
        return self.ui_slots.get("file", [])

    @ui_slot_file.setter
    def ui_slot_file(self, value):
        self._set_slot("file", value)

    @property
    def ui_slot_hint(self):
        """Slot for hint text; Enabled only if 'bottom-slots' prop is used; Suggestion: <div>"""
        return self.ui_slots.get("hint", [])

    @ui_slot_hint.setter
    def ui_slot_hint(self, value):
        self._set_slot("hint", value)

    @property
    def ui_slot_label(self):
        """Slot for label; Used only if 'label-slot' prop is set or the 'label' prop is set; When it is used the text in the 'label' prop is ignored"""
        return self.ui_slots.get("label", [])

    @ui_slot_label.setter
    def ui_slot_label(self, value):
        self._set_slot("label", value)

    @property
    def ui_slot_loading(self):
        """Override default spinner when component is in loading mode; Use in conjunction with 'loading' prop"""
        return self.ui_slots.get("loading", [])

    @ui_slot_loading.setter
    def ui_slot_loading(self, value):
        self._set_slot("loading", value)

    @property
    def ui_slot_prepend(self):
        """Prepend inner field; Suggestions: QIcon, QBtn"""
        return self.ui_slots.get("prepend", [])

    @ui_slot_prepend.setter
    def ui_slot_prepend(self, value):
        self._set_slot("prepend", value)

    @property
    def ui_slot_selected(self):
        """Override default selection slot; Suggestion: QChip"""
        return self.ui_slots.get("selected", [])

    @ui_slot_selected.setter
    def ui_slot_selected(self, value):
        self._set_slot("selected", value)

    def on_blur(self, handler: Callable, arg: object = None):
        """
        Emitted when component loses focus

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("blur", handler, arg)

    def on_clear(self, handler: Callable, arg: object = None):
        """
        When using the 'clearable' property, this event is emitted when the clear icon is clicked

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("clear", handler, arg)

    def on_focus(self, handler: Callable, arg: object = None):
        """
        Emitted when component gets focused

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("focus", handler, arg)

    def on_rejected(self, handler: Callable, arg: object = None):
        """
        Emitted after files are picked and some do not pass the validation props (accept, max-file-size, max-total-size, filter, etc)

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("rejected", handler, arg)

    def on_update_model_value(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("update:model-value", handler, arg)

    def ui_addFiles(self, ui_files):
        """Add files programmatically"""
        kwargs = {}
        if ui_files is not None:
            kwargs["files"] = ui_files
        self._js_call_method("addFiles", [kwargs])

    def ui_blur(self):
        """Blur component (lose focus)"""
        self._js_call_method("blur")

    def ui_focus(self):
        """Focus component"""
        self._js_call_method("focus")

    def ui_getNativeElement(self):
        """DEPRECATED; Access 'nativeEl' directly; Gets the native input DOM Element"""
        self._js_call_method("getNativeElement")

    def ui_pickFiles(self, ui_evt=None):
        """Trigger file pick; Must be called as a direct consequence of user interaction (eg. in a click handler), due to browsers security policy"""
        kwargs = {}
        if ui_evt is not None:
            kwargs["evt"] = ui_evt
        self._js_call_method("pickFiles", [kwargs])

    def ui_removeAtIndex(self, ui_index):
        """Remove file located at specific index in the model"""
        kwargs = {}
        if ui_index is not None:
            kwargs["index"] = ui_index
        self._js_call_method("removeAtIndex", [kwargs])

    def ui_removeFile(self, ui_file):
        """Remove specified file from the model"""
        kwargs = {}
        if ui_file is not None:
            kwargs["file"] = ui_file
        self._js_call_method("removeFile", [kwargs])

    def ui_resetValidation(self):
        """Reset validation status"""
        self._js_call_method("resetValidation")

    def ui_validate(self, ui_value=None):
        """Trigger a validation"""
        kwargs = {}
        if ui_value is not None:
            kwargs["value"] = ui_value
        self._js_call_method("validate", [kwargs])

    def _get_js_methods(self):
        return [
            "addFiles",
            "blur",
            "focus",
            "getNativeElement",
            "pickFiles",
            "removeAtIndex",
            "removeFile",
            "resetValidation",
            "validate",
        ]


class QFooter(Component):
    """
    Quasar Component: `QFooter <https://v2.quasar.dev/layout/header-and-footer>`__

    :param ui_model_value: Model of the component defining if it is shown or hidden to the user; Either use this property (along with a listener for 'update:modelValue' event) OR use v-model directive
    :param ui_reveal: Enable 'reveal' mode; Takes into account user scroll to temporarily show/hide footer
    :param ui_bordered:
    :param ui_elevated: Adds a default shadow to the footer
    :param ui_height_hint: When using SSR, you can optionally hint of the height (in pixels) of the QFooter
    """

    def __init__(
        self,
        *children,
        ui_model_value: bool | None = None,
        ui_reveal: bool | None = None,
        ui_bordered: Any | None = None,
        ui_elevated: bool | None = None,
        ui_height_hint: float | str | None = None,
        **kwargs,
    ):
        super().__init__("QFooter", *children, **kwargs)
        self.on("update:model-value", self.__update_model_value)

        if ui_model_value is not None:
            self._props["model-value"] = ui_model_value
        if ui_reveal is not None:
            self._props["reveal"] = ui_reveal
        if ui_bordered is not None:
            self._props["bordered"] = ui_bordered
        if ui_elevated is not None:
            self._props["elevated"] = ui_elevated
        if ui_height_hint is not None:
            self._props["height-hint"] = ui_height_hint

    def __update_model_value(self, event: Event):
        self._set_prop("model-value", event.value)

    @property
    def ui_model_value(self):
        """Model of the component defining if it is shown or hidden to the user; Either use this property (along with a listener for 'update:modelValue' event) OR use v-model directive"""
        return self._props.get("model-value")

    @ui_model_value.setter
    def ui_model_value(self, value):
        self._set_prop("model-value", value)

    @property
    def ui_reveal(self):
        """Enable 'reveal' mode; Takes into account user scroll to temporarily show/hide footer"""
        return self._props.get("reveal")

    @ui_reveal.setter
    def ui_reveal(self, value):
        self._set_prop("reveal", value)

    @property
    def ui_bordered(self):
        return self._props.get("bordered")

    @ui_bordered.setter
    def ui_bordered(self, value):
        self._set_prop("bordered", value)

    @property
    def ui_elevated(self):
        """Adds a default shadow to the footer"""
        return self._props.get("elevated")

    @ui_elevated.setter
    def ui_elevated(self, value):
        self._set_prop("elevated", value)

    @property
    def ui_height_hint(self):
        """When using SSR, you can optionally hint of the height (in pixels) of the QFooter"""
        return self._props.get("height-hint")

    @ui_height_hint.setter
    def ui_height_hint(self, value):
        self._set_prop("height-hint", value)

    def on_focusin(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("focusin", handler, arg)

    def on_reveal(self, handler: Callable, arg: object = None):
        """
        Emitted when 'reveal' state gets changed

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("reveal", handler, arg)

    def _get_js_methods(self):
        return []


class QForm(Component):
    """
    Quasar Component: `QForm <https://v2.quasar.dev/vue-components/form>`__

    :param ui_autofocus: Focus first focusable element on initial component render
    :param ui_no_error_focus: Do not try to focus on first component that has a validation error when submitting form
    :param ui_no_reset_focus: Do not try to focus on first component when resetting form
    :param ui_greedy: Validate all fields in form (by default it stops after finding the first invalid field with synchronous validation)
    """

    def __init__(
        self,
        *children,
        ui_autofocus: bool | None = None,
        ui_no_error_focus: bool | None = None,
        ui_no_reset_focus: bool | None = None,
        ui_greedy: bool | None = None,
        **kwargs,
    ):
        super().__init__("QForm", *children, **kwargs)
        if ui_autofocus is not None:
            self._props["autofocus"] = ui_autofocus
        if ui_no_error_focus is not None:
            self._props["no-error-focus"] = ui_no_error_focus
        if ui_no_reset_focus is not None:
            self._props["no-reset-focus"] = ui_no_reset_focus
        if ui_greedy is not None:
            self._props["greedy"] = ui_greedy

    @property
    def ui_autofocus(self):
        """Focus first focusable element on initial component render"""
        return self._props.get("autofocus")

    @ui_autofocus.setter
    def ui_autofocus(self, value):
        self._set_prop("autofocus", value)

    @property
    def ui_no_error_focus(self):
        """Do not try to focus on first component that has a validation error when submitting form"""
        return self._props.get("no-error-focus")

    @ui_no_error_focus.setter
    def ui_no_error_focus(self, value):
        self._set_prop("no-error-focus", value)

    @property
    def ui_no_reset_focus(self):
        """Do not try to focus on first component when resetting form"""
        return self._props.get("no-reset-focus")

    @ui_no_reset_focus.setter
    def ui_no_reset_focus(self, value):
        self._set_prop("no-reset-focus", value)

    @property
    def ui_greedy(self):
        """Validate all fields in form (by default it stops after finding the first invalid field with synchronous validation)"""
        return self._props.get("greedy")

    @ui_greedy.setter
    def ui_greedy(self, value):
        self._set_prop("greedy", value)

    def on_reset(self, handler: Callable, arg: object = None):
        """
        Emitted when all validations have been reset when tethered to a reset button; It is recommended to manually reset the wrapped components models in this handler

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("reset", handler, arg)

    def on_submit(self, handler: Callable, arg: object = None):
        """
        Emitted when all validations have passed when tethered to a submit button

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("submit", handler, arg)

    def on_validation_error(self, handler: Callable, arg: object = None):
        """
        Emitted after a validation was triggered and at least one of the inner Quasar components models are NOT valid

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("validation-error", handler, arg)

    def on_validation_success(self, handler: Callable, arg: object = None):
        """
        Emitted after a validation was triggered and all inner Quasar components models are valid

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("validation-success", handler, arg)

    def ui_focus(self):
        """Focus on first focusable element/component in the form"""
        self._js_call_method("focus")

    def ui_getValidationComponents(self):
        """Get an array of children Vue component instances that support Quasar validation API (derived from QField, or using useFormChild()/QFormChildMixin)"""
        self._js_call_method("getValidationComponents")

    def ui_reset(self, ui_evt=None):
        """Manually trigger form reset"""
        kwargs = {}
        if ui_evt is not None:
            kwargs["evt"] = ui_evt
        self._js_call_method("reset", [kwargs])

    def ui_resetValidation(self):
        """Resets the validation on all applicable inner Quasar components"""
        self._js_call_method("resetValidation")

    def ui_submit(self, ui_evt=None):
        """Manually trigger form validation and submit"""
        kwargs = {}
        if ui_evt is not None:
            kwargs["evt"] = ui_evt
        self._js_call_method("submit", [kwargs])

    def ui_validate(self, ui_shouldFocus=None):
        """Triggers a validation on all applicable inner Quasar components"""
        kwargs = {}
        if ui_shouldFocus is not None:
            kwargs["shouldFocus"] = ui_shouldFocus
        self._js_call_method("validate", [kwargs])

    def _get_js_methods(self):
        return [
            "focus",
            "getValidationComponents",
            "reset",
            "resetValidation",
            "submit",
            "validate",
        ]


class QFormChildMixin(Component):
    """
    Quasar Component: `QFormChildMixin <https://v2.quasar.dev/vue-components/form>`__

    """

    def __init__(self, *children, **kwargs):
        super().__init__("QFormChildMixin", *children, **kwargs)

    def ui_resetValidation(self):
        """Needs to be overwritten when getting extended/mixed in"""
        self._js_call_method("resetValidation")

    def ui_validate(self):
        """Needs to be overwritten when getting extended/mixed in"""
        self._js_call_method("validate")

    def _get_js_methods(self):
        return ["resetValidation", "validate"]


class QHeader(Component):
    """
    Quasar Component: `QHeader <https://v2.quasar.dev/layout/header-and-footer>`__

    :param ui_model_value: Model of the component defining if it is shown or hidden to the user; Either use this property (along with a listener for 'update:modelValue' event) OR use v-model directive
    :param ui_reveal: Enable 'reveal' mode; Takes into account user scroll to temporarily show/hide header
    :param ui_reveal_offset: Amount of scroll (in pixels) that should trigger a 'reveal' state change
    :param ui_bordered:
    :param ui_elevated: Adds a default shadow to the header
    :param ui_height_hint: When using SSR, you can optionally hint of the height (in pixels) of the QHeader
    """

    def __init__(
        self,
        *children,
        ui_model_value: bool | None = None,
        ui_reveal: bool | None = None,
        ui_reveal_offset: float | None = None,
        ui_bordered: Any | None = None,
        ui_elevated: bool | None = None,
        ui_height_hint: float | str | None = None,
        **kwargs,
    ):
        super().__init__("QHeader", *children, **kwargs)
        self.on("update:model-value", self.__update_model_value)

        if ui_model_value is not None:
            self._props["model-value"] = ui_model_value
        if ui_reveal is not None:
            self._props["reveal"] = ui_reveal
        if ui_reveal_offset is not None:
            self._props["reveal-offset"] = ui_reveal_offset
        if ui_bordered is not None:
            self._props["bordered"] = ui_bordered
        if ui_elevated is not None:
            self._props["elevated"] = ui_elevated
        if ui_height_hint is not None:
            self._props["height-hint"] = ui_height_hint

    def __update_model_value(self, event: Event):
        self._set_prop("model-value", event.value)

    @property
    def ui_model_value(self):
        """Model of the component defining if it is shown or hidden to the user; Either use this property (along with a listener for 'update:modelValue' event) OR use v-model directive"""
        return self._props.get("model-value")

    @ui_model_value.setter
    def ui_model_value(self, value):
        self._set_prop("model-value", value)

    @property
    def ui_reveal(self):
        """Enable 'reveal' mode; Takes into account user scroll to temporarily show/hide header"""
        return self._props.get("reveal")

    @ui_reveal.setter
    def ui_reveal(self, value):
        self._set_prop("reveal", value)

    @property
    def ui_reveal_offset(self):
        """Amount of scroll (in pixels) that should trigger a 'reveal' state change"""
        return self._props.get("reveal-offset")

    @ui_reveal_offset.setter
    def ui_reveal_offset(self, value):
        self._set_prop("reveal-offset", value)

    @property
    def ui_bordered(self):
        return self._props.get("bordered")

    @ui_bordered.setter
    def ui_bordered(self, value):
        self._set_prop("bordered", value)

    @property
    def ui_elevated(self):
        """Adds a default shadow to the header"""
        return self._props.get("elevated")

    @ui_elevated.setter
    def ui_elevated(self, value):
        self._set_prop("elevated", value)

    @property
    def ui_height_hint(self):
        """When using SSR, you can optionally hint of the height (in pixels) of the QHeader"""
        return self._props.get("height-hint")

    @ui_height_hint.setter
    def ui_height_hint(self, value):
        self._set_prop("height-hint", value)

    def on_focusin(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("focusin", handler, arg)

    def on_reveal(self, handler: Callable, arg: object = None):
        """
        Emitted when 'reveal' state gets changed

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("reveal", handler, arg)

    def _get_js_methods(self):
        return []


class QIcon(Component):
    """
    Quasar Component: `QIcon <https://v2.quasar.dev/vue-components/icon>`__

    :param ui_tag: HTML tag to render, unless no icon is supplied or it's an svg icon
    :param ui_name:
    :param ui_color:
    :param ui_left: Useful if icon is on the left side of something: applies a standard margin on the right side of Icon
    :param ui_right: Useful if icon is on the right side of something: applies a standard margin on the left side of Icon
    :param ui_size: Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)
    """

    def __init__(
        self,
        *children,
        ui_tag: Any | None = None,
        ui_name: Any | None = None,
        ui_color: Any | None = None,
        ui_left: bool | None = None,
        ui_right: bool | None = None,
        ui_size: str | None = None,
        **kwargs,
    ):
        super().__init__("QIcon", *children, **kwargs)
        if ui_tag is not None:
            self._props["tag"] = ui_tag
        if ui_name is not None:
            self._props["name"] = ui_name
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_left is not None:
            self._props["left"] = ui_left
        if ui_right is not None:
            self._props["right"] = ui_right
        if ui_size is not None:
            self._props["size"] = ui_size

    @property
    def ui_tag(self):
        """HTML tag to render, unless no icon is supplied or it's an svg icon"""
        return self._props.get("tag")

    @ui_tag.setter
    def ui_tag(self, value):
        self._set_prop("tag", value)

    @property
    def ui_name(self):
        return self._props.get("name")

    @ui_name.setter
    def ui_name(self, value):
        self._set_prop("name", value)

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_left(self):
        """Useful if icon is on the left side of something: applies a standard margin on the right side of Icon"""
        return self._props.get("left")

    @ui_left.setter
    def ui_left(self, value):
        self._set_prop("left", value)

    @property
    def ui_right(self):
        """Useful if icon is on the right side of something: applies a standard margin on the left side of Icon"""
        return self._props.get("right")

    @ui_right.setter
    def ui_right(self, value):
        self._set_prop("right", value)

    @property
    def ui_size(self):
        """Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)"""
        return self._props.get("size")

    @ui_size.setter
    def ui_size(self, value):
        self._set_prop("size", value)

    def _get_js_methods(self):
        return []


class QImg(Component):
    """
    Quasar Component: `QImg <https://v2.quasar.dev/vue-components/img>`__

    :param ui_src: Path to image
    :param ui_srcset: Same syntax as <img> srcset attribute
    :param ui_sizes: Same syntax as <img> sizes attribute
    :param ui_placeholder_src: While waiting for your image to load, you can use a placeholder image
    :param ui_error_src: In case your image fails to load, you can use an error image
    :param ui_ratio: Aspect ratio for the content; If value is a String, then avoid using a computational statement (like '16/9') and instead specify the String value of the result directly (eg. '1.7777')
    :param ui_initial_ratio: Use it when not specifying 'ratio' but still wanting an initial aspect ratio
    :param ui_width: Forces image width; Must also include the unit (px or %)
    :param ui_height: Forces image height; Must also include the unit (px or %)
    :param ui_loading: Lazy or immediate load; Same syntax as <img> loading attribute
    :param ui_loading_show_delay: Delay showing the spinner when image changes; Gives time for the browser to load the image from cache to prevent flashing the spinner unnecessarily; Value should represent milliseconds
    :param ui_crossorigin: Same syntax as <img> crossorigin attribute
    :param ui_decoding: Same syntax as <img> decoding attribute
    :param ui_referrerpolicy: Same syntax as <img> referrerpolicy attribute
    :param ui_fetchpriority: Provides a hint of the relative priority to use when fetching the image
    :param ui_fit: How the image will fit into the container; Equivalent of the object-fit prop; Can be coordinated with 'position' prop
    :param ui_position: The alignment of the image into the container; Equivalent of the object-position CSS prop
    :param ui_alt: Specifies an alternate text for the image, if the image cannot be displayed
    :param ui_draggable: Adds the native 'draggable' attribute
    :param ui_img_class: CSS classes to be attributed to the native img element
    :param ui_img_style: Apply CSS to the native img element
    :param ui_spinner_color: Color name for default Spinner (unless using a 'loading' slot)
    :param ui_spinner_size: Size in CSS units, including unit name, for default Spinner (unless using a 'loading' slot)
    :param ui_no_spinner: Do not display the default spinner while waiting for the image to be loaded; It is overriden by the 'loading' slot when one is present
    :param ui_no_native_menu: Disables the native context menu for the image
    :param ui_no_transition: Disable default transition when switching between old and new image
    """

    def __init__(
        self,
        *children,
        ui_src: str | None = None,
        ui_srcset: str | None = None,
        ui_sizes: str | None = None,
        ui_placeholder_src: str | None = None,
        ui_error_src: str | None = None,
        ui_ratio: str | float | None = None,
        ui_initial_ratio: str | float | None = None,
        ui_width: str | None = None,
        ui_height: str | None = None,
        ui_loading: str | None = None,
        ui_loading_show_delay: float | str | None = None,
        ui_crossorigin: str | None = None,
        ui_decoding: str | None = None,
        ui_referrerpolicy: str | None = None,
        ui_fetchpriority: str | None = None,
        ui_fit: str | None = None,
        ui_position: str | None = None,
        ui_alt: str | None = None,
        ui_draggable: bool | None = None,
        ui_img_class: str | None = None,
        ui_img_style: dict | None = None,
        ui_spinner_color: Any | None = None,
        ui_spinner_size: Any | None = None,
        ui_no_spinner: bool | None = None,
        ui_no_native_menu: bool | None = None,
        ui_no_transition: bool | None = None,
        **kwargs,
    ):
        super().__init__("QImg", *children, **kwargs)
        if ui_src is not None:
            self._props["src"] = ui_src
        if ui_srcset is not None:
            self._props["srcset"] = ui_srcset
        if ui_sizes is not None:
            self._props["sizes"] = ui_sizes
        if ui_placeholder_src is not None:
            self._props["placeholder-src"] = ui_placeholder_src
        if ui_error_src is not None:
            self._props["error-src"] = ui_error_src
        if ui_ratio is not None:
            self._props["ratio"] = ui_ratio
        if ui_initial_ratio is not None:
            self._props["initial-ratio"] = ui_initial_ratio
        if ui_width is not None:
            self._props["width"] = ui_width
        if ui_height is not None:
            self._props["height"] = ui_height
        if ui_loading is not None:
            self._props["loading"] = ui_loading
        if ui_loading_show_delay is not None:
            self._props["loading-show-delay"] = ui_loading_show_delay
        if ui_crossorigin is not None:
            self._props["crossorigin"] = ui_crossorigin
        if ui_decoding is not None:
            self._props["decoding"] = ui_decoding
        if ui_referrerpolicy is not None:
            self._props["referrerpolicy"] = ui_referrerpolicy
        if ui_fetchpriority is not None:
            self._props["fetchpriority"] = ui_fetchpriority
        if ui_fit is not None:
            self._props["fit"] = ui_fit
        if ui_position is not None:
            self._props["position"] = ui_position
        if ui_alt is not None:
            self._props["alt"] = ui_alt
        if ui_draggable is not None:
            self._props["draggable"] = ui_draggable
        if ui_img_class is not None:
            self._props["img-class"] = ui_img_class
        if ui_img_style is not None:
            self._props["img-style"] = ui_img_style
        if ui_spinner_color is not None:
            self._props["spinner-color"] = ui_spinner_color
        if ui_spinner_size is not None:
            self._props["spinner-size"] = ui_spinner_size
        if ui_no_spinner is not None:
            self._props["no-spinner"] = ui_no_spinner
        if ui_no_native_menu is not None:
            self._props["no-native-menu"] = ui_no_native_menu
        if ui_no_transition is not None:
            self._props["no-transition"] = ui_no_transition

    @property
    def ui_src(self):
        """Path to image"""
        return self._props.get("src")

    @ui_src.setter
    def ui_src(self, value):
        self._set_prop("src", value)

    @property
    def ui_srcset(self):
        """Same syntax as <img> srcset attribute"""
        return self._props.get("srcset")

    @ui_srcset.setter
    def ui_srcset(self, value):
        self._set_prop("srcset", value)

    @property
    def ui_sizes(self):
        """Same syntax as <img> sizes attribute"""
        return self._props.get("sizes")

    @ui_sizes.setter
    def ui_sizes(self, value):
        self._set_prop("sizes", value)

    @property
    def ui_placeholder_src(self):
        """While waiting for your image to load, you can use a placeholder image"""
        return self._props.get("placeholder-src")

    @ui_placeholder_src.setter
    def ui_placeholder_src(self, value):
        self._set_prop("placeholder-src", value)

    @property
    def ui_error_src(self):
        """In case your image fails to load, you can use an error image"""
        return self._props.get("error-src")

    @ui_error_src.setter
    def ui_error_src(self, value):
        self._set_prop("error-src", value)

    @property
    def ui_ratio(self):
        """Aspect ratio for the content; If value is a String, then avoid using a computational statement (like '16/9') and instead specify the String value of the result directly (eg. '1.7777')"""
        return self._props.get("ratio")

    @ui_ratio.setter
    def ui_ratio(self, value):
        self._set_prop("ratio", value)

    @property
    def ui_initial_ratio(self):
        """Use it when not specifying 'ratio' but still wanting an initial aspect ratio"""
        return self._props.get("initial-ratio")

    @ui_initial_ratio.setter
    def ui_initial_ratio(self, value):
        self._set_prop("initial-ratio", value)

    @property
    def ui_width(self):
        """Forces image width; Must also include the unit (px or %)"""
        return self._props.get("width")

    @ui_width.setter
    def ui_width(self, value):
        self._set_prop("width", value)

    @property
    def ui_height(self):
        """Forces image height; Must also include the unit (px or %)"""
        return self._props.get("height")

    @ui_height.setter
    def ui_height(self, value):
        self._set_prop("height", value)

    @property
    def ui_loading(self):
        """Lazy or immediate load; Same syntax as <img> loading attribute"""
        return self._props.get("loading")

    @ui_loading.setter
    def ui_loading(self, value):
        self._set_prop("loading", value)

    @property
    def ui_loading_show_delay(self):
        """Delay showing the spinner when image changes; Gives time for the browser to load the image from cache to prevent flashing the spinner unnecessarily; Value should represent milliseconds"""
        return self._props.get("loading-show-delay")

    @ui_loading_show_delay.setter
    def ui_loading_show_delay(self, value):
        self._set_prop("loading-show-delay", value)

    @property
    def ui_crossorigin(self):
        """Same syntax as <img> crossorigin attribute"""
        return self._props.get("crossorigin")

    @ui_crossorigin.setter
    def ui_crossorigin(self, value):
        self._set_prop("crossorigin", value)

    @property
    def ui_decoding(self):
        """Same syntax as <img> decoding attribute"""
        return self._props.get("decoding")

    @ui_decoding.setter
    def ui_decoding(self, value):
        self._set_prop("decoding", value)

    @property
    def ui_referrerpolicy(self):
        """Same syntax as <img> referrerpolicy attribute"""
        return self._props.get("referrerpolicy")

    @ui_referrerpolicy.setter
    def ui_referrerpolicy(self, value):
        self._set_prop("referrerpolicy", value)

    @property
    def ui_fetchpriority(self):
        """Provides a hint of the relative priority to use when fetching the image"""
        return self._props.get("fetchpriority")

    @ui_fetchpriority.setter
    def ui_fetchpriority(self, value):
        self._set_prop("fetchpriority", value)

    @property
    def ui_fit(self):
        """How the image will fit into the container; Equivalent of the object-fit prop; Can be coordinated with 'position' prop"""
        return self._props.get("fit")

    @ui_fit.setter
    def ui_fit(self, value):
        self._set_prop("fit", value)

    @property
    def ui_position(self):
        """The alignment of the image into the container; Equivalent of the object-position CSS prop"""
        return self._props.get("position")

    @ui_position.setter
    def ui_position(self, value):
        self._set_prop("position", value)

    @property
    def ui_alt(self):
        """Specifies an alternate text for the image, if the image cannot be displayed"""
        return self._props.get("alt")

    @ui_alt.setter
    def ui_alt(self, value):
        self._set_prop("alt", value)

    @property
    def ui_draggable(self):
        """Adds the native 'draggable' attribute"""
        return self._props.get("draggable")

    @ui_draggable.setter
    def ui_draggable(self, value):
        self._set_prop("draggable", value)

    @property
    def ui_img_class(self):
        """CSS classes to be attributed to the native img element"""
        return self._props.get("img-class")

    @ui_img_class.setter
    def ui_img_class(self, value):
        self._set_prop("img-class", value)

    @property
    def ui_img_style(self):
        """Apply CSS to the native img element"""
        return self._props.get("img-style")

    @ui_img_style.setter
    def ui_img_style(self, value):
        self._set_prop("img-style", value)

    @property
    def ui_spinner_color(self):
        """Color name for default Spinner (unless using a 'loading' slot)"""
        return self._props.get("spinner-color")

    @ui_spinner_color.setter
    def ui_spinner_color(self, value):
        self._set_prop("spinner-color", value)

    @property
    def ui_spinner_size(self):
        """Size in CSS units, including unit name, for default Spinner (unless using a 'loading' slot)"""
        return self._props.get("spinner-size")

    @ui_spinner_size.setter
    def ui_spinner_size(self, value):
        self._set_prop("spinner-size", value)

    @property
    def ui_no_spinner(self):
        """Do not display the default spinner while waiting for the image to be loaded; It is overriden by the 'loading' slot when one is present"""
        return self._props.get("no-spinner")

    @ui_no_spinner.setter
    def ui_no_spinner(self, value):
        self._set_prop("no-spinner", value)

    @property
    def ui_no_native_menu(self):
        """Disables the native context menu for the image"""
        return self._props.get("no-native-menu")

    @ui_no_native_menu.setter
    def ui_no_native_menu(self, value):
        self._set_prop("no-native-menu", value)

    @property
    def ui_no_transition(self):
        """Disable default transition when switching between old and new image"""
        return self._props.get("no-transition")

    @ui_no_transition.setter
    def ui_no_transition(self, value):
        self._set_prop("no-transition", value)

    @property
    def ui_slot_error(self):
        """Optional slot to be used when image could not be loaded; make sure you assign a min-height and min-width to the component through CSS"""
        return self.ui_slots.get("error", [])

    @ui_slot_error.setter
    def ui_slot_error(self, value):
        self._set_slot("error", value)

    @property
    def ui_slot_loading(self):
        """While image is loading, this slot is being displayed on top of the component; Suggestions: a spinner or text"""
        return self.ui_slots.get("loading", [])

    @ui_slot_loading.setter
    def ui_slot_loading(self, value):
        self._set_slot("loading", value)

    def on_error(self, handler: Callable, arg: object = None):
        """
        Emitted when browser could not load the image

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("error", handler, arg)

    def on_load(self, handler: Callable, arg: object = None):
        """
        Emitted when image has been loaded by the browser

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("load", handler, arg)

    def _get_js_methods(self):
        return []


class QInfiniteScroll(Component):
    """
    Quasar Component: `QInfiniteScroll <https://v2.quasar.dev/vue-components/infinite-scroll>`__

    :param ui_offset: Offset (pixels) to bottom of Infinite Scroll container from which the component should start loading more content in advance
    :param ui_debounce: Debounce amount (in milliseconds)
    :param ui_initial_index: Initialize the pagination index (used for the @load event)
    :param ui_scroll_target:
    :param ui_disable:
    :param ui_reverse: Scroll area should behave like a messenger - starting scrolled to bottom and loading when reaching the top
    """

    def __init__(
        self,
        *children,
        ui_offset: float | None = None,
        ui_debounce: str | float | None = None,
        ui_initial_index: float | None = None,
        ui_scroll_target: Any | None = None,
        ui_disable: Any | None = None,
        ui_reverse: bool | None = None,
        **kwargs,
    ):
        super().__init__("QInfiniteScroll", *children, **kwargs)
        if ui_offset is not None:
            self._props["offset"] = ui_offset
        if ui_debounce is not None:
            self._props["debounce"] = ui_debounce
        if ui_initial_index is not None:
            self._props["initial-index"] = ui_initial_index
        if ui_scroll_target is not None:
            self._props["scroll-target"] = ui_scroll_target
        if ui_disable is not None:
            self._props["disable"] = ui_disable
        if ui_reverse is not None:
            self._props["reverse"] = ui_reverse

    @property
    def ui_offset(self):
        """Offset (pixels) to bottom of Infinite Scroll container from which the component should start loading more content in advance"""
        return self._props.get("offset")

    @ui_offset.setter
    def ui_offset(self, value):
        self._set_prop("offset", value)

    @property
    def ui_debounce(self):
        """Debounce amount (in milliseconds)"""
        return self._props.get("debounce")

    @ui_debounce.setter
    def ui_debounce(self, value):
        self._set_prop("debounce", value)

    @property
    def ui_initial_index(self):
        """Initialize the pagination index (used for the @load event)"""
        return self._props.get("initial-index")

    @ui_initial_index.setter
    def ui_initial_index(self, value):
        self._set_prop("initial-index", value)

    @property
    def ui_scroll_target(self):
        return self._props.get("scroll-target")

    @ui_scroll_target.setter
    def ui_scroll_target(self, value):
        self._set_prop("scroll-target", value)

    @property
    def ui_disable(self):
        return self._props.get("disable")

    @ui_disable.setter
    def ui_disable(self, value):
        self._set_prop("disable", value)

    @property
    def ui_reverse(self):
        """Scroll area should behave like a messenger - starting scrolled to bottom and loading when reaching the top"""
        return self._props.get("reverse")

    @ui_reverse.setter
    def ui_reverse(self, value):
        self._set_prop("reverse", value)

    @property
    def ui_slot_loading(self):
        """Slot displaying something while loading content; Example: QSpinner"""
        return self.ui_slots.get("loading", [])

    @ui_slot_loading.setter
    def ui_slot_loading(self, value):
        self._set_slot("loading", value)

    def on_load(self, handler: Callable, arg: object = None):
        """
        Emitted when Infinite Scroll needs to load more data

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("load", handler, arg)

    def ui_poll(self):
        """Checks scroll position and loads more content if necessary"""
        self._js_call_method("poll")

    def ui_reset(self):
        """Resets calling index to 0"""
        self._js_call_method("reset")

    def ui_resume(self):
        """Starts working. Checks scroll position upon call and if trigger is hit, it loads more content"""
        self._js_call_method("resume")

    def ui_setIndex(self, ui_newIndex):
        """Overwrite the current pagination index"""
        kwargs = {}
        if ui_newIndex is not None:
            kwargs["newIndex"] = ui_newIndex
        self._js_call_method("setIndex", [kwargs])

    def ui_stop(self):
        """Stops working, regardless of scroll position"""
        self._js_call_method("stop")

    def ui_trigger(self):
        """Tells Infinite Scroll to load more content, regardless of the scroll position"""
        self._js_call_method("trigger")

    def ui_updateScrollTarget(self):
        """Updates the scroll target; Useful when the parent elements change so that the scrolling target also changes"""
        self._js_call_method("updateScrollTarget")

    def _get_js_methods(self):
        return [
            "poll",
            "reset",
            "resume",
            "setIndex",
            "stop",
            "trigger",
            "updateScrollTarget",
        ]


class QInnerLoading(Component):
    """
    Quasar Component: `QInnerLoading <https://v2.quasar.dev/vue-components/inner-loading>`__

    :param ui_showing: State - loading or not
    :param ui_color: Color name for component from the Quasar Color Palette for the inner Spinner (unless using the default slot)
    :param ui_size: Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)
    :param ui_label: Add a label; Gets overriden when using the default slot
    :param ui_label_class: Add CSS class(es) to the label; Works along the 'label' prop only
    :param ui_label_style: Apply custom style to the label; Works along the 'label' prop only
    :param ui_dark:
    :param ui_transition_show:
    :param ui_transition_hide:
    :param ui_transition_duration: Transition duration (in milliseconds, without unit)
    """

    def __init__(
        self,
        *children,
        ui_showing: bool | None = None,
        ui_color: Any | None = None,
        ui_size: str | None = None,
        ui_label: str | None = None,
        ui_label_class: str | None = None,
        ui_label_style: str | list | dict | None = None,
        ui_dark: Any | None = None,
        ui_transition_show: Any | None = None,
        ui_transition_hide: Any | None = None,
        ui_transition_duration: str | float | None = None,
        **kwargs,
    ):
        super().__init__("QInnerLoading", *children, **kwargs)
        if ui_showing is not None:
            self._props["showing"] = ui_showing
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_size is not None:
            self._props["size"] = ui_size
        if ui_label is not None:
            self._props["label"] = ui_label
        if ui_label_class is not None:
            self._props["label-class"] = ui_label_class
        if ui_label_style is not None:
            self._props["label-style"] = ui_label_style
        if ui_dark is not None:
            self._props["dark"] = ui_dark
        if ui_transition_show is not None:
            self._props["transition-show"] = ui_transition_show
        if ui_transition_hide is not None:
            self._props["transition-hide"] = ui_transition_hide
        if ui_transition_duration is not None:
            self._props["transition-duration"] = ui_transition_duration

    @property
    def ui_showing(self):
        """State - loading or not"""
        return self._props.get("showing")

    @ui_showing.setter
    def ui_showing(self, value):
        self._set_prop("showing", value)

    @property
    def ui_color(self):
        """Color name for component from the Quasar Color Palette for the inner Spinner (unless using the default slot)"""
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_size(self):
        """Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)"""
        return self._props.get("size")

    @ui_size.setter
    def ui_size(self, value):
        self._set_prop("size", value)

    @property
    def ui_label(self):
        """Add a label; Gets overriden when using the default slot"""
        return self._props.get("label")

    @ui_label.setter
    def ui_label(self, value):
        self._set_prop("label", value)

    @property
    def ui_label_class(self):
        """Add CSS class(es) to the label; Works along the 'label' prop only"""
        return self._props.get("label-class")

    @ui_label_class.setter
    def ui_label_class(self, value):
        self._set_prop("label-class", value)

    @property
    def ui_label_style(self):
        """Apply custom style to the label; Works along the 'label' prop only"""
        return self._props.get("label-style")

    @ui_label_style.setter
    def ui_label_style(self, value):
        self._set_prop("label-style", value)

    @property
    def ui_dark(self):
        return self._props.get("dark")

    @ui_dark.setter
    def ui_dark(self, value):
        self._set_prop("dark", value)

    @property
    def ui_transition_show(self):
        return self._props.get("transition-show")

    @ui_transition_show.setter
    def ui_transition_show(self, value):
        self._set_prop("transition-show", value)

    @property
    def ui_transition_hide(self):
        return self._props.get("transition-hide")

    @ui_transition_hide.setter
    def ui_transition_hide(self, value):
        self._set_prop("transition-hide", value)

    @property
    def ui_transition_duration(self):
        """Transition duration (in milliseconds, without unit)"""
        return self._props.get("transition-duration")

    @ui_transition_duration.setter
    def ui_transition_duration(self, value):
        self._set_prop("transition-duration", value)

    def _get_js_methods(self):
        return []


class QInput(Component):
    """
    Quasar Component: `QInput <https://v2.quasar.dev/vue-components/input>`__

    :param ui_model_value: Model of the component; Either use this property (along with a listener for 'update:model-value' event) OR use v-model directive
    :param ui_shadow_text: Text to be displayed as shadow at the end of the text in the control; Does NOT applies to type=file
    :param ui_type: Input type
    :param ui_debounce: Debounce amount (in milliseconds) when updating model
    :param ui_maxlength: Specify a max length of model
    :param ui_autogrow: Make field autogrow along with its content (uses a textarea)
    :param ui_input_class: Class definitions to be attributed to the underlying input tag
    :param ui_input_style: Style definitions to be attributed to the underlying input tag
    :param ui_name: Used to specify the name of the control; Useful if dealing with forms submitted directly to a URL
    :param ui_label: A text label that will “float” up above the input field, once the field gets focus
    :param ui_stack_label: Label will be always shown above the field regardless of field content (if any)
    :param ui_hint: Helper (hint) text which gets placed below your wrapped form component
    :param ui_hide_hint: Hide the helper (hint) text when field doesn't have focus
    :param ui_prefix: Prefix
    :param ui_suffix: Suffix
    :param ui_label_color: Color name for the label from the Quasar Color Palette; Overrides the 'color' prop; The difference from 'color' prop is that the label will always have this color, even when field is not focused
    :param ui_color:
    :param ui_bg_color:
    :param ui_dark:
    :param ui_loading: Signals the user a process is in progress by displaying a spinner; Spinner can be customized by using the 'loading' slot.
    :param ui_clearable: Appends clearable icon when a value (not undefined or null) is set; When clicked, model becomes null
    :param ui_clear_icon: Custom icon to use for the clear button when using along with 'clearable' prop
    :param ui_filled: Use 'filled' design for the field
    :param ui_outlined: Use 'outlined' design for the field
    :param ui_borderless: Use 'borderless' design for the field
    :param ui_standout: Use 'standout' design for the field; Specifies classes to be applied when focused (overriding default ones)
    :param ui_label_slot: Enables label slot; You need to set it to force use of the 'label' slot if the 'label' prop is not set
    :param ui_bottom_slots: Enables bottom slots ('error', 'hint', 'counter')
    :param ui_hide_bottom_space: Do not reserve space for hint/error/counter anymore when these are not used; As a result, it also disables the animation for those; It also allows the hint/error area to stretch vertically based on its content
    :param ui_counter: Show an automatic counter on bottom right
    :param ui_rounded:
    :param ui_square: Remove border-radius so borders are squared; Overrides 'rounded' prop
    :param ui_dense:
    :param ui_item_aligned: Match inner content alignment to that of QItem
    :param ui_disable:
    :param ui_readonly:
    :param ui_autofocus: Focus field on initial component render
    :param ui_for: Used to specify the 'id' of the control and also the 'for' attribute of the label that wraps it; If no 'name' prop is specified, then it is used for this attribute as well
    :param ui_error: Does field have validation errors?
    :param ui_error_message: Validation error message (gets displayed only if 'error' is set to 'true')
    :param ui_no_error_icon: Hide error icon when there is an error
    :param ui_rules: Array of Functions/Strings; If String, then it must be a name of one of the embedded validation rules
    :param ui_reactive_rules: By default a change in the rules does not trigger a new validation until the model changes; If set to true then a change in the rules will trigger a validation; Has a performance penalty, so use it only when you really need it
    :param ui_lazy_rules: If set to boolean true then it checks validation status against the 'rules' only after field loses focus for first time; If set to 'ondemand' then it will trigger only when component's validate() method is manually called or when the wrapper QForm submits itself
    :param ui_mask: Custom mask or one of the predefined mask names
    :param ui_fill_mask: Fills string with specified characters (or underscore if value is not string) to fill mask's length
    :param ui_reverse_fill_mask: Fills string from the right side of the mask
    :param ui_unmasked_value: Model will be unmasked (won't contain tokens/separation characters)
    """

    def __init__(
        self,
        *children,
        ui_model_value: Any | None = None,
        ui_shadow_text: str | None = None,
        ui_type: str | None = None,
        ui_debounce: str | float | None = None,
        ui_maxlength: str | float | None = None,
        ui_autogrow: bool | None = None,
        ui_input_class: str | list | dict | None = None,
        ui_input_style: str | list | dict | None = None,
        ui_name: str | None = None,
        ui_label: str | None = None,
        ui_stack_label: bool | None = None,
        ui_hint: str | None = None,
        ui_hide_hint: bool | None = None,
        ui_prefix: str | None = None,
        ui_suffix: str | None = None,
        ui_label_color: Any | None = None,
        ui_color: Any | None = None,
        ui_bg_color: Any | None = None,
        ui_dark: Any | None = None,
        ui_loading: bool | None = None,
        ui_clearable: bool | None = None,
        ui_clear_icon: str | None = None,
        ui_filled: bool | None = None,
        ui_outlined: bool | None = None,
        ui_borderless: bool | None = None,
        ui_standout: bool | str | None = None,
        ui_label_slot: bool | None = None,
        ui_bottom_slots: bool | None = None,
        ui_hide_bottom_space: bool | None = None,
        ui_counter: bool | None = None,
        ui_rounded: Any | None = None,
        ui_square: bool | None = None,
        ui_dense: Any | None = None,
        ui_item_aligned: bool | None = None,
        ui_disable: Any | None = None,
        ui_readonly: Any | None = None,
        ui_autofocus: bool | None = None,
        ui_for: str | None = None,
        ui_error: bool | None = None,
        ui_error_message: str | None = None,
        ui_no_error_icon: bool | None = None,
        ui_rules: list | None = None,
        ui_reactive_rules: bool | None = None,
        ui_lazy_rules: bool | str | None = None,
        ui_mask: str | None = None,
        ui_fill_mask: bool | str | None = None,
        ui_reverse_fill_mask: bool | None = None,
        ui_unmasked_value: bool | None = None,
        **kwargs,
    ):
        super().__init__("QInput", *children, **kwargs)
        self.on("update:model-value", self.__update_model_value)

        if ui_model_value is not None:
            self._props["model-value"] = ui_model_value
        if ui_shadow_text is not None:
            self._props["shadow-text"] = ui_shadow_text
        if ui_type is not None:
            self._props["type"] = ui_type
        if ui_debounce is not None:
            self._props["debounce"] = ui_debounce
        if ui_maxlength is not None:
            self._props["maxlength"] = ui_maxlength
        if ui_autogrow is not None:
            self._props["autogrow"] = ui_autogrow
        if ui_input_class is not None:
            self._props["input-class"] = ui_input_class
        if ui_input_style is not None:
            self._props["input-style"] = ui_input_style
        if ui_name is not None:
            self._props["name"] = ui_name
        if ui_label is not None:
            self._props["label"] = ui_label
        if ui_stack_label is not None:
            self._props["stack-label"] = ui_stack_label
        if ui_hint is not None:
            self._props["hint"] = ui_hint
        if ui_hide_hint is not None:
            self._props["hide-hint"] = ui_hide_hint
        if ui_prefix is not None:
            self._props["prefix"] = ui_prefix
        if ui_suffix is not None:
            self._props["suffix"] = ui_suffix
        if ui_label_color is not None:
            self._props["label-color"] = ui_label_color
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_bg_color is not None:
            self._props["bg-color"] = ui_bg_color
        if ui_dark is not None:
            self._props["dark"] = ui_dark
        if ui_loading is not None:
            self._props["loading"] = ui_loading
        if ui_clearable is not None:
            self._props["clearable"] = ui_clearable
        if ui_clear_icon is not None:
            self._props["clear-icon"] = ui_clear_icon
        if ui_filled is not None:
            self._props["filled"] = ui_filled
        if ui_outlined is not None:
            self._props["outlined"] = ui_outlined
        if ui_borderless is not None:
            self._props["borderless"] = ui_borderless
        if ui_standout is not None:
            self._props["standout"] = ui_standout
        if ui_label_slot is not None:
            self._props["label-slot"] = ui_label_slot
        if ui_bottom_slots is not None:
            self._props["bottom-slots"] = ui_bottom_slots
        if ui_hide_bottom_space is not None:
            self._props["hide-bottom-space"] = ui_hide_bottom_space
        if ui_counter is not None:
            self._props["counter"] = ui_counter
        if ui_rounded is not None:
            self._props["rounded"] = ui_rounded
        if ui_square is not None:
            self._props["square"] = ui_square
        if ui_dense is not None:
            self._props["dense"] = ui_dense
        if ui_item_aligned is not None:
            self._props["item-aligned"] = ui_item_aligned
        if ui_disable is not None:
            self._props["disable"] = ui_disable
        if ui_readonly is not None:
            self._props["readonly"] = ui_readonly
        if ui_autofocus is not None:
            self._props["autofocus"] = ui_autofocus
        if ui_for is not None:
            self._props["for"] = ui_for
        if ui_error is not None:
            self._props["error"] = ui_error
        if ui_error_message is not None:
            self._props["error-message"] = ui_error_message
        if ui_no_error_icon is not None:
            self._props["no-error-icon"] = ui_no_error_icon

        self._rules = [] if ui_rules is None else ui_rules
        self._rules_registered = False
        if self._rules:
            self._rules_registered = True
            self.on_update_model_value(self._validate_rules)

        if ui_reactive_rules is not None:
            self._props["reactive-rules"] = ui_reactive_rules
        if ui_lazy_rules is not None:
            self._props["lazy-rules"] = ui_lazy_rules
        if ui_mask is not None:
            self._props["mask"] = ui_mask
        if ui_fill_mask is not None:
            self._props["fill-mask"] = ui_fill_mask
        if ui_reverse_fill_mask is not None:
            self._props["reverse-fill-mask"] = ui_reverse_fill_mask
        if ui_unmasked_value is not None:
            self._props["unmasked-value"] = ui_unmasked_value

    def __update_model_value(self, event: Event):
        self._set_prop("model-value", event.value)

    @property
    def ui_model_value(self):
        """Model of the component; Either use this property (along with a listener for 'update:model-value' event) OR use v-model directive"""
        return self._props.get("model-value")

    @ui_model_value.setter
    def ui_model_value(self, value):
        self._set_prop("model-value", value)

    @property
    def ui_shadow_text(self):
        """Text to be displayed as shadow at the end of the text in the control; Does NOT applies to type=file"""
        return self._props.get("shadow-text")

    @ui_shadow_text.setter
    def ui_shadow_text(self, value):
        self._set_prop("shadow-text", value)

    @property
    def ui_type(self):
        """Input type"""
        return self._props.get("type")

    @ui_type.setter
    def ui_type(self, value):
        self._set_prop("type", value)

    @property
    def ui_debounce(self):
        """Debounce amount (in milliseconds) when updating model"""
        return self._props.get("debounce")

    @ui_debounce.setter
    def ui_debounce(self, value):
        self._set_prop("debounce", value)

    @property
    def ui_maxlength(self):
        """Specify a max length of model"""
        return self._props.get("maxlength")

    @ui_maxlength.setter
    def ui_maxlength(self, value):
        self._set_prop("maxlength", value)

    @property
    def ui_autogrow(self):
        """Make field autogrow along with its content (uses a textarea)"""
        return self._props.get("autogrow")

    @ui_autogrow.setter
    def ui_autogrow(self, value):
        self._set_prop("autogrow", value)

    @property
    def ui_input_class(self):
        """Class definitions to be attributed to the underlying input tag"""
        return self._props.get("input-class")

    @ui_input_class.setter
    def ui_input_class(self, value):
        self._set_prop("input-class", value)

    @property
    def ui_input_style(self):
        """Style definitions to be attributed to the underlying input tag"""
        return self._props.get("input-style")

    @ui_input_style.setter
    def ui_input_style(self, value):
        self._set_prop("input-style", value)

    @property
    def ui_name(self):
        """Used to specify the name of the control; Useful if dealing with forms submitted directly to a URL"""
        return self._props.get("name")

    @ui_name.setter
    def ui_name(self, value):
        self._set_prop("name", value)

    @property
    def ui_label(self):
        """A text label that will “float” up above the input field, once the field gets focus"""
        return self._props.get("label")

    @ui_label.setter
    def ui_label(self, value):
        self._set_prop("label", value)

    @property
    def ui_stack_label(self):
        """Label will be always shown above the field regardless of field content (if any)"""
        return self._props.get("stack-label")

    @ui_stack_label.setter
    def ui_stack_label(self, value):
        self._set_prop("stack-label", value)

    @property
    def ui_hint(self):
        """Helper (hint) text which gets placed below your wrapped form component"""
        return self._props.get("hint")

    @ui_hint.setter
    def ui_hint(self, value):
        self._set_prop("hint", value)

    @property
    def ui_hide_hint(self):
        """Hide the helper (hint) text when field doesn't have focus"""
        return self._props.get("hide-hint")

    @ui_hide_hint.setter
    def ui_hide_hint(self, value):
        self._set_prop("hide-hint", value)

    @property
    def ui_prefix(self):
        """Prefix"""
        return self._props.get("prefix")

    @ui_prefix.setter
    def ui_prefix(self, value):
        self._set_prop("prefix", value)

    @property
    def ui_suffix(self):
        """Suffix"""
        return self._props.get("suffix")

    @ui_suffix.setter
    def ui_suffix(self, value):
        self._set_prop("suffix", value)

    @property
    def ui_label_color(self):
        """Color name for the label from the Quasar Color Palette; Overrides the 'color' prop; The difference from 'color' prop is that the label will always have this color, even when field is not focused"""
        return self._props.get("label-color")

    @ui_label_color.setter
    def ui_label_color(self, value):
        self._set_prop("label-color", value)

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_bg_color(self):
        return self._props.get("bg-color")

    @ui_bg_color.setter
    def ui_bg_color(self, value):
        self._set_prop("bg-color", value)

    @property
    def ui_dark(self):
        return self._props.get("dark")

    @ui_dark.setter
    def ui_dark(self, value):
        self._set_prop("dark", value)

    @property
    def ui_loading(self):
        """Signals the user a process is in progress by displaying a spinner; Spinner can be customized by using the 'loading' slot."""
        return self._props.get("loading")

    @ui_loading.setter
    def ui_loading(self, value):
        self._set_prop("loading", value)

    @property
    def ui_clearable(self):
        """Appends clearable icon when a value (not undefined or null) is set; When clicked, model becomes null"""
        return self._props.get("clearable")

    @ui_clearable.setter
    def ui_clearable(self, value):
        self._set_prop("clearable", value)

    @property
    def ui_clear_icon(self):
        """Custom icon to use for the clear button when using along with 'clearable' prop"""
        return self._props.get("clear-icon")

    @ui_clear_icon.setter
    def ui_clear_icon(self, value):
        self._set_prop("clear-icon", value)

    @property
    def ui_filled(self):
        """Use 'filled' design for the field"""
        return self._props.get("filled")

    @ui_filled.setter
    def ui_filled(self, value):
        self._set_prop("filled", value)

    @property
    def ui_outlined(self):
        """Use 'outlined' design for the field"""
        return self._props.get("outlined")

    @ui_outlined.setter
    def ui_outlined(self, value):
        self._set_prop("outlined", value)

    @property
    def ui_borderless(self):
        """Use 'borderless' design for the field"""
        return self._props.get("borderless")

    @ui_borderless.setter
    def ui_borderless(self, value):
        self._set_prop("borderless", value)

    @property
    def ui_standout(self):
        """Use 'standout' design for the field; Specifies classes to be applied when focused (overriding default ones)"""
        return self._props.get("standout")

    @ui_standout.setter
    def ui_standout(self, value):
        self._set_prop("standout", value)

    @property
    def ui_label_slot(self):
        """Enables label slot; You need to set it to force use of the 'label' slot if the 'label' prop is not set"""
        return self._props.get("label-slot")

    @ui_label_slot.setter
    def ui_label_slot(self, value):
        self._set_prop("label-slot", value)

    @property
    def ui_bottom_slots(self):
        """Enables bottom slots ('error', 'hint', 'counter')"""
        return self._props.get("bottom-slots")

    @ui_bottom_slots.setter
    def ui_bottom_slots(self, value):
        self._set_prop("bottom-slots", value)

    @property
    def ui_hide_bottom_space(self):
        """Do not reserve space for hint/error/counter anymore when these are not used; As a result, it also disables the animation for those; It also allows the hint/error area to stretch vertically based on its content"""
        return self._props.get("hide-bottom-space")

    @ui_hide_bottom_space.setter
    def ui_hide_bottom_space(self, value):
        self._set_prop("hide-bottom-space", value)

    @property
    def ui_counter(self):
        """Show an automatic counter on bottom right"""
        return self._props.get("counter")

    @ui_counter.setter
    def ui_counter(self, value):
        self._set_prop("counter", value)

    @property
    def ui_rounded(self):
        return self._props.get("rounded")

    @ui_rounded.setter
    def ui_rounded(self, value):
        self._set_prop("rounded", value)

    @property
    def ui_square(self):
        """Remove border-radius so borders are squared; Overrides 'rounded' prop"""
        return self._props.get("square")

    @ui_square.setter
    def ui_square(self, value):
        self._set_prop("square", value)

    @property
    def ui_dense(self):
        return self._props.get("dense")

    @ui_dense.setter
    def ui_dense(self, value):
        self._set_prop("dense", value)

    @property
    def ui_item_aligned(self):
        """Match inner content alignment to that of QItem"""
        return self._props.get("item-aligned")

    @ui_item_aligned.setter
    def ui_item_aligned(self, value):
        self._set_prop("item-aligned", value)

    @property
    def ui_disable(self):
        return self._props.get("disable")

    @ui_disable.setter
    def ui_disable(self, value):
        self._set_prop("disable", value)

    @property
    def ui_readonly(self):
        return self._props.get("readonly")

    @ui_readonly.setter
    def ui_readonly(self, value):
        self._set_prop("readonly", value)

    @property
    def ui_autofocus(self):
        """Focus field on initial component render"""
        return self._props.get("autofocus")

    @ui_autofocus.setter
    def ui_autofocus(self, value):
        self._set_prop("autofocus", value)

    @property
    def ui_for(self):
        """Used to specify the 'id' of the control and also the 'for' attribute of the label that wraps it; If no 'name' prop is specified, then it is used for this attribute as well"""
        return self._props.get("for")

    @ui_for.setter
    def ui_for(self, value):
        self._set_prop("for", value)

    @property
    def ui_error(self):
        """Does field have validation errors?"""
        return self._props.get("error")

    @ui_error.setter
    def ui_error(self, value):
        self._set_prop("error", value)

    @property
    def ui_error_message(self):
        """Validation error message (gets displayed only if 'error' is set to 'true')"""
        return self._props.get("error-message")

    @ui_error_message.setter
    def ui_error_message(self, value):
        self._set_prop("error-message", value)

    @property
    def ui_no_error_icon(self):
        """Hide error icon when there is an error"""
        return self._props.get("no-error-icon")

    @ui_no_error_icon.setter
    def ui_no_error_icon(self, value):
        self._set_prop("no-error-icon", value)

    @property
    def ui_rules(self):
        """Array of Functions/Strings; If String, then it must be a name of one of the embedded validation rules"""
        return self._rules

    @ui_rules.setter
    def ui_rules(self, value):
        self._rules = value
        if self._rules and not self._rules_registered:
            self._rules_registered = True
            self.on_update_model_value(self._validate_rules)

    def _validate_rules(self):
        for rule in self.ui_rules:
            value = rule(self.ui_model_value)
            if isinstance(value, str) and value != "":
                self.ui_error_message = value
                self.ui_error = True
                return
        self.ui_error = None

    @property
    def ui_reactive_rules(self):
        """By default a change in the rules does not trigger a new validation until the model changes; If set to true then a change in the rules will trigger a validation; Has a performance penalty, so use it only when you really need it"""
        return self._props.get("reactive-rules")

    @ui_reactive_rules.setter
    def ui_reactive_rules(self, value):
        self._set_prop("reactive-rules", value)

    @property
    def ui_lazy_rules(self):
        """If set to boolean true then it checks validation status against the 'rules' only after field loses focus for first time; If set to 'ondemand' then it will trigger only when component's validate() method is manually called or when the wrapper QForm submits itself"""
        return self._props.get("lazy-rules")

    @ui_lazy_rules.setter
    def ui_lazy_rules(self, value):
        self._set_prop("lazy-rules", value)

    @property
    def ui_mask(self):
        """Custom mask or one of the predefined mask names"""
        return self._props.get("mask")

    @ui_mask.setter
    def ui_mask(self, value):
        self._set_prop("mask", value)

    @property
    def ui_fill_mask(self):
        """Fills string with specified characters (or underscore if value is not string) to fill mask's length"""
        return self._props.get("fill-mask")

    @ui_fill_mask.setter
    def ui_fill_mask(self, value):
        self._set_prop("fill-mask", value)

    @property
    def ui_reverse_fill_mask(self):
        """Fills string from the right side of the mask"""
        return self._props.get("reverse-fill-mask")

    @ui_reverse_fill_mask.setter
    def ui_reverse_fill_mask(self, value):
        self._set_prop("reverse-fill-mask", value)

    @property
    def ui_unmasked_value(self):
        """Model will be unmasked (won't contain tokens/separation characters)"""
        return self._props.get("unmasked-value")

    @ui_unmasked_value.setter
    def ui_unmasked_value(self, value):
        self._set_prop("unmasked-value", value)

    @property
    def ui_slot_after(self):
        """Append outer field; Suggestions: QIcon, QBtn"""
        return self.ui_slots.get("after", [])

    @ui_slot_after.setter
    def ui_slot_after(self, value):
        self._set_slot("after", value)

    @property
    def ui_slot_append(self):
        """Append to inner field; Suggestions: QIcon, QBtn"""
        return self.ui_slots.get("append", [])

    @ui_slot_append.setter
    def ui_slot_append(self, value):
        self._set_slot("append", value)

    @property
    def ui_slot_before(self):
        """Prepend outer field; Suggestions: QIcon, QBtn"""
        return self.ui_slots.get("before", [])

    @ui_slot_before.setter
    def ui_slot_before(self, value):
        self._set_slot("before", value)

    @property
    def ui_slot_counter(self):
        """Slot for counter text; Enabled only if 'bottom-slots' prop is used; Suggestion: <div>"""
        return self.ui_slots.get("counter", [])

    @ui_slot_counter.setter
    def ui_slot_counter(self, value):
        self._set_slot("counter", value)

    @property
    def ui_slot_error(self):
        """Slot for errors; Enabled only if 'bottom-slots' prop is used; Suggestion: <div>"""
        return self.ui_slots.get("error", [])

    @ui_slot_error.setter
    def ui_slot_error(self, value):
        self._set_slot("error", value)

    @property
    def ui_slot_hint(self):
        """Slot for hint text; Enabled only if 'bottom-slots' prop is used; Suggestion: <div>"""
        return self.ui_slots.get("hint", [])

    @ui_slot_hint.setter
    def ui_slot_hint(self, value):
        self._set_slot("hint", value)

    @property
    def ui_slot_label(self):
        """Slot for label; Used only if 'label-slot' prop is set or the 'label' prop is set; When it is used the text in the 'label' prop is ignored"""
        return self.ui_slots.get("label", [])

    @ui_slot_label.setter
    def ui_slot_label(self, value):
        self._set_slot("label", value)

    @property
    def ui_slot_loading(self):
        """Override default spinner when component is in loading mode; Use in conjunction with 'loading' prop"""
        return self.ui_slots.get("loading", [])

    @ui_slot_loading.setter
    def ui_slot_loading(self, value):
        self._set_slot("loading", value)

    @property
    def ui_slot_prepend(self):
        """Prepend inner field; Suggestions: QIcon, QBtn"""
        return self.ui_slots.get("prepend", [])

    @ui_slot_prepend.setter
    def ui_slot_prepend(self, value):
        self._set_slot("prepend", value)

    def on_animationend(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("animationend", handler, arg)

    def on_blur(self, handler: Callable, arg: object = None):
        """
        Emitted when component loses focus

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("blur", handler, arg)

    def on_change(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("change", handler, arg)

    def on_clear(self, handler: Callable, arg: object = None):
        """
        When using the 'clearable' property, this event is emitted when the clear icon is clicked

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("clear", handler, arg)

    def on_click(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("click.stop", handler, arg)

    def on_focus(self, handler: Callable, arg: object = None):
        """
        Emitted when component gets focused

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("focus", handler, arg)

    def on_keydown(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("keydown", handler, arg)

    def on_paste(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("paste", handler, arg)

    def on_update_model_value(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("update:model-value", handler, arg)

    def ui_blur(self):
        """Blur component (lose focus)"""
        self._js_call_method("blur")

    def ui_focus(self):
        """Focus component"""
        self._js_call_method("focus")

    def ui_getNativeElement(self):
        """DEPRECATED; Access 'nativeEl' directly instead; Get the native input/textarea DOM Element"""
        self._js_call_method("getNativeElement")

    def ui_resetValidation(self):
        """Reset validation status"""
        self._js_call_method("resetValidation")

    def ui_select(self):
        """Select input text"""
        self._js_call_method("select")

    def ui_validate(self, ui_value=None):
        """Trigger a validation"""
        kwargs = {}
        if ui_value is not None:
            kwargs["value"] = ui_value
        self._js_call_method("validate", [kwargs])

    def _get_js_methods(self):
        return [
            "blur",
            "focus",
            "getNativeElement",
            "resetValidation",
            "select",
            "validate",
        ]


class QIntersection(Component):
    """
    Quasar Component: `QIntersection <https://v2.quasar.dev/vue-components/intersection>`__

    :param ui_tag:
    :param ui_once: Get triggered only once
    :param ui_ssr_prerender: Pre-render content on server side if using SSR (use it to pre-render above the fold content)
    :param ui_root: [Intersection API root prop] Lets you define an alternative to the viewport as your root (through its DOM element); It is important to keep in mind that root needs to be an ancestor of the observed element
    :param ui_margin: [Intersection API rootMargin prop] Allows you to specify the margins for the root, effectively allowing you to either grow or shrink the area used for intersections
    :param ui_threshold: [Intersection API threshold prop] Threshold(s) at which to trigger, specified as a ratio, or list of ratios, of (visible area / total area) of the observed element
    :param ui_transition:
    :param ui_transition_duration: Transition duration (in milliseconds, without unit)
    :param ui_disable: Disable visibility observable (content will remain as it was, visible or hidden)
    """

    def __init__(
        self,
        *children,
        ui_tag: Any | None = None,
        ui_once: bool | None = None,
        ui_ssr_prerender: bool | None = None,
        ui_root: Any | None = None,
        ui_margin: str | None = None,
        ui_threshold: list | float | None = None,
        ui_transition: Any | None = None,
        ui_transition_duration: str | float | None = None,
        ui_disable: bool | None = None,
        **kwargs,
    ):
        super().__init__("QIntersection", *children, **kwargs)
        if ui_tag is not None:
            self._props["tag"] = ui_tag
        if ui_once is not None:
            self._props["once"] = ui_once
        if ui_ssr_prerender is not None:
            self._props["ssr-prerender"] = ui_ssr_prerender
        if ui_root is not None:
            self._props["root"] = ui_root
        if ui_margin is not None:
            self._props["margin"] = ui_margin
        if ui_threshold is not None:
            self._props["threshold"] = ui_threshold
        if ui_transition is not None:
            self._props["transition"] = ui_transition
        if ui_transition_duration is not None:
            self._props["transition-duration"] = ui_transition_duration
        if ui_disable is not None:
            self._props["disable"] = ui_disable

    @property
    def ui_tag(self):
        return self._props.get("tag")

    @ui_tag.setter
    def ui_tag(self, value):
        self._set_prop("tag", value)

    @property
    def ui_once(self):
        """Get triggered only once"""
        return self._props.get("once")

    @ui_once.setter
    def ui_once(self, value):
        self._set_prop("once", value)

    @property
    def ui_ssr_prerender(self):
        """Pre-render content on server side if using SSR (use it to pre-render above the fold content)"""
        return self._props.get("ssr-prerender")

    @ui_ssr_prerender.setter
    def ui_ssr_prerender(self, value):
        self._set_prop("ssr-prerender", value)

    @property
    def ui_root(self):
        """[Intersection API root prop] Lets you define an alternative to the viewport as your root (through its DOM element); It is important to keep in mind that root needs to be an ancestor of the observed element"""
        return self._props.get("root")

    @ui_root.setter
    def ui_root(self, value):
        self._set_prop("root", value)

    @property
    def ui_margin(self):
        """[Intersection API rootMargin prop] Allows you to specify the margins for the root, effectively allowing you to either grow or shrink the area used for intersections"""
        return self._props.get("margin")

    @ui_margin.setter
    def ui_margin(self, value):
        self._set_prop("margin", value)

    @property
    def ui_threshold(self):
        """[Intersection API threshold prop] Threshold(s) at which to trigger, specified as a ratio, or list of ratios, of (visible area / total area) of the observed element"""
        return self._props.get("threshold")

    @ui_threshold.setter
    def ui_threshold(self, value):
        self._set_prop("threshold", value)

    @property
    def ui_transition(self):
        return self._props.get("transition")

    @ui_transition.setter
    def ui_transition(self, value):
        self._set_prop("transition", value)

    @property
    def ui_transition_duration(self):
        """Transition duration (in milliseconds, without unit)"""
        return self._props.get("transition-duration")

    @ui_transition_duration.setter
    def ui_transition_duration(self, value):
        self._set_prop("transition-duration", value)

    @property
    def ui_disable(self):
        """Disable visibility observable (content will remain as it was, visible or hidden)"""
        return self._props.get("disable")

    @ui_disable.setter
    def ui_disable(self, value):
        self._set_prop("disable", value)

    @property
    def ui_slot_hidden(self):
        """Slot for content to render when component is not on screen; Example: a text that the user can search for with the browser's search function"""
        return self.ui_slots.get("hidden", [])

    @ui_slot_hidden.setter
    def ui_slot_hidden(self, value):
        self._set_slot("hidden", value)

    def on_visibility(self, handler: Callable, arg: object = None):
        """
        Fires when visibility changes

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("visibility", handler, arg)

    def _get_js_methods(self):
        return []


class QList(Component):
    """
    Quasar Component: `QList <https://v2.quasar.dev/vue-components/list-and-list-items>`__

    :param ui_bordered:
    :param ui_dense:
    :param ui_separator: Applies a separator between contained items
    :param ui_dark:
    :param ui_padding: Applies a material design-like padding on top and bottom
    :param ui_tag:
    """

    def __init__(
        self,
        *children,
        ui_bordered: Any | None = None,
        ui_dense: Any | None = None,
        ui_separator: bool | None = None,
        ui_dark: Any | None = None,
        ui_padding: bool | None = None,
        ui_tag: Any | None = None,
        **kwargs,
    ):
        super().__init__("QList", *children, **kwargs)
        if ui_bordered is not None:
            self._props["bordered"] = ui_bordered
        if ui_dense is not None:
            self._props["dense"] = ui_dense
        if ui_separator is not None:
            self._props["separator"] = ui_separator
        if ui_dark is not None:
            self._props["dark"] = ui_dark
        if ui_padding is not None:
            self._props["padding"] = ui_padding
        if ui_tag is not None:
            self._props["tag"] = ui_tag

    @property
    def ui_bordered(self):
        return self._props.get("bordered")

    @ui_bordered.setter
    def ui_bordered(self, value):
        self._set_prop("bordered", value)

    @property
    def ui_dense(self):
        return self._props.get("dense")

    @ui_dense.setter
    def ui_dense(self, value):
        self._set_prop("dense", value)

    @property
    def ui_separator(self):
        """Applies a separator between contained items"""
        return self._props.get("separator")

    @ui_separator.setter
    def ui_separator(self, value):
        self._set_prop("separator", value)

    @property
    def ui_dark(self):
        return self._props.get("dark")

    @ui_dark.setter
    def ui_dark(self, value):
        self._set_prop("dark", value)

    @property
    def ui_padding(self):
        """Applies a material design-like padding on top and bottom"""
        return self._props.get("padding")

    @ui_padding.setter
    def ui_padding(self, value):
        self._set_prop("padding", value)

    @property
    def ui_tag(self):
        return self._props.get("tag")

    @ui_tag.setter
    def ui_tag(self, value):
        self._set_prop("tag", value)

    def _get_js_methods(self):
        return []


class QItem(Component):
    """
    Quasar Component: `QItem <https://v2.quasar.dev/vue-components/list-and-list-items>`__

    :param ui_active: Put item into 'active' state
    :param ui_dark:
    :param ui_clickable: Is QItem clickable? If it's the case, then it will add hover effects and emit 'click' events
    :param ui_dense:
    :param ui_inset_level: Apply an inset; Useful when avatar/left side is missing but you want to align content with other items that do have a left side, or when you're building a menu
    :param ui_tabindex:
    :param ui_tag: HTML tag to render; Suggestion: use 'label' when encapsulating a QCheckbox/QRadio/QToggle so that when user clicks/taps on the whole item it will trigger a model change for the mentioned components
    :param ui_manual_focus: Put item into a manual focus state; Enables 'focused' prop which will determine if item is focused or not, rather than relying on native hover/focus states
    :param ui_focused: Determines focus state, ONLY if 'manual-focus' is enabled / set to true
    :param ui_to: Equivalent to Vue Router <router-link> 'to' property; Superseded by 'href' prop if used
    :param ui_exact: Equivalent to Vue Router <router-link> 'exact' property; Superseded by 'href' prop if used
    :param ui_replace: Equivalent to Vue Router <router-link> 'replace' property; Superseded by 'href' prop if used
    :param ui_active_class: Equivalent to Vue Router <router-link> 'active-class' property; Superseded by 'href' prop if used
    :param ui_exact_active_class: Equivalent to Vue Router <router-link> 'active-class' property; Superseded by 'href' prop if used
    :param ui_href: Native <a> link href attribute; Has priority over the 'to'/'exact'/'replace'/'active-class'/'exact-active-class' props
    :param ui_target: Native <a> link target attribute; Use it only along with 'href' prop; Has priority over the 'to'/'exact'/'replace'/'active-class'/'exact-active-class' props
    :param ui_disable:
    """

    def __init__(
        self,
        *children,
        ui_active: bool | None = None,
        ui_dark: Any | None = None,
        ui_clickable: bool | None = None,
        ui_dense: Any | None = None,
        ui_inset_level: float | None = None,
        ui_tabindex: Any | None = None,
        ui_tag: Any | None = None,
        ui_manual_focus: bool | None = None,
        ui_focused: bool | None = None,
        ui_to: str | dict | None = None,
        ui_exact: bool | None = None,
        ui_replace: bool | None = None,
        ui_active_class: str | None = None,
        ui_exact_active_class: str | None = None,
        ui_href: str | None = None,
        ui_target: str | None = None,
        ui_disable: Any | None = None,
        **kwargs,
    ):
        super().__init__("QItem", *children, **kwargs)
        if ui_active is not None:
            self._props["active"] = ui_active
        if ui_dark is not None:
            self._props["dark"] = ui_dark
        if ui_clickable is not None:
            self._props["clickable"] = ui_clickable
        if ui_dense is not None:
            self._props["dense"] = ui_dense
        if ui_inset_level is not None:
            self._props["inset-level"] = ui_inset_level
        if ui_tabindex is not None:
            self._props["tabindex"] = ui_tabindex
        if ui_tag is not None:
            self._props["tag"] = ui_tag
        if ui_manual_focus is not None:
            self._props["manual-focus"] = ui_manual_focus
        if ui_focused is not None:
            self._props["focused"] = ui_focused
        if ui_to is not None:
            self._props["to"] = ui_to
        if ui_exact is not None:
            self._props["exact"] = ui_exact
        if ui_replace is not None:
            self._props["replace"] = ui_replace
        if ui_active_class is not None:
            self._props["active-class"] = ui_active_class
        if ui_exact_active_class is not None:
            self._props["exact-active-class"] = ui_exact_active_class
        if ui_href is not None:
            self._props["href"] = ui_href
        if ui_target is not None:
            self._props["target"] = ui_target
        if ui_disable is not None:
            self._props["disable"] = ui_disable

    @property
    def ui_active(self):
        """Put item into 'active' state"""
        return self._props.get("active")

    @ui_active.setter
    def ui_active(self, value):
        self._set_prop("active", value)

    @property
    def ui_dark(self):
        return self._props.get("dark")

    @ui_dark.setter
    def ui_dark(self, value):
        self._set_prop("dark", value)

    @property
    def ui_clickable(self):
        """Is QItem clickable? If it's the case, then it will add hover effects and emit 'click' events"""
        return self._props.get("clickable")

    @ui_clickable.setter
    def ui_clickable(self, value):
        self._set_prop("clickable", value)

    @property
    def ui_dense(self):
        return self._props.get("dense")

    @ui_dense.setter
    def ui_dense(self, value):
        self._set_prop("dense", value)

    @property
    def ui_inset_level(self):
        """Apply an inset; Useful when avatar/left side is missing but you want to align content with other items that do have a left side, or when you're building a menu"""
        return self._props.get("inset-level")

    @ui_inset_level.setter
    def ui_inset_level(self, value):
        self._set_prop("inset-level", value)

    @property
    def ui_tabindex(self):
        return self._props.get("tabindex")

    @ui_tabindex.setter
    def ui_tabindex(self, value):
        self._set_prop("tabindex", value)

    @property
    def ui_tag(self):
        """HTML tag to render; Suggestion: use 'label' when encapsulating a QCheckbox/QRadio/QToggle so that when user clicks/taps on the whole item it will trigger a model change for the mentioned components"""
        return self._props.get("tag")

    @ui_tag.setter
    def ui_tag(self, value):
        self._set_prop("tag", value)

    @property
    def ui_manual_focus(self):
        """Put item into a manual focus state; Enables 'focused' prop which will determine if item is focused or not, rather than relying on native hover/focus states"""
        return self._props.get("manual-focus")

    @ui_manual_focus.setter
    def ui_manual_focus(self, value):
        self._set_prop("manual-focus", value)

    @property
    def ui_focused(self):
        """Determines focus state, ONLY if 'manual-focus' is enabled / set to true"""
        return self._props.get("focused")

    @ui_focused.setter
    def ui_focused(self, value):
        self._set_prop("focused", value)

    @property
    def ui_to(self):
        """Equivalent to Vue Router <router-link> 'to' property; Superseded by 'href' prop if used"""
        return self._props.get("to")

    @ui_to.setter
    def ui_to(self, value):
        self._set_prop("to", value)

    @property
    def ui_exact(self):
        """Equivalent to Vue Router <router-link> 'exact' property; Superseded by 'href' prop if used"""
        return self._props.get("exact")

    @ui_exact.setter
    def ui_exact(self, value):
        self._set_prop("exact", value)

    @property
    def ui_replace(self):
        """Equivalent to Vue Router <router-link> 'replace' property; Superseded by 'href' prop if used"""
        return self._props.get("replace")

    @ui_replace.setter
    def ui_replace(self, value):
        self._set_prop("replace", value)

    @property
    def ui_active_class(self):
        """Equivalent to Vue Router <router-link> 'active-class' property; Superseded by 'href' prop if used"""
        return self._props.get("active-class")

    @ui_active_class.setter
    def ui_active_class(self, value):
        self._set_prop("active-class", value)

    @property
    def ui_exact_active_class(self):
        """Equivalent to Vue Router <router-link> 'active-class' property; Superseded by 'href' prop if used"""
        return self._props.get("exact-active-class")

    @ui_exact_active_class.setter
    def ui_exact_active_class(self, value):
        self._set_prop("exact-active-class", value)

    @property
    def ui_href(self):
        """Native <a> link href attribute; Has priority over the 'to'/'exact'/'replace'/'active-class'/'exact-active-class' props"""
        return self._props.get("href")

    @ui_href.setter
    def ui_href(self, value):
        self._set_prop("href", value)

    @property
    def ui_target(self):
        """Native <a> link target attribute; Use it only along with 'href' prop; Has priority over the 'to'/'exact'/'replace'/'active-class'/'exact-active-class' props"""
        return self._props.get("target")

    @ui_target.setter
    def ui_target(self, value):
        self._set_prop("target", value)

    @property
    def ui_disable(self):
        return self._props.get("disable")

    @ui_disable.setter
    def ui_disable(self, value):
        self._set_prop("disable", value)

    def on_click(self, handler: Callable, arg: object = None):
        """
        Emitted when the component is clicked

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("click.stop", handler, arg)

    def on_keyup(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("keyup", handler, arg)

    def _get_js_methods(self):
        return []


class QItemSection(Component):
    """
    Quasar Component: `QItemSection <https://v2.quasar.dev/vue-components/list-and-list-items>`__

    :param ui_avatar: Render an avatar item side (does not needs 'side' prop to be set)
    :param ui_thumbnail: Render a thumbnail item side (does not needs 'side' prop to be set)
    :param ui_side: Renders as a side of the item
    :param ui_top: Align content to top (useful for multi-line items)
    :param ui_no_wrap: Do not wrap text (useful for item's main content)
    """

    def __init__(
        self,
        *children,
        ui_avatar: bool | None = None,
        ui_thumbnail: bool | None = None,
        ui_side: bool | None = None,
        ui_top: bool | None = None,
        ui_no_wrap: bool | None = None,
        **kwargs,
    ):
        super().__init__("QItemSection", *children, **kwargs)
        if ui_avatar is not None:
            self._props["avatar"] = ui_avatar
        if ui_thumbnail is not None:
            self._props["thumbnail"] = ui_thumbnail
        if ui_side is not None:
            self._props["side"] = ui_side
        if ui_top is not None:
            self._props["top"] = ui_top
        if ui_no_wrap is not None:
            self._props["no-wrap"] = ui_no_wrap

    @property
    def ui_avatar(self):
        """Render an avatar item side (does not needs 'side' prop to be set)"""
        return self._props.get("avatar")

    @ui_avatar.setter
    def ui_avatar(self, value):
        self._set_prop("avatar", value)

    @property
    def ui_thumbnail(self):
        """Render a thumbnail item side (does not needs 'side' prop to be set)"""
        return self._props.get("thumbnail")

    @ui_thumbnail.setter
    def ui_thumbnail(self, value):
        self._set_prop("thumbnail", value)

    @property
    def ui_side(self):
        """Renders as a side of the item"""
        return self._props.get("side")

    @ui_side.setter
    def ui_side(self, value):
        self._set_prop("side", value)

    @property
    def ui_top(self):
        """Align content to top (useful for multi-line items)"""
        return self._props.get("top")

    @ui_top.setter
    def ui_top(self, value):
        self._set_prop("top", value)

    @property
    def ui_no_wrap(self):
        """Do not wrap text (useful for item's main content)"""
        return self._props.get("no-wrap")

    @ui_no_wrap.setter
    def ui_no_wrap(self, value):
        self._set_prop("no-wrap", value)

    def _get_js_methods(self):
        return []


class QItemLabel(Component):
    """
    Quasar Component: `QItemLabel <https://v2.quasar.dev/vue-components/list-and-list-items>`__

    :param ui_overline: Renders an overline label
    :param ui_caption: Renders a caption label
    :param ui_header: Renders a header label
    :param ui_lines: Apply ellipsis when there's not enough space to render on the specified number of lines;
    """

    def __init__(
        self,
        *children,
        ui_overline: bool | None = None,
        ui_caption: bool | None = None,
        ui_header: bool | None = None,
        ui_lines: float | str | None = None,
        **kwargs,
    ):
        super().__init__("QItemLabel", *children, **kwargs)
        if ui_overline is not None:
            self._props["overline"] = ui_overline
        if ui_caption is not None:
            self._props["caption"] = ui_caption
        if ui_header is not None:
            self._props["header"] = ui_header
        if ui_lines is not None:
            self._props["lines"] = ui_lines

    @property
    def ui_overline(self):
        """Renders an overline label"""
        return self._props.get("overline")

    @ui_overline.setter
    def ui_overline(self, value):
        self._set_prop("overline", value)

    @property
    def ui_caption(self):
        """Renders a caption label"""
        return self._props.get("caption")

    @ui_caption.setter
    def ui_caption(self, value):
        self._set_prop("caption", value)

    @property
    def ui_header(self):
        """Renders a header label"""
        return self._props.get("header")

    @ui_header.setter
    def ui_header(self, value):
        self._set_prop("header", value)

    @property
    def ui_lines(self):
        """Apply ellipsis when there's not enough space to render on the specified number of lines;"""
        return self._props.get("lines")

    @ui_lines.setter
    def ui_lines(self, value):
        self._set_prop("lines", value)

    def _get_js_methods(self):
        return []


class QKnob(Component):
    """
    Quasar Component: `QKnob <https://v2.quasar.dev/vue-components/knob>`__

    :param ui_model_value: Any number to indicate the given value of the knob. Either use this property (along with a listener for 'update:modelValue' event) OR use the v-model directive
    :param ui_min: The minimum value that the model (the knob value) should start at
    :param ui_max: The maximum value that the model (the knob value) should go to
    :param ui_inner_min: Inner minimum value of the model; Use in case you need the model value to be inside of the track's min-max values; Needs to be higher or equal to 'min' prop; Defaults to 'min' prop
    :param ui_inner_max: Inner maximum value of the model; Use in case you need the model value to be inside of the track's min-max values; Needs to be lower or equal to 'max' prop; Defaults to 'max' prop
    :param ui_step: A number representing steps in the value of the model, while adjusting the knob
    :param ui_reverse: Reverses the direction of progress
    :param ui_instant_feedback: No animation when model changes
    :param ui_color:
    :param ui_center_color: Color name for the center part of the component from the Quasar Color Palette
    :param ui_track_color: Color name for the track of the component from the Quasar Color Palette
    :param ui_font_size: Size of text in CSS units, including unit name. Suggestion: use 'em' units to sync with component size
    :param ui_rounded: Rounding the arc of progress
    :param ui_thickness: Thickness of progress arc as a ratio (0.0 < x < 1.0) of component size
    :param ui_angle: Angle to rotate progress arc by
    :param ui_show_value: Enables the default slot and uses it (if available), otherwise it displays the 'value' prop as text; Make sure the text has enough space to be displayed inside the component
    :param ui_tabindex:
    :param ui_disable:
    :param ui_readonly:
    :param ui_size: Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)
    :param ui_name: Used to specify the name of the control; Useful if dealing with forms submitted directly to a URL
    """

    def __init__(
        self,
        *children,
        ui_model_value: float | None = None,
        ui_min: float | None = None,
        ui_max: float | None = None,
        ui_inner_min: float | None = None,
        ui_inner_max: float | None = None,
        ui_step: float | None = None,
        ui_reverse: bool | None = None,
        ui_instant_feedback: bool | None = None,
        ui_color: Any | None = None,
        ui_center_color: Any | None = None,
        ui_track_color: Any | None = None,
        ui_font_size: str | None = None,
        ui_rounded: bool | None = None,
        ui_thickness: float | None = None,
        ui_angle: float | None = None,
        ui_show_value: bool | None = None,
        ui_tabindex: Any | None = None,
        ui_disable: Any | None = None,
        ui_readonly: Any | None = None,
        ui_size: str | None = None,
        ui_name: str | None = None,
        **kwargs,
    ):
        super().__init__("QKnob", *children, **kwargs)
        self.on("update:model-value", self.__update_model_value)

        if ui_model_value is not None:
            self._props["model-value"] = ui_model_value
        if ui_min is not None:
            self._props["min"] = ui_min
        if ui_max is not None:
            self._props["max"] = ui_max
        if ui_inner_min is not None:
            self._props["inner-min"] = ui_inner_min
        if ui_inner_max is not None:
            self._props["inner-max"] = ui_inner_max
        if ui_step is not None:
            self._props["step"] = ui_step
        if ui_reverse is not None:
            self._props["reverse"] = ui_reverse
        if ui_instant_feedback is not None:
            self._props["instant-feedback"] = ui_instant_feedback
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_center_color is not None:
            self._props["center-color"] = ui_center_color
        if ui_track_color is not None:
            self._props["track-color"] = ui_track_color
        if ui_font_size is not None:
            self._props["font-size"] = ui_font_size
        if ui_rounded is not None:
            self._props["rounded"] = ui_rounded
        if ui_thickness is not None:
            self._props["thickness"] = ui_thickness
        if ui_angle is not None:
            self._props["angle"] = ui_angle
        if ui_show_value is not None:
            self._props["show-value"] = ui_show_value
        if ui_tabindex is not None:
            self._props["tabindex"] = ui_tabindex
        if ui_disable is not None:
            self._props["disable"] = ui_disable
        if ui_readonly is not None:
            self._props["readonly"] = ui_readonly
        if ui_size is not None:
            self._props["size"] = ui_size
        if ui_name is not None:
            self._props["name"] = ui_name

    def __update_model_value(self, event: Event):
        self._set_prop("model-value", event.value)

    @property
    def ui_model_value(self):
        """Any number to indicate the given value of the knob. Either use this property (along with a listener for 'update:modelValue' event) OR use the v-model directive"""
        return self._props.get("model-value")

    @ui_model_value.setter
    def ui_model_value(self, value):
        self._set_prop("model-value", value)

    @property
    def ui_min(self):
        """The minimum value that the model (the knob value) should start at"""
        return self._props.get("min")

    @ui_min.setter
    def ui_min(self, value):
        self._set_prop("min", value)

    @property
    def ui_max(self):
        """The maximum value that the model (the knob value) should go to"""
        return self._props.get("max")

    @ui_max.setter
    def ui_max(self, value):
        self._set_prop("max", value)

    @property
    def ui_inner_min(self):
        """Inner minimum value of the model; Use in case you need the model value to be inside of the track's min-max values; Needs to be higher or equal to 'min' prop; Defaults to 'min' prop"""
        return self._props.get("inner-min")

    @ui_inner_min.setter
    def ui_inner_min(self, value):
        self._set_prop("inner-min", value)

    @property
    def ui_inner_max(self):
        """Inner maximum value of the model; Use in case you need the model value to be inside of the track's min-max values; Needs to be lower or equal to 'max' prop; Defaults to 'max' prop"""
        return self._props.get("inner-max")

    @ui_inner_max.setter
    def ui_inner_max(self, value):
        self._set_prop("inner-max", value)

    @property
    def ui_step(self):
        """A number representing steps in the value of the model, while adjusting the knob"""
        return self._props.get("step")

    @ui_step.setter
    def ui_step(self, value):
        self._set_prop("step", value)

    @property
    def ui_reverse(self):
        """Reverses the direction of progress"""
        return self._props.get("reverse")

    @ui_reverse.setter
    def ui_reverse(self, value):
        self._set_prop("reverse", value)

    @property
    def ui_instant_feedback(self):
        """No animation when model changes"""
        return self._props.get("instant-feedback")

    @ui_instant_feedback.setter
    def ui_instant_feedback(self, value):
        self._set_prop("instant-feedback", value)

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_center_color(self):
        """Color name for the center part of the component from the Quasar Color Palette"""
        return self._props.get("center-color")

    @ui_center_color.setter
    def ui_center_color(self, value):
        self._set_prop("center-color", value)

    @property
    def ui_track_color(self):
        """Color name for the track of the component from the Quasar Color Palette"""
        return self._props.get("track-color")

    @ui_track_color.setter
    def ui_track_color(self, value):
        self._set_prop("track-color", value)

    @property
    def ui_font_size(self):
        """Size of text in CSS units, including unit name. Suggestion: use 'em' units to sync with component size"""
        return self._props.get("font-size")

    @ui_font_size.setter
    def ui_font_size(self, value):
        self._set_prop("font-size", value)

    @property
    def ui_rounded(self):
        """Rounding the arc of progress"""
        return self._props.get("rounded")

    @ui_rounded.setter
    def ui_rounded(self, value):
        self._set_prop("rounded", value)

    @property
    def ui_thickness(self):
        """Thickness of progress arc as a ratio (0.0 < x < 1.0) of component size"""
        return self._props.get("thickness")

    @ui_thickness.setter
    def ui_thickness(self, value):
        self._set_prop("thickness", value)

    @property
    def ui_angle(self):
        """Angle to rotate progress arc by"""
        return self._props.get("angle")

    @ui_angle.setter
    def ui_angle(self, value):
        self._set_prop("angle", value)

    @property
    def ui_show_value(self):
        """Enables the default slot and uses it (if available), otherwise it displays the 'value' prop as text; Make sure the text has enough space to be displayed inside the component"""
        return self._props.get("show-value")

    @ui_show_value.setter
    def ui_show_value(self, value):
        self._set_prop("show-value", value)

    @property
    def ui_tabindex(self):
        return self._props.get("tabindex")

    @ui_tabindex.setter
    def ui_tabindex(self, value):
        self._set_prop("tabindex", value)

    @property
    def ui_disable(self):
        return self._props.get("disable")

    @ui_disable.setter
    def ui_disable(self, value):
        self._set_prop("disable", value)

    @property
    def ui_readonly(self):
        return self._props.get("readonly")

    @ui_readonly.setter
    def ui_readonly(self, value):
        self._set_prop("readonly", value)

    @property
    def ui_size(self):
        """Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)"""
        return self._props.get("size")

    @ui_size.setter
    def ui_size(self, value):
        self._set_prop("size", value)

    @property
    def ui_name(self):
        """Used to specify the name of the control; Useful if dealing with forms submitted directly to a URL"""
        return self._props.get("name")

    @ui_name.setter
    def ui_name(self, value):
        self._set_prop("name", value)

    def on_change(self, handler: Callable, arg: object = None):
        """
        Fires at the end of a knob's adjustment and offers the value of the model

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("change", handler, arg)

    def on_drag_value(self, handler: Callable, arg: object = None):
        """
        The value of the model while dragging is still in progress

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("drag-value", handler, arg)

    def on_update_model_value(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("update:model-value", handler, arg)

    def _get_js_methods(self):
        return []


class QLayout(Component):
    """
    Quasar Component: `QLayout <https://v2.quasar.dev/layout/layout>`__

    :param ui_view: Defines how your layout components (header/footer/drawer) should be placed on screen; See docs examples
    :param ui_container: Containerize the layout which means it changes the default behavior of expanding to the whole window; Useful (but not limited to) for when using on a QDialog
    """

    def __init__(
        self,
        *children,
        ui_view: str | None = None,
        ui_container: bool | None = None,
        **kwargs,
    ):
        super().__init__("QLayout", *children, **kwargs)
        if ui_view is not None:
            self._props["view"] = ui_view
        if ui_container is not None:
            self._props["container"] = ui_container

    @property
    def ui_view(self):
        """Defines how your layout components (header/footer/drawer) should be placed on screen; See docs examples"""
        return self._props.get("view")

    @ui_view.setter
    def ui_view(self, value):
        self._set_prop("view", value)

    @property
    def ui_container(self):
        """Containerize the layout which means it changes the default behavior of expanding to the whole window; Useful (but not limited to) for when using on a QDialog"""
        return self._props.get("container")

    @ui_container.setter
    def ui_container(self, value):
        self._set_prop("container", value)

    def on_resize(self, handler: Callable, arg: object = None):
        """
        Emitted when layout size (height, width) changes

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("resize", handler, arg)

    def on_scroll(self, handler: Callable, arg: object = None):
        """
        Emitted when user scrolls within layout

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("scroll", handler, arg)

    def on_scroll_height(self, handler: Callable, arg: object = None):
        """
        Emitted when the scroll size of layout changes

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("scroll-height", handler, arg)

    def _get_js_methods(self):
        return []


class QLinearProgress(Component):
    """
    Quasar Component: `QLinearProgress <https://v2.quasar.dev/vue-components/linear-progress>`__

    :param ui_value: Progress value (0.0 < x < 1.0)
    :param ui_buffer: Optional buffer value (0.0 < x < 1.0)
    :param ui_color:
    :param ui_track_color: Color name for component's track from the Quasar Color Palette
    :param ui_dark:
    :param ui_reverse: Reverse direction of progress
    :param ui_stripe: Draw stripes; For determinate state only (for performance reasons)
    :param ui_indeterminate: Put component into indeterminate mode
    :param ui_query: Put component into query mode
    :param ui_rounded:
    :param ui_instant_feedback: No transition when model changes
    :param ui_animation_speed:
    :param ui_size: Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)
    """

    def __init__(
        self,
        *children,
        ui_value: float | None = None,
        ui_buffer: float | None = None,
        ui_color: Any | None = None,
        ui_track_color: Any | None = None,
        ui_dark: Any | None = None,
        ui_reverse: bool | None = None,
        ui_stripe: bool | None = None,
        ui_indeterminate: bool | None = None,
        ui_query: bool | None = None,
        ui_rounded: Any | None = None,
        ui_instant_feedback: bool | None = None,
        ui_animation_speed: Any | None = None,
        ui_size: str | None = None,
        **kwargs,
    ):
        super().__init__("QLinearProgress", *children, **kwargs)
        if ui_value is not None:
            self._props["value"] = ui_value
        if ui_buffer is not None:
            self._props["buffer"] = ui_buffer
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_track_color is not None:
            self._props["track-color"] = ui_track_color
        if ui_dark is not None:
            self._props["dark"] = ui_dark
        if ui_reverse is not None:
            self._props["reverse"] = ui_reverse
        if ui_stripe is not None:
            self._props["stripe"] = ui_stripe
        if ui_indeterminate is not None:
            self._props["indeterminate"] = ui_indeterminate
        if ui_query is not None:
            self._props["query"] = ui_query
        if ui_rounded is not None:
            self._props["rounded"] = ui_rounded
        if ui_instant_feedback is not None:
            self._props["instant-feedback"] = ui_instant_feedback
        if ui_animation_speed is not None:
            self._props["animation-speed"] = ui_animation_speed
        if ui_size is not None:
            self._props["size"] = ui_size

    @property
    def ui_value(self):
        """Progress value (0.0 < x < 1.0)"""
        return self._props.get("value")

    @ui_value.setter
    def ui_value(self, value):
        self._set_prop("value", value)

    @property
    def ui_buffer(self):
        """Optional buffer value (0.0 < x < 1.0)"""
        return self._props.get("buffer")

    @ui_buffer.setter
    def ui_buffer(self, value):
        self._set_prop("buffer", value)

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_track_color(self):
        """Color name for component's track from the Quasar Color Palette"""
        return self._props.get("track-color")

    @ui_track_color.setter
    def ui_track_color(self, value):
        self._set_prop("track-color", value)

    @property
    def ui_dark(self):
        return self._props.get("dark")

    @ui_dark.setter
    def ui_dark(self, value):
        self._set_prop("dark", value)

    @property
    def ui_reverse(self):
        """Reverse direction of progress"""
        return self._props.get("reverse")

    @ui_reverse.setter
    def ui_reverse(self, value):
        self._set_prop("reverse", value)

    @property
    def ui_stripe(self):
        """Draw stripes; For determinate state only (for performance reasons)"""
        return self._props.get("stripe")

    @ui_stripe.setter
    def ui_stripe(self, value):
        self._set_prop("stripe", value)

    @property
    def ui_indeterminate(self):
        """Put component into indeterminate mode"""
        return self._props.get("indeterminate")

    @ui_indeterminate.setter
    def ui_indeterminate(self, value):
        self._set_prop("indeterminate", value)

    @property
    def ui_query(self):
        """Put component into query mode"""
        return self._props.get("query")

    @ui_query.setter
    def ui_query(self, value):
        self._set_prop("query", value)

    @property
    def ui_rounded(self):
        return self._props.get("rounded")

    @ui_rounded.setter
    def ui_rounded(self, value):
        self._set_prop("rounded", value)

    @property
    def ui_instant_feedback(self):
        """No transition when model changes"""
        return self._props.get("instant-feedback")

    @ui_instant_feedback.setter
    def ui_instant_feedback(self, value):
        self._set_prop("instant-feedback", value)

    @property
    def ui_animation_speed(self):
        return self._props.get("animation-speed")

    @ui_animation_speed.setter
    def ui_animation_speed(self, value):
        self._set_prop("animation-speed", value)

    @property
    def ui_size(self):
        """Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)"""
        return self._props.get("size")

    @ui_size.setter
    def ui_size(self, value):
        self._set_prop("size", value)

    def _get_js_methods(self):
        return []


class QMarkupTable(Component):
    """
    Quasar Component: `QMarkupTable <https://v2.quasar.dev/vue-components/markup-table>`__

    :param ui_dense:
    :param ui_dark:
    :param ui_flat:
    :param ui_bordered:
    :param ui_square:
    :param ui_separator: Use a separator/border between rows, columns or all cells
    :param ui_wrap_cells: Wrap text within table cells
    """

    def __init__(
        self,
        *children,
        ui_dense: Any | None = None,
        ui_dark: Any | None = None,
        ui_flat: Any | None = None,
        ui_bordered: Any | None = None,
        ui_square: Any | None = None,
        ui_separator: str | None = None,
        ui_wrap_cells: bool | None = None,
        **kwargs,
    ):
        super().__init__("QMarkupTable", *children, **kwargs)
        if ui_dense is not None:
            self._props["dense"] = ui_dense
        if ui_dark is not None:
            self._props["dark"] = ui_dark
        if ui_flat is not None:
            self._props["flat"] = ui_flat
        if ui_bordered is not None:
            self._props["bordered"] = ui_bordered
        if ui_square is not None:
            self._props["square"] = ui_square
        if ui_separator is not None:
            self._props["separator"] = ui_separator
        if ui_wrap_cells is not None:
            self._props["wrap-cells"] = ui_wrap_cells

    @property
    def ui_dense(self):
        return self._props.get("dense")

    @ui_dense.setter
    def ui_dense(self, value):
        self._set_prop("dense", value)

    @property
    def ui_dark(self):
        return self._props.get("dark")

    @ui_dark.setter
    def ui_dark(self, value):
        self._set_prop("dark", value)

    @property
    def ui_flat(self):
        return self._props.get("flat")

    @ui_flat.setter
    def ui_flat(self, value):
        self._set_prop("flat", value)

    @property
    def ui_bordered(self):
        return self._props.get("bordered")

    @ui_bordered.setter
    def ui_bordered(self, value):
        self._set_prop("bordered", value)

    @property
    def ui_square(self):
        return self._props.get("square")

    @ui_square.setter
    def ui_square(self, value):
        self._set_prop("square", value)

    @property
    def ui_separator(self):
        """Use a separator/border between rows, columns or all cells"""
        return self._props.get("separator")

    @ui_separator.setter
    def ui_separator(self, value):
        self._set_prop("separator", value)

    @property
    def ui_wrap_cells(self):
        """Wrap text within table cells"""
        return self._props.get("wrap-cells")

    @ui_wrap_cells.setter
    def ui_wrap_cells(self, value):
        self._set_prop("wrap-cells", value)

    def _get_js_methods(self):
        return []


class QMenu(Component):
    """
    Quasar Component: `QMenu <https://v2.quasar.dev/vue-components/menu>`__

    :param ui_dark:
    :param ui_fit: Allows the menu to match at least the full width of its target
    :param ui_cover: Allows the menu to cover its target. When used, the 'self' and 'fit' props are no longer effective
    :param ui_anchor: Two values setting the starting position or anchor point of the menu relative to its target
    :param ui_self: Two values setting the menu's own position relative to its target
    :param ui_offset: An array of two numbers to offset the menu horizontally and vertically in pixels
    :param ui_scroll_target:
    :param ui_touch_position: Allows for the target position to be set by the mouse position, when the target of the menu is either clicked or touched
    :param ui_persistent: Allows the menu to not be dismissed by a click/tap outside of the menu or by hitting the ESC key; Also, an app route change won't dismiss it
    :param ui_no_route_dismiss: Changing route app won't dismiss the popup; No need to set it if 'persistent' prop is also set
    :param ui_auto_close: Allows any click/tap in the menu to close it; Useful instead of attaching events to each menu item that should close the menu on click/tap
    :param ui_separate_close_popup: Separate from parent menu, marking it as a separate closing point for v-close-popup (without this, chained menus close all together)
    :param ui_square: Forces content to have squared borders
    :param ui_no_refocus: (Accessibility) When Menu gets hidden, do not refocus on the DOM element that previously had focus
    :param ui_no_focus: (Accessibility) When Menu gets shown, do not switch focus on it
    :param ui_max_height: The maximum height of the menu; Size in CSS units, including unit name
    :param ui_max_width: The maximum width of the menu; Size in CSS units, including unit name
    :param ui_model_value: Model of the component defining shown/hidden state; Either use this property (along with a listener for 'update:model-value' event) OR use v-model directive
    :param ui_context_menu: Allows the component to behave like a context menu, which opens with a right mouse click (or long tap on mobile)
    :param ui_target: Configure a target element to trigger component toggle; 'true' means it enables the parent DOM element, 'false' means it disables attaching events to any DOM elements; By using a String (CSS selector) or a DOM element it attaches the events to the specified DOM element (if it exists)
    :param ui_no_parent_event: Skips attaching events to the target DOM element (that trigger the element to get shown)
    :param ui_transition_show:
    :param ui_transition_hide:
    :param ui_transition_duration: Transition duration (in milliseconds, without unit)
    """

    def __init__(
        self,
        *children,
        ui_dark: Any | None = None,
        ui_fit: bool | None = None,
        ui_cover: bool | None = None,
        ui_anchor: str | None = None,
        ui_self: str | None = None,
        ui_offset: list | None = None,
        ui_scroll_target: Any | None = None,
        ui_touch_position: bool | None = None,
        ui_persistent: bool | None = None,
        ui_no_route_dismiss: bool | None = None,
        ui_auto_close: bool | None = None,
        ui_separate_close_popup: bool | None = None,
        ui_square: bool | None = None,
        ui_no_refocus: bool | None = None,
        ui_no_focus: bool | None = None,
        ui_max_height: str | None = None,
        ui_max_width: str | None = None,
        ui_model_value: bool | None = None,
        ui_context_menu: bool | None = None,
        ui_target: bool | str | Any | None = None,
        ui_no_parent_event: bool | None = None,
        ui_transition_show: Any | None = None,
        ui_transition_hide: Any | None = None,
        ui_transition_duration: str | float | None = None,
        **kwargs,
    ):
        super().__init__("QMenu", *children, **kwargs)
        self.on("update:model-value", self.__update_model_value)

        if ui_dark is not None:
            self._props["dark"] = ui_dark
        if ui_fit is not None:
            self._props["fit"] = ui_fit
        if ui_cover is not None:
            self._props["cover"] = ui_cover
        if ui_anchor is not None:
            self._props["anchor"] = ui_anchor
        if ui_self is not None:
            self._props["self"] = ui_self
        if ui_offset is not None:
            self._props["offset"] = ui_offset
        if ui_scroll_target is not None:
            self._props["scroll-target"] = ui_scroll_target
        if ui_touch_position is not None:
            self._props["touch-position"] = ui_touch_position
        if ui_persistent is not None:
            self._props["persistent"] = ui_persistent
        if ui_no_route_dismiss is not None:
            self._props["no-route-dismiss"] = ui_no_route_dismiss
        if ui_auto_close is not None:
            self._props["auto-close"] = ui_auto_close
        if ui_separate_close_popup is not None:
            self._props["separate-close-popup"] = ui_separate_close_popup
        if ui_square is not None:
            self._props["square"] = ui_square
        if ui_no_refocus is not None:
            self._props["no-refocus"] = ui_no_refocus
        if ui_no_focus is not None:
            self._props["no-focus"] = ui_no_focus
        if ui_max_height is not None:
            self._props["max-height"] = ui_max_height
        if ui_max_width is not None:
            self._props["max-width"] = ui_max_width
        if ui_model_value is not None:
            self._props["model-value"] = ui_model_value
        if ui_context_menu is not None:
            self._props["context-menu"] = ui_context_menu
        if ui_target is not None:
            self._props["target"] = ui_target
        if ui_no_parent_event is not None:
            self._props["no-parent-event"] = ui_no_parent_event
        if ui_transition_show is not None:
            self._props["transition-show"] = ui_transition_show
        if ui_transition_hide is not None:
            self._props["transition-hide"] = ui_transition_hide
        if ui_transition_duration is not None:
            self._props["transition-duration"] = ui_transition_duration

    def __update_model_value(self, event: Event):
        self._set_prop("model-value", event.value)

    @property
    def ui_dark(self):
        return self._props.get("dark")

    @ui_dark.setter
    def ui_dark(self, value):
        self._set_prop("dark", value)

    @property
    def ui_fit(self):
        """Allows the menu to match at least the full width of its target"""
        return self._props.get("fit")

    @ui_fit.setter
    def ui_fit(self, value):
        self._set_prop("fit", value)

    @property
    def ui_cover(self):
        """Allows the menu to cover its target. When used, the 'self' and 'fit' props are no longer effective"""
        return self._props.get("cover")

    @ui_cover.setter
    def ui_cover(self, value):
        self._set_prop("cover", value)

    @property
    def ui_anchor(self):
        """Two values setting the starting position or anchor point of the menu relative to its target"""
        return self._props.get("anchor")

    @ui_anchor.setter
    def ui_anchor(self, value):
        self._set_prop("anchor", value)

    @property
    def ui_self(self):
        """Two values setting the menu's own position relative to its target"""
        return self._props.get("self")

    @ui_self.setter
    def ui_self(self, value):
        self._set_prop("self", value)

    @property
    def ui_offset(self):
        """An array of two numbers to offset the menu horizontally and vertically in pixels"""
        return self._props.get("offset")

    @ui_offset.setter
    def ui_offset(self, value):
        self._set_prop("offset", value)

    @property
    def ui_scroll_target(self):
        return self._props.get("scroll-target")

    @ui_scroll_target.setter
    def ui_scroll_target(self, value):
        self._set_prop("scroll-target", value)

    @property
    def ui_touch_position(self):
        """Allows for the target position to be set by the mouse position, when the target of the menu is either clicked or touched"""
        return self._props.get("touch-position")

    @ui_touch_position.setter
    def ui_touch_position(self, value):
        self._set_prop("touch-position", value)

    @property
    def ui_persistent(self):
        """Allows the menu to not be dismissed by a click/tap outside of the menu or by hitting the ESC key; Also, an app route change won't dismiss it"""
        return self._props.get("persistent")

    @ui_persistent.setter
    def ui_persistent(self, value):
        self._set_prop("persistent", value)

    @property
    def ui_no_route_dismiss(self):
        """Changing route app won't dismiss the popup; No need to set it if 'persistent' prop is also set"""
        return self._props.get("no-route-dismiss")

    @ui_no_route_dismiss.setter
    def ui_no_route_dismiss(self, value):
        self._set_prop("no-route-dismiss", value)

    @property
    def ui_auto_close(self):
        """Allows any click/tap in the menu to close it; Useful instead of attaching events to each menu item that should close the menu on click/tap"""
        return self._props.get("auto-close")

    @ui_auto_close.setter
    def ui_auto_close(self, value):
        self._set_prop("auto-close", value)

    @property
    def ui_separate_close_popup(self):
        """Separate from parent menu, marking it as a separate closing point for v-close-popup (without this, chained menus close all together)"""
        return self._props.get("separate-close-popup")

    @ui_separate_close_popup.setter
    def ui_separate_close_popup(self, value):
        self._set_prop("separate-close-popup", value)

    @property
    def ui_square(self):
        """Forces content to have squared borders"""
        return self._props.get("square")

    @ui_square.setter
    def ui_square(self, value):
        self._set_prop("square", value)

    @property
    def ui_no_refocus(self):
        """(Accessibility) When Menu gets hidden, do not refocus on the DOM element that previously had focus"""
        return self._props.get("no-refocus")

    @ui_no_refocus.setter
    def ui_no_refocus(self, value):
        self._set_prop("no-refocus", value)

    @property
    def ui_no_focus(self):
        """(Accessibility) When Menu gets shown, do not switch focus on it"""
        return self._props.get("no-focus")

    @ui_no_focus.setter
    def ui_no_focus(self, value):
        self._set_prop("no-focus", value)

    @property
    def ui_max_height(self):
        """The maximum height of the menu; Size in CSS units, including unit name"""
        return self._props.get("max-height")

    @ui_max_height.setter
    def ui_max_height(self, value):
        self._set_prop("max-height", value)

    @property
    def ui_max_width(self):
        """The maximum width of the menu; Size in CSS units, including unit name"""
        return self._props.get("max-width")

    @ui_max_width.setter
    def ui_max_width(self, value):
        self._set_prop("max-width", value)

    @property
    def ui_model_value(self):
        """Model of the component defining shown/hidden state; Either use this property (along with a listener for 'update:model-value' event) OR use v-model directive"""
        return self._props.get("model-value")

    @ui_model_value.setter
    def ui_model_value(self, value):
        self._set_prop("model-value", value)

    @property
    def ui_context_menu(self):
        """Allows the component to behave like a context menu, which opens with a right mouse click (or long tap on mobile)"""
        return self._props.get("context-menu")

    @ui_context_menu.setter
    def ui_context_menu(self, value):
        self._set_prop("context-menu", value)

    @property
    def ui_target(self):
        """Configure a target element to trigger component toggle; 'true' means it enables the parent DOM element, 'false' means it disables attaching events to any DOM elements; By using a String (CSS selector) or a DOM element it attaches the events to the specified DOM element (if it exists)"""
        return self._props.get("target")

    @ui_target.setter
    def ui_target(self, value):
        self._set_prop("target", value)

    @property
    def ui_no_parent_event(self):
        """Skips attaching events to the target DOM element (that trigger the element to get shown)"""
        return self._props.get("no-parent-event")

    @ui_no_parent_event.setter
    def ui_no_parent_event(self, value):
        self._set_prop("no-parent-event", value)

    @property
    def ui_transition_show(self):
        return self._props.get("transition-show")

    @ui_transition_show.setter
    def ui_transition_show(self, value):
        self._set_prop("transition-show", value)

    @property
    def ui_transition_hide(self):
        return self._props.get("transition-hide")

    @ui_transition_hide.setter
    def ui_transition_hide(self, value):
        self._set_prop("transition-hide", value)

    @property
    def ui_transition_duration(self):
        """Transition duration (in milliseconds, without unit)"""
        return self._props.get("transition-duration")

    @ui_transition_duration.setter
    def ui_transition_duration(self, value):
        self._set_prop("transition-duration", value)

    def on_before_hide(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("before-hide", handler, arg)

    def on_before_show(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("before-show", handler, arg)

    def on_click(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("click.stop", handler, arg)

    def on_escape_key(self, handler: Callable, arg: object = None):
        """
        Emitted when ESC key is pressed; Does not get emitted if Menu is 'persistent'

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("escape-key", handler, arg)

    def on_hide(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("hide", handler, arg)

    def on_show(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("show", handler, arg)

    def on_update_model_value(self, handler: Callable, arg: object = None):
        """
        Emitted when showing/hidden state changes; Is also used by v-model

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("update:model-value", handler, arg)

    def ui_focus(self):
        """Focus menu; if you have content with autofocus attribute, it will directly focus it"""
        self._js_call_method("focus")

    def ui_hide(self):
        self._js_call_method("hide")

    def ui_show(self):
        self._js_call_method("show")

    def ui_toggle(self):
        self._js_call_method("toggle")

    def ui_updatePosition(self):
        """There are some custom scenarios for which Quasar cannot automatically reposition the menu without significant performance drawbacks so the optimal solution is for you to call this method when you need it"""
        self._js_call_method("updatePosition")

    def _get_js_methods(self):
        return ["focus", "hide", "show", "toggle", "updatePosition"]


class QNoSsr(Component):
    """
    Quasar Component: `QNoSsr <https://v2.quasar.dev/vue-components/no-ssr>`__

    :param ui_tag:
    :param ui_placeholder: Text to display on server-side render (unless using 'placeholder' slot)
    """

    def __init__(
        self,
        *children,
        ui_tag: Any | None = None,
        ui_placeholder: str | None = None,
        **kwargs,
    ):
        super().__init__("QNoSsr", *children, **kwargs)
        if ui_tag is not None:
            self._props["tag"] = ui_tag
        if ui_placeholder is not None:
            self._props["placeholder"] = ui_placeholder

    @property
    def ui_tag(self):
        return self._props.get("tag")

    @ui_tag.setter
    def ui_tag(self, value):
        self._set_prop("tag", value)

    @property
    def ui_placeholder(self):
        """Text to display on server-side render (unless using 'placeholder' slot)"""
        return self._props.get("placeholder")

    @ui_placeholder.setter
    def ui_placeholder(self, value):
        self._set_prop("placeholder", value)

    @property
    def ui_slot_placeholder(self):
        """Slot used as placeholder on server-side render, which gets replaced by the default slot on client-side; overrides 'placeholder' prop"""
        return self.ui_slots.get("placeholder", [])

    @ui_slot_placeholder.setter
    def ui_slot_placeholder(self, value):
        self._set_slot("placeholder", value)

    def _get_js_methods(self):
        return []


class QOptionGroup(Component):
    """
    Quasar Component: `QOptionGroup <https://v2.quasar.dev/vue-components/option-group>`__

    :param ui_model_value:
    :param ui_options: Array of objects that the binary components will be created from. For best performance reference a variable in your scope. Canonical form of each object is with 'label' (String), 'value' (Any) and optional 'disable' (Boolean) props (can be customized with options-value/option-label/option-disable props) along with any other props from QToggle, QCheckbox, or QRadio.
    :param ui_option_value: Property of option which holds the 'value'; If using a function then for best performance, reference it from your scope and do not define it inline
    :param ui_option_label: Property of option which holds the 'label'; If using a function then for best performance, reference it from your scope and do not define it inline
    :param ui_option_disable: Property of option which tells it's disabled; The value of the property must be a Boolean; If using a function then for best performance, reference it from your scope and do not define it inline
    :param ui_name: Used to specify the name of the controls; Useful if dealing with forms submitted directly to a URL
    :param ui_type: The type of input component to be used
    :param ui_color:
    :param ui_keep_color: Should the color (if specified any) be kept when input components are unticked?
    :param ui_dark:
    :param ui_dense:
    :param ui_left_label: Label (if any specified) should be displayed on the left side of the input components
    :param ui_inline: Show input components as inline-block rather than each having their own row
    :param ui_disable:
    :param ui_size: Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)
    """

    def __init__(
        self,
        *children,
        ui_model_value: Any | None = None,
        ui_options: list | None = None,
        ui_option_value: Callable | str | None = None,
        ui_option_label: Callable | str | None = None,
        ui_option_disable: Callable | str | None = None,
        ui_name: str | None = None,
        ui_type: str | None = None,
        ui_color: Any | None = None,
        ui_keep_color: bool | None = None,
        ui_dark: Any | None = None,
        ui_dense: Any | None = None,
        ui_left_label: bool | None = None,
        ui_inline: bool | None = None,
        ui_disable: Any | None = None,
        ui_size: str | None = None,
        **kwargs,
    ):
        super().__init__("QOptionGroup", *children, **kwargs)
        self.on("update:model-value", self.__update_model_value)

        if ui_model_value is not None:
            self._props["model-value"] = ui_model_value
        if ui_options is not None:
            self._props["options"] = ui_options
        if ui_option_value is not None:
            self._props["option-value"] = ui_option_value
        if ui_option_label is not None:
            self._props["option-label"] = ui_option_label
        if ui_option_disable is not None:
            self._props["option-disable"] = ui_option_disable
        if ui_name is not None:
            self._props["name"] = ui_name
        if ui_type is not None:
            self._props["type"] = ui_type
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_keep_color is not None:
            self._props["keep-color"] = ui_keep_color
        if ui_dark is not None:
            self._props["dark"] = ui_dark
        if ui_dense is not None:
            self._props["dense"] = ui_dense
        if ui_left_label is not None:
            self._props["left-label"] = ui_left_label
        if ui_inline is not None:
            self._props["inline"] = ui_inline
        if ui_disable is not None:
            self._props["disable"] = ui_disable
        if ui_size is not None:
            self._props["size"] = ui_size

    def __update_model_value(self, event: Event):
        self._set_prop("model-value", event.value)

    @property
    def ui_model_value(self):
        return self._props.get("model-value")

    @ui_model_value.setter
    def ui_model_value(self, value):
        self._set_prop("model-value", value)

    @property
    def ui_options(self):
        """Array of objects that the binary components will be created from. For best performance reference a variable in your scope. Canonical form of each object is with 'label' (String), 'value' (Any) and optional 'disable' (Boolean) props (can be customized with options-value/option-label/option-disable props) along with any other props from QToggle, QCheckbox, or QRadio."""
        return self._props.get("options")

    @ui_options.setter
    def ui_options(self, value):
        self._set_prop("options", value)

    @property
    def ui_option_value(self):
        """Property of option which holds the 'value'; If using a function then for best performance, reference it from your scope and do not define it inline"""
        return self._props.get("option-value")

    @ui_option_value.setter
    def ui_option_value(self, value):
        self._set_prop("option-value", value)

    @property
    def ui_option_label(self):
        """Property of option which holds the 'label'; If using a function then for best performance, reference it from your scope and do not define it inline"""
        return self._props.get("option-label")

    @ui_option_label.setter
    def ui_option_label(self, value):
        self._set_prop("option-label", value)

    @property
    def ui_option_disable(self):
        """Property of option which tells it's disabled; The value of the property must be a Boolean; If using a function then for best performance, reference it from your scope and do not define it inline"""
        return self._props.get("option-disable")

    @ui_option_disable.setter
    def ui_option_disable(self, value):
        self._set_prop("option-disable", value)

    @property
    def ui_name(self):
        """Used to specify the name of the controls; Useful if dealing with forms submitted directly to a URL"""
        return self._props.get("name")

    @ui_name.setter
    def ui_name(self, value):
        self._set_prop("name", value)

    @property
    def ui_type(self):
        """The type of input component to be used"""
        return self._props.get("type")

    @ui_type.setter
    def ui_type(self, value):
        self._set_prop("type", value)

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_keep_color(self):
        """Should the color (if specified any) be kept when input components are unticked?"""
        return self._props.get("keep-color")

    @ui_keep_color.setter
    def ui_keep_color(self, value):
        self._set_prop("keep-color", value)

    @property
    def ui_dark(self):
        return self._props.get("dark")

    @ui_dark.setter
    def ui_dark(self, value):
        self._set_prop("dark", value)

    @property
    def ui_dense(self):
        return self._props.get("dense")

    @ui_dense.setter
    def ui_dense(self, value):
        self._set_prop("dense", value)

    @property
    def ui_left_label(self):
        """Label (if any specified) should be displayed on the left side of the input components"""
        return self._props.get("left-label")

    @ui_left_label.setter
    def ui_left_label(self, value):
        self._set_prop("left-label", value)

    @property
    def ui_inline(self):
        """Show input components as inline-block rather than each having their own row"""
        return self._props.get("inline")

    @ui_inline.setter
    def ui_inline(self, value):
        self._set_prop("inline", value)

    @property
    def ui_disable(self):
        return self._props.get("disable")

    @ui_disable.setter
    def ui_disable(self, value):
        self._set_prop("disable", value)

    @property
    def ui_size(self):
        """Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)"""
        return self._props.get("size")

    @ui_size.setter
    def ui_size(self, value):
        self._set_prop("size", value)

    @property
    def ui_slot_label(self):
        """Generic slot for all labels"""
        return self.ui_slots.get("label", [])

    @ui_slot_label.setter
    def ui_slot_label(self, value):
        self._set_slot("label", value)

    def ui_slot_label_name(self, name, value):
        """Slot to define the specific label for the option at '[name]' where name is a 0-based index; Overrides the generic 'label' slot if used"""
        self._set_slot("label-" + name, value)

    def on_update_model_value(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("update:model-value", handler, arg)

    def _get_js_methods(self):
        return []


class QPageContainer(Component):
    """
    Quasar Component: `QPageContainer <https://v2.quasar.dev/layout/page>`__

    """

    def __init__(self, *children, **kwargs):
        super().__init__("QPageContainer", *children, **kwargs)

    def _get_js_methods(self):
        return []


class QPage(Component):
    """
    Quasar Component: `QPage <https://v2.quasar.dev/layout/page>`__

    :param ui_padding: Applies a default responsive page padding
    :param ui_style_fn: Override default CSS style applied to the component (sets minHeight); Function(offset: Number) => CSS props/value: Object; For best performance, reference it from your scope and do not define it inline
    """

    def __init__(
        self,
        *children,
        ui_padding: bool | None = None,
        ui_style_fn: Callable | None = None,
        **kwargs,
    ):
        super().__init__("QPage", *children, **kwargs)
        if ui_padding is not None:
            self._props["padding"] = ui_padding
        if ui_style_fn is not None:
            self._props["style-fn"] = ui_style_fn

    @property
    def ui_padding(self):
        """Applies a default responsive page padding"""
        return self._props.get("padding")

    @ui_padding.setter
    def ui_padding(self, value):
        self._set_prop("padding", value)

    @property
    def ui_style_fn(self):
        """Override default CSS style applied to the component (sets minHeight); Function(offset: Number) => CSS props/value: Object; For best performance, reference it from your scope and do not define it inline"""
        return self._props.get("style-fn")

    @ui_style_fn.setter
    def ui_style_fn(self, value):
        self._set_prop("style-fn", value)

    def _get_js_methods(self):
        return []


class QPageScroller(Component):
    """
    Quasar Component: `QPageScroller <https://v2.quasar.dev/layout/page-sticky>`__

    :param ui_scroll_offset: Scroll offset (in pixels) from which point the component is shown on page; Measured from the top of the page (or from the bottom if in 'reverse' mode)
    :param ui_reverse: Work in reverse (shows when scrolling to the top of the page and scrolls to bottom when triggered)
    :param ui_duration: Duration (in milliseconds) of the scrolling until it reaches its target
    :param ui_offset: An array of two numbers to offset the component horizontally and vertically in pixels
    :param ui_position: Page side/corner to stick to
    :param ui_expand: By default the component shrinks to content's size; By using this prop you make the component fully expand horizontally or vertically, based on 'position' prop
    """

    def __init__(
        self,
        *children,
        ui_scroll_offset: float | None = None,
        ui_reverse: bool | None = None,
        ui_duration: float | None = None,
        ui_offset: list | None = None,
        ui_position: str | None = None,
        ui_expand: bool | None = None,
        **kwargs,
    ):
        super().__init__("QPageScroller", *children, **kwargs)
        if ui_scroll_offset is not None:
            self._props["scroll-offset"] = ui_scroll_offset
        if ui_reverse is not None:
            self._props["reverse"] = ui_reverse
        if ui_duration is not None:
            self._props["duration"] = ui_duration
        if ui_offset is not None:
            self._props["offset"] = ui_offset
        if ui_position is not None:
            self._props["position"] = ui_position
        if ui_expand is not None:
            self._props["expand"] = ui_expand

    @property
    def ui_scroll_offset(self):
        """Scroll offset (in pixels) from which point the component is shown on page; Measured from the top of the page (or from the bottom if in 'reverse' mode)"""
        return self._props.get("scroll-offset")

    @ui_scroll_offset.setter
    def ui_scroll_offset(self, value):
        self._set_prop("scroll-offset", value)

    @property
    def ui_reverse(self):
        """Work in reverse (shows when scrolling to the top of the page and scrolls to bottom when triggered)"""
        return self._props.get("reverse")

    @ui_reverse.setter
    def ui_reverse(self, value):
        self._set_prop("reverse", value)

    @property
    def ui_duration(self):
        """Duration (in milliseconds) of the scrolling until it reaches its target"""
        return self._props.get("duration")

    @ui_duration.setter
    def ui_duration(self, value):
        self._set_prop("duration", value)

    @property
    def ui_offset(self):
        """An array of two numbers to offset the component horizontally and vertically in pixels"""
        return self._props.get("offset")

    @ui_offset.setter
    def ui_offset(self, value):
        self._set_prop("offset", value)

    @property
    def ui_position(self):
        """Page side/corner to stick to"""
        return self._props.get("position")

    @ui_position.setter
    def ui_position(self, value):
        self._set_prop("position", value)

    @property
    def ui_expand(self):
        """By default the component shrinks to content's size; By using this prop you make the component fully expand horizontally or vertically, based on 'position' prop"""
        return self._props.get("expand")

    @ui_expand.setter
    def ui_expand(self, value):
        self._set_prop("expand", value)

    def on_click(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("click.stop", handler, arg)

    def _get_js_methods(self):
        return []


class QPageSticky(Component):
    """
    Quasar Component: `QPageSticky <https://v2.quasar.dev/layout/page-sticky>`__

    :param ui_position: Page side/corner to stick to
    :param ui_offset: An array of two numbers to offset the component horizontally and vertically in pixels
    :param ui_expand: By default the component shrinks to content's size; By using this prop you make the component fully expand horizontally or vertically, based on 'position' prop
    """

    def __init__(
        self,
        *children,
        ui_position: str | None = None,
        ui_offset: list | None = None,
        ui_expand: bool | None = None,
        **kwargs,
    ):
        super().__init__("QPageSticky", *children, **kwargs)
        if ui_position is not None:
            self._props["position"] = ui_position
        if ui_offset is not None:
            self._props["offset"] = ui_offset
        if ui_expand is not None:
            self._props["expand"] = ui_expand

    @property
    def ui_position(self):
        """Page side/corner to stick to"""
        return self._props.get("position")

    @ui_position.setter
    def ui_position(self, value):
        self._set_prop("position", value)

    @property
    def ui_offset(self):
        """An array of two numbers to offset the component horizontally and vertically in pixels"""
        return self._props.get("offset")

    @ui_offset.setter
    def ui_offset(self, value):
        self._set_prop("offset", value)

    @property
    def ui_expand(self):
        """By default the component shrinks to content's size; By using this prop you make the component fully expand horizontally or vertically, based on 'position' prop"""
        return self._props.get("expand")

    @ui_expand.setter
    def ui_expand(self, value):
        self._set_prop("expand", value)

    def _get_js_methods(self):
        return []


class QPagination(Component):
    """
    Quasar Component: `QPagination <https://v2.quasar.dev/vue-components/pagination>`__

    :param ui_model_value: Current page (must be between min/max)
    :param ui_min: Minimum page (must be lower than 'max')
    :param ui_max: Number of last page (must be higher than 'min')
    :param ui_dark: Notify the component that the background is a dark color (useful when you are using it along with the 'input' prop)
    :param ui_size: Button size in CSS units, including unit name
    :param ui_disable:
    :param ui_input: Use an input instead of buttons
    :param ui_icon_prev:
    :param ui_icon_next:
    :param ui_icon_first:
    :param ui_icon_last:
    :param ui_to_fn: Generate link for page buttons; For best performance, reference it from your scope and do not define it inline
    :param ui_boundary_links: Show boundary button links
    :param ui_boundary_numbers: Always show first and last page buttons (if not using 'input')
    :param ui_direction_links: Show direction buttons
    :param ui_ellipses: Show ellipses (...) when pages are available
    :param ui_max_pages: Maximum number of page links to display at a time; 0 means Infinite
    :param ui_flat: Use 'flat' design for non-active buttons (it's the default option)
    :param ui_outline: Use 'outline' design for non-active buttons
    :param ui_unelevated: Remove shadow for non-active buttons
    :param ui_push: Use 'push' design for non-active buttons
    :param ui_color: Color name from the Quasar Color Palette for the non-active buttons
    :param ui_text_color: Text color name from the Quasar Color Palette for the ACTIVE buttons
    :param ui_active_design: The design of the ACTIVE button, similar to the flat/outline/push/unelevated props (but those are used for non-active buttons)
    :param ui_active_color: Color name from the Quasar Color Palette for the ACTIVE button
    :param ui_active_text_color: Text color name from the Quasar Color Palette for the ACTIVE button
    :param ui_round: Makes a circle shaped button for all buttons
    :param ui_rounded: Applies a more prominent border-radius for a squared shape button for all buttons
    :param ui_glossy: Applies a glossy effect for all buttons
    :param ui_gutter: Apply custom gutter; Size in CSS units, including unit name or standard size name (none|xs|sm|md|lg|xl)
    :param ui_padding: Apply custom padding (vertical [horizontal]); Size in CSS units, including unit name or standard size name (none|xs|sm|md|lg|xl); Also removes the min width and height when set
    :param ui_input_style: Style definitions to be attributed to the input (if using one)
    :param ui_input_class: Class definitions to be attributed to the input (if using one)
    :param ui_ripple: Configure buttons material ripple (disable it by setting it to 'false' or supply a config object); Does not applies to boundary and ellipsis buttons
    """

    def __init__(
        self,
        *children,
        ui_model_value: float | None = None,
        ui_min: float | str | None = None,
        ui_max: float | str | None = None,
        ui_dark: Any | None = None,
        ui_size: str | None = None,
        ui_disable: Any | None = None,
        ui_input: bool | None = None,
        ui_icon_prev: Any | None = None,
        ui_icon_next: Any | None = None,
        ui_icon_first: Any | None = None,
        ui_icon_last: Any | None = None,
        ui_to_fn: Callable | None = None,
        ui_boundary_links: bool | None = None,
        ui_boundary_numbers: bool | None = None,
        ui_direction_links: bool | None = None,
        ui_ellipses: bool | None = None,
        ui_max_pages: float | str | None = None,
        ui_flat: bool | None = None,
        ui_outline: bool | None = None,
        ui_unelevated: bool | None = None,
        ui_push: bool | None = None,
        ui_color: Any | None = None,
        ui_text_color: Any | None = None,
        ui_active_design: str | None = None,
        ui_active_color: Any | None = None,
        ui_active_text_color: Any | None = None,
        ui_round: bool | None = None,
        ui_rounded: bool | None = None,
        ui_glossy: bool | None = None,
        ui_gutter: str | None = None,
        ui_padding: str | None = None,
        ui_input_style: str | list | dict | None = None,
        ui_input_class: str | list | dict | None = None,
        ui_ripple: bool | dict | None = None,
        **kwargs,
    ):
        super().__init__("QPagination", *children, **kwargs)
        self.on("update:model-value", self.__update_model_value)

        if ui_model_value is not None:
            self._props["model-value"] = ui_model_value
        if ui_min is not None:
            self._props["min"] = ui_min
        if ui_max is not None:
            self._props["max"] = ui_max
        if ui_dark is not None:
            self._props["dark"] = ui_dark
        if ui_size is not None:
            self._props["size"] = ui_size
        if ui_disable is not None:
            self._props["disable"] = ui_disable
        if ui_input is not None:
            self._props["input"] = ui_input
        if ui_icon_prev is not None:
            self._props["icon-prev"] = ui_icon_prev
        if ui_icon_next is not None:
            self._props["icon-next"] = ui_icon_next
        if ui_icon_first is not None:
            self._props["icon-first"] = ui_icon_first
        if ui_icon_last is not None:
            self._props["icon-last"] = ui_icon_last
        if ui_to_fn is not None:
            self._props["to-fn"] = ui_to_fn
        if ui_boundary_links is not None:
            self._props["boundary-links"] = ui_boundary_links
        if ui_boundary_numbers is not None:
            self._props["boundary-numbers"] = ui_boundary_numbers
        if ui_direction_links is not None:
            self._props["direction-links"] = ui_direction_links
        if ui_ellipses is not None:
            self._props["ellipses"] = ui_ellipses
        if ui_max_pages is not None:
            self._props["max-pages"] = ui_max_pages
        if ui_flat is not None:
            self._props["flat"] = ui_flat
        if ui_outline is not None:
            self._props["outline"] = ui_outline
        if ui_unelevated is not None:
            self._props["unelevated"] = ui_unelevated
        if ui_push is not None:
            self._props["push"] = ui_push
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_text_color is not None:
            self._props["text-color"] = ui_text_color
        if ui_active_design is not None:
            self._props["active-design"] = ui_active_design
        if ui_active_color is not None:
            self._props["active-color"] = ui_active_color
        if ui_active_text_color is not None:
            self._props["active-text-color"] = ui_active_text_color
        if ui_round is not None:
            self._props["round"] = ui_round
        if ui_rounded is not None:
            self._props["rounded"] = ui_rounded
        if ui_glossy is not None:
            self._props["glossy"] = ui_glossy
        if ui_gutter is not None:
            self._props["gutter"] = ui_gutter
        if ui_padding is not None:
            self._props["padding"] = ui_padding
        if ui_input_style is not None:
            self._props["input-style"] = ui_input_style
        if ui_input_class is not None:
            self._props["input-class"] = ui_input_class
        if ui_ripple is not None:
            self._props["ripple"] = ui_ripple

    def __update_model_value(self, event: Event):
        self._set_prop("model-value", event.value)

    @property
    def ui_model_value(self):
        """Current page (must be between min/max)"""
        return self._props.get("model-value")

    @ui_model_value.setter
    def ui_model_value(self, value):
        self._set_prop("model-value", value)

    @property
    def ui_min(self):
        """Minimum page (must be lower than 'max')"""
        return self._props.get("min")

    @ui_min.setter
    def ui_min(self, value):
        self._set_prop("min", value)

    @property
    def ui_max(self):
        """Number of last page (must be higher than 'min')"""
        return self._props.get("max")

    @ui_max.setter
    def ui_max(self, value):
        self._set_prop("max", value)

    @property
    def ui_dark(self):
        """Notify the component that the background is a dark color (useful when you are using it along with the 'input' prop)"""
        return self._props.get("dark")

    @ui_dark.setter
    def ui_dark(self, value):
        self._set_prop("dark", value)

    @property
    def ui_size(self):
        """Button size in CSS units, including unit name"""
        return self._props.get("size")

    @ui_size.setter
    def ui_size(self, value):
        self._set_prop("size", value)

    @property
    def ui_disable(self):
        return self._props.get("disable")

    @ui_disable.setter
    def ui_disable(self, value):
        self._set_prop("disable", value)

    @property
    def ui_input(self):
        """Use an input instead of buttons"""
        return self._props.get("input")

    @ui_input.setter
    def ui_input(self, value):
        self._set_prop("input", value)

    @property
    def ui_icon_prev(self):
        return self._props.get("icon-prev")

    @ui_icon_prev.setter
    def ui_icon_prev(self, value):
        self._set_prop("icon-prev", value)

    @property
    def ui_icon_next(self):
        return self._props.get("icon-next")

    @ui_icon_next.setter
    def ui_icon_next(self, value):
        self._set_prop("icon-next", value)

    @property
    def ui_icon_first(self):
        return self._props.get("icon-first")

    @ui_icon_first.setter
    def ui_icon_first(self, value):
        self._set_prop("icon-first", value)

    @property
    def ui_icon_last(self):
        return self._props.get("icon-last")

    @ui_icon_last.setter
    def ui_icon_last(self, value):
        self._set_prop("icon-last", value)

    @property
    def ui_to_fn(self):
        """Generate link for page buttons; For best performance, reference it from your scope and do not define it inline"""
        return self._props.get("to-fn")

    @ui_to_fn.setter
    def ui_to_fn(self, value):
        self._set_prop("to-fn", value)

    @property
    def ui_boundary_links(self):
        """Show boundary button links"""
        return self._props.get("boundary-links")

    @ui_boundary_links.setter
    def ui_boundary_links(self, value):
        self._set_prop("boundary-links", value)

    @property
    def ui_boundary_numbers(self):
        """Always show first and last page buttons (if not using 'input')"""
        return self._props.get("boundary-numbers")

    @ui_boundary_numbers.setter
    def ui_boundary_numbers(self, value):
        self._set_prop("boundary-numbers", value)

    @property
    def ui_direction_links(self):
        """Show direction buttons"""
        return self._props.get("direction-links")

    @ui_direction_links.setter
    def ui_direction_links(self, value):
        self._set_prop("direction-links", value)

    @property
    def ui_ellipses(self):
        """Show ellipses (...) when pages are available"""
        return self._props.get("ellipses")

    @ui_ellipses.setter
    def ui_ellipses(self, value):
        self._set_prop("ellipses", value)

    @property
    def ui_max_pages(self):
        """Maximum number of page links to display at a time; 0 means Infinite"""
        return self._props.get("max-pages")

    @ui_max_pages.setter
    def ui_max_pages(self, value):
        self._set_prop("max-pages", value)

    @property
    def ui_flat(self):
        """Use 'flat' design for non-active buttons (it's the default option)"""
        return self._props.get("flat")

    @ui_flat.setter
    def ui_flat(self, value):
        self._set_prop("flat", value)

    @property
    def ui_outline(self):
        """Use 'outline' design for non-active buttons"""
        return self._props.get("outline")

    @ui_outline.setter
    def ui_outline(self, value):
        self._set_prop("outline", value)

    @property
    def ui_unelevated(self):
        """Remove shadow for non-active buttons"""
        return self._props.get("unelevated")

    @ui_unelevated.setter
    def ui_unelevated(self, value):
        self._set_prop("unelevated", value)

    @property
    def ui_push(self):
        """Use 'push' design for non-active buttons"""
        return self._props.get("push")

    @ui_push.setter
    def ui_push(self, value):
        self._set_prop("push", value)

    @property
    def ui_color(self):
        """Color name from the Quasar Color Palette for the non-active buttons"""
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_text_color(self):
        """Text color name from the Quasar Color Palette for the ACTIVE buttons"""
        return self._props.get("text-color")

    @ui_text_color.setter
    def ui_text_color(self, value):
        self._set_prop("text-color", value)

    @property
    def ui_active_design(self):
        """The design of the ACTIVE button, similar to the flat/outline/push/unelevated props (but those are used for non-active buttons)"""
        return self._props.get("active-design")

    @ui_active_design.setter
    def ui_active_design(self, value):
        self._set_prop("active-design", value)

    @property
    def ui_active_color(self):
        """Color name from the Quasar Color Palette for the ACTIVE button"""
        return self._props.get("active-color")

    @ui_active_color.setter
    def ui_active_color(self, value):
        self._set_prop("active-color", value)

    @property
    def ui_active_text_color(self):
        """Text color name from the Quasar Color Palette for the ACTIVE button"""
        return self._props.get("active-text-color")

    @ui_active_text_color.setter
    def ui_active_text_color(self, value):
        self._set_prop("active-text-color", value)

    @property
    def ui_round(self):
        """Makes a circle shaped button for all buttons"""
        return self._props.get("round")

    @ui_round.setter
    def ui_round(self, value):
        self._set_prop("round", value)

    @property
    def ui_rounded(self):
        """Applies a more prominent border-radius for a squared shape button for all buttons"""
        return self._props.get("rounded")

    @ui_rounded.setter
    def ui_rounded(self, value):
        self._set_prop("rounded", value)

    @property
    def ui_glossy(self):
        """Applies a glossy effect for all buttons"""
        return self._props.get("glossy")

    @ui_glossy.setter
    def ui_glossy(self, value):
        self._set_prop("glossy", value)

    @property
    def ui_gutter(self):
        """Apply custom gutter; Size in CSS units, including unit name or standard size name (none|xs|sm|md|lg|xl)"""
        return self._props.get("gutter")

    @ui_gutter.setter
    def ui_gutter(self, value):
        self._set_prop("gutter", value)

    @property
    def ui_padding(self):
        """Apply custom padding (vertical [horizontal]); Size in CSS units, including unit name or standard size name (none|xs|sm|md|lg|xl); Also removes the min width and height when set"""
        return self._props.get("padding")

    @ui_padding.setter
    def ui_padding(self, value):
        self._set_prop("padding", value)

    @property
    def ui_input_style(self):
        """Style definitions to be attributed to the input (if using one)"""
        return self._props.get("input-style")

    @ui_input_style.setter
    def ui_input_style(self, value):
        self._set_prop("input-style", value)

    @property
    def ui_input_class(self):
        """Class definitions to be attributed to the input (if using one)"""
        return self._props.get("input-class")

    @ui_input_class.setter
    def ui_input_class(self, value):
        self._set_prop("input-class", value)

    @property
    def ui_ripple(self):
        """Configure buttons material ripple (disable it by setting it to 'false' or supply a config object); Does not applies to boundary and ellipsis buttons"""
        return self._props.get("ripple")

    @ui_ripple.setter
    def ui_ripple(self, value):
        self._set_prop("ripple", value)

    def on_update_model_value(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("update:model-value", handler, arg)

    def ui_set(self, ui_pageNumber=None):
        """Go directly to the specified page"""
        kwargs = {}
        if ui_pageNumber is not None:
            kwargs["pageNumber"] = ui_pageNumber
        self._js_call_method("set", [kwargs])

    def ui_setByOffset(self, ui_offset=None):
        """Increment/Decrement current page by offset"""
        kwargs = {}
        if ui_offset is not None:
            kwargs["offset"] = ui_offset
        self._js_call_method("setByOffset", [kwargs])

    def _get_js_methods(self):
        return ["set", "setByOffset"]


class QParallax(Component):
    """
    Quasar Component: `QParallax <https://v2.quasar.dev/vue-components/parallax>`__

    :param ui_src: Path to image (unless a 'media' slot is used)
    :param ui_height: Height of component (in pixels)
    :param ui_speed: Speed of parallax effect (0.0 < x < 1.0)
    :param ui_scroll_target:
    """

    def __init__(
        self,
        *children,
        ui_src: str | None = None,
        ui_height: float | None = None,
        ui_speed: float | None = None,
        ui_scroll_target: Any | None = None,
        **kwargs,
    ):
        super().__init__("QParallax", *children, **kwargs)
        if ui_src is not None:
            self._props["src"] = ui_src
        if ui_height is not None:
            self._props["height"] = ui_height
        if ui_speed is not None:
            self._props["speed"] = ui_speed
        if ui_scroll_target is not None:
            self._props["scroll-target"] = ui_scroll_target

    @property
    def ui_src(self):
        """Path to image (unless a 'media' slot is used)"""
        return self._props.get("src")

    @ui_src.setter
    def ui_src(self, value):
        self._set_prop("src", value)

    @property
    def ui_height(self):
        """Height of component (in pixels)"""
        return self._props.get("height")

    @ui_height.setter
    def ui_height(self, value):
        self._set_prop("height", value)

    @property
    def ui_speed(self):
        """Speed of parallax effect (0.0 < x < 1.0)"""
        return self._props.get("speed")

    @ui_speed.setter
    def ui_speed(self, value):
        self._set_prop("speed", value)

    @property
    def ui_scroll_target(self):
        return self._props.get("scroll-target")

    @ui_scroll_target.setter
    def ui_scroll_target(self, value):
        self._set_prop("scroll-target", value)

    @property
    def ui_slot_content(self):
        """Scoped slot for describing content that gets displayed on top of the component; If specified, it overrides the default slot"""
        return self.ui_slots.get("content", [])

    @ui_slot_content.setter
    def ui_slot_content(self, value):
        self._set_slot("content", value)

    @property
    def ui_slot_media(self):
        """Slot for describing <img> or <video> tags"""
        return self.ui_slots.get("media", [])

    @ui_slot_media.setter
    def ui_slot_media(self, value):
        self._set_slot("media", value)

    def on_scroll(self, handler: Callable, arg: object = None):
        """
        Emitted when scrolling occurs

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("scroll", handler, arg)

    def _get_js_methods(self):
        return []


class QPopupEdit(Component):
    """
    Quasar Component: `QPopupEdit <https://v2.quasar.dev/vue-components/popup-edit>`__

    :param ui_model_value:
    :param ui_title: Optional title (unless 'title' slot is used)
    :param ui_buttons: Show Set and Cancel buttons
    :param ui_label_set: Override Set button label
    :param ui_label_cancel: Override Cancel button label
    :param ui_auto_save: Automatically save the model (if changed) when user clicks/taps outside of the popup; It does not apply to ESC key
    :param ui_color:
    :param ui_validate: Validates model then triggers 'save' and closes Popup; Returns a Boolean ('true' means valid, 'false' means abort); Syntax: validate(value); For best performance, reference it from your scope and do not define it inline
    :param ui_disable:
    :param ui_fit: Allows the menu to match at least the full width of its target
    :param ui_cover: Allows the menu to cover its target. When used, the 'self' and 'fit' props are no longer effective
    :param ui_anchor: Two values setting the starting position or anchor point of the menu relative to its target
    :param ui_self: Two values setting the menu's own position relative to its target
    :param ui_offset: An array of two numbers to offset the menu horizontally and vertically in pixels
    :param ui_touch_position: Allows for the target position to be set by the mouse position, when the target of the menu is either clicked or touched
    :param ui_persistent: Avoid menu closing by hitting ESC key or by clicking/tapping outside of the Popup
    :param ui_separate_close_popup: Separate from parent menu, marking it as a separate closing point for v-close-popup (without this, chained menus close all together)
    :param ui_square: Forces menu to have squared borders
    :param ui_max_height: The maximum height of the menu; Size in CSS units, including unit name
    :param ui_max_width: The maximum width of the menu; Size in CSS units, including unit name
    """

    def __init__(
        self,
        *children,
        ui_model_value: Any | None = None,
        ui_title: str | None = None,
        ui_buttons: bool | None = None,
        ui_label_set: str | None = None,
        ui_label_cancel: str | None = None,
        ui_auto_save: bool | None = None,
        ui_color: Any | None = None,
        ui_validate: Callable | None = None,
        ui_disable: Any | None = None,
        ui_fit: bool | None = None,
        ui_cover: bool | None = None,
        ui_anchor: str | None = None,
        ui_self: str | None = None,
        ui_offset: list | None = None,
        ui_touch_position: bool | None = None,
        ui_persistent: bool | None = None,
        ui_separate_close_popup: bool | None = None,
        ui_square: bool | None = None,
        ui_max_height: Any | None = None,
        ui_max_width: Any | None = None,
        **kwargs,
    ):
        super().__init__("QPopupEdit", *children, **kwargs)
        self.on("update:model-value", self.__update_model_value)

        if ui_model_value is not None:
            self._props["model-value"] = ui_model_value
        if ui_title is not None:
            self._props["title"] = ui_title
        if ui_buttons is not None:
            self._props["buttons"] = ui_buttons
        if ui_label_set is not None:
            self._props["label-set"] = ui_label_set
        if ui_label_cancel is not None:
            self._props["label-cancel"] = ui_label_cancel
        if ui_auto_save is not None:
            self._props["auto-save"] = ui_auto_save
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_validate is not None:
            self._props["validate"] = ui_validate
        if ui_disable is not None:
            self._props["disable"] = ui_disable
        if ui_fit is not None:
            self._props["fit"] = ui_fit
        if ui_cover is not None:
            self._props["cover"] = ui_cover
        if ui_anchor is not None:
            self._props["anchor"] = ui_anchor
        if ui_self is not None:
            self._props["self"] = ui_self
        if ui_offset is not None:
            self._props["offset"] = ui_offset
        if ui_touch_position is not None:
            self._props["touch-position"] = ui_touch_position
        if ui_persistent is not None:
            self._props["persistent"] = ui_persistent
        if ui_separate_close_popup is not None:
            self._props["separate-close-popup"] = ui_separate_close_popup
        if ui_square is not None:
            self._props["square"] = ui_square
        if ui_max_height is not None:
            self._props["max-height"] = ui_max_height
        if ui_max_width is not None:
            self._props["max-width"] = ui_max_width

    def __update_model_value(self, event: Event):
        self._set_prop("model-value", event.value)

    @property
    def ui_model_value(self):
        return self._props.get("model-value")

    @ui_model_value.setter
    def ui_model_value(self, value):
        self._set_prop("model-value", value)

    @property
    def ui_title(self):
        """Optional title (unless 'title' slot is used)"""
        return self._props.get("title")

    @ui_title.setter
    def ui_title(self, value):
        self._set_prop("title", value)

    @property
    def ui_buttons(self):
        """Show Set and Cancel buttons"""
        return self._props.get("buttons")

    @ui_buttons.setter
    def ui_buttons(self, value):
        self._set_prop("buttons", value)

    @property
    def ui_label_set(self):
        """Override Set button label"""
        return self._props.get("label-set")

    @ui_label_set.setter
    def ui_label_set(self, value):
        self._set_prop("label-set", value)

    @property
    def ui_label_cancel(self):
        """Override Cancel button label"""
        return self._props.get("label-cancel")

    @ui_label_cancel.setter
    def ui_label_cancel(self, value):
        self._set_prop("label-cancel", value)

    @property
    def ui_auto_save(self):
        """Automatically save the model (if changed) when user clicks/taps outside of the popup; It does not apply to ESC key"""
        return self._props.get("auto-save")

    @ui_auto_save.setter
    def ui_auto_save(self, value):
        self._set_prop("auto-save", value)

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_validate(self):
        """Validates model then triggers 'save' and closes Popup; Returns a Boolean ('true' means valid, 'false' means abort); Syntax: validate(value); For best performance, reference it from your scope and do not define it inline"""
        return self._props.get("validate")

    @ui_validate.setter
    def ui_validate(self, value):
        self._set_prop("validate", value)

    @property
    def ui_disable(self):
        return self._props.get("disable")

    @ui_disable.setter
    def ui_disable(self, value):
        self._set_prop("disable", value)

    @property
    def ui_fit(self):
        """Allows the menu to match at least the full width of its target"""
        return self._props.get("fit")

    @ui_fit.setter
    def ui_fit(self, value):
        self._set_prop("fit", value)

    @property
    def ui_cover(self):
        """Allows the menu to cover its target. When used, the 'self' and 'fit' props are no longer effective"""
        return self._props.get("cover")

    @ui_cover.setter
    def ui_cover(self, value):
        self._set_prop("cover", value)

    @property
    def ui_anchor(self):
        """Two values setting the starting position or anchor point of the menu relative to its target"""
        return self._props.get("anchor")

    @ui_anchor.setter
    def ui_anchor(self, value):
        self._set_prop("anchor", value)

    @property
    def ui_self(self):
        """Two values setting the menu's own position relative to its target"""
        return self._props.get("self")

    @ui_self.setter
    def ui_self(self, value):
        self._set_prop("self", value)

    @property
    def ui_offset(self):
        """An array of two numbers to offset the menu horizontally and vertically in pixels"""
        return self._props.get("offset")

    @ui_offset.setter
    def ui_offset(self, value):
        self._set_prop("offset", value)

    @property
    def ui_touch_position(self):
        """Allows for the target position to be set by the mouse position, when the target of the menu is either clicked or touched"""
        return self._props.get("touch-position")

    @ui_touch_position.setter
    def ui_touch_position(self, value):
        self._set_prop("touch-position", value)

    @property
    def ui_persistent(self):
        """Avoid menu closing by hitting ESC key or by clicking/tapping outside of the Popup"""
        return self._props.get("persistent")

    @ui_persistent.setter
    def ui_persistent(self, value):
        self._set_prop("persistent", value)

    @property
    def ui_separate_close_popup(self):
        """Separate from parent menu, marking it as a separate closing point for v-close-popup (without this, chained menus close all together)"""
        return self._props.get("separate-close-popup")

    @ui_separate_close_popup.setter
    def ui_separate_close_popup(self, value):
        self._set_prop("separate-close-popup", value)

    @property
    def ui_square(self):
        """Forces menu to have squared borders"""
        return self._props.get("square")

    @ui_square.setter
    def ui_square(self, value):
        self._set_prop("square", value)

    @property
    def ui_max_height(self):
        """The maximum height of the menu; Size in CSS units, including unit name"""
        return self._props.get("max-height")

    @ui_max_height.setter
    def ui_max_height(self, value):
        self._set_prop("max-height", value)

    @property
    def ui_max_width(self):
        """The maximum width of the menu; Size in CSS units, including unit name"""
        return self._props.get("max-width")

    @ui_max_width.setter
    def ui_max_width(self, value):
        self._set_prop("max-width", value)

    def on_before_hide(self, handler: Callable, arg: object = None):
        """
        Emitted right before Popup gets dismissed

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("before-hide", handler, arg)

    def on_before_show(self, handler: Callable, arg: object = None):
        """
        Emitted right before Popup gets shown

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("before-show", handler, arg)

    def on_cancel(self, handler: Callable, arg: object = None):
        """
        Emitted when user cancelled the change (hit ESC key or clicking outside of Popup or hit 'Cancel' button)

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("cancel", handler, arg)

    def on_hide(self, handler: Callable, arg: object = None):
        """
        Emitted right after Popup gets dismissed

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("hide", handler, arg)

    def on_save(self, handler: Callable, arg: object = None):
        """
        Emitted when value has been successfully validated and it should be saved

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("save", handler, arg)

    def on_show(self, handler: Callable, arg: object = None):
        """
        Emitted right after Popup gets shown

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("show", handler, arg)

    def on_update_model_value(self, handler: Callable, arg: object = None):
        """
        Emitted when Popup gets cancelled in order to reset model to its initial value; Is also used by v-model

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("update:model-value", handler, arg)

    def ui_cancel(self):
        """Triggers a model reset to its initial value ('cancel' event is emitted) then closes Popup"""
        self._js_call_method("cancel")

    def ui_hide(self):
        self._js_call_method("hide")

    def ui_set(self):
        """Trigger a model update; Validates model (and emits 'save' event if it's the case) then closes Popup"""
        self._js_call_method("set")

    def ui_show(self):
        self._js_call_method("show")

    def ui_updatePosition(self):
        """There are some custom scenarios for which Quasar cannot automatically reposition the component without significant performance drawbacks so the optimal solution is for you to call this method when you need it"""
        self._js_call_method("updatePosition")

    def _get_js_methods(self):
        return ["cancel", "hide", "set", "show", "updatePosition"]


class QPopupProxy(Component):
    """
    Quasar Component: `QPopupProxy <https://v2.quasar.dev/vue-components/popup-proxy>`__

    :param ui_model_value: Defines the state of the component (shown/hidden); Either use this property (along with a listener for 'update:modelValue' event) OR use v-model directive
    :param ui_breakpoint: Breakpoint (in pixels) of window width/height (whichever is smaller) from where a Menu will get to be used instead of a Dialog
    :param ui_context_menu: Allows the component to behave like a context menu, which opens with a right mouse click (or long tap on mobile)
    :param ui_target: Configure a target element to trigger component toggle; 'true' means it enables the parent DOM element, 'false' means it disables attaching events to any DOM elements; By using a String (CSS selector) or a DOM element it attaches the events to the specified DOM element (if it exists)
    :param ui_no_parent_event: Skips attaching events to the target DOM element (that trigger the element to get shown)
    """

    def __init__(
        self,
        *children,
        ui_model_value: bool | None = None,
        ui_breakpoint: float | str | None = None,
        ui_context_menu: bool | None = None,
        ui_target: bool | str | Any | None = None,
        ui_no_parent_event: bool | None = None,
        **kwargs,
    ):
        super().__init__("QPopupProxy", *children, **kwargs)
        self.on("update:model-value", self.__update_model_value)

        if ui_model_value is not None:
            self._props["model-value"] = ui_model_value
        if ui_breakpoint is not None:
            self._props["breakpoint"] = ui_breakpoint
        if ui_context_menu is not None:
            self._props["context-menu"] = ui_context_menu
        if ui_target is not None:
            self._props["target"] = ui_target
        if ui_no_parent_event is not None:
            self._props["no-parent-event"] = ui_no_parent_event

    def __update_model_value(self, event: Event):
        self._set_prop("model-value", event.value)

    @property
    def ui_model_value(self):
        """Defines the state of the component (shown/hidden); Either use this property (along with a listener for 'update:modelValue' event) OR use v-model directive"""
        return self._props.get("model-value")

    @ui_model_value.setter
    def ui_model_value(self, value):
        self._set_prop("model-value", value)

    @property
    def ui_breakpoint(self):
        """Breakpoint (in pixels) of window width/height (whichever is smaller) from where a Menu will get to be used instead of a Dialog"""
        return self._props.get("breakpoint")

    @ui_breakpoint.setter
    def ui_breakpoint(self, value):
        self._set_prop("breakpoint", value)

    @property
    def ui_context_menu(self):
        """Allows the component to behave like a context menu, which opens with a right mouse click (or long tap on mobile)"""
        return self._props.get("context-menu")

    @ui_context_menu.setter
    def ui_context_menu(self, value):
        self._set_prop("context-menu", value)

    @property
    def ui_target(self):
        """Configure a target element to trigger component toggle; 'true' means it enables the parent DOM element, 'false' means it disables attaching events to any DOM elements; By using a String (CSS selector) or a DOM element it attaches the events to the specified DOM element (if it exists)"""
        return self._props.get("target")

    @ui_target.setter
    def ui_target(self, value):
        self._set_prop("target", value)

    @property
    def ui_no_parent_event(self):
        """Skips attaching events to the target DOM element (that trigger the element to get shown)"""
        return self._props.get("no-parent-event")

    @ui_no_parent_event.setter
    def ui_no_parent_event(self, value):
        self._set_prop("no-parent-event", value)

    def on_before_hide(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("before-hide", handler, arg)

    def on_before_show(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("before-show", handler, arg)

    def on_hide(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("hide", handler, arg)

    def on_show(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("show", handler, arg)

    def on_update_model_value(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("update:model-value", handler, arg)

    def ui_hide(self):
        self._js_call_method("hide")

    def ui_show(self):
        self._js_call_method("show")

    def ui_toggle(self):
        self._js_call_method("toggle")

    def _get_js_methods(self):
        return ["hide", "show", "toggle"]


class QPullToRefresh(Component):
    """
    Quasar Component: `QPullToRefresh <https://v2.quasar.dev/vue-components/pull-to-refresh>`__

    :param ui_color: Color name for the icon from the Quasar Color Palette
    :param ui_bg_color: Color name for background of the icon container from the Quasar Color Palette
    :param ui_icon: Icon to display when refreshing the content
    :param ui_no_mouse: Don't listen for mouse events
    :param ui_disable:
    :param ui_scroll_target:
    """

    def __init__(
        self,
        *children,
        ui_color: Any | None = None,
        ui_bg_color: Any | None = None,
        ui_icon: Any | None = None,
        ui_no_mouse: bool | None = None,
        ui_disable: Any | None = None,
        ui_scroll_target: Any | None = None,
        **kwargs,
    ):
        super().__init__("QPullToRefresh", *children, **kwargs)
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_bg_color is not None:
            self._props["bg-color"] = ui_bg_color
        if ui_icon is not None:
            self._props["icon"] = ui_icon
        if ui_no_mouse is not None:
            self._props["no-mouse"] = ui_no_mouse
        if ui_disable is not None:
            self._props["disable"] = ui_disable
        if ui_scroll_target is not None:
            self._props["scroll-target"] = ui_scroll_target

    @property
    def ui_color(self):
        """Color name for the icon from the Quasar Color Palette"""
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_bg_color(self):
        """Color name for background of the icon container from the Quasar Color Palette"""
        return self._props.get("bg-color")

    @ui_bg_color.setter
    def ui_bg_color(self, value):
        self._set_prop("bg-color", value)

    @property
    def ui_icon(self):
        """Icon to display when refreshing the content"""
        return self._props.get("icon")

    @ui_icon.setter
    def ui_icon(self, value):
        self._set_prop("icon", value)

    @property
    def ui_no_mouse(self):
        """Don't listen for mouse events"""
        return self._props.get("no-mouse")

    @ui_no_mouse.setter
    def ui_no_mouse(self, value):
        self._set_prop("no-mouse", value)

    @property
    def ui_disable(self):
        return self._props.get("disable")

    @ui_disable.setter
    def ui_disable(self, value):
        self._set_prop("disable", value)

    @property
    def ui_scroll_target(self):
        return self._props.get("scroll-target")

    @ui_scroll_target.setter
    def ui_scroll_target(self, value):
        self._set_prop("scroll-target", value)

    def on_refresh(self, handler: Callable, arg: object = None):
        """
        Called whenever a refresh is triggered; at this time, your function should load more data

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("refresh", handler, arg)

    def ui_trigger(self):
        """Triggers a refresh"""
        self._js_call_method("trigger")

    def ui_updateScrollTarget(self):
        """Updates the scroll target; Useful when the parent elements change so that the scrolling target also changes"""
        self._js_call_method("updateScrollTarget")

    def _get_js_methods(self):
        return ["trigger", "updateScrollTarget"]


class QRadio(Component):
    """
    Quasar Component: `QRadio <https://v2.quasar.dev/vue-components/radio>`__

    :param ui_model_value:
    :param ui_val: The actual value of the option with which model value is changed
    :param ui_label: Label to display along the radio control (or use the default slot instead of this prop)
    :param ui_left_label: Label (if any specified) should be displayed on the left side of the checkbox
    :param ui_checked_icon: The icon to be used when selected (instead of the default design)
    :param ui_unchecked_icon: The icon to be used when un-selected (instead of the default design)
    :param ui_color:
    :param ui_keep_color: Should the color (if specified any) be kept when checkbox is unticked?
    :param ui_dark:
    :param ui_dense:
    :param ui_disable:
    :param ui_tabindex:
    :param ui_size: Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)
    :param ui_name: Used to specify the name of the control; Useful if dealing with forms submitted directly to a URL
    """

    def __init__(
        self,
        *children,
        ui_model_value: Any | None = None,
        ui_val: Any | None = None,
        ui_label: str | None = None,
        ui_left_label: bool | None = None,
        ui_checked_icon: str | None = None,
        ui_unchecked_icon: str | None = None,
        ui_color: Any | None = None,
        ui_keep_color: bool | None = None,
        ui_dark: Any | None = None,
        ui_dense: Any | None = None,
        ui_disable: Any | None = None,
        ui_tabindex: Any | None = None,
        ui_size: str | None = None,
        ui_name: str | None = None,
        **kwargs,
    ):
        super().__init__("QRadio", *children, **kwargs)
        self.on("update:model-value", self.__update_model_value)

        if ui_model_value is not None:
            self._props["model-value"] = ui_model_value
        if ui_val is not None:
            self._props["val"] = ui_val
        if ui_label is not None:
            self._props["label"] = ui_label
        if ui_left_label is not None:
            self._props["left-label"] = ui_left_label
        if ui_checked_icon is not None:
            self._props["checked-icon"] = ui_checked_icon
        if ui_unchecked_icon is not None:
            self._props["unchecked-icon"] = ui_unchecked_icon
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_keep_color is not None:
            self._props["keep-color"] = ui_keep_color
        if ui_dark is not None:
            self._props["dark"] = ui_dark
        if ui_dense is not None:
            self._props["dense"] = ui_dense
        if ui_disable is not None:
            self._props["disable"] = ui_disable
        if ui_tabindex is not None:
            self._props["tabindex"] = ui_tabindex
        if ui_size is not None:
            self._props["size"] = ui_size
        if ui_name is not None:
            self._props["name"] = ui_name

    def __update_model_value(self, event: Event):
        self._set_prop("model-value", event.value)

    @property
    def ui_model_value(self):
        return self._props.get("model-value")

    @ui_model_value.setter
    def ui_model_value(self, value):
        self._set_prop("model-value", value)

    @property
    def ui_val(self):
        """The actual value of the option with which model value is changed"""
        return self._props.get("val")

    @ui_val.setter
    def ui_val(self, value):
        self._set_prop("val", value)

    @property
    def ui_label(self):
        """Label to display along the radio control (or use the default slot instead of this prop)"""
        return self._props.get("label")

    @ui_label.setter
    def ui_label(self, value):
        self._set_prop("label", value)

    @property
    def ui_left_label(self):
        """Label (if any specified) should be displayed on the left side of the checkbox"""
        return self._props.get("left-label")

    @ui_left_label.setter
    def ui_left_label(self, value):
        self._set_prop("left-label", value)

    @property
    def ui_checked_icon(self):
        """The icon to be used when selected (instead of the default design)"""
        return self._props.get("checked-icon")

    @ui_checked_icon.setter
    def ui_checked_icon(self, value):
        self._set_prop("checked-icon", value)

    @property
    def ui_unchecked_icon(self):
        """The icon to be used when un-selected (instead of the default design)"""
        return self._props.get("unchecked-icon")

    @ui_unchecked_icon.setter
    def ui_unchecked_icon(self, value):
        self._set_prop("unchecked-icon", value)

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_keep_color(self):
        """Should the color (if specified any) be kept when checkbox is unticked?"""
        return self._props.get("keep-color")

    @ui_keep_color.setter
    def ui_keep_color(self, value):
        self._set_prop("keep-color", value)

    @property
    def ui_dark(self):
        return self._props.get("dark")

    @ui_dark.setter
    def ui_dark(self, value):
        self._set_prop("dark", value)

    @property
    def ui_dense(self):
        return self._props.get("dense")

    @ui_dense.setter
    def ui_dense(self, value):
        self._set_prop("dense", value)

    @property
    def ui_disable(self):
        return self._props.get("disable")

    @ui_disable.setter
    def ui_disable(self, value):
        self._set_prop("disable", value)

    @property
    def ui_tabindex(self):
        return self._props.get("tabindex")

    @ui_tabindex.setter
    def ui_tabindex(self, value):
        self._set_prop("tabindex", value)

    @property
    def ui_size(self):
        """Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)"""
        return self._props.get("size")

    @ui_size.setter
    def ui_size(self, value):
        self._set_prop("size", value)

    @property
    def ui_name(self):
        """Used to specify the name of the control; Useful if dealing with forms submitted directly to a URL"""
        return self._props.get("name")

    @ui_name.setter
    def ui_name(self, value):
        self._set_prop("name", value)

    def on_update_model_value(self, handler: Callable, arg: object = None):
        """
        Emitted when the component needs to change the model; Is also used by v-model

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("update:model-value", handler, arg)

    def ui_set(self):
        """Sets the Radio's v-model to equal the val"""
        self._js_call_method("set")

    def _get_js_methods(self):
        return ["set"]


class QRange(Component):
    """
    Quasar Component: `QRange <https://v2.quasar.dev/vue-components/range>`__

    :param ui_model_value: Model of the component of type { min, max } (both values must be between global min/max); Either use this property (along with a listener for 'update:modelValue' event) OR use v-model directive
    :param ui_drag_range: User can drag range instead of just the two thumbs
    :param ui_drag_only_range: User can drag only the range instead and NOT the two thumbs
    :param ui_left_label_color: Color name for left label background from the Quasar Color Palette
    :param ui_left_label_text_color: Color name for left label text from the Quasar Color Palette
    :param ui_right_label_color: Color name for right label background from the Quasar Color Palette
    :param ui_right_label_text_color: Color name for right label text from the Quasar Color Palette
    :param ui_left_label_value: Override default label for min value
    :param ui_right_label_value: Override default label for max value
    :param ui_left_thumb_color: Color name (from the Quasar Color Palette) for left thumb
    :param ui_right_thumb_color: Color name (from the Quasar Color Palette) for right thumb
    :param ui_min: Minimum value of the model; Set track's minimum value
    :param ui_max: Maximum value of the model; Set track's maximum value
    :param ui_inner_min: Inner minimum value of the model; Use in case you need the model value to be inside of the track's min-max values; Needs to be higher or equal to 'min' prop; Defaults to 'min' prop
    :param ui_inner_max: Inner maximum value of the model; Use in case you need the model value to be inside of the track's min-max values; Needs to be lower or equal to 'max' prop; Defaults to 'max' prop
    :param ui_step: Specify step amount between valid values (> 0.0); When step equals to 0 it defines infinite granularity
    :param ui_snap: Snap on valid values, rather than sliding freely; Suggestion: use with 'step' prop
    :param ui_reverse: Work in reverse (changes direction)
    :param ui_vertical: Display in vertical direction
    :param ui_color:
    :param ui_track_color: Color name for the track (can be 'transparent' too) from the Quasar Color Palette
    :param ui_track_img: Apply a pattern image on the track
    :param ui_inner_track_color: Color name for the inner track (can be 'transparent' too) from the Quasar Color Palette
    :param ui_inner_track_img: Apply a pattern image on the inner track
    :param ui_selection_color: Color name for the selection bar (can be 'transparent' too) from the Quasar Color Palette
    :param ui_selection_img: Apply a pattern image on the selection bar
    :param ui_label: Popup a label when user clicks/taps on the slider thumb and moves it
    :param ui_label_color:
    :param ui_label_text_color:
    :param ui_switch_label_side: Switch the position of the label (top <-> bottom or left <-> right)
    :param ui_label_always: Always display the label
    :param ui_markers: Display markers on the track, one for each possible value for the model or using a custom step (when specifying a Number)
    :param ui_marker_labels: Configure the marker labels (or show the default ones if 'true'); Array of definition Objects or Object with key-value where key is the model and the value is the marker label definition
    :param ui_marker_labels_class: CSS class(es) to apply to the marker labels container
    :param ui_switch_marker_labels_side: Switch the position of the marker labels (top <-> bottom or left <-> right)
    :param ui_track_size: Track size (including CSS unit)
    :param ui_thumb_size: Thumb size (including CSS unit)
    :param ui_thumb_color:
    :param ui_thumb_path: Set custom thumb svg path
    :param ui_dark:
    :param ui_dense:
    :param ui_disable:
    :param ui_readonly:
    :param ui_tabindex:
    :param ui_name: Used to specify the name of the control; Useful if dealing with forms submitted directly to a URL
    """

    def __init__(
        self,
        *children,
        ui_model_value: dict | None | Any = None,
        ui_drag_range: bool | None = None,
        ui_drag_only_range: bool | None = None,
        ui_left_label_color: Any | None = None,
        ui_left_label_text_color: Any | None = None,
        ui_right_label_color: Any | None = None,
        ui_right_label_text_color: Any | None = None,
        ui_left_label_value: str | float | None = None,
        ui_right_label_value: str | float | None = None,
        ui_left_thumb_color: Any | None = None,
        ui_right_thumb_color: Any | None = None,
        ui_min: float | None = None,
        ui_max: float | None = None,
        ui_inner_min: float | None = None,
        ui_inner_max: float | None = None,
        ui_step: float | None = None,
        ui_snap: bool | None = None,
        ui_reverse: bool | None = None,
        ui_vertical: bool | None = None,
        ui_color: Any | None = None,
        ui_track_color: Any | None = None,
        ui_track_img: str | None = None,
        ui_inner_track_color: Any | None = None,
        ui_inner_track_img: str | None = None,
        ui_selection_color: Any | None = None,
        ui_selection_img: str | None = None,
        ui_label: bool | None = None,
        ui_label_color: Any | None = None,
        ui_label_text_color: Any | None = None,
        ui_switch_label_side: bool | None = None,
        ui_label_always: bool | None = None,
        ui_markers: bool | float | None = None,
        ui_marker_labels: bool | list | dict | Callable | None = None,
        ui_marker_labels_class: str | None = None,
        ui_switch_marker_labels_side: bool | None = None,
        ui_track_size: str | None = None,
        ui_thumb_size: str | None = None,
        ui_thumb_color: Any | None = None,
        ui_thumb_path: str | None = None,
        ui_dark: Any | None = None,
        ui_dense: Any | None = None,
        ui_disable: Any | None = None,
        ui_readonly: Any | None = None,
        ui_tabindex: Any | None = None,
        ui_name: str | None = None,
        **kwargs,
    ):
        super().__init__("QRange", *children, **kwargs)
        self.on("update:model-value", self.__update_model_value)

        if ui_model_value is not None:
            self._props["model-value"] = ui_model_value
        if ui_drag_range is not None:
            self._props["drag-range"] = ui_drag_range
        if ui_drag_only_range is not None:
            self._props["drag-only-range"] = ui_drag_only_range
        if ui_left_label_color is not None:
            self._props["left-label-color"] = ui_left_label_color
        if ui_left_label_text_color is not None:
            self._props["left-label-text-color"] = ui_left_label_text_color
        if ui_right_label_color is not None:
            self._props["right-label-color"] = ui_right_label_color
        if ui_right_label_text_color is not None:
            self._props["right-label-text-color"] = ui_right_label_text_color
        if ui_left_label_value is not None:
            self._props["left-label-value"] = ui_left_label_value
        if ui_right_label_value is not None:
            self._props["right-label-value"] = ui_right_label_value
        if ui_left_thumb_color is not None:
            self._props["left-thumb-color"] = ui_left_thumb_color
        if ui_right_thumb_color is not None:
            self._props["right-thumb-color"] = ui_right_thumb_color
        if ui_min is not None:
            self._props["min"] = ui_min
        if ui_max is not None:
            self._props["max"] = ui_max
        if ui_inner_min is not None:
            self._props["inner-min"] = ui_inner_min
        if ui_inner_max is not None:
            self._props["inner-max"] = ui_inner_max
        if ui_step is not None:
            self._props["step"] = ui_step
        if ui_snap is not None:
            self._props["snap"] = ui_snap
        if ui_reverse is not None:
            self._props["reverse"] = ui_reverse
        if ui_vertical is not None:
            self._props["vertical"] = ui_vertical
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_track_color is not None:
            self._props["track-color"] = ui_track_color
        if ui_track_img is not None:
            self._props["track-img"] = ui_track_img
        if ui_inner_track_color is not None:
            self._props["inner-track-color"] = ui_inner_track_color
        if ui_inner_track_img is not None:
            self._props["inner-track-img"] = ui_inner_track_img
        if ui_selection_color is not None:
            self._props["selection-color"] = ui_selection_color
        if ui_selection_img is not None:
            self._props["selection-img"] = ui_selection_img
        if ui_label is not None:
            self._props["label"] = ui_label
        if ui_label_color is not None:
            self._props["label-color"] = ui_label_color
        if ui_label_text_color is not None:
            self._props["label-text-color"] = ui_label_text_color
        if ui_switch_label_side is not None:
            self._props["switch-label-side"] = ui_switch_label_side
        if ui_label_always is not None:
            self._props["label-always"] = ui_label_always
        if ui_markers is not None:
            self._props["markers"] = ui_markers
        if ui_marker_labels is not None:
            self._props["marker-labels"] = ui_marker_labels
        if ui_marker_labels_class is not None:
            self._props["marker-labels-class"] = ui_marker_labels_class
        if ui_switch_marker_labels_side is not None:
            self._props["switch-marker-labels-side"] = (
                ui_switch_marker_labels_side
            )
        if ui_track_size is not None:
            self._props["track-size"] = ui_track_size
        if ui_thumb_size is not None:
            self._props["thumb-size"] = ui_thumb_size
        if ui_thumb_color is not None:
            self._props["thumb-color"] = ui_thumb_color
        if ui_thumb_path is not None:
            self._props["thumb-path"] = ui_thumb_path
        if ui_dark is not None:
            self._props["dark"] = ui_dark
        if ui_dense is not None:
            self._props["dense"] = ui_dense
        if ui_disable is not None:
            self._props["disable"] = ui_disable
        if ui_readonly is not None:
            self._props["readonly"] = ui_readonly
        if ui_tabindex is not None:
            self._props["tabindex"] = ui_tabindex
        if ui_name is not None:
            self._props["name"] = ui_name

    def __update_model_value(self, event: Event):
        self._set_prop("model-value", event.value)

    @property
    def ui_model_value(self):
        """Model of the component of type { min, max } (both values must be between global min/max); Either use this property (along with a listener for 'update:modelValue' event) OR use v-model directive"""
        return self._props.get("model-value")

    @ui_model_value.setter
    def ui_model_value(self, value):
        self._set_prop("model-value", value)

    @property
    def ui_drag_range(self):
        """User can drag range instead of just the two thumbs"""
        return self._props.get("drag-range")

    @ui_drag_range.setter
    def ui_drag_range(self, value):
        self._set_prop("drag-range", value)

    @property
    def ui_drag_only_range(self):
        """User can drag only the range instead and NOT the two thumbs"""
        return self._props.get("drag-only-range")

    @ui_drag_only_range.setter
    def ui_drag_only_range(self, value):
        self._set_prop("drag-only-range", value)

    @property
    def ui_left_label_color(self):
        """Color name for left label background from the Quasar Color Palette"""
        return self._props.get("left-label-color")

    @ui_left_label_color.setter
    def ui_left_label_color(self, value):
        self._set_prop("left-label-color", value)

    @property
    def ui_left_label_text_color(self):
        """Color name for left label text from the Quasar Color Palette"""
        return self._props.get("left-label-text-color")

    @ui_left_label_text_color.setter
    def ui_left_label_text_color(self, value):
        self._set_prop("left-label-text-color", value)

    @property
    def ui_right_label_color(self):
        """Color name for right label background from the Quasar Color Palette"""
        return self._props.get("right-label-color")

    @ui_right_label_color.setter
    def ui_right_label_color(self, value):
        self._set_prop("right-label-color", value)

    @property
    def ui_right_label_text_color(self):
        """Color name for right label text from the Quasar Color Palette"""
        return self._props.get("right-label-text-color")

    @ui_right_label_text_color.setter
    def ui_right_label_text_color(self, value):
        self._set_prop("right-label-text-color", value)

    @property
    def ui_left_label_value(self):
        """Override default label for min value"""
        return self._props.get("left-label-value")

    @ui_left_label_value.setter
    def ui_left_label_value(self, value):
        self._set_prop("left-label-value", value)

    @property
    def ui_right_label_value(self):
        """Override default label for max value"""
        return self._props.get("right-label-value")

    @ui_right_label_value.setter
    def ui_right_label_value(self, value):
        self._set_prop("right-label-value", value)

    @property
    def ui_left_thumb_color(self):
        """Color name (from the Quasar Color Palette) for left thumb"""
        return self._props.get("left-thumb-color")

    @ui_left_thumb_color.setter
    def ui_left_thumb_color(self, value):
        self._set_prop("left-thumb-color", value)

    @property
    def ui_right_thumb_color(self):
        """Color name (from the Quasar Color Palette) for right thumb"""
        return self._props.get("right-thumb-color")

    @ui_right_thumb_color.setter
    def ui_right_thumb_color(self, value):
        self._set_prop("right-thumb-color", value)

    @property
    def ui_min(self):
        """Minimum value of the model; Set track's minimum value"""
        return self._props.get("min")

    @ui_min.setter
    def ui_min(self, value):
        self._set_prop("min", value)

    @property
    def ui_max(self):
        """Maximum value of the model; Set track's maximum value"""
        return self._props.get("max")

    @ui_max.setter
    def ui_max(self, value):
        self._set_prop("max", value)

    @property
    def ui_inner_min(self):
        """Inner minimum value of the model; Use in case you need the model value to be inside of the track's min-max values; Needs to be higher or equal to 'min' prop; Defaults to 'min' prop"""
        return self._props.get("inner-min")

    @ui_inner_min.setter
    def ui_inner_min(self, value):
        self._set_prop("inner-min", value)

    @property
    def ui_inner_max(self):
        """Inner maximum value of the model; Use in case you need the model value to be inside of the track's min-max values; Needs to be lower or equal to 'max' prop; Defaults to 'max' prop"""
        return self._props.get("inner-max")

    @ui_inner_max.setter
    def ui_inner_max(self, value):
        self._set_prop("inner-max", value)

    @property
    def ui_step(self):
        """Specify step amount between valid values (> 0.0); When step equals to 0 it defines infinite granularity"""
        return self._props.get("step")

    @ui_step.setter
    def ui_step(self, value):
        self._set_prop("step", value)

    @property
    def ui_snap(self):
        """Snap on valid values, rather than sliding freely; Suggestion: use with 'step' prop"""
        return self._props.get("snap")

    @ui_snap.setter
    def ui_snap(self, value):
        self._set_prop("snap", value)

    @property
    def ui_reverse(self):
        """Work in reverse (changes direction)"""
        return self._props.get("reverse")

    @ui_reverse.setter
    def ui_reverse(self, value):
        self._set_prop("reverse", value)

    @property
    def ui_vertical(self):
        """Display in vertical direction"""
        return self._props.get("vertical")

    @ui_vertical.setter
    def ui_vertical(self, value):
        self._set_prop("vertical", value)

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_track_color(self):
        """Color name for the track (can be 'transparent' too) from the Quasar Color Palette"""
        return self._props.get("track-color")

    @ui_track_color.setter
    def ui_track_color(self, value):
        self._set_prop("track-color", value)

    @property
    def ui_track_img(self):
        """Apply a pattern image on the track"""
        return self._props.get("track-img")

    @ui_track_img.setter
    def ui_track_img(self, value):
        self._set_prop("track-img", value)

    @property
    def ui_inner_track_color(self):
        """Color name for the inner track (can be 'transparent' too) from the Quasar Color Palette"""
        return self._props.get("inner-track-color")

    @ui_inner_track_color.setter
    def ui_inner_track_color(self, value):
        self._set_prop("inner-track-color", value)

    @property
    def ui_inner_track_img(self):
        """Apply a pattern image on the inner track"""
        return self._props.get("inner-track-img")

    @ui_inner_track_img.setter
    def ui_inner_track_img(self, value):
        self._set_prop("inner-track-img", value)

    @property
    def ui_selection_color(self):
        """Color name for the selection bar (can be 'transparent' too) from the Quasar Color Palette"""
        return self._props.get("selection-color")

    @ui_selection_color.setter
    def ui_selection_color(self, value):
        self._set_prop("selection-color", value)

    @property
    def ui_selection_img(self):
        """Apply a pattern image on the selection bar"""
        return self._props.get("selection-img")

    @ui_selection_img.setter
    def ui_selection_img(self, value):
        self._set_prop("selection-img", value)

    @property
    def ui_label(self):
        """Popup a label when user clicks/taps on the slider thumb and moves it"""
        return self._props.get("label")

    @ui_label.setter
    def ui_label(self, value):
        self._set_prop("label", value)

    @property
    def ui_label_color(self):
        return self._props.get("label-color")

    @ui_label_color.setter
    def ui_label_color(self, value):
        self._set_prop("label-color", value)

    @property
    def ui_label_text_color(self):
        return self._props.get("label-text-color")

    @ui_label_text_color.setter
    def ui_label_text_color(self, value):
        self._set_prop("label-text-color", value)

    @property
    def ui_switch_label_side(self):
        """Switch the position of the label (top <-> bottom or left <-> right)"""
        return self._props.get("switch-label-side")

    @ui_switch_label_side.setter
    def ui_switch_label_side(self, value):
        self._set_prop("switch-label-side", value)

    @property
    def ui_label_always(self):
        """Always display the label"""
        return self._props.get("label-always")

    @ui_label_always.setter
    def ui_label_always(self, value):
        self._set_prop("label-always", value)

    @property
    def ui_markers(self):
        """Display markers on the track, one for each possible value for the model or using a custom step (when specifying a Number)"""
        return self._props.get("markers")

    @ui_markers.setter
    def ui_markers(self, value):
        self._set_prop("markers", value)

    @property
    def ui_marker_labels(self):
        """Configure the marker labels (or show the default ones if 'true'); Array of definition Objects or Object with key-value where key is the model and the value is the marker label definition"""
        return self._props.get("marker-labels")

    @ui_marker_labels.setter
    def ui_marker_labels(self, value):
        self._set_prop("marker-labels", value)

    @property
    def ui_marker_labels_class(self):
        """CSS class(es) to apply to the marker labels container"""
        return self._props.get("marker-labels-class")

    @ui_marker_labels_class.setter
    def ui_marker_labels_class(self, value):
        self._set_prop("marker-labels-class", value)

    @property
    def ui_switch_marker_labels_side(self):
        """Switch the position of the marker labels (top <-> bottom or left <-> right)"""
        return self._props.get("switch-marker-labels-side")

    @ui_switch_marker_labels_side.setter
    def ui_switch_marker_labels_side(self, value):
        self._set_prop("switch-marker-labels-side", value)

    @property
    def ui_track_size(self):
        """Track size (including CSS unit)"""
        return self._props.get("track-size")

    @ui_track_size.setter
    def ui_track_size(self, value):
        self._set_prop("track-size", value)

    @property
    def ui_thumb_size(self):
        """Thumb size (including CSS unit)"""
        return self._props.get("thumb-size")

    @ui_thumb_size.setter
    def ui_thumb_size(self, value):
        self._set_prop("thumb-size", value)

    @property
    def ui_thumb_color(self):
        return self._props.get("thumb-color")

    @ui_thumb_color.setter
    def ui_thumb_color(self, value):
        self._set_prop("thumb-color", value)

    @property
    def ui_thumb_path(self):
        """Set custom thumb svg path"""
        return self._props.get("thumb-path")

    @ui_thumb_path.setter
    def ui_thumb_path(self, value):
        self._set_prop("thumb-path", value)

    @property
    def ui_dark(self):
        return self._props.get("dark")

    @ui_dark.setter
    def ui_dark(self, value):
        self._set_prop("dark", value)

    @property
    def ui_dense(self):
        return self._props.get("dense")

    @ui_dense.setter
    def ui_dense(self, value):
        self._set_prop("dense", value)

    @property
    def ui_disable(self):
        return self._props.get("disable")

    @ui_disable.setter
    def ui_disable(self, value):
        self._set_prop("disable", value)

    @property
    def ui_readonly(self):
        return self._props.get("readonly")

    @ui_readonly.setter
    def ui_readonly(self, value):
        self._set_prop("readonly", value)

    @property
    def ui_tabindex(self):
        return self._props.get("tabindex")

    @ui_tabindex.setter
    def ui_tabindex(self, value):
        self._set_prop("tabindex", value)

    @property
    def ui_name(self):
        """Used to specify the name of the control; Useful if dealing with forms submitted directly to a URL"""
        return self._props.get("name")

    @ui_name.setter
    def ui_name(self, value):
        self._set_prop("name", value)

    @property
    def ui_slot_marker_label(self):
        """What should the menu display after filtering options and none are left to be displayed; Suggestion: <div>"""
        return self.ui_slots.get("marker-label", [])

    @ui_slot_marker_label.setter
    def ui_slot_marker_label(self, value):
        self._set_slot("marker-label", value)

    @property
    def ui_slot_marker_label_group(self):
        """What should the menu display after filtering options and none are left to be displayed; Suggestion: <div>"""
        return self.ui_slots.get("marker-label-group", [])

    @ui_slot_marker_label_group.setter
    def ui_slot_marker_label_group(self, value):
        self._set_slot("marker-label-group", value)

    def on_change(self, handler: Callable, arg: object = None):
        """
        Emitted on lazy model value change (after user slides then releases the thumb)

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("change", handler, arg)

    def on_pan(self, handler: Callable, arg: object = None):
        """
        Triggered when user starts panning on the component

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("pan", handler, arg)

    def on_update_model_value(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("update:model-value", handler, arg)

    def _get_js_methods(self):
        return []


class QRating(Component):
    """
    Quasar Component: `QRating <https://v2.quasar.dev/vue-components/rating>`__

    :param ui_model_value:
    :param ui_max: Number of icons to display
    :param ui_icon: Icon name following Quasar convention; make sure you have the icon library installed unless you are using 'img:' prefix; If an array is provided each rating value will use the corresponding icon in the array (0 based)
    :param ui_icon_selected: Icon name following Quasar convention to be used when selected (optional); make sure you have the icon library installed unless you are using 'img:' prefix; If an array is provided each rating value will use the corresponding icon in the array (0 based)
    :param ui_icon_half: Icon name following Quasar convention to be used when selected (optional); make sure you have the icon library installed unless you are using 'img:' prefix; If an array is provided each rating value will use the corresponding icon in the array (0 based)
    :param ui_icon_aria_label: Label to be set on aria-label for Icon; If an array is provided each rating value will use the corresponding aria-label in the array (0 based); If string value is provided the rating value will be appended; If not provided the name of the icon will be used
    :param ui_color: Color name for component from the Quasar Color Palette; v1.5.0+: If an array is provided each rating value will use the corresponding color in the array (0 based)
    :param ui_color_selected: Color name from the Quasar Palette for selected icons
    :param ui_color_half: Color name from the Quasar Palette for half selected icons
    :param ui_no_dimming: Does not lower opacity for unselected icons
    :param ui_no_reset: When used, disables default behavior of clicking/tapping on icon which represents current model value to reset model to 0
    :param ui_readonly:
    :param ui_disable:
    :param ui_size: Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)
    :param ui_name: Used to specify the name of the control; Useful if dealing with forms submitted directly to a URL
    """

    def __init__(
        self,
        *children,
        ui_model_value: float | None = None,
        ui_max: float | str | None = None,
        ui_icon: str | list | None = None,
        ui_icon_selected: str | list | None = None,
        ui_icon_half: str | list | None = None,
        ui_icon_aria_label: str | list | None = None,
        ui_color: str | list | None = None,
        ui_color_selected: str | list | None = None,
        ui_color_half: str | list | None = None,
        ui_no_dimming: bool | None = None,
        ui_no_reset: bool | None = None,
        ui_readonly: Any | None = None,
        ui_disable: Any | None = None,
        ui_size: str | None = None,
        ui_name: str | None = None,
        **kwargs,
    ):
        super().__init__("QRating", *children, **kwargs)
        self.on("update:model-value", self.__update_model_value)

        if ui_model_value is not None:
            self._props["model-value"] = ui_model_value
        if ui_max is not None:
            self._props["max"] = ui_max
        if ui_icon is not None:
            self._props["icon"] = ui_icon
        if ui_icon_selected is not None:
            self._props["icon-selected"] = ui_icon_selected
        if ui_icon_half is not None:
            self._props["icon-half"] = ui_icon_half
        if ui_icon_aria_label is not None:
            self._props["icon-aria-label"] = ui_icon_aria_label
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_color_selected is not None:
            self._props["color-selected"] = ui_color_selected
        if ui_color_half is not None:
            self._props["color-half"] = ui_color_half
        if ui_no_dimming is not None:
            self._props["no-dimming"] = ui_no_dimming
        if ui_no_reset is not None:
            self._props["no-reset"] = ui_no_reset
        if ui_readonly is not None:
            self._props["readonly"] = ui_readonly
        if ui_disable is not None:
            self._props["disable"] = ui_disable
        if ui_size is not None:
            self._props["size"] = ui_size
        if ui_name is not None:
            self._props["name"] = ui_name

    def __update_model_value(self, event: Event):
        self._set_prop("model-value", event.value)

    @property
    def ui_model_value(self):
        return self._props.get("model-value")

    @ui_model_value.setter
    def ui_model_value(self, value):
        self._set_prop("model-value", value)

    @property
    def ui_max(self):
        """Number of icons to display"""
        return self._props.get("max")

    @ui_max.setter
    def ui_max(self, value):
        self._set_prop("max", value)

    @property
    def ui_icon(self):
        """Icon name following Quasar convention; make sure you have the icon library installed unless you are using 'img:' prefix; If an array is provided each rating value will use the corresponding icon in the array (0 based)"""
        return self._props.get("icon")

    @ui_icon.setter
    def ui_icon(self, value):
        self._set_prop("icon", value)

    @property
    def ui_icon_selected(self):
        """Icon name following Quasar convention to be used when selected (optional); make sure you have the icon library installed unless you are using 'img:' prefix; If an array is provided each rating value will use the corresponding icon in the array (0 based)"""
        return self._props.get("icon-selected")

    @ui_icon_selected.setter
    def ui_icon_selected(self, value):
        self._set_prop("icon-selected", value)

    @property
    def ui_icon_half(self):
        """Icon name following Quasar convention to be used when selected (optional); make sure you have the icon library installed unless you are using 'img:' prefix; If an array is provided each rating value will use the corresponding icon in the array (0 based)"""
        return self._props.get("icon-half")

    @ui_icon_half.setter
    def ui_icon_half(self, value):
        self._set_prop("icon-half", value)

    @property
    def ui_icon_aria_label(self):
        """Label to be set on aria-label for Icon; If an array is provided each rating value will use the corresponding aria-label in the array (0 based); If string value is provided the rating value will be appended; If not provided the name of the icon will be used"""
        return self._props.get("icon-aria-label")

    @ui_icon_aria_label.setter
    def ui_icon_aria_label(self, value):
        self._set_prop("icon-aria-label", value)

    @property
    def ui_color(self):
        """Color name for component from the Quasar Color Palette; v1.5.0+: If an array is provided each rating value will use the corresponding color in the array (0 based)"""
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_color_selected(self):
        """Color name from the Quasar Palette for selected icons"""
        return self._props.get("color-selected")

    @ui_color_selected.setter
    def ui_color_selected(self, value):
        self._set_prop("color-selected", value)

    @property
    def ui_color_half(self):
        """Color name from the Quasar Palette for half selected icons"""
        return self._props.get("color-half")

    @ui_color_half.setter
    def ui_color_half(self, value):
        self._set_prop("color-half", value)

    @property
    def ui_no_dimming(self):
        """Does not lower opacity for unselected icons"""
        return self._props.get("no-dimming")

    @ui_no_dimming.setter
    def ui_no_dimming(self, value):
        self._set_prop("no-dimming", value)

    @property
    def ui_no_reset(self):
        """When used, disables default behavior of clicking/tapping on icon which represents current model value to reset model to 0"""
        return self._props.get("no-reset")

    @ui_no_reset.setter
    def ui_no_reset(self, value):
        self._set_prop("no-reset", value)

    @property
    def ui_readonly(self):
        return self._props.get("readonly")

    @ui_readonly.setter
    def ui_readonly(self, value):
        self._set_prop("readonly", value)

    @property
    def ui_disable(self):
        return self._props.get("disable")

    @ui_disable.setter
    def ui_disable(self, value):
        self._set_prop("disable", value)

    @property
    def ui_size(self):
        """Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)"""
        return self._props.get("size")

    @ui_size.setter
    def ui_size(self, value):
        self._set_prop("size", value)

    @property
    def ui_name(self):
        """Used to specify the name of the control; Useful if dealing with forms submitted directly to a URL"""
        return self._props.get("name")

    @ui_name.setter
    def ui_name(self, value):
        self._set_prop("name", value)

    def ui_slot_tip_name(self, name, value):
        """Slot to define the tooltip of icon at '[name]' where name is a 1-based index; Suggestion: QTooltip"""
        self._set_slot("tip-" + name, value)

    def on_update_model_value(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("update:model-value", handler, arg)

    def _get_js_methods(self):
        return []


class QResizeObserver(Component):
    """
    Quasar Component: `QResizeObserver <https://v2.quasar.dev/vue-components/resize-observer>`__

    :param ui_debounce: Debounce amount (in milliseconds)
    """

    def __init__(
        self, *children, ui_debounce: str | float | None = None, **kwargs
    ):
        super().__init__("QResizeObserver", *children, **kwargs)
        if ui_debounce is not None:
            self._props["debounce"] = ui_debounce

    @property
    def ui_debounce(self):
        """Debounce amount (in milliseconds)"""
        return self._props.get("debounce")

    @ui_debounce.setter
    def ui_debounce(self, value):
        self._set_prop("debounce", value)

    def on_resize(self, handler: Callable, arg: object = None):
        """
        Parent element has resized (width or height changed)

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("resize", handler, arg)

    def ui_trigger(self, ui_immediately=None):
        """Emit a 'resize' event"""
        kwargs = {}
        if ui_immediately is not None:
            kwargs["immediately"] = ui_immediately
        self._js_call_method("trigger", [kwargs])

    def _get_js_methods(self):
        return ["trigger"]


class QResponsive(Component):
    """
    Quasar Component: `QResponsive <https://v2.quasar.dev/vue-components/responsive>`__

    :param ui_ratio: Aspect ratio for the content; If value is a String, then avoid using a computational statement (like '16/9') and instead specify the String value of the result directly (eg. '1.7777')
    """

    def __init__(
        self, *children, ui_ratio: str | float | None = None, **kwargs
    ):
        super().__init__("QResponsive", *children, **kwargs)
        if ui_ratio is not None:
            self._props["ratio"] = ui_ratio

    @property
    def ui_ratio(self):
        """Aspect ratio for the content; If value is a String, then avoid using a computational statement (like '16/9') and instead specify the String value of the result directly (eg. '1.7777')"""
        return self._props.get("ratio")

    @ui_ratio.setter
    def ui_ratio(self, value):
        self._set_prop("ratio", value)

    def _get_js_methods(self):
        return []


class QScrollArea(Component):
    """
    Quasar Component: `QScrollArea <https://v2.quasar.dev/vue-components/scroll-area>`__

    :param ui_dark:
    :param ui_vertical_offset: Adds [top, bottom] offset to vertical thumb
    :param ui_horizontal_offset: Adds [left, right] offset to horizontal thumb
    :param ui_bar_style: Object with CSS properties and values for custom styling the scrollbars (both vertical and horizontal)
    :param ui_vertical_bar_style: Object with CSS properties and values for custom styling the vertical scrollbar; Is applied on top of 'bar-style' prop
    :param ui_horizontal_bar_style: Object with CSS properties and values for custom styling the horizontal scrollbar; Is applied on top of 'bar-style' prop
    :param ui_thumb_style: Object with CSS properties and values for custom styling the thumb of scrollbars (both vertical and horizontal)
    :param ui_vertical_thumb_style: Object with CSS properties and values for custom styling the thumb of the vertical scrollbar; Is applied on top of 'thumb-style' prop
    :param ui_horizontal_thumb_style: Object with CSS properties and values for custom styling the thumb of the horizontal scrollbar; Is applied on top of 'thumb-style' prop
    :param ui_content_style: Object with CSS properties and values for styling the container of QScrollArea
    :param ui_content_active_style: Object with CSS properties and values for styling the container of QScrollArea when scroll area becomes active (is mouse hovered)
    :param ui_visible: Manually control the visibility of the scrollbar; Overrides default mouse over/leave behavior
    :param ui_delay: When content changes, the scrollbar appears; this delay defines the amount of time (in milliseconds) before scrollbars disappear again (if component is not hovered)
    :param ui_tabindex:
    """

    def __init__(
        self,
        *children,
        ui_dark: Any | None = None,
        ui_vertical_offset: list | None = None,
        ui_horizontal_offset: list | None = None,
        ui_bar_style: str | list | dict | None = None,
        ui_vertical_bar_style: str | list | dict | None = None,
        ui_horizontal_bar_style: str | list | dict | None = None,
        ui_thumb_style: dict | None = None,
        ui_vertical_thumb_style: dict | None = None,
        ui_horizontal_thumb_style: dict | None = None,
        ui_content_style: str | list | dict | None = None,
        ui_content_active_style: str | list | dict | None = None,
        ui_visible: bool | None = None,
        ui_delay: float | str | None = None,
        ui_tabindex: Any | None = None,
        **kwargs,
    ):
        super().__init__("QScrollArea", *children, **kwargs)
        if ui_dark is not None:
            self._props["dark"] = ui_dark
        if ui_vertical_offset is not None:
            self._props["vertical-offset"] = ui_vertical_offset
        if ui_horizontal_offset is not None:
            self._props["horizontal-offset"] = ui_horizontal_offset
        if ui_bar_style is not None:
            self._props["bar-style"] = ui_bar_style
        if ui_vertical_bar_style is not None:
            self._props["vertical-bar-style"] = ui_vertical_bar_style
        if ui_horizontal_bar_style is not None:
            self._props["horizontal-bar-style"] = ui_horizontal_bar_style
        if ui_thumb_style is not None:
            self._props["thumb-style"] = ui_thumb_style
        if ui_vertical_thumb_style is not None:
            self._props["vertical-thumb-style"] = ui_vertical_thumb_style
        if ui_horizontal_thumb_style is not None:
            self._props["horizontal-thumb-style"] = ui_horizontal_thumb_style
        if ui_content_style is not None:
            self._props["content-style"] = ui_content_style
        if ui_content_active_style is not None:
            self._props["content-active-style"] = ui_content_active_style
        if ui_visible is not None:
            self._props["visible"] = ui_visible
        if ui_delay is not None:
            self._props["delay"] = ui_delay
        if ui_tabindex is not None:
            self._props["tabindex"] = ui_tabindex

    @property
    def ui_dark(self):
        return self._props.get("dark")

    @ui_dark.setter
    def ui_dark(self, value):
        self._set_prop("dark", value)

    @property
    def ui_vertical_offset(self):
        """Adds [top, bottom] offset to vertical thumb"""
        return self._props.get("vertical-offset")

    @ui_vertical_offset.setter
    def ui_vertical_offset(self, value):
        self._set_prop("vertical-offset", value)

    @property
    def ui_horizontal_offset(self):
        """Adds [left, right] offset to horizontal thumb"""
        return self._props.get("horizontal-offset")

    @ui_horizontal_offset.setter
    def ui_horizontal_offset(self, value):
        self._set_prop("horizontal-offset", value)

    @property
    def ui_bar_style(self):
        """Object with CSS properties and values for custom styling the scrollbars (both vertical and horizontal)"""
        return self._props.get("bar-style")

    @ui_bar_style.setter
    def ui_bar_style(self, value):
        self._set_prop("bar-style", value)

    @property
    def ui_vertical_bar_style(self):
        """Object with CSS properties and values for custom styling the vertical scrollbar; Is applied on top of 'bar-style' prop"""
        return self._props.get("vertical-bar-style")

    @ui_vertical_bar_style.setter
    def ui_vertical_bar_style(self, value):
        self._set_prop("vertical-bar-style", value)

    @property
    def ui_horizontal_bar_style(self):
        """Object with CSS properties and values for custom styling the horizontal scrollbar; Is applied on top of 'bar-style' prop"""
        return self._props.get("horizontal-bar-style")

    @ui_horizontal_bar_style.setter
    def ui_horizontal_bar_style(self, value):
        self._set_prop("horizontal-bar-style", value)

    @property
    def ui_thumb_style(self):
        """Object with CSS properties and values for custom styling the thumb of scrollbars (both vertical and horizontal)"""
        return self._props.get("thumb-style")

    @ui_thumb_style.setter
    def ui_thumb_style(self, value):
        self._set_prop("thumb-style", value)

    @property
    def ui_vertical_thumb_style(self):
        """Object with CSS properties and values for custom styling the thumb of the vertical scrollbar; Is applied on top of 'thumb-style' prop"""
        return self._props.get("vertical-thumb-style")

    @ui_vertical_thumb_style.setter
    def ui_vertical_thumb_style(self, value):
        self._set_prop("vertical-thumb-style", value)

    @property
    def ui_horizontal_thumb_style(self):
        """Object with CSS properties and values for custom styling the thumb of the horizontal scrollbar; Is applied on top of 'thumb-style' prop"""
        return self._props.get("horizontal-thumb-style")

    @ui_horizontal_thumb_style.setter
    def ui_horizontal_thumb_style(self, value):
        self._set_prop("horizontal-thumb-style", value)

    @property
    def ui_content_style(self):
        """Object with CSS properties and values for styling the container of QScrollArea"""
        return self._props.get("content-style")

    @ui_content_style.setter
    def ui_content_style(self, value):
        self._set_prop("content-style", value)

    @property
    def ui_content_active_style(self):
        """Object with CSS properties and values for styling the container of QScrollArea when scroll area becomes active (is mouse hovered)"""
        return self._props.get("content-active-style")

    @ui_content_active_style.setter
    def ui_content_active_style(self, value):
        self._set_prop("content-active-style", value)

    @property
    def ui_visible(self):
        """Manually control the visibility of the scrollbar; Overrides default mouse over/leave behavior"""
        return self._props.get("visible")

    @ui_visible.setter
    def ui_visible(self, value):
        self._set_prop("visible", value)

    @property
    def ui_delay(self):
        """When content changes, the scrollbar appears; this delay defines the amount of time (in milliseconds) before scrollbars disappear again (if component is not hovered)"""
        return self._props.get("delay")

    @ui_delay.setter
    def ui_delay(self, value):
        self._set_prop("delay", value)

    @property
    def ui_tabindex(self):
        return self._props.get("tabindex")

    @ui_tabindex.setter
    def ui_tabindex(self, value):
        self._set_prop("tabindex", value)

    def on_scroll(self, handler: Callable, arg: object = None):
        """
        Emitted when scroll information changes (and listener is configured)

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("scroll", handler, arg)

    def ui_getScroll(self):
        """Get the current scroll information"""
        self._js_call_method("getScroll")

    def ui_getScrollPercentage(self):
        """Get current scroll position in percentage (0.0 <= x <= 1.0)"""
        self._js_call_method("getScrollPercentage")

    def ui_getScrollPosition(self):
        """Get current scroll position"""
        self._js_call_method("getScrollPosition")

    def ui_getScrollTarget(self):
        """Get the scrolling DOM element target"""
        self._js_call_method("getScrollTarget")

    def ui_setScrollPercentage(self, ui_axis, ui_offset, ui_duration=None):
        """Set scroll position to a percentage (0.0 <= x <= 1.0) of the total scrolling size; If a duration (in milliseconds) is specified then the scroll is animated"""
        kwargs = {}
        if ui_axis is not None:
            kwargs["axis"] = ui_axis
        if ui_offset is not None:
            kwargs["offset"] = ui_offset
        if ui_duration is not None:
            kwargs["duration"] = ui_duration
        self._js_call_method("setScrollPercentage", [kwargs])

    def ui_setScrollPosition(self, ui_axis, ui_offset, ui_duration=None):
        """Set scroll position to an offset; If a duration (in milliseconds) is specified then the scroll is animated"""
        kwargs = {}
        if ui_axis is not None:
            kwargs["axis"] = ui_axis
        if ui_offset is not None:
            kwargs["offset"] = ui_offset
        if ui_duration is not None:
            kwargs["duration"] = ui_duration
        self._js_call_method("setScrollPosition", [kwargs])

    def _get_js_methods(self):
        return [
            "getScroll",
            "getScrollPercentage",
            "getScrollPosition",
            "getScrollTarget",
            "setScrollPercentage",
            "setScrollPosition",
        ]


class QScrollObserver(Component):
    """
    Quasar Component: `QScrollObserver <https://v2.quasar.dev/vue-components/scroll-observer>`__

    :param ui_debounce: Debounce amount (in milliseconds)
    :param ui_axis: Axis on which to detect changes
    :param ui_scroll_target:
    """

    def __init__(
        self,
        *children,
        ui_debounce: str | float | None = None,
        ui_axis: str | None = None,
        ui_scroll_target: Any | None = None,
        **kwargs,
    ):
        super().__init__("QScrollObserver", *children, **kwargs)
        if ui_debounce is not None:
            self._props["debounce"] = ui_debounce
        if ui_axis is not None:
            self._props["axis"] = ui_axis
        if ui_scroll_target is not None:
            self._props["scroll-target"] = ui_scroll_target

    @property
    def ui_debounce(self):
        """Debounce amount (in milliseconds)"""
        return self._props.get("debounce")

    @ui_debounce.setter
    def ui_debounce(self, value):
        self._set_prop("debounce", value)

    @property
    def ui_axis(self):
        """Axis on which to detect changes"""
        return self._props.get("axis")

    @ui_axis.setter
    def ui_axis(self, value):
        self._set_prop("axis", value)

    @property
    def ui_scroll_target(self):
        return self._props.get("scroll-target")

    @ui_scroll_target.setter
    def ui_scroll_target(self, value):
        self._set_prop("scroll-target", value)

    def on_scroll(self, handler: Callable, arg: object = None):
        """
        Emitted when scroll position changes

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("scroll", handler, arg)

    def ui_getPosition(self):
        """Get current scroll details under the form of an Object: { position, direction, directionChanged, inflectionPoint }"""
        self._js_call_method("getPosition")

    def ui_trigger(self, ui_immediately=None):
        """Emit a 'scroll' event"""
        kwargs = {}
        if ui_immediately is not None:
            kwargs["immediately"] = ui_immediately
        self._js_call_method("trigger", [kwargs])

    def _get_js_methods(self):
        return ["getPosition", "trigger"]


class QSelect(Component):
    """
    Quasar Component: `QSelect <https://v2.quasar.dev/vue-components/select>`__

    :param ui_model_value: Model of the component; Either use this property (along with a listener for 'update:model-value' event) OR use v-model directive
    :param ui_multiple: Allow multiple selection; Model must be Array
    :param ui_display_value: Override default selection string, if not using 'selected' slot/scoped slot and if not using 'use-chips' prop
    :param ui_display_value_html: Force render the selected option(s) as HTML; This can lead to XSS attacks so make sure that you sanitize the content; Does NOT apply when using 'selected' or 'selected-item' slots!
    :param ui_options: Array of objects with available options that the user can select from. For best performance freeze the list of options. Canonical form of each object is with 'label' (String), 'value' (Any) and optional 'disable' (Boolean) props (can be customized with options-value/option-label/option-disable props).
    :param ui_option_value: Property of option which holds the 'value'; If using a function then for best performance, reference it from your scope and do not define it inline
    :param ui_option_label: Property of option which holds the 'label'; If using a function then for best performance, reference it from your scope and do not define it inline
    :param ui_option_disable: Property of option which tells it's disabled; The value of the property must be a Boolean; If using a function then for best performance, reference it from your scope and do not define it inline
    :param ui_hide_selected: Hides selection; Use the underlying input tag to hold the label (instead of showing it to the right of the input) of the selected option; Only works for non 'multiple' Selects
    :param ui_hide_dropdown_icon: Hides dropdown icon
    :param ui_dropdown_icon:
    :param ui_max_values: Allow a maximum number of selections that the user can do
    :param ui_options_dense: Dense mode for options list; occupies less space
    :param ui_options_dark: Options menu will be colored with a dark color
    :param ui_options_selected_class: CSS class name for options that are active/selected; Set it to an empty string to stop applying the default (which is text-\\* where \\* is the 'color' prop value)
    :param ui_options_html: Force render the options as HTML; This can lead to XSS attacks so make sure that you sanitize the content; Does NOT apply when using 'option' slot!
    :param ui_options_cover: Expanded menu will cover the component (will not work along with 'use-input' prop for obvious reasons)
    :param ui_menu_shrink: Allow the options list to be narrower than the field (only in menu mode)
    :param ui_menu_anchor: Two values setting the starting position or anchor point of the options list relative to the field (only in menu mode)
    :param ui_menu_self: Two values setting the options list's own position relative to its target (only in menu mode)
    :param ui_menu_offset: An array of two numbers to offset the options list horizontally and vertically in pixels (only in menu mode)
    :param ui_popup_content_class: Class definitions to be attributed to the popup content
    :param ui_popup_content_style: Style definitions to be attributed to the popup content
    :param ui_popup_no_route_dismiss: Changing route app won't dismiss the popup (menu or dialog)
    :param ui_use_chips: Use QChip to show what is currently selected
    :param ui_use_input: Use an input tag where users can type
    :param ui_maxlength: Specify a max length for the inner input tag (if 'use-input' is enabled)
    :param ui_fill_input: Fills the input with current value; Useful along with 'hide-selected'; Does NOT works along with 'multiple' selection
    :param ui_new_value_mode: Enables creation of new values and defines behavior when a new value is added: 'add' means it adds the value (even if possible duplicate), 'add-unique' adds only unique values, and 'toggle' adds or removes the value (based on if it exists or not already); When using this prop then listening for @new-value becomes optional (only to override the behavior defined by 'new-value-mode')
    :param ui_map_options: Try to map labels of model from 'options' Array; has a small performance penalty; If you are using emit-value you will probably need to use map-options to display the label text in the select field rather than the value;  Refer to the 'Affecting model' section above
    :param ui_disable_tab_selection: Prevents the tab key from confirming the currently hovered option
    :param ui_emit_value: Update model with the value of the selected option instead of the whole option
    :param ui_input_debounce: Debounce the input model update with an amount of milliseconds (also affects the 'filter' event, if used)
    :param ui_input_class: Class definitions to be attributed to the underlying input tag
    :param ui_input_style: Style definitions to be attributed to the underlying input tag
    :param ui_tabindex:
    :param ui_autocomplete: Autocomplete attribute for field
    :param ui_transition_show: Transition when showing the menu/dialog; One of Quasar's embedded transitions
    :param ui_transition_hide: Transition when hiding the menu/dialog; One of Quasar's embedded transitions
    :param ui_transition_duration: Transition duration when hiding the menu/dialog (in milliseconds, without unit)
    :param ui_behavior: Overrides the default dynamic mode of showing as menu on desktop and dialog on mobiles
    :param ui_name: Used to specify the name of the control; Useful if dealing with forms submitted directly to a URL
    :param ui_virtual_scroll_item_size: Default size in pixels (height if vertical, width if horizontal) of an item; This value is used for rendering the initial list; Try to use a value close to the minimum size of an item
    :param ui_label: A text label that will “float” up above the input field, once the field gets focus
    :param ui_stack_label: Label will be always shown above the field regardless of field content (if any)
    :param ui_hint: Helper (hint) text which gets placed below your wrapped form component
    :param ui_hide_hint: Hide the helper (hint) text when field doesn't have focus
    :param ui_prefix: Prefix
    :param ui_suffix: Suffix
    :param ui_label_color: Color name for the label from the Quasar Color Palette; Overrides the 'color' prop; The difference from 'color' prop is that the label will always have this color, even when field is not focused
    :param ui_color:
    :param ui_bg_color:
    :param ui_dark:
    :param ui_loading: Signals the user a process is in progress by displaying a spinner; Spinner can be customized by using the 'loading' slot.
    :param ui_clearable: Appends clearable icon when a value (not undefined or null) is set; When clicked, model becomes null
    :param ui_clear_icon: Custom icon to use for the clear button when using along with 'clearable' prop
    :param ui_filled: Use 'filled' design for the field
    :param ui_outlined: Use 'outlined' design for the field
    :param ui_borderless: Use 'borderless' design for the field
    :param ui_standout: Use 'standout' design for the field; Specifies classes to be applied when focused (overriding default ones)
    :param ui_label_slot: Enables label slot; You need to set it to force use of the 'label' slot if the 'label' prop is not set
    :param ui_bottom_slots: Enables bottom slots ('error', 'hint', 'counter')
    :param ui_hide_bottom_space: Do not reserve space for hint/error/counter anymore when these are not used; As a result, it also disables the animation for those; It also allows the hint/error area to stretch vertically based on its content
    :param ui_counter: Show an automatic counter on bottom right
    :param ui_rounded:
    :param ui_square: Remove border-radius so borders are squared; Overrides 'rounded' prop
    :param ui_dense:
    :param ui_item_aligned: Match inner content alignment to that of QItem
    :param ui_disable:
    :param ui_readonly:
    :param ui_autofocus: Focus field on initial component render
    :param ui_for: Used to specify the 'id' of the control and also the 'for' attribute of the label that wraps it; If no 'name' prop is specified, then it is used for this attribute as well
    :param ui_error: Does field have validation errors?
    :param ui_error_message: Validation error message (gets displayed only if 'error' is set to 'true')
    :param ui_no_error_icon: Hide error icon when there is an error
    :param ui_rules: Array of Functions/Strings; If String, then it must be a name of one of the embedded validation rules
    :param ui_reactive_rules: By default a change in the rules does not trigger a new validation until the model changes; If set to true then a change in the rules will trigger a validation; Has a performance penalty, so use it only when you really need it
    :param ui_lazy_rules: If set to boolean true then it checks validation status against the 'rules' only after field loses focus for first time; If set to 'ondemand' then it will trigger only when component's validate() method is manually called or when the wrapper QForm submits itself
    :param ui_virtual_scroll_horizontal: Make virtual list work in horizontal mode
    :param ui_virtual_scroll_slice_size: Minimum number of items to render in the virtual list
    :param ui_virtual_scroll_slice_ratio_before: Ratio of number of items in visible zone to render before it
    :param ui_virtual_scroll_slice_ratio_after: Ratio of number of items in visible zone to render after it
    :param ui_virtual_scroll_sticky_size_start: Size in pixels (height if vertical, width if horizontal) of the sticky part (if using one) at the start of the list; A correct value will improve scroll precision
    :param ui_virtual_scroll_sticky_size_end: Size in pixels (height if vertical, width if horizontal) of the sticky part (if using one) at the end of the list; A correct value will improve scroll precision
    :param ui_table_colspan: The number of columns in the table (you need this if you use table-layout: fixed)
    """

    def __init__(
        self,
        *children,
        ui_model_value: Any | None = None,
        ui_multiple: bool | None = None,
        ui_display_value: float | str | None = None,
        ui_display_value_html: Any | None = None,
        ui_options: list | None = None,
        ui_option_value: Callable | str | None = None,
        ui_option_label: Callable | str | None = None,
        ui_option_disable: Callable | str | None = None,
        ui_hide_selected: bool | None = None,
        ui_hide_dropdown_icon: bool | None = None,
        ui_dropdown_icon: Any | None = None,
        ui_max_values: float | str | None = None,
        ui_options_dense: Any | None = None,
        ui_options_dark: bool | None = None,
        ui_options_selected_class: str | None = None,
        ui_options_html: Any | None = None,
        ui_options_cover: bool | None = None,
        ui_menu_shrink: bool | None = None,
        ui_menu_anchor: str | None = None,
        ui_menu_self: str | None = None,
        ui_menu_offset: list | None = None,
        ui_popup_content_class: str | None = None,
        ui_popup_content_style: str | list | dict | None = None,
        ui_popup_no_route_dismiss: bool | None = None,
        ui_use_chips: bool | None = None,
        ui_use_input: bool | None = None,
        ui_maxlength: str | float | None = None,
        ui_fill_input: bool | None = None,
        ui_new_value_mode: str | None = None,
        ui_map_options: bool | None = None,
        ui_disable_tab_selection: bool | None = None,
        ui_emit_value: bool | None = None,
        ui_input_debounce: float | str | None = None,
        ui_input_class: str | list | dict | None = None,
        ui_input_style: str | list | dict | None = None,
        ui_tabindex: Any | None = None,
        ui_autocomplete: str | None = None,
        ui_transition_show: Any | None = None,
        ui_transition_hide: Any | None = None,
        ui_transition_duration: str | float | None = None,
        ui_behavior: str | None = None,
        ui_name: str | None = None,
        ui_virtual_scroll_item_size: float | str | None = None,
        ui_label: str | None = None,
        ui_stack_label: bool | None = None,
        ui_hint: str | None = None,
        ui_hide_hint: bool | None = None,
        ui_prefix: str | None = None,
        ui_suffix: str | None = None,
        ui_label_color: Any | None = None,
        ui_color: Any | None = None,
        ui_bg_color: Any | None = None,
        ui_dark: Any | None = None,
        ui_loading: bool | None = None,
        ui_clearable: bool | None = None,
        ui_clear_icon: str | None = None,
        ui_filled: bool | None = None,
        ui_outlined: bool | None = None,
        ui_borderless: bool | None = None,
        ui_standout: bool | str | None = None,
        ui_label_slot: bool | None = None,
        ui_bottom_slots: bool | None = None,
        ui_hide_bottom_space: bool | None = None,
        ui_counter: bool | None = None,
        ui_rounded: Any | None = None,
        ui_square: bool | None = None,
        ui_dense: Any | None = None,
        ui_item_aligned: bool | None = None,
        ui_disable: Any | None = None,
        ui_readonly: Any | None = None,
        ui_autofocus: bool | None = None,
        ui_for: str | None = None,
        ui_error: bool | None = None,
        ui_error_message: str | None = None,
        ui_no_error_icon: bool | None = None,
        ui_rules: list | None = None,
        ui_reactive_rules: bool | None = None,
        ui_lazy_rules: bool | str | None = None,
        ui_virtual_scroll_horizontal: bool | None = None,
        ui_virtual_scroll_slice_size: float | str | None = None,
        ui_virtual_scroll_slice_ratio_before: float | str | None = None,
        ui_virtual_scroll_slice_ratio_after: float | str | None = None,
        ui_virtual_scroll_sticky_size_start: float | str | None = None,
        ui_virtual_scroll_sticky_size_end: float | str | None = None,
        ui_table_colspan: float | str | None = None,
        **kwargs,
    ):
        super().__init__("QSelect", *children, **kwargs)
        self.on("update:model-value", self.__update_model_value)

        if ui_model_value is not None:
            self._props["model-value"] = ui_model_value
        if ui_multiple is not None:
            self._props["multiple"] = ui_multiple
        if ui_display_value is not None:
            self._props["display-value"] = ui_display_value
        if ui_display_value_html is not None:
            self._props["display-value-html"] = ui_display_value_html
        if ui_options is not None:
            self._props["options"] = ui_options
        if ui_option_value is not None:
            self._props["option-value"] = ui_option_value
        if ui_option_label is not None:
            self._props["option-label"] = ui_option_label
        if ui_option_disable is not None:
            self._props["option-disable"] = ui_option_disable
        if ui_hide_selected is not None:
            self._props["hide-selected"] = ui_hide_selected
        if ui_hide_dropdown_icon is not None:
            self._props["hide-dropdown-icon"] = ui_hide_dropdown_icon
        if ui_dropdown_icon is not None:
            self._props["dropdown-icon"] = ui_dropdown_icon
        if ui_max_values is not None:
            self._props["max-values"] = ui_max_values
        if ui_options_dense is not None:
            self._props["options-dense"] = ui_options_dense
        if ui_options_dark is not None:
            self._props["options-dark"] = ui_options_dark
        if ui_options_selected_class is not None:
            self._props["options-selected-class"] = ui_options_selected_class
        if ui_options_html is not None:
            self._props["options-html"] = ui_options_html
        if ui_options_cover is not None:
            self._props["options-cover"] = ui_options_cover
        if ui_menu_shrink is not None:
            self._props["menu-shrink"] = ui_menu_shrink
        if ui_menu_anchor is not None:
            self._props["menu-anchor"] = ui_menu_anchor
        if ui_menu_self is not None:
            self._props["menu-self"] = ui_menu_self
        if ui_menu_offset is not None:
            self._props["menu-offset"] = ui_menu_offset
        if ui_popup_content_class is not None:
            self._props["popup-content-class"] = ui_popup_content_class
        if ui_popup_content_style is not None:
            self._props["popup-content-style"] = ui_popup_content_style
        if ui_popup_no_route_dismiss is not None:
            self._props["popup-no-route-dismiss"] = ui_popup_no_route_dismiss
        if ui_use_chips is not None:
            self._props["use-chips"] = ui_use_chips
        if ui_use_input is not None:
            self._props["use-input"] = ui_use_input
        if ui_maxlength is not None:
            self._props["maxlength"] = ui_maxlength
        if ui_fill_input is not None:
            self._props["fill-input"] = ui_fill_input
        if ui_new_value_mode is not None:
            self._props["new-value-mode"] = ui_new_value_mode
        if ui_map_options is not None:
            self._props["map-options"] = ui_map_options
        if ui_disable_tab_selection is not None:
            self._props["disable-tab-selection"] = ui_disable_tab_selection
        if ui_emit_value is not None:
            self._props["emit-value"] = ui_emit_value
        if ui_input_debounce is not None:
            self._props["input-debounce"] = ui_input_debounce
        if ui_input_class is not None:
            self._props["input-class"] = ui_input_class
        if ui_input_style is not None:
            self._props["input-style"] = ui_input_style
        if ui_tabindex is not None:
            self._props["tabindex"] = ui_tabindex
        if ui_autocomplete is not None:
            self._props["autocomplete"] = ui_autocomplete
        if ui_transition_show is not None:
            self._props["transition-show"] = ui_transition_show
        if ui_transition_hide is not None:
            self._props["transition-hide"] = ui_transition_hide
        if ui_transition_duration is not None:
            self._props["transition-duration"] = ui_transition_duration
        if ui_behavior is not None:
            self._props["behavior"] = ui_behavior
        if ui_name is not None:
            self._props["name"] = ui_name
        if ui_virtual_scroll_item_size is not None:
            self._props["virtual-scroll-item-size"] = (
                ui_virtual_scroll_item_size
            )
        if ui_label is not None:
            self._props["label"] = ui_label
        if ui_stack_label is not None:
            self._props["stack-label"] = ui_stack_label
        if ui_hint is not None:
            self._props["hint"] = ui_hint
        if ui_hide_hint is not None:
            self._props["hide-hint"] = ui_hide_hint
        if ui_prefix is not None:
            self._props["prefix"] = ui_prefix
        if ui_suffix is not None:
            self._props["suffix"] = ui_suffix
        if ui_label_color is not None:
            self._props["label-color"] = ui_label_color
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_bg_color is not None:
            self._props["bg-color"] = ui_bg_color
        if ui_dark is not None:
            self._props["dark"] = ui_dark
        if ui_loading is not None:
            self._props["loading"] = ui_loading
        if ui_clearable is not None:
            self._props["clearable"] = ui_clearable
        if ui_clear_icon is not None:
            self._props["clear-icon"] = ui_clear_icon
        if ui_filled is not None:
            self._props["filled"] = ui_filled
        if ui_outlined is not None:
            self._props["outlined"] = ui_outlined
        if ui_borderless is not None:
            self._props["borderless"] = ui_borderless
        if ui_standout is not None:
            self._props["standout"] = ui_standout
        if ui_label_slot is not None:
            self._props["label-slot"] = ui_label_slot
        if ui_bottom_slots is not None:
            self._props["bottom-slots"] = ui_bottom_slots
        if ui_hide_bottom_space is not None:
            self._props["hide-bottom-space"] = ui_hide_bottom_space
        if ui_counter is not None:
            self._props["counter"] = ui_counter
        if ui_rounded is not None:
            self._props["rounded"] = ui_rounded
        if ui_square is not None:
            self._props["square"] = ui_square
        if ui_dense is not None:
            self._props["dense"] = ui_dense
        if ui_item_aligned is not None:
            self._props["item-aligned"] = ui_item_aligned
        if ui_disable is not None:
            self._props["disable"] = ui_disable
        if ui_readonly is not None:
            self._props["readonly"] = ui_readonly
        if ui_autofocus is not None:
            self._props["autofocus"] = ui_autofocus
        if ui_for is not None:
            self._props["for"] = ui_for
        if ui_error is not None:
            self._props["error"] = ui_error
        if ui_error_message is not None:
            self._props["error-message"] = ui_error_message
        if ui_no_error_icon is not None:
            self._props["no-error-icon"] = ui_no_error_icon

        self._rules = [] if ui_rules is None else ui_rules
        self._rules_registered = False
        if self._rules:
            self._rules_registered = True
            self.on_update_model_value(self._validate_rules)

        if ui_reactive_rules is not None:
            self._props["reactive-rules"] = ui_reactive_rules
        if ui_lazy_rules is not None:
            self._props["lazy-rules"] = ui_lazy_rules
        if ui_virtual_scroll_horizontal is not None:
            self._props["virtual-scroll-horizontal"] = (
                ui_virtual_scroll_horizontal
            )
        if ui_virtual_scroll_slice_size is not None:
            self._props["virtual-scroll-slice-size"] = (
                ui_virtual_scroll_slice_size
            )
        if ui_virtual_scroll_slice_ratio_before is not None:
            self._props["virtual-scroll-slice-ratio-before"] = (
                ui_virtual_scroll_slice_ratio_before
            )
        if ui_virtual_scroll_slice_ratio_after is not None:
            self._props["virtual-scroll-slice-ratio-after"] = (
                ui_virtual_scroll_slice_ratio_after
            )
        if ui_virtual_scroll_sticky_size_start is not None:
            self._props["virtual-scroll-sticky-size-start"] = (
                ui_virtual_scroll_sticky_size_start
            )
        if ui_virtual_scroll_sticky_size_end is not None:
            self._props["virtual-scroll-sticky-size-end"] = (
                ui_virtual_scroll_sticky_size_end
            )
        if ui_table_colspan is not None:
            self._props["table-colspan"] = ui_table_colspan

    def __update_model_value(self, event: Event):
        self._set_prop("model-value", event.value)

    @property
    def ui_model_value(self):
        """Model of the component; Either use this property (along with a listener for 'update:model-value' event) OR use v-model directive"""
        return self._props.get("model-value")

    @ui_model_value.setter
    def ui_model_value(self, value):
        self._set_prop("model-value", value)

    @property
    def ui_multiple(self):
        """Allow multiple selection; Model must be Array"""
        return self._props.get("multiple")

    @ui_multiple.setter
    def ui_multiple(self, value):
        self._set_prop("multiple", value)

    @property
    def ui_display_value(self):
        """Override default selection string, if not using 'selected' slot/scoped slot and if not using 'use-chips' prop"""
        return self._props.get("display-value")

    @ui_display_value.setter
    def ui_display_value(self, value):
        self._set_prop("display-value", value)

    @property
    def ui_display_value_html(self):
        """Force render the selected option(s) as HTML; This can lead to XSS attacks so make sure that you sanitize the content; Does NOT apply when using 'selected' or 'selected-item' slots!"""
        return self._props.get("display-value-html")

    @ui_display_value_html.setter
    def ui_display_value_html(self, value):
        self._set_prop("display-value-html", value)

    @property
    def ui_options(self):
        """Array of objects with available options that the user can select from. For best performance freeze the list of options. Canonical form of each object is with 'label' (String), 'value' (Any) and optional 'disable' (Boolean) props (can be customized with options-value/option-label/option-disable props)."""
        return self._props.get("options")

    @ui_options.setter
    def ui_options(self, value):
        self._set_prop("options", value)

    @property
    def ui_option_value(self):
        """Property of option which holds the 'value'; If using a function then for best performance, reference it from your scope and do not define it inline"""
        return self._props.get("option-value")

    @ui_option_value.setter
    def ui_option_value(self, value):
        self._set_prop("option-value", value)

    @property
    def ui_option_label(self):
        """Property of option which holds the 'label'; If using a function then for best performance, reference it from your scope and do not define it inline"""
        return self._props.get("option-label")

    @ui_option_label.setter
    def ui_option_label(self, value):
        self._set_prop("option-label", value)

    @property
    def ui_option_disable(self):
        """Property of option which tells it's disabled; The value of the property must be a Boolean; If using a function then for best performance, reference it from your scope and do not define it inline"""
        return self._props.get("option-disable")

    @ui_option_disable.setter
    def ui_option_disable(self, value):
        self._set_prop("option-disable", value)

    @property
    def ui_hide_selected(self):
        """Hides selection; Use the underlying input tag to hold the label (instead of showing it to the right of the input) of the selected option; Only works for non 'multiple' Selects"""
        return self._props.get("hide-selected")

    @ui_hide_selected.setter
    def ui_hide_selected(self, value):
        self._set_prop("hide-selected", value)

    @property
    def ui_hide_dropdown_icon(self):
        """Hides dropdown icon"""
        return self._props.get("hide-dropdown-icon")

    @ui_hide_dropdown_icon.setter
    def ui_hide_dropdown_icon(self, value):
        self._set_prop("hide-dropdown-icon", value)

    @property
    def ui_dropdown_icon(self):
        return self._props.get("dropdown-icon")

    @ui_dropdown_icon.setter
    def ui_dropdown_icon(self, value):
        self._set_prop("dropdown-icon", value)

    @property
    def ui_max_values(self):
        """Allow a maximum number of selections that the user can do"""
        return self._props.get("max-values")

    @ui_max_values.setter
    def ui_max_values(self, value):
        self._set_prop("max-values", value)

    @property
    def ui_options_dense(self):
        """Dense mode for options list; occupies less space"""
        return self._props.get("options-dense")

    @ui_options_dense.setter
    def ui_options_dense(self, value):
        self._set_prop("options-dense", value)

    @property
    def ui_options_dark(self):
        """Options menu will be colored with a dark color"""
        return self._props.get("options-dark")

    @ui_options_dark.setter
    def ui_options_dark(self, value):
        self._set_prop("options-dark", value)

    @property
    def ui_options_selected_class(self):
        """CSS class name for options that are active/selected; Set it to an empty string to stop applying the default (which is text-\\* where \\* is the 'color' prop value)"""
        return self._props.get("options-selected-class")

    @ui_options_selected_class.setter
    def ui_options_selected_class(self, value):
        self._set_prop("options-selected-class", value)

    @property
    def ui_options_html(self):
        """Force render the options as HTML; This can lead to XSS attacks so make sure that you sanitize the content; Does NOT apply when using 'option' slot!"""
        return self._props.get("options-html")

    @ui_options_html.setter
    def ui_options_html(self, value):
        self._set_prop("options-html", value)

    @property
    def ui_options_cover(self):
        """Expanded menu will cover the component (will not work along with 'use-input' prop for obvious reasons)"""
        return self._props.get("options-cover")

    @ui_options_cover.setter
    def ui_options_cover(self, value):
        self._set_prop("options-cover", value)

    @property
    def ui_menu_shrink(self):
        """Allow the options list to be narrower than the field (only in menu mode)"""
        return self._props.get("menu-shrink")

    @ui_menu_shrink.setter
    def ui_menu_shrink(self, value):
        self._set_prop("menu-shrink", value)

    @property
    def ui_menu_anchor(self):
        """Two values setting the starting position or anchor point of the options list relative to the field (only in menu mode)"""
        return self._props.get("menu-anchor")

    @ui_menu_anchor.setter
    def ui_menu_anchor(self, value):
        self._set_prop("menu-anchor", value)

    @property
    def ui_menu_self(self):
        """Two values setting the options list's own position relative to its target (only in menu mode)"""
        return self._props.get("menu-self")

    @ui_menu_self.setter
    def ui_menu_self(self, value):
        self._set_prop("menu-self", value)

    @property
    def ui_menu_offset(self):
        """An array of two numbers to offset the options list horizontally and vertically in pixels (only in menu mode)"""
        return self._props.get("menu-offset")

    @ui_menu_offset.setter
    def ui_menu_offset(self, value):
        self._set_prop("menu-offset", value)

    @property
    def ui_popup_content_class(self):
        """Class definitions to be attributed to the popup content"""
        return self._props.get("popup-content-class")

    @ui_popup_content_class.setter
    def ui_popup_content_class(self, value):
        self._set_prop("popup-content-class", value)

    @property
    def ui_popup_content_style(self):
        """Style definitions to be attributed to the popup content"""
        return self._props.get("popup-content-style")

    @ui_popup_content_style.setter
    def ui_popup_content_style(self, value):
        self._set_prop("popup-content-style", value)

    @property
    def ui_popup_no_route_dismiss(self):
        """Changing route app won't dismiss the popup (menu or dialog)"""
        return self._props.get("popup-no-route-dismiss")

    @ui_popup_no_route_dismiss.setter
    def ui_popup_no_route_dismiss(self, value):
        self._set_prop("popup-no-route-dismiss", value)

    @property
    def ui_use_chips(self):
        """Use QChip to show what is currently selected"""
        return self._props.get("use-chips")

    @ui_use_chips.setter
    def ui_use_chips(self, value):
        self._set_prop("use-chips", value)

    @property
    def ui_use_input(self):
        """Use an input tag where users can type"""
        return self._props.get("use-input")

    @ui_use_input.setter
    def ui_use_input(self, value):
        self._set_prop("use-input", value)

    @property
    def ui_maxlength(self):
        """Specify a max length for the inner input tag (if 'use-input' is enabled)"""
        return self._props.get("maxlength")

    @ui_maxlength.setter
    def ui_maxlength(self, value):
        self._set_prop("maxlength", value)

    @property
    def ui_fill_input(self):
        """Fills the input with current value; Useful along with 'hide-selected'; Does NOT works along with 'multiple' selection"""
        return self._props.get("fill-input")

    @ui_fill_input.setter
    def ui_fill_input(self, value):
        self._set_prop("fill-input", value)

    @property
    def ui_new_value_mode(self):
        """Enables creation of new values and defines behavior when a new value is added: 'add' means it adds the value (even if possible duplicate), 'add-unique' adds only unique values, and 'toggle' adds or removes the value (based on if it exists or not already); When using this prop then listening for @new-value becomes optional (only to override the behavior defined by 'new-value-mode')"""
        return self._props.get("new-value-mode")

    @ui_new_value_mode.setter
    def ui_new_value_mode(self, value):
        self._set_prop("new-value-mode", value)

    @property
    def ui_map_options(self):
        """Try to map labels of model from 'options' Array; has a small performance penalty; If you are using emit-value you will probably need to use map-options to display the label text in the select field rather than the value;  Refer to the 'Affecting model' section above"""
        return self._props.get("map-options")

    @ui_map_options.setter
    def ui_map_options(self, value):
        self._set_prop("map-options", value)

    @property
    def ui_disable_tab_selection(self):
        """Prevents the tab key from confirming the currently hovered option"""
        return self._props.get("disable-tab-selection")

    @ui_disable_tab_selection.setter
    def ui_disable_tab_selection(self, value):
        self._set_prop("disable-tab-selection", value)

    @property
    def ui_emit_value(self):
        """Update model with the value of the selected option instead of the whole option"""
        return self._props.get("emit-value")

    @ui_emit_value.setter
    def ui_emit_value(self, value):
        self._set_prop("emit-value", value)

    @property
    def ui_input_debounce(self):
        """Debounce the input model update with an amount of milliseconds (also affects the 'filter' event, if used)"""
        return self._props.get("input-debounce")

    @ui_input_debounce.setter
    def ui_input_debounce(self, value):
        self._set_prop("input-debounce", value)

    @property
    def ui_input_class(self):
        """Class definitions to be attributed to the underlying input tag"""
        return self._props.get("input-class")

    @ui_input_class.setter
    def ui_input_class(self, value):
        self._set_prop("input-class", value)

    @property
    def ui_input_style(self):
        """Style definitions to be attributed to the underlying input tag"""
        return self._props.get("input-style")

    @ui_input_style.setter
    def ui_input_style(self, value):
        self._set_prop("input-style", value)

    @property
    def ui_tabindex(self):
        return self._props.get("tabindex")

    @ui_tabindex.setter
    def ui_tabindex(self, value):
        self._set_prop("tabindex", value)

    @property
    def ui_autocomplete(self):
        """Autocomplete attribute for field"""
        return self._props.get("autocomplete")

    @ui_autocomplete.setter
    def ui_autocomplete(self, value):
        self._set_prop("autocomplete", value)

    @property
    def ui_transition_show(self):
        """Transition when showing the menu/dialog; One of Quasar's embedded transitions"""
        return self._props.get("transition-show")

    @ui_transition_show.setter
    def ui_transition_show(self, value):
        self._set_prop("transition-show", value)

    @property
    def ui_transition_hide(self):
        """Transition when hiding the menu/dialog; One of Quasar's embedded transitions"""
        return self._props.get("transition-hide")

    @ui_transition_hide.setter
    def ui_transition_hide(self, value):
        self._set_prop("transition-hide", value)

    @property
    def ui_transition_duration(self):
        """Transition duration when hiding the menu/dialog (in milliseconds, without unit)"""
        return self._props.get("transition-duration")

    @ui_transition_duration.setter
    def ui_transition_duration(self, value):
        self._set_prop("transition-duration", value)

    @property
    def ui_behavior(self):
        """Overrides the default dynamic mode of showing as menu on desktop and dialog on mobiles"""
        return self._props.get("behavior")

    @ui_behavior.setter
    def ui_behavior(self, value):
        self._set_prop("behavior", value)

    @property
    def ui_name(self):
        """Used to specify the name of the control; Useful if dealing with forms submitted directly to a URL"""
        return self._props.get("name")

    @ui_name.setter
    def ui_name(self, value):
        self._set_prop("name", value)

    @property
    def ui_virtual_scroll_item_size(self):
        """Default size in pixels (height if vertical, width if horizontal) of an item; This value is used for rendering the initial list; Try to use a value close to the minimum size of an item"""
        return self._props.get("virtual-scroll-item-size")

    @ui_virtual_scroll_item_size.setter
    def ui_virtual_scroll_item_size(self, value):
        self._set_prop("virtual-scroll-item-size", value)

    @property
    def ui_label(self):
        """A text label that will “float” up above the input field, once the field gets focus"""
        return self._props.get("label")

    @ui_label.setter
    def ui_label(self, value):
        self._set_prop("label", value)

    @property
    def ui_stack_label(self):
        """Label will be always shown above the field regardless of field content (if any)"""
        return self._props.get("stack-label")

    @ui_stack_label.setter
    def ui_stack_label(self, value):
        self._set_prop("stack-label", value)

    @property
    def ui_hint(self):
        """Helper (hint) text which gets placed below your wrapped form component"""
        return self._props.get("hint")

    @ui_hint.setter
    def ui_hint(self, value):
        self._set_prop("hint", value)

    @property
    def ui_hide_hint(self):
        """Hide the helper (hint) text when field doesn't have focus"""
        return self._props.get("hide-hint")

    @ui_hide_hint.setter
    def ui_hide_hint(self, value):
        self._set_prop("hide-hint", value)

    @property
    def ui_prefix(self):
        """Prefix"""
        return self._props.get("prefix")

    @ui_prefix.setter
    def ui_prefix(self, value):
        self._set_prop("prefix", value)

    @property
    def ui_suffix(self):
        """Suffix"""
        return self._props.get("suffix")

    @ui_suffix.setter
    def ui_suffix(self, value):
        self._set_prop("suffix", value)

    @property
    def ui_label_color(self):
        """Color name for the label from the Quasar Color Palette; Overrides the 'color' prop; The difference from 'color' prop is that the label will always have this color, even when field is not focused"""
        return self._props.get("label-color")

    @ui_label_color.setter
    def ui_label_color(self, value):
        self._set_prop("label-color", value)

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_bg_color(self):
        return self._props.get("bg-color")

    @ui_bg_color.setter
    def ui_bg_color(self, value):
        self._set_prop("bg-color", value)

    @property
    def ui_dark(self):
        return self._props.get("dark")

    @ui_dark.setter
    def ui_dark(self, value):
        self._set_prop("dark", value)

    @property
    def ui_loading(self):
        """Signals the user a process is in progress by displaying a spinner; Spinner can be customized by using the 'loading' slot."""
        return self._props.get("loading")

    @ui_loading.setter
    def ui_loading(self, value):
        self._set_prop("loading", value)

    @property
    def ui_clearable(self):
        """Appends clearable icon when a value (not undefined or null) is set; When clicked, model becomes null"""
        return self._props.get("clearable")

    @ui_clearable.setter
    def ui_clearable(self, value):
        self._set_prop("clearable", value)

    @property
    def ui_clear_icon(self):
        """Custom icon to use for the clear button when using along with 'clearable' prop"""
        return self._props.get("clear-icon")

    @ui_clear_icon.setter
    def ui_clear_icon(self, value):
        self._set_prop("clear-icon", value)

    @property
    def ui_filled(self):
        """Use 'filled' design for the field"""
        return self._props.get("filled")

    @ui_filled.setter
    def ui_filled(self, value):
        self._set_prop("filled", value)

    @property
    def ui_outlined(self):
        """Use 'outlined' design for the field"""
        return self._props.get("outlined")

    @ui_outlined.setter
    def ui_outlined(self, value):
        self._set_prop("outlined", value)

    @property
    def ui_borderless(self):
        """Use 'borderless' design for the field"""
        return self._props.get("borderless")

    @ui_borderless.setter
    def ui_borderless(self, value):
        self._set_prop("borderless", value)

    @property
    def ui_standout(self):
        """Use 'standout' design for the field; Specifies classes to be applied when focused (overriding default ones)"""
        return self._props.get("standout")

    @ui_standout.setter
    def ui_standout(self, value):
        self._set_prop("standout", value)

    @property
    def ui_label_slot(self):
        """Enables label slot; You need to set it to force use of the 'label' slot if the 'label' prop is not set"""
        return self._props.get("label-slot")

    @ui_label_slot.setter
    def ui_label_slot(self, value):
        self._set_prop("label-slot", value)

    @property
    def ui_bottom_slots(self):
        """Enables bottom slots ('error', 'hint', 'counter')"""
        return self._props.get("bottom-slots")

    @ui_bottom_slots.setter
    def ui_bottom_slots(self, value):
        self._set_prop("bottom-slots", value)

    @property
    def ui_hide_bottom_space(self):
        """Do not reserve space for hint/error/counter anymore when these are not used; As a result, it also disables the animation for those; It also allows the hint/error area to stretch vertically based on its content"""
        return self._props.get("hide-bottom-space")

    @ui_hide_bottom_space.setter
    def ui_hide_bottom_space(self, value):
        self._set_prop("hide-bottom-space", value)

    @property
    def ui_counter(self):
        """Show an automatic counter on bottom right"""
        return self._props.get("counter")

    @ui_counter.setter
    def ui_counter(self, value):
        self._set_prop("counter", value)

    @property
    def ui_rounded(self):
        return self._props.get("rounded")

    @ui_rounded.setter
    def ui_rounded(self, value):
        self._set_prop("rounded", value)

    @property
    def ui_square(self):
        """Remove border-radius so borders are squared; Overrides 'rounded' prop"""
        return self._props.get("square")

    @ui_square.setter
    def ui_square(self, value):
        self._set_prop("square", value)

    @property
    def ui_dense(self):
        return self._props.get("dense")

    @ui_dense.setter
    def ui_dense(self, value):
        self._set_prop("dense", value)

    @property
    def ui_item_aligned(self):
        """Match inner content alignment to that of QItem"""
        return self._props.get("item-aligned")

    @ui_item_aligned.setter
    def ui_item_aligned(self, value):
        self._set_prop("item-aligned", value)

    @property
    def ui_disable(self):
        return self._props.get("disable")

    @ui_disable.setter
    def ui_disable(self, value):
        self._set_prop("disable", value)

    @property
    def ui_readonly(self):
        return self._props.get("readonly")

    @ui_readonly.setter
    def ui_readonly(self, value):
        self._set_prop("readonly", value)

    @property
    def ui_autofocus(self):
        """Focus field on initial component render"""
        return self._props.get("autofocus")

    @ui_autofocus.setter
    def ui_autofocus(self, value):
        self._set_prop("autofocus", value)

    @property
    def ui_for(self):
        """Used to specify the 'id' of the control and also the 'for' attribute of the label that wraps it; If no 'name' prop is specified, then it is used for this attribute as well"""
        return self._props.get("for")

    @ui_for.setter
    def ui_for(self, value):
        self._set_prop("for", value)

    @property
    def ui_error(self):
        """Does field have validation errors?"""
        return self._props.get("error")

    @ui_error.setter
    def ui_error(self, value):
        self._set_prop("error", value)

    @property
    def ui_error_message(self):
        """Validation error message (gets displayed only if 'error' is set to 'true')"""
        return self._props.get("error-message")

    @ui_error_message.setter
    def ui_error_message(self, value):
        self._set_prop("error-message", value)

    @property
    def ui_no_error_icon(self):
        """Hide error icon when there is an error"""
        return self._props.get("no-error-icon")

    @ui_no_error_icon.setter
    def ui_no_error_icon(self, value):
        self._set_prop("no-error-icon", value)

    @property
    def ui_rules(self):
        """Array of Functions/Strings; If String, then it must be a name of one of the embedded validation rules"""
        return self._rules

    @ui_rules.setter
    def ui_rules(self, value):
        self._rules = value
        if self._rules and not self._rules_registered:
            self._rules_registered = True
            self.on_update_model_value(self._validate_rules)

    def _validate_rules(self):
        for rule in self.ui_rules:
            value = rule(self.ui_model_value)
            if isinstance(value, str) and value != "":
                self.ui_error_message = value
                self.ui_error = True
                return
        self.ui_error = None

    @property
    def ui_reactive_rules(self):
        """By default a change in the rules does not trigger a new validation until the model changes; If set to true then a change in the rules will trigger a validation; Has a performance penalty, so use it only when you really need it"""
        return self._props.get("reactive-rules")

    @ui_reactive_rules.setter
    def ui_reactive_rules(self, value):
        self._set_prop("reactive-rules", value)

    @property
    def ui_lazy_rules(self):
        """If set to boolean true then it checks validation status against the 'rules' only after field loses focus for first time; If set to 'ondemand' then it will trigger only when component's validate() method is manually called or when the wrapper QForm submits itself"""
        return self._props.get("lazy-rules")

    @ui_lazy_rules.setter
    def ui_lazy_rules(self, value):
        self._set_prop("lazy-rules", value)

    @property
    def ui_virtual_scroll_horizontal(self):
        """Make virtual list work in horizontal mode"""
        return self._props.get("virtual-scroll-horizontal")

    @ui_virtual_scroll_horizontal.setter
    def ui_virtual_scroll_horizontal(self, value):
        self._set_prop("virtual-scroll-horizontal", value)

    @property
    def ui_virtual_scroll_slice_size(self):
        """Minimum number of items to render in the virtual list"""
        return self._props.get("virtual-scroll-slice-size")

    @ui_virtual_scroll_slice_size.setter
    def ui_virtual_scroll_slice_size(self, value):
        self._set_prop("virtual-scroll-slice-size", value)

    @property
    def ui_virtual_scroll_slice_ratio_before(self):
        """Ratio of number of items in visible zone to render before it"""
        return self._props.get("virtual-scroll-slice-ratio-before")

    @ui_virtual_scroll_slice_ratio_before.setter
    def ui_virtual_scroll_slice_ratio_before(self, value):
        self._set_prop("virtual-scroll-slice-ratio-before", value)

    @property
    def ui_virtual_scroll_slice_ratio_after(self):
        """Ratio of number of items in visible zone to render after it"""
        return self._props.get("virtual-scroll-slice-ratio-after")

    @ui_virtual_scroll_slice_ratio_after.setter
    def ui_virtual_scroll_slice_ratio_after(self, value):
        self._set_prop("virtual-scroll-slice-ratio-after", value)

    @property
    def ui_virtual_scroll_sticky_size_start(self):
        """Size in pixels (height if vertical, width if horizontal) of the sticky part (if using one) at the start of the list; A correct value will improve scroll precision"""
        return self._props.get("virtual-scroll-sticky-size-start")

    @ui_virtual_scroll_sticky_size_start.setter
    def ui_virtual_scroll_sticky_size_start(self, value):
        self._set_prop("virtual-scroll-sticky-size-start", value)

    @property
    def ui_virtual_scroll_sticky_size_end(self):
        """Size in pixels (height if vertical, width if horizontal) of the sticky part (if using one) at the end of the list; A correct value will improve scroll precision"""
        return self._props.get("virtual-scroll-sticky-size-end")

    @ui_virtual_scroll_sticky_size_end.setter
    def ui_virtual_scroll_sticky_size_end(self, value):
        self._set_prop("virtual-scroll-sticky-size-end", value)

    @property
    def ui_table_colspan(self):
        """The number of columns in the table (you need this if you use table-layout: fixed)"""
        return self._props.get("table-colspan")

    @ui_table_colspan.setter
    def ui_table_colspan(self, value):
        self._set_prop("table-colspan", value)

    @property
    def ui_slot_after(self):
        """Append outer field; Suggestions: QIcon, QBtn"""
        return self.ui_slots.get("after", [])

    @ui_slot_after.setter
    def ui_slot_after(self, value):
        self._set_slot("after", value)

    @property
    def ui_slot_after_options(self):
        """Template slot for the elements that should be rendered after the list of options"""
        return self.ui_slots.get("after-options", [])

    @ui_slot_after_options.setter
    def ui_slot_after_options(self, value):
        self._set_slot("after-options", value)

    @property
    def ui_slot_append(self):
        """Append to inner field; Suggestions: QIcon, QBtn"""
        return self.ui_slots.get("append", [])

    @ui_slot_append.setter
    def ui_slot_append(self, value):
        self._set_slot("append", value)

    @property
    def ui_slot_before(self):
        """Prepend outer field; Suggestions: QIcon, QBtn"""
        return self.ui_slots.get("before", [])

    @ui_slot_before.setter
    def ui_slot_before(self, value):
        self._set_slot("before", value)

    @property
    def ui_slot_before_options(self):
        """Template slot for the elements that should be rendered before the list of options"""
        return self.ui_slots.get("before-options", [])

    @ui_slot_before_options.setter
    def ui_slot_before_options(self, value):
        self._set_slot("before-options", value)

    @property
    def ui_slot_counter(self):
        """Slot for counter text; Enabled only if 'bottom-slots' prop is used; Suggestion: <div>"""
        return self.ui_slots.get("counter", [])

    @ui_slot_counter.setter
    def ui_slot_counter(self, value):
        self._set_slot("counter", value)

    @property
    def ui_slot_error(self):
        """Slot for errors; Enabled only if 'bottom-slots' prop is used; Suggestion: <div>"""
        return self.ui_slots.get("error", [])

    @ui_slot_error.setter
    def ui_slot_error(self, value):
        self._set_slot("error", value)

    @property
    def ui_slot_hint(self):
        """Slot for hint text; Enabled only if 'bottom-slots' prop is used; Suggestion: <div>"""
        return self.ui_slots.get("hint", [])

    @ui_slot_hint.setter
    def ui_slot_hint(self, value):
        self._set_slot("hint", value)

    @property
    def ui_slot_label(self):
        """Slot for label; Used only if 'label-slot' prop is set or the 'label' prop is set; When it is used the text in the 'label' prop is ignored"""
        return self.ui_slots.get("label", [])

    @ui_slot_label.setter
    def ui_slot_label(self, value):
        self._set_slot("label", value)

    @property
    def ui_slot_loading(self):
        """Override default spinner when component is in loading mode; Use in conjunction with 'loading' prop"""
        return self.ui_slots.get("loading", [])

    @ui_slot_loading.setter
    def ui_slot_loading(self, value):
        self._set_slot("loading", value)

    @property
    def ui_slot_no_option(self):
        """What should the menu display after filtering options and none are left to be displayed; Suggestion: <div>"""
        return self.ui_slots.get("no-option", [])

    @ui_slot_no_option.setter
    def ui_slot_no_option(self, value):
        self._set_slot("no-option", value)

    @property
    def ui_slot_option(self):
        """Customize how options are rendered; Suggestion: QItem"""
        return self.ui_slots.get("option", [])

    @ui_slot_option.setter
    def ui_slot_option(self, value):
        self._set_slot("option", value)

    @property
    def ui_slot_prepend(self):
        """Prepend inner field; Suggestions: QIcon, QBtn"""
        return self.ui_slots.get("prepend", [])

    @ui_slot_prepend.setter
    def ui_slot_prepend(self, value):
        self._set_slot("prepend", value)

    @property
    def ui_slot_selected(self):
        """Override default selection slot; Suggestion: QChip"""
        return self.ui_slots.get("selected", [])

    @ui_slot_selected.setter
    def ui_slot_selected(self, value):
        self._set_slot("selected", value)

    @property
    def ui_slot_selected_item(self):
        """Override default selection slot; Suggestion: QChip"""
        return self.ui_slots.get("selected-item", [])

    @ui_slot_selected_item.setter
    def ui_slot_selected_item(self, value):
        self._set_slot("selected-item", value)

    def on_add(self, handler: Callable, arg: object = None):
        """
        Emitted when an option is added to the selection

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("add", handler, arg)

    def on_blur(self, handler: Callable, arg: object = None):
        """
        Emitted when component loses focus

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("blur", handler, arg)

    def on_clear(self, handler: Callable, arg: object = None):
        """
        When using the 'clearable' property, this event is emitted when the clear icon is clicked

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("clear", handler, arg)

    def on_filter(self, handler: Callable, arg: object = None):
        """
        Emitted when user wants to filter a value

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("filter", handler, arg)

    def on_filter_abort(self, handler: Callable, arg: object = None):
        """
        Emitted when a filtering was aborted; Probably a new one was requested?

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("filter-abort", handler, arg)

    def on_focus(self, handler: Callable, arg: object = None):
        """
        Emitted when component gets focused

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("focus", handler, arg)

    def on_input_value(self, handler: Callable, arg: object = None):
        """
        Emitted when the value in the text input changes

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("input-value", handler, arg)

    def on_keydown(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("keydown", handler, arg)

    def on_keypress(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("keypress", handler, arg)

    def on_keyup(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("keyup", handler, arg)

    def on_new_value(self, handler: Callable, arg: object = None):
        """
        Enables creation of new values; Emitted when a new value has been created; You can override 'new-value-mode' property with it

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("new-value", handler, arg)

    def on_popup_hide(self, handler: Callable, arg: object = None):
        """
        Emitted when the select options menu or dialog is hidden.

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("popup-hide", handler, arg)

    def on_popup_show(self, handler: Callable, arg: object = None):
        """
        Emitted when the select options menu or dialog is shown.

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("popup-show", handler, arg)

    def on_remove(self, handler: Callable, arg: object = None):
        """
        Emitted when an option is removed from selection

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("remove", handler, arg)

    def on_update_model_value(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("update:model-value", handler, arg)

    def on_virtual_scroll(self, handler: Callable, arg: object = None):
        """
        Emitted when the virtual scroll occurs

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("virtual-scroll", handler, arg)

    def ui_add(self, ui_opt, ui_unique=None):
        """Adds option to model"""
        kwargs = {}
        if ui_opt is not None:
            kwargs["opt"] = ui_opt
        if ui_unique is not None:
            kwargs["unique"] = ui_unique
        self._js_call_method("add", [kwargs])

    def ui_blur(self):
        """Blur component (lose focus)"""
        self._js_call_method("blur")

    def ui_filter(self, ui_value):
        """Filter options"""
        kwargs = {}
        if ui_value is not None:
            kwargs["value"] = ui_value
        self._js_call_method("filter", [kwargs])

    def ui_focus(self):
        """Focus component"""
        self._js_call_method("focus")

    def ui_getEmittingOptionValue(self, ui_opt):
        """Get the model value that would be emitted by QSelect when selecting a said option; Also takes into consideration if 'emit-value' is set"""
        kwargs = {}
        if ui_opt is not None:
            kwargs["opt"] = ui_opt
        self._js_call_method("getEmittingOptionValue", [kwargs])

    def ui_getOptionIndex(self):
        """Gets current focused option index from menu; It's -1 if no option is focused"""
        self._js_call_method("getOptionIndex")

    def ui_getOptionLabel(self, ui_opt):
        """Get the label of an option; Takes into consideration the 'option-label' prop (if used)"""
        kwargs = {}
        if ui_opt is not None:
            kwargs["opt"] = ui_opt
        self._js_call_method("getOptionLabel", [kwargs])

    def ui_getOptionValue(self, ui_opt):
        """Get the model value of an option; Takes into consideration 'option-value' (if used), but does not looks for 'emit-value', like getEmittingOptionValue() does"""
        kwargs = {}
        if ui_opt is not None:
            kwargs["opt"] = ui_opt
        self._js_call_method("getOptionValue", [kwargs])

    def ui_hidePopup(self):
        """Hide popup"""
        self._js_call_method("hidePopup")

    def ui_isOptionDisabled(self, ui_opt):
        """Tells if an option is disabled; Takes into consideration 'option-disable' prop (if used)"""
        kwargs = {}
        if ui_opt is not None:
            kwargs["opt"] = ui_opt
        self._js_call_method("isOptionDisabled", [kwargs])

    def ui_isOptionSelected(self, ui_opt):
        """Tells if an option is selected"""
        kwargs = {}
        if ui_opt is not None:
            kwargs["opt"] = ui_opt
        self._js_call_method("isOptionSelected", [kwargs])

    def ui_moveOptionSelection(self, ui_offset=None, ui_skipInputValue=None):
        """Move selected option from menu by index offset"""
        kwargs = {}
        if ui_offset is not None:
            kwargs["offset"] = ui_offset
        if ui_skipInputValue is not None:
            kwargs["skipInputValue"] = ui_skipInputValue
        self._js_call_method("moveOptionSelection", [kwargs])

    def ui_refresh(self, ui_index=None):
        """Refreshes the virtual scroll list; Use it after appending items"""
        kwargs = {}
        if ui_index is not None:
            kwargs["index"] = ui_index
        self._js_call_method("refresh", [kwargs])

    def ui_removeAtIndex(self, ui_index):
        """Remove selected option located at specific index"""
        kwargs = {}
        if ui_index is not None:
            kwargs["index"] = ui_index
        self._js_call_method("removeAtIndex", [kwargs])

    def ui_reset(self):
        """Resets the virtual scroll computations; Needed for custom edge-cases"""
        self._js_call_method("reset")

    def ui_resetValidation(self):
        """Reset validation status"""
        self._js_call_method("resetValidation")

    def ui_scrollTo(self, ui_index, ui_edge=None):
        """Scroll the virtual scroll list to the item with the specified index (0 based)"""
        kwargs = {}
        if ui_index is not None:
            kwargs["index"] = ui_index
        if ui_edge is not None:
            kwargs["edge"] = ui_edge
        self._js_call_method("scrollTo", [kwargs])

    def ui_setOptionIndex(self, ui_index):
        """Sets option from menu as 'focused'; -1 to focus none"""
        kwargs = {}
        if ui_index is not None:
            kwargs["index"] = ui_index
        self._js_call_method("setOptionIndex", [kwargs])

    def ui_showPopup(self):
        """Focus and open popup"""
        self._js_call_method("showPopup")

    def ui_toggleOption(self, ui_opt, ui_keepOpen=None):
        """Add/remove option from model"""
        kwargs = {}
        if ui_opt is not None:
            kwargs["opt"] = ui_opt
        if ui_keepOpen is not None:
            kwargs["keepOpen"] = ui_keepOpen
        self._js_call_method("toggleOption", [kwargs])

    def ui_updateInputValue(self, ui_value, ui_noFilter=None):
        """If 'use-input' is specified, this updates the value that it holds"""
        kwargs = {}
        if ui_value is not None:
            kwargs["value"] = ui_value
        if ui_noFilter is not None:
            kwargs["noFilter"] = ui_noFilter
        self._js_call_method("updateInputValue", [kwargs])

    def ui_updateMenuPosition(self):
        """Recomputes menu position"""
        self._js_call_method("updateMenuPosition")

    def ui_validate(self, ui_value=None):
        """Trigger a validation"""
        kwargs = {}
        if ui_value is not None:
            kwargs["value"] = ui_value
        self._js_call_method("validate", [kwargs])

    def _get_js_methods(self):
        return [
            "add",
            "blur",
            "filter",
            "focus",
            "getEmittingOptionValue",
            "getOptionIndex",
            "getOptionLabel",
            "getOptionValue",
            "hidePopup",
            "isOptionDisabled",
            "isOptionSelected",
            "moveOptionSelection",
            "refresh",
            "removeAtIndex",
            "reset",
            "resetValidation",
            "scrollTo",
            "setOptionIndex",
            "showPopup",
            "toggleOption",
            "updateInputValue",
            "updateMenuPosition",
            "validate",
        ]


class QSeparator(Component):
    """
    Quasar Component: `QSeparator <https://v2.quasar.dev/vue-components/separator>`__

    :param ui_dark:
    :param ui_spaced: If set to true, the corresponding direction margins will be set to 8px; It can also be set to a size in CSS units, including unit name, or one of the xs|sm|md|lg|xl predefined sizes
    :param ui_inset: If set to Boolean true, the left and right margins will be set to 16px. If set to 'item' then it will match a QItem's design. If set to 'item-thumbnail' then it will match the design of a QItem with a thumbnail on the left side
    :param ui_vertical: If set to true, the separator will be vertical.
    :param ui_size:
    :param ui_color:
    """

    def __init__(
        self,
        *children,
        ui_dark: Any | None = None,
        ui_spaced: bool | str | None = None,
        ui_inset: bool | str | None = None,
        ui_vertical: bool | None = None,
        ui_size: Any | None = None,
        ui_color: Any | None = None,
        **kwargs,
    ):
        super().__init__("QSeparator", *children, **kwargs)
        if ui_dark is not None:
            self._props["dark"] = ui_dark
        if ui_spaced is not None:
            self._props["spaced"] = ui_spaced
        if ui_inset is not None:
            self._props["inset"] = ui_inset
        if ui_vertical is not None:
            self._props["vertical"] = ui_vertical
        if ui_size is not None:
            self._props["size"] = ui_size
        if ui_color is not None:
            self._props["color"] = ui_color

    @property
    def ui_dark(self):
        return self._props.get("dark")

    @ui_dark.setter
    def ui_dark(self, value):
        self._set_prop("dark", value)

    @property
    def ui_spaced(self):
        """If set to true, the corresponding direction margins will be set to 8px; It can also be set to a size in CSS units, including unit name, or one of the xs|sm|md|lg|xl predefined sizes"""
        return self._props.get("spaced")

    @ui_spaced.setter
    def ui_spaced(self, value):
        self._set_prop("spaced", value)

    @property
    def ui_inset(self):
        """If set to Boolean true, the left and right margins will be set to 16px. If set to 'item' then it will match a QItem's design. If set to 'item-thumbnail' then it will match the design of a QItem with a thumbnail on the left side"""
        return self._props.get("inset")

    @ui_inset.setter
    def ui_inset(self, value):
        self._set_prop("inset", value)

    @property
    def ui_vertical(self):
        """If set to true, the separator will be vertical."""
        return self._props.get("vertical")

    @ui_vertical.setter
    def ui_vertical(self, value):
        self._set_prop("vertical", value)

    @property
    def ui_size(self):
        return self._props.get("size")

    @ui_size.setter
    def ui_size(self, value):
        self._set_prop("size", value)

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    def _get_js_methods(self):
        return []


class QSkeleton(Component):
    """
    Quasar Component: `QSkeleton <https://v2.quasar.dev/vue-components/skeleton>`__

    :param ui_dark:
    :param ui_type: Type of skeleton placeholder
    :param ui_animation: The animation effect of the skeleton placeholder
    :param ui_animation_speed:
    :param ui_square:
    :param ui_bordered:
    :param ui_size: Size in CSS units, including unit name; Overrides 'height' and 'width' props and applies the value to both height and width
    :param ui_width: Width in CSS units, including unit name; Apply custom width; Use this prop or through CSS; Overridden by 'size' prop if used
    :param ui_height: Height in CSS units, including unit name; Apply custom height; Use this prop or through CSS; Overridden by 'size' prop if used
    :param ui_tag:
    """

    def __init__(
        self,
        *children,
        ui_dark: Any | None = None,
        ui_type: str | None = None,
        ui_animation: str | None = None,
        ui_animation_speed: Any | None = None,
        ui_square: Any | None = None,
        ui_bordered: Any | None = None,
        ui_size: str | None = None,
        ui_width: str | None = None,
        ui_height: str | None = None,
        ui_tag: Any | None = None,
        **kwargs,
    ):
        super().__init__("QSkeleton", *children, **kwargs)
        if ui_dark is not None:
            self._props["dark"] = ui_dark
        if ui_type is not None:
            self._props["type"] = ui_type
        if ui_animation is not None:
            self._props["animation"] = ui_animation
        if ui_animation_speed is not None:
            self._props["animation-speed"] = ui_animation_speed
        if ui_square is not None:
            self._props["square"] = ui_square
        if ui_bordered is not None:
            self._props["bordered"] = ui_bordered
        if ui_size is not None:
            self._props["size"] = ui_size
        if ui_width is not None:
            self._props["width"] = ui_width
        if ui_height is not None:
            self._props["height"] = ui_height
        if ui_tag is not None:
            self._props["tag"] = ui_tag

    @property
    def ui_dark(self):
        return self._props.get("dark")

    @ui_dark.setter
    def ui_dark(self, value):
        self._set_prop("dark", value)

    @property
    def ui_type(self):
        """Type of skeleton placeholder"""
        return self._props.get("type")

    @ui_type.setter
    def ui_type(self, value):
        self._set_prop("type", value)

    @property
    def ui_animation(self):
        """The animation effect of the skeleton placeholder"""
        return self._props.get("animation")

    @ui_animation.setter
    def ui_animation(self, value):
        self._set_prop("animation", value)

    @property
    def ui_animation_speed(self):
        return self._props.get("animation-speed")

    @ui_animation_speed.setter
    def ui_animation_speed(self, value):
        self._set_prop("animation-speed", value)

    @property
    def ui_square(self):
        return self._props.get("square")

    @ui_square.setter
    def ui_square(self, value):
        self._set_prop("square", value)

    @property
    def ui_bordered(self):
        return self._props.get("bordered")

    @ui_bordered.setter
    def ui_bordered(self, value):
        self._set_prop("bordered", value)

    @property
    def ui_size(self):
        """Size in CSS units, including unit name; Overrides 'height' and 'width' props and applies the value to both height and width"""
        return self._props.get("size")

    @ui_size.setter
    def ui_size(self, value):
        self._set_prop("size", value)

    @property
    def ui_width(self):
        """Width in CSS units, including unit name; Apply custom width; Use this prop or through CSS; Overridden by 'size' prop if used"""
        return self._props.get("width")

    @ui_width.setter
    def ui_width(self, value):
        self._set_prop("width", value)

    @property
    def ui_height(self):
        """Height in CSS units, including unit name; Apply custom height; Use this prop or through CSS; Overridden by 'size' prop if used"""
        return self._props.get("height")

    @ui_height.setter
    def ui_height(self, value):
        self._set_prop("height", value)

    @property
    def ui_tag(self):
        return self._props.get("tag")

    @ui_tag.setter
    def ui_tag(self, value):
        self._set_prop("tag", value)

    def _get_js_methods(self):
        return []


class QSlideItem(Component):
    """
    Quasar Component: `QSlideItem <https://v2.quasar.dev/vue-components/slide-item>`__

    :param ui_left_color: Color name for left-side background from the Quasar Color Palette
    :param ui_right_color: Color name for right-side background from the Quasar Color Palette
    :param ui_top_color: Color name for top-side background from the Quasar Color Palette
    :param ui_bottom_color: Color name for bottom-side background from the Quasar Color Palette
    :param ui_dark:
    """

    def __init__(
        self,
        *children,
        ui_left_color: Any | None = None,
        ui_right_color: Any | None = None,
        ui_top_color: Any | None = None,
        ui_bottom_color: Any | None = None,
        ui_dark: Any | None = None,
        **kwargs,
    ):
        super().__init__("QSlideItem", *children, **kwargs)
        if ui_left_color is not None:
            self._props["left-color"] = ui_left_color
        if ui_right_color is not None:
            self._props["right-color"] = ui_right_color
        if ui_top_color is not None:
            self._props["top-color"] = ui_top_color
        if ui_bottom_color is not None:
            self._props["bottom-color"] = ui_bottom_color
        if ui_dark is not None:
            self._props["dark"] = ui_dark

    @property
    def ui_left_color(self):
        """Color name for left-side background from the Quasar Color Palette"""
        return self._props.get("left-color")

    @ui_left_color.setter
    def ui_left_color(self, value):
        self._set_prop("left-color", value)

    @property
    def ui_right_color(self):
        """Color name for right-side background from the Quasar Color Palette"""
        return self._props.get("right-color")

    @ui_right_color.setter
    def ui_right_color(self, value):
        self._set_prop("right-color", value)

    @property
    def ui_top_color(self):
        """Color name for top-side background from the Quasar Color Palette"""
        return self._props.get("top-color")

    @ui_top_color.setter
    def ui_top_color(self, value):
        self._set_prop("top-color", value)

    @property
    def ui_bottom_color(self):
        """Color name for bottom-side background from the Quasar Color Palette"""
        return self._props.get("bottom-color")

    @ui_bottom_color.setter
    def ui_bottom_color(self, value):
        self._set_prop("bottom-color", value)

    @property
    def ui_dark(self):
        return self._props.get("dark")

    @ui_dark.setter
    def ui_dark(self, value):
        self._set_prop("dark", value)

    @property
    def ui_slot_bottom(self):
        """Bottom side content when sliding"""
        return self.ui_slots.get("bottom", [])

    @ui_slot_bottom.setter
    def ui_slot_bottom(self, value):
        self._set_slot("bottom", value)

    @property
    def ui_slot_left(self):
        """Left side content when sliding"""
        return self.ui_slots.get("left", [])

    @ui_slot_left.setter
    def ui_slot_left(self, value):
        self._set_slot("left", value)

    @property
    def ui_slot_right(self):
        """Right side content when sliding"""
        return self.ui_slots.get("right", [])

    @ui_slot_right.setter
    def ui_slot_right(self, value):
        self._set_slot("right", value)

    @property
    def ui_slot_top(self):
        """Top side content when sliding"""
        return self.ui_slots.get("top", [])

    @ui_slot_top.setter
    def ui_slot_top(self, value):
        self._set_slot("top", value)

    def on_action(self, handler: Callable, arg: object = None):
        """
        Emitted when user finished sliding the item to either sides

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("action", handler, arg)

    def on_bottom(self, handler: Callable, arg: object = None):
        """
        Emitted when user finished sliding the item down

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("bottom", handler, arg)

    def on_left(self, handler: Callable, arg: object = None):
        """
        Emitted when user finished sliding the item to the left

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("left", handler, arg)

    def on_right(self, handler: Callable, arg: object = None):
        """
        Emitted when user finished sliding the item to the right

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("right", handler, arg)

    def on_slide(self, handler: Callable, arg: object = None):
        """
        Emitted while user is sliding the item to one of the available sides

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("slide", handler, arg)

    def on_top(self, handler: Callable, arg: object = None):
        """
        Emitted when user finished sliding the item up

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("top", handler, arg)

    def ui_reset(self):
        """Reset to initial state (not swiped to any side)"""
        self._js_call_method("reset")

    def _get_js_methods(self):
        return ["reset"]


class QSlideTransition(Component):
    """
    Quasar Component: `QSlideTransition <https://v2.quasar.dev/vue-components/slide-transition>`__

    :param ui_appear: If set to true, the transition will be applied on the initial render.
    :param ui_duration: Duration (in milliseconds) enabling animated scroll.
    """

    def __init__(
        self,
        *children,
        ui_appear: bool | None = None,
        ui_duration: float | None = None,
        **kwargs,
    ):
        super().__init__("QSlideTransition", *children, **kwargs)
        if ui_appear is not None:
            self._props["appear"] = ui_appear
        if ui_duration is not None:
            self._props["duration"] = ui_duration

    @property
    def ui_appear(self):
        """If set to true, the transition will be applied on the initial render."""
        return self._props.get("appear")

    @ui_appear.setter
    def ui_appear(self, value):
        self._set_prop("appear", value)

    @property
    def ui_duration(self):
        """Duration (in milliseconds) enabling animated scroll."""
        return self._props.get("duration")

    @ui_duration.setter
    def ui_duration(self, value):
        self._set_prop("duration", value)

    def on_hide(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("hide", handler, arg)

    def on_show(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("show", handler, arg)

    def _get_js_methods(self):
        return []


class QSlider(Component):
    """
    Quasar Component: `QSlider <https://v2.quasar.dev/vue-components/slider>`__

    :param ui_model_value: Model of the component (must be between min/max); Either use this property (along with a listener for 'update:modelValue' event) OR use v-model directive
    :param ui_label_value: Override default label value
    :param ui_min: Minimum value of the model; Set track's minimum value
    :param ui_max: Maximum value of the model; Set track's maximum value
    :param ui_inner_min: Inner minimum value of the model; Use in case you need the model value to be inside of the track's min-max values; Needs to be higher or equal to 'min' prop; Defaults to 'min' prop
    :param ui_inner_max: Inner maximum value of the model; Use in case you need the model value to be inside of the track's min-max values; Needs to be lower or equal to 'max' prop; Defaults to 'max' prop
    :param ui_step: Specify step amount between valid values (> 0.0); When step equals to 0 it defines infinite granularity
    :param ui_snap: Snap on valid values, rather than sliding freely; Suggestion: use with 'step' prop
    :param ui_reverse: Work in reverse (changes direction)
    :param ui_vertical: Display in vertical direction
    :param ui_color:
    :param ui_track_color: Color name for the track (can be 'transparent' too) from the Quasar Color Palette
    :param ui_track_img: Apply a pattern image on the track
    :param ui_inner_track_color: Color name for the inner track (can be 'transparent' too) from the Quasar Color Palette
    :param ui_inner_track_img: Apply a pattern image on the inner track
    :param ui_selection_color: Color name for the selection bar (can be 'transparent' too) from the Quasar Color Palette
    :param ui_selection_img: Apply a pattern image on the selection bar
    :param ui_label: Popup a label when user clicks/taps on the slider thumb and moves it
    :param ui_label_color:
    :param ui_label_text_color:
    :param ui_switch_label_side: Switch the position of the label (top <-> bottom or left <-> right)
    :param ui_label_always: Always display the label
    :param ui_markers: Display markers on the track, one for each possible value for the model or using a custom step (when specifying a Number)
    :param ui_marker_labels: Configure the marker labels (or show the default ones if 'true'); Array of definition Objects or Object with key-value where key is the model and the value is the marker label definition
    :param ui_marker_labels_class: CSS class(es) to apply to the marker labels container
    :param ui_switch_marker_labels_side: Switch the position of the marker labels (top <-> bottom or left <-> right)
    :param ui_track_size: Track size (including CSS unit)
    :param ui_thumb_size: Thumb size (including CSS unit)
    :param ui_thumb_color:
    :param ui_thumb_path: Set custom thumb svg path
    :param ui_dark:
    :param ui_dense:
    :param ui_disable:
    :param ui_readonly:
    :param ui_tabindex:
    :param ui_name: Used to specify the name of the control; Useful if dealing with forms submitted directly to a URL
    """

    def __init__(
        self,
        *children,
        ui_model_value: float | None | Any = None,
        ui_label_value: str | float | None = None,
        ui_min: float | None = None,
        ui_max: float | None = None,
        ui_inner_min: float | None = None,
        ui_inner_max: float | None = None,
        ui_step: float | None = None,
        ui_snap: bool | None = None,
        ui_reverse: bool | None = None,
        ui_vertical: bool | None = None,
        ui_color: Any | None = None,
        ui_track_color: Any | None = None,
        ui_track_img: str | None = None,
        ui_inner_track_color: Any | None = None,
        ui_inner_track_img: str | None = None,
        ui_selection_color: Any | None = None,
        ui_selection_img: str | None = None,
        ui_label: bool | None = None,
        ui_label_color: Any | None = None,
        ui_label_text_color: Any | None = None,
        ui_switch_label_side: bool | None = None,
        ui_label_always: bool | None = None,
        ui_markers: bool | float | None = None,
        ui_marker_labels: bool | list | dict | Callable | None = None,
        ui_marker_labels_class: str | None = None,
        ui_switch_marker_labels_side: bool | None = None,
        ui_track_size: str | None = None,
        ui_thumb_size: str | None = None,
        ui_thumb_color: Any | None = None,
        ui_thumb_path: str | None = None,
        ui_dark: Any | None = None,
        ui_dense: Any | None = None,
        ui_disable: Any | None = None,
        ui_readonly: Any | None = None,
        ui_tabindex: Any | None = None,
        ui_name: str | None = None,
        **kwargs,
    ):
        super().__init__("QSlider", *children, **kwargs)
        self.on("update:model-value", self.__update_model_value)

        if ui_model_value is not None:
            self._props["model-value"] = ui_model_value
        if ui_label_value is not None:
            self._props["label-value"] = ui_label_value
        if ui_min is not None:
            self._props["min"] = ui_min
        if ui_max is not None:
            self._props["max"] = ui_max
        if ui_inner_min is not None:
            self._props["inner-min"] = ui_inner_min
        if ui_inner_max is not None:
            self._props["inner-max"] = ui_inner_max
        if ui_step is not None:
            self._props["step"] = ui_step
        if ui_snap is not None:
            self._props["snap"] = ui_snap
        if ui_reverse is not None:
            self._props["reverse"] = ui_reverse
        if ui_vertical is not None:
            self._props["vertical"] = ui_vertical
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_track_color is not None:
            self._props["track-color"] = ui_track_color
        if ui_track_img is not None:
            self._props["track-img"] = ui_track_img
        if ui_inner_track_color is not None:
            self._props["inner-track-color"] = ui_inner_track_color
        if ui_inner_track_img is not None:
            self._props["inner-track-img"] = ui_inner_track_img
        if ui_selection_color is not None:
            self._props["selection-color"] = ui_selection_color
        if ui_selection_img is not None:
            self._props["selection-img"] = ui_selection_img
        if ui_label is not None:
            self._props["label"] = ui_label
        if ui_label_color is not None:
            self._props["label-color"] = ui_label_color
        if ui_label_text_color is not None:
            self._props["label-text-color"] = ui_label_text_color
        if ui_switch_label_side is not None:
            self._props["switch-label-side"] = ui_switch_label_side
        if ui_label_always is not None:
            self._props["label-always"] = ui_label_always
        if ui_markers is not None:
            self._props["markers"] = ui_markers
        if ui_marker_labels is not None:
            self._props["marker-labels"] = ui_marker_labels
        if ui_marker_labels_class is not None:
            self._props["marker-labels-class"] = ui_marker_labels_class
        if ui_switch_marker_labels_side is not None:
            self._props["switch-marker-labels-side"] = (
                ui_switch_marker_labels_side
            )
        if ui_track_size is not None:
            self._props["track-size"] = ui_track_size
        if ui_thumb_size is not None:
            self._props["thumb-size"] = ui_thumb_size
        if ui_thumb_color is not None:
            self._props["thumb-color"] = ui_thumb_color
        if ui_thumb_path is not None:
            self._props["thumb-path"] = ui_thumb_path
        if ui_dark is not None:
            self._props["dark"] = ui_dark
        if ui_dense is not None:
            self._props["dense"] = ui_dense
        if ui_disable is not None:
            self._props["disable"] = ui_disable
        if ui_readonly is not None:
            self._props["readonly"] = ui_readonly
        if ui_tabindex is not None:
            self._props["tabindex"] = ui_tabindex
        if ui_name is not None:
            self._props["name"] = ui_name

    def __update_model_value(self, event: Event):
        self._set_prop("model-value", event.value)

    @property
    def ui_model_value(self):
        """Model of the component (must be between min/max); Either use this property (along with a listener for 'update:modelValue' event) OR use v-model directive"""
        return self._props.get("model-value")

    @ui_model_value.setter
    def ui_model_value(self, value):
        self._set_prop("model-value", value)

    @property
    def ui_label_value(self):
        """Override default label value"""
        return self._props.get("label-value")

    @ui_label_value.setter
    def ui_label_value(self, value):
        self._set_prop("label-value", value)

    @property
    def ui_min(self):
        """Minimum value of the model; Set track's minimum value"""
        return self._props.get("min")

    @ui_min.setter
    def ui_min(self, value):
        self._set_prop("min", value)

    @property
    def ui_max(self):
        """Maximum value of the model; Set track's maximum value"""
        return self._props.get("max")

    @ui_max.setter
    def ui_max(self, value):
        self._set_prop("max", value)

    @property
    def ui_inner_min(self):
        """Inner minimum value of the model; Use in case you need the model value to be inside of the track's min-max values; Needs to be higher or equal to 'min' prop; Defaults to 'min' prop"""
        return self._props.get("inner-min")

    @ui_inner_min.setter
    def ui_inner_min(self, value):
        self._set_prop("inner-min", value)

    @property
    def ui_inner_max(self):
        """Inner maximum value of the model; Use in case you need the model value to be inside of the track's min-max values; Needs to be lower or equal to 'max' prop; Defaults to 'max' prop"""
        return self._props.get("inner-max")

    @ui_inner_max.setter
    def ui_inner_max(self, value):
        self._set_prop("inner-max", value)

    @property
    def ui_step(self):
        """Specify step amount between valid values (> 0.0); When step equals to 0 it defines infinite granularity"""
        return self._props.get("step")

    @ui_step.setter
    def ui_step(self, value):
        self._set_prop("step", value)

    @property
    def ui_snap(self):
        """Snap on valid values, rather than sliding freely; Suggestion: use with 'step' prop"""
        return self._props.get("snap")

    @ui_snap.setter
    def ui_snap(self, value):
        self._set_prop("snap", value)

    @property
    def ui_reverse(self):
        """Work in reverse (changes direction)"""
        return self._props.get("reverse")

    @ui_reverse.setter
    def ui_reverse(self, value):
        self._set_prop("reverse", value)

    @property
    def ui_vertical(self):
        """Display in vertical direction"""
        return self._props.get("vertical")

    @ui_vertical.setter
    def ui_vertical(self, value):
        self._set_prop("vertical", value)

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_track_color(self):
        """Color name for the track (can be 'transparent' too) from the Quasar Color Palette"""
        return self._props.get("track-color")

    @ui_track_color.setter
    def ui_track_color(self, value):
        self._set_prop("track-color", value)

    @property
    def ui_track_img(self):
        """Apply a pattern image on the track"""
        return self._props.get("track-img")

    @ui_track_img.setter
    def ui_track_img(self, value):
        self._set_prop("track-img", value)

    @property
    def ui_inner_track_color(self):
        """Color name for the inner track (can be 'transparent' too) from the Quasar Color Palette"""
        return self._props.get("inner-track-color")

    @ui_inner_track_color.setter
    def ui_inner_track_color(self, value):
        self._set_prop("inner-track-color", value)

    @property
    def ui_inner_track_img(self):
        """Apply a pattern image on the inner track"""
        return self._props.get("inner-track-img")

    @ui_inner_track_img.setter
    def ui_inner_track_img(self, value):
        self._set_prop("inner-track-img", value)

    @property
    def ui_selection_color(self):
        """Color name for the selection bar (can be 'transparent' too) from the Quasar Color Palette"""
        return self._props.get("selection-color")

    @ui_selection_color.setter
    def ui_selection_color(self, value):
        self._set_prop("selection-color", value)

    @property
    def ui_selection_img(self):
        """Apply a pattern image on the selection bar"""
        return self._props.get("selection-img")

    @ui_selection_img.setter
    def ui_selection_img(self, value):
        self._set_prop("selection-img", value)

    @property
    def ui_label(self):
        """Popup a label when user clicks/taps on the slider thumb and moves it"""
        return self._props.get("label")

    @ui_label.setter
    def ui_label(self, value):
        self._set_prop("label", value)

    @property
    def ui_label_color(self):
        return self._props.get("label-color")

    @ui_label_color.setter
    def ui_label_color(self, value):
        self._set_prop("label-color", value)

    @property
    def ui_label_text_color(self):
        return self._props.get("label-text-color")

    @ui_label_text_color.setter
    def ui_label_text_color(self, value):
        self._set_prop("label-text-color", value)

    @property
    def ui_switch_label_side(self):
        """Switch the position of the label (top <-> bottom or left <-> right)"""
        return self._props.get("switch-label-side")

    @ui_switch_label_side.setter
    def ui_switch_label_side(self, value):
        self._set_prop("switch-label-side", value)

    @property
    def ui_label_always(self):
        """Always display the label"""
        return self._props.get("label-always")

    @ui_label_always.setter
    def ui_label_always(self, value):
        self._set_prop("label-always", value)

    @property
    def ui_markers(self):
        """Display markers on the track, one for each possible value for the model or using a custom step (when specifying a Number)"""
        return self._props.get("markers")

    @ui_markers.setter
    def ui_markers(self, value):
        self._set_prop("markers", value)

    @property
    def ui_marker_labels(self):
        """Configure the marker labels (or show the default ones if 'true'); Array of definition Objects or Object with key-value where key is the model and the value is the marker label definition"""
        return self._props.get("marker-labels")

    @ui_marker_labels.setter
    def ui_marker_labels(self, value):
        self._set_prop("marker-labels", value)

    @property
    def ui_marker_labels_class(self):
        """CSS class(es) to apply to the marker labels container"""
        return self._props.get("marker-labels-class")

    @ui_marker_labels_class.setter
    def ui_marker_labels_class(self, value):
        self._set_prop("marker-labels-class", value)

    @property
    def ui_switch_marker_labels_side(self):
        """Switch the position of the marker labels (top <-> bottom or left <-> right)"""
        return self._props.get("switch-marker-labels-side")

    @ui_switch_marker_labels_side.setter
    def ui_switch_marker_labels_side(self, value):
        self._set_prop("switch-marker-labels-side", value)

    @property
    def ui_track_size(self):
        """Track size (including CSS unit)"""
        return self._props.get("track-size")

    @ui_track_size.setter
    def ui_track_size(self, value):
        self._set_prop("track-size", value)

    @property
    def ui_thumb_size(self):
        """Thumb size (including CSS unit)"""
        return self._props.get("thumb-size")

    @ui_thumb_size.setter
    def ui_thumb_size(self, value):
        self._set_prop("thumb-size", value)

    @property
    def ui_thumb_color(self):
        return self._props.get("thumb-color")

    @ui_thumb_color.setter
    def ui_thumb_color(self, value):
        self._set_prop("thumb-color", value)

    @property
    def ui_thumb_path(self):
        """Set custom thumb svg path"""
        return self._props.get("thumb-path")

    @ui_thumb_path.setter
    def ui_thumb_path(self, value):
        self._set_prop("thumb-path", value)

    @property
    def ui_dark(self):
        return self._props.get("dark")

    @ui_dark.setter
    def ui_dark(self, value):
        self._set_prop("dark", value)

    @property
    def ui_dense(self):
        return self._props.get("dense")

    @ui_dense.setter
    def ui_dense(self, value):
        self._set_prop("dense", value)

    @property
    def ui_disable(self):
        return self._props.get("disable")

    @ui_disable.setter
    def ui_disable(self, value):
        self._set_prop("disable", value)

    @property
    def ui_readonly(self):
        return self._props.get("readonly")

    @ui_readonly.setter
    def ui_readonly(self, value):
        self._set_prop("readonly", value)

    @property
    def ui_tabindex(self):
        return self._props.get("tabindex")

    @ui_tabindex.setter
    def ui_tabindex(self, value):
        self._set_prop("tabindex", value)

    @property
    def ui_name(self):
        """Used to specify the name of the control; Useful if dealing with forms submitted directly to a URL"""
        return self._props.get("name")

    @ui_name.setter
    def ui_name(self, value):
        self._set_prop("name", value)

    @property
    def ui_slot_marker_label(self):
        """What should the menu display after filtering options and none are left to be displayed; Suggestion: <div>"""
        return self.ui_slots.get("marker-label", [])

    @ui_slot_marker_label.setter
    def ui_slot_marker_label(self, value):
        self._set_slot("marker-label", value)

    @property
    def ui_slot_marker_label_group(self):
        """What should the menu display after filtering options and none are left to be displayed; Suggestion: <div>"""
        return self.ui_slots.get("marker-label-group", [])

    @ui_slot_marker_label_group.setter
    def ui_slot_marker_label_group(self, value):
        self._set_slot("marker-label-group", value)

    def on_change(self, handler: Callable, arg: object = None):
        """
        Emitted on lazy model value change (after user slides then releases the thumb)

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("change", handler, arg)

    def on_pan(self, handler: Callable, arg: object = None):
        """
        Triggered when user starts panning on the component

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("pan", handler, arg)

    def on_update_model_value(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("update:model-value", handler, arg)

    def _get_js_methods(self):
        return []


class QSpace(Component):
    """
    Quasar Component: `QSpace <https://v2.quasar.dev/vue-components/space>`__

    """

    def __init__(self, *children, **kwargs):
        super().__init__("QSpace", *children, **kwargs)

    def _get_js_methods(self):
        return []


class QSpinnerHourglass(Component):
    """
    Quasar Component: `QSpinnerHourglass <https://v2.quasar.dev/vue-components/spinners>`__

    :param ui_color:
    :param ui_size: Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)
    """

    def __init__(
        self,
        *children,
        ui_color: Any | None = None,
        ui_size: str | None = None,
        **kwargs,
    ):
        super().__init__("QSpinnerHourglass", *children, **kwargs)
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_size is not None:
            self._props["size"] = ui_size

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_size(self):
        """Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)"""
        return self._props.get("size")

    @ui_size.setter
    def ui_size(self, value):
        self._set_prop("size", value)

    def _get_js_methods(self):
        return []


class QSpinnerClock(Component):
    """
    Quasar Component: `QSpinnerClock <https://v2.quasar.dev/vue-components/spinners>`__

    :param ui_color:
    :param ui_size: Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)
    """

    def __init__(
        self,
        *children,
        ui_color: Any | None = None,
        ui_size: str | None = None,
        **kwargs,
    ):
        super().__init__("QSpinnerClock", *children, **kwargs)
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_size is not None:
            self._props["size"] = ui_size

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_size(self):
        """Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)"""
        return self._props.get("size")

    @ui_size.setter
    def ui_size(self, value):
        self._set_prop("size", value)

    def _get_js_methods(self):
        return []


class QSpinnerAudio(Component):
    """
    Quasar Component: `QSpinnerAudio <https://v2.quasar.dev/vue-components/spinners>`__

    :param ui_color:
    :param ui_size: Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)
    """

    def __init__(
        self,
        *children,
        ui_color: Any | None = None,
        ui_size: str | None = None,
        **kwargs,
    ):
        super().__init__("QSpinnerAudio", *children, **kwargs)
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_size is not None:
            self._props["size"] = ui_size

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_size(self):
        """Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)"""
        return self._props.get("size")

    @ui_size.setter
    def ui_size(self, value):
        self._set_prop("size", value)

    def _get_js_methods(self):
        return []


class QSpinnerRadio(Component):
    """
    Quasar Component: `QSpinnerRadio <https://v2.quasar.dev/vue-components/spinners>`__

    :param ui_color:
    :param ui_size: Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)
    """

    def __init__(
        self,
        *children,
        ui_color: Any | None = None,
        ui_size: str | None = None,
        **kwargs,
    ):
        super().__init__("QSpinnerRadio", *children, **kwargs)
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_size is not None:
            self._props["size"] = ui_size

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_size(self):
        """Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)"""
        return self._props.get("size")

    @ui_size.setter
    def ui_size(self, value):
        self._set_prop("size", value)

    def _get_js_methods(self):
        return []


class QSpinnerIos(Component):
    """
    Quasar Component: `QSpinnerIos <https://v2.quasar.dev/vue-components/spinners>`__

    :param ui_color:
    :param ui_size: Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)
    """

    def __init__(
        self,
        *children,
        ui_color: Any | None = None,
        ui_size: str | None = None,
        **kwargs,
    ):
        super().__init__("QSpinnerIos", *children, **kwargs)
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_size is not None:
            self._props["size"] = ui_size

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_size(self):
        """Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)"""
        return self._props.get("size")

    @ui_size.setter
    def ui_size(self, value):
        self._set_prop("size", value)

    def _get_js_methods(self):
        return []


class QSpinnerBars(Component):
    """
    Quasar Component: `QSpinnerBars <https://v2.quasar.dev/vue-components/spinners>`__

    :param ui_color:
    :param ui_size: Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)
    """

    def __init__(
        self,
        *children,
        ui_color: Any | None = None,
        ui_size: str | None = None,
        **kwargs,
    ):
        super().__init__("QSpinnerBars", *children, **kwargs)
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_size is not None:
            self._props["size"] = ui_size

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_size(self):
        """Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)"""
        return self._props.get("size")

    @ui_size.setter
    def ui_size(self, value):
        self._set_prop("size", value)

    def _get_js_methods(self):
        return []


class QSpinnerDots(Component):
    """
    Quasar Component: `QSpinnerDots <https://v2.quasar.dev/vue-components/spinners>`__

    :param ui_color:
    :param ui_size: Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)
    """

    def __init__(
        self,
        *children,
        ui_color: Any | None = None,
        ui_size: str | None = None,
        **kwargs,
    ):
        super().__init__("QSpinnerDots", *children, **kwargs)
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_size is not None:
            self._props["size"] = ui_size

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_size(self):
        """Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)"""
        return self._props.get("size")

    @ui_size.setter
    def ui_size(self, value):
        self._set_prop("size", value)

    def _get_js_methods(self):
        return []


class QSpinnerCube(Component):
    """
    Quasar Component: `QSpinnerCube <https://v2.quasar.dev/vue-components/spinners>`__

    :param ui_color:
    :param ui_size: Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)
    """

    def __init__(
        self,
        *children,
        ui_color: Any | None = None,
        ui_size: str | None = None,
        **kwargs,
    ):
        super().__init__("QSpinnerCube", *children, **kwargs)
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_size is not None:
            self._props["size"] = ui_size

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_size(self):
        """Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)"""
        return self._props.get("size")

    @ui_size.setter
    def ui_size(self, value):
        self._set_prop("size", value)

    def _get_js_methods(self):
        return []


class QSpinnerBox(Component):
    """
    Quasar Component: `QSpinnerBox <https://v2.quasar.dev/vue-components/spinners>`__

    :param ui_color:
    :param ui_size: Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)
    """

    def __init__(
        self,
        *children,
        ui_color: Any | None = None,
        ui_size: str | None = None,
        **kwargs,
    ):
        super().__init__("QSpinnerBox", *children, **kwargs)
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_size is not None:
            self._props["size"] = ui_size

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_size(self):
        """Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)"""
        return self._props.get("size")

    @ui_size.setter
    def ui_size(self, value):
        self._set_prop("size", value)

    def _get_js_methods(self):
        return []


class QSpinnerBall(Component):
    """
    Quasar Component: `QSpinnerBall <https://v2.quasar.dev/vue-components/spinners>`__

    :param ui_color:
    :param ui_size: Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)
    """

    def __init__(
        self,
        *children,
        ui_color: Any | None = None,
        ui_size: str | None = None,
        **kwargs,
    ):
        super().__init__("QSpinnerBall", *children, **kwargs)
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_size is not None:
            self._props["size"] = ui_size

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_size(self):
        """Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)"""
        return self._props.get("size")

    @ui_size.setter
    def ui_size(self, value):
        self._set_prop("size", value)

    def _get_js_methods(self):
        return []


class QSpinnerOrbit(Component):
    """
    Quasar Component: `QSpinnerOrbit <https://v2.quasar.dev/vue-components/spinners>`__

    :param ui_color:
    :param ui_size: Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)
    """

    def __init__(
        self,
        *children,
        ui_color: Any | None = None,
        ui_size: str | None = None,
        **kwargs,
    ):
        super().__init__("QSpinnerOrbit", *children, **kwargs)
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_size is not None:
            self._props["size"] = ui_size

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_size(self):
        """Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)"""
        return self._props.get("size")

    @ui_size.setter
    def ui_size(self, value):
        self._set_prop("size", value)

    def _get_js_methods(self):
        return []


class QSpinnerComment(Component):
    """
    Quasar Component: `QSpinnerComment <https://v2.quasar.dev/vue-components/spinners>`__

    :param ui_color:
    :param ui_size: Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)
    """

    def __init__(
        self,
        *children,
        ui_color: Any | None = None,
        ui_size: str | None = None,
        **kwargs,
    ):
        super().__init__("QSpinnerComment", *children, **kwargs)
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_size is not None:
            self._props["size"] = ui_size

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_size(self):
        """Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)"""
        return self._props.get("size")

    @ui_size.setter
    def ui_size(self, value):
        self._set_prop("size", value)

    def _get_js_methods(self):
        return []


class QSpinnerRings(Component):
    """
    Quasar Component: `QSpinnerRings <https://v2.quasar.dev/vue-components/spinners>`__

    :param ui_color:
    :param ui_size: Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)
    """

    def __init__(
        self,
        *children,
        ui_color: Any | None = None,
        ui_size: str | None = None,
        **kwargs,
    ):
        super().__init__("QSpinnerRings", *children, **kwargs)
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_size is not None:
            self._props["size"] = ui_size

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_size(self):
        """Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)"""
        return self._props.get("size")

    @ui_size.setter
    def ui_size(self, value):
        self._set_prop("size", value)

    def _get_js_methods(self):
        return []


class QSpinner(Component):
    """
    Quasar Component: `QSpinner <https://v2.quasar.dev/vue-components/spinners>`__

    :param ui_thickness: Override value to use for stroke-width
    :param ui_color:
    :param ui_size: Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)
    """

    def __init__(
        self,
        *children,
        ui_thickness: float | None = None,
        ui_color: Any | None = None,
        ui_size: str | None = None,
        **kwargs,
    ):
        super().__init__("QSpinner", *children, **kwargs)
        if ui_thickness is not None:
            self._props["thickness"] = ui_thickness
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_size is not None:
            self._props["size"] = ui_size

    @property
    def ui_thickness(self):
        """Override value to use for stroke-width"""
        return self._props.get("thickness")

    @ui_thickness.setter
    def ui_thickness(self, value):
        self._set_prop("thickness", value)

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_size(self):
        """Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)"""
        return self._props.get("size")

    @ui_size.setter
    def ui_size(self, value):
        self._set_prop("size", value)

    def _get_js_methods(self):
        return []


class QSpinnerInfinity(Component):
    """
    Quasar Component: `QSpinnerInfinity <https://v2.quasar.dev/vue-components/spinners>`__

    :param ui_color:
    :param ui_size: Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)
    """

    def __init__(
        self,
        *children,
        ui_color: Any | None = None,
        ui_size: str | None = None,
        **kwargs,
    ):
        super().__init__("QSpinnerInfinity", *children, **kwargs)
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_size is not None:
            self._props["size"] = ui_size

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_size(self):
        """Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)"""
        return self._props.get("size")

    @ui_size.setter
    def ui_size(self, value):
        self._set_prop("size", value)

    def _get_js_methods(self):
        return []


class QSpinnerGears(Component):
    """
    Quasar Component: `QSpinnerGears <https://v2.quasar.dev/vue-components/spinners>`__

    :param ui_color:
    :param ui_size: Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)
    """

    def __init__(
        self,
        *children,
        ui_color: Any | None = None,
        ui_size: str | None = None,
        **kwargs,
    ):
        super().__init__("QSpinnerGears", *children, **kwargs)
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_size is not None:
            self._props["size"] = ui_size

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_size(self):
        """Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)"""
        return self._props.get("size")

    @ui_size.setter
    def ui_size(self, value):
        self._set_prop("size", value)

    def _get_js_methods(self):
        return []


class QSpinnerHearts(Component):
    """
    Quasar Component: `QSpinnerHearts <https://v2.quasar.dev/vue-components/spinners>`__

    :param ui_color:
    :param ui_size: Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)
    """

    def __init__(
        self,
        *children,
        ui_color: Any | None = None,
        ui_size: str | None = None,
        **kwargs,
    ):
        super().__init__("QSpinnerHearts", *children, **kwargs)
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_size is not None:
            self._props["size"] = ui_size

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_size(self):
        """Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)"""
        return self._props.get("size")

    @ui_size.setter
    def ui_size(self, value):
        self._set_prop("size", value)

    def _get_js_methods(self):
        return []


class QSpinnerPuff(Component):
    """
    Quasar Component: `QSpinnerPuff <https://v2.quasar.dev/vue-components/spinners>`__

    :param ui_color:
    :param ui_size: Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)
    """

    def __init__(
        self,
        *children,
        ui_color: Any | None = None,
        ui_size: str | None = None,
        **kwargs,
    ):
        super().__init__("QSpinnerPuff", *children, **kwargs)
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_size is not None:
            self._props["size"] = ui_size

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_size(self):
        """Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)"""
        return self._props.get("size")

    @ui_size.setter
    def ui_size(self, value):
        self._set_prop("size", value)

    def _get_js_methods(self):
        return []


class QSpinnerTail(Component):
    """
    Quasar Component: `QSpinnerTail <https://v2.quasar.dev/vue-components/spinners>`__

    :param ui_color:
    :param ui_size: Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)
    """

    def __init__(
        self,
        *children,
        ui_color: Any | None = None,
        ui_size: str | None = None,
        **kwargs,
    ):
        super().__init__("QSpinnerTail", *children, **kwargs)
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_size is not None:
            self._props["size"] = ui_size

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_size(self):
        """Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)"""
        return self._props.get("size")

    @ui_size.setter
    def ui_size(self, value):
        self._set_prop("size", value)

    def _get_js_methods(self):
        return []


class QSpinnerOval(Component):
    """
    Quasar Component: `QSpinnerOval <https://v2.quasar.dev/vue-components/spinners>`__

    :param ui_color:
    :param ui_size: Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)
    """

    def __init__(
        self,
        *children,
        ui_color: Any | None = None,
        ui_size: str | None = None,
        **kwargs,
    ):
        super().__init__("QSpinnerOval", *children, **kwargs)
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_size is not None:
            self._props["size"] = ui_size

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_size(self):
        """Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)"""
        return self._props.get("size")

    @ui_size.setter
    def ui_size(self, value):
        self._set_prop("size", value)

    def _get_js_methods(self):
        return []


class QSpinnerPie(Component):
    """
    Quasar Component: `QSpinnerPie <https://v2.quasar.dev/vue-components/spinners>`__

    :param ui_color:
    :param ui_size: Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)
    """

    def __init__(
        self,
        *children,
        ui_color: Any | None = None,
        ui_size: str | None = None,
        **kwargs,
    ):
        super().__init__("QSpinnerPie", *children, **kwargs)
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_size is not None:
            self._props["size"] = ui_size

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_size(self):
        """Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)"""
        return self._props.get("size")

    @ui_size.setter
    def ui_size(self, value):
        self._set_prop("size", value)

    def _get_js_methods(self):
        return []


class QSpinnerGrid(Component):
    """
    Quasar Component: `QSpinnerGrid <https://v2.quasar.dev/vue-components/spinners>`__

    :param ui_color:
    :param ui_size: Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)
    """

    def __init__(
        self,
        *children,
        ui_color: Any | None = None,
        ui_size: str | None = None,
        **kwargs,
    ):
        super().__init__("QSpinnerGrid", *children, **kwargs)
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_size is not None:
            self._props["size"] = ui_size

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_size(self):
        """Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)"""
        return self._props.get("size")

    @ui_size.setter
    def ui_size(self, value):
        self._set_prop("size", value)

    def _get_js_methods(self):
        return []


class QSpinnerFacebook(Component):
    """
    Quasar Component: `QSpinnerFacebook <https://v2.quasar.dev/vue-components/spinners>`__

    :param ui_color:
    :param ui_size: Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)
    """

    def __init__(
        self,
        *children,
        ui_color: Any | None = None,
        ui_size: str | None = None,
        **kwargs,
    ):
        super().__init__("QSpinnerFacebook", *children, **kwargs)
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_size is not None:
            self._props["size"] = ui_size

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_size(self):
        """Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)"""
        return self._props.get("size")

    @ui_size.setter
    def ui_size(self, value):
        self._set_prop("size", value)

    def _get_js_methods(self):
        return []


class QSplitter(Component):
    """
    Quasar Component: `QSplitter <https://v2.quasar.dev/vue-components/splitter>`__

    :param ui_model_value: Model of the component defining the size of first panel (or second if using reverse) in the unit specified (for '%' it's the split ratio percent - 0.0 < x < 100.0; for 'px' it's the size in px); Either use this property (along with a listener for 'update:modelValue' event) OR use v-model directive
    :param ui_reverse: Apply the model size to the second panel (by default it applies to the first)
    :param ui_unit: CSS unit for the model
    :param ui_emit_immediately: Emit model while user is panning on the separator
    :param ui_horizontal: Allows the splitter to split its two panels horizontally, instead of vertically
    :param ui_limits: An array of two values representing the minimum and maximum split size of the two panels; When 'px' unit is set then you can use Infinity as the second value to make it unbound on the other side; Default value: for '%' unit it is [10, 90], while for 'px' unit it is [50, Infinity]
    :param ui_disable:
    :param ui_before_class: Class definitions to be attributed to the 'before' panel
    :param ui_after_class: Class definitions to be attributed to the 'after' panel
    :param ui_separator_class: Class definitions to be attributed to the splitter separator
    :param ui_separator_style: Style definitions to be attributed to the splitter separator
    :param ui_dark: Applies a default lighter color on the separator; To be used when background is darker; Avoid using when you are overriding through separator-class or separator-style props
    """

    def __init__(
        self,
        *children,
        ui_model_value: float | None = None,
        ui_reverse: bool | None = None,
        ui_unit: str | None = None,
        ui_emit_immediately: bool | None = None,
        ui_horizontal: bool | None = None,
        ui_limits: list | None = None,
        ui_disable: Any | None = None,
        ui_before_class: str | list | dict | None = None,
        ui_after_class: str | list | dict | None = None,
        ui_separator_class: str | list | dict | None = None,
        ui_separator_style: str | list | dict | None = None,
        ui_dark: Any | None = None,
        **kwargs,
    ):
        super().__init__("QSplitter", *children, **kwargs)
        self.on("update:model-value", self.__update_model_value)

        if ui_model_value is not None:
            self._props["model-value"] = ui_model_value
        if ui_reverse is not None:
            self._props["reverse"] = ui_reverse
        if ui_unit is not None:
            self._props["unit"] = ui_unit
        if ui_emit_immediately is not None:
            self._props["emit-immediately"] = ui_emit_immediately
        if ui_horizontal is not None:
            self._props["horizontal"] = ui_horizontal
        if ui_limits is not None:
            self._props["limits"] = ui_limits
        if ui_disable is not None:
            self._props["disable"] = ui_disable
        if ui_before_class is not None:
            self._props["before-class"] = ui_before_class
        if ui_after_class is not None:
            self._props["after-class"] = ui_after_class
        if ui_separator_class is not None:
            self._props["separator-class"] = ui_separator_class
        if ui_separator_style is not None:
            self._props["separator-style"] = ui_separator_style
        if ui_dark is not None:
            self._props["dark"] = ui_dark

    def __update_model_value(self, event: Event):
        self._set_prop("model-value", event.value)

    @property
    def ui_model_value(self):
        """Model of the component defining the size of first panel (or second if using reverse) in the unit specified (for '%' it's the split ratio percent - 0.0 < x < 100.0; for 'px' it's the size in px); Either use this property (along with a listener for 'update:modelValue' event) OR use v-model directive"""
        return self._props.get("model-value")

    @ui_model_value.setter
    def ui_model_value(self, value):
        self._set_prop("model-value", value)

    @property
    def ui_reverse(self):
        """Apply the model size to the second panel (by default it applies to the first)"""
        return self._props.get("reverse")

    @ui_reverse.setter
    def ui_reverse(self, value):
        self._set_prop("reverse", value)

    @property
    def ui_unit(self):
        """CSS unit for the model"""
        return self._props.get("unit")

    @ui_unit.setter
    def ui_unit(self, value):
        self._set_prop("unit", value)

    @property
    def ui_emit_immediately(self):
        """Emit model while user is panning on the separator"""
        return self._props.get("emit-immediately")

    @ui_emit_immediately.setter
    def ui_emit_immediately(self, value):
        self._set_prop("emit-immediately", value)

    @property
    def ui_horizontal(self):
        """Allows the splitter to split its two panels horizontally, instead of vertically"""
        return self._props.get("horizontal")

    @ui_horizontal.setter
    def ui_horizontal(self, value):
        self._set_prop("horizontal", value)

    @property
    def ui_limits(self):
        """An array of two values representing the minimum and maximum split size of the two panels; When 'px' unit is set then you can use Infinity as the second value to make it unbound on the other side; Default value: for '%' unit it is [10, 90], while for 'px' unit it is [50, Infinity]"""
        return self._props.get("limits")

    @ui_limits.setter
    def ui_limits(self, value):
        self._set_prop("limits", value)

    @property
    def ui_disable(self):
        return self._props.get("disable")

    @ui_disable.setter
    def ui_disable(self, value):
        self._set_prop("disable", value)

    @property
    def ui_before_class(self):
        """Class definitions to be attributed to the 'before' panel"""
        return self._props.get("before-class")

    @ui_before_class.setter
    def ui_before_class(self, value):
        self._set_prop("before-class", value)

    @property
    def ui_after_class(self):
        """Class definitions to be attributed to the 'after' panel"""
        return self._props.get("after-class")

    @ui_after_class.setter
    def ui_after_class(self, value):
        self._set_prop("after-class", value)

    @property
    def ui_separator_class(self):
        """Class definitions to be attributed to the splitter separator"""
        return self._props.get("separator-class")

    @ui_separator_class.setter
    def ui_separator_class(self, value):
        self._set_prop("separator-class", value)

    @property
    def ui_separator_style(self):
        """Style definitions to be attributed to the splitter separator"""
        return self._props.get("separator-style")

    @ui_separator_style.setter
    def ui_separator_style(self, value):
        self._set_prop("separator-style", value)

    @property
    def ui_dark(self):
        """Applies a default lighter color on the separator; To be used when background is darker; Avoid using when you are overriding through separator-class or separator-style props"""
        return self._props.get("dark")

    @ui_dark.setter
    def ui_dark(self, value):
        self._set_prop("dark", value)

    @property
    def ui_slot_after(self):
        """Content of the panel on right/bottom"""
        return self.ui_slots.get("after", [])

    @ui_slot_after.setter
    def ui_slot_after(self, value):
        self._set_slot("after", value)

    @property
    def ui_slot_before(self):
        """Content of the panel on left/top"""
        return self.ui_slots.get("before", [])

    @ui_slot_before.setter
    def ui_slot_before(self, value):
        self._set_slot("before", value)

    @property
    def ui_slot_separator(self):
        """Content to be placed inside the separator; By default it is centered"""
        return self.ui_slots.get("separator", [])

    @ui_slot_separator.setter
    def ui_slot_separator(self, value):
        self._set_slot("separator", value)

    def on_update_model_value(self, handler: Callable, arg: object = None):
        """
        Emitted when component's model value changes; Is also used by v-model

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("update:model-value", handler, arg)

    def _get_js_methods(self):
        return []


class QStep(Component):
    """
    Quasar Component: `QStep <https://v2.quasar.dev/vue-components/stepper>`__

    :param ui_icon:
    :param ui_color:
    :param ui_title: Step title
    :param ui_caption: Step’s additional information that appears beneath the title
    :param ui_prefix: Step's prefix (max 2 characters) which replaces the icon if step does not has error, is being edited or is marked as done
    :param ui_done_icon: Icon name following Quasar convention; If 'none' (String) is used as value, then it will defer to prefix or the regular icon for this state; Make sure you have the icon library installed unless you are using 'img:' prefix
    :param ui_done_color:
    :param ui_active_icon: Icon name following Quasar convention; If 'none' (String) is used as value, then it will defer to prefix or the regular icon for this state; Make sure you have the icon library installed unless you are using 'img:' prefix
    :param ui_active_color:
    :param ui_error_icon: Icon name following Quasar convention; If 'none' (String) is used as value, then it will defer to prefix or the regular icon for this state; Make sure you have the icon library installed unless you are using 'img:' prefix
    :param ui_error_color:
    :param ui_header_nav: Allow navigation through the header
    :param ui_done: Mark the step as 'done'
    :param ui_error: Mark the step as having an error
    :param ui_name: Panel name
    :param ui_disable:
    """

    def __init__(
        self,
        *children,
        ui_icon: Any | None = None,
        ui_color: Any | None = None,
        ui_title: str | None = None,
        ui_caption: str | None = None,
        ui_prefix: str | float | None = None,
        ui_done_icon: Any | None = None,
        ui_done_color: Any | None = None,
        ui_active_icon: Any | None = None,
        ui_active_color: Any | None = None,
        ui_error_icon: Any | None = None,
        ui_error_color: Any | None = None,
        ui_header_nav: bool | None = None,
        ui_done: bool | None = None,
        ui_error: bool | None = None,
        ui_name: Any | None = None,
        ui_disable: Any | None = None,
        **kwargs,
    ):
        super().__init__("QStep", *children, **kwargs)
        if ui_icon is not None:
            self._props["icon"] = ui_icon
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_title is not None:
            self._props["title"] = ui_title
        if ui_caption is not None:
            self._props["caption"] = ui_caption
        if ui_prefix is not None:
            self._props["prefix"] = ui_prefix
        if ui_done_icon is not None:
            self._props["done-icon"] = ui_done_icon
        if ui_done_color is not None:
            self._props["done-color"] = ui_done_color
        if ui_active_icon is not None:
            self._props["active-icon"] = ui_active_icon
        if ui_active_color is not None:
            self._props["active-color"] = ui_active_color
        if ui_error_icon is not None:
            self._props["error-icon"] = ui_error_icon
        if ui_error_color is not None:
            self._props["error-color"] = ui_error_color
        if ui_header_nav is not None:
            self._props["header-nav"] = ui_header_nav
        if ui_done is not None:
            self._props["done"] = ui_done
        if ui_error is not None:
            self._props["error"] = ui_error
        if ui_name is not None:
            self._props["name"] = ui_name
        if ui_disable is not None:
            self._props["disable"] = ui_disable

    @property
    def ui_icon(self):
        return self._props.get("icon")

    @ui_icon.setter
    def ui_icon(self, value):
        self._set_prop("icon", value)

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_title(self):
        """Step title"""
        return self._props.get("title")

    @ui_title.setter
    def ui_title(self, value):
        self._set_prop("title", value)

    @property
    def ui_caption(self):
        """Step’s additional information that appears beneath the title"""
        return self._props.get("caption")

    @ui_caption.setter
    def ui_caption(self, value):
        self._set_prop("caption", value)

    @property
    def ui_prefix(self):
        """Step's prefix (max 2 characters) which replaces the icon if step does not has error, is being edited or is marked as done"""
        return self._props.get("prefix")

    @ui_prefix.setter
    def ui_prefix(self, value):
        self._set_prop("prefix", value)

    @property
    def ui_done_icon(self):
        """Icon name following Quasar convention; If 'none' (String) is used as value, then it will defer to prefix or the regular icon for this state; Make sure you have the icon library installed unless you are using 'img:' prefix"""
        return self._props.get("done-icon")

    @ui_done_icon.setter
    def ui_done_icon(self, value):
        self._set_prop("done-icon", value)

    @property
    def ui_done_color(self):
        return self._props.get("done-color")

    @ui_done_color.setter
    def ui_done_color(self, value):
        self._set_prop("done-color", value)

    @property
    def ui_active_icon(self):
        """Icon name following Quasar convention; If 'none' (String) is used as value, then it will defer to prefix or the regular icon for this state; Make sure you have the icon library installed unless you are using 'img:' prefix"""
        return self._props.get("active-icon")

    @ui_active_icon.setter
    def ui_active_icon(self, value):
        self._set_prop("active-icon", value)

    @property
    def ui_active_color(self):
        return self._props.get("active-color")

    @ui_active_color.setter
    def ui_active_color(self, value):
        self._set_prop("active-color", value)

    @property
    def ui_error_icon(self):
        """Icon name following Quasar convention; If 'none' (String) is used as value, then it will defer to prefix or the regular icon for this state; Make sure you have the icon library installed unless you are using 'img:' prefix"""
        return self._props.get("error-icon")

    @ui_error_icon.setter
    def ui_error_icon(self, value):
        self._set_prop("error-icon", value)

    @property
    def ui_error_color(self):
        return self._props.get("error-color")

    @ui_error_color.setter
    def ui_error_color(self, value):
        self._set_prop("error-color", value)

    @property
    def ui_header_nav(self):
        """Allow navigation through the header"""
        return self._props.get("header-nav")

    @ui_header_nav.setter
    def ui_header_nav(self, value):
        self._set_prop("header-nav", value)

    @property
    def ui_done(self):
        """Mark the step as 'done'"""
        return self._props.get("done")

    @ui_done.setter
    def ui_done(self, value):
        self._set_prop("done", value)

    @property
    def ui_error(self):
        """Mark the step as having an error"""
        return self._props.get("error")

    @ui_error.setter
    def ui_error(self, value):
        self._set_prop("error", value)

    @property
    def ui_name(self):
        """Panel name"""
        return self._props.get("name")

    @ui_name.setter
    def ui_name(self, value):
        self._set_prop("name", value)

    @property
    def ui_disable(self):
        return self._props.get("disable")

    @ui_disable.setter
    def ui_disable(self, value):
        self._set_prop("disable", value)

    def on_scroll(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("scroll", handler, arg)

    def _get_js_methods(self):
        return []

    def _get_my_wrapper_props(self):
        return super()._get_my_wrapper_props() | {
            "name": self.ui_name,
            "title": self.ui_title,
            "error": self.ui_error,
            "done": self.ui_done,
        }


class QStepperNavigation(Component):
    """
    Quasar Component: `QStepperNavigation <https://v2.quasar.dev/vue-components/stepper>`__

    """

    def __init__(self, *children, **kwargs):
        super().__init__("QStepperNavigation", *children, **kwargs)

    def _get_js_methods(self):
        return []


class QStepper(Component):
    """
    Quasar Component: `QStepper <https://v2.quasar.dev/vue-components/stepper>`__

    :param ui_dark:
    :param ui_flat:
    :param ui_bordered:
    :param ui_vertical: Default transitions and swipe actions will be on the vertical axis
    :param ui_alternative_labels: Use alternative labels - stacks the icon on top of the label (applies only to horizontal stepper)
    :param ui_header_nav: Allow navigation through the header
    :param ui_contracted: Hide header labels on narrow windows
    :param ui_inactive_icon:
    :param ui_inactive_color:
    :param ui_done_icon: Icon name following Quasar convention; If 'none' (String) is used as value, then it will defer to prefix or the regular icon for this state; Make sure you have the icon library installed unless you are using 'img:' prefix
    :param ui_done_color:
    :param ui_active_icon: Icon name following Quasar convention; If 'none' (String) is used as value, then it will defer to prefix or the regular icon for this state; Make sure you have the icon library installed unless you are using 'img:' prefix
    :param ui_active_color:
    :param ui_error_icon: Icon name following Quasar convention; If 'none' (String) is used as value, then it will defer to prefix or the regular icon for this state; Make sure you have the icon library installed unless you are using 'img:' prefix
    :param ui_error_color:
    :param ui_header_class: Class definitions to be attributed to the header
    :param ui_model_value: Model of the component defining the current panel's name; If a Number is used, it does not define the panel's index, but rather the panel's name which can also be an Integer; Either use this property (along with a listener for 'update:model-value' event) OR use the v-model directive.
    :param ui_keep_alive: Equivalent to using Vue's native <keep-alive> component on the content
    :param ui_keep_alive_include: Equivalent to using Vue's native include prop for <keep-alive>; Values must be valid Vue component names
    :param ui_keep_alive_exclude: Equivalent to using Vue's native exclude prop for <keep-alive>; Values must be valid Vue component names
    :param ui_keep_alive_max: Equivalent to using Vue's native max prop for <keep-alive>
    :param ui_animated: Enable transitions between panel (also see 'transition-prev' and 'transition-next' props)
    :param ui_infinite: Makes component appear as infinite (when reaching last panel, next one will become the first one)
    :param ui_swipeable: Enable swipe events (may interfere with content's touch/mouse events)
    :param ui_transition_prev: One of Quasar's embedded transitions (has effect only if 'animated' prop is set)
    :param ui_transition_next: One of Quasar's embedded transitions (has effect only if 'animated' prop is set)
    :param ui_transition_duration: Transition duration (in milliseconds, without unit)
    """

    def __init__(
        self,
        *children,
        ui_dark: Any | None = None,
        ui_flat: Any | None = None,
        ui_bordered: Any | None = None,
        ui_vertical: bool | None = None,
        ui_alternative_labels: bool | None = None,
        ui_header_nav: bool | None = None,
        ui_contracted: bool | None = None,
        ui_inactive_icon: Any | None = None,
        ui_inactive_color: Any | None = None,
        ui_done_icon: Any | None = None,
        ui_done_color: Any | None = None,
        ui_active_icon: Any | None = None,
        ui_active_color: Any | None = None,
        ui_error_icon: Any | None = None,
        ui_error_color: Any | None = None,
        ui_header_class: str | None = None,
        ui_model_value: Any | None = None,
        ui_keep_alive: bool | None = None,
        ui_keep_alive_include: str | list | re.Pattern | None = None,
        ui_keep_alive_exclude: str | list | re.Pattern | None = None,
        ui_keep_alive_max: float | None = None,
        ui_animated: bool | None = None,
        ui_infinite: bool | None = None,
        ui_swipeable: bool | None = None,
        ui_transition_prev: Any | None = None,
        ui_transition_next: Any | None = None,
        ui_transition_duration: str | float | None = None,
        **kwargs,
    ):
        super().__init__("QStepper", *children, **kwargs)
        self.on("update:model-value", self.__update_model_value)

        if ui_dark is not None:
            self._props["dark"] = ui_dark
        if ui_flat is not None:
            self._props["flat"] = ui_flat
        if ui_bordered is not None:
            self._props["bordered"] = ui_bordered
        if ui_vertical is not None:
            self._props["vertical"] = ui_vertical
        if ui_alternative_labels is not None:
            self._props["alternative-labels"] = ui_alternative_labels
        if ui_header_nav is not None:
            self._props["header-nav"] = ui_header_nav
        if ui_contracted is not None:
            self._props["contracted"] = ui_contracted
        if ui_inactive_icon is not None:
            self._props["inactive-icon"] = ui_inactive_icon
        if ui_inactive_color is not None:
            self._props["inactive-color"] = ui_inactive_color
        if ui_done_icon is not None:
            self._props["done-icon"] = ui_done_icon
        if ui_done_color is not None:
            self._props["done-color"] = ui_done_color
        if ui_active_icon is not None:
            self._props["active-icon"] = ui_active_icon
        if ui_active_color is not None:
            self._props["active-color"] = ui_active_color
        if ui_error_icon is not None:
            self._props["error-icon"] = ui_error_icon
        if ui_error_color is not None:
            self._props["error-color"] = ui_error_color
        if ui_header_class is not None:
            self._props["header-class"] = ui_header_class
        if ui_model_value is not None:
            self._props["model-value"] = ui_model_value
        if ui_keep_alive is not None:
            self._props["keep-alive"] = ui_keep_alive
        if ui_keep_alive_include is not None:
            self._props["keep-alive-include"] = ui_keep_alive_include
        if ui_keep_alive_exclude is not None:
            self._props["keep-alive-exclude"] = ui_keep_alive_exclude
        if ui_keep_alive_max is not None:
            self._props["keep-alive-max"] = ui_keep_alive_max
        if ui_animated is not None:
            self._props["animated"] = ui_animated
        if ui_infinite is not None:
            self._props["infinite"] = ui_infinite
        if ui_swipeable is not None:
            self._props["swipeable"] = ui_swipeable
        if ui_transition_prev is not None:
            self._props["transition-prev"] = ui_transition_prev
        if ui_transition_next is not None:
            self._props["transition-next"] = ui_transition_next
        if ui_transition_duration is not None:
            self._props["transition-duration"] = ui_transition_duration

    def __update_model_value(self, event: Event):
        self._set_prop("model-value", event.value)

    @property
    def ui_dark(self):
        return self._props.get("dark")

    @ui_dark.setter
    def ui_dark(self, value):
        self._set_prop("dark", value)

    @property
    def ui_flat(self):
        return self._props.get("flat")

    @ui_flat.setter
    def ui_flat(self, value):
        self._set_prop("flat", value)

    @property
    def ui_bordered(self):
        return self._props.get("bordered")

    @ui_bordered.setter
    def ui_bordered(self, value):
        self._set_prop("bordered", value)

    @property
    def ui_vertical(self):
        """Default transitions and swipe actions will be on the vertical axis"""
        return self._props.get("vertical")

    @ui_vertical.setter
    def ui_vertical(self, value):
        self._set_prop("vertical", value)

    @property
    def ui_alternative_labels(self):
        """Use alternative labels - stacks the icon on top of the label (applies only to horizontal stepper)"""
        return self._props.get("alternative-labels")

    @ui_alternative_labels.setter
    def ui_alternative_labels(self, value):
        self._set_prop("alternative-labels", value)

    @property
    def ui_header_nav(self):
        """Allow navigation through the header"""
        return self._props.get("header-nav")

    @ui_header_nav.setter
    def ui_header_nav(self, value):
        self._set_prop("header-nav", value)

    @property
    def ui_contracted(self):
        """Hide header labels on narrow windows"""
        return self._props.get("contracted")

    @ui_contracted.setter
    def ui_contracted(self, value):
        self._set_prop("contracted", value)

    @property
    def ui_inactive_icon(self):
        return self._props.get("inactive-icon")

    @ui_inactive_icon.setter
    def ui_inactive_icon(self, value):
        self._set_prop("inactive-icon", value)

    @property
    def ui_inactive_color(self):
        return self._props.get("inactive-color")

    @ui_inactive_color.setter
    def ui_inactive_color(self, value):
        self._set_prop("inactive-color", value)

    @property
    def ui_done_icon(self):
        """Icon name following Quasar convention; If 'none' (String) is used as value, then it will defer to prefix or the regular icon for this state; Make sure you have the icon library installed unless you are using 'img:' prefix"""
        return self._props.get("done-icon")

    @ui_done_icon.setter
    def ui_done_icon(self, value):
        self._set_prop("done-icon", value)

    @property
    def ui_done_color(self):
        return self._props.get("done-color")

    @ui_done_color.setter
    def ui_done_color(self, value):
        self._set_prop("done-color", value)

    @property
    def ui_active_icon(self):
        """Icon name following Quasar convention; If 'none' (String) is used as value, then it will defer to prefix or the regular icon for this state; Make sure you have the icon library installed unless you are using 'img:' prefix"""
        return self._props.get("active-icon")

    @ui_active_icon.setter
    def ui_active_icon(self, value):
        self._set_prop("active-icon", value)

    @property
    def ui_active_color(self):
        return self._props.get("active-color")

    @ui_active_color.setter
    def ui_active_color(self, value):
        self._set_prop("active-color", value)

    @property
    def ui_error_icon(self):
        """Icon name following Quasar convention; If 'none' (String) is used as value, then it will defer to prefix or the regular icon for this state; Make sure you have the icon library installed unless you are using 'img:' prefix"""
        return self._props.get("error-icon")

    @ui_error_icon.setter
    def ui_error_icon(self, value):
        self._set_prop("error-icon", value)

    @property
    def ui_error_color(self):
        return self._props.get("error-color")

    @ui_error_color.setter
    def ui_error_color(self, value):
        self._set_prop("error-color", value)

    @property
    def ui_header_class(self):
        """Class definitions to be attributed to the header"""
        return self._props.get("header-class")

    @ui_header_class.setter
    def ui_header_class(self, value):
        self._set_prop("header-class", value)

    @property
    def ui_model_value(self):
        """Model of the component defining the current panel's name; If a Number is used, it does not define the panel's index, but rather the panel's name which can also be an Integer; Either use this property (along with a listener for 'update:model-value' event) OR use the v-model directive."""
        return self._props.get("model-value")

    @ui_model_value.setter
    def ui_model_value(self, value):
        self._set_prop("model-value", value)

    @property
    def ui_keep_alive(self):
        """Equivalent to using Vue's native <keep-alive> component on the content"""
        return self._props.get("keep-alive")

    @ui_keep_alive.setter
    def ui_keep_alive(self, value):
        self._set_prop("keep-alive", value)

    @property
    def ui_keep_alive_include(self):
        """Equivalent to using Vue's native include prop for <keep-alive>; Values must be valid Vue component names"""
        return self._props.get("keep-alive-include")

    @ui_keep_alive_include.setter
    def ui_keep_alive_include(self, value):
        self._set_prop("keep-alive-include", value)

    @property
    def ui_keep_alive_exclude(self):
        """Equivalent to using Vue's native exclude prop for <keep-alive>; Values must be valid Vue component names"""
        return self._props.get("keep-alive-exclude")

    @ui_keep_alive_exclude.setter
    def ui_keep_alive_exclude(self, value):
        self._set_prop("keep-alive-exclude", value)

    @property
    def ui_keep_alive_max(self):
        """Equivalent to using Vue's native max prop for <keep-alive>"""
        return self._props.get("keep-alive-max")

    @ui_keep_alive_max.setter
    def ui_keep_alive_max(self, value):
        self._set_prop("keep-alive-max", value)

    @property
    def ui_animated(self):
        """Enable transitions between panel (also see 'transition-prev' and 'transition-next' props)"""
        return self._props.get("animated")

    @ui_animated.setter
    def ui_animated(self, value):
        self._set_prop("animated", value)

    @property
    def ui_infinite(self):
        """Makes component appear as infinite (when reaching last panel, next one will become the first one)"""
        return self._props.get("infinite")

    @ui_infinite.setter
    def ui_infinite(self, value):
        self._set_prop("infinite", value)

    @property
    def ui_swipeable(self):
        """Enable swipe events (may interfere with content's touch/mouse events)"""
        return self._props.get("swipeable")

    @ui_swipeable.setter
    def ui_swipeable(self, value):
        self._set_prop("swipeable", value)

    @property
    def ui_transition_prev(self):
        """One of Quasar's embedded transitions (has effect only if 'animated' prop is set)"""
        return self._props.get("transition-prev")

    @ui_transition_prev.setter
    def ui_transition_prev(self, value):
        self._set_prop("transition-prev", value)

    @property
    def ui_transition_next(self):
        """One of Quasar's embedded transitions (has effect only if 'animated' prop is set)"""
        return self._props.get("transition-next")

    @ui_transition_next.setter
    def ui_transition_next(self, value):
        self._set_prop("transition-next", value)

    @property
    def ui_transition_duration(self):
        """Transition duration (in milliseconds, without unit)"""
        return self._props.get("transition-duration")

    @ui_transition_duration.setter
    def ui_transition_duration(self, value):
        self._set_prop("transition-duration", value)

    @property
    def ui_slot_message(self):
        """Slot specific for putting a message on top of each step (if horizontal stepper) or above steps (if vertical); Suggestion: QBanner, div.q-pa-lg"""
        return self.ui_slots.get("message", [])

    @ui_slot_message.setter
    def ui_slot_message(self, value):
        self._set_slot("message", value)

    @property
    def ui_slot_navigation(self):
        """Slot specific for the global navigation; Suggestion: QStepperNavigation"""
        return self.ui_slots.get("navigation", [])

    @ui_slot_navigation.setter
    def ui_slot_navigation(self, value):
        self._set_slot("navigation", value)

    def on_before_transition(self, handler: Callable, arg: object = None):
        """
        Emitted before transitioning to a new panel

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("before-transition", handler, arg)

    def on_transition(self, handler: Callable, arg: object = None):
        """
        Emitted after component transitioned to a new panel

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("transition", handler, arg)

    def on_update_model_value(self, handler: Callable, arg: object = None):
        """
        Emitted when the component changes the model; This event isn't fired if the model is changed externally; Is also used by v-model

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("update:model-value", handler, arg)

    def ui_goTo(self, ui_panelName):
        """Go to specific panel"""
        kwargs = {}
        if ui_panelName is not None:
            kwargs["panelName"] = ui_panelName
        self._js_call_method("goTo", [kwargs])

    def ui_next(self):
        """Go to next panel"""
        self._js_call_method("next")

    def ui_previous(self):
        """Go to previous panel"""
        self._js_call_method("previous")

    def _get_js_methods(self):
        return ["goTo", "next", "previous"]


class QTabPanel(Component):
    """
    Quasar Component: `QTabPanel <https://v2.quasar.dev/vue-components/tab-panels>`__

    :param ui_name: Panel name
    :param ui_disable:
    """

    def __init__(
        self,
        *children,
        ui_name: Any | None = None,
        ui_disable: Any | None = None,
        **kwargs,
    ):
        super().__init__("QTabPanel", *children, **kwargs)
        if ui_name is not None:
            self._props["name"] = ui_name
        if ui_disable is not None:
            self._props["disable"] = ui_disable

    @property
    def ui_name(self):
        """Panel name"""
        return self._props.get("name")

    @ui_name.setter
    def ui_name(self, value):
        self._set_prop("name", value)

    @property
    def ui_disable(self):
        return self._props.get("disable")

    @ui_disable.setter
    def ui_disable(self, value):
        self._set_prop("disable", value)

    def _get_js_methods(self):
        return []

    def _get_my_wrapper_props(self):
        return super()._get_my_wrapper_props() | {"name": self.ui_name}


class QTabPanels(Component):
    """
    Quasar Component: `QTabPanels <https://v2.quasar.dev/vue-components/tab-panels>`__

    :param ui_dark:
    :param ui_model_value: Model of the component defining the current panel's name; If a Number is used, it does not define the panel's index, but rather the panel's name which can also be an Integer; Either use this property (along with a listener for 'update:model-value' event) OR use the v-model directive.
    :param ui_keep_alive: Equivalent to using Vue's native <keep-alive> component on the content
    :param ui_keep_alive_include: Equivalent to using Vue's native include prop for <keep-alive>; Values must be valid Vue component names
    :param ui_keep_alive_exclude: Equivalent to using Vue's native exclude prop for <keep-alive>; Values must be valid Vue component names
    :param ui_keep_alive_max: Equivalent to using Vue's native max prop for <keep-alive>
    :param ui_animated: Enable transitions between panel (also see 'transition-prev' and 'transition-next' props)
    :param ui_infinite: Makes component appear as infinite (when reaching last panel, next one will become the first one)
    :param ui_swipeable: Enable swipe events (may interfere with content's touch/mouse events)
    :param ui_vertical: Default transitions and swipe actions will be on the vertical axis
    :param ui_transition_prev: One of Quasar's embedded transitions (has effect only if 'animated' prop is set)
    :param ui_transition_next: One of Quasar's embedded transitions (has effect only if 'animated' prop is set)
    :param ui_transition_duration: Transition duration (in milliseconds, without unit)
    """

    def __init__(
        self,
        *children,
        ui_dark: Any | None = None,
        ui_model_value: Any | None = None,
        ui_keep_alive: bool | None = None,
        ui_keep_alive_include: str | list | re.Pattern | None = None,
        ui_keep_alive_exclude: str | list | re.Pattern | None = None,
        ui_keep_alive_max: float | None = None,
        ui_animated: bool | None = None,
        ui_infinite: bool | None = None,
        ui_swipeable: bool | None = None,
        ui_vertical: bool | None = None,
        ui_transition_prev: Any | None = None,
        ui_transition_next: Any | None = None,
        ui_transition_duration: str | float | None = None,
        **kwargs,
    ):
        super().__init__("QTabPanels", *children, **kwargs)
        self.on("update:model-value", self.__update_model_value)

        if ui_dark is not None:
            self._props["dark"] = ui_dark
        if ui_model_value is not None:
            self._props["model-value"] = ui_model_value
        if ui_keep_alive is not None:
            self._props["keep-alive"] = ui_keep_alive
        if ui_keep_alive_include is not None:
            self._props["keep-alive-include"] = ui_keep_alive_include
        if ui_keep_alive_exclude is not None:
            self._props["keep-alive-exclude"] = ui_keep_alive_exclude
        if ui_keep_alive_max is not None:
            self._props["keep-alive-max"] = ui_keep_alive_max
        if ui_animated is not None:
            self._props["animated"] = ui_animated
        if ui_infinite is not None:
            self._props["infinite"] = ui_infinite
        if ui_swipeable is not None:
            self._props["swipeable"] = ui_swipeable
        if ui_vertical is not None:
            self._props["vertical"] = ui_vertical
        if ui_transition_prev is not None:
            self._props["transition-prev"] = ui_transition_prev
        if ui_transition_next is not None:
            self._props["transition-next"] = ui_transition_next
        if ui_transition_duration is not None:
            self._props["transition-duration"] = ui_transition_duration

    def __update_model_value(self, event: Event):
        self._set_prop("model-value", event.value)

    @property
    def ui_dark(self):
        return self._props.get("dark")

    @ui_dark.setter
    def ui_dark(self, value):
        self._set_prop("dark", value)

    @property
    def ui_model_value(self):
        """Model of the component defining the current panel's name; If a Number is used, it does not define the panel's index, but rather the panel's name which can also be an Integer; Either use this property (along with a listener for 'update:model-value' event) OR use the v-model directive."""
        return self._props.get("model-value")

    @ui_model_value.setter
    def ui_model_value(self, value):
        self._set_prop("model-value", value)

    @property
    def ui_keep_alive(self):
        """Equivalent to using Vue's native <keep-alive> component on the content"""
        return self._props.get("keep-alive")

    @ui_keep_alive.setter
    def ui_keep_alive(self, value):
        self._set_prop("keep-alive", value)

    @property
    def ui_keep_alive_include(self):
        """Equivalent to using Vue's native include prop for <keep-alive>; Values must be valid Vue component names"""
        return self._props.get("keep-alive-include")

    @ui_keep_alive_include.setter
    def ui_keep_alive_include(self, value):
        self._set_prop("keep-alive-include", value)

    @property
    def ui_keep_alive_exclude(self):
        """Equivalent to using Vue's native exclude prop for <keep-alive>; Values must be valid Vue component names"""
        return self._props.get("keep-alive-exclude")

    @ui_keep_alive_exclude.setter
    def ui_keep_alive_exclude(self, value):
        self._set_prop("keep-alive-exclude", value)

    @property
    def ui_keep_alive_max(self):
        """Equivalent to using Vue's native max prop for <keep-alive>"""
        return self._props.get("keep-alive-max")

    @ui_keep_alive_max.setter
    def ui_keep_alive_max(self, value):
        self._set_prop("keep-alive-max", value)

    @property
    def ui_animated(self):
        """Enable transitions between panel (also see 'transition-prev' and 'transition-next' props)"""
        return self._props.get("animated")

    @ui_animated.setter
    def ui_animated(self, value):
        self._set_prop("animated", value)

    @property
    def ui_infinite(self):
        """Makes component appear as infinite (when reaching last panel, next one will become the first one)"""
        return self._props.get("infinite")

    @ui_infinite.setter
    def ui_infinite(self, value):
        self._set_prop("infinite", value)

    @property
    def ui_swipeable(self):
        """Enable swipe events (may interfere with content's touch/mouse events)"""
        return self._props.get("swipeable")

    @ui_swipeable.setter
    def ui_swipeable(self, value):
        self._set_prop("swipeable", value)

    @property
    def ui_vertical(self):
        """Default transitions and swipe actions will be on the vertical axis"""
        return self._props.get("vertical")

    @ui_vertical.setter
    def ui_vertical(self, value):
        self._set_prop("vertical", value)

    @property
    def ui_transition_prev(self):
        """One of Quasar's embedded transitions (has effect only if 'animated' prop is set)"""
        return self._props.get("transition-prev")

    @ui_transition_prev.setter
    def ui_transition_prev(self, value):
        self._set_prop("transition-prev", value)

    @property
    def ui_transition_next(self):
        """One of Quasar's embedded transitions (has effect only if 'animated' prop is set)"""
        return self._props.get("transition-next")

    @ui_transition_next.setter
    def ui_transition_next(self, value):
        self._set_prop("transition-next", value)

    @property
    def ui_transition_duration(self):
        """Transition duration (in milliseconds, without unit)"""
        return self._props.get("transition-duration")

    @ui_transition_duration.setter
    def ui_transition_duration(self, value):
        self._set_prop("transition-duration", value)

    def on_before_transition(self, handler: Callable, arg: object = None):
        """
        Emitted before transitioning to a new panel

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("before-transition", handler, arg)

    def on_transition(self, handler: Callable, arg: object = None):
        """
        Emitted after component transitioned to a new panel

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("transition", handler, arg)

    def on_update_model_value(self, handler: Callable, arg: object = None):
        """
        Emitted when the component changes the model; This event isn't fired if the model is changed externally; Is also used by v-model

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("update:model-value", handler, arg)

    def ui_goTo(self, ui_panelName):
        """Go to specific panel"""
        kwargs = {}
        if ui_panelName is not None:
            kwargs["panelName"] = ui_panelName
        self._js_call_method("goTo", [kwargs])

    def ui_next(self):
        """Go to next panel"""
        self._js_call_method("next")

    def ui_previous(self):
        """Go to previous panel"""
        self._js_call_method("previous")

    def _get_js_methods(self):
        return ["goTo", "next", "previous"]


class QTh(Component):
    """
    Quasar Component: `QTh <https://v2.quasar.dev/vue-components/table>`__

    :param ui_props: QTable's header column scoped slot property
    :param ui_auto_width: Tries to shrink header column width size; Useful for columns with a checkbox/radio/toggle
    """

    def __init__(
        self,
        *children,
        ui_props: dict | None = None,
        ui_auto_width: bool | None = None,
        **kwargs,
    ):
        super().__init__("QTh", *children, **kwargs)
        if ui_props is not None:
            self._props["props"] = ui_props
        if ui_auto_width is not None:
            self._props["auto-width"] = ui_auto_width

    @property
    def ui_props(self):
        """QTable's header column scoped slot property"""
        return self._props.get("props")

    @ui_props.setter
    def ui_props(self, value):
        self._set_prop("props", value)

    @property
    def ui_auto_width(self):
        """Tries to shrink header column width size; Useful for columns with a checkbox/radio/toggle"""
        return self._props.get("auto-width")

    @ui_auto_width.setter
    def ui_auto_width(self, value):
        self._set_prop("auto-width", value)

    def on_click(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("click.stop", handler, arg)

    def _get_js_methods(self):
        return []


class QTd(Component):
    """
    Quasar Component: `QTd <https://v2.quasar.dev/vue-components/table>`__

    :param ui_props: QTable's column scoped slot property
    :param ui_auto_width: Tries to shrink column width size; Useful for columns with a checkbox/radio/toggle
    :param ui_no_hover: Disable hover effect
    """

    def __init__(
        self,
        *children,
        ui_props: dict | None = None,
        ui_auto_width: bool | None = None,
        ui_no_hover: bool | None = None,
        **kwargs,
    ):
        super().__init__("QTd", *children, **kwargs)
        if ui_props is not None:
            self._props["props"] = ui_props
        if ui_auto_width is not None:
            self._props["auto-width"] = ui_auto_width
        if ui_no_hover is not None:
            self._props["no-hover"] = ui_no_hover

    @property
    def ui_props(self):
        """QTable's column scoped slot property"""
        return self._props.get("props")

    @ui_props.setter
    def ui_props(self, value):
        self._set_prop("props", value)

    @property
    def ui_auto_width(self):
        """Tries to shrink column width size; Useful for columns with a checkbox/radio/toggle"""
        return self._props.get("auto-width")

    @ui_auto_width.setter
    def ui_auto_width(self, value):
        self._set_prop("auto-width", value)

    @property
    def ui_no_hover(self):
        """Disable hover effect"""
        return self._props.get("no-hover")

    @ui_no_hover.setter
    def ui_no_hover(self, value):
        self._set_prop("no-hover", value)

    def _get_js_methods(self):
        return []


class QTable(Component):
    """
    Quasar Component: `QTable <https://v2.quasar.dev/vue-components/table>`__

    :param ui_rows: Rows of data to display
    :param ui_row_key: Property of each row that defines the unique key of each row (the result must be a primitive, not Object, Array, etc); The value of property must be string or a function taking a row and returning the desired (nested) key in the row; If supplying a function then for best performance, reference it from your scope and do not define it inline
    :param ui_virtual_scroll: Display data using QVirtualScroll (for non-grid mode only)
    :param ui_virtual_scroll_target:
    :param ui_virtual_scroll_slice_size: Minimum number of rows to render in the virtual list
    :param ui_virtual_scroll_slice_ratio_before: Ratio of number of rows in visible zone to render before it
    :param ui_virtual_scroll_slice_ratio_after: Ratio of number of rows in visible zone to render after it
    :param ui_virtual_scroll_item_size: Default size in pixels of a row; This value is used for rendering the initial table; Try to use a value close to the minimum size of a row; Default value: 48 (24 if dense)
    :param ui_virtual_scroll_sticky_size_start: Size in pixels of the sticky header (if using one); A correct value will improve scroll precision; Will be also used for non-virtual-scroll tables for fixing top alignment when using scrollTo method
    :param ui_virtual_scroll_sticky_size_end: Size in pixels of the sticky footer part (if using one); A correct value will improve scroll precision
    :param ui_table_colspan: The number of columns in the table (you need this if you use table-layout: fixed)
    :param ui_color:
    :param ui_icon_first_page: Icon name following Quasar convention for stepping to first page; Make sure you have the icon library installed unless you are using 'img:' prefix
    :param ui_icon_prev_page: Icon name following Quasar convention for stepping to previous page; Make sure you have the icon library installed unless you are using 'img:' prefix
    :param ui_icon_next_page: Icon name following Quasar convention for stepping to next page; Make sure you have the icon library installed unless you are using 'img:' prefix
    :param ui_icon_last_page: Icon name following Quasar convention for stepping to last page; Make sure you have the icon library installed unless you are using 'img:' prefix
    :param ui_grid: Display data as a grid instead of the default table
    :param ui_grid_header: Display header for grid-mode also
    :param ui_dense: Dense mode; Connect with $q.screen for responsive behavior
    :param ui_columns: The column definitions (Array of Objects)
    :param ui_visible_columns: Array of Strings defining column names ('name' property of each column from 'columns' prop definitions); Columns marked as 'required' are not affected by this property
    :param ui_loading: Put Table into 'loading' state; Notify the user something is happening behind the scenes
    :param ui_title: Table title
    :param ui_hide_header: Hide table header layer
    :param ui_hide_bottom: Hide table bottom layer regardless of what it has to display
    :param ui_hide_selected_banner: Hide the selected rows banner (if any)
    :param ui_hide_no_data: Hide the default no data bottom layer
    :param ui_hide_pagination: Hide the pagination controls at the bottom
    :param ui_dark:
    :param ui_flat:
    :param ui_bordered:
    :param ui_square:
    :param ui_separator: Use a separator/border between rows, columns or all cells
    :param ui_wrap_cells: Wrap text within table cells
    :param ui_binary_state_sort: Skip the third state (unsorted) when user toggles column sort direction
    :param ui_column_sort_order: Set column sort order: 'ad' (ascending-descending) or 'da' (descending-ascending); It gets applied to all columns unless a column has its own sortOrder specified in the 'columns' definition prop
    :param ui_no_data_label: Override default text to display when no data is available
    :param ui_no_results_label: Override default text to display when user filters the table and no matched results are found
    :param ui_loading_label: Override default text to display when table is in loading state (see 'loading' prop)
    :param ui_selected_rows_label: Text to display when user selected at least one row; For best performance, reference it from your scope and do not define it inline
    :param ui_rows_per_page_label: Text to override default rows per page label at bottom of table
    :param ui_pagination_label: Text to override default pagination label at bottom of table (unless 'pagination' scoped slot is used); For best performance, reference it from your scope and do not define it inline
    :param ui_table_style: CSS style to apply to native HTML <table> element's wrapper (which is a DIV)
    :param ui_table_class: CSS classes to apply to native HTML <table> element's wrapper (which is a DIV)
    :param ui_table_header_style: CSS style to apply to header of native HTML <table> (which is a TR)
    :param ui_table_header_class: CSS classes to apply to header of native HTML <table> (which is a TR)
    :param ui_card_container_style: CSS style to apply to the cards container (when in grid mode)
    :param ui_card_container_class: CSS classes to apply to the cards container (when in grid mode)
    :param ui_card_style: CSS style to apply to the card (when in grid mode) or container card (when not in grid mode)
    :param ui_card_class: CSS classes to apply to the card (when in grid mode) or container card (when not in grid mode)
    :param ui_title_class: CSS classes to apply to the title (if using 'title' prop)
    :param ui_filter: String/Object to filter table with; When using an Object it requires 'filter-method' to also be specified since it will be a custom filtering
    :param ui_filter_method: The actual filtering mechanism; For best performance, reference it from your scope and do not define it inline
    :param ui_pagination: Pagination object; You can also use the 'v-model:pagination' for synching; When not synching it simply initializes the pagination on first render
    :param ui_rows_per_page_options: Options for user to pick (Numbers); Number 0 means 'Show all rows in one page'
    :param ui_selection: Selection type
    :param ui_selected: Keeps the user selection array
    :param ui_expanded: Keeps the array with expanded rows keys
    :param ui_sort_method: The actual sort mechanism. Function (rows, sortBy, descending) => sorted rows; For best performance, reference it from your scope and do not define it inline
    :param ui_fullscreen: Fullscreen mode
    :param ui_no_route_fullscreen_exit: Changing route app won't exit fullscreen
    """

    def __init__(
        self,
        *children,
        ui_rows: list | None = None,
        ui_row_key: str | Callable | None = None,
        ui_virtual_scroll: bool | None = None,
        ui_virtual_scroll_target: Any | None = None,
        ui_virtual_scroll_slice_size: float | str | None = None,
        ui_virtual_scroll_slice_ratio_before: float | str | None = None,
        ui_virtual_scroll_slice_ratio_after: float | str | None = None,
        ui_virtual_scroll_item_size: float | str | None = None,
        ui_virtual_scroll_sticky_size_start: float | str | None = None,
        ui_virtual_scroll_sticky_size_end: float | str | None = None,
        ui_table_colspan: float | str | None = None,
        ui_color: Any | None = None,
        ui_icon_first_page: Any | None = None,
        ui_icon_prev_page: Any | None = None,
        ui_icon_next_page: Any | None = None,
        ui_icon_last_page: Any | None = None,
        ui_grid: bool | None = None,
        ui_grid_header: bool | None = None,
        ui_dense: Any | None = None,
        ui_columns: list | None = None,
        ui_visible_columns: list | None = None,
        ui_loading: bool | None = None,
        ui_title: str | None = None,
        ui_hide_header: bool | None = None,
        ui_hide_bottom: bool | None = None,
        ui_hide_selected_banner: bool | None = None,
        ui_hide_no_data: bool | None = None,
        ui_hide_pagination: bool | None = None,
        ui_dark: Any | None = None,
        ui_flat: Any | None = None,
        ui_bordered: Any | None = None,
        ui_square: Any | None = None,
        ui_separator: str | None = None,
        ui_wrap_cells: bool | None = None,
        ui_binary_state_sort: bool | None = None,
        ui_column_sort_order: str | None = None,
        ui_no_data_label: str | None = None,
        ui_no_results_label: str | None = None,
        ui_loading_label: str | None = None,
        ui_selected_rows_label: Callable | None = None,
        ui_rows_per_page_label: str | None = None,
        ui_pagination_label: Callable | None = None,
        ui_table_style: str | list | dict | None = None,
        ui_table_class: str | list | dict | None = None,
        ui_table_header_style: str | list | dict | None = None,
        ui_table_header_class: str | list | dict | None = None,
        ui_card_container_style: str | list | dict | None = None,
        ui_card_container_class: str | list | dict | None = None,
        ui_card_style: str | list | dict | None = None,
        ui_card_class: str | list | dict | None = None,
        ui_title_class: str | list | dict | None = None,
        ui_filter: str | dict | None = None,
        ui_filter_method: Callable | None = None,
        ui_pagination: dict | None = None,
        ui_rows_per_page_options: list | None = None,
        ui_selection: str | None = None,
        ui_selected: list | None = None,
        ui_expanded: list | None = None,
        ui_sort_method: Callable | None = None,
        ui_fullscreen: bool | None = None,
        ui_no_route_fullscreen_exit: bool | None = None,
        **kwargs,
    ):
        super().__init__("QTable", *children, **kwargs)
        if ui_rows is not None:
            self._props["rows"] = ui_rows
        if ui_row_key is not None:
            self._props["row-key"] = ui_row_key
        if ui_virtual_scroll is not None:
            self._props["virtual-scroll"] = ui_virtual_scroll
        if ui_virtual_scroll_target is not None:
            self._props["virtual-scroll-target"] = ui_virtual_scroll_target
        if ui_virtual_scroll_slice_size is not None:
            self._props["virtual-scroll-slice-size"] = (
                ui_virtual_scroll_slice_size
            )
        if ui_virtual_scroll_slice_ratio_before is not None:
            self._props["virtual-scroll-slice-ratio-before"] = (
                ui_virtual_scroll_slice_ratio_before
            )
        if ui_virtual_scroll_slice_ratio_after is not None:
            self._props["virtual-scroll-slice-ratio-after"] = (
                ui_virtual_scroll_slice_ratio_after
            )
        if ui_virtual_scroll_item_size is not None:
            self._props["virtual-scroll-item-size"] = (
                ui_virtual_scroll_item_size
            )
        if ui_virtual_scroll_sticky_size_start is not None:
            self._props["virtual-scroll-sticky-size-start"] = (
                ui_virtual_scroll_sticky_size_start
            )
        if ui_virtual_scroll_sticky_size_end is not None:
            self._props["virtual-scroll-sticky-size-end"] = (
                ui_virtual_scroll_sticky_size_end
            )
        if ui_table_colspan is not None:
            self._props["table-colspan"] = ui_table_colspan
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_icon_first_page is not None:
            self._props["icon-first-page"] = ui_icon_first_page
        if ui_icon_prev_page is not None:
            self._props["icon-prev-page"] = ui_icon_prev_page
        if ui_icon_next_page is not None:
            self._props["icon-next-page"] = ui_icon_next_page
        if ui_icon_last_page is not None:
            self._props["icon-last-page"] = ui_icon_last_page
        if ui_grid is not None:
            self._props["grid"] = ui_grid
        if ui_grid_header is not None:
            self._props["grid-header"] = ui_grid_header
        if ui_dense is not None:
            self._props["dense"] = ui_dense
        if ui_columns is not None:
            self._props["columns"] = ui_columns
        if ui_visible_columns is not None:
            self._props["visible-columns"] = ui_visible_columns
        if ui_loading is not None:
            self._props["loading"] = ui_loading
        if ui_title is not None:
            self._props["title"] = ui_title
        if ui_hide_header is not None:
            self._props["hide-header"] = ui_hide_header
        if ui_hide_bottom is not None:
            self._props["hide-bottom"] = ui_hide_bottom
        if ui_hide_selected_banner is not None:
            self._props["hide-selected-banner"] = ui_hide_selected_banner
        if ui_hide_no_data is not None:
            self._props["hide-no-data"] = ui_hide_no_data
        if ui_hide_pagination is not None:
            self._props["hide-pagination"] = ui_hide_pagination
        if ui_dark is not None:
            self._props["dark"] = ui_dark
        if ui_flat is not None:
            self._props["flat"] = ui_flat
        if ui_bordered is not None:
            self._props["bordered"] = ui_bordered
        if ui_square is not None:
            self._props["square"] = ui_square
        if ui_separator is not None:
            self._props["separator"] = ui_separator
        if ui_wrap_cells is not None:
            self._props["wrap-cells"] = ui_wrap_cells
        if ui_binary_state_sort is not None:
            self._props["binary-state-sort"] = ui_binary_state_sort
        if ui_column_sort_order is not None:
            self._props["column-sort-order"] = ui_column_sort_order
        if ui_no_data_label is not None:
            self._props["no-data-label"] = ui_no_data_label
        if ui_no_results_label is not None:
            self._props["no-results-label"] = ui_no_results_label
        if ui_loading_label is not None:
            self._props["loading-label"] = ui_loading_label
        if ui_selected_rows_label is not None:
            self._props["selected-rows-label"] = ui_selected_rows_label
        if ui_rows_per_page_label is not None:
            self._props["rows-per-page-label"] = ui_rows_per_page_label
        if ui_pagination_label is not None:
            self._props["pagination-label"] = ui_pagination_label
        if ui_table_style is not None:
            self._props["table-style"] = ui_table_style
        if ui_table_class is not None:
            self._props["table-class"] = ui_table_class
        if ui_table_header_style is not None:
            self._props["table-header-style"] = ui_table_header_style
        if ui_table_header_class is not None:
            self._props["table-header-class"] = ui_table_header_class
        if ui_card_container_style is not None:
            self._props["card-container-style"] = ui_card_container_style
        if ui_card_container_class is not None:
            self._props["card-container-class"] = ui_card_container_class
        if ui_card_style is not None:
            self._props["card-style"] = ui_card_style
        if ui_card_class is not None:
            self._props["card-class"] = ui_card_class
        if ui_title_class is not None:
            self._props["title-class"] = ui_title_class
        if ui_filter is not None:
            self._props["filter"] = ui_filter
        if ui_filter_method is not None:
            self._props["filter-method"] = ui_filter_method
        if ui_pagination is not None:
            self._props["pagination"] = ui_pagination
        if ui_rows_per_page_options is not None:
            self._props["rows-per-page-options"] = ui_rows_per_page_options
        if ui_selection is not None:
            self._props["selection"] = ui_selection
        if ui_selected is not None:
            self._props["selected"] = ui_selected
        if ui_expanded is not None:
            self._props["expanded"] = ui_expanded
        if ui_sort_method is not None:
            self._props["sort-method"] = ui_sort_method
        if ui_fullscreen is not None:
            self._props["fullscreen"] = ui_fullscreen
        if ui_no_route_fullscreen_exit is not None:
            self._props["no-route-fullscreen-exit"] = (
                ui_no_route_fullscreen_exit
            )

    @property
    def ui_rows(self):
        """Rows of data to display"""
        return self._props.get("rows")

    @ui_rows.setter
    def ui_rows(self, value):
        self._set_prop("rows", value)

    @property
    def ui_row_key(self):
        """Property of each row that defines the unique key of each row (the result must be a primitive, not Object, Array, etc); The value of property must be string or a function taking a row and returning the desired (nested) key in the row; If supplying a function then for best performance, reference it from your scope and do not define it inline"""
        return self._props.get("row-key")

    @ui_row_key.setter
    def ui_row_key(self, value):
        self._set_prop("row-key", value)

    @property
    def ui_virtual_scroll(self):
        """Display data using QVirtualScroll (for non-grid mode only)"""
        return self._props.get("virtual-scroll")

    @ui_virtual_scroll.setter
    def ui_virtual_scroll(self, value):
        self._set_prop("virtual-scroll", value)

    @property
    def ui_virtual_scroll_target(self):
        return self._props.get("virtual-scroll-target")

    @ui_virtual_scroll_target.setter
    def ui_virtual_scroll_target(self, value):
        self._set_prop("virtual-scroll-target", value)

    @property
    def ui_virtual_scroll_slice_size(self):
        """Minimum number of rows to render in the virtual list"""
        return self._props.get("virtual-scroll-slice-size")

    @ui_virtual_scroll_slice_size.setter
    def ui_virtual_scroll_slice_size(self, value):
        self._set_prop("virtual-scroll-slice-size", value)

    @property
    def ui_virtual_scroll_slice_ratio_before(self):
        """Ratio of number of rows in visible zone to render before it"""
        return self._props.get("virtual-scroll-slice-ratio-before")

    @ui_virtual_scroll_slice_ratio_before.setter
    def ui_virtual_scroll_slice_ratio_before(self, value):
        self._set_prop("virtual-scroll-slice-ratio-before", value)

    @property
    def ui_virtual_scroll_slice_ratio_after(self):
        """Ratio of number of rows in visible zone to render after it"""
        return self._props.get("virtual-scroll-slice-ratio-after")

    @ui_virtual_scroll_slice_ratio_after.setter
    def ui_virtual_scroll_slice_ratio_after(self, value):
        self._set_prop("virtual-scroll-slice-ratio-after", value)

    @property
    def ui_virtual_scroll_item_size(self):
        """Default size in pixels of a row; This value is used for rendering the initial table; Try to use a value close to the minimum size of a row; Default value: 48 (24 if dense)"""
        return self._props.get("virtual-scroll-item-size")

    @ui_virtual_scroll_item_size.setter
    def ui_virtual_scroll_item_size(self, value):
        self._set_prop("virtual-scroll-item-size", value)

    @property
    def ui_virtual_scroll_sticky_size_start(self):
        """Size in pixels of the sticky header (if using one); A correct value will improve scroll precision; Will be also used for non-virtual-scroll tables for fixing top alignment when using scrollTo method"""
        return self._props.get("virtual-scroll-sticky-size-start")

    @ui_virtual_scroll_sticky_size_start.setter
    def ui_virtual_scroll_sticky_size_start(self, value):
        self._set_prop("virtual-scroll-sticky-size-start", value)

    @property
    def ui_virtual_scroll_sticky_size_end(self):
        """Size in pixels of the sticky footer part (if using one); A correct value will improve scroll precision"""
        return self._props.get("virtual-scroll-sticky-size-end")

    @ui_virtual_scroll_sticky_size_end.setter
    def ui_virtual_scroll_sticky_size_end(self, value):
        self._set_prop("virtual-scroll-sticky-size-end", value)

    @property
    def ui_table_colspan(self):
        """The number of columns in the table (you need this if you use table-layout: fixed)"""
        return self._props.get("table-colspan")

    @ui_table_colspan.setter
    def ui_table_colspan(self, value):
        self._set_prop("table-colspan", value)

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_icon_first_page(self):
        """Icon name following Quasar convention for stepping to first page; Make sure you have the icon library installed unless you are using 'img:' prefix"""
        return self._props.get("icon-first-page")

    @ui_icon_first_page.setter
    def ui_icon_first_page(self, value):
        self._set_prop("icon-first-page", value)

    @property
    def ui_icon_prev_page(self):
        """Icon name following Quasar convention for stepping to previous page; Make sure you have the icon library installed unless you are using 'img:' prefix"""
        return self._props.get("icon-prev-page")

    @ui_icon_prev_page.setter
    def ui_icon_prev_page(self, value):
        self._set_prop("icon-prev-page", value)

    @property
    def ui_icon_next_page(self):
        """Icon name following Quasar convention for stepping to next page; Make sure you have the icon library installed unless you are using 'img:' prefix"""
        return self._props.get("icon-next-page")

    @ui_icon_next_page.setter
    def ui_icon_next_page(self, value):
        self._set_prop("icon-next-page", value)

    @property
    def ui_icon_last_page(self):
        """Icon name following Quasar convention for stepping to last page; Make sure you have the icon library installed unless you are using 'img:' prefix"""
        return self._props.get("icon-last-page")

    @ui_icon_last_page.setter
    def ui_icon_last_page(self, value):
        self._set_prop("icon-last-page", value)

    @property
    def ui_grid(self):
        """Display data as a grid instead of the default table"""
        return self._props.get("grid")

    @ui_grid.setter
    def ui_grid(self, value):
        self._set_prop("grid", value)

    @property
    def ui_grid_header(self):
        """Display header for grid-mode also"""
        return self._props.get("grid-header")

    @ui_grid_header.setter
    def ui_grid_header(self, value):
        self._set_prop("grid-header", value)

    @property
    def ui_dense(self):
        """Dense mode; Connect with $q.screen for responsive behavior"""
        return self._props.get("dense")

    @ui_dense.setter
    def ui_dense(self, value):
        self._set_prop("dense", value)

    @property
    def ui_columns(self):
        """The column definitions (Array of Objects)"""
        return self._props.get("columns")

    @ui_columns.setter
    def ui_columns(self, value):
        self._set_prop("columns", value)

    @property
    def ui_visible_columns(self):
        """Array of Strings defining column names ('name' property of each column from 'columns' prop definitions); Columns marked as 'required' are not affected by this property"""
        return self._props.get("visible-columns")

    @ui_visible_columns.setter
    def ui_visible_columns(self, value):
        self._set_prop("visible-columns", value)

    @property
    def ui_loading(self):
        """Put Table into 'loading' state; Notify the user something is happening behind the scenes"""
        return self._props.get("loading")

    @ui_loading.setter
    def ui_loading(self, value):
        self._set_prop("loading", value)

    @property
    def ui_title(self):
        """Table title"""
        return self._props.get("title")

    @ui_title.setter
    def ui_title(self, value):
        self._set_prop("title", value)

    @property
    def ui_hide_header(self):
        """Hide table header layer"""
        return self._props.get("hide-header")

    @ui_hide_header.setter
    def ui_hide_header(self, value):
        self._set_prop("hide-header", value)

    @property
    def ui_hide_bottom(self):
        """Hide table bottom layer regardless of what it has to display"""
        return self._props.get("hide-bottom")

    @ui_hide_bottom.setter
    def ui_hide_bottom(self, value):
        self._set_prop("hide-bottom", value)

    @property
    def ui_hide_selected_banner(self):
        """Hide the selected rows banner (if any)"""
        return self._props.get("hide-selected-banner")

    @ui_hide_selected_banner.setter
    def ui_hide_selected_banner(self, value):
        self._set_prop("hide-selected-banner", value)

    @property
    def ui_hide_no_data(self):
        """Hide the default no data bottom layer"""
        return self._props.get("hide-no-data")

    @ui_hide_no_data.setter
    def ui_hide_no_data(self, value):
        self._set_prop("hide-no-data", value)

    @property
    def ui_hide_pagination(self):
        """Hide the pagination controls at the bottom"""
        return self._props.get("hide-pagination")

    @ui_hide_pagination.setter
    def ui_hide_pagination(self, value):
        self._set_prop("hide-pagination", value)

    @property
    def ui_dark(self):
        return self._props.get("dark")

    @ui_dark.setter
    def ui_dark(self, value):
        self._set_prop("dark", value)

    @property
    def ui_flat(self):
        return self._props.get("flat")

    @ui_flat.setter
    def ui_flat(self, value):
        self._set_prop("flat", value)

    @property
    def ui_bordered(self):
        return self._props.get("bordered")

    @ui_bordered.setter
    def ui_bordered(self, value):
        self._set_prop("bordered", value)

    @property
    def ui_square(self):
        return self._props.get("square")

    @ui_square.setter
    def ui_square(self, value):
        self._set_prop("square", value)

    @property
    def ui_separator(self):
        """Use a separator/border between rows, columns or all cells"""
        return self._props.get("separator")

    @ui_separator.setter
    def ui_separator(self, value):
        self._set_prop("separator", value)

    @property
    def ui_wrap_cells(self):
        """Wrap text within table cells"""
        return self._props.get("wrap-cells")

    @ui_wrap_cells.setter
    def ui_wrap_cells(self, value):
        self._set_prop("wrap-cells", value)

    @property
    def ui_binary_state_sort(self):
        """Skip the third state (unsorted) when user toggles column sort direction"""
        return self._props.get("binary-state-sort")

    @ui_binary_state_sort.setter
    def ui_binary_state_sort(self, value):
        self._set_prop("binary-state-sort", value)

    @property
    def ui_column_sort_order(self):
        """Set column sort order: 'ad' (ascending-descending) or 'da' (descending-ascending); It gets applied to all columns unless a column has its own sortOrder specified in the 'columns' definition prop"""
        return self._props.get("column-sort-order")

    @ui_column_sort_order.setter
    def ui_column_sort_order(self, value):
        self._set_prop("column-sort-order", value)

    @property
    def ui_no_data_label(self):
        """Override default text to display when no data is available"""
        return self._props.get("no-data-label")

    @ui_no_data_label.setter
    def ui_no_data_label(self, value):
        self._set_prop("no-data-label", value)

    @property
    def ui_no_results_label(self):
        """Override default text to display when user filters the table and no matched results are found"""
        return self._props.get("no-results-label")

    @ui_no_results_label.setter
    def ui_no_results_label(self, value):
        self._set_prop("no-results-label", value)

    @property
    def ui_loading_label(self):
        """Override default text to display when table is in loading state (see 'loading' prop)"""
        return self._props.get("loading-label")

    @ui_loading_label.setter
    def ui_loading_label(self, value):
        self._set_prop("loading-label", value)

    @property
    def ui_selected_rows_label(self):
        """Text to display when user selected at least one row; For best performance, reference it from your scope and do not define it inline"""
        return self._props.get("selected-rows-label")

    @ui_selected_rows_label.setter
    def ui_selected_rows_label(self, value):
        self._set_prop("selected-rows-label", value)

    @property
    def ui_rows_per_page_label(self):
        """Text to override default rows per page label at bottom of table"""
        return self._props.get("rows-per-page-label")

    @ui_rows_per_page_label.setter
    def ui_rows_per_page_label(self, value):
        self._set_prop("rows-per-page-label", value)

    @property
    def ui_pagination_label(self):
        """Text to override default pagination label at bottom of table (unless 'pagination' scoped slot is used); For best performance, reference it from your scope and do not define it inline"""
        return self._props.get("pagination-label")

    @ui_pagination_label.setter
    def ui_pagination_label(self, value):
        self._set_prop("pagination-label", value)

    @property
    def ui_table_style(self):
        """CSS style to apply to native HTML <table> element's wrapper (which is a DIV)"""
        return self._props.get("table-style")

    @ui_table_style.setter
    def ui_table_style(self, value):
        self._set_prop("table-style", value)

    @property
    def ui_table_class(self):
        """CSS classes to apply to native HTML <table> element's wrapper (which is a DIV)"""
        return self._props.get("table-class")

    @ui_table_class.setter
    def ui_table_class(self, value):
        self._set_prop("table-class", value)

    @property
    def ui_table_header_style(self):
        """CSS style to apply to header of native HTML <table> (which is a TR)"""
        return self._props.get("table-header-style")

    @ui_table_header_style.setter
    def ui_table_header_style(self, value):
        self._set_prop("table-header-style", value)

    @property
    def ui_table_header_class(self):
        """CSS classes to apply to header of native HTML <table> (which is a TR)"""
        return self._props.get("table-header-class")

    @ui_table_header_class.setter
    def ui_table_header_class(self, value):
        self._set_prop("table-header-class", value)

    @property
    def ui_card_container_style(self):
        """CSS style to apply to the cards container (when in grid mode)"""
        return self._props.get("card-container-style")

    @ui_card_container_style.setter
    def ui_card_container_style(self, value):
        self._set_prop("card-container-style", value)

    @property
    def ui_card_container_class(self):
        """CSS classes to apply to the cards container (when in grid mode)"""
        return self._props.get("card-container-class")

    @ui_card_container_class.setter
    def ui_card_container_class(self, value):
        self._set_prop("card-container-class", value)

    @property
    def ui_card_style(self):
        """CSS style to apply to the card (when in grid mode) or container card (when not in grid mode)"""
        return self._props.get("card-style")

    @ui_card_style.setter
    def ui_card_style(self, value):
        self._set_prop("card-style", value)

    @property
    def ui_card_class(self):
        """CSS classes to apply to the card (when in grid mode) or container card (when not in grid mode)"""
        return self._props.get("card-class")

    @ui_card_class.setter
    def ui_card_class(self, value):
        self._set_prop("card-class", value)

    @property
    def ui_title_class(self):
        """CSS classes to apply to the title (if using 'title' prop)"""
        return self._props.get("title-class")

    @ui_title_class.setter
    def ui_title_class(self, value):
        self._set_prop("title-class", value)

    @property
    def ui_filter(self):
        """String/Object to filter table with; When using an Object it requires 'filter-method' to also be specified since it will be a custom filtering"""
        return self._props.get("filter")

    @ui_filter.setter
    def ui_filter(self, value):
        self._set_prop("filter", value)

    @property
    def ui_filter_method(self):
        """The actual filtering mechanism; For best performance, reference it from your scope and do not define it inline"""
        return self._props.get("filter-method")

    @ui_filter_method.setter
    def ui_filter_method(self, value):
        self._set_prop("filter-method", value)

    @property
    def ui_pagination(self):
        """Pagination object; You can also use the 'v-model:pagination' for synching; When not synching it simply initializes the pagination on first render"""
        return self._props.get("pagination")

    @ui_pagination.setter
    def ui_pagination(self, value):
        self._set_prop("pagination", value)

    @property
    def ui_rows_per_page_options(self):
        """Options for user to pick (Numbers); Number 0 means 'Show all rows in one page'"""
        return self._props.get("rows-per-page-options")

    @ui_rows_per_page_options.setter
    def ui_rows_per_page_options(self, value):
        self._set_prop("rows-per-page-options", value)

    @property
    def ui_selection(self):
        """Selection type"""
        return self._props.get("selection")

    @ui_selection.setter
    def ui_selection(self, value):
        self._set_prop("selection", value)

    @property
    def ui_selected(self):
        """Keeps the user selection array"""
        return self._props.get("selected")

    @ui_selected.setter
    def ui_selected(self, value):
        self._set_prop("selected", value)

    @property
    def ui_expanded(self):
        """Keeps the array with expanded rows keys"""
        return self._props.get("expanded")

    @ui_expanded.setter
    def ui_expanded(self, value):
        self._set_prop("expanded", value)

    @property
    def ui_sort_method(self):
        """The actual sort mechanism. Function (rows, sortBy, descending) => sorted rows; For best performance, reference it from your scope and do not define it inline"""
        return self._props.get("sort-method")

    @ui_sort_method.setter
    def ui_sort_method(self, value):
        self._set_prop("sort-method", value)

    @property
    def ui_fullscreen(self):
        """Fullscreen mode"""
        return self._props.get("fullscreen")

    @ui_fullscreen.setter
    def ui_fullscreen(self, value):
        self._set_prop("fullscreen", value)

    @property
    def ui_no_route_fullscreen_exit(self):
        """Changing route app won't exit fullscreen"""
        return self._props.get("no-route-fullscreen-exit")

    @ui_no_route_fullscreen_exit.setter
    def ui_no_route_fullscreen_exit(self, value):
        self._set_prop("no-route-fullscreen-exit", value)

    @property
    def ui_slot_body(self):
        """Slot to define how a body row looks like; Suggestion: QTr + Td"""
        return self.ui_slots.get("body", [])

    @ui_slot_body.setter
    def ui_slot_body(self, value):
        self._set_slot("body", value)

    @property
    def ui_slot_body_cell(self):
        """Slot to define how all body cells look like; Suggestion: QTd"""
        return self.ui_slots.get("body-cell", [])

    @ui_slot_body_cell.setter
    def ui_slot_body_cell(self, value):
        self._set_slot("body-cell", value)

    def ui_slot_body_cell_name(self, name, value):
        """Slot to define how a specific column cell looks like; replace '[name]' with column name (from columns definition object)"""
        self._set_slot("body-cell-" + name, value)

    @property
    def ui_slot_body_selection(self):
        """Slot to define how body selection column looks like; Suggestion: QCheckbox"""
        return self.ui_slots.get("body-selection", [])

    @ui_slot_body_selection.setter
    def ui_slot_body_selection(self, value):
        self._set_slot("body-selection", value)

    @property
    def ui_slot_bottom(self):
        """Slot to define how table bottom looks like"""
        return self.ui_slots.get("bottom", [])

    @ui_slot_bottom.setter
    def ui_slot_bottom(self, value):
        self._set_slot("bottom", value)

    @property
    def ui_slot_bottom_row(self):
        """Slot to define how bottom extra row looks like"""
        return self.ui_slots.get("bottom-row", [])

    @ui_slot_bottom_row.setter
    def ui_slot_bottom_row(self, value):
        self._set_slot("bottom-row", value)

    @property
    def ui_slot_header(self):
        """Slot to define how header looks like; Suggestion: QTr + QTh"""
        return self.ui_slots.get("header", [])

    @ui_slot_header.setter
    def ui_slot_header(self, value):
        self._set_slot("header", value)

    @property
    def ui_slot_header_cell(self):
        """Slot to define how each header cell looks like; Suggestion: QTh"""
        return self.ui_slots.get("header-cell", [])

    @ui_slot_header_cell.setter
    def ui_slot_header_cell(self, value):
        self._set_slot("header-cell", value)

    def ui_slot_header_cell_name(self, name, value):
        """Slot to define how a specific header cell looks like; replace '[name]' with column name (from columns definition object)"""
        self._set_slot("header-cell-" + name, value)

    @property
    def ui_slot_header_selection(self):
        """Slot to define how header selection column looks like (available only for multiple selection mode); Suggestion: QCheckbox"""
        return self.ui_slots.get("header-selection", [])

    @ui_slot_header_selection.setter
    def ui_slot_header_selection(self, value):
        self._set_slot("header-selection", value)

    @property
    def ui_slot_item(self):
        """Slot to use for defining an item when in 'grid' mode; Suggestion: QCard"""
        return self.ui_slots.get("item", [])

    @ui_slot_item.setter
    def ui_slot_item(self, value):
        self._set_slot("item", value)

    @property
    def ui_slot_loading(self):
        """Override default effect when table is in loading state; Suggestion: QInnerLoading"""
        return self.ui_slots.get("loading", [])

    @ui_slot_loading.setter
    def ui_slot_loading(self, value):
        self._set_slot("loading", value)

    @property
    def ui_slot_no_data(self):
        """Slot to define how the bottom will look like when is nothing to display"""
        return self.ui_slots.get("no-data", [])

    @ui_slot_no_data.setter
    def ui_slot_no_data(self, value):
        self._set_slot("no-data", value)

    @property
    def ui_slot_pagination(self):
        """Slot to override default pagination label and buttons"""
        return self.ui_slots.get("pagination", [])

    @ui_slot_pagination.setter
    def ui_slot_pagination(self, value):
        self._set_slot("pagination", value)

    @property
    def ui_slot_top(self):
        """Slot to define how table top looks like"""
        return self.ui_slots.get("top", [])

    @ui_slot_top.setter
    def ui_slot_top(self, value):
        self._set_slot("top", value)

    @property
    def ui_slot_top_left(self):
        """Slot to define how left part of the table top looks like"""
        return self.ui_slots.get("top-left", [])

    @ui_slot_top_left.setter
    def ui_slot_top_left(self, value):
        self._set_slot("top-left", value)

    @property
    def ui_slot_top_right(self):
        """Slot to define how right part of the table top looks like"""
        return self.ui_slots.get("top-right", [])

    @ui_slot_top_right.setter
    def ui_slot_top_right(self, value):
        self._set_slot("top-right", value)

    @property
    def ui_slot_top_row(self):
        """Slot to define how top extra row looks like"""
        return self.ui_slots.get("top-row", [])

    @ui_slot_top_row.setter
    def ui_slot_top_row(self, value):
        self._set_slot("top-row", value)

    @property
    def ui_slot_top_selection(self):
        """Slot to define how top table section looks like when user has selected at least one row"""
        return self.ui_slots.get("top-selection", [])

    @ui_slot_top_selection.setter
    def ui_slot_top_selection(self, value):
        self._set_slot("top-selection", value)

    def on_fullscreen(self, handler: Callable, arg: object = None):
        """
        Emitted when fullscreen state changes

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("fullscreen", handler, arg)

    def on_request(self, handler: Callable, arg: object = None):
        """
        Emitted when a server request is triggered

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("request", handler, arg)

    def on_row_click(self, handler: Callable, arg: object = None):
        """
        Emitted when user clicks/taps on a row; Is not emitted when using body/row/item scoped slots

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("row-click", handler, arg)

    def on_row_contextmenu(self, handler: Callable, arg: object = None):
        """
        Emitted when user right clicks/long taps on a row; Is not emitted when using body/row/item scoped slots

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("row-contextmenu", handler, arg)

    def on_row_dblclick(self, handler: Callable, arg: object = None):
        """
        Emitted when user quickly double clicks/taps on a row; Is not emitted when using body/row/item scoped slots; Please check JS dblclick event support before using

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("row-dblclick", handler, arg)

    def on_selection(self, handler: Callable, arg: object = None):
        """
        Emitted when user selects/unselects row(s)

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("selection", handler, arg)

    def on_update_expanded(self, handler: Callable, arg: object = None):
        """
        Used by Vue on 'v-model:expanded' prop for updating its value

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("update:expanded", handler, arg)

    def on_update_fullscreen(self, handler: Callable, arg: object = None):
        """
        Used by Vue on 'v-model:fullscreen' prop for updating its value

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("update:fullscreen", handler, arg)

    def on_update_pagination(self, handler: Callable, arg: object = None):
        """
        Used by Vue on 'v-model:pagination' for updating its value

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("update:pagination", handler, arg)

    def on_update_selected(self, handler: Callable, arg: object = None):
        """
        Used by Vue on 'v-model:selected' prop for updating its value

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("update:selected", handler, arg)

    def on_virtual_scroll(self, handler: Callable, arg: object = None):
        """
        Emitted when the virtual scroll occurs, if using virtual scroll

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("virtual-scroll", handler, arg)

    def ui_clearSelection(self):
        """Clears user selection (emits 'update:selected' with empty array)"""
        self._js_call_method("clearSelection")

    def ui_exitFullscreen(self):
        """Leave the fullscreen view"""
        self._js_call_method("exitFullscreen")

    def ui_firstPage(self):
        """Navigates to first page"""
        self._js_call_method("firstPage")

    def ui_isRowExpanded(self, ui_key):
        """Determine if a row is expanded or not"""
        kwargs = {}
        if ui_key is not None:
            kwargs["key"] = ui_key
        self._js_call_method("isRowExpanded", [kwargs])

    def ui_isRowSelected(self, ui_key):
        """Determine if a row has been selected by user"""
        kwargs = {}
        if ui_key is not None:
            kwargs["key"] = ui_key
        self._js_call_method("isRowSelected", [kwargs])

    def ui_lastPage(self):
        """Navigates to last page"""
        self._js_call_method("lastPage")

    def ui_nextPage(self):
        """Navigates to next page, if available"""
        self._js_call_method("nextPage")

    def ui_prevPage(self):
        """Navigates to previous page, if available"""
        self._js_call_method("prevPage")

    def ui_requestServerInteraction(self, ui_props=None):
        """Trigger a server request (emits 'request' event)"""
        kwargs = {}
        if ui_props is not None:
            kwargs["props"] = ui_props
        self._js_call_method("requestServerInteraction", [kwargs])

    def ui_resetVirtualScroll(self):
        """Resets the virtual scroll (if using it) computations; Needed for custom edge-cases"""
        self._js_call_method("resetVirtualScroll")

    def ui_scrollTo(self, ui_index, ui_edge=None):
        """Scroll the table to the row with the specified index in page (0 based)"""
        kwargs = {}
        if ui_index is not None:
            kwargs["index"] = ui_index
        if ui_edge is not None:
            kwargs["edge"] = ui_edge
        self._js_call_method("scrollTo", [kwargs])

    def ui_setExpanded(self, ui_expanded):
        """Sets the expanded rows keys array; Especially useful if not using an external 'expanded' state otherwise just emits 'update:expanded' with the value"""
        kwargs = {}
        if ui_expanded is not None:
            kwargs["expanded"] = ui_expanded
        self._js_call_method("setExpanded", [kwargs])

    def ui_setFullscreen(self):
        """Enter the fullscreen view"""
        self._js_call_method("setFullscreen")

    def ui_setPagination(self, ui_pagination, ui_forceServerRequest=None):
        """Unless using an external pagination Object (through 'v-model:pagination' prop), you can use this method and force the internal pagination to change"""
        kwargs = {}
        if ui_pagination is not None:
            kwargs["pagination"] = ui_pagination
        if ui_forceServerRequest is not None:
            kwargs["forceServerRequest"] = ui_forceServerRequest
        self._js_call_method("setPagination", [kwargs])

    def ui_sort(self, ui_col):
        """Trigger a table sort"""
        kwargs = {}
        if ui_col is not None:
            kwargs["col"] = ui_col
        self._js_call_method("sort", [kwargs])

    def ui_toggleFullscreen(self):
        """Toggle the view to be fullscreen or not fullscreen"""
        self._js_call_method("toggleFullscreen")

    def _get_js_methods(self):
        return [
            "clearSelection",
            "exitFullscreen",
            "firstPage",
            "isRowExpanded",
            "isRowSelected",
            "lastPage",
            "nextPage",
            "prevPage",
            "requestServerInteraction",
            "resetVirtualScroll",
            "scrollTo",
            "setExpanded",
            "setFullscreen",
            "setPagination",
            "sort",
            "toggleFullscreen",
        ]


class QTr(Component):
    """
    Quasar Component: `QTr <https://v2.quasar.dev/vue-components/table>`__

    :param ui_props: QTable's row scoped slot property
    :param ui_no_hover: Disable hover effect
    """

    def __init__(
        self,
        *children,
        ui_props: dict | None = None,
        ui_no_hover: bool | None = None,
        **kwargs,
    ):
        super().__init__("QTr", *children, **kwargs)
        if ui_props is not None:
            self._props["props"] = ui_props
        if ui_no_hover is not None:
            self._props["no-hover"] = ui_no_hover

    @property
    def ui_props(self):
        """QTable's row scoped slot property"""
        return self._props.get("props")

    @ui_props.setter
    def ui_props(self, value):
        self._set_prop("props", value)

    @property
    def ui_no_hover(self):
        """Disable hover effect"""
        return self._props.get("no-hover")

    @ui_no_hover.setter
    def ui_no_hover(self, value):
        self._set_prop("no-hover", value)

    def _get_js_methods(self):
        return []


class QTab(Component):
    """
    Quasar Component: `QTab <https://v2.quasar.dev/vue-components/tabs>`__

    :param ui_icon:
    :param ui_label: A number or string to label the tab
    :param ui_alert: Adds an alert symbol to the tab, notifying the user there are some updates; If its value is not a Boolean, then you can specify a color
    :param ui_alert_icon: Adds a floating icon to the tab, notifying the user there are some updates; It's displayed only if 'alert' is set; Can use the color specified by 'alert' prop
    :param ui_name: Panel name
    :param ui_no_caps: Turns off capitalizing all letters within the tab (which is the default)
    :param ui_content_class: Class definitions to be attributed to the content wrapper
    :param ui_ripple:
    :param ui_tabindex:
    :param ui_disable:
    """

    def __init__(
        self,
        *children,
        ui_icon: Any | None = None,
        ui_label: float | str | None = None,
        ui_alert: bool | str | None = None,
        ui_alert_icon: str | None = None,
        ui_name: float | str | None = None,
        ui_no_caps: bool | None = None,
        ui_content_class: str | None = None,
        ui_ripple: Any | None = None,
        ui_tabindex: Any | None = None,
        ui_disable: Any | None = None,
        **kwargs,
    ):
        super().__init__("QTab", *children, **kwargs)
        if ui_icon is not None:
            self._props["icon"] = ui_icon
        if ui_label is not None:
            self._props["label"] = ui_label
        if ui_alert is not None:
            self._props["alert"] = ui_alert
        if ui_alert_icon is not None:
            self._props["alert-icon"] = ui_alert_icon
        if ui_name is not None:
            self._props["name"] = ui_name
        if ui_no_caps is not None:
            self._props["no-caps"] = ui_no_caps
        if ui_content_class is not None:
            self._props["content-class"] = ui_content_class
        if ui_ripple is not None:
            self._props["ripple"] = ui_ripple
        if ui_tabindex is not None:
            self._props["tabindex"] = ui_tabindex
        if ui_disable is not None:
            self._props["disable"] = ui_disable

    @property
    def ui_icon(self):
        return self._props.get("icon")

    @ui_icon.setter
    def ui_icon(self, value):
        self._set_prop("icon", value)

    @property
    def ui_label(self):
        """A number or string to label the tab"""
        return self._props.get("label")

    @ui_label.setter
    def ui_label(self, value):
        self._set_prop("label", value)

    @property
    def ui_alert(self):
        """Adds an alert symbol to the tab, notifying the user there are some updates; If its value is not a Boolean, then you can specify a color"""
        return self._props.get("alert")

    @ui_alert.setter
    def ui_alert(self, value):
        self._set_prop("alert", value)

    @property
    def ui_alert_icon(self):
        """Adds a floating icon to the tab, notifying the user there are some updates; It's displayed only if 'alert' is set; Can use the color specified by 'alert' prop"""
        return self._props.get("alert-icon")

    @ui_alert_icon.setter
    def ui_alert_icon(self, value):
        self._set_prop("alert-icon", value)

    @property
    def ui_name(self):
        """Panel name"""
        return self._props.get("name")

    @ui_name.setter
    def ui_name(self, value):
        self._set_prop("name", value)

    @property
    def ui_no_caps(self):
        """Turns off capitalizing all letters within the tab (which is the default)"""
        return self._props.get("no-caps")

    @ui_no_caps.setter
    def ui_no_caps(self, value):
        self._set_prop("no-caps", value)

    @property
    def ui_content_class(self):
        """Class definitions to be attributed to the content wrapper"""
        return self._props.get("content-class")

    @ui_content_class.setter
    def ui_content_class(self, value):
        self._set_prop("content-class", value)

    @property
    def ui_ripple(self):
        return self._props.get("ripple")

    @ui_ripple.setter
    def ui_ripple(self, value):
        self._set_prop("ripple", value)

    @property
    def ui_tabindex(self):
        return self._props.get("tabindex")

    @ui_tabindex.setter
    def ui_tabindex(self, value):
        self._set_prop("tabindex", value)

    @property
    def ui_disable(self):
        return self._props.get("disable")

    @ui_disable.setter
    def ui_disable(self, value):
        self._set_prop("disable", value)

    def on_click(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("click.stop", handler, arg)

    def on_keydown(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("keydown", handler, arg)

    def _get_js_methods(self):
        return []


class QRouteTab(Component):
    """
    Quasar Component: `QRouteTab <https://v2.quasar.dev/vue-components/tabs>`__

    :param ui_icon:
    :param ui_label: A number or string to label the tab
    :param ui_alert: Adds an alert symbol to the tab, notifying the user there are some updates; If its value is not a Boolean, then you can specify a color
    :param ui_alert_icon: Adds a floating icon to the tab, notifying the user there are some updates; It's displayed only if 'alert' is set; Can use the color specified by 'alert' prop
    :param ui_name: Panel name
    :param ui_no_caps: Turns off capitalizing all letters within the tab (which is the default)
    :param ui_content_class: Class definitions to be attributed to the content wrapper
    :param ui_ripple:
    :param ui_tabindex:
    :param ui_disable:
    :param ui_to: Equivalent to Vue Router <router-link> 'to' property; Superseded by 'href' prop if used
    :param ui_exact: Equivalent to Vue Router <router-link> 'exact' property; Superseded by 'href' prop if used
    :param ui_replace: Equivalent to Vue Router <router-link> 'replace' property; Superseded by 'href' prop if used
    :param ui_active_class: Equivalent to Vue Router <router-link> 'active-class' property; Superseded by 'href' prop if used
    :param ui_exact_active_class: Equivalent to Vue Router <router-link> 'active-class' property; Superseded by 'href' prop if used
    :param ui_href: Native <a> link href attribute; Has priority over the 'to'/'exact'/'replace'/'active-class'/'exact-active-class' props
    :param ui_target: Native <a> link target attribute; Use it only along with 'href' prop; Has priority over the 'to'/'exact'/'replace'/'active-class'/'exact-active-class' props
    """

    def __init__(
        self,
        *children,
        ui_icon: Any | None = None,
        ui_label: float | str | None = None,
        ui_alert: bool | str | None = None,
        ui_alert_icon: str | None = None,
        ui_name: float | str | None = None,
        ui_no_caps: bool | None = None,
        ui_content_class: str | None = None,
        ui_ripple: Any | None = None,
        ui_tabindex: Any | None = None,
        ui_disable: Any | None = None,
        ui_to: str | dict | None = None,
        ui_exact: bool | None = None,
        ui_replace: bool | None = None,
        ui_active_class: str | None = None,
        ui_exact_active_class: str | None = None,
        ui_href: str | None = None,
        ui_target: str | None = None,
        **kwargs,
    ):
        super().__init__("QRouteTab", *children, **kwargs)
        if ui_icon is not None:
            self._props["icon"] = ui_icon
        if ui_label is not None:
            self._props["label"] = ui_label
        if ui_alert is not None:
            self._props["alert"] = ui_alert
        if ui_alert_icon is not None:
            self._props["alert-icon"] = ui_alert_icon
        if ui_name is not None:
            self._props["name"] = ui_name
        if ui_no_caps is not None:
            self._props["no-caps"] = ui_no_caps
        if ui_content_class is not None:
            self._props["content-class"] = ui_content_class
        if ui_ripple is not None:
            self._props["ripple"] = ui_ripple
        if ui_tabindex is not None:
            self._props["tabindex"] = ui_tabindex
        if ui_disable is not None:
            self._props["disable"] = ui_disable
        if ui_to is not None:
            self._props["to"] = ui_to
        if ui_exact is not None:
            self._props["exact"] = ui_exact
        if ui_replace is not None:
            self._props["replace"] = ui_replace
        if ui_active_class is not None:
            self._props["active-class"] = ui_active_class
        if ui_exact_active_class is not None:
            self._props["exact-active-class"] = ui_exact_active_class
        if ui_href is not None:
            self._props["href"] = ui_href
        if ui_target is not None:
            self._props["target"] = ui_target

    @property
    def ui_icon(self):
        return self._props.get("icon")

    @ui_icon.setter
    def ui_icon(self, value):
        self._set_prop("icon", value)

    @property
    def ui_label(self):
        """A number or string to label the tab"""
        return self._props.get("label")

    @ui_label.setter
    def ui_label(self, value):
        self._set_prop("label", value)

    @property
    def ui_alert(self):
        """Adds an alert symbol to the tab, notifying the user there are some updates; If its value is not a Boolean, then you can specify a color"""
        return self._props.get("alert")

    @ui_alert.setter
    def ui_alert(self, value):
        self._set_prop("alert", value)

    @property
    def ui_alert_icon(self):
        """Adds a floating icon to the tab, notifying the user there are some updates; It's displayed only if 'alert' is set; Can use the color specified by 'alert' prop"""
        return self._props.get("alert-icon")

    @ui_alert_icon.setter
    def ui_alert_icon(self, value):
        self._set_prop("alert-icon", value)

    @property
    def ui_name(self):
        """Panel name"""
        return self._props.get("name")

    @ui_name.setter
    def ui_name(self, value):
        self._set_prop("name", value)

    @property
    def ui_no_caps(self):
        """Turns off capitalizing all letters within the tab (which is the default)"""
        return self._props.get("no-caps")

    @ui_no_caps.setter
    def ui_no_caps(self, value):
        self._set_prop("no-caps", value)

    @property
    def ui_content_class(self):
        """Class definitions to be attributed to the content wrapper"""
        return self._props.get("content-class")

    @ui_content_class.setter
    def ui_content_class(self, value):
        self._set_prop("content-class", value)

    @property
    def ui_ripple(self):
        return self._props.get("ripple")

    @ui_ripple.setter
    def ui_ripple(self, value):
        self._set_prop("ripple", value)

    @property
    def ui_tabindex(self):
        return self._props.get("tabindex")

    @ui_tabindex.setter
    def ui_tabindex(self, value):
        self._set_prop("tabindex", value)

    @property
    def ui_disable(self):
        return self._props.get("disable")

    @ui_disable.setter
    def ui_disable(self, value):
        self._set_prop("disable", value)

    @property
    def ui_to(self):
        """Equivalent to Vue Router <router-link> 'to' property; Superseded by 'href' prop if used"""
        return self._props.get("to")

    @ui_to.setter
    def ui_to(self, value):
        self._set_prop("to", value)

    @property
    def ui_exact(self):
        """Equivalent to Vue Router <router-link> 'exact' property; Superseded by 'href' prop if used"""
        return self._props.get("exact")

    @ui_exact.setter
    def ui_exact(self, value):
        self._set_prop("exact", value)

    @property
    def ui_replace(self):
        """Equivalent to Vue Router <router-link> 'replace' property; Superseded by 'href' prop if used"""
        return self._props.get("replace")

    @ui_replace.setter
    def ui_replace(self, value):
        self._set_prop("replace", value)

    @property
    def ui_active_class(self):
        """Equivalent to Vue Router <router-link> 'active-class' property; Superseded by 'href' prop if used"""
        return self._props.get("active-class")

    @ui_active_class.setter
    def ui_active_class(self, value):
        self._set_prop("active-class", value)

    @property
    def ui_exact_active_class(self):
        """Equivalent to Vue Router <router-link> 'active-class' property; Superseded by 'href' prop if used"""
        return self._props.get("exact-active-class")

    @ui_exact_active_class.setter
    def ui_exact_active_class(self, value):
        self._set_prop("exact-active-class", value)

    @property
    def ui_href(self):
        """Native <a> link href attribute; Has priority over the 'to'/'exact'/'replace'/'active-class'/'exact-active-class' props"""
        return self._props.get("href")

    @ui_href.setter
    def ui_href(self, value):
        self._set_prop("href", value)

    @property
    def ui_target(self):
        """Native <a> link target attribute; Use it only along with 'href' prop; Has priority over the 'to'/'exact'/'replace'/'active-class'/'exact-active-class' props"""
        return self._props.get("target")

    @ui_target.setter
    def ui_target(self, value):
        self._set_prop("target", value)

    def on_click(self, handler: Callable, arg: object = None):
        """
        Emitted when the component is clicked

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("click.stop", handler, arg)

    def on_keydown(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("keydown", handler, arg)

    def _get_js_methods(self):
        return []


class QTabs(Component):
    """
    Quasar Component: `QTabs <https://v2.quasar.dev/vue-components/tabs>`__

    :param ui_model_value: Model of the component defining current panel name; Either use this property (along with a listener for 'update:modelValue' event) OR use v-model directive
    :param ui_vertical: Use vertical design (tabs one on top of each other rather than one next to the other horizontally)
    :param ui_outside_arrows: Reserve space for arrows to place them on each side of the tabs (the arrows fade when inactive)
    :param ui_mobile_arrows: Force display of arrows (if needed) on mobile
    :param ui_align: Horizontal alignment the tabs within the tabs container
    :param ui_breakpoint: Breakpoint (in pixels) of tabs container width at which the tabs automatically turn to a justify alignment
    :param ui_active_color: The color to be attributed to the text of the active tab
    :param ui_active_bg_color: The color to be attributed to the background of the active tab
    :param ui_indicator_color: The color to be attributed to the indicator (the underline) of the active tab
    :param ui_content_class: Class definitions to be attributed to the content wrapper
    :param ui_active_class: The class to be set on the active tab
    :param ui_left_icon: The name of an icon to replace the default arrow used to scroll through the tabs to the left, when the tabs extend past the width of the tabs container
    :param ui_right_icon: The name of an icon to replace the default arrow used to scroll through the tabs to the right, when the tabs extend past the width of the tabs container
    :param ui_stretch: When used on flexbox parent, tabs will stretch to parent's height
    :param ui_shrink: By default, QTabs is set to grow to the available space; However, you can reverse that with this prop; Useful (and required) when placing the component in a QToolbar
    :param ui_switch_indicator: Switches the indicator position (on left of tab for vertical mode or above the tab for default horizontal mode)
    :param ui_narrow_indicator: Allows the indicator to be the same width as the tab's content (text or icon), instead of the whole width of the tab
    :param ui_inline_label: Allows the text to be inline with the icon, should one be used
    :param ui_no_caps: Turns off capitalizing all letters within the tab (which is the default)
    :param ui_dense:
    """

    def __init__(
        self,
        *children,
        ui_model_value: float | str | None | Any = None,
        ui_vertical: bool | None = None,
        ui_outside_arrows: bool | None = None,
        ui_mobile_arrows: bool | None = None,
        ui_align: str | None = None,
        ui_breakpoint: float | str | None = None,
        ui_active_color: Any | None = None,
        ui_active_bg_color: Any | None = None,
        ui_indicator_color: Any | None = None,
        ui_content_class: str | None = None,
        ui_active_class: str | None = None,
        ui_left_icon: str | None = None,
        ui_right_icon: str | None = None,
        ui_stretch: bool | None = None,
        ui_shrink: bool | None = None,
        ui_switch_indicator: bool | None = None,
        ui_narrow_indicator: bool | None = None,
        ui_inline_label: bool | None = None,
        ui_no_caps: bool | None = None,
        ui_dense: Any | None = None,
        **kwargs,
    ):
        super().__init__("QTabs", *children, **kwargs)
        self.on("update:model-value", self.__update_model_value)

        if ui_model_value is not None:
            self._props["model-value"] = ui_model_value
        if ui_vertical is not None:
            self._props["vertical"] = ui_vertical
        if ui_outside_arrows is not None:
            self._props["outside-arrows"] = ui_outside_arrows
        if ui_mobile_arrows is not None:
            self._props["mobile-arrows"] = ui_mobile_arrows
        if ui_align is not None:
            self._props["align"] = ui_align
        if ui_breakpoint is not None:
            self._props["breakpoint"] = ui_breakpoint
        if ui_active_color is not None:
            self._props["active-color"] = ui_active_color
        if ui_active_bg_color is not None:
            self._props["active-bg-color"] = ui_active_bg_color
        if ui_indicator_color is not None:
            self._props["indicator-color"] = ui_indicator_color
        if ui_content_class is not None:
            self._props["content-class"] = ui_content_class
        if ui_active_class is not None:
            self._props["active-class"] = ui_active_class
        if ui_left_icon is not None:
            self._props["left-icon"] = ui_left_icon
        if ui_right_icon is not None:
            self._props["right-icon"] = ui_right_icon
        if ui_stretch is not None:
            self._props["stretch"] = ui_stretch
        if ui_shrink is not None:
            self._props["shrink"] = ui_shrink
        if ui_switch_indicator is not None:
            self._props["switch-indicator"] = ui_switch_indicator
        if ui_narrow_indicator is not None:
            self._props["narrow-indicator"] = ui_narrow_indicator
        if ui_inline_label is not None:
            self._props["inline-label"] = ui_inline_label
        if ui_no_caps is not None:
            self._props["no-caps"] = ui_no_caps
        if ui_dense is not None:
            self._props["dense"] = ui_dense

    def __update_model_value(self, event: Event):
        self._set_prop("model-value", event.value)

    @property
    def ui_model_value(self):
        """Model of the component defining current panel name; Either use this property (along with a listener for 'update:modelValue' event) OR use v-model directive"""
        return self._props.get("model-value")

    @ui_model_value.setter
    def ui_model_value(self, value):
        self._set_prop("model-value", value)

    @property
    def ui_vertical(self):
        """Use vertical design (tabs one on top of each other rather than one next to the other horizontally)"""
        return self._props.get("vertical")

    @ui_vertical.setter
    def ui_vertical(self, value):
        self._set_prop("vertical", value)

    @property
    def ui_outside_arrows(self):
        """Reserve space for arrows to place them on each side of the tabs (the arrows fade when inactive)"""
        return self._props.get("outside-arrows")

    @ui_outside_arrows.setter
    def ui_outside_arrows(self, value):
        self._set_prop("outside-arrows", value)

    @property
    def ui_mobile_arrows(self):
        """Force display of arrows (if needed) on mobile"""
        return self._props.get("mobile-arrows")

    @ui_mobile_arrows.setter
    def ui_mobile_arrows(self, value):
        self._set_prop("mobile-arrows", value)

    @property
    def ui_align(self):
        """Horizontal alignment the tabs within the tabs container"""
        return self._props.get("align")

    @ui_align.setter
    def ui_align(self, value):
        self._set_prop("align", value)

    @property
    def ui_breakpoint(self):
        """Breakpoint (in pixels) of tabs container width at which the tabs automatically turn to a justify alignment"""
        return self._props.get("breakpoint")

    @ui_breakpoint.setter
    def ui_breakpoint(self, value):
        self._set_prop("breakpoint", value)

    @property
    def ui_active_color(self):
        """The color to be attributed to the text of the active tab"""
        return self._props.get("active-color")

    @ui_active_color.setter
    def ui_active_color(self, value):
        self._set_prop("active-color", value)

    @property
    def ui_active_bg_color(self):
        """The color to be attributed to the background of the active tab"""
        return self._props.get("active-bg-color")

    @ui_active_bg_color.setter
    def ui_active_bg_color(self, value):
        self._set_prop("active-bg-color", value)

    @property
    def ui_indicator_color(self):
        """The color to be attributed to the indicator (the underline) of the active tab"""
        return self._props.get("indicator-color")

    @ui_indicator_color.setter
    def ui_indicator_color(self, value):
        self._set_prop("indicator-color", value)

    @property
    def ui_content_class(self):
        """Class definitions to be attributed to the content wrapper"""
        return self._props.get("content-class")

    @ui_content_class.setter
    def ui_content_class(self, value):
        self._set_prop("content-class", value)

    @property
    def ui_active_class(self):
        """The class to be set on the active tab"""
        return self._props.get("active-class")

    @ui_active_class.setter
    def ui_active_class(self, value):
        self._set_prop("active-class", value)

    @property
    def ui_left_icon(self):
        """The name of an icon to replace the default arrow used to scroll through the tabs to the left, when the tabs extend past the width of the tabs container"""
        return self._props.get("left-icon")

    @ui_left_icon.setter
    def ui_left_icon(self, value):
        self._set_prop("left-icon", value)

    @property
    def ui_right_icon(self):
        """The name of an icon to replace the default arrow used to scroll through the tabs to the right, when the tabs extend past the width of the tabs container"""
        return self._props.get("right-icon")

    @ui_right_icon.setter
    def ui_right_icon(self, value):
        self._set_prop("right-icon", value)

    @property
    def ui_stretch(self):
        """When used on flexbox parent, tabs will stretch to parent's height"""
        return self._props.get("stretch")

    @ui_stretch.setter
    def ui_stretch(self, value):
        self._set_prop("stretch", value)

    @property
    def ui_shrink(self):
        """By default, QTabs is set to grow to the available space; However, you can reverse that with this prop; Useful (and required) when placing the component in a QToolbar"""
        return self._props.get("shrink")

    @ui_shrink.setter
    def ui_shrink(self, value):
        self._set_prop("shrink", value)

    @property
    def ui_switch_indicator(self):
        """Switches the indicator position (on left of tab for vertical mode or above the tab for default horizontal mode)"""
        return self._props.get("switch-indicator")

    @ui_switch_indicator.setter
    def ui_switch_indicator(self, value):
        self._set_prop("switch-indicator", value)

    @property
    def ui_narrow_indicator(self):
        """Allows the indicator to be the same width as the tab's content (text or icon), instead of the whole width of the tab"""
        return self._props.get("narrow-indicator")

    @ui_narrow_indicator.setter
    def ui_narrow_indicator(self, value):
        self._set_prop("narrow-indicator", value)

    @property
    def ui_inline_label(self):
        """Allows the text to be inline with the icon, should one be used"""
        return self._props.get("inline-label")

    @ui_inline_label.setter
    def ui_inline_label(self, value):
        self._set_prop("inline-label", value)

    @property
    def ui_no_caps(self):
        """Turns off capitalizing all letters within the tab (which is the default)"""
        return self._props.get("no-caps")

    @ui_no_caps.setter
    def ui_no_caps(self, value):
        self._set_prop("no-caps", value)

    @property
    def ui_dense(self):
        return self._props.get("dense")

    @ui_dense.setter
    def ui_dense(self, value):
        self._set_prop("dense", value)

    def on_update_model_value(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("update:model-value", handler, arg)

    def _get_js_methods(self):
        return []


class QTime(Component):
    """
    Quasar Component: `QTime <https://v2.quasar.dev/vue-components/time>`__

    :param ui_model_value: Time of the component; Either use this property (along with a listener for 'update:modelValue' event) OR use v-model directive
    :param ui_format24h: Forces 24 hour time display instead of AM/PM system; If prop is not set, then the default is based on Quasar lang language being used
    :param ui_default_date: The default date to use (in YYYY/MM/DD format) when model is unfilled (undefined or null)
    :param ui_mask: Mask (formatting string) used for parsing and formatting value
    :param ui_options: Optionally configure what time is the user allowed to set; Overridden by 'hour-options', 'minute-options' and 'second-options' if those are set; For best performance, reference it from your scope and do not define it inline
    :param ui_hour_options: Optionally configure what hours is the user allowed to set; Overrides 'options' prop if that is also set
    :param ui_minute_options: Optionally configure what minutes is the user allowed to set; Overrides 'options' prop if that is also set
    :param ui_second_options: Optionally configure what seconds is the user allowed to set; Overrides 'options' prop if that is also set
    :param ui_with_seconds: Allow the time to be set with seconds
    :param ui_now_btn: Display a button that selects the current time
    :param ui_landscape: Display the component in landscape mode
    :param ui_locale: Locale formatting options
    :param ui_calendar: Specify calendar type
    :param ui_color:
    :param ui_text_color:
    :param ui_dark:
    :param ui_square:
    :param ui_flat:
    :param ui_bordered:
    :param ui_readonly:
    :param ui_disable:
    :param ui_name: Used to specify the name of the control; Useful if dealing with forms submitted directly to a URL
    """

    def __init__(
        self,
        *children,
        ui_model_value: str | None | Any = None,
        ui_format24h: bool | None = None,
        ui_default_date: str | None = None,
        ui_mask: str | None = None,
        ui_options: Callable | None = None,
        ui_hour_options: list | None = None,
        ui_minute_options: list | None = None,
        ui_second_options: list | None = None,
        ui_with_seconds: bool | None = None,
        ui_now_btn: bool | None = None,
        ui_landscape: bool | None = None,
        ui_locale: dict | None = None,
        ui_calendar: str | None = None,
        ui_color: Any | None = None,
        ui_text_color: Any | None = None,
        ui_dark: Any | None = None,
        ui_square: Any | None = None,
        ui_flat: Any | None = None,
        ui_bordered: Any | None = None,
        ui_readonly: Any | None = None,
        ui_disable: Any | None = None,
        ui_name: str | None = None,
        **kwargs,
    ):
        super().__init__("QTime", *children, **kwargs)
        self.on("update:model-value", self.__update_model_value)

        if ui_model_value is not None:
            self._props["model-value"] = ui_model_value
        if ui_format24h is not None:
            self._props["format24h"] = ui_format24h
        if ui_default_date is not None:
            self._props["default-date"] = ui_default_date
        if ui_mask is not None:
            self._props["mask"] = ui_mask
        if ui_options is not None:
            self._props["options"] = ui_options
        if ui_hour_options is not None:
            self._props["hour-options"] = ui_hour_options
        if ui_minute_options is not None:
            self._props["minute-options"] = ui_minute_options
        if ui_second_options is not None:
            self._props["second-options"] = ui_second_options
        if ui_with_seconds is not None:
            self._props["with-seconds"] = ui_with_seconds
        if ui_now_btn is not None:
            self._props["now-btn"] = ui_now_btn
        if ui_landscape is not None:
            self._props["landscape"] = ui_landscape
        if ui_locale is not None:
            self._props["locale"] = ui_locale
        if ui_calendar is not None:
            self._props["calendar"] = ui_calendar
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_text_color is not None:
            self._props["text-color"] = ui_text_color
        if ui_dark is not None:
            self._props["dark"] = ui_dark
        if ui_square is not None:
            self._props["square"] = ui_square
        if ui_flat is not None:
            self._props["flat"] = ui_flat
        if ui_bordered is not None:
            self._props["bordered"] = ui_bordered
        if ui_readonly is not None:
            self._props["readonly"] = ui_readonly
        if ui_disable is not None:
            self._props["disable"] = ui_disable
        if ui_name is not None:
            self._props["name"] = ui_name

    def __update_model_value(self, event: Event):
        self._set_prop("model-value", event.value)

    @property
    def ui_model_value(self):
        """Time of the component; Either use this property (along with a listener for 'update:modelValue' event) OR use v-model directive"""
        return self._props.get("model-value")

    @ui_model_value.setter
    def ui_model_value(self, value):
        self._set_prop("model-value", value)

    @property
    def ui_format24h(self):
        """Forces 24 hour time display instead of AM/PM system; If prop is not set, then the default is based on Quasar lang language being used"""
        return self._props.get("format24h")

    @ui_format24h.setter
    def ui_format24h(self, value):
        self._set_prop("format24h", value)

    @property
    def ui_default_date(self):
        """The default date to use (in YYYY/MM/DD format) when model is unfilled (undefined or null)"""
        return self._props.get("default-date")

    @ui_default_date.setter
    def ui_default_date(self, value):
        self._set_prop("default-date", value)

    @property
    def ui_mask(self):
        """Mask (formatting string) used for parsing and formatting value"""
        return self._props.get("mask")

    @ui_mask.setter
    def ui_mask(self, value):
        self._set_prop("mask", value)

    @property
    def ui_options(self):
        """Optionally configure what time is the user allowed to set; Overridden by 'hour-options', 'minute-options' and 'second-options' if those are set; For best performance, reference it from your scope and do not define it inline"""
        return self._props.get("options")

    @ui_options.setter
    def ui_options(self, value):
        self._set_prop("options", value)

    @property
    def ui_hour_options(self):
        """Optionally configure what hours is the user allowed to set; Overrides 'options' prop if that is also set"""
        return self._props.get("hour-options")

    @ui_hour_options.setter
    def ui_hour_options(self, value):
        self._set_prop("hour-options", value)

    @property
    def ui_minute_options(self):
        """Optionally configure what minutes is the user allowed to set; Overrides 'options' prop if that is also set"""
        return self._props.get("minute-options")

    @ui_minute_options.setter
    def ui_minute_options(self, value):
        self._set_prop("minute-options", value)

    @property
    def ui_second_options(self):
        """Optionally configure what seconds is the user allowed to set; Overrides 'options' prop if that is also set"""
        return self._props.get("second-options")

    @ui_second_options.setter
    def ui_second_options(self, value):
        self._set_prop("second-options", value)

    @property
    def ui_with_seconds(self):
        """Allow the time to be set with seconds"""
        return self._props.get("with-seconds")

    @ui_with_seconds.setter
    def ui_with_seconds(self, value):
        self._set_prop("with-seconds", value)

    @property
    def ui_now_btn(self):
        """Display a button that selects the current time"""
        return self._props.get("now-btn")

    @ui_now_btn.setter
    def ui_now_btn(self, value):
        self._set_prop("now-btn", value)

    @property
    def ui_landscape(self):
        """Display the component in landscape mode"""
        return self._props.get("landscape")

    @ui_landscape.setter
    def ui_landscape(self, value):
        self._set_prop("landscape", value)

    @property
    def ui_locale(self):
        """Locale formatting options"""
        return self._props.get("locale")

    @ui_locale.setter
    def ui_locale(self, value):
        self._set_prop("locale", value)

    @property
    def ui_calendar(self):
        """Specify calendar type"""
        return self._props.get("calendar")

    @ui_calendar.setter
    def ui_calendar(self, value):
        self._set_prop("calendar", value)

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_text_color(self):
        return self._props.get("text-color")

    @ui_text_color.setter
    def ui_text_color(self, value):
        self._set_prop("text-color", value)

    @property
    def ui_dark(self):
        return self._props.get("dark")

    @ui_dark.setter
    def ui_dark(self, value):
        self._set_prop("dark", value)

    @property
    def ui_square(self):
        return self._props.get("square")

    @ui_square.setter
    def ui_square(self, value):
        self._set_prop("square", value)

    @property
    def ui_flat(self):
        return self._props.get("flat")

    @ui_flat.setter
    def ui_flat(self, value):
        self._set_prop("flat", value)

    @property
    def ui_bordered(self):
        return self._props.get("bordered")

    @ui_bordered.setter
    def ui_bordered(self, value):
        self._set_prop("bordered", value)

    @property
    def ui_readonly(self):
        return self._props.get("readonly")

    @ui_readonly.setter
    def ui_readonly(self, value):
        self._set_prop("readonly", value)

    @property
    def ui_disable(self):
        return self._props.get("disable")

    @ui_disable.setter
    def ui_disable(self, value):
        self._set_prop("disable", value)

    @property
    def ui_name(self):
        """Used to specify the name of the control; Useful if dealing with forms submitted directly to a URL"""
        return self._props.get("name")

    @ui_name.setter
    def ui_name(self, value):
        self._set_prop("name", value)

    def on_update_model_value(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("update:model-value", handler, arg)

    def ui_setNow(self):
        """Change model to current moment"""
        self._js_call_method("setNow")

    def _get_js_methods(self):
        return ["setNow"]


class QTimeline(Component):
    """
    Quasar Component: `QTimeline <https://v2.quasar.dev/vue-components/timeline>`__

    :param ui_color:
    :param ui_side: Side to place the timeline entries in dense and comfortable layout; For loose layout it gets overridden by QTimelineEntry side prop
    :param ui_layout: Layout of the timeline. Dense keeps content and labels on one side. Comfortable keeps content on one side and labels on the opposite side. Loose puts content on both sides.
    :param ui_dark:
    """

    def __init__(
        self,
        *children,
        ui_color: Any | None = None,
        ui_side: str | None = None,
        ui_layout: str | None = None,
        ui_dark: Any | None = None,
        **kwargs,
    ):
        super().__init__("QTimeline", *children, **kwargs)
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_side is not None:
            self._props["side"] = ui_side
        if ui_layout is not None:
            self._props["layout"] = ui_layout
        if ui_dark is not None:
            self._props["dark"] = ui_dark

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_side(self):
        """Side to place the timeline entries in dense and comfortable layout; For loose layout it gets overridden by QTimelineEntry side prop"""
        return self._props.get("side")

    @ui_side.setter
    def ui_side(self, value):
        self._set_prop("side", value)

    @property
    def ui_layout(self):
        """Layout of the timeline. Dense keeps content and labels on one side. Comfortable keeps content on one side and labels on the opposite side. Loose puts content on both sides."""
        return self._props.get("layout")

    @ui_layout.setter
    def ui_layout(self, value):
        self._set_prop("layout", value)

    @property
    def ui_dark(self):
        return self._props.get("dark")

    @ui_dark.setter
    def ui_dark(self, value):
        self._set_prop("dark", value)

    def _get_js_methods(self):
        return []


class QTimelineEntry(Component):
    """
    Quasar Component: `QTimelineEntry <https://v2.quasar.dev/vue-components/timeline>`__

    :param ui_heading: Defines a heading timeline item
    :param ui_tag: Tag to use, if of type 'heading' only
    :param ui_side: Side to place the timeline entry; Works only if QTimeline layout is loose.
    :param ui_icon:
    :param ui_avatar: URL to the avatar image; Icon takes precedence if used, so it replaces avatar
    :param ui_color:
    :param ui_title: Title of timeline entry; Is overridden if using 'title' slot
    :param ui_subtitle: Subtitle of timeline entry; Is overridden if using 'subtitle' slot
    :param ui_body: Body content of timeline entry; Use this prop or the default slot
    """

    def __init__(
        self,
        *children,
        ui_heading: bool | None = None,
        ui_tag: Any | None = None,
        ui_side: str | None = None,
        ui_icon: Any | None = None,
        ui_avatar: str | None = None,
        ui_color: Any | None = None,
        ui_title: str | None = None,
        ui_subtitle: str | None = None,
        ui_body: str | None = None,
        **kwargs,
    ):
        super().__init__("QTimelineEntry", *children, **kwargs)
        if ui_heading is not None:
            self._props["heading"] = ui_heading
        if ui_tag is not None:
            self._props["tag"] = ui_tag
        if ui_side is not None:
            self._props["side"] = ui_side
        if ui_icon is not None:
            self._props["icon"] = ui_icon
        if ui_avatar is not None:
            self._props["avatar"] = ui_avatar
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_title is not None:
            self._props["title"] = ui_title
        if ui_subtitle is not None:
            self._props["subtitle"] = ui_subtitle
        if ui_body is not None:
            self._props["body"] = ui_body

    @property
    def ui_heading(self):
        """Defines a heading timeline item"""
        return self._props.get("heading")

    @ui_heading.setter
    def ui_heading(self, value):
        self._set_prop("heading", value)

    @property
    def ui_tag(self):
        """Tag to use, if of type 'heading' only"""
        return self._props.get("tag")

    @ui_tag.setter
    def ui_tag(self, value):
        self._set_prop("tag", value)

    @property
    def ui_side(self):
        """Side to place the timeline entry; Works only if QTimeline layout is loose."""
        return self._props.get("side")

    @ui_side.setter
    def ui_side(self, value):
        self._set_prop("side", value)

    @property
    def ui_icon(self):
        return self._props.get("icon")

    @ui_icon.setter
    def ui_icon(self, value):
        self._set_prop("icon", value)

    @property
    def ui_avatar(self):
        """URL to the avatar image; Icon takes precedence if used, so it replaces avatar"""
        return self._props.get("avatar")

    @ui_avatar.setter
    def ui_avatar(self, value):
        self._set_prop("avatar", value)

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_title(self):
        """Title of timeline entry; Is overridden if using 'title' slot"""
        return self._props.get("title")

    @ui_title.setter
    def ui_title(self, value):
        self._set_prop("title", value)

    @property
    def ui_subtitle(self):
        """Subtitle of timeline entry; Is overridden if using 'subtitle' slot"""
        return self._props.get("subtitle")

    @ui_subtitle.setter
    def ui_subtitle(self, value):
        self._set_prop("subtitle", value)

    @property
    def ui_body(self):
        """Body content of timeline entry; Use this prop or the default slot"""
        return self._props.get("body")

    @ui_body.setter
    def ui_body(self, value):
        self._set_prop("body", value)

    @property
    def ui_slot_subtitle(self):
        """Optional slot for subtitle; When used, it overrides 'subtitle' prop"""
        return self.ui_slots.get("subtitle", [])

    @ui_slot_subtitle.setter
    def ui_slot_subtitle(self, value):
        self._set_slot("subtitle", value)

    @property
    def ui_slot_title(self):
        """Optional slot for title; When used, it overrides 'title' prop"""
        return self.ui_slots.get("title", [])

    @ui_slot_title.setter
    def ui_slot_title(self, value):
        self._set_slot("title", value)

    def _get_js_methods(self):
        return []


class QToggle(Component):
    """
    Quasar Component: `QToggle <https://v2.quasar.dev/vue-components/toggle>`__

    :param ui_icon:
    :param ui_checked_icon: The icon to be used when the toggle is on
    :param ui_unchecked_icon: The icon to be used when the toggle is off
    :param ui_indeterminate_icon: The icon to be used when the model is indeterminate
    :param ui_icon_color: Override default icon color (for truthy state only); Color name for component from the Quasar Color Palette
    :param ui_model_value:
    :param ui_val: Works when model ('value') is Array. It tells the component which value should add/remove when ticked/unticked
    :param ui_true_value: What model value should be considered as checked/ticked/on?
    :param ui_false_value: What model value should be considered as unchecked/unticked/off?
    :param ui_indeterminate_value: What model value should be considered as 'indeterminate'?
    :param ui_toggle_order: Determines toggle order of the two states ('t' stands for state of true, 'f' for state of false); If 'toggle-indeterminate' is true, then the order is: indet -> first state -> second state -> indet (and repeat), otherwise: indet -> first state -> second state -> first state -> second state -> ...
    :param ui_toggle_indeterminate: When user clicks/taps on the component, should we toggle through the indeterminate state too?
    :param ui_label: Label to display along the component (or use the default slot instead of this prop)
    :param ui_left_label: Label (if any specified) should be displayed on the left side of the component
    :param ui_color:
    :param ui_keep_color: Should the color (if specified any) be kept when the component is unticked/ off?
    :param ui_dark:
    :param ui_dense:
    :param ui_disable:
    :param ui_tabindex:
    :param ui_size: Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)
    :param ui_name: Used to specify the name of the control; Useful if dealing with forms submitted directly to a URL
    """

    def __init__(
        self,
        *children,
        ui_icon: Any | None = None,
        ui_checked_icon: str | None = None,
        ui_unchecked_icon: str | None = None,
        ui_indeterminate_icon: str | None = None,
        ui_icon_color: Any | None = None,
        ui_model_value: Any | list | None = None,
        ui_val: Any | None = None,
        ui_true_value: Any | None = None,
        ui_false_value: Any | None = None,
        ui_indeterminate_value: Any | None = None,
        ui_toggle_order: str | None = None,
        ui_toggle_indeterminate: bool | None = None,
        ui_label: str | None = None,
        ui_left_label: bool | None = None,
        ui_color: Any | None = None,
        ui_keep_color: bool | None = None,
        ui_dark: Any | None = None,
        ui_dense: Any | None = None,
        ui_disable: Any | None = None,
        ui_tabindex: Any | None = None,
        ui_size: str | None = None,
        ui_name: str | None = None,
        **kwargs,
    ):
        super().__init__("QToggle", *children, **kwargs)
        self.on("update:model-value", self.__update_model_value)

        if ui_icon is not None:
            self._props["icon"] = ui_icon
        if ui_checked_icon is not None:
            self._props["checked-icon"] = ui_checked_icon
        if ui_unchecked_icon is not None:
            self._props["unchecked-icon"] = ui_unchecked_icon
        if ui_indeterminate_icon is not None:
            self._props["indeterminate-icon"] = ui_indeterminate_icon
        if ui_icon_color is not None:
            self._props["icon-color"] = ui_icon_color
        if ui_model_value is not None:
            self._props["model-value"] = ui_model_value
        if ui_val is not None:
            self._props["val"] = ui_val
        if ui_true_value is not None:
            self._props["true-value"] = ui_true_value
        if ui_false_value is not None:
            self._props["false-value"] = ui_false_value
        if ui_indeterminate_value is not None:
            self._props["indeterminate-value"] = ui_indeterminate_value
        if ui_toggle_order is not None:
            self._props["toggle-order"] = ui_toggle_order
        if ui_toggle_indeterminate is not None:
            self._props["toggle-indeterminate"] = ui_toggle_indeterminate
        if ui_label is not None:
            self._props["label"] = ui_label
        if ui_left_label is not None:
            self._props["left-label"] = ui_left_label
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_keep_color is not None:
            self._props["keep-color"] = ui_keep_color
        if ui_dark is not None:
            self._props["dark"] = ui_dark
        if ui_dense is not None:
            self._props["dense"] = ui_dense
        if ui_disable is not None:
            self._props["disable"] = ui_disable
        if ui_tabindex is not None:
            self._props["tabindex"] = ui_tabindex
        if ui_size is not None:
            self._props["size"] = ui_size
        if ui_name is not None:
            self._props["name"] = ui_name

    def __update_model_value(self, event: Event):
        self._set_prop("model-value", event.value)

    @property
    def ui_icon(self):
        return self._props.get("icon")

    @ui_icon.setter
    def ui_icon(self, value):
        self._set_prop("icon", value)

    @property
    def ui_checked_icon(self):
        """The icon to be used when the toggle is on"""
        return self._props.get("checked-icon")

    @ui_checked_icon.setter
    def ui_checked_icon(self, value):
        self._set_prop("checked-icon", value)

    @property
    def ui_unchecked_icon(self):
        """The icon to be used when the toggle is off"""
        return self._props.get("unchecked-icon")

    @ui_unchecked_icon.setter
    def ui_unchecked_icon(self, value):
        self._set_prop("unchecked-icon", value)

    @property
    def ui_indeterminate_icon(self):
        """The icon to be used when the model is indeterminate"""
        return self._props.get("indeterminate-icon")

    @ui_indeterminate_icon.setter
    def ui_indeterminate_icon(self, value):
        self._set_prop("indeterminate-icon", value)

    @property
    def ui_icon_color(self):
        """Override default icon color (for truthy state only); Color name for component from the Quasar Color Palette"""
        return self._props.get("icon-color")

    @ui_icon_color.setter
    def ui_icon_color(self, value):
        self._set_prop("icon-color", value)

    @property
    def ui_model_value(self):
        return self._props.get("model-value")

    @ui_model_value.setter
    def ui_model_value(self, value):
        self._set_prop("model-value", value)

    @property
    def ui_val(self):
        """Works when model ('value') is Array. It tells the component which value should add/remove when ticked/unticked"""
        return self._props.get("val")

    @ui_val.setter
    def ui_val(self, value):
        self._set_prop("val", value)

    @property
    def ui_true_value(self):
        """What model value should be considered as checked/ticked/on?"""
        return self._props.get("true-value")

    @ui_true_value.setter
    def ui_true_value(self, value):
        self._set_prop("true-value", value)

    @property
    def ui_false_value(self):
        """What model value should be considered as unchecked/unticked/off?"""
        return self._props.get("false-value")

    @ui_false_value.setter
    def ui_false_value(self, value):
        self._set_prop("false-value", value)

    @property
    def ui_indeterminate_value(self):
        """What model value should be considered as 'indeterminate'?"""
        return self._props.get("indeterminate-value")

    @ui_indeterminate_value.setter
    def ui_indeterminate_value(self, value):
        self._set_prop("indeterminate-value", value)

    @property
    def ui_toggle_order(self):
        """Determines toggle order of the two states ('t' stands for state of true, 'f' for state of false); If 'toggle-indeterminate' is true, then the order is: indet -> first state -> second state -> indet (and repeat), otherwise: indet -> first state -> second state -> first state -> second state -> ..."""
        return self._props.get("toggle-order")

    @ui_toggle_order.setter
    def ui_toggle_order(self, value):
        self._set_prop("toggle-order", value)

    @property
    def ui_toggle_indeterminate(self):
        """When user clicks/taps on the component, should we toggle through the indeterminate state too?"""
        return self._props.get("toggle-indeterminate")

    @ui_toggle_indeterminate.setter
    def ui_toggle_indeterminate(self, value):
        self._set_prop("toggle-indeterminate", value)

    @property
    def ui_label(self):
        """Label to display along the component (or use the default slot instead of this prop)"""
        return self._props.get("label")

    @ui_label.setter
    def ui_label(self, value):
        self._set_prop("label", value)

    @property
    def ui_left_label(self):
        """Label (if any specified) should be displayed on the left side of the component"""
        return self._props.get("left-label")

    @ui_left_label.setter
    def ui_left_label(self, value):
        self._set_prop("left-label", value)

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_keep_color(self):
        """Should the color (if specified any) be kept when the component is unticked/ off?"""
        return self._props.get("keep-color")

    @ui_keep_color.setter
    def ui_keep_color(self, value):
        self._set_prop("keep-color", value)

    @property
    def ui_dark(self):
        return self._props.get("dark")

    @ui_dark.setter
    def ui_dark(self, value):
        self._set_prop("dark", value)

    @property
    def ui_dense(self):
        return self._props.get("dense")

    @ui_dense.setter
    def ui_dense(self, value):
        self._set_prop("dense", value)

    @property
    def ui_disable(self):
        return self._props.get("disable")

    @ui_disable.setter
    def ui_disable(self, value):
        self._set_prop("disable", value)

    @property
    def ui_tabindex(self):
        return self._props.get("tabindex")

    @ui_tabindex.setter
    def ui_tabindex(self, value):
        self._set_prop("tabindex", value)

    @property
    def ui_size(self):
        """Size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl)"""
        return self._props.get("size")

    @ui_size.setter
    def ui_size(self, value):
        self._set_prop("size", value)

    @property
    def ui_name(self):
        """Used to specify the name of the control; Useful if dealing with forms submitted directly to a URL"""
        return self._props.get("name")

    @ui_name.setter
    def ui_name(self, value):
        self._set_prop("name", value)

    def on_update_model_value(self, handler: Callable, arg: object = None):
        """
        Emitted when the component needs to change the model; Is also used by v-model

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("update:model-value", handler, arg)

    def ui_toggle(self):
        """Toggle the state (of the model)"""
        self._js_call_method("toggle")

    def _get_js_methods(self):
        return ["toggle"]


class QToolbarTitle(Component):
    """
    Quasar Component: `QToolbarTitle <https://v2.quasar.dev/vue-components/toolbar>`__

    :param ui_shrink: By default, QToolbarTitle is set to grow to the available space. However, you can reverse that with this prop
    """

    def __init__(self, *children, ui_shrink: bool | None = None, **kwargs):
        super().__init__("QToolbarTitle", *children, **kwargs)
        if ui_shrink is not None:
            self._props["shrink"] = ui_shrink

    @property
    def ui_shrink(self):
        """By default, QToolbarTitle is set to grow to the available space. However, you can reverse that with this prop"""
        return self._props.get("shrink")

    @ui_shrink.setter
    def ui_shrink(self, value):
        self._set_prop("shrink", value)

    def _get_js_methods(self):
        return []


class QToolbar(Component):
    """
    Quasar Component: `QToolbar <https://v2.quasar.dev/vue-components/toolbar>`__

    :param ui_inset: Apply an inset to content (useful for subsequent toolbars)
    """

    def __init__(self, *children, ui_inset: bool | None = None, **kwargs):
        super().__init__("QToolbar", *children, **kwargs)
        if ui_inset is not None:
            self._props["inset"] = ui_inset

    @property
    def ui_inset(self):
        """Apply an inset to content (useful for subsequent toolbars)"""
        return self._props.get("inset")

    @ui_inset.setter
    def ui_inset(self, value):
        self._set_prop("inset", value)

    def _get_js_methods(self):
        return []


class QTooltip(Component):
    """
    Quasar Component: `QTooltip <https://v2.quasar.dev/vue-components/tooltip>`__

    :param ui_max_height: The maximum height of the Tooltip; Size in CSS units, including unit name
    :param ui_max_width: The maximum width of the Tooltip; Size in CSS units, including unit name
    :param ui_transition_show:
    :param ui_transition_hide:
    :param ui_anchor: Two values setting the starting position or anchor point of the Tooltip relative to its target
    :param ui_self: Two values setting the Tooltip's own position relative to its target
    :param ui_offset: An array of two numbers to offset the Tooltip horizontally and vertically in pixels
    :param ui_scroll_target:
    :param ui_delay: Configure Tooltip to appear with delay
    :param ui_hide_delay: Configure Tooltip to disappear with delay
    :param ui_persistent: Prevents Tooltip from auto-closing when app's route changes
    :param ui_model_value: Model of the component defining shown/hidden state; Either use this property (along with a listener for 'update:model-value' event) OR use v-model directive
    :param ui_target: Configure a target element to trigger component toggle; 'true' means it enables the parent DOM element, 'false' means it disables attaching events to any DOM elements; By using a String (CSS selector) or a DOM element it attaches the events to the specified DOM element (if it exists)
    :param ui_no_parent_event: Skips attaching events to the target DOM element (that trigger the element to get shown)
    :param ui_transition_duration: Transition duration (in milliseconds, without unit)
    """

    def __init__(
        self,
        *children,
        ui_max_height: str | None = None,
        ui_max_width: str | None = None,
        ui_transition_show: Any | None = None,
        ui_transition_hide: Any | None = None,
        ui_anchor: str | None = None,
        ui_self: str | None = None,
        ui_offset: list | None = None,
        ui_scroll_target: Any | None = None,
        ui_delay: float | None = None,
        ui_hide_delay: float | None = None,
        ui_persistent: bool | None = None,
        ui_model_value: bool | None = None,
        ui_target: bool | str | Any | None = None,
        ui_no_parent_event: bool | None = None,
        ui_transition_duration: str | float | None = None,
        **kwargs,
    ):
        super().__init__("QTooltip", *children, **kwargs)
        self.on("update:model-value", self.__update_model_value)

        if ui_max_height is not None:
            self._props["max-height"] = ui_max_height
        if ui_max_width is not None:
            self._props["max-width"] = ui_max_width
        if ui_transition_show is not None:
            self._props["transition-show"] = ui_transition_show
        if ui_transition_hide is not None:
            self._props["transition-hide"] = ui_transition_hide
        if ui_anchor is not None:
            self._props["anchor"] = ui_anchor
        if ui_self is not None:
            self._props["self"] = ui_self
        if ui_offset is not None:
            self._props["offset"] = ui_offset
        if ui_scroll_target is not None:
            self._props["scroll-target"] = ui_scroll_target
        if ui_delay is not None:
            self._props["delay"] = ui_delay
        if ui_hide_delay is not None:
            self._props["hide-delay"] = ui_hide_delay
        if ui_persistent is not None:
            self._props["persistent"] = ui_persistent
        if ui_model_value is not None:
            self._props["model-value"] = ui_model_value
        if ui_target is not None:
            self._props["target"] = ui_target
        if ui_no_parent_event is not None:
            self._props["no-parent-event"] = ui_no_parent_event
        if ui_transition_duration is not None:
            self._props["transition-duration"] = ui_transition_duration

    def __update_model_value(self, event: Event):
        self._set_prop("model-value", event.value)

    @property
    def ui_max_height(self):
        """The maximum height of the Tooltip; Size in CSS units, including unit name"""
        return self._props.get("max-height")

    @ui_max_height.setter
    def ui_max_height(self, value):
        self._set_prop("max-height", value)

    @property
    def ui_max_width(self):
        """The maximum width of the Tooltip; Size in CSS units, including unit name"""
        return self._props.get("max-width")

    @ui_max_width.setter
    def ui_max_width(self, value):
        self._set_prop("max-width", value)

    @property
    def ui_transition_show(self):
        return self._props.get("transition-show")

    @ui_transition_show.setter
    def ui_transition_show(self, value):
        self._set_prop("transition-show", value)

    @property
    def ui_transition_hide(self):
        return self._props.get("transition-hide")

    @ui_transition_hide.setter
    def ui_transition_hide(self, value):
        self._set_prop("transition-hide", value)

    @property
    def ui_anchor(self):
        """Two values setting the starting position or anchor point of the Tooltip relative to its target"""
        return self._props.get("anchor")

    @ui_anchor.setter
    def ui_anchor(self, value):
        self._set_prop("anchor", value)

    @property
    def ui_self(self):
        """Two values setting the Tooltip's own position relative to its target"""
        return self._props.get("self")

    @ui_self.setter
    def ui_self(self, value):
        self._set_prop("self", value)

    @property
    def ui_offset(self):
        """An array of two numbers to offset the Tooltip horizontally and vertically in pixels"""
        return self._props.get("offset")

    @ui_offset.setter
    def ui_offset(self, value):
        self._set_prop("offset", value)

    @property
    def ui_scroll_target(self):
        return self._props.get("scroll-target")

    @ui_scroll_target.setter
    def ui_scroll_target(self, value):
        self._set_prop("scroll-target", value)

    @property
    def ui_delay(self):
        """Configure Tooltip to appear with delay"""
        return self._props.get("delay")

    @ui_delay.setter
    def ui_delay(self, value):
        self._set_prop("delay", value)

    @property
    def ui_hide_delay(self):
        """Configure Tooltip to disappear with delay"""
        return self._props.get("hide-delay")

    @ui_hide_delay.setter
    def ui_hide_delay(self, value):
        self._set_prop("hide-delay", value)

    @property
    def ui_persistent(self):
        """Prevents Tooltip from auto-closing when app's route changes"""
        return self._props.get("persistent")

    @ui_persistent.setter
    def ui_persistent(self, value):
        self._set_prop("persistent", value)

    @property
    def ui_model_value(self):
        """Model of the component defining shown/hidden state; Either use this property (along with a listener for 'update:model-value' event) OR use v-model directive"""
        return self._props.get("model-value")

    @ui_model_value.setter
    def ui_model_value(self, value):
        self._set_prop("model-value", value)

    @property
    def ui_target(self):
        """Configure a target element to trigger component toggle; 'true' means it enables the parent DOM element, 'false' means it disables attaching events to any DOM elements; By using a String (CSS selector) or a DOM element it attaches the events to the specified DOM element (if it exists)"""
        return self._props.get("target")

    @ui_target.setter
    def ui_target(self, value):
        self._set_prop("target", value)

    @property
    def ui_no_parent_event(self):
        """Skips attaching events to the target DOM element (that trigger the element to get shown)"""
        return self._props.get("no-parent-event")

    @ui_no_parent_event.setter
    def ui_no_parent_event(self, value):
        self._set_prop("no-parent-event", value)

    @property
    def ui_transition_duration(self):
        """Transition duration (in milliseconds, without unit)"""
        return self._props.get("transition-duration")

    @ui_transition_duration.setter
    def ui_transition_duration(self, value):
        self._set_prop("transition-duration", value)

    def on_before_hide(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("before-hide", handler, arg)

    def on_before_show(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("before-show", handler, arg)

    def on_hide(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("hide", handler, arg)

    def on_show(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("show", handler, arg)

    def on_update_model_value(self, handler: Callable, arg: object = None):
        """
        Emitted when showing/hidden state changes; Is also used by v-model

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("update:model-value", handler, arg)

    def ui_hide(self):
        self._js_call_method("hide")

    def ui_show(self):
        self._js_call_method("show")

    def ui_toggle(self):
        self._js_call_method("toggle")

    def ui_updatePosition(self):
        """There are some custom scenarios for which Quasar cannot automatically reposition the tooltip without significant performance drawbacks so the optimal solution is for you to call this method when you need it"""
        self._js_call_method("updatePosition")

    def _get_js_methods(self):
        return ["hide", "show", "toggle", "updatePosition"]


class QTree(Component):
    """
    Quasar Component: `QTree <https://v2.quasar.dev/vue-components/tree>`__

    :param ui_nodes: The array of nodes that designates the tree structure
    :param ui_node_key: The property name of each node object that holds a unique node id
    :param ui_label_key: The property name of each node object that holds the label of the node
    :param ui_children_key: The property name of each node object that holds the list of children of the node
    :param ui_no_connectors: Do not display the connector lines between nodes
    :param ui_color:
    :param ui_control_color: Color name for controls (like checkboxes) from the Quasar Color Palette
    :param ui_text_color:
    :param ui_selected_color: Color name for selected nodes (from the Quasar Color Palette)
    :param ui_dense:
    :param ui_dark:
    :param ui_icon:
    :param ui_tick_strategy: The type of strategy to use for the selection of the nodes
    :param ui_ticked: Keys of nodes that are ticked
    :param ui_expanded: Keys of nodes that are expanded
    :param ui_selected: Key of node currently selected
    :param ui_no_selection_unset: Do not allow un-selection when clicking currently selected node
    :param ui_default_expand_all: Allow the tree to have all its branches expanded, when first rendered
    :param ui_accordion: Allows the tree to be set in accordion mode
    :param ui_no_transition: Turn off transition effects when expanding/collapsing nodes; Also enhances perf by a lot as a side-effect; Recommended for big trees
    :param ui_filter: The text value to be used for filtering nodes
    :param ui_filter_method: The function to use to filter the tree nodes; For best performance, reference it from your scope and do not define it inline
    :param ui_duration: Toggle animation duration (in milliseconds)
    :param ui_no_nodes_label: Override default such label for when no nodes are available
    :param ui_no_results_label: Override default such label for when no nodes are available due to filtering
    """

    def __init__(
        self,
        *children,
        ui_nodes: list | None = None,
        ui_node_key: str | None = None,
        ui_label_key: str | None = None,
        ui_children_key: str | None = None,
        ui_no_connectors: bool | None = None,
        ui_color: Any | None = None,
        ui_control_color: Any | None = None,
        ui_text_color: Any | None = None,
        ui_selected_color: Any | None = None,
        ui_dense: Any | None = None,
        ui_dark: Any | None = None,
        ui_icon: Any | None = None,
        ui_tick_strategy: str | None = None,
        ui_ticked: list | None = None,
        ui_expanded: list | None = None,
        ui_selected: Any | None = None,
        ui_no_selection_unset: bool | None = None,
        ui_default_expand_all: bool | None = None,
        ui_accordion: bool | None = None,
        ui_no_transition: bool | None = None,
        ui_filter: str | None = None,
        ui_filter_method: Callable | None = None,
        ui_duration: float | None = None,
        ui_no_nodes_label: str | None = None,
        ui_no_results_label: str | None = None,
        **kwargs,
    ):
        super().__init__("QTree", *children, **kwargs)
        if ui_nodes is not None:
            self._props["nodes"] = ui_nodes
        if ui_node_key is not None:
            self._props["node-key"] = ui_node_key
        if ui_label_key is not None:
            self._props["label-key"] = ui_label_key
        if ui_children_key is not None:
            self._props["children-key"] = ui_children_key
        if ui_no_connectors is not None:
            self._props["no-connectors"] = ui_no_connectors
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_control_color is not None:
            self._props["control-color"] = ui_control_color
        if ui_text_color is not None:
            self._props["text-color"] = ui_text_color
        if ui_selected_color is not None:
            self._props["selected-color"] = ui_selected_color
        if ui_dense is not None:
            self._props["dense"] = ui_dense
        if ui_dark is not None:
            self._props["dark"] = ui_dark
        if ui_icon is not None:
            self._props["icon"] = ui_icon
        if ui_tick_strategy is not None:
            self._props["tick-strategy"] = ui_tick_strategy
        if ui_ticked is not None:
            self._props["ticked"] = ui_ticked
        if ui_expanded is not None:
            self._props["expanded"] = ui_expanded
        if ui_selected is not None:
            self._props["selected"] = ui_selected
        if ui_no_selection_unset is not None:
            self._props["no-selection-unset"] = ui_no_selection_unset
        if ui_default_expand_all is not None:
            self._props["default-expand-all"] = ui_default_expand_all
        if ui_accordion is not None:
            self._props["accordion"] = ui_accordion
        if ui_no_transition is not None:
            self._props["no-transition"] = ui_no_transition
        if ui_filter is not None:
            self._props["filter"] = ui_filter
        if ui_filter_method is not None:
            self._props["filter-method"] = ui_filter_method
        if ui_duration is not None:
            self._props["duration"] = ui_duration
        if ui_no_nodes_label is not None:
            self._props["no-nodes-label"] = ui_no_nodes_label
        if ui_no_results_label is not None:
            self._props["no-results-label"] = ui_no_results_label

    @property
    def ui_nodes(self):
        """The array of nodes that designates the tree structure"""
        return self._props.get("nodes")

    @ui_nodes.setter
    def ui_nodes(self, value):
        self._set_prop("nodes", value)

    @property
    def ui_node_key(self):
        """The property name of each node object that holds a unique node id"""
        return self._props.get("node-key")

    @ui_node_key.setter
    def ui_node_key(self, value):
        self._set_prop("node-key", value)

    @property
    def ui_label_key(self):
        """The property name of each node object that holds the label of the node"""
        return self._props.get("label-key")

    @ui_label_key.setter
    def ui_label_key(self, value):
        self._set_prop("label-key", value)

    @property
    def ui_children_key(self):
        """The property name of each node object that holds the list of children of the node"""
        return self._props.get("children-key")

    @ui_children_key.setter
    def ui_children_key(self, value):
        self._set_prop("children-key", value)

    @property
    def ui_no_connectors(self):
        """Do not display the connector lines between nodes"""
        return self._props.get("no-connectors")

    @ui_no_connectors.setter
    def ui_no_connectors(self, value):
        self._set_prop("no-connectors", value)

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_control_color(self):
        """Color name for controls (like checkboxes) from the Quasar Color Palette"""
        return self._props.get("control-color")

    @ui_control_color.setter
    def ui_control_color(self, value):
        self._set_prop("control-color", value)

    @property
    def ui_text_color(self):
        return self._props.get("text-color")

    @ui_text_color.setter
    def ui_text_color(self, value):
        self._set_prop("text-color", value)

    @property
    def ui_selected_color(self):
        """Color name for selected nodes (from the Quasar Color Palette)"""
        return self._props.get("selected-color")

    @ui_selected_color.setter
    def ui_selected_color(self, value):
        self._set_prop("selected-color", value)

    @property
    def ui_dense(self):
        return self._props.get("dense")

    @ui_dense.setter
    def ui_dense(self, value):
        self._set_prop("dense", value)

    @property
    def ui_dark(self):
        return self._props.get("dark")

    @ui_dark.setter
    def ui_dark(self, value):
        self._set_prop("dark", value)

    @property
    def ui_icon(self):
        return self._props.get("icon")

    @ui_icon.setter
    def ui_icon(self, value):
        self._set_prop("icon", value)

    @property
    def ui_tick_strategy(self):
        """The type of strategy to use for the selection of the nodes"""
        return self._props.get("tick-strategy")

    @ui_tick_strategy.setter
    def ui_tick_strategy(self, value):
        self._set_prop("tick-strategy", value)

    @property
    def ui_ticked(self):
        """Keys of nodes that are ticked"""
        return self._props.get("ticked")

    @ui_ticked.setter
    def ui_ticked(self, value):
        self._set_prop("ticked", value)

    @property
    def ui_expanded(self):
        """Keys of nodes that are expanded"""
        return self._props.get("expanded")

    @ui_expanded.setter
    def ui_expanded(self, value):
        self._set_prop("expanded", value)

    @property
    def ui_selected(self):
        """Key of node currently selected"""
        return self._props.get("selected")

    @ui_selected.setter
    def ui_selected(self, value):
        self._set_prop("selected", value)

    @property
    def ui_no_selection_unset(self):
        """Do not allow un-selection when clicking currently selected node"""
        return self._props.get("no-selection-unset")

    @ui_no_selection_unset.setter
    def ui_no_selection_unset(self, value):
        self._set_prop("no-selection-unset", value)

    @property
    def ui_default_expand_all(self):
        """Allow the tree to have all its branches expanded, when first rendered"""
        return self._props.get("default-expand-all")

    @ui_default_expand_all.setter
    def ui_default_expand_all(self, value):
        self._set_prop("default-expand-all", value)

    @property
    def ui_accordion(self):
        """Allows the tree to be set in accordion mode"""
        return self._props.get("accordion")

    @ui_accordion.setter
    def ui_accordion(self, value):
        self._set_prop("accordion", value)

    @property
    def ui_no_transition(self):
        """Turn off transition effects when expanding/collapsing nodes; Also enhances perf by a lot as a side-effect; Recommended for big trees"""
        return self._props.get("no-transition")

    @ui_no_transition.setter
    def ui_no_transition(self, value):
        self._set_prop("no-transition", value)

    @property
    def ui_filter(self):
        """The text value to be used for filtering nodes"""
        return self._props.get("filter")

    @ui_filter.setter
    def ui_filter(self, value):
        self._set_prop("filter", value)

    @property
    def ui_filter_method(self):
        """The function to use to filter the tree nodes; For best performance, reference it from your scope and do not define it inline"""
        return self._props.get("filter-method")

    @ui_filter_method.setter
    def ui_filter_method(self, value):
        self._set_prop("filter-method", value)

    @property
    def ui_duration(self):
        """Toggle animation duration (in milliseconds)"""
        return self._props.get("duration")

    @ui_duration.setter
    def ui_duration(self, value):
        self._set_prop("duration", value)

    @property
    def ui_no_nodes_label(self):
        """Override default such label for when no nodes are available"""
        return self._props.get("no-nodes-label")

    @ui_no_nodes_label.setter
    def ui_no_nodes_label(self, value):
        self._set_prop("no-nodes-label", value)

    @property
    def ui_no_results_label(self):
        """Override default such label for when no nodes are available due to filtering"""
        return self._props.get("no-results-label")

    @ui_no_results_label.setter
    def ui_no_results_label(self, value):
        self._set_prop("no-results-label", value)

    def ui_slot_body_name(self, name, value):
        """Body template slot for describing node body; Used by nodes which have their 'body' prop set to '[name]', where '[name]' can be any string"""
        self._set_slot("body-" + name, value)

    @property
    def ui_slot_default_body(self):
        """Slot to use for defining the body of a node"""
        return self.ui_slots.get("default-body", [])

    @ui_slot_default_body.setter
    def ui_slot_default_body(self, value):
        self._set_slot("default-body", value)

    @property
    def ui_slot_default_header(self):
        """Slot to use for defining the header of a node"""
        return self.ui_slots.get("default-header", [])

    @ui_slot_default_header.setter
    def ui_slot_default_header(self, value):
        self._set_slot("default-header", value)

    def ui_slot_header_name(self, name, value):
        """Header template slot for describing node header; Used by nodes which have their 'header' prop set to '[name]', where '[name]' can be any string"""
        self._set_slot("header-" + name, value)

    def on_after_hide(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("after-hide", handler, arg)

    def on_after_show(self, handler: Callable, arg: object = None):
        """


        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("after-show", handler, arg)

    def on_lazy_load(self, handler: Callable, arg: object = None):
        """
        Emitted when the lazy loading of nodes is finished

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("lazy-load", handler, arg)

    def on_update_expanded(self, handler: Callable, arg: object = None):
        """
        Triggered when nodes are expanded or collapsed; Used by Vue on 'v-model:update' to update its value

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("update:expanded", handler, arg)

    def on_update_selected(self, handler: Callable, arg: object = None):
        """
        Emitted when selected node changes; Used by Vue on 'v-model:selected' to update its value

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("update:selected", handler, arg)

    def on_update_ticked(self, handler: Callable, arg: object = None):
        """
        Emitted when nodes are ticked/unticked via the checkbox; Used by Vue on 'v-model:ticked' to update its value

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("update:ticked", handler, arg)

    def ui_collapseAll(self):
        """Use to collapse all branches of the tree"""
        self._js_call_method("collapseAll")

    def ui_expandAll(self):
        """Use to expand all branches of the tree"""
        self._js_call_method("expandAll")

    def ui_getExpandedNodes(self):
        """Get array of nodes that are expanded"""
        self._js_call_method("getExpandedNodes")

    def ui_getNodeByKey(self, ui_key):
        """Get the node with the given key"""
        kwargs = {}
        if ui_key is not None:
            kwargs["key"] = ui_key
        self._js_call_method("getNodeByKey", [kwargs])

    def ui_getTickedNodes(self):
        """Get array of nodes that are ticked"""
        self._js_call_method("getTickedNodes")

    def ui_isExpanded(self, ui_key):
        """Determine if a node is expanded"""
        kwargs = {}
        if ui_key is not None:
            kwargs["key"] = ui_key
        self._js_call_method("isExpanded", [kwargs])

    def ui_isTicked(self, ui_key):
        """Method to check if a node's checkbox is selected or not"""
        kwargs = {}
        if ui_key is not None:
            kwargs["key"] = ui_key
        self._js_call_method("isTicked", [kwargs])

    def ui_setExpanded(self, ui_key, ui_state):
        """Expands the tree at the point of the node with the key given"""
        kwargs = {}
        if ui_key is not None:
            kwargs["key"] = ui_key
        if ui_state is not None:
            kwargs["state"] = ui_state
        self._js_call_method("setExpanded", [kwargs])

    def ui_setTicked(self, ui_keys, ui_state):
        """Method to set a node's checkbox programmatically"""
        kwargs = {}
        if ui_keys is not None:
            kwargs["keys"] = ui_keys
        if ui_state is not None:
            kwargs["state"] = ui_state
        self._js_call_method("setTicked", [kwargs])

    def _get_js_methods(self):
        return [
            "collapseAll",
            "expandAll",
            "getExpandedNodes",
            "getNodeByKey",
            "getTickedNodes",
            "isExpanded",
            "isTicked",
            "setExpanded",
            "setTicked",
        ]


class QUploader(Component):
    """
    Quasar Component: `QUploader <https://v2.quasar.dev/vue-components/uploader>`__

    :param ui_label: Label for the uploader
    :param ui_color:
    :param ui_text_color:
    :param ui_dark:
    :param ui_square:
    :param ui_flat:
    :param ui_bordered:
    :param ui_no_thumbnails: Don't display thumbnails for image files
    :param ui_auto_upload: Upload files immediately when added
    :param ui_hide_upload_btn: Don't show the upload button
    :param ui_thumbnail_fit: How the thumbnail image will fit into the container; Equivalent of the background-size prop
    :param ui_disable:
    :param ui_readonly:
    :param ui_multiple: Allow multiple file uploads
    :param ui_accept: Comma separated list of unique file type specifiers. Maps to 'accept' attribute of native input type=file element
    :param ui_capture: Optionally, specify that a new file should be captured, and which device should be used to capture that new media of a type defined by the 'accept' prop. Maps to 'capture' attribute of native input type=file element
    :param ui_max_file_size: Maximum size of individual file in bytes
    :param ui_max_total_size: Maximum size of all files combined in bytes
    :param ui_max_files: Maximum number of files to contain
    :param ui_filter: Custom filter for added files; Only files that pass this filter will be added to the queue and uploaded; For best performance, reference it from your scope and do not define it inline
    :param ui_factory: Function which should return an Object or a Promise resolving with an Object; For best performance, reference it from your scope and do not define it inline
    :param ui_url: URL or path to the server which handles the upload. Takes String or factory function, which returns String. Function is called right before upload; If using a function then for best performance, reference it from your scope and do not define it inline
    :param ui_method: HTTP method to use for upload; Takes String or factory function which returns a String; Function is called right before upload; If using a function then for best performance, reference it from your scope and do not define it inline
    :param ui_field_name: Field name for each file upload; This goes into the following header: 'Content-Disposition: form-data; name="__HERE__"; filename="somefile.png"; If using a function then for best performance, reference it from your scope and do not define it inline
    :param ui_headers: Array or a factory function which returns an array; Array consists of objects with header definitions; Function is called right before upload; If using a function then for best performance, reference it from your scope and do not define it inline
    :param ui_form_fields: Array or a factory function which returns an array; Array consists of objects with additional fields definitions (used by Form to be uploaded); Function is called right before upload; If using a function then for best performance, reference it from your scope and do not define it inline
    :param ui_with_credentials: Sets withCredentials to true on the XHR that manages the upload; Takes boolean or factory function for Boolean; Function is called right before upload; If using a function then for best performance, reference it from your scope and do not define it inline
    :param ui_send_raw: Send raw files without wrapping into a Form(); Takes boolean or factory function for Boolean; Function is called right before upload; If using a function then for best performance, reference it from your scope and do not define it inline
    :param ui_batch: Upload files in batch (in one XHR request); Takes boolean or factory function for Boolean; Function is called right before upload; If using a function then for best performance, reference it from your scope and do not define it inline
    """

    def __init__(
        self,
        *children,
        ui_label: str | None = None,
        ui_color: Any | None = None,
        ui_text_color: Any | None = None,
        ui_dark: Any | None = None,
        ui_square: Any | None = None,
        ui_flat: Any | None = None,
        ui_bordered: Any | None = None,
        ui_no_thumbnails: bool | None = None,
        ui_auto_upload: bool | None = None,
        ui_hide_upload_btn: bool | None = None,
        ui_thumbnail_fit: str | None = None,
        ui_disable: Any | None = None,
        ui_readonly: Any | None = None,
        ui_multiple: bool | None = None,
        ui_accept: str | None = None,
        ui_capture: str | None = None,
        ui_max_file_size: float | str | None = None,
        ui_max_total_size: float | str | None = None,
        ui_max_files: float | str | None = None,
        ui_filter: Callable | None = None,
        ui_factory: Callable | None = None,
        ui_url: str | Callable | None = None,
        ui_method: str | Callable | None = None,
        ui_field_name: str | Callable | None = None,
        ui_headers: list | Callable | None = None,
        ui_form_fields: list | Callable | None = None,
        ui_with_credentials: bool | Callable | None = None,
        ui_send_raw: bool | Callable | None = None,
        ui_batch: bool | Callable | None = None,
        **kwargs,
    ):
        super().__init__("QUploader", *children, **kwargs)
        if ui_label is not None:
            self._props["label"] = ui_label
        if ui_color is not None:
            self._props["color"] = ui_color
        if ui_text_color is not None:
            self._props["text-color"] = ui_text_color
        if ui_dark is not None:
            self._props["dark"] = ui_dark
        if ui_square is not None:
            self._props["square"] = ui_square
        if ui_flat is not None:
            self._props["flat"] = ui_flat
        if ui_bordered is not None:
            self._props["bordered"] = ui_bordered
        if ui_no_thumbnails is not None:
            self._props["no-thumbnails"] = ui_no_thumbnails
        if ui_auto_upload is not None:
            self._props["auto-upload"] = ui_auto_upload
        if ui_hide_upload_btn is not None:
            self._props["hide-upload-btn"] = ui_hide_upload_btn
        if ui_thumbnail_fit is not None:
            self._props["thumbnail-fit"] = ui_thumbnail_fit
        if ui_disable is not None:
            self._props["disable"] = ui_disable
        if ui_readonly is not None:
            self._props["readonly"] = ui_readonly
        if ui_multiple is not None:
            self._props["multiple"] = ui_multiple
        if ui_accept is not None:
            self._props["accept"] = ui_accept
        if ui_capture is not None:
            self._props["capture"] = ui_capture
        if ui_max_file_size is not None:
            self._props["max-file-size"] = ui_max_file_size
        if ui_max_total_size is not None:
            self._props["max-total-size"] = ui_max_total_size
        if ui_max_files is not None:
            self._props["max-files"] = ui_max_files
        if ui_filter is not None:
            self._props["filter"] = ui_filter
        if ui_factory is not None:
            self._props["factory"] = ui_factory
        if ui_url is not None:
            self._props["url"] = ui_url
        if ui_method is not None:
            self._props["method"] = ui_method
        if ui_field_name is not None:
            self._props["field-name"] = ui_field_name
        if ui_headers is not None:
            self._props["headers"] = ui_headers
        if ui_form_fields is not None:
            self._props["form-fields"] = ui_form_fields
        if ui_with_credentials is not None:
            self._props["with-credentials"] = ui_with_credentials
        if ui_send_raw is not None:
            self._props["send-raw"] = ui_send_raw
        if ui_batch is not None:
            self._props["batch"] = ui_batch

    @property
    def ui_label(self):
        """Label for the uploader"""
        return self._props.get("label")

    @ui_label.setter
    def ui_label(self, value):
        self._set_prop("label", value)

    @property
    def ui_color(self):
        return self._props.get("color")

    @ui_color.setter
    def ui_color(self, value):
        self._set_prop("color", value)

    @property
    def ui_text_color(self):
        return self._props.get("text-color")

    @ui_text_color.setter
    def ui_text_color(self, value):
        self._set_prop("text-color", value)

    @property
    def ui_dark(self):
        return self._props.get("dark")

    @ui_dark.setter
    def ui_dark(self, value):
        self._set_prop("dark", value)

    @property
    def ui_square(self):
        return self._props.get("square")

    @ui_square.setter
    def ui_square(self, value):
        self._set_prop("square", value)

    @property
    def ui_flat(self):
        return self._props.get("flat")

    @ui_flat.setter
    def ui_flat(self, value):
        self._set_prop("flat", value)

    @property
    def ui_bordered(self):
        return self._props.get("bordered")

    @ui_bordered.setter
    def ui_bordered(self, value):
        self._set_prop("bordered", value)

    @property
    def ui_no_thumbnails(self):
        """Don't display thumbnails for image files"""
        return self._props.get("no-thumbnails")

    @ui_no_thumbnails.setter
    def ui_no_thumbnails(self, value):
        self._set_prop("no-thumbnails", value)

    @property
    def ui_auto_upload(self):
        """Upload files immediately when added"""
        return self._props.get("auto-upload")

    @ui_auto_upload.setter
    def ui_auto_upload(self, value):
        self._set_prop("auto-upload", value)

    @property
    def ui_hide_upload_btn(self):
        """Don't show the upload button"""
        return self._props.get("hide-upload-btn")

    @ui_hide_upload_btn.setter
    def ui_hide_upload_btn(self, value):
        self._set_prop("hide-upload-btn", value)

    @property
    def ui_thumbnail_fit(self):
        """How the thumbnail image will fit into the container; Equivalent of the background-size prop"""
        return self._props.get("thumbnail-fit")

    @ui_thumbnail_fit.setter
    def ui_thumbnail_fit(self, value):
        self._set_prop("thumbnail-fit", value)

    @property
    def ui_disable(self):
        return self._props.get("disable")

    @ui_disable.setter
    def ui_disable(self, value):
        self._set_prop("disable", value)

    @property
    def ui_readonly(self):
        return self._props.get("readonly")

    @ui_readonly.setter
    def ui_readonly(self, value):
        self._set_prop("readonly", value)

    @property
    def ui_multiple(self):
        """Allow multiple file uploads"""
        return self._props.get("multiple")

    @ui_multiple.setter
    def ui_multiple(self, value):
        self._set_prop("multiple", value)

    @property
    def ui_accept(self):
        """Comma separated list of unique file type specifiers. Maps to 'accept' attribute of native input type=file element"""
        return self._props.get("accept")

    @ui_accept.setter
    def ui_accept(self, value):
        self._set_prop("accept", value)

    @property
    def ui_capture(self):
        """Optionally, specify that a new file should be captured, and which device should be used to capture that new media of a type defined by the 'accept' prop. Maps to 'capture' attribute of native input type=file element"""
        return self._props.get("capture")

    @ui_capture.setter
    def ui_capture(self, value):
        self._set_prop("capture", value)

    @property
    def ui_max_file_size(self):
        """Maximum size of individual file in bytes"""
        return self._props.get("max-file-size")

    @ui_max_file_size.setter
    def ui_max_file_size(self, value):
        self._set_prop("max-file-size", value)

    @property
    def ui_max_total_size(self):
        """Maximum size of all files combined in bytes"""
        return self._props.get("max-total-size")

    @ui_max_total_size.setter
    def ui_max_total_size(self, value):
        self._set_prop("max-total-size", value)

    @property
    def ui_max_files(self):
        """Maximum number of files to contain"""
        return self._props.get("max-files")

    @ui_max_files.setter
    def ui_max_files(self, value):
        self._set_prop("max-files", value)

    @property
    def ui_filter(self):
        """Custom filter for added files; Only files that pass this filter will be added to the queue and uploaded; For best performance, reference it from your scope and do not define it inline"""
        return self._props.get("filter")

    @ui_filter.setter
    def ui_filter(self, value):
        self._set_prop("filter", value)

    @property
    def ui_factory(self):
        """Function which should return an Object or a Promise resolving with an Object; For best performance, reference it from your scope and do not define it inline"""
        return self._props.get("factory")

    @ui_factory.setter
    def ui_factory(self, value):
        self._set_prop("factory", value)

    @property
    def ui_url(self):
        """URL or path to the server which handles the upload. Takes String or factory function, which returns String. Function is called right before upload; If using a function then for best performance, reference it from your scope and do not define it inline"""
        return self._props.get("url")

    @ui_url.setter
    def ui_url(self, value):
        self._set_prop("url", value)

    @property
    def ui_method(self):
        """HTTP method to use for upload; Takes String or factory function which returns a String; Function is called right before upload; If using a function then for best performance, reference it from your scope and do not define it inline"""
        return self._props.get("method")

    @ui_method.setter
    def ui_method(self, value):
        self._set_prop("method", value)

    @property
    def ui_field_name(self):
        """Field name for each file upload; This goes into the following header: 'Content-Disposition: form-data; name="__HERE__"; filename="somefile.png"; If using a function then for best performance, reference it from your scope and do not define it inline"""
        return self._props.get("field-name")

    @ui_field_name.setter
    def ui_field_name(self, value):
        self._set_prop("field-name", value)

    @property
    def ui_headers(self):
        """Array or a factory function which returns an array; Array consists of objects with header definitions; Function is called right before upload; If using a function then for best performance, reference it from your scope and do not define it inline"""
        return self._props.get("headers")

    @ui_headers.setter
    def ui_headers(self, value):
        self._set_prop("headers", value)

    @property
    def ui_form_fields(self):
        """Array or a factory function which returns an array; Array consists of objects with additional fields definitions (used by Form to be uploaded); Function is called right before upload; If using a function then for best performance, reference it from your scope and do not define it inline"""
        return self._props.get("form-fields")

    @ui_form_fields.setter
    def ui_form_fields(self, value):
        self._set_prop("form-fields", value)

    @property
    def ui_with_credentials(self):
        """Sets withCredentials to true on the XHR that manages the upload; Takes boolean or factory function for Boolean; Function is called right before upload; If using a function then for best performance, reference it from your scope and do not define it inline"""
        return self._props.get("with-credentials")

    @ui_with_credentials.setter
    def ui_with_credentials(self, value):
        self._set_prop("with-credentials", value)

    @property
    def ui_send_raw(self):
        """Send raw files without wrapping into a Form(); Takes boolean or factory function for Boolean; Function is called right before upload; If using a function then for best performance, reference it from your scope and do not define it inline"""
        return self._props.get("send-raw")

    @ui_send_raw.setter
    def ui_send_raw(self, value):
        self._set_prop("send-raw", value)

    @property
    def ui_batch(self):
        """Upload files in batch (in one XHR request); Takes boolean or factory function for Boolean; Function is called right before upload; If using a function then for best performance, reference it from your scope and do not define it inline"""
        return self._props.get("batch")

    @ui_batch.setter
    def ui_batch(self, value):
        self._set_prop("batch", value)

    @property
    def ui_slot_header(self):
        """Slot for custom header; Scope is the QUploader instance itself"""
        return self.ui_slots.get("header", [])

    @ui_slot_header.setter
    def ui_slot_header(self, value):
        self._set_slot("header", value)

    @property
    def ui_slot_list(self):
        """Slot for custom list; Scope is the QUploader instance itself"""
        return self.ui_slots.get("list", [])

    @ui_slot_list.setter
    def ui_slot_list(self, value):
        self._set_slot("list", value)

    def on_added(self, handler: Callable, arg: object = None):
        """
        Emitted when files are added into the list

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("added", handler, arg)

    def on_factory_failed(self, handler: Callable, arg: object = None):
        """
        Emitted when factory function is supplied with a Promise which is rejected

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("factory-failed", handler, arg)

    def on_failed(self, handler: Callable, arg: object = None):
        """
        Emitted when file or batch of files has encountered error while uploading

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("failed", handler, arg)

    def on_finish(self, handler: Callable, arg: object = None):
        """
        Finished working (regardless of success or fail)

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("finish", handler, arg)

    def on_rejected(self, handler: Callable, arg: object = None):
        """
        Emitted after files are picked and some do not pass the validation props (accept, max-file-size, max-total-size, filter, etc)

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("rejected", handler, arg)

    def on_removed(self, handler: Callable, arg: object = None):
        """
        Emitted when files are removed from the list

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("removed", handler, arg)

    def on_start(self, handler: Callable, arg: object = None):
        """
        Started working

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("start", handler, arg)

    def on_uploaded(self, handler: Callable, arg: object = None):
        """
        Emitted when file or batch of files is uploaded

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("uploaded", handler, arg)

    def on_uploading(self, handler: Callable, arg: object = None):
        """
        Emitted when file or batch of files started uploading

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("uploading", handler, arg)

    def ui_abort(self):
        """Abort upload of all files (same as clicking the abort button)"""
        self._js_call_method("abort")

    def ui_addFiles(self, ui_files):
        """Add files programmatically"""
        kwargs = {}
        if ui_files is not None:
            kwargs["files"] = ui_files
        self._js_call_method("addFiles", [kwargs])

    def ui_isAlive(self):
        """Is the component alive (activated but not unmounted); Useful to determine if you still need to compute anything going further"""
        self._js_call_method("isAlive")

    def ui_pickFiles(self, ui_evt):
        """Trigger file pick; Must be called as a direct consequence of user interaction (eg. in a click handler), due to browsers security policy"""
        kwargs = {}
        if ui_evt is not None:
            kwargs["evt"] = ui_evt
        self._js_call_method("pickFiles", [kwargs])

    def ui_removeFile(self, ui_file):
        """Remove specified file from the queue"""
        kwargs = {}
        if ui_file is not None:
            kwargs["file"] = ui_file
        self._js_call_method("removeFile", [kwargs])

    def ui_removeQueuedFiles(self):
        """Remove files that are waiting for upload to start (same as clicking the left clear button)"""
        self._js_call_method("removeQueuedFiles")

    def ui_removeUploadedFiles(self):
        """Removes already uploaded files from the list"""
        self._js_call_method("removeUploadedFiles")

    def ui_reset(self):
        """Resets uploader to default; Empties queue, aborts current uploads"""
        self._js_call_method("reset")

    def ui_updateFileStatus(self, ui_file, ui_status, ui_uploadedSize):
        """Update the status of a file"""
        kwargs = {}
        if ui_file is not None:
            kwargs["file"] = ui_file
        if ui_status is not None:
            kwargs["status"] = ui_status
        if ui_uploadedSize is not None:
            kwargs["uploadedSize"] = ui_uploadedSize
        self._js_call_method("updateFileStatus", [kwargs])

    def ui_upload(self):
        """Start uploading (same as clicking the upload button)"""
        self._js_call_method("upload")

    def _get_js_methods(self):
        return [
            "abort",
            "addFiles",
            "isAlive",
            "pickFiles",
            "removeFile",
            "removeQueuedFiles",
            "removeUploadedFiles",
            "reset",
            "updateFileStatus",
            "upload",
        ]


class QUploaderAddTrigger(Component):
    """
    Quasar Component: `QUploaderAddTrigger <https://v2.quasar.dev/vue-components/uploader>`__

    """

    def __init__(self, *children, **kwargs):
        super().__init__("QUploaderAddTrigger", *children, **kwargs)

    def _get_js_methods(self):
        return []


class QVideo(Component):
    """
    Quasar Component: `QVideo <https://v2.quasar.dev/vue-components/video>`__

    :param ui_src: The source url to display in an iframe
    :param ui_title: (Accessibility) Set the native 'title' attribute value of the inner iframe being used
    :param ui_fetchpriority: Provides a hint of the relative priority to use when fetching the iframe document
    :param ui_loading: Indicates how the browser should load the iframe
    :param ui_referrerpolicy: Indicates which referrer to send when fetching the frame's resource
    :param ui_ratio: Aspect ratio for the content; If value is a String, then avoid using a computational statement (like '16/9') and instead specify the String value of the result directly (eg. '1.7777')
    """

    def __init__(
        self,
        *children,
        ui_src: str | None = None,
        ui_title: str | None = None,
        ui_fetchpriority: str | None = None,
        ui_loading: str | None = None,
        ui_referrerpolicy: str | None = None,
        ui_ratio: str | float | None = None,
        **kwargs,
    ):
        super().__init__("QVideo", *children, **kwargs)
        if ui_src is not None:
            self._props["src"] = ui_src
        if ui_title is not None:
            self._props["title"] = ui_title
        if ui_fetchpriority is not None:
            self._props["fetchpriority"] = ui_fetchpriority
        if ui_loading is not None:
            self._props["loading"] = ui_loading
        if ui_referrerpolicy is not None:
            self._props["referrerpolicy"] = ui_referrerpolicy
        if ui_ratio is not None:
            self._props["ratio"] = ui_ratio

    @property
    def ui_src(self):
        """The source url to display in an iframe"""
        return self._props.get("src")

    @ui_src.setter
    def ui_src(self, value):
        self._set_prop("src", value)

    @property
    def ui_title(self):
        """(Accessibility) Set the native 'title' attribute value of the inner iframe being used"""
        return self._props.get("title")

    @ui_title.setter
    def ui_title(self, value):
        self._set_prop("title", value)

    @property
    def ui_fetchpriority(self):
        """Provides a hint of the relative priority to use when fetching the iframe document"""
        return self._props.get("fetchpriority")

    @ui_fetchpriority.setter
    def ui_fetchpriority(self, value):
        self._set_prop("fetchpriority", value)

    @property
    def ui_loading(self):
        """Indicates how the browser should load the iframe"""
        return self._props.get("loading")

    @ui_loading.setter
    def ui_loading(self, value):
        self._set_prop("loading", value)

    @property
    def ui_referrerpolicy(self):
        """Indicates which referrer to send when fetching the frame's resource"""
        return self._props.get("referrerpolicy")

    @ui_referrerpolicy.setter
    def ui_referrerpolicy(self, value):
        self._set_prop("referrerpolicy", value)

    @property
    def ui_ratio(self):
        """Aspect ratio for the content; If value is a String, then avoid using a computational statement (like '16/9') and instead specify the String value of the result directly (eg. '1.7777')"""
        return self._props.get("ratio")

    @ui_ratio.setter
    def ui_ratio(self, value):
        self._set_prop("ratio", value)

    def _get_js_methods(self):
        return []


class QVirtualScroll(Component):
    """
    Quasar Component: `QVirtualScroll <https://v2.quasar.dev/vue-components/virtual-scroll>`__

    :param ui_type: The type of content: list (default) or table
    :param ui_items: Available list items that will be passed to the scoped slot; For best performance freeze the list of items; Required if 'itemsFn' is not supplied
    :param ui_items_size: Number of available items in the list; Required and used only if 'itemsFn' is provided
    :param ui_items_fn: Function to return the scope for the items to be displayed; Should return an array for items starting from 'from' index for size length; For best performance, reference it from your scope and do not define it inline
    :param ui_scroll_target:
    :param ui_virtual_scroll_horizontal: Make virtual list work in horizontal mode
    :param ui_virtual_scroll_slice_size: Minimum number of items to render in the virtual list
    :param ui_virtual_scroll_slice_ratio_before: Ratio of number of items in visible zone to render before it
    :param ui_virtual_scroll_slice_ratio_after: Ratio of number of items in visible zone to render after it
    :param ui_virtual_scroll_item_size: Default size in pixels (height if vertical, width if horizontal) of an item; This value is used for rendering the initial list; Try to use a value close to the minimum size of an item
    :param ui_virtual_scroll_sticky_size_start: Size in pixels (height if vertical, width if horizontal) of the sticky part (if using one) at the start of the list; A correct value will improve scroll precision
    :param ui_virtual_scroll_sticky_size_end: Size in pixels (height if vertical, width if horizontal) of the sticky part (if using one) at the end of the list; A correct value will improve scroll precision
    :param ui_table_colspan: The number of columns in the table (you need this if you use table-layout: fixed)
    """

    def __init__(
        self,
        *children,
        ui_type: str | None = None,
        ui_items: list | None = None,
        ui_items_size: float | None = None,
        ui_items_fn: Callable | None = None,
        ui_scroll_target: Any | None = None,
        ui_virtual_scroll_horizontal: bool | None = None,
        ui_virtual_scroll_slice_size: float | str | None = None,
        ui_virtual_scroll_slice_ratio_before: float | str | None = None,
        ui_virtual_scroll_slice_ratio_after: float | str | None = None,
        ui_virtual_scroll_item_size: float | str | None = None,
        ui_virtual_scroll_sticky_size_start: float | str | None = None,
        ui_virtual_scroll_sticky_size_end: float | str | None = None,
        ui_table_colspan: float | str | None = None,
        **kwargs,
    ):
        super().__init__("QVirtualScroll", *children, **kwargs)
        if ui_type is not None:
            self._props["type"] = ui_type
        if ui_items is not None:
            self._props["items"] = ui_items
        if ui_items_size is not None:
            self._props["items-size"] = ui_items_size
        if ui_items_fn is not None:
            self._props["items-fn"] = ui_items_fn
        if ui_scroll_target is not None:
            self._props["scroll-target"] = ui_scroll_target
        if ui_virtual_scroll_horizontal is not None:
            self._props["virtual-scroll-horizontal"] = (
                ui_virtual_scroll_horizontal
            )
        if ui_virtual_scroll_slice_size is not None:
            self._props["virtual-scroll-slice-size"] = (
                ui_virtual_scroll_slice_size
            )
        if ui_virtual_scroll_slice_ratio_before is not None:
            self._props["virtual-scroll-slice-ratio-before"] = (
                ui_virtual_scroll_slice_ratio_before
            )
        if ui_virtual_scroll_slice_ratio_after is not None:
            self._props["virtual-scroll-slice-ratio-after"] = (
                ui_virtual_scroll_slice_ratio_after
            )
        if ui_virtual_scroll_item_size is not None:
            self._props["virtual-scroll-item-size"] = (
                ui_virtual_scroll_item_size
            )
        if ui_virtual_scroll_sticky_size_start is not None:
            self._props["virtual-scroll-sticky-size-start"] = (
                ui_virtual_scroll_sticky_size_start
            )
        if ui_virtual_scroll_sticky_size_end is not None:
            self._props["virtual-scroll-sticky-size-end"] = (
                ui_virtual_scroll_sticky_size_end
            )
        if ui_table_colspan is not None:
            self._props["table-colspan"] = ui_table_colspan

    @property
    def ui_type(self):
        """The type of content: list (default) or table"""
        return self._props.get("type")

    @ui_type.setter
    def ui_type(self, value):
        self._set_prop("type", value)

    @property
    def ui_items(self):
        """Available list items that will be passed to the scoped slot; For best performance freeze the list of items; Required if 'itemsFn' is not supplied"""
        return self._props.get("items")

    @ui_items.setter
    def ui_items(self, value):
        self._set_prop("items", value)

    @property
    def ui_items_size(self):
        """Number of available items in the list; Required and used only if 'itemsFn' is provided"""
        return self._props.get("items-size")

    @ui_items_size.setter
    def ui_items_size(self, value):
        self._set_prop("items-size", value)

    @property
    def ui_items_fn(self):
        """Function to return the scope for the items to be displayed; Should return an array for items starting from 'from' index for size length; For best performance, reference it from your scope and do not define it inline"""
        return self._props.get("items-fn")

    @ui_items_fn.setter
    def ui_items_fn(self, value):
        self._set_prop("items-fn", value)

    @property
    def ui_scroll_target(self):
        return self._props.get("scroll-target")

    @ui_scroll_target.setter
    def ui_scroll_target(self, value):
        self._set_prop("scroll-target", value)

    @property
    def ui_virtual_scroll_horizontal(self):
        """Make virtual list work in horizontal mode"""
        return self._props.get("virtual-scroll-horizontal")

    @ui_virtual_scroll_horizontal.setter
    def ui_virtual_scroll_horizontal(self, value):
        self._set_prop("virtual-scroll-horizontal", value)

    @property
    def ui_virtual_scroll_slice_size(self):
        """Minimum number of items to render in the virtual list"""
        return self._props.get("virtual-scroll-slice-size")

    @ui_virtual_scroll_slice_size.setter
    def ui_virtual_scroll_slice_size(self, value):
        self._set_prop("virtual-scroll-slice-size", value)

    @property
    def ui_virtual_scroll_slice_ratio_before(self):
        """Ratio of number of items in visible zone to render before it"""
        return self._props.get("virtual-scroll-slice-ratio-before")

    @ui_virtual_scroll_slice_ratio_before.setter
    def ui_virtual_scroll_slice_ratio_before(self, value):
        self._set_prop("virtual-scroll-slice-ratio-before", value)

    @property
    def ui_virtual_scroll_slice_ratio_after(self):
        """Ratio of number of items in visible zone to render after it"""
        return self._props.get("virtual-scroll-slice-ratio-after")

    @ui_virtual_scroll_slice_ratio_after.setter
    def ui_virtual_scroll_slice_ratio_after(self, value):
        self._set_prop("virtual-scroll-slice-ratio-after", value)

    @property
    def ui_virtual_scroll_item_size(self):
        """Default size in pixels (height if vertical, width if horizontal) of an item; This value is used for rendering the initial list; Try to use a value close to the minimum size of an item"""
        return self._props.get("virtual-scroll-item-size")

    @ui_virtual_scroll_item_size.setter
    def ui_virtual_scroll_item_size(self, value):
        self._set_prop("virtual-scroll-item-size", value)

    @property
    def ui_virtual_scroll_sticky_size_start(self):
        """Size in pixels (height if vertical, width if horizontal) of the sticky part (if using one) at the start of the list; A correct value will improve scroll precision"""
        return self._props.get("virtual-scroll-sticky-size-start")

    @ui_virtual_scroll_sticky_size_start.setter
    def ui_virtual_scroll_sticky_size_start(self, value):
        self._set_prop("virtual-scroll-sticky-size-start", value)

    @property
    def ui_virtual_scroll_sticky_size_end(self):
        """Size in pixels (height if vertical, width if horizontal) of the sticky part (if using one) at the end of the list; A correct value will improve scroll precision"""
        return self._props.get("virtual-scroll-sticky-size-end")

    @ui_virtual_scroll_sticky_size_end.setter
    def ui_virtual_scroll_sticky_size_end(self, value):
        self._set_prop("virtual-scroll-sticky-size-end", value)

    @property
    def ui_table_colspan(self):
        """The number of columns in the table (you need this if you use table-layout: fixed)"""
        return self._props.get("table-colspan")

    @ui_table_colspan.setter
    def ui_table_colspan(self, value):
        self._set_prop("table-colspan", value)

    @property
    def ui_slot_after(self):
        """Template slot for the elements that should be rendered after the list; Suggestion: tfoot after a table"""
        return self.ui_slots.get("after", [])

    @ui_slot_after.setter
    def ui_slot_after(self, value):
        self._set_slot("after", value)

    @property
    def ui_slot_before(self):
        """Template slot for the elements that should be rendered before the list; Suggestion: thead before a table"""
        return self.ui_slots.get("before", [])

    @ui_slot_before.setter
    def ui_slot_before(self, value):
        self._set_slot("before", value)

    def on_virtual_scroll(self, handler: Callable, arg: object = None):
        """
        Emitted when the virtual scroll occurs

        :param handler: Function to be called on emit event
        :param arg: Additional argument to be passed to the handler
        """
        return self.on("virtual-scroll", handler, arg)

    def ui_refresh(self, ui_index=None):
        """Refreshes the virtual scroll list; Use it after appending items"""
        kwargs = {}
        if ui_index is not None:
            kwargs["index"] = ui_index
        self._js_call_method("refresh", [kwargs])

    def ui_reset(self):
        """Resets the virtual scroll computations; Needed for custom edge-cases"""
        self._js_call_method("reset")

    def ui_scrollTo(self, ui_index, ui_edge=None):
        """Scroll the virtual scroll list to the item with the specified index (0 based)"""
        kwargs = {}
        if ui_index is not None:
            kwargs["index"] = ui_index
        if ui_edge is not None:
            kwargs["edge"] = ui_edge
        self._js_call_method("scrollTo", [kwargs])

    def _get_js_methods(self):
        return ["refresh", "reset", "scrollTo"]
