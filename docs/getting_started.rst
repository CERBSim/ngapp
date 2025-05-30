
Getting Started
===============

After installing ngapp and required development dependencies with

.. code-block:: bash

   pip install ngapp[dev]

you can create your first app by opening a console in a desired project location and executing

.. code-block:: bash

   python -m ngapp.create_app

this script will ask you for your python module name for the project, the app name and the name of the app class. The module name and the app class name need to be valid Python identifiers.

If successful the script will prompt you with the message to start your new app with

.. code-block:: bash

   python -m <module_name> --dev

where ``<module_name>`` is the module name you provided. The ``--dev`` option starts the app in development mode, which enables hot reloading and other development features.

You should see our "Hello World!" app opening up in a new browser session (if the session does not open up automatically click on the link in the console).

Now open the module directory in your favorite editor and start coding! For example as a first start change some labels or add some print statements to the ``increment_counter`` function in the app and observe live changes and outputs in the console.

The new directory called ``<module_name>`` will have the following structure:

.. code-block:: text

   <module_name>/
   ├── src/
   │   ├── <module_name>/
   │   │   ├── __init__.py
   │   │   ├── app.py
   │   │   ├── appconfig.py
   │   │   └── __main__.py
   ├── ├── .github
   │   │   ├── workflows/
   │   │   │   └── deploy.yml
   ├── README.md
   └── pyproject.toml

The ``<module_name>/src/<module_name>/app.py`` contains the main app code. The ``deploy.yml`` a github workflow that automatically deploys your app as a web-version onto GitHub.
