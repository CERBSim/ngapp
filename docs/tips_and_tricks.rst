Advanced Topics
===============

Printing
--------

You can see Python print statements as output in the console and get with this info on the Python side of objects.

JavaScript Integration
----------------------

ngapp provides seamless integration with JavaScript, allowing you to execute
JavaScript code, manipulate the DOM, and access browser APIs directly from
Python. There are three main ways to interact with JavaScript (see also
the lower-level utilities documented in :doc:`api_utils`):

1. **Direct JavaScript access with `.js`**
2. **Deferred execution with `call_js()`**
3. **Quasar framework integration with `.quasar`**
4. **Event handler creation with `create_event_handler()`**

These functions call be called from any component or from the app itself. 

Direct JavaScript Access (.js)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The `.js` property provides immediate access to the JavaScript runtime environment. This allows you to execute any JavaScript function or access any JavaScript object directly.

**Basic Usage:**

.. code-block:: python

   # Access console
   self.js.console.log("Hello from Python!")

   # Access DOM
   element = self.js.document.getElementById("my-element")
   element.style.backgroundColor = "red"

   # Access window object
   self.js.window.alert("Alert from Python!")

   # Create new JavaScript objects
   canvas = self.js.document.createElement("canvas")
   ctx = canvas.getContext("2d")

**DOM Manipulation Examples:**

.. code-block:: python

   # Create and append elements
   div = self.js.document.createElement("div")
   div.textContent = "Created from Python"
   div.style.color = "blue"
   self.js.document.body.appendChild(div)

   # Query selectors
   elements = self.js.document.querySelectorAll(".my-class")
   for element in elements:
       element.style.display = "none"

   # Event listeners
   def handle_click(event):
       self.js.console.log("Button clicked!")

   button = self.js.document.getElementById("my-button")
   button.addEventListener("click", handle_click)

**Browser API Access:**

.. code-block:: python

   # File picker
   options = {"multiple": False, "accept": ".json"}
   file_picker = self.js.showOpenFilePicker(options)

   # Local storage
   self.js.localStorage.setItem("key", "value")
   value = self.js.localStorage.getItem("key")

**Important Notes:**

- Cannot be used in ``__init__`` methods (JavaScript environment not ready yet)
- Only available after the component is mounted
- Use ``call_js()`` for initialization-time JavaScript execution

Deferred JavaScript Execution (call_js)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``call_js()`` method ensures safe JavaScript execution by automatically deferring function calls until the JavaScript environment is ready. This is essential for code that needs to run during component initialization.

**Basic Usage:**

.. code-block:: python

   def my_js_function(js):
       js.console.log("This runs when JS is ready")

   # Safe to call in __init__ or anytime
   self.call_js(my_js_function)

**With Parameters:**

.. code-block:: python

   def setup_element(js, element_id, color):
       element = js.document.getElementById(element_id)
       if element:
           element.style.backgroundColor = color

   # Pass additional arguments
   self.call_js(setup_element, "my-div", "lightblue")

**Complex Initialization Example:**

.. code-block:: python

   class MyComponent(Component):
       def __init__(self):
           super().__init__()

           # This won't work in __init__ - JS not ready yet
           # self.js.console.log("This would fail!")

           # This works - deferred until JS is ready
           def initialize_js(js):
               js.console.log("Component initialized")

               # Set up event listeners
               element = js.document.querySelector(f"#{self._fullid}")
               element.addEventListener("click", self.handle_click)

               # Initialize third-party libraries
               if hasattr(js.window, "myLibrary"):
                   js.window.myLibrary.init({
                       "target": element,
                       "options": {"theme": "dark"}
                   })

           self.call_js(initialize_js)

**Return Values:**

Note that ``call_js()`` doesn't return values directly since execution is deferred. For getting return values, use the direct ``.js`` property after the component is mounted.

Quasar Framework Integration (.quasar)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``.quasar`` property provides access to the Quasar framework's ``$q`` object, giving you access to all Quasar utilities, plugins, and services.

