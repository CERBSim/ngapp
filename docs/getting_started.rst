
Getting Started
===============

This guide walks you through installing ngapp, creating your first
application, and understanding the generated project layout.

Installation
------------

Install ngapp and the development extras with:

.. code-block:: bash

   pip install ngapp[dev]

The ``[dev]`` extras include tools useful while developing ngapp-based apps.
When distributing your own app to end users, you usually only need a
dependency on ``ngapp`` itself.

Creating your first app
-----------------------

Create your first app by opening a console in the desired project location
and executing:

.. code-block:: bash

   python -m ngapp.create_app

The wizard will ask you for:

* the Python **module name** for the project,
* the **app name**, and
* the name of the **app class**.

The module name and the app class name must be valid Python identifiers. If
you want to create an app with additional backend resources, pass the
``--with_backend`` flag to the command above.

If the script finishes successfully, it will show a message telling you how
to start your new app:

.. code-block:: bash

   python -m <module_name> --dev

where ``<module_name>`` is the module name you provided. The ``--dev`` option
starts the app in development mode, which enables hot reloading and other
development features.

You should see a "Hello World!" app opening in a new browser session. If the
browser does not open automatically, click on the link printed in the
console.

First edits
-----------

Now open the new module directory in your favourite editor and start coding.
As a first step, change some labels or add print statements to the
``increment_counter`` function in the generated app and observe live updates
in the browser and console.

Generated project layout
------------------------

The new directory called ``<module_name>`` will have the following structure:

.. code-block:: text

   <module_name>/
   ├── src/
   │   └── <module_name>/
   │       ├── __init__.py
   │       ├── app.py
   │       ├── appconfig.py
   │       └── __main__.py
   ├── .github/
   │   └── workflows/
   │       └── deploy.yml
   ├── README.md
   └── pyproject.toml

The file ``<module_name>/src/<module_name>/app.py`` contains the main app
code. The workflow file ``.github/workflows/deploy.yml`` defines a GitHub
Actions pipeline that can automatically deploy your app as a web version to
GitHub Pages.

Next steps
----------

Once your first app is running, you can:

* Follow the :doc:`tutorials` for step-by-step examples.
* Explore :doc:`components` to learn how to build richer interfaces.
* Read :doc:`visualization` for interactive plots and 3D views.
* Check :doc:`tips_and_tricks` for JavaScript/Quasar integration patterns.
