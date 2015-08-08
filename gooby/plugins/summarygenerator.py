#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`summarygenerator` --- Markov Chain based summary generator
================================================================
"""


from __future__ import unicode_literals


__docformat__ = "restructuredtext en"


import os
import random
import string
import re

from Skype4Py.enums import cmsReceived

from plugin import Plugin
from output import ChatMessage
from config import CACHE_DIR
from cache_new import from_dict
from plugins.herpderper import (
    parse_linux_quote, parse_macosx_quote, parse_windows_quote
)


def parse_windows_multiple_quote(message):
    """
    >>> message = ur'''[06.08.2015 12:30:27] some derp: le message >> Kappa
    ... [06.08.2015 12:32:51] othername.derp: Asdf?'''
    >>> messages = parse_windows_multiple_quote(message)
    >>> messages
    [u'le message >> Kappa', u'Asdf?']
    >>> messages = parse_windows_multiple_quote('')
    >>> messages
    []
    """
    pattern = re.compile(
        r"""
        \[
        (?P<date>
            \d{2}\.\d{2}\.\d{4}
        )\s
        (?P<time>
            \d{2}:\d{2}:\d{2}
        )
        \]\s
        (?P<sender>
            .+
        ):\s
        (?P<message>
            .*
        )\s*
        """,
        re.VERBOSE | re.UNICODE | re.MULTILINE
    )

    try:
        return [m.groupdict().get('message') for m in pattern.finditer(message)]
    except AttributeError:
        pass
    return []


def url_filter(word):
    crap = ('http', 'ftp', 'www', 'mailto')
    return '' if any(substring in word.lower() for substring in crap) else word


def timestamp_filter(word):
    pattern = re.compile(ur'(\[\d{1,2}:\d{1,2}:\d{2}\])')
    return pattern.sub('', word)


def quotation_filter(word):
    s = set(word)
    return '' if len(s) is 1 and any(char in s for char in '<>') else word


def sentence_normalizer(sentence):
    """
    >>> print sentence_normalizer("чот рофл, ходил ")
    Чот рофл, ходил.
    >>> print sentence_normalizer("как же так(")
    Как же так(
    >>> print sentence_normalizer('Рофел')
    Рофел.
    >>> print sentence_normalizer('а')
    А.
    >>> print sentence_normalizer('.один... два, три .. четыре. пять')
    Один... Два, три.. Четыре. Пять.
    >>> print sentence_normalizer('///.')
    <BLANKLINE>
    >>> print sentence_normalizer('.')
    <BLANKLINE>
    """
    pattern = re.compile(r'\w+', re.U)
    sentences = [word.strip() for word in re.split(ur'(\.)', sentence) if word]
    ending = '.'

    output = []
    for word in sentences:
        if not output:
            if word == '.':
                continue
            output.append(word)
            continue
        if word != ending and output[-1][-1] == ending:
            output.append(word)
        if word == ending:
            output[-1] += word

    for i, s in enumerate(output):
        output[i] = output[i][0].upper() + output[i][1:]
        if not output[i].endswith(tuple(string.punctuation)):
            output[i] += ending

    if not pattern.match(' '.join(output)):
        return ''

    if not filter(None, ' '.join(output).split(ending)):
        return ''

    return ' '.join(output)


def sentence_quote_filter(sentence):
    for func in (parse_windows_quote, parse_linux_quote, parse_macosx_quote):
        match = func(sentence)
        if match is not None:
            try:
                return match.group('message')
            except AttributeError:
                pass
    messages = parse_windows_multiple_quote(sentence)
    if messages:
        return ' '.join(messages)
    return sentence


# Filter order matters.
SENTENCE_PREFILTERS = (sentence_quote_filter, )
WORD_FILTERS = (url_filter, timestamp_filter, quotation_filter)
SENTENCE_POSTFILTERS = (sentence_normalizer, )


class MarkovChain(object):
    """
    >>> mc = MarkovChain.from_textfile('D:/Projects/Miscellaneous/the_golem_-_intro.txt')
    >>> mc.generate_sentences(sentences_count=3)
    """
    ENDING_CHARACTERS = ('!', '?', '.')
    RUSSIAN_ALPHABET = u'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'
    ENGLISH_ALPHABET = string.lowercase
    ALPHABETIC = RUSSIAN_ALPHABET + ENGLISH_ALPHABET

    def __init__(self, order=1):
        self._order = order
        self._db = dict()
        self._order = 1

    def generate_db(self, words):
        for i, word in enumerate(words[:-(self._order + 1)]):
            value_pos = i + self._order
            key = tuple(words[i:i + self._order])
            values = self._db.setdefault(key, set())
            value = words[value_pos]
            values.add(value)

    def _find_first_key(self):
        possible_keys = []
        for key in self._db.iterkeys():
            first_word = key[0]
            last_word = key[-1]
            if not first_word.lower().startswith(tuple(self.ALPHABETIC)):
                continue
            if first_word.endswith(tuple(string.punctuation)):
                continue
            if first_word.startswith(tuple(string.punctuation)):
                continue
            if last_word.endswith(tuple(string.punctuation)):
                continue
            if first_word.istitle():
                possible_keys.append(key)
        if not possible_keys:
            possible_keys.extend(self._db.keys())
        return random.choice(possible_keys)

    def generate_sentence(self, max_len=8):
        key = self._find_first_key()
        words = list()
        words.append(key[0])
        while 1:
            possible_words = self._db.get(key)
            if not possible_words:
                break
            word = random.choice(list(possible_words))
            words.append(word)
            if word.endswith(self.ENDING_CHARACTERS) and len(words) > max_len:
                break
            key = key[1:] + (word, )
        return ' '.join(words)

    def generate_sentences(self, sentences_count=3, max_word_per_sentence=24):
        sentences = []
        for _ in xrange(sentences_count):
            sentence = self.generate_sentence()
            sentences.append(sentence)
            if len(sentence.split()) > max_word_per_sentence:
                break
        return sentences

    @classmethod
    def from_string(cls, text, order=1, skip_urls=True):
        obj = cls(order)
        words = []
        for word in text.split():
            if not word:
                continue
            if skip_urls and any(s in word.lower() for s in ('http', 'www.')):
                continue
            words.append(word)
        obj.generate_db(words)
        return obj

    @classmethod
    def from_textfile(cls, path, order=1):
        with open(os.path.abspath(path), mode='rb') as f:
            text = f.read().decode('utf-8')
        obj = cls.from_string(text, order)
        return obj


class SummaryGenerator(Plugin):
    # Determines text generation frequency, i.e. generate text for every
    # n messages received.
    MESSAGE_THRESHOLD = 200

    def _init_cache(self):
        return from_dict({
            'backend': 'cache_new.SQLiteCache',
            'location': os.path.join(CACHE_DIR, "summarygenerator.sqlite"),
            'timeout': 0,
            'key_prefix': '',
        })

    @staticmethod
    def process_message(message):
        output = message.Body
        for f in SENTENCE_PREFILTERS:
            output = f(output)
        for f in WORD_FILTERS:
            output = ' '.join(filter(None, [f(w) for w in output.split()]))
        for f in SENTENCE_POSTFILTERS:
            output = f(output)
        return output

    def on_message_status(self, message, status):
        if status != cmsReceived:
            return

        chat_name = message.Chat.Name

        cached_messages = self.cache.get(chat_name) or list()

        processed_message = self.process_message(message)

        if processed_message:
            cached_messages.append(processed_message)
            self.cache.set(chat_name, cached_messages)

        cached_messages_count = len(cached_messages)

        if not cached_messages_count % 50 and cached_messages_count:
            self.logger.info("Accumulated %s/%s messages at %s",
                             cached_messages_count, self.MESSAGE_THRESHOLD,
                             chat_name)

        if cached_messages_count >= self.MESSAGE_THRESHOLD:
            text = ' '.join([sentence for sentence in cached_messages])
            mc = MarkovChain.from_string(text)
            output = ' '.join(mc.generate_sentences())
            self.logger.info("Generating gibberish for %s", chat_name)
            self.output.append(ChatMessage(chat_name, output))
            self.logger.info("Flushing cache for %s", chat_name)
            self.cache.set(chat_name, list())

        return message, status


if __name__ == '__main__':
    import doctest
    doctest.testmod()
