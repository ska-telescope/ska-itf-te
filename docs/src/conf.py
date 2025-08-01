# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
import sphinx_rtd_theme

sys.path.insert(0, os.path.abspath("../../src"))


def setup(app):
    app.add_css_file("css/custom.css")


# -- Project information -----------------------------------------------------

project = "SKA Mid ITF Tests"
copyright = "Adriaan de Beer, adebeer@sarao.ac.za"
author = "ATLAS Team"

# The full version, including alpha/beta/rc tags

release = "27.3.0"

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.coverage",
    "sphinx.ext.mathjax",
    "sphinx.ext.ifconfig",
    "sphinx.ext.viewcode",
    "sphinx.ext.githubpages",
    "recommonmark",
    "sphinx.ext.autosectionlabel",
]


# Add any paths that contain templates here, relative to this directory.
templates_path = ["ska-ser-sphinx-templates/_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["ska-ser-sphinx-templates/_static"]

html_context = {
    "favicon": "img/favicon_mono.ico",
    "logo": "img/logo.png",
    "theme_logo_only": True,
}

intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}
