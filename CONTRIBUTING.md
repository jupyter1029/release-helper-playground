# Contributing to Release Helper

## General Jupyter contributor guidelines

If you're reading this section, you're probably interested in contributing to
Jupyter. Welcome and thanks for your interest in contributing!

Please take a look at the Contributor documentation, familiarize yourself with
using the Jupyter Server, and introduce yourself on the mailing list and
share what area of the project you are interested in working on.

For general documentation about contributing to Jupyter projects, see the
[Project Jupyter Contributor Documentation](https://jupyter.readthedocs.io/en/latest/contributing/content-contributor.html)

## Setting Up a Development Environment

Use the following steps:

```bash
python -m pip install --upgrade setuptools pip
git clone https://github.com/jupyter-server/release-helper
cd release-helper
pip install -e .
```

If you are using a system-wide Python installation and you only want to install the package for you,
you can add `--user` to the install commands.

Set up pre-commit hooks for automatic code formatting, etc.

```bash
pre-commit install
```

You can also invoke the pre-commit hook manually at any time with

```bash
pre-commit run
```

Once you have done this, you can launch the master branch of release helper
from any directory in your system with::

```bash
release-helper --help
```

## Running Tests

Install dependencies:

```bash
pip install -e .[test]
```

To run the Python tests, use:

```bash
pytest
```
