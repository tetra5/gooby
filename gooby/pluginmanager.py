#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`pluginmanager` --- Plugin management facility
===================================================
"""


from __future__ import unicode_literals


__docformat__ = "restructuredtext en"


import importlib
import itertools
import re
import logging
import operator

from Skype4Py.skype import SkypeEvents

from plugin import DEFAULT_PLUGIN_CONFIG
from errors import PluginError


_debug = False

log = logging.getLogger("Gooby.PluginManager")

if _debug:
    logging.basicConfig()
    log.setLevel(logging.DEBUG)


def camelcase_to_underscores(s):
    """
    >>> camelcase_to_underscores("CamelCasedStringTEST")
    u'camel_cased_string_test'
    >>> camelcase_to_underscores("MessageStatus")
    u'message_status'
    """

    return re.sub("(?!^)([A-Z]+)", r"_\1", s).lower()


# A rather dirty way of getting a complete Skype events list.
_excluded = set(dir(type)).union(["__weakref__"])
SKYPE_EVENTS = frozenset(dir(SkypeEvents)).difference(_excluded)
del _excluded

EVENT_HANDLERS = dict()
for evt in SKYPE_EVENTS:
    EVENT_HANDLERS.update({evt: "on_{0}".format(camelcase_to_underscores(evt))})


class PluginManager(object):
    def __init__(self, config=None):
        self.config = config or dict()
        self._handlers = dict()
        self._plugins = list()
        self._import()

    def _import(self):
        log.info("Found %d plugin(s)", len(self.config))
        for p_name, p_conf in self.config.iteritems():
            try:
                module_name, p_class = p_name.rsplit(".", 1)
                module = importlib.import_module(module_name)
                p = getattr(module, p_class)
            except (ImportError, AttributeError, ValueError) as error:
                raise PluginError("Unable to import {0}: {1}".format(
                    p_name, error.message))
            else:
                conf = DEFAULT_PLUGIN_CONFIG.copy()
                conf.update(p_conf)
                log.info("Registering %s", p_class)
                self._plugins.append(p(**conf))

    @property
    def plugins(self):
        for p in sorted(self._plugins,
                        key=operator.attrgetter("priority"),
                        reverse=True):
            yield p

    def register_event_handler(self, event, handler):
        log.debug("Registering event handler {0} for event {1}".format(
            handler, event))

        if event not in SKYPE_EVENTS:
            log.error("Unknown event {0}, skipping".format(event))
            return None

        self._handlers.setdefault(event, list())
        self._handlers[event].append(handler)
        return self._handlers[event][-1]

    def handlers(self, event):
        def _yield_from_plugins():
            for p in self.plugins:
                method = EVENT_HANDLERS.get(event)
                try:
                    handler = getattr(p, method)
                except (AttributeError, TypeError):
                    continue
                else:
                    if callable(handler):
                        yield handler, p.priority, p.whitelist

        def _yield_from_handlers():
            for e, handlers in self._handlers.iteritems():
                if e == event:
                    for handler in handlers:
                        if callable(handler):
                            yield handler, 0, None

        return itertools.chain(_yield_from_plugins(), _yield_from_handlers())

    def on_event(self, event):
        """
        An entry point for a corresponding event handler execution chain.
        """

        handlers = self.handlers

        class ProxyHandler(object):
            def __init__(self, _event):
                self._event = _event

            def __call__(self, *args):
                if self._event not in SKYPE_EVENTS:
                    log.error("Unknown event received: {0}".format(self._event))
                    return

                log.debug("Event received: {0}".format(self._event))

                initial_args = dict()

                for handler, priority, whitelist in sorted(
                        handlers(self._event),
                        key=operator.itemgetter(1),
                        reverse=True):

                    if self._event == "MessageStatus":
                        try:
                            message, status = args
                            chat = message.Chat.Name
                        except (AttributeError, TypeError):
                            pass
                        else:
                            if whitelist and chat not in whitelist:
                                log.debug("{0} is not whitelisted".format(
                                    chat))
                                continue

                    # Since event handler execution is chained, we have to
                    # make sure each of them return same variables or None,
                    # in which case we pass valid arguments restored from
                    # the previously successful call to the next
                    # consecutively called handler.
                    # arg1, arg2 = handler1(arg1, arg2)
                    # arg1, arg2 = handler2(arg1, arg2)
                    # ...etc.
                    handler_name = handler.__name__
                    initial_args.setdefault(handler_name, args)

                    log.debug("Executing {0} with priority {1}".format(
                        handler, priority))
                    args = handler(*args)

                    if args is None:
                        args = tuple()
                    elif not isinstance(args, tuple):
                        args = (args,)

                    if args != initial_args[handler_name]:
                        log.debug("Arguments mismatch, recovering")
                        args = initial_args[handler_name]

                return args

        return ProxyHandler(event)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
