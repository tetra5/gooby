#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`test`
===========
"""


from __future__ import unicode_literals


__docformat__ = "restructuredtext en"


from Skype4Py.enums import cmsReceived

from plugin import Plugin
from output import ChatMessage


class Test(Plugin):
    def on_message_status(self, message, status):
        if status != cmsReceived:
            return

        self.output.append(ChatMessage(message.Chat.Name, "herp derp"))
        return message, status


if __name__ == "__main__":
    import doctest
    doctest.testmod()
