User-wide app settings
=======================

ngapp provides a small helper to persist **user-wide, per-app settings**
(such as UI preferences or default values) on the local machine.

Settings are stored as JSON files in the operating system's standard
configuration directory, using the `platformdirs`_ library.

.. _platformdirs: https://platformdirs.readthedocs.io/

Overview
--------

Each :class:`ngapp.App` instance exposes a :attr:`usersettings` attribute
backed by :class:`ngapp.utils.UserSettings`.

* Settings are stored **per user** and **per app**.
* Storage location is computed via :func:`platformdirs.user_config_dir`,
  using ``"ngapp"`` as the application name.
* Each app gets its own **subfolder** inside the ``ngapp`` config
  directory, named after a stable app identifier (by default the app's
  ``metadata['name']`` or, as a fallback, ``"<module>.<ClassName>"``).
* The main settings for that app are stored in a ``config.json`` file
  inside this subfolder.

Typical use case
----------------

A common pattern is to remember form defaults, e.g. number of threads,
checkbox states, or last-used options.

Example: QInput bound to a setting
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class MyApp(App):
       def __init__(self):
           super().__init__()

           nthreads = QInput(
               ui_label="Number of Threads",
               ui_model_value=self.usersettings.get("nthreads", default=None),
           )

           # Persist the value whenever the input changes
           nthreads.on_update_model_value(
               self.usersettings.update("nthreads")
           )

Example: QCheckbox bound to a setting
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class MyApp(App):
       def __init__(self):
           super().__init__()

           darkmode = QCheckbox(
               ui_label="Dark mode",
               ui_model_value=self.usersettings.get("darkmode", default=False),
           )

           darkmode.on_update_model_value(
               self.usersettings.update("darkmode")
           )

How it works
------------

The :class:`ngapp.utils.UserSettings` helper is responsible for loading
and saving settings:

.. code-block:: python

   from ngapp.utils import UserSettings

   settings = UserSettings(app_id="my.unique.app.id")

   # Read a setting with a default
   nthreads = settings.get("nthreads", default=8)

   # Update and persist a value
   settings.set("nthreads", 16)

   # Create an event handler for components
   handler = settings.update("nthreads")

   # Later, attach it to a component event
   nthreads_input.on_update_model_value(handler)

You normally do not need to create :class:`UserSettings` directly; the
:attr:`ngapp.App.usersettings` property gives you an instance that uses
an appropriate app identifier.

Storage layout and location
---------------------------

The exact path is platform-dependent and determined by
:func:`platformdirs.user_config_dir`.

* **Linux**: typically ``$XDG_CONFIG_HOME/ngapp`` or ``~/.config/ngapp``
* **macOS**: typically ``~/Library/Application Support/ngapp``
* **Windows**: typically ``%APPDATA%\ngapp``

Within that directory ngapp creates one subfolder per app, named after
its identifier with path separators and other problematic characters
replaced by underscores. The main config file is::

  ~/.config/ngapp/my_app/config.json
  ~/.config/ngapp/mymodule.MyApp/config.json

The :class:`ngapp.utils.UserSettings` instance returned by
``App.usersettings`` operates on this ``config.json`` file.

Additional JSON settings files
------------------------------

Sometimes an app needs more than one JSON file, for example to separate
recent-project lists from UI preferences. The :class:`UserSettings`
instance can create wrappers for extra files in the same folder:

.. code-block:: python

  extra = self.usersettings.json_file("recent_projects")

  # Read with a default
  recent = extra.get("items", default=[])

  # Update and persist
  extra.set("items", ["proj1", "proj2"])

  # Or use as an event handler target
  project_input.on_update_model_value(
     extra.update("last_opened")
  )

Notes and recommendations
-------------------------

* Keep keys simple (``"nthreads"``, ``"darkmode"``, ``"last_project"``, …).
* Use small, JSON-serializable values (numbers, strings, booleans,
  small dicts/lists).
* Treat user settings as **preferences**, not as primary application
  data or results.
* If you change meaning or expected type of a key, consider using a
  new key name to avoid confusion with existing user data.
