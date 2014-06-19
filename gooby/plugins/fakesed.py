#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`fakesed`
==============

s/old/new
"""


from __future__ import unicode_literals


__docformat__ = "restructuredtext en"


import re
from collections import deque

from Skype4Py.enums import cmsReceived

from plugin import Plugin
from output import ChatMessage


_regexp = re.compile('s/(\w+)/(\w+)', re.UNICODE | re.IGNORECASE)


class FakeSed(Plugin):
    HISTORY_LENGTH = 5

    def __init__(self, priority, whitelist, **kwargs):
        super(FakeSed, self).__init__(priority, whitelist, **kwargs)
        self._history = dict()

    def on_message_status(self, message, status):
        if status != cmsReceived:
            return

        if message.Chat.Name not in self._history:
            self._history[message.Chat.Name] = deque(maxlen=self.HISTORY_LENGTH)

        match = re.match(_regexp, message.Body)

        if not match:
            self._history[message.Chat.Name].append(message.Body)
            return

        search, replace = match.groups((1, 2))

        replaced = False
        replaced_str = ''
        for msg in self._history[message.Chat.Name]:
            m = msg.replace(match.group(0), '')
            replaced_str = msg.replace(search, replace)
            if m != replaced_str:
                replaced = True
                break

        msg = None
        if replaced:
            msg = ">>> {0}".format(replaced_str)
        else:
            m = message.Body.replace(match.group(0), '')
            replaced_str = m.replace(search, replace)
            if m != replaced_str:
                msg = ">>> {0}".format(m)

        if msg is not None:
            self.output.append(ChatMessage(message.Chat.Name, msg))

        return message, status


if __name__ == "__main__":
    import doctest
    doctest.testmod()
