#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`ezroller` --- Number rolling made easy
============================================

Simple plugin that reacts on "!roll <n>" text message and rolls a random number
between 1 and `n`. `n` is set to 100 by default.
"""


__docformat__ = "restructuredtext en"


import random

from plugin import ChatCommandPlugin


class EzRoller(ChatCommandPlugin):
    def __init__(self, parent):
        super(EzRoller, self).__init__(parent)
        self._commands = {
            "!roll": self.on_roll_command,
        }

    def on_roll_command(self, message):
        max_value = message.Body.strip().split()[1]
        try:
            max_value = abs(int(max_value))
        except (ValueError, IndexError):
            max_value = 100

        value = random.randint(1, max_value)
        message.Chat.SendMessage("{0} has rolled {1} (1-{2})".format(
            message.FromDisplayName, value, max_value
        ))
