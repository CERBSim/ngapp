
ngapp
=====

Welcome to the ngapp documentation.

ngapp is a Python framework for building interactive scientific and engineering
applications as web or desktop apps — without writing JavaScript or HTML.
You declare user interfaces in Python, ngapp wires them to a Quasar/Vue
frontend, and keeps browser state and Python logic in sync.

What you can do with ngapp
--------------------------

ngapp is a good fit when you want to:

* Turn scripts or Jupyter notebooks into user-friendly apps
* Build rich forms, dashboards, and 3D visualizations in pure Python
* Ship your app as a desktop-like tool or deploy it as a web app
* Especially for scientific and engineering use cases
* Built for use with the Finite Element Framework NGSolve, but usable
  independently

Typical workflow
----------------

1. **Install** ngapp and development extras::

      pip install ngapp[dev]

2. **Create** a new app skeleton with a guided wizard::

      python -m ngapp.create_app

3. **Run** your app in development mode with hot reload::

      python -m <module_name> --dev

4. **Iterate** on the generated ``app.py`` using ngapp components, helper
   widgets, and visualization tools.

5. **Deploy** your app, for example using the included GitHub Pages workflow
   or your own infrastructure.

Where to start
--------------

If you are new to ngapp, begin with:

* :doc:`getting_started` – installation, project layout, first run
* :doc:`tutorials` – step-by-step examples (parametric sine, NACA generator,
  beam solver, GitHub deployment)

Then explore:

* :doc:`concepts_architecture` – core ideas: apps, components, state, compute
* :doc:`components` – building interfaces from ngapp and Quasar components
* :doc:`visualization` – interactive Plotly, WebGPU, and VTK-based views
* :doc:`deployment_environments` – deployment options and compute environments
* :doc:`tips_and_tricks` – advanced topics and JavaScript/Quasar integration
* :doc:`api/api_doc` – full Python API reference and component listings
* :doc:`testing` – snapshot and end-to-end testing utilities for apps

Contents
--------

.. toctree::
      :maxdepth: 2

      user_guide
      tutorials
      api/api_doc

