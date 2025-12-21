Concepts & Architecture
=======================

This page explains the core ideas behind ngapp so that you have a clear
mental model before diving into components, tutorials, or the full
API reference.

What is an app?
----------------

An **app** is a Python class derived from :class:`ngapp.App` that
encapsulates:

- The **root component tree** that defines your user interface
- The **application state** (Python attributes and data structures)
- Optional **compute functions** that can run locally or on remote
  compute environments

Typically you create one app class per project, and ngapp takes care of
wiring it to the browser.

Components and the UI tree
--------------------------

User interfaces in ngapp are built from **components**:

- Quasar-based components (buttons, inputs, dialogs, tables, layouts)
- Helper components (layout helpers, file widgets, warnings, etc.)
- Visualization components (Plotly, WebGPU, VTK)

Components are arranged into a tree: each component can have children,
which together form the structure of your page. The root of this tree is
attached to the app.

State & event handling
----------------------

The ngapp runtime keeps Python state and the browser UI in sync:

- Component attributes (for example ``ui_model_value`` or ``ui_style``)
  are mirrored between Python and the frontend.
- User interactions (clicks, typing, selections) raise **events** that
  call your Python callbacks (such as ``on_click`` or ``on_input``).
- Only minimal **diffs** are sent over the bridge, making updates
  efficient.

This lets you focus on your data and logic instead of manual
JavaScript and DOM manipulation.

Development workflow
--------------------

A typical development workflow looks like this:

1. Scaffold a new project with ``python -m ngapp.create_app``.
2. Implement your app by composing components in ``app.py``.
3. Run in development mode with ``python -m <module_name> --dev``.
4. Add compute functions or visualizations as needed.
5. Package and deploy your app (for example to GitHub Pages or your
   own infrastructure).

Where to go next
----------------

- To learn how to build user interfaces, read :doc:`components`.
- For plots and 3D graphics, see :doc:`visualization`.
- To configure deployment, see
  :doc:`deployment_environments`.
- For detailed APIs, go to :doc:`api/api_doc`.
