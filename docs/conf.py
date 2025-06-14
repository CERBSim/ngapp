#!/usr/bin/env python3
# -*- coding: utf-8 -*-

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.mathjax",
    "sphinx.ext.todo",
    "sphinx_design",
]

master_doc = "index"
source_suffix = [".rst", ".md"]
language = "en"

html_theme = "pydata_sphinx_theme"

html_static_path = ["_static"]

html_logo = "_static/logo.svg"

html_theme_options = {
    "logo": {
        "text": "NGApp Docs",
        "image_dark": "_static/logo_dark.png",
        "image_light": "_static/logo.svg",
    }
}

todo_include_todos = True

# Automatically extract typehints when specified and place them in
# descriptions of the relevant function/method.
autodoc_typehints = "both"
autodoc_inherit_docstrings = False

# Introduce line breaks if the line length is greater than 80 characters.
python_maximum_signature_line_length = 80


def setup(app):
    app.add_css_file("custom.css")
