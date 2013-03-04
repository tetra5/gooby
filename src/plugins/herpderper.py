#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`herpderper` --- Derping the herp since 1895
=================================================
"""


__docformat__ = "restructuredtext en"


import random
import re

from Skype4Py.enums import cmsReceived

from plugin import Plugin


def all_same(myiter):
    """
    Check whether all elements in iterable are the same.

    :return: True or False
    :rtype: `bool`

    >>> all_same([1, 1, 1, 1])
    True
    >>> all_same([0, 1, 1])
    False
    >>> all_same("aaa")
    True
    >>> all_same("aab")
    False
    """

    return all([myiter[0] == item for item in myiter])


class HerpDerper(Plugin):
    """
    A very simple and "fun" plugin which reacts on certain keywords by replying
    messages with random amount of "herp"'s and "derp"'s while maintaining
    meaningless statistics.
    """

    _triggers = [
        u"губи",
        u"ue,b",
        u"gooby",
        u"пщщин",
    ]

    def on_message_status(self, message, status):
        if status != cmsReceived:
            return

        match = None
        for t in self._triggers:
            p = re.compile(ur"{0}\b".format(t), re.IGNORECASE | re.UNICODE)
            match = re.search(p, message.Body)
            if match:
                break

        if not match:
            return

        output = []

        max_herpderps = 6
        words_count = random.randint(1, max_herpderps)
        herps = ["herp"] * random.randint(1, words_count)
        herpsderps = herps + ["derp"] * (words_count - len(herps))

        random.shuffle(herpsderps)

        output.append(" ".join(herpsderps))

        if len(herpsderps) is max_herpderps and all_same(herpsderps):
            output.append("{0} wins the jackpot!".format(
                message.FromDisplayName
            ))

        message.Chat.SendMessage("\n".join(output))


if __name__ == "__main__":
    import doctest
    doctest.testmod()
