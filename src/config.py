#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`config` --- Default application settings
==============================================
"""


__docformat__ = "restructuredtext en"


from os import path

from utils import get_current_file_path


ROOT_DIR = path.abspath(path.dirname(get_current_file_path()))
CACHE_DIR = path.normpath(path.join(ROOT_DIR, "./cache"))
PLUGINS_DIR = path.normpath(path.join(ROOT_DIR, "./plugins"))
LOGS_DIR = path.normpath(path.join(ROOT_DIR, "./logs"))

CACHE_FILE_EXT = ".cache"
CACHE_TTL = 0
PICKLE_PROTOCOL_LEVEL = 0

SLEEP_TIME = 1

LOGGING_CONFIG = {
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
        "null": {
            "level": "DEBUG",
            "class": "logging.NullHandler",
        },
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "brief",
        },
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "formatter": "verbose",
            "filename": path.join(LOGS_DIR, "gooby.log"),
        },
        "file_errors": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "formatter": "verbose",
            "filename": path.join(LOGS_DIR, "errors.log"),
        },
        "file_session": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "formatter": "verbose",
            "filename": path.join(LOGS_DIR, "session.log"),
            "mode": "w",
        },
    },
    "loggers": {
        "Gooby": {
            "handlers": ["console", "file", "file_errors", "file_session"],
            "level": "DEBUG",
        },
        "Skype4Py": {
            "handlers": ["console", "file", "file_errors", "file_session"],
            "level": "WARNING",
        },
    },
}
