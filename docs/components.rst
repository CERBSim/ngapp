
Components
==========

.. todo::

   This is outdated and needs rework.

Components are the main tools to create your web-app. With them you can define everything: inputs, outputs, visualization, etc.

.. toctree::
   :maxdepth: 1

   components/group.rst
   components/webgui.rst

Your defined components will be automatically synchronized with the javascript objects, so calling component functions usually calls some javascript code on the user side.


Events
------

You can attach callbacks to events emitted by components.

.. code-block:: python

    my_component.on('event_name', my_python_function)

============ ============================== ==========
Event          Description                   Arguments
============ ============================== ==========
'load'        Component is constructed       None
'update'      Component data changes         None
'click'       Component is clicked           Event Data
'dblclick'    Component is double-clicked    Event Data
'blur'        Component loses focus          Event Data
'focus'       Component gains focus          Event Data
'paste'       Content is pasted              Event Data
'mousedown'   Mouse button is pressed        Event Data
'mouseup'     Mouse button is released       Event Data
'mouseenter'  Mouse enters element           Event Data
'mouseleave'  Mouse leaves element           Event Data
============ ============================== ==========

The "Event Data" is a dictionary with the following keys:

* **altKey**: Indicates if the "Alt" key was pressed.
* **ctrlKey**: Indicates if the "Ctrl" key was pressed.
* **shiftKey**: Indicates if the "Shift" key was pressed.
* **metaKey**: Indicates if the "Meta" key was pressed (Command key on Mac, Windows key on Windows).
* **type**: Type of the event (e.g., 'click', 'dblclick', 'blur').


For example

.. code-block:: python

   def print_hi():
       print("hi")
   
   my_button.on('click', print_hi)

will print the message "hi" into the browser console when the button is clicked.


JS Functions
-------------

Also all components provide some frontend functions that can be called from the python side, for example to let the user download files we need to pass the file to javascript and make a download event in the browser.

These functions can be called from inside the component using

.. code-block:: python

   component.callJSFunction('function_name', kwargs)

For example

.. code-block:: python

   my_button.callJSFunction('download', { 'filename': 'mesh.vol' })

The following JS callbacks are implemented for all components:

========== =========================== =================
Name        Description                 Arguments
========== =========================== =================
'download'  Download a file             filename
========== =========================== =================



