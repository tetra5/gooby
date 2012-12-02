#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`gooby` --- Gooby application
==================================
"""


__docformat__ = "restructuredtext en"


import os
import sys
import time
import logging

import Skype4Py
from Skype4Py.errors import SkypeAPIError, SkypeError

from application import Application
import plugin
from utils import camelcase_to_underscore


# TODO: ConfigParser + external configuration file(s) support.

# TODO: Accept friend list requests automatically?
# Having a dedicated plugin should be sufficient.

# TODO: Rework caching.
# Use caching dict class instead of plugin cache for more versatility.
# It's also going to be much more easier to implement database caching if
# necessary.

# TODO: Move API clients to separate packages (YouTube, Google, etc).
# Common tasks should be as reusable as possible.

# TODO: Some kind of plugin manager to make use of chained plugins.
# i.e. situation when shortened URL contains YouTube video URL, and unshortener
# plugin triggers YouTube URL parser plugin as soon as it's done with
# unshortening. Note that it's going to be a long-term task and won't be here
# in near future.


class Gooby(Application):
    def __init__(self, sleep_time, plugins_dir, cache_dir, logs_dir):
        super(Gooby, self).__init__("Gooby")

        self._logger = logging.getLogger("Gooby")

        self._sleep_time = sleep_time
        self._plugins_dir = plugins_dir
        self._cache_dir = cache_dir
        self._logs_dir = logs_dir
        self._plugin_classes = []
        self._plugins = []

        # Check if essential directories are present and try to create them
        # otherwise.
        for d in (self._plugins_dir, self._cache_dir, self._logs_dir):
            if not os.path.exists(d):
                try:
                    os.mkdir(d)
                except OSError:
                    self._logger.critical(
                        "Unable to create directory '{0}'".format(d)
                    )
                    raise

        if not self._plugins_dir in sys.path:
            sys.path.insert(0, self._plugins_dir)

        # Build a list of plugin modules.
        modules = []
        for mod_path in os.listdir(self._plugins_dir):
            if mod_path.endswith(".py") and "__init__" not in mod_path:
                modules.append(mod_path[:-3])

        # Build a list of plugin classes.
        for mod in modules:
            imported = __import__(mod)

            # Here we're trying to search and find plugin classes inside a
            # module. To do that properly we have to exclude base ones first.
            for entity in set(dir(imported)).difference(dir(plugin)):
                attr = getattr(imported, entity)

                # Check if current attribute is a class which subclasses
                # the base one.
                if isinstance(attr, type) and issubclass(attr, plugin.Plugin):
                    self._plugin_classes.append(attr)

    def register_plugin(self, plugincls):
        """
        This method instantiates plugin object and then binds its event
        handlers to corresponding Skype events.

        :param plugincls: plugin class
        :type plugincls: :class:`~plugin.Plugin`

        ..seealso::
            :class:`plugin.Plugin` - base plugin class for more information
            on handling Skype events.
        """

        assert not isinstance(plugincls, plugin.Plugin), \
            "Incompatible plugin type"

        pluginobj = plugincls(parent=self)

        # Set of object attributes to be excluded.
        s = set(dir(type)).union("__weakref__")

        for event in set(dir(Skype4Py.skype.SkypeEvents)).difference(s):
            meth = "on_{0}".format(camelcase_to_underscore(event))
            try:
                handler = getattr(pluginobj, meth)
            except AttributeError:
                # Skip method if it hasn't been overridden.
                pass
            else:
                if callable(handler):
                    self._skype.RegisterEventHandler(event, handler)

        self._plugins.append(pluginobj)

    def run(self):
        self._logger.info("Starting up")

        self._logger.info("Starting Skype client")
        try:
            self.start_skype()
        except (SkypeAPIError, SkypeError) as e:
            self._logger.critical("Failed to start Skype client")
            self._logger.exception(e)
            raise

        self._logger.info("Attaching to Skype window")
        try:
            self.attach_to_skype()
        except (SkypeAPIError, SkypeError) as e:
            self._logger.critical("Failed to attach to Skype window")
            self._logger.exception(e)
            raise

        self._logger.info("Logs directory is set to '{0}'".format(
            self._logs_dir
        ))
        self._logger.info("Cache directory is set to '{0}'".format(
            self._cache_dir
        ))
        self._logger.info("Plugins directory is set to '{0}'".format(
            self._plugins_dir
        ))

        plugins_count = len(self._plugin_classes)

        if not plugins_count:
            self._logger.warning("No plugins found")
        else:
            plugin_names = [p.__name__ for p in self._plugin_classes]
            self._logger.info("Found {0} plugin(s): {1}".format(
                plugins_count, ", ".join(plugin_names)
            ))

        for i, plugincls in enumerate(self._plugin_classes):
            self._logger.info("Registering plugin {0} ({1}/{2})".format(
                plugincls.__name__, i + 1, plugins_count
            ))
            self.register_plugin(plugincls)

        # Main loop.
        self._logger.info("Entering main loop. Press Ctrl+C to exit")
        while self.is_attached():
            time.sleep(self._sleep_time)

    def stop(self):
        self._logger.info("Shutting down")

        # FIXME: Temporary work-around until the new cache system is done.
        for plugin in self._plugins:
            plugin._write_cache()

        logging.shutdown()


def main():
    import socket
    import logging.config
    import argparse

    from config import CACHE_DIR, LOGS_DIR, PLUGINS_DIR, SLEEP_TIME, \
        LOGGING_CONFIG

    if sys.version_info < (2, 7):
        raise SystemExit("Gooby requires Python 2.7")

    logging.config.dictConfig(LOGGING_CONFIG)

    socket.setdefaulttimeout(3)

    __version__ = "unknown"

    # Get package version without importing it.
    for line in open(os.path.abspath("./__init__.py")):
        if line.startswith("__version__"):
            exec line
            break

    argparser = argparse.ArgumentParser(
        version=__version__,
        description="A modular Skype bot",
        epilog="Use at own risk"
    )

    argparser.add_argument(
        "-c", "--cache_dir",
        help="cache directory path (default: '%(default)s')",
    )

    argparser.add_argument(
        "-l", "--logs_dir",
        help="logs directory path (default: '%(default)s')",
    )

    argparser.add_argument(
        "-p", "--plugins_dir",
        help="plugins directory path (default: '%(default)s')",
    )

    argparser.add_argument(
        "-s", "--sleep_time",
        type=int,
        choices=range(1, 6),
        help="main thread sleep time in seconds (default: %(default)s)",
    )

    default_args = {
        "cache_dir": os.path.relpath(CACHE_DIR),
        "logs_dir": os.path.relpath(LOGS_DIR),
        "plugins_dir": os.path.relpath(PLUGINS_DIR),
        "sleep_time": SLEEP_TIME,
    }

    argparser.set_defaults(**default_args)

    gooby = Gooby(**argparser.parse_args().__dict__)

    try:
        gooby.run()

    # Regular application exit.
    except KeyboardInterrupt:
        return 0

    except:
        print >> sys.stderr, sys.exc_info()
        return 1

    finally:
        gooby.stop()

if __name__ == "__main__":
    sys.exit(main())
