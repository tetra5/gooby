#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`herpderper` --- Derping the herp since 1895
=================================================
"""


__docformat__ = "restructuredtext en"


import random

from Skype4Py.enums import cmsReceived, cmeEmoted

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


# TODO: Maintain jackpot statistics.


class HerpDerper(Plugin):
    """
    A very simple and "fun" plugin which reacts on certain keywords by replying
    messages with random amount of "herp"'s and "derp"'s while maintaining
    meaningless statistics.

    26.06.13 в 13:42 tetra5.org написал (-а):
    > ouya оказалась фэйлом
    невообразимо!


    > [Wednesday, June 26, 2013 3:35:23 PM slimcheg] что он выбрал очень хороший рейс для этого

    хуйпизда
    """

    _triggers = [
        u"губи",
        u"ue,b",
        u"gooby",
        u"пщщин",
    ]

    def on_message_status(self, message, status):
        if status != cmsReceived and message.Type == cmeEmoted:
            return

        if not any(t.lower() in message.Body.lower() for t in self._triggers):
            return

        msg = []

        max_herpderps = 4
        words_count = random.randint(1, max_herpderps)
        herps = ["herp"] * random.randint(1, words_count)
        herpsderps = herps + ["derp"] * (words_count - len(herps))
        random.shuffle(herpsderps)

        msg.append(" ".join(herpsderps))

        if len(herpsderps) is max_herpderps and all_same(herpsderps):
            msg.append("{0} wins the jackpot!".format(message.FromDisplayName))

        message.Chat.SendMessage(u"\n".join(msg))


if __name__ == "__main__":
    import doctest
    doctest.testmod()
