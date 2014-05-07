#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`gooby` --- Gooby application
==================================
"""


from __future__ import unicode_literals, print_function


__docformat__ = "restructuredtext en"


import os
import sys
import logging
import time
import itertools

import Skype4Py

from pluginmanager import PluginManager, SKYPE_EVENTS
from config import PLUGINS_CONFIG
from version import __version__ as gooby_version
from errors import PluginOutputError, PluginError
from dispatcher import dispatcher
import signals


log = logging.getLogger("Gooby")


class Gooby(object):
    def __init__(self, options):
        self.options = options
        self.plugin_manager = None

        log.info("Gooby %s", gooby_version)
        log.debug("Options: %s", self.options)

        skype_options = {}
        if any(sys.platform.startswith(p) for p in ("linux", "darwin")):
            skype_options.update({"Transport": "x11"})
        self.skype = Skype4Py.Skype(**skype_options)
        setattr(self.skype, "FriendlyName", "Gooby")
        self.skype.Client.Start(Minimized=True, Nosplash=True)
        self.skype.Attach(Protocol=8)

        for path in (options.cache_dir, options.logs_dir):
            if not os.path.exists(path):
                os.mkdir(path)
        log.info("Cache: %s", os.path.abspath(options.cache_dir))
        log.info("Logs: %s", os.path.abspath(options.logs_dir))

    def __connect_signals(self):
        dispatcher.connect(self._plugins, signals.REQUEST_PLUGINS, False)
        dispatcher.connect(self._usage, signals.REQUEST_USAGE, False)
        dispatcher.connect(self._chats, signals.REQUEST_CHATS, False)

    def _chats(self):
        """Signal receiver."""

        for chat in itertools.chain(self.skype.RecentChats,
                                    self.skype.BookmarkedChats):
            yield chat.Name

    def _usage(self, target, *args, **kwargs):
        """Signal receiver."""

        for plugin in self.plugin_manager.plugins:
            usage = plugin.usage
            if plugin.__class__.__name__.lower() == target.lower():
                return [usage(*args, **kwargs)]
        return None

    def _plugins(self):
        """Signal receiver."""

        plugins = list()
        for plugin in self.plugin_manager.plugins:
            plugins.append(plugin.__class__.__name__)
        return plugins

    def _list_chats(self):
        log.info("Recent chats:")
        for i, chat in enumerate(self.skype.RecentChats):
            log.info("%3d) %s", i + 1, chat.Name)

        log.info("Bookmarked chats:")
        for i, chat in enumerate(self.skype.BookmarkedChats):
            log.info("%3d) %s", i + 1, chat.Name)

    def _attached_to_skype(self):
        return self.skype.AttachmentStatus == Skype4Py.enums.apiAttachSuccess

    def run(self):
        if self.options.listchats:
            self._list_chats()
            return

        self.__connect_signals()

        self.plugin_manager = PluginManager(PLUGINS_CONFIG)
        for event in SKYPE_EVENTS:
            self.skype.RegisterEventHandler(
                event, self.plugin_manager.on_event(event))

        log.info("*** Entering main loop. Press CTRL+C to quit ***")
        while self._attached_to_skype():
            for plugin in self.plugin_manager.plugins:
                messages = plugin.flush_output()
                for message in messages:
                    try:
                        message.send(self.skype)
                    except PluginOutputError, e:
                        log.error("Unable to send message %s by plugin %s: %s",
                                  plugin, message.text, e)
            time.sleep(self.options.sleep_time)

    def shutdown(self):
        log.info("Shutting down")
        del self.skype
        logging.shutdown()


def main():
    import traceback
    import logging.config
    import argparse
    import datetime
    import codecs

    from config import (CACHE_DIR, LOGS_DIR, SLEEP_TIME, LOGGING_CONFIG,
                        CACHE_CONFIG)
    import cache

    if sys.platform == "win32":
        writer = codecs.getwriter("utf-8")
        writer(sys.stdout)
        writer(sys.stderr)

    logging.config.dictConfig(LOGGING_CONFIG)

    cache.dict_config(CACHE_CONFIG)

    parser = argparse.ArgumentParser(
        version=gooby_version,
        description="A modular Skype bot",
        epilog="Use at own risk"
    )

    parser.add_argument(
        "-C", "--cache-dir",
        dest="cache_dir",
        help="cache directory path (default: '%(default)s')",
    )

    parser.add_argument(
        "-L", "--logs-dir",
        dest="logs_dir",
        help="logs directory path (default: '%(default)s')",
    )

    parser.add_argument(
        "-s", "--sleep",
        dest="sleep_time",
        type=int,
        choices=range(1, 6),
        help="main thread sleep time in seconds (default: %(default)s)",
    )

    parser.add_argument(
        "listchats",
        nargs="?",
        help="output both recent and bookmarked chat lists and quit"
    )

    defaults = {
        "cache_dir": CACHE_DIR,
        "logs_dir": LOGS_DIR,
        "sleep_time": SLEEP_TIME,
    }

    parser.set_defaults(**defaults)
    options = parser.parse_args()

    gooby = None

    try:
        gooby = Gooby(options)
        gooby.run()

    except (KeyboardInterrupt, SystemExit):
        # Regular application exit.
        return 0

    except PluginError, e:
        log.error("Plugin error: %s", e)

    except:
        dt = datetime.date.today().isoformat()
        f = os.path.join(options.logs_dir, "traceback-{0}.log".format(dt))
        message = "Unexpected error has occurred. Terminating application"
        print(message, file=sys.stderr)
        try:
            with open(f, "w") as _f:
                print("See '{0}' for more details".format(f), file=sys.stderr)
                traceback.print_exc(file=_f)
        except (IOError, OSError):
            traceback.print_exc(file=sys.stderr)
        return 1

    finally:
        if gooby is not None:
            gooby.shutdown()


if __name__ == "__main__":
    sys.exit(main())
