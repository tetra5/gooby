#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
@author: tetra5 <tetra5dotorg@gmail.com>
"""


__version__ = "2012.1"


from plugin import Plugin


class VerboseDebugger(Plugin):
    def on_message_status(self, message, status):
        self._logger.debug(
            "Message status: %s, type: %s, from: %s (%s), chat name: %s" %
                (status, message.Type, message.FromDisplayName,
                 message.FromHandle, message.ChatName))
