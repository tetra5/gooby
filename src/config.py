#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`settings` --- Global application settings
===============================================
"""


__docformat__ = "restructuredtext en"


from os import path


ROOT_DIRECTORY = path.abspath(path.dirname(__file__))
CACHE_DIRECTORY = path.normpath(path.join(ROOT_DIRECTORY, "./cache"))
PLUGINS_DIRECTORY = path.normpath(path.join(ROOT_DIRECTORY, "./plugins"))

CACHE_TTL = 1200
PICKLE_PROTOCOL_LEVEL = 0
