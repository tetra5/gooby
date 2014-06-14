#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`azazafication`
====================
"""


from __future__ import unicode_literals


__docformat__ = "restructuredtext en"


from collections import Counter
import random

from Skype4Py.enums import cmsReceived

from plugin import Plugin
from output import ChatMessage


OPENING_BRACES = "("

CLOSING_BRACES = ")"

SAD_ANSWERS = [
    "грустняффо",
    "грустняво",
    "печаль",
    "пичалька",
    "печальбеда",
    "бида",
    "пичаль",
]

JOYFUL_ANSWERS = [
    "лал",
    "{0}{1}".format("а", "за" * random.randint(2, 5)),
    "{0}{1}".format("ах", "за" * random.randint(2, 5)),
    "{0}{1}".format("а" * random.randint(0, 1), "ха" * random.randint(3, 5)),
    "красава",
    "малаца",
    "жжош",
    "харош",
    "+1",
]

SKIPPED = [
    "=)",
    "=(",
    ":)",
    ":(",
    "%)",
    "%(",
    ";)",
    ";(",
    "=-)",
    "=-(",
    ":-)",
    ":-(",
    "%-)",
    "%-(",
    ";-)",
    ";-(",
]


def braces_are_matched(s,
                       opening_braces=OPENING_BRACES,
                       closing_braces=CLOSING_BRACES):
    """
    >>> assert braces_are_matched("test)") is False

    >>> assert braces_are_matched("test(") is False

    >>> assert braces_are_matched("((test") is False

    >>> assert braces_are_matched("a(a)a") is True

    >>> assert braces_are_matched("a()a()a") is True

    >>> assert braces_are_matched("((aa))") is True

    >>> assert braces_are_matched("") is True
    """

    assert isinstance(s, basestring)
    stack = list()
    for char in s:
        if char in opening_braces:
            stack.append(char)
        elif char in closing_braces:
            if not stack:
                return False
            stack.pop()
    return not stack


class Azazafication(Plugin):
    """
    http://xkcd.com/859/
    """

    TRIGGER_THRESHOLD = 0.1

    def on_message_status(self, message, status):
        if status != cmsReceived:
            return

        s = message.Body.strip().replace(" ", "")
        for smile in SKIPPED:
            s = s.replace(smile, "")

        if braces_are_matched(s):
            return

        if random.uniform(0.0, 1.0) >= self.TRIGGER_THRESHOLD:
            return

        counter = Counter(s)
        opening_braces_count = 0
        closing_braces_count = 0
        for opening_brace in OPENING_BRACES:
            opening_braces_count += counter.get(opening_brace, 0)
        for closing_brace in CLOSING_BRACES:
            closing_braces_count += counter.get(closing_brace, 0)

        if opening_braces_count > closing_braces_count:
            text = "{0}{1}".format(random.choice(SAD_ANSWERS),
                                   "(" * random.randint(1, 5))
            self.output.append(ChatMessage(message.Chat.Name, text))
        else:
            text = "{0}{1}".format(random.choice(JOYFUL_ANSWERS),
                                   ")" * random.randint(1, 5))
            self.output.append(ChatMessage(message.Chat.Name, text))

        return message, status


if __name__ == "__main__":
    import doctest
    doctest.testmod()
