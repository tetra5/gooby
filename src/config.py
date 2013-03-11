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
PLUGINS_DIR = path.normpath(path.join(ROOT_DIR, "./plugins"))

# CACHE_DIR = path.normpath(path.join(ROOT_DIR, "./cache"))
# LOGS_DIR = path.normpath(path.join(ROOT_DIR, "./logs"))
HOME_DIR = path.normpath(path.join(path.expanduser("~"), ".gooby"))
CACHE_DIR = path.normpath(path.join(HOME_DIR, "./cache"))
LOGS_DIR = path.normpath(path.join(HOME_DIR, "./logs"))

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
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "brief",
        },
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "verbose",
            "filename": path.join(LOGS_DIR, "gooby.log"),
            "maxBytes": 128000,
            "backupCount": 4,
        },
        "file_errors": {
            "level": "WARNING",
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "verbose",
            "filename": path.join(LOGS_DIR, "errors.log"),
            "maxBytes": 128000,
            "backupCount": 4,
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


try:
    from config_local import *
except ImportError:
    pass
