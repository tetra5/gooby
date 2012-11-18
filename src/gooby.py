#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`gooby` --- Gooby application
==================================
"""


import sys
import time
import logging
import logging.config

from Skype4Py import SkypeAPIError, SkypeError

from application import Application
from config import PLUGINS_DIRECTORY, CACHE_DIRECTORY, LOGS_DIRECTORY, \
    LOGGER_CONFIG


SLEEP_TIME = 1


# Known issues:
# - Application isn't able to receive Skype messages for some reason sometimes.


# TODO: Cache auto-save feature.


# TODO: Accept friend list requests automatically?


class ConsoleApplication(Application):
    """
    Skype bot console application.
    """
    def __init__(self):
        super(ConsoleApplication, self).__init__()
        self._plugins_dir = PLUGINS_DIRECTORY
        self._sleep_time = SLEEP_TIME

    def set_sleep_time(self, value):
        self._sleep_time = value

    def get_sleep_time(self):
        return self._sleep_time

    sleep_time = property(get_sleep_time, set_sleep_time)


def main():
    """
    Gooby pls.
    """
    logging.config.dictConfig(LOGGER_CONFIG)
    logger = logging.getLogger("Gooby")

    logger.info("Initializing application ...")
    logger.debug("Cache directory is set to '{0}'".format(CACHE_DIRECTORY))
    logger.debug("Logs directory is set to '{0}'".format(LOGS_DIRECTORY))

    app = ConsoleApplication()

    logger.info("Attaching to Skype window ...")
    try:
        app.attach_to_skype()
    except (SkypeError, SkypeAPIError) as e:
        logger.exception(e)
        logger.critical("Failed to attach to Skype window, program terminated")
        logging.shutdown()
        return 1
    else:
        logger.info("Attached to Skype window")

    plugins_count = len(app.plugins)
    if plugins_count is 0:
        logger.warning("No plugins found")
    else:
        logger.info("Found %d plugin(s)", plugins_count)
        for i, plugin in enumerate(app.plugins):
            plugin_name = plugin.__name__
            logger.info("Registering plugin %s (%d/%d) ...", plugin_name,
                        i + 1, plugins_count)
            try:
                app.register_plugin(plugin)
            except:
                logger.error("Failed to register %s", plugin_name)
                raise
            else:
                logger.info("Registered plugin %s", plugin_name)

    if sys.platform == "win32":
        import signal
        signal.signal(signal.SIGBREAK, signal.default_int_handler)

    logger.info("Entering main loop. Press Ctrl+C or Ctrl+Break to exit")

    # Main loop.
    try:
        # TODO: optimizations?
        while app.is_attached():
            time.sleep(app.sleep_time)

    except KeyboardInterrupt:
        # Regular application exit.
        return 0

    except SkypeAPIError, e:
        logger.exception(e)
        return 1

    except SkypeError, e:
        logger.exception(e)
        return 1

    except Exception, e:
        logger.exception(e)
        return 1

    except:
        raise

    finally:
        logger.info("Writing plugin cache ...")
        for pluginobj in app.plugin_objects:
            pluginobj.write_cache()
        logger.info("Shutting down")
        logging.shutdown()


if __name__ == "__main__":
    if sys.version_info < (2, 7):
        raise SystemExit("This program requires Python 2.7 or greater.")

    sys.exit(main())
