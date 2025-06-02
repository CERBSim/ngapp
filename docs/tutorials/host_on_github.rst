
Deploy App to Github Pages
##########################

Prerequisites
-------------

* You created an app using ``python -m ngapp.create_app``
* The app is using only python packages, which are available on pyodide (see below :ref:`pyodide packages`)
* All python dependencies are listed in the ``frontend_pip_dependencies`` field in your ``appconfig.py`` file

Steps
-------------

#. If you haven't already, initialize a git project locally in your app directory

   .. code-block:: bash

     git init .
     git add .
     git commit -m'Initial commit'

#. `Create a new repository on github <https://github.com/new>`_, fill out only the repository name, **don't** add gitignore, license or a README file

#. On the Github Repository website, go to **Settings** (at the top bar )-> **Pages** (left side pane) and change **Build and deployment**/Source from "Deploy from a branch" to **GitHub Actions**.

#. Tell your local git repository about the github repo you just created. Instructions are shown by github after creating the repository, they should look like this

   .. code-block:: bash

     git remote add origin git@github.com/{github_user}/{github_repo}
     git push origin main

Now, your app is hosted on *https://{github_user}.github.io/{github_repo}* and automatically updated when you do ``git push`` 🎉


.. _pyodide packages:

Available Python Packages
-------------------------

Some python packages are not available when the app is hosted on github pages, since it's running using `Pyodide <https://pyodide.org>`_.

Available packages are

* All pure Python packages on pypi (the .whl file has ``none`` in it's name, no ``darwin``, ``win``  or ``linux`` ).
* Netgen/NGSolve
* Popular packages provided by pyodide (e.g. numpy), a full list is `here <https://github.com/pyodide/pyodide/tree/main/packages>`_

Note that some packages are lacking features (for instance there is no Intel MKL/Pardiso available on, also scipy is missing some solvers).
