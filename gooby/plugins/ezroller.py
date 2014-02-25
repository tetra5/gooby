#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`ezroller` --- Number rolling made easy
============================================

Simple plugin that reacts on "!roll <n>" text message and rolls a random number
between 1 and `n`. `n` is set to 100 by default.
"""


from __future__ import unicode_literals


__docformat__ = "restructuredtext en"


import random

from plugin import ChatCommandPlugin
from output import ChatMessage


class EzRoller(ChatCommandPlugin):
    def __init__(self, priority, whitelist, **kwargs):
        super(EzRoller, self).__init__(priority, whitelist, **kwargs)
        self._commands = {
            u"!roll": self.on_roll_command,
            u"!кщдд": self.on_roll_command,
            u"!ролл": self.on_roll_command,
        }

    def on_roll_command(self, message):
        try:
            max_value = abs(int(message.Body.strip().split()[1]))
        except (ValueError, IndexError):
            max_value = 100

        value = random.randint(1, max_value)
        msg = "{0} has rolled {1} (1-{2})".format(message.FromDisplayName,
                                                  value, max_value)
        self.output.append(ChatMessage(message.Chat.Name, msg))
        #message.Chat.SendMessage("{0} has rolled {1} (1-{2})".format(
        #    message.FromDisplayName, value, max_value
        #))
