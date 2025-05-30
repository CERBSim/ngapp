
NGApp
========

Welcome to NGApp — a Python framework for building interactive scientific and engineering applications as web or desktop apps.

NGApp makes it easy to turn your existing Python scripts or Jupyter notebooks into user-friendly, production-ready applications — without needing to write a single line of JavaScript or HTML. Whether you're developing a prototype or deploying tools for end users, NGApp provides a clean and Pythonic interface for building rich UIs and synchronizing frontend and backend logic.

This documentation will guide you through:

* Getting started with installation and first steps
* Understanding NGApp’s architecture and core components
* Tips and best practices for development
* Troubleshooting common issues
* Full API reference for advanced usage

Installation
------------

To get started with NGApp, install it using pip:

.. code-block:: bash

   pip install ngapp[dev]

The [dev] extras include tools needed for developing NGApp-based apps. When distributing your own app, you can simply depend on ngapp — users do not need the [dev] extras.

.. toctree::
   :titlesonly:
   :maxdepth: 1
   :hidden:

   getting_started.rst
   tutorials.rst
   components.rst
   tips_and_tricks.rst
   api_doc.rst