**Notifications:**

.. code-block:: python

   # Basic notification
   self.quasar.notify("Operation completed!")

   # Advanced notification with options
   self.quasar.notify({
       'message': 'File uploaded successfully!',
       'color': 'positive',
       'icon': 'cloud_upload',
       'position': 'top',
       'timeout': 3000,
       'actions': [
           {
               'label': 'Dismiss',
               'color': 'white',
               'handler': lambda: None
           }
       ]
   })

   # Different notification types
   self.quasar.notify({
       'type': 'negative',
       'message': 'Error occurred!',
       'caption': 'Please try again'
   })

**Dialogs:**

.. code-block:: python

   # Simple dialog
   self.quasar.dialog({
       'title': 'Confirm Action',
       'message': 'Are you sure you want to delete this item?'
   }).onOk(lambda: self.delete_item())

   # Prompt dialog
   def handle_input(value):
       print(f"User entered: {value}")

   self.quasar.dialog({
       'title': 'Enter Name',
       'prompt': {
           'model': '',
           'type': 'text',
           'label': 'Your name'
       }
   }).onOk(handle_input)

   # Custom dialog with HTML
   self.quasar.dialog({
       'title': 'Custom Content',
       'html': True,
       'message': '<p>This is <strong>HTML</strong> content</p>'
   })

**Platform Detection:**

.. code-block:: python

   # Check platform
   if self.quasar.platform["is"].mobile:
       print("Running on mobile")

   if self.quasar.platform["is"].desktop:
       print("Running on desktop")

**Dark Mode:**

.. code-block:: python

   # Toggle dark mode
   self.quasar.dark.toggle()

   # Set dark mode
   self.quasar.dark.set(True)  # Enable dark mode
   self.quasar.dark.set(False)  # Disable dark mode

   # Check current mode
   if self.quasar.dark.isActive:
       print("Dark mode is active")

**Screen Information:**

.. code-block:: python

   # Get screen info
   screen = self.quasar.screen
   print(f"Width: {screen.width}px")
   print(f"Height: {screen.height}px")

   # Responsive breakpoints
   if screen.lt.md:  # Less than medium
       print("Small screen")
   elif screen.gt.lg:  # Greater than large
       print("Large screen")

**Important Notes:**

- Cannot be used in ``__init__`` methods
- Only available after component mounting
- Provides access to all Quasar ``$q`` object functionality
- See `Quasar documentation <https://quasar.dev/options/the-q-object>`__ for complete API reference

Common Patterns and Best Practices
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Using JavaScript ``new`` from Python
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When working with browser APIs, you often need to call JavaScript
constructors using the ``new`` operator (for example, ``new
Uint8ClampedArray(...)`` or ``new ImageData(...)``). The JavaScript
proxy objects exposed by ngapp support this via a special ``_new``
method on constructor functions and classes.

Instead of writing JavaScript like:

.. code-block:: javascript

     const u8 = new Uint8ClampedArray(buffer);
     const imageData = new ImageData(u8, width, height);

you can do the equivalent from Python using ``.js``:

.. code-block:: python

     # self is a Component (or App) with access to self.js

     width, height = 640, 480
     buffer = some_numpy_array.tobytes()

     # Call JS constructors via _new
     u8 = self.js.Uint8ClampedArray._new(buffer)
     image_data = self.js.ImageData._new(u8, width, height)

     # Use the constructed objects as usual
     canvas = self.js.document.createElement("canvas")
     canvas.width = width
     canvas.height = height
     ctx = canvas.getContext("2d")
     ctx.putImageData(image_data, 0, 0)

**Guidelines for using ``_new``:**

- Use ``Class._new(...)`` whenever you would normally write
  ``new Class(...)`` in JavaScript.
- Arguments and return values are proxied automatically; you can pass
  basic Python types (``int``, ``float``, ``str``), lists, dicts, or
  byte buffers (e.g. ``numpy_array.tobytes()``).
