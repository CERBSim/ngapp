
Components
==========

ngapp lets you build interactive web apps entirely in Python, using a rich set of UI components—no JavaScript or HTML required. Components are the building blocks of your app’s interface, from buttons and sliders to tables, dialogs, and custom visualizations.

ngapp synchronizes state and events between Python and the browser, so you can focus on your logic and data.

Quick Example
=============

Here’s a minimal example of using ngapp components:

.. code-block:: python

   from ngapp.components import QBtn, QInput, QCard, QCardSection, QCardActions

   def on_click(event):
      print("Button clicked! Value:", input_box.value)

   input_box = QInput(ui_label="Enter something")
   button = QBtn(ui_label="Submit").on_click(on_click)
   card = QCard(
      QCardSection(input_box),
      QCardActions(button)
   )

Component Overview
===================

ngapp provides:

- **Quasar-based UI components** (QBtn, QInput, QTable, etc.) for forms, layouts, and controls
- **Helper components** (Row, Col, Div, FileName, etc.) for layout, utilities, and common patterns
- **Visualization components** for plots and custom graphics
- **Material and scientific widgets** for domain-specific input
- **BaseComponent** for building your own custom components

You can mix and match these to create complex, interactive apps. See the
API reference (:doc:`api_qcomponents` and :doc:`api_components`) and
the :doc:`tutorials` for more details and advanced usage.


Basic Quasar Components
========================

ngapp wraps the popular Quasar UI library, giving you access to a wide range of ready-to-use components. Most component properties use a `ui_` prefix (e.g., `ui_label`, `ui_color`). This makes it clear which arguments are passed to the frontend and avoids conflicts with Python keywords or internal names. For example, to set the label of a button, use `ui_label="Click me"`.

Here are some of the most useful components to get started:


:class:`~ngapp.components.qcomponents.QBtn` — Button
-----------------------------------------------------

Create clickable buttons for actions and forms. See :class:`~ngapp.components.qcomponents.QBtn` for all options.

.. code-block:: python

   from ngapp.components import QBtn
   btn = QBtn(ui_label="Click me").on_click(lambda e: print("Clicked!"))


:class:`~ngapp.components.qcomponents.QInput` — Text Input
-----------------------------------------------------------

Collect user input with a text box. See :class:`~ngapp.components.qcomponents.QInput` for all options.

.. code-block:: python

   from ngapp.components import QInput
   input_box = QInput(ui_label="Your name")


:class:`~ngapp.components.qcomponents.QCheckbox` — Checkbox
------------------------------------------------------------

Let users toggle options on or off. See :class:`~ngapp.components.qcomponents.QCheckbox` for all options.

.. code-block:: python

   from ngapp.components import QCheckbox
   checkbox = QCheckbox(ui_label="I agree")


:class:`~ngapp.components.qcomponents.QCard` — Card Layout
------------------------------------------------------------

Group related content in a card with sections and actions. See :class:`~ngapp.components.qcomponents.QCard` for all options.

.. code-block:: python

   from ngapp.components import QCard, QCardSection, QCardActions, QBtn
   card = QCard(
       QCardSection("Welcome!"),
       QCardActions(QBtn(ui_label="OK"))
   )

:class:`~ngapp.components.qcomponents.QAvatar`, :class:`~ngapp.components.qcomponents.QBadge`, :class:`~ngapp.components.qcomponents.QChip`, :class:`~ngapp.components.qcomponents.QBanner`, :class:`~ngapp.components.qcomponents.QSlider`, :class:`~ngapp.components.qcomponents.QToggle`, :class:`~ngapp.components.qcomponents.QDialog`, :class:`~ngapp.components.qcomponents.QIcon`, :class:`~ngapp.components.qcomponents.QImg`, :class:`~ngapp.components.qcomponents.QToolbar`, :class:`~ngapp.components.qcomponents.QTooltip` and many more are also available. See the API docs for each for details.


Helper Components
==================

ngapp includes a set of helper components that simplify common layout patterns, provide useful utilities, and offer convenient wrappers for frequent use cases. These components help you build interfaces faster without needing to create custom components from scratch.


:class:`~ngapp.components.helper_components.Row` — Horizontal Layout
--------------------------------------------------------------------

Arrange components side by side in a horizontal row layout. See :class:`~ngapp.components.helper_components.Row` for all options.

.. code-block:: python

   from ngapp.components import Row, QBtn
   row = Row(
       QBtn(ui_label="Left"),
       QBtn(ui_label="Center"), 
       QBtn(ui_label="Right"),
       weights=[4, 4, 4]  # Equal width columns
   )


:class:`~ngapp.components.helper_components.Col` — Vertical Layout
------------------------------------------------------------------

Stack components vertically in a column layout. See :class:`~ngapp.components.helper_components.Col` for all options.

.. code-block:: python

   from ngapp.components import Col, QInput
   col = Col(
       QInput(ui_label="First"),
       QInput(ui_label="Second"),
       QInput(ui_label="Third"),
       weights=[2, 6, 4]  # Different heights
   )


:class:`~ngapp.components.helper_components.Div` — Generic Container
--------------------------------------------------------------------

Create a generic div container for grouping content. See :class:`~ngapp.components.helper_components.Div` for all options.

.. code-block:: python

   from ngapp.components import Div, QBtn
   container = Div(
       "Some text",
       QBtn(ui_label="Button"),
       ui_class="q-pa-md"
   )


:class:`~ngapp.components.helper_components.FileName` — File Name Input
------------------------------------------------------------------------

A specialized input for setting file names with automatic app integration. See :class:`~ngapp.components.helper_components.FileName` for all options.

.. code-block:: python

   from ngapp.components import FileName
   filename_input = FileName(app=my_app, ui_label="Simulation Name")


