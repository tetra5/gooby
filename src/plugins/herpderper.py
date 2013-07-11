#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`herpderper` --- Derping the herp since 1895
=================================================
"""


__docformat__ = "restructuredtext en"


import random
import re

from Skype4Py.enums import cmsReceived, cmeEmoted

from plugin import Plugin


def all_same(myiter):
    """
    Check whether all elements in iterable are the same.

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


def parse_linux_quote(message):
    """
    >>> message = ur'''
    ... > [Wednesday, June 26, 2013 1:37:59 PM username derp] a quoted message
    ...
    ... some other message.
    ... '''
    >>> found = parse_linux_quote(message)
    >>> assert found is not None
    >>> assert found.group("quote") == "a quoted message"
    """

    pattern = re.compile(
        r"""
        # Conversation message pattern which matches Linux Skype client message
        # quotation.
        >\s\[
        (?P<datetime>
            (?P<day>
                \w+
            ),\s
            (?P<month>
                \w+
            )\s
            (?P<date>
                \d{1,2}
            ),\s
            (?P<year>
                \d{4}
            )\s
            (?P<time>
                \d{1,2}:\d{2}:\d{2}
            )\s
            (?P<ampm>
                \w{2}
            )
        )\s
        (?P<sender>
            .*
        )
        ]\s
        (?P<quote>
            .*
        )\n?
        (?P<message>
            .*
        )
        """,
        re.UNICODE | re.VERBOSE)

    return re.search(pattern, message)


def parse_macosx_quote(message):
    """
    >>> message = ur'''
    ... 26.06.13 в 13:37 skypename.derp написал (-а):
    ... > a quoted message
    ... some other message.
    ... '''
    >>> found = parse_macosx_quote(message)
    >>> assert found is not None
    >>> assert found.group("quote") == "a quoted message"
    """

    pattern = re.compile(
        r"""
        # Conversation message pattern which matches Mac OS X Skype client
        # message quotation.
        (?P<date>
            \d{2}.\d{2}.\d{2}
        )\s\w+\s
        (?P<time>
            \d{2}:\d{2}
        )\s
        # There are no space characters in Skype user names.
        (?P<sender>
            [a-zA-Z0-9_\-\.]+
        )\s.*:\n
        >\s*
        (?P<quote>
            .*
        )\n*
        (?P<message>
            .*
        )
        """,
        re.UNICODE | re.VERBOSE)

    return re.search(pattern, message)


def parse_windows_quote(message):
    """
    >>> message = ur'''[1:37:59] username derp: a quoted message
    ... <<<'''
    >>> found = parse_windows_quote(message)
    >>> assert found is not None
    >>> assert found.group("quote") == "a quoted message"
    """

    pattern = re.compile(
        r"""
        # Conversation message pattern which matches Windows Skype client
        # message quotation.
        \[
        (?P<time>
            \d{1,2}:\d{2}:\d{2}
        )\s*
        (?P<ampm>
            \w{2}
        )?]\s
        (?P<sender>
            .*
        ):\s
        (?P<quote>
            .*
        )\n*
        <<<\s*
        (?P<message>
            .*
        )
        """,
        re.UNICODE | re.VERBOSE)

    return re.search(pattern, message)


def message_is_quoted(message):
    """
    >>> # Windows client.
    >>> message = ur'''
    ... [1:37:59 PM] юзернейм derp: a quoted message
    ...
    ... <<< тест
    ... '''
    >>> assert message_is_quoted(message) is True

    >>> # Linux client.
    >>> message = ur'''
    ... > [Wednesday, June 26, 2013 1:37:59 PM юзернейм derp] a quoted message
    ...
    ... some other message.
    ... '''
    >>> assert message_is_quoted(message) is True

    >>> # Mac OS X client.
    >>> message = ur'''
    ... 26.06.13 в 13:37 skypename.derp написал (-а):
    ... > a quoted message
    ... some other message.
    ... '''
    >>> assert message_is_quoted(message) is True
    """

    if parse_macosx_quote(message) is not None:
        return True
    if parse_linux_quote(message) is not None:
        return True
    if parse_windows_quote(message) is not None:
        return True
    return False


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
        if status != cmsReceived or message.Type == cmeEmoted:
            return

        if not any(t.lower() in message.Body.lower() for t in self._triggers):
            return

        if message_is_quoted(message.Body):
            return

        msg = []

        max_words = 3
        words = []
        for _ in xrange(1, max_words + 1):
            words.append(random.choice(["herp", "derp", "hurr", "durr"]))

        msg.append(" ".join(words))

        if len(words) is max_words and all_same(words):
            self._logger.info("Jackpot winner {0}".format(message.FromHandle))

            try:
                wins = int(self._cache.get(message.FromHandle))
            except TypeError:
                wins = 0
            wins += 1
            self._cache.set(message.FromHandle, wins)

            msg.append("{0} wins the jackpot! {1} in total".format(
                message.FromDisplayName, wins
            ))

        message.Chat.SendMessage(u"\n".join(msg))


if __name__ == "__main__":
    import doctest
    doctest.testmod()
