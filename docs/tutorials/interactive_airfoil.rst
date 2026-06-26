
Interactive Airfoil Tutorial
============================

A guided, in-app tutorial: a drawer walks you through building a small airfoil
tool step by step, and a code popup hands you each snippet to paste into
``app.py``. Press *Apply*, the app hot-reloads, and the new piece appears.

Running it
----------

.. code-block:: bash

   pip install ngapp[dev]
   python -m ngapp.tutorial

This scaffolds a complete project (the same layout as
:doc:`python -m ngapp.create_app <../getting_started>`: a ``pyproject.toml``, a
``src/`` package, and a GitHub Pages workflow), then launches it with the guide
attached.

The default folder is ``airfoil_tutorial``. Options:

.. code-block:: bash

   python -m ngapp.tutorial my_airfoil   # custom folder/module name
   python -m ngapp.tutorial --no-browser # don't open a browser
   python -m ngapp.tutorial --no-run     # only scaffold + install

Re-running ``python -m ngapp.tutorial`` restarts an existing folder instead of
recreating it.

The app needs `ngsolve <https://ngsolve.org>`_,
`ngsolve_webgpu <https://github.com/CERBSim/ngsolve_webgpu>`_ and
`ngsolve_gui <https://github.com/CERBSim/ngsolve_gui>`_, listed in the generated
``appconfig.py``.

The guide
---------

* The drawer lists the steps and tracks progress; drag its left edge to resize.
* The code popup shows each change as a diff. *Apply* writes it into ``app.py``;
  *Copy* lets you paste it by hand if you edited that part.
* Clicking a step rewrites ``app.py`` to that step's checkpoint.

Steps
-----

#. **Input panel** - slider, dropdown, number field and knob for the NACA
   parameters.
#. **3D viewport** - a WebGPU canvas with a potential-flow solve, re-solved when
   inputs change.
#. **Results** - lift and drag in a table, plus a lift-to-drag plot per attempt.
#. **Styling** - the ngsolve_gui theme and a dark-mode toggle backed by a
   :doc:`user setting <../user_settings>`.
#. **Picking** - read field values off the GPU as you hover.
#. **Make it yours** - drop the tutorial metaclass to be left with your own
   app, ready to ``pip install``, run as an executable, or
   :doc:`deploy <host_on_github>`.
