#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`birthdayreminder` --- Birthday reminder plugin
====================================================
"""


from __future__ import unicode_literals


__docformat__ = "restructuredtext en"


import datetime
from threading import Timer
import random

from plugin import Plugin
from output import ChatMessage


INTERJECTIONS = [
    "Hurrah!",
    "Hooray!",
    "Huzzah!",
    "Fancy!",
    "Awesome!",
    "Whee!",
    "Whoa!",
    "Unbelievable!"
    "Wow!",
    "Amazing!",
    "Yahoo!",
    "Yippie!",
    "Yay!",
    "Yeah!",
    "Exciting!",
    "Yee-haw!",
    "Sweet!",
]


def str_to_datetime(date_str):
    """
    >>> str_to_datetime("13.1")
    datetime.datetime(1900, 1, 13, 0, 0)

    >>> str_to_datetime("13.01")
    datetime.datetime(1900, 1, 13, 0, 0)

    >>> str_to_datetime("01.13")
    Traceback (most recent call last):
        ...
    ValueError: Input string does not match any known date format

    >>> str_to_datetime("13.1.2000")
    datetime.datetime(2000, 1, 13, 0, 0)

    >>> str_to_datetime("13.01.2000")
    datetime.datetime(2000, 1, 13, 0, 0)

    >>> str_to_datetime("01.13.2000")
    Traceback (most recent call last):
        ...
    ValueError: Input string does not match any known date format
    """

    dt = None
    formats = ["%d.%m", "%d.%m.%Y", "%Y-%m-%d"]
    for fmt in formats:
        try:
            dt = datetime.datetime.strptime(date_str, fmt)
            break
        except ValueError:
            pass
    if dt is None:
        raise ValueError("Input string does not match any known date format")
    return dt


class BirthdayReminder(Plugin):
    CHECK_INTERVAL = 600

    def __init__(self, priority=0, whitelist=None, **kwargs):
        super(BirthdayReminder, self).__init__(priority, whitelist, **kwargs)

        self.birthdays = dict()
        birthdays = self.options.setdefault("birthdays")
        for name, date_str in birthdays.iteritems():
            try:
                dt = str_to_datetime(date_str)
            except ValueError:
                self._logger.error("Parse error: '%s' for '%s'", name, date_str)
            else:
                self.birthdays.update({name: dt})

        if not self.birthdays:
            self._logger.warning("No valid dates has been parsed!")
            return

        self._notified = False
        self._repeats = 0
        self._repeat_timers = list()
        self._logger.info("Parsed %d date(s)", len(self.birthdays))
        self._timer = None
        self._check()

    def _check(self):
        today = datetime.datetime.today()
        recipients = list()
        for name, dt in self.birthdays.iteritems():
            dt = dt.replace(year=today.year)
            delta = today - dt
            if delta.days == 0:
                recipients.append(name)
        if recipients:
            if not self._notified:
                self._notify(recipients)
                self._notified = True
            return
        self._notified = False
        self._timer = Timer(self.CHECK_INTERVAL, self._check)
        self._timer.daemon = True
        self._timer.start()

    def _notify(self, recipients):
        if not recipients:
            raise ValueError("Input list should contain at least one string")

        template = "Today is {0} birthday!"
        message = None

        recs = ["{0}'s".format(recipient) for recipient in recipients[:]]
        if len(recs) is 1:
            message = template.format(recs[0])
        elif len(recs) > 1:
            m = "{0} and {1}".format(", ".join(recs[:-1]), recs[-1])
            message = template.format(m)

        message = "{0} {1}".format(message, random.choice(INTERJECTIONS))

        for chat in self.whitelist:
            self.output.append(ChatMessage(chat, message))

if __name__ == "__main__":
    import doctest
    doctest.testmod()
