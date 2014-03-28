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
from pluginmanager import chat_is_whitelisted
from dispatcher import dispatcher
import signals


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

TODAY = "Today is {name} birthday! {interjection}!"

PREVIOUS = "It was {name} birthday {delta_days} {day_or_days} ago."

UPCOMING = "{name} birthday is coming up next in {delta_days} {day_or_days}."

DAY_OR_DAYS = {
    "singular": "day",
    "plural": "days",
}

POSSESSIVE = "{name}'s"

CONJUNCTION = "and"


def humanize_names_list(names_list,
                        possessive=POSSESSIVE,
                        conjunction=CONJUNCTION):
    """
    >>> possessive = "{name}'s"
    >>> conjunction = "and"

    >>> humanize_names_list(["herp"],
    ...                     possessive=possessive,
    ...                     conjunction=conjunction)
    u"herp's"

    >>> humanize_names_list(["herp", "derp"],
    ...                     possessive=possessive,
    ...                     conjunction=conjunction)
    u"herp's and derp's"

    >>> humanize_names_list(["herp", "derp", "durp"],
    ...                     possessive=possessive,
    ...                     conjunction=conjunction)
    u"herp's, derp's and durp's"
    """

    assert isinstance(names_list, (list, tuple))
    names = [possessive.format(name=name) for name in names_list[:]]
    if len(names) is 1:
        return names[0]
    elif len(names) > 1:
        return "{0} {conjunction} {1}".format(", ".join(names[:-1]), names[-1],
                                              conjunction=conjunction)


