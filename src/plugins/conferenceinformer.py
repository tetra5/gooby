#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
@author: tetra5 <tetra5dotorg@gmail.com>
"""


__version__ = "0.1.0"


from plugin import ConferenceCommandPlugin
from plugin.ConferenceCommandPlugin import log_request


class ConferenceInformer(ConferenceCommandPlugin):
    def __init__(self, parent):
        super(ConferenceInformer, self).__init__(parent)
        self._commands = {
            "!topic": self.on_topic_command,
            }

    @log_request
    def on_topic_command(self, message):
        """Displays current chat room topic."""
        chat = message.Chat
        chat.SendMessage("Current topic: '%s'" % chat.Topic)
