#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
@author: tetra5 <tetra5dotorg@gmail.com>
"""


__version__ = "0.1.0"


import sys
import logging
import time
import signal

from Skype4Py import SkypeAPIError, SkypeError

from application import Application


LOGGER_NAME = "Gooby"
LOG_FORMAT = "%(asctime)-15s %(levelname)s %(name)s: %(message)s"
LOG_LEVEL = logging.DEBUG

PLUGINS_DIR = "./plugins/"

SLEEP_TIME = 5


class ConsoleApplication(Application):
    """
    Skype bot console application.
    """
    def __init__(self):
        super(ConsoleApplication, self).__init__()
        self._plugins_dir = PLUGINS_DIR
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
    logging.basicConfig(format=LOG_FORMAT)
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(LOG_LEVEL)

    logger.info("Initializing application ...")
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
                pluginobj = app.register_plugin(plugin)
                pluginobj.set_logger_name("%s.%s" % (LOGGER_NAME, plugin_name))
            except:
                logger.error("Failed to register %s", plugin_name)
                raise
            else:
                logger.info("Registered plugin %s", plugin_name)

    """
    Main loop.
    """
    logger.info("Entering main loop. Press Ctrl+C or Ctrl+Break to exit")
    signal.signal(signal.SIGBREAK, signal.default_int_handler)
    try:
        while 1:
            time.sleep(app.sleep_time)

    except KeyboardInterrupt:
        # Regular application exit.
        return 0

    except SkypeAPIError, e:
        logger.exception(e)

    except SkypeError, e:
        logger.exception(e)

    except Exception, e:
        # Unexpected error has occured. Terminating application.
        logger.exception(e)
        return 1

    finally:
        logger.info("Shutting down")
        logging.shutdown()


if __name__ == "__main__":
    sys.exit(main())
