#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`output`
=============
"""


from __future__ import unicode_literals


__docformat__ = "restructuredtext en"


import time

from Skype4Py.errors import SkypeError

from errors import PluginOutputError


class ChatMessage(object):
    def __init__(self, chat_name, text, timestamp=None):
        self.chat_name = chat_name
        self.text = text
        self.timestamp = timestamp or time.time()

    def send(self, skype_instance):
        try:
            chat = skype_instance.Chat(self.chat_name)
            message = chat.SendMessage(self.text)
        except SkypeError as e:
            raise PluginOutputError("Skype error {0}: {1}".format(e[0], e[1]))
        return message

    def __repr__(self):
        return "<ChatMessage '{0}' to '{1}' on '{2}'>".format(
            self.text, self.chat_name, self.timestamp)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
