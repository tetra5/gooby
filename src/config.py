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
            "maxBytes": 1024000,
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

# Plugin cache configuration. Keys are case-sensitive and should match
# corresponding plugin class names. Regular Python dictionary is being used as
# a cache-like storage by default unless it hasn't been set explicitly.
#
# It's also possible to add additional config entries to setup the low-level
# cache system usage, i.e.:
#
# >>> cache = cache.get_cache("derp")
#
# will be looking for "derp" cache config entry firstly.
#
# Note this behaviour is a subject to change in a near future to remotely
# match Django cache system which is far more flexible.
CACHE_CONFIG = {
    "VimeoURLParser": {
        "backend": "cache.SQLiteCache",
        "timeout": 0.0,
        "location": path.join(CACHE_DIR, "vimeo.sqlite"),
    },
    "YouTubeURLParser": {
        "backend": "cache.SQLiteCache",
        "timeout": 0.0,
        "location": path.join(CACHE_DIR, "youtube.sqlite"),
    },
    "URLDiscoverer": {
        "backend": "cache.SQLiteCache",
        "timeout": 128000.0 * 42,  # 42 days.
        "location": path.join(CACHE_DIR, "urls.sqlite"),
    },
    "SteamURLParser": {
        "backend": "cache.SQLiteCache",
        "timeout": 3600.0,
        "location": path.join(CACHE_DIR, "steam.sqlite"),
    },
    "HerpDerper": {
        "backend": "cache.SQLiteCache",
        "timeout": 0.0,
        "location": path.join(CACHE_DIR, "herpderper.sqlite"),
    },
    "IMDbURLParser": {
        "backend": "cache.SQLiteCache",
        "timeout": 0.0,
        "location": path.join(CACHE_DIR, "imdb.sqlite"),
    },
}


try:
    from localconfig import *
except ImportError:
    pass
