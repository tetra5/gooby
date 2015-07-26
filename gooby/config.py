#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`config` --- Default application settings
==============================================
"""


from __future__ import unicode_literals


__docformat__ = "restructuredtext en"


import os

from utils import get_current_file_path


ROOT_DIR = os.path.abspath(os.path.dirname(get_current_file_path()))
PLUGINS_DIR = os.path.normpath(os.path.join(ROOT_DIR, "./plugins"))

HOME_DIR = os.path.normpath(os.path.join(os.path.expanduser("~"), ".gooby"))
# CACHE_DIR = os.path.normpath(os.path.join(ROOT_DIR, "./cache"))
CACHE_DIR = os.path.normpath(os.path.join(HOME_DIR, "./cache"))
# LOGS_DIR = os.path.normpath(os.path.join(ROOT_DIR, "./logs"))
LOGS_DIR = os.path.normpath(os.path.join(HOME_DIR, "./logs"))

SLEEP_TIME = 1

GOOGLE_API_KEY = 'your_google_API_key'

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
            "filename": os.path.join(LOGS_DIR, "gooby.log"),
            "maxBytes": 1024000,
            "backupCount": 4,
        },
        "file_errors": {
            "level": "WARNING",
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "verbose",
            "filename": os.path.join(LOGS_DIR, "errors.log"),
            "maxBytes": 128000,
            "backupCount": 4,
        },
        "file_session": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "formatter": "verbose",
            "filename": os.path.join(LOGS_DIR, "session.log"),
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
CACHE_CONFIG = {
    "VimeoURLParser": {
        "backend": "cache.SQLiteCache",
        "timeout": 0.0,
        "location": os.path.join(CACHE_DIR, "vimeo.sqlite"),
    },
    "YouTubeURLParser": {
        "backend": "cache.SQLiteCache",
        "timeout": 0.0,
        "location": os.path.join(CACHE_DIR, "youtube.sqlite"),
    },
    "URLDiscoverer": {
        "backend": "cache.SQLiteCache",
        "timeout": 128000.0 * 42,  # 42 days.
        "location": os.path.join(CACHE_DIR, "urls.sqlite"),
    },
    # "SteamURLParser": {
    #     "backend": "cache.SQLiteCache",
    #     "timeout": 3600.0,
    #     "location": os.path.join(CACHE_DIR, "steam.sqlite"),
    # },
    "HerpDerper": {
        "backend": "cache.SQLiteCache",
        "timeout": 0.0,
        "location": os.path.join(CACHE_DIR, "herpderper.sqlite"),
    },
    "IMDbURLParser": {
        "backend": "cache.SQLiteCache",
        "timeout": 0.0,
        "location": os.path.join(CACHE_DIR, "imdb.sqlite"),
    },
    "DuplicateURLChecker": {
        "backend": "cache.SQLiteCache",
        "timeout": 128000.0 * 3,  # 3 days.
        "location": os.path.join(CACHE_DIR, "duplicateurls.sqlite"),
    },
    "GuessThePicture": {
        "backend": "cache.SQLiteCache",
        "timeout": 128000.0 * 42,  # 42 days.
        "location": os.path.join(CACHE_DIR, "guessthepicture.sqlite"),
    },
    "LentaURLParser": {
        "backend": "cache.SQLiteCache",
        "timeout": 0,
        "location": os.path.join(CACHE_DIR, "lentaurlparser.sqlite"),
    },
    "CoubURLParser": {
        "backend": "cache.SQLiteCache",
        "timeout": 0,
        "location": os.path.join(CACHE_DIR, "couburlparser.sqlite"),
    },
    "TwitchTvNotifier": {
        "backend": "cache.SQLiteCache",
        "timeout": 0,
        "location": os.path.join(CACHE_DIR, "twitchtvnotifier.sqlite"),
    },
}

# Plugin configuration syntax:
#
# PLUGINS_CONFIG = {
#     # Plugin module, plugin class name.
#     "plugins.myplugin.MyPlugin": {
#
#         # Plugin execution priority, higher priority gets handled earlier.
#         # Default: 0.
#         "priority": 1,
#
#         # List of chat names, where this particular plugin is allowed.
#         # Recent/bookmarked chat lists are accessible by executing the
#         # following command:
#         #     $ python ./gooby.py listchats
#         #
#         # Default: None or empty list, which means whitelist is disabled.
#         "whitelist": [
#             # Whitelisted by chat name with chat ID:
#             "#herp/$derp;0000000000000000",
#             # Whitelisted by chat name only (Skype is known for changing chat
#             # IDs):
#             "#herp/$derp"
#             # Whitelisted by ID only:
#             "0000000000000000"
#         ],
#     },
# }
PLUGINS_CONFIG = {
    "plugins.urldiscoverer.URLDiscoverer": {
        "priority": 42,
    },

    "plugins.youtubeurlparser.YouTubeURLParser": {},

    "plugins.vimeourlparser.VimeoURLParser": {},

    # "plugins.steamurlparser.SteamURLParser": {},

    "plugins.steamstoreparser.SteamStoreParser": {},

    "plugins.noncegenerator.NonceGenerator": {},

    "plugins.imdburlparser.IMDbURLParser": {},

    "plugins.herpderper.HerpDerper": {},

    "plugins.guessthepicture.GuessThePicture": {},

    "plugins.ezroller.EzRoller": {},

    "plugins.duplicateurlchecker.DuplicateURLChecker": {},

    "plugins.lentaurlparser.LentaURLParser": {},
    
    "plugins.couburlparser.CoubURLParser": {},

    "plugins.twitchtvnotifier.TwitchTvNotifier": {
        "check_interval": 60,
        "streams": [
            # "herp",
            # "derp",
        ],
    },

    "plugins.birthdayreminder.BirthdayReminder": {
        "birthdays": {
            # Valid date formats:
            # ["%d.%m", "%d.%m.%Y", "%Y-%m-%d"]
            #
            # Examples:
            # "Derp": "31.12.1900",
            # "Derp": "31.12",
            # "Derp": "2000-12-31",
        },
    },

    "plugins.azazafication.Azazafication": {},

    "plugins.fakesed.FakeSed": {},

    # "plugins.littlehelper.LittleHelper": {},

    "plugins.summarygenerator.SummaryGenerator": {},
}

# Import custom settings.
try:
    from localconfig import *
except ImportError:
    pass
