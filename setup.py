#!/usr/bin/env python
# -*- coding: utf-8 -*-


from distutils.core import setup
from src import __version__


__doc__ = """Gooby is a modular plugin-based Skype bot built on top of Skype4Py
Skype API wrapper written completely in Python."""


if __name__ == "__main__":
    setup(
        name="gooby",
        version=__version__,
        description="A modular Skype bot",
        author="Dmitriy Vinogradov",
        author_email="tetra5dotorg@gmail.com",
        url="https://github.com/tetra5/gooby",
        keywords="python skype skype4py bot",
        license="MIT License",
        platforms=[
            "Windows",
            "Linux",
            "MacOS X",
        ],
        requires=[
            "Skype4Py (>=1.0.32)",
            "lxml (>=2.3.2)",
            "oauth2 (>=1.5.211)",
        ],
        provides=[
            "gooby",
        ],
        long_description=__doc__,
        packages=[
            "gooby",
            "gooby.plugins",
        ],
        package_dir={
            "gooby": "src",
            "gooby.plugins": "src/plugins",
        },
        classifiers=[
            "Development Status :: 4 - Beta",
            "Environment :: Console",
            "Topic :: Utilities",
            "Intended Audience :: Developers",
            "Intended Audience :: End Users/Desktop",
            "License :: OSI Approved :: MIT License",
            "Natural Language :: English",
            "Operating System :: Microsoft :: Windows",
            "Operating System :: POSIX :: Linux",
            "Operating System :: MacOS :: MacOS X",
            "Programming Language :: Python :: 2.7",
            "Topic :: Communications",
            "Topic :: Internet",
        ],
    )