- Combine ``_new`` with ``call_js()`` if you need to construct objects
  during component initialization, before ``self.js`` is directly
  available.

Initialization Pattern
^^^^^^^^^^^^^^^^^^^^^^

This pattern uses ``call_js()`` during ``__init__`` to perform any
JavaScript setup once the environment is ready, while keeping direct
``.js`` access for code that runs after mounting.

.. code-block:: python

   class MyComponent(Component):
       def __init__(self):
           super().__init__()
           # Use call_js for initialization
           self.call_js(self._setup_javascript)

       def _setup_javascript(self, js):
           # JavaScript setup code here
           js.console.log("Component ready")

       def on_mounted(self):
           # Use .js for immediate access after mounting
           self.js.console.log("Component mounted")

Error Handling
^^^^^^^^^^^^^^

Wrap risky JavaScript operations and surface failures to the user
through Quasar notifications or other UI feedback.

.. code-block:: python

   def safe_js_operation(self):
       try:
           result = self.js.someRiskyOperation()
           return result
       except Exception as e:
           self.quasar.notify({
               'type': 'negative',
               'message': f'JavaScript error: {str(e)}'
           })
           return None

Async Operations
^^^^^^^^^^^^^^^^

Use JavaScript promises for async operations and bridge success/error
callbacks back into Python.

.. code-block:: python

   def handle_async_operation(self):
       def on_success(result):
           self.quasar.notify("Operation successful!")

       def on_error(error):
           self.quasar.notify({
               'type': 'negative',
               'message': 'Operation failed'
           })

       # Use JavaScript promises
       promise = self.js.fetch("/api/data")
       promise.then(on_success).catch(on_error)


Event Handler Creation (create_event_handler)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``create_event_handler()`` method creates properly wrapped event handlers that can be safely attached to JavaScript events. This is essential for handling DOM events and controlling event behavior.

**Basic Usage:**

.. code-block:: python

   def my_click_handler(event):
       print(f"Clicked element: {event}")

   # Create the event handler
   handler = self.create_event_handler(my_click_handler)

   # Attach to DOM element
   button = self.js.document.getElementById("my-button")
   button.addEventListener("click", handler)

**Event Control Parameters:**

.. code-block:: python

   def handle_form_submit(event):
       print("Form submitted")
       # Custom validation logic here

   handler = self.create_event_handler(
       handle_form_submit,
       prevent_default=True,        # Prevents default action of the event
       stop_propagation=True,       # Stops the propagation of the event
       stop_immediate_propagation=False,  # Stop immediate propagation of the event
       return_value=None           # Value returned by event handler
   )

   form = self.js.document.querySelector("form")
   form.addEventListener("submit", handler)

**Common Event Handling Patterns:**

.. code-block:: python

   class InteractiveComponent(Component):
       def __init__(self):
           super().__init__()
           self.call_js(self._setup_event_handlers)

       def _setup_event_handlers(self, js):
           js = self.js
           # Mouse events
           mouse_handler = self.create_event_handler(self.on_mouse_move)
           js.document.addEventListener("mousemove", mouse_handler)

           # Keyboard events
           key_handler = self.create_event_handler(
               self.on_key_press,
               prevent_default=False  # Allow normal key behavior
           )
           js.document.addEventListener("keydown", key_handler)

           # Window events
           resize_handler = self.create_event_handler(self.on_window_resize)
           js.window.addEventListener("resize", resize_handler)

       def on_mouse_move(self, event):
           # Access event properties
           x, y = event.x, event.y
           print(f"Mouse at: {x}, {y}")

       def on_key_press(self, event):
           # Handle keyboard input
           if event.key == "Escape":
               self.close_dialog()
           elif event.ctrlKey and event.key == "s":
               self.save_data()

       def on_window_resize(self, event):
           # Responsive behavior
           width = self.js.window.innerWidth
           if width < 768:
               self.switch_to_mobile_layout()

These JavaScript integration features make ngapp extremely powerful for creating rich, interactive web applications while maintaining the convenience of Python development.