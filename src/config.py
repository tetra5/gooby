#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`config` --- Global application settings
=============================================
"""


__docformat__ = "restructuredtext en"


from os import path


ROOT_DIRECTORY = path.abspath(path.dirname(__file__))
CACHE_DIRECTORY = path.normpath(path.join(ROOT_DIRECTORY, "./cache"))
PLUGINS_DIRECTORY = path.normpath(path.join(ROOT_DIRECTORY, "./plugins"))
LOGS_DIRECTORY = path.normpath(path.join(ROOT_DIRECTORY, "./logs"))

CACHE_TTL = 0
PICKLE_PROTOCOL_LEVEL = 0

LOGGER_CONFIG = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "verbose": {
            "format": "%(asctime)-15s %(levelname)s %(name)s: %(message)s",
        },
        "brief": {
            "format": "%(name)s: %(message)s",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "brief",
        },
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "formatter": "verbose",
            "filename": path.join(LOGS_DIRECTORY, "gooby.log"),
        },
        "file_errors": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "formatter": "verbose",
            "filename": path.join(LOGS_DIRECTORY, "errors.log"),
        },
        "file_session": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "formatter": "verbose",
            "filename": path.join(LOGS_DIRECTORY, "session.log"),
            "mode": "w",
        },
    },
    "loggers": {
        "Gooby": {
            "handlers": ["console", "file", "file_errors", "file_session"],
            "level": "DEBUG",
        },
    },
}