:class:`~ngapp.components.helper_components.Heading` — Text Heading
--------------------------------------------------------------------

Create headings with different levels (h1, h2, etc.). See :class:`~ngapp.components.helper_components.Heading` for all options.

.. code-block:: python

   from ngapp.components import Heading
   heading = Heading("Section Title", level=2)


:class:`~ngapp.components.helper_components.FileUpload` — File Upload Widget
------------------------------------------------------------------------------

Upload files with drag-and-drop support and error handling. See :class:`~ngapp.components.helper_components.FileUpload` for all options.

.. code-block:: python

   from ngapp.components import FileUpload
   upload = FileUpload(
       ui_error_title="Upload Error",
       ui_error_message="Please select a valid file"
   )
   # Access uploaded file
   with upload.as_temporary_file as temp_file:
       # Process the uploaded file
       pass


:class:`~ngapp.components.helper_components.SaveSimulationButton` — Save Simulation Button
-------------------------------------------------------------------------------------------

A button that saves the current simulation state. See :class:`~ngapp.components.helper_components.SaveSimulationButton` for all options.

.. code-block:: python

   from ngapp.components import SaveSimulationButton
   save_btn = SaveSimulationButton(
       app=my_app,
       ui_tooltip="Save Simulation",
       ui_icon="mdi-content-save"
   )


Additional helper components like :class:`~ngapp.components.helper_components.Br`, :class:`~ngapp.components.helper_components.FileDownload`, :class:`~ngapp.components.helper_components.Table`, :class:`~ngapp.components.helper_components.UserWarning`, :class:`~ngapp.components.helper_components.JsonEditor` and more are also available for specialized use cases. See the API docs for each for details.


Component Arguments and Customization
========================================

Each Quasar component in ngapp accepts a variety of keyword arguments to control its appearance and behavior. Most of these arguments are prefixed with `ui_` (such as `ui_label`, `ui_color`, `ui_icon`, `ui_value`, etc.).

**Types of arguments include:**

- **Visual properties:** `ui_color`, `ui_size`, `ui_icon`, `ui_flat`, `ui_outline`, etc.
- **Content and labels:** `ui_label`, `ui_placeholder`, `ui_caption`, etc.
- **Behavior and state:** `ui_model_value`, `ui_checked`, `ui_disable`, `ui_loading`, etc.
- **Event handlers:** Python callbacks like `on_click`, `on_input`, etc.

**How to find available options:**

- See the :doc:`api_qcomponents` for a full list of all Quasar components and their arguments, including docstrings and parameter descriptions.
- You can also refer to the official Quasar documentation (https://quasar.dev/vue-components) for a detailed explanation of each component’s properties and events. Most Quasar property names map directly to NGApp’s `ui_` arguments.

**Example:**

.. code-block:: python

   QBtn(
       ui_label="Save",
       ui_color="primary",
       ui_icon="save",
       ui_flat=True).on_click(handle_save)

You can nest components to build complex layouts and combine multiple arguments for rich, interactive UIs.


Building Custom Components
=============================

ngapp makes it easy to create your own custom UI components by subclassing existing ones or the base :class:`~ngapp.components.basecomponent.Component`. You can add new properties, override methods, or combine multiple components to build reusable widgets tailored to your needs.


**Example: Custom Labeled Number Input**

.. code-block:: python

   from ngapp.components import QInput, Div

   class LabeledNumberInput(Div):
       def __init__(self, label, **kwargs):
           super().__init__(label, QInput(ui_type="number", **kwargs))

You can also override event handlers or add new methods to encapsulate logic:

.. code-block:: python

   from ngapp.components import QBtn

   class ConfirmButton(QBtn):
       def __init__(self, ui_label="Confirm", **kwargs):
           super().__init__(ui_label=ui_label, ui_color="positive", **kwargs)
           self.on_click(self.confirm_action)

       def confirm_action(self, event):
           print("Confirmed!")


Custom components can be used just like built-in ones, and can be composed, styled, and extended as needed. For more advanced use, see the :class:`~ngapp.components.basecomponent.Component` API and the Quasar component wrappers in `ngapp.components.qcomponents`.


Styling Components: `ui_style` and `ui_class`
===============================================

You can control the appearance of any component using the `ui_style` and `ui_class` keyword arguments:

- **`ui_style`** lets you set inline CSS styles directly on the component. For example, `ui_style="color: red; font-size: 20px;"` will make the text red and larger. This is a string of CSS rules applied only to that element.
- **`ui_class`** lets you assign one or more CSS classes to the component. For example, `ui_class="q-mt-md text-bold"` will apply Quasar’s margin-top and bold text classes. This is useful for using Quasar’s utility classes or your own custom styles.

If you’re new to CSS and HTML:

- `ui_style` is like giving direct instructions for how something should look (color, size, spacing, etc.).
- `ui_class` is like giving the component a label that groups it with other elements that should look the same, using predefined style rules.

**Example:**

.. code-block:: python

   QBtn(ui_label="Styled Button", ui_style="background: orange; color: white;", ui_class="q-mb-lg")

For more about CSS and styling:

- [MDN: CSS Basics](https://developer.mozilla.org/en-US/docs/Learn/Getting_started_with_the_web/CSS_basics)
- [Quasar CSS Utility Classes](https://quasar.dev/docs) Part "Style & Identity"
- [MDN: class attribute](https://developer.mozilla.org/en-US/docs/Web/HTML/Global_attributes/class)
- [MDN: style attribute](https://developer.mozilla.org/en-US/docs/Web/HTML/Global_attributes/style)

Next Steps
===========

- Explore the :doc:`api_qcomponents` for a full list of UI widgets
- See :doc:`tutorials` for step-by-step guides
- Check :doc:`api_components` for advanced and custom components
