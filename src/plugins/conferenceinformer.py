#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
Created on 16.08.2012

@author: tetra5 <tetra5dotorg@gmail.com>
"""


__version__ = "0.1.0"


from plugin import ConferenceCommandPlugin


class ConferenceInformer(ConferenceCommandPlugin):
    def __init__(self, parent):
        super(ConferenceInformer, self).__init__(parent)
        self._commands = {
            "!topic": self.on_topic_command,
            }

    def on_topic_command(self, message):
        """Displays current chat room topic."""
        self._logger.debug("Chat topic request from '%s'" % message.FromHandle)
        chat = message.Chat
        chat.SendMessage("Current topic: '%s'" % chat.Topic)
