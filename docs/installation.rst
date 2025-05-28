
Installation
=============

Download the webapp_client from the App Dev page and install it
.. code-block::
 
   pip install webapp_client*.whl

Download the demo_app.zip file and extract it.

Open a command line in the new folder :code:`demo_app`.

Run :code:`pip install -e .` to install the demo app.

Click on the 'Copy serve command' button.

Open a command line and paste the command (it's in your clipboard), before
executing it, you must add the Path to the Python app class, for the demoapp
this is :code:`demo_app.DemoApp`.

The command should look like this:

.. code-block::

   python -m webapp_client.cli.serve_app https://the.backend.url "your_dev_token" demo_app.DemoApp


Once you run the command, the app will be uploaded and is visible in your
dashboard. Every time you change the source code locally, the app is
automatically updated on the server and in the browser. You don't need to
reload the website. Steps 1-4 are only needed once (or when you need to update
the webapp_client code).

Further development of app
---------------------------

The next time you you work on the app, you can create the needed command by
clicking on the dev icon in the Apps page.
