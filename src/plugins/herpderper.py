#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`herpderper` --- Derping the herp since 1895
=================================================
"""

__docformat__ = "restructuredtext en"


import random

from Skype4Py.enums import cmsReceived

from plugin import Plugin


class HerpDerper(Plugin):
    def __init__(self, parent):
        super(HerpDerper, self).__init__(parent)

    def on_message_status(self, message, status):
        if status != cmsReceived:
            return

        strings = [
            u"губи",
            u"gooby",
            u"uemb",
            u"пщщин",
            u"губе",
            u"ue,t",
            u"губан",
            u"ue,fy",
        ]

        if not any(s in message.Body.lower() for s in strings):
            return

        chat = message.Chat

        max_words_count = 5

        herps = ["herp"] * random.randint(1, max_words_count - 1)
        derps = ["derp"] * (max_words_count - len(herps))

        herpsderps = herps + derps
        random.shuffle(herpsderps)

        chat.SendMessage(" ".join(herpsderps))


if __name__ == "__main__":
    import doctest
    doctest.testmod()
