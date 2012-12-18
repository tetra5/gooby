#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`herpderper` --- Derping the herp since 1895
=================================================
"""


__docformat__ = "restructuredtext en"


import random
from collections import Counter
import re

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
            u"ue,b",
            u"gooby",
            u"пщщин",
            ]

        if not any(s.lower() in message.Body.lower() for s in strings):
            return

        found = False
        for s in strings:
            s = unicode(s)
            p = re.compile(ur"{0}\b".format(s), re.IGNORECASE | re.UNICODE)
            matches = re.findall(p, message.Body)
            print matches
            if matches:
                found = True
                break
        if not found:
            return

        output = []
        max_words_count = 6
        words_count = random.randint(1, max_words_count)

        herps = ["herp"] * random.randint(1, words_count)
        herpsderps = herps + ["derp"] * (words_count - len(herps))
        random.shuffle(herpsderps)

        output.append(" ".join(herpsderps))

        c = Counter(herpsderps)
        if c.get(herpsderps[0]) is max_words_count:
            output.append("{0} wins the jackpot!".format(
                message.FromDisplayName
            ))

        message.Chat.SendMessage("\n".join(output))


if __name__ == "__main__":
    import doctest
    doctest.testmod()
