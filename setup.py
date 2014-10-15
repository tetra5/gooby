#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys
from distutils.core import setup

from pip.req import parse_requirements


sys.path.append('./gooby')


from gooby.version import __version__


__doc__ = """Gooby is a modular plugin-based Skype bot built on top of Skype4Py
Skype API wrapper written completely in Python."""


if sys.argv[-1] == "test":
    status = os.system("python -m unittest discover -v -p test_*.py")
    sys.exit(1 if status > 127 else status)


install_requires = []
try:
    requirements = parse_requirements("./requirements.txt")
    install_requires[:] = [str(r.req) for r in requirements]
except (OSError, IOError):
    pass


def full_split(path, result=None):
    """
    Split a path name into components (the opposite of os.path.join)
    in a platform-neutral way.
    """

    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == '':
        return [tail] + result
    if head == path:
        return result
    return full_split(head, [tail] + result)


EXCLUDE_FROM_PACKAGES = []


def is_package(package_name):
    for pkg in EXCLUDE_FROM_PACKAGES:
        if package_name.startswith(pkg):
            return False
    return True


# Compile the list of packages available, because distutils doesn't have
# an easy way to do this.
packages, package_data = [], {}


root_dir = os.path.dirname(__file__)
if root_dir != "":
    os.chdir(root_dir)
project_dir = "gooby"


for dir_path, dir_names, file_names in os.walk(project_dir):
    # Ignore PEP 3147 cache dirs and those whose names start with "."
    dir_names[:] = [
        d for d in dir_names if not d.startswith('.') and d != "__pycache__"
    ]
    parts = full_split(dir_path)
    package_name = "/".join(parts)
    if "__init__.py" in file_names and is_package(package_name):
        packages.append(package_name)
    elif file_names:
        relative_path = []
        while "/".join(parts) not in packages:
            relative_path.append(parts.pop())
        relative_path.reverse()
        path = os.path.join(*relative_path)
        package_files = package_data.setdefault("/".join(parts), [])
        package_files.extend([os.path.join(path, f) for f in file_names])


if __name__ == "__main__":
    setup(
        name="gooby",
        version=__version__,
        description="A modular Skype bot",
        long_description=__doc__,
        author="Dmitriy Vinogradov",
        author_email="tetra5dotorg@gmail.com",
        url="https://github.com/tetra5/gooby",
        download_url="https://github.com/tetra5/gooby",
        keywords="python skype skype4py bot",
        license="MIT License",
        platforms=["Windows", "Linux", "MacOS X"],
        install_requires=install_requires,
        provides=["gooby"],
        packages=packages,
        package_data=package_data,
        include_package_data=True,
        package_dir={"gooby": "gooby"},
        classifiers=[
            "Development Status :: 5 - Production/Stable",
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
            "Topic :: Communications :: Chat",
        ],
    )