def str_to_datetime(date_str):
    """
    >>> str_to_datetime("13.1").strftime("%d.%m.%Y")
    '13.01.1900'

    >>> str_to_datetime("13.01").strftime("%d.%m.%Y")
    '13.01.1900'

    >>> str_to_datetime("01.13").strftime("%d.%m.%Y")
    Traceback (most recent call last):
        ...
    ValueError: Input string does not match any known date format

    >>> str_to_datetime("13.1.2000").strftime("%d.%m.%Y")
    '13.01.2000'

    >>> str_to_datetime("2000-01-13").strftime("%d.%m.%Y")
    '13.01.2000'

    >>> str_to_datetime("2000-13-01").strftime("%d.%m.%Y")
    Traceback (most recent call last):
        ...
    ValueError: Input string does not match any known date format

    >>> str_to_datetime("13.01.2000").strftime("%d.%m.%Y")
    '13.01.2000'

    >>> str_to_datetime("01.13.2000").strftime("%d.%m.%Y")
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


_timer = None


class BirthdayReminder(Plugin):
    """
    >>> import datetime
    >>> class FakeDatetime(datetime.datetime):
    ...     @classmethod
    ...     def today(cls):
    ...         return cls(2014, 3 , 27)
    >>> datetime.datetime = FakeDatetime

    >>> from Skype4Py.enums import cmsReceived
    >>> class ChatStub:
    ...     Name = "test"
    >>> class MessageStub:
    ...     Body = "!birthdays"
    ...     Chat = ChatStub
    >>> fake_status = cmsReceived

    >>> birthdays = {
    ...     "test1": "1986-03-27",
    ...     "test2": "2000-03-27",
    ...     "test3": "1986-03-25",
    ...     "test4": "2000-04-30",
    ... }
    >>> plugin = BirthdayReminder(birthdays=birthdays)
    >>> message, status = plugin.on_message_status(MessageStub, fake_status)
    >>> output = plugin.flush_output()[0]

    Output with ``#doctest: +ELLIPSIS``:

    >>> output.text #doctest: +ELLIPSIS
    u"Today is test1's and test2's...test3's...2 days...test4's...34 days."
    """

    # Time in seconds.
    CHECK_INTERVAL = 600

    @staticmethod
    @atexit.register
    def _cleanup():
        global _timer
        try:
            _timer.cancel()
            _timer.join()
        except AttributeError:
            pass
        finally:
            del _timer

    def __init__(self, priority=0, whitelist=None, **kwargs):
        super(BirthdayReminder, self).__init__(priority, whitelist, **kwargs)

        self.dates = dict()
        birthdays = self.options.setdefault("birthdays")
        for name, date_str in birthdays.iteritems():
            try:
                dt = str_to_datetime(date_str)
            except ValueError:
                self._logger.error("Parse error: '%s' for '%s'", name, date_str)
            else:
                self.dates.update({name: dt})

        if not self.dates:
            self._logger.warning("No valid dates has been parsed!")
            return

        self._notified = False
        self._logger.info("Parsed %d date(s)", len(self.dates))
        self._check_dates()

    def _check_dates(self):
        global _timer

        today = datetime.datetime.today()

        persons = list()
        for name, dt in self.dates.iteritems():
            dt = dt.replace(year=today.year)
            delta = today - dt
            if delta.days == 0:
                persons.append(name)
        if persons:
            if not self._notified:
                self._notify_chats(persons)
                self._notified = True
            return
        self._notified = False
        _timer = Timer(self.CHECK_INTERVAL, self._check_dates)
        _timer.daemon = True
        _timer.start()

    def _notify_chats(self, names):
        substitutes = {
            "name": humanize_names_list(names),
            "interjection": random.choice(INTERJECTIONS),
        }
        message = TODAY.format(**substitutes)
        if self.whitelist:
            # for chat in self.whitelist:
            #     self.output.append(ChatMessage(chat, message))
            responses = dispatcher.send(signals.REQUEST_CHATS)
            chats = responses[0]
            for chat in chats:
                if chat_is_whitelisted(chat, self.whitelist):
                    self.output.append(ChatMessage(chat, message))

    def on_message_status(self, message, status):
        if status != cmsReceived:
            return

        if not message.Body.strip().startswith("!birthdays"):
            return

        today = datetime.datetime.today()

        previous_persons = list()
        upcoming_persons = list()
        today_names = list()
        for name, dt in self.dates.iteritems():
            dt = dt.replace(year=today.year)
            delta = today - dt
            person = (name, delta)
            if delta.days > 0:
                previous_persons.append(person)
            elif delta.days < 0:
                upcoming_persons.append(person)
            elif delta.days == 0:
                today_names.append(name)

        def __same_by_delta(persons, delta):
            for _name, _delta in persons:
                if _delta.days == delta.days:
                    yield (_name, _delta)

        previous_names = list()
        previous_person = min(previous_persons, key=operator.itemgetter(1))
        previous_delta = previous_person[1]
        previous_delta_days = previous_delta.days
        for name, _ in __same_by_delta(previous_persons, previous_delta):
            previous_names.append(name)

        upcoming_names = list()
        upcoming_person = max(upcoming_persons, key=operator.itemgetter(1))
        upcoming_delta = upcoming_person[1]
        upcoming_delta_days = abs(upcoming_delta.days)
        for name, _ in __same_by_delta(upcoming_persons, upcoming_delta):
            upcoming_names.append(name)

        out = list()

        if today_names:
            substitutes = {
                "name": humanize_names_list(today_names),
                "interjection": random.choice(INTERJECTIONS),
            }
            out.append(TODAY.format(**substitutes))

        def __day_or_days(number):
            if number > 1:
                return DAY_OR_DAYS["plural"]
            return DAY_OR_DAYS["singular"]

        substitutes = {
            "name": humanize_names_list(previous_names),
            "delta_days": previous_delta_days,
            "day_or_days": __day_or_days(previous_delta_days),
        }
        out.append(PREVIOUS.format(**substitutes))

        substitutes = {
            "name": humanize_names_list(upcoming_names),
            "delta_days": upcoming_delta_days,
            "day_or_days": __day_or_days(upcoming_delta_days),
        }
        out.append(UPCOMING.format(**substitutes))

        self.output.append(ChatMessage(message.Chat.Name, "\n".join(out)))

        return message, status


if __name__ == "__main__":
    import doctest
    doctest.testmod()
