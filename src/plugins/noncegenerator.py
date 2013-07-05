#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`noncegenerator` --- Nonce bullshit generator
==================================================
"""


__docformat__ = "restructuredtext en"


from string import punctuation
from collections import OrderedDict, deque
from random import choice, shuffle, uniform
from math import ceil

from Skype4Py.enums import cmsReceived, cmeEmoted

from plugin import Plugin


VOWELS = u"аеёиоуыэюя"

SUBSTITUTES = {
    u"а": u"хуя",
    u"е": u"хуе",
    u"ё": u"хуё",
    u"и": u"хуи",
    u"о": u"хуё",
    u"у": u"хую",
    u"ы": u"хуи",
    u"э": u"хуэ",
    u"ю": u"хую",
    u"я": u"хуя",
}

EXTRA_WORDS = [
    u"тян",
    u"кун",
    u"лал",
    u"лойс",
    u"азаза",
    u"нарм",
    u"бахнул",
    u"бахает",
    u"саси",
    u"лах",
    u"бомбанул",
    u"бамбан",
    u"пукан",
    u"пердак",
    u"выйгра",
    u"сасай",
    u"сасал",
]

TEMPLATES_SIMPLE = [
    u"{nonce_word}",
    u"{word}-{nonce_word}",
]

TEMPLATES_COMPOSITE = [
    u"{word}-{nonce_word}",
    u"{nonce_word}",
    u"{nonce_word}, блядь",
    u"{nonce_word}, нахуй",
    u"{word}-{nonce_word}, блядь",
    u"{word}-{nonce_word}, нахуй",
]

TEMPLATES_NONCE_ONLY = [
    u"{nonce_word}",
]


def _translate(s, characters, translate_to=u" "):
    translation_table = dict((ord(char), translate_to) for char in characters)
    return s.translate(translation_table)


def find_first_vowel_index(word):
    """
    >>> assert find_first_vowel_index("учёт".decode("utf8")) is 2

    >>> assert find_first_vowel_index("АОРТА".decode("utf8")) is 1

    >>> assert find_first_vowel_index("прнс".decode("utf8")) is None
    """

    index = word.lower().find(u"ё")

    if index is not -1:
        return index

    found = False

    for index, char in enumerate(word):
        if char.lower() in VOWELS.lower():
            if not found:
                found = True
        else:
            if found:
                break

    return index - 1 if found else None


def word_is_eligible(word, vowel_threshold=2):
    """
    >>> assert word_is_eligible("учёт".decode("utf8"), 2) is True

    >>> assert word_is_eligible("откос".decode("utf8"), 2) is True

    >>> assert word_is_eligible("молоко".decode("utf8"), 4) is False
    """

    if any(sub.lower() in word.lower() for sub in SUBSTITUTES.itervalues()):
        return False

    vowel_count = 0

    for vowel in VOWELS.lower():
        vowel_count += word.lower().count(vowel.lower())

    return vowel_count >= vowel_threshold


def generate_nonce_word(word, preserve_case=False):
    """
    >>> nw = generate_nonce_word("ЛАЛКА".decode("utf8"), preserve_case=True)
    >>> assert nw == "ХУЯЛКА".decode("utf8")

    >>> nw = generate_nonce_word("Лалка!".decode("utf8"), preserve_case=True)
    >>> assert nw == "Хуялка!".decode("utf8")

    >>> nw = generate_nonce_word("ЛАЛКА".decode("utf8"), preserve_case=False)
    >>> assert nw == "хуялка".decode("utf8")
    """

    index = find_first_vowel_index(word)

    if index is None:
        return word

    char = word[index]
    nonce_word = u"{0}{1}".format(SUBSTITUTES[char.lower()], word[index + 1:])

    if not preserve_case:
        return nonce_word.lower()

    if word[:index + 1].istitle():
        nonce_word = nonce_word.title()
    elif word[:index + 1].isupper():
        nonce_word = nonce_word.upper()
    elif word[:index + 1].islower():
        nonce_word = nonce_word.lower()

    return nonce_word


def generate_nonce_phrase(phrase,
                          nonce_quantity=1.0,
                          extra_words=EXTRA_WORDS,
                          templates_simple=TEMPLATES_SIMPLE,
                          templates_composite=TEMPLATES_COMPOSITE,
                          templates_nonce_only=TEMPLATES_NONCE_ONLY,
                          preserve_case=True):
    """
    >>> templates_simple = ["{word}-{nonce_word}".decode("utf8")]
    >>> templates_composite = ["{word}-{nonce_word}".decode("utf8")]
    >>> templates_nonce_only = ["test".decode("utf8")]
    >>> extra_words = ["двач".decode("utf8")]

    >>> np = generate_nonce_phrase("ПРОВЕРКА, двач!".decode("utf8"),
    ...                            extra_words=extra_words,
    ...                            templates_simple=templates_simple,
    ...                            nonce_quantity=1.0)
    >>> assert np == "ПРОВЕРКА-ХУЁВЕРКА, двач-хуяч!".decode("utf8")

    >>> np = generate_nonce_phrase("Проверка".decode("utf8"),
    ...                            templates_composite=templates_composite,
    ...                            nonce_quantity=1.0)
    >>> assert np == "Проверка-Хуёверка".decode("utf8")

    >>> np = generate_nonce_phrase("рики-тики-тави".decode("utf8"),
    ...                            templates_nonce_only=templates_nonce_only,
    ...                            nonce_quantity=1.0)
    >>> assert np == "test-test-test".decode("utf8")

    >>> np = generate_nonce_phrase("без изменений".decode("utf8"),
    ...                            nonce_quantity=0.0)
    >>> assert np == "без изменений".decode("utf8")
    """

    assert 0 <= nonce_quantity <= 1.0

    substitutes = OrderedDict()
    words = phrase.split()

    if len(words) is 1:
        templates = templates_composite
    else:
        templates = templates_simple

    for word in words:
        w = word.strip(u"{0}{1}".format(u"—", punctuation))
        word_parts = _translate(w, punctuation).split()

        if len(word_parts) > 1:
            templates = templates_nonce_only

        for part in word_parts:
            if not word_is_eligible(part) and part.lower() not in extra_words:
                continue
            nonce_word = generate_nonce_word(part, preserve_case=preserve_case)
            template = choice(templates)
            sub = {part: template.format(word=part, nonce_word=nonce_word)}
            substitutes.update(sub)

    for _ in range(int(ceil(len(substitutes) * nonce_quantity))):
        match = choice(substitutes.keys())
        replace = substitutes.pop(match)
        phrase = phrase.replace(match, replace)

    return phrase


def count_vowels(word):
    """
    >>> assert count_vowels("проверка".decode("utf8")) is 3
    """

    return len([char for char in word if char.lower() in VOWELS])


class NonceGenerator(Plugin):
    """
    Herp derp.
    """

    # Quota total messages limit (int).
    QUOTA_MESSAGE_LIMIT = 3

    # Quota message interval limit in seconds (float).
    TIME_INTERVAL_LIMIT = 2

    # A value which algorithm should trigger on randomly (float 0 <= x <= 1.0)
    # Default is 1/1600.
    TRIGGER_THRESHOLD = 0.000625

    # A value which "special words only" algorithm should trigger on
    # randomly. (float 0 <= x <= 1.0). Default is 1/2.
    EXTRA_TRIGGER_THRESHOLD = 1.0

    HISTORY_LIMIT = 5

    _quotas = None

    # Previous output history for excessive flood prevention.
    _history = None

    def on_message_status(self, message, status):
        if status != cmsReceived or message.Type == cmeEmoted:
            return

        assert 0 <= self.TRIGGER_THRESHOLD <= 1.0

        assert 0 <= self.EXTRA_TRIGGER_THRESHOLD <= 1.0

        _output = list()

        if self._history is None:
            self._history = dict()

        if message.Chat.Name not in self._history:
            self._history[message.Chat.Name] = deque(maxlen=self.HISTORY_LIMIT)

        if self._quotas is None:
            self._quotas = dict()

        if message.FromHandle not in self._quotas:
            self._quotas[message.FromHandle] = list()

        # Algorithm which only triggers on certain keywords.
        if any(word.lower() in message.Body.lower() for word in EXTRA_WORDS):
            words = message.Body.split()
            for word in words:
                word = word.strip(u"{0}{1}".format(u"—", punctuation))
                for keyword in EXTRA_WORDS:
                    if word.lower().startswith(keyword.lower()):
                        if self.EXTRA_TRIGGER_THRESHOLD - uniform(0.0, 1.0) > 0:
                            _output.append(generate_nonce_phrase(word))

        # Quota algorithm.
        # Triggers on several subsequent messages are being sent by the same
        # user within the quota limits.
        quota_is_reached = False

        timestamps = self._quotas[message.FromHandle]

        if not timestamps:
            timestamps.append(message.Timestamp)
        else:
            if message.Timestamp - timestamps[-1] <= self.TIME_INTERVAL_LIMIT:
                timestamps.append(message.Timestamp)
                if len(timestamps) > self.QUOTA_MESSAGE_LIMIT:
                    quota_is_reached = True
            else:
                self._quotas[message.FromHandle] = [message.Timestamp]

        if quota_is_reached:
            result = generate_nonce_phrase(message.Body)
            if message.Body.lower() != result.lower():
                _output.append(result)

        # Algorithm which triggers randomly if nothing else has been
        # triggered before.
        if not _output:
            if self.TRIGGER_THRESHOLD - uniform(0.0, 1.0) > 0:
                result = generate_nonce_phrase(phrase=message.Body,
                                               nonce_quantity=uniform(0.1, 0.9))
                if message.Body.lower() != result.lower():
                    _output.append(result)

        if _output:
            msg = list()
            history = self._history[message.Chat.Name]
            for string_ in _output:
                if string_ not in history:
                    msg.append(string_)
                    history.append(string_)

            shuffle(msg)

            message.Chat.SendMessage(u"\n".join(msg))


if __name__ == "__main__":
    import doctest
    doctest.testmod()
