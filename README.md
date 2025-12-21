
# ngapp

ngapp is a Python framework for building interactive scientific and engineering
applications as web or desktop apps – without writing JavaScript or HTML.
You declare user interfaces in Python, ngapp connects them to a Quasar/Vue
frontend, and keeps browser state and Python logic in sync.

---

## What you can use it for

ngapp is a good fit when you want to:

* turn scripts or Jupyter notebooks into user-friendly apps,
* build forms, dashboards, and visualizations in pure Python,
* run heavy numerical workflows locally or on remote compute nodes,
* ship your app as a desktop-like tool or as a web app.

---

## Installation

Install ngapp and the development extras with:

```bash
pip install ngapp[dev]
```

The [dev] extras include tools useful while developing ngapp-based apps.
When distributing your own app to end users, you usually only need a
dependency on ngapp itself.

---

## Create your first app

1. Open a console in the directory where you want to create the project and run:

   ```bash
   python -m ngapp.create_app
   ```

   The wizard will ask for:

   * the Python module name for the project,
   * the app name, and
   * the name of the app class.

   The module name and the app class name must be valid Python identifiers.
   If you want to create an app with additional backend resources, pass the
   `--with_backend` flag to the command above.

2. Start the new app in development mode:

   ```bash
   python -m <module_name> --dev
   ```

   where `<module_name>` is the module name you provided. The `--dev` option
   starts the app in development mode, which enables hot reloading and other
   development features.

3. You should see a "Hello World" app in your browser. If the browser does
   not open automatically, click on the link printed in the console.

---

## First edits

Open the new module directory in your editor and start coding. As a first step,
change some labels or add print statements to the `increment_counter`
function in the generated app and observe live updates in the browser and
console.

---

## Generated project layout

The new directory called `<module_name>` will have the following structure:

```text
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
```

The file `<module_name>/src/<module_name>/app.py` contains the main app code.
The workflow file `.github/workflows/deploy.yml` defines a GitHub Actions
pipeline that can automatically deploy your app as a web version to
GitHub Pages.

---

## Documentation and next steps

Full documentation is available at:

https://cerbsim.github.io/ngapp

If you are new to ngapp, start with:

* Getting Started – installation, project layout, first run
* Tutorials – step-by-step examples (parametric sine, NACA generator,
  beam solver, GitHub deployment)

Then explore:

* Concepts and architecture – core ideas: apps, components, state, compute
* Components – building interfaces from ngapp and Quasar components
* Visualization – interactive plots and 3D views
* Deployment environments – deployment options and compute environments
* Tips and tricks – advanced topics and JavaScript/Quasar integration

---

## License

LGPL-2.1
