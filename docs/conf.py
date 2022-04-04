# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# Read the docs setup
import sphinx_rtd_theme

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys


# some comments about path setup
# getting make html, etc to work locally is as simple as inserting the python project path into the system path
# variable using the following two lines of code:
# >>>python_project_path = os.path.abspath('../pypet2bids')
# >>>sys.path.insert(0, python_project_path)
# However, when readthedocs.io attempts to build the site within their system we get a bunch of import errors
# and no html gets built from our docstrings in our python code.
# some 'possibly' helpful links on changing/adjusting the path to make RTD.io work are:
# https://github.com/readthedocs/readthedocs.org/issues/7883
# https://github.com/python/python-docs-es/blob/c79c770adf608d2cf9ac707792c6c54b9fb01f89/conf.py#L112-L113


# get absolute path to python project files
python_project_path = os.path.abspath('../pypet2bids')
sys.path.insert(0, python_project_path)

# -- Project information -----------------------------------------------------

project = 'PET2BIDS'
copyright = '2022, OpenNeuroPET'
author = 'OpenNeuroPET'

# The full version, including alpha/beta/rc tags
release = '0.0.1'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx_rtd_theme',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', 'tests']


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#

html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
