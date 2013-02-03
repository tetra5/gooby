#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
from distutils.core import setup


__version__ = None
# Get package version without importing it.
for line in open(os.path.abspath("./src/__init__.py")):
    if line.startswith("__version__"):
        exec line
        break


params = {
    "name": "gooby",
    "version": __version__,
    "description": "A modular Skype bot",
    "author": "Dmitriy Vinogradov",
    "author_email": "tetra5dotorg@gmail.com",
    "url": "https://github.com/tetra5/gooby",
    "keywords": "python skype skype4py bot",
    "license": "MIT",
    "platforms": ["Windows", "Linux", "MacOS X"],
    "requires": ["Skype4Py (>=1.0.32)"],
    "provides": ["gooby"],
    "long_description" : """Gooby is a modular plugin-based Skype bot built on
        top of Skype4Py Skype API wrapper written completely in Python.""",

    "packages": ["gooby", "gooby.plugins"],

    "package_dir": {
        "gooby": "src",
        "gooby.plugins": "src/plugins",
        },

    "classifiers": [
        "Development Status :: Development Status :: 4 - Beta",
        "Environment :: Console",
        "Topic :: Utilities",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
        "Programming Language :: Python :: 2",
        ],
    }


if __name__ == "__main__":
    setup(**params)
