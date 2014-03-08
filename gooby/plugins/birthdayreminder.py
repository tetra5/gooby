#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`birthdayreminder` --- Birthday reminder plugin
====================================================
"""


from __future__ import unicode_literals


__docformat__ = "restructuredtext en"


import atexit
import datetime
from threading import Timer
import random
import operator

from Skype4Py.enums import cmsReceived

from plugin import Plugin
from output import ChatMessage


NOTIFICATION_TEMPLATE = "Today is {recipient} birthday! {interjection}!"

REMINDER_TEMPLATE = """
It was {last_recipient} birthday {last_delta} {last_day_or_days} ago.
{next_recipient} birthday is coming up next in {next_delta} {next_day_or_days}.
"""

INTERJECTIONS = [
    "Hurrah",
    "Hooray",
    "Huzzah",
    "Fancy",
    "Awesome",
    "Whee",
    "Whoa",
    "Unbelievable",
    "Wow",
    "Amazing",
    "Yahoo",
    "Yippie",
    "Yay",
    "Yeah",
    "Exciting",
    "Yee-haw",
    "Sweet",
    "Fantastic",
    "OMG",
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


def _format_recipients(recipients):
    """
    >>> _format_recipients(["herp"])
    u"herp's"

    >>> _format_recipients(["herp", "derp"])
    u"herp's and derp's"

    >>> _format_recipients(["herp", "derp", "durp"])
    u"herp's, derp's and durp's"
    """

    if not recipients:
        raise ValueError("Input list should contain at least one string")

    recs = ["{0}'s".format(recipient) for recipient in recipients[:]]
    if len(recs) is 1:
        return recs[0]
    elif len(recs) > 1:
        return "{0} and {1}".format(", ".join(recs[:-1]), recs[-1])


_timer = None

@atexit.register
def _cleanup():
    global _timer
    if _timer:
        _timer.cancel()
        _timer.join()
    del _timer


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
        self._check()

    def _check(self):
        global _timer
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
        _timer = Timer(self.CHECK_INTERVAL, self._check)
        _timer.daemon = True
        _timer.start()

    def _notify(self, recipients):
        recs = _format_recipients(recipients)
        substitutes = {
            "recipient": recs,
            "interjection": random.choice(INTERJECTIONS),
        }
        msg = NOTIFICATION_TEMPLATE.format(**substitutes)

        for chat in self.whitelist:
            self.output.append(ChatMessage(chat, msg))

    def on_message_status(self, message, status):
        if status != cmsReceived:
            return

        if not message.Body.startswith("!birthdays"):
            return

        _pluralize = lambda n, s: "{0}s".format(s) if n > 1 else s

        last_deltas = list()
        next_deltas = list()
        todays_birthdays = list()
        today = datetime.datetime.today()
        for name, dt in self.birthdays.iteritems():
            dt = dt.replace(year=today.year)
            delta = today - dt
            item = (name, delta)
            if delta.days > 0:
                last_deltas.append(item)
            elif delta.days < 0:
                next_deltas.append(item)
            elif delta.days == 0:
                todays_birthdays.append(name)

        last_item = min(last_deltas, key=operator.itemgetter(1))
        last_recipient = _format_recipients((last_item[0],))
        last_delta = last_item[1].days
        next_item = max(next_deltas, key=operator.itemgetter(1))
        next_recipient = _format_recipients((next_item[0],))
        next_delta = abs(next_item[1].days)
        substitutes = {
            "last_recipient": last_recipient,
            "last_delta": last_delta,
            "last_day_or_days": _pluralize(last_delta, "day"),
            "next_recipient": next_recipient,
            "next_delta": next_delta,
            "next_day_or_days": _pluralize(next_delta, "day"),
        }
        msg = REMINDER_TEMPLATE.format(**substitutes)
        if todays_birthdays:
            recs = _format_recipients(todays_birthdays)
            substitutes = {
                "recipient": recs,
                "interjection": random.choice(INTERJECTIONS),
            }
            notification = NOTIFICATION_TEMPLATE.format(**substitutes)
            msg = "{0}{1}".format(notification, msg)

        self.output.append(ChatMessage(message.Chat.Name, msg))

        return message, status


if __name__ == "__main__":
    import doctest
    doctest.testmod()
