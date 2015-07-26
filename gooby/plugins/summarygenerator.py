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
# from collections import Counter

from Skype4Py.enums import cmsReceived

from plugin import Plugin
from output import ChatMessage
from config import CACHE_DIR
from cache_new import from_dict


def sanitize_string(s):
    """
    >>> print sanitize_string("чот рофл, ходил миску на лодстоуны на время")
    Чот рофл, ходил миску на лодстоуны на время.
    >>> print sanitize_string("как же так(")
    Как же так(
    >>> print sanitize_string('Рофел')
    Рофел.
    >>> print sanitize_string('а')
    А.
    """
    s = s.strip()
    if not s.endswith(tuple(string.punctuation)):
        s += '.'
    s = s[0].upper() + s[1:]
    return s


class MarkovChain(object):
    """
    >>> mc = MarkovChain.from_textfile('D:/Projects/Miscellaneous/the_golem_-_intro.txt')
    >>> mc.generate_sentences(sentences_count=3)
    """
    BRACKETS = ('()', '[]', '{}', '<>')
    QUOTES = '\'"'
    ENDING_CHARACTERS = ('!', '?', '.')

    _db = dict()
    _order = 1

    def __init__(self, order=1):
        self._order = order

    def generate_db(self, words):
        for i, word in enumerate(words[:-(self._order + 1)]):
            value_pos = i + self._order
            key = tuple(words[i:i + self._order])
            values = self._db.setdefault(key, list())
            value = words[value_pos]
            if value not in values:
                values.append(value)

    def _find_first_key(self):
        possible_keys = []
        for key in self._db.iterkeys():
            first_word = key[0]
            if first_word.endswith(tuple(string.punctuation)):
                continue
            if first_word.startswith(tuple(string.punctuation)):
                continue
            if first_word[0].isupper():
                possible_keys.append(key)
        return random.choice(possible_keys)

    def generate_sentence(self, max_len=5):
        key = self._find_first_key()
        words = list()
        words.append(key[0])
        while 1:
            possible_words = self._db.get(key)
            if not possible_words:
                break
            word = random.choice(possible_words)
            # if any(quote in word for quote in self.QUOTES):
            #     for quote in self.QUOTES:
            #         counter = Counter(''.join(words))
            #         if counter.get(quote, 0) % 2:
            #             continue
            # for left_bracket, right_bracket in self.BRACKETS:
            #     if right_bracket in word:
            #         if left_bracket not in word:
            #             if not any(left_bracket in w for w in words):
            #                 continue
            words.append(word)
            if word.endswith(self.ENDING_CHARACTERS) and len(words) > max_len:
                break
            key = key[1:] + (word, )
        return ' '.join(words)

    def generate_sentences(self, sentences_count=3, max_word_per_sentence=10):
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
    # Determines text generation frequency, i.e. generate text for every n
    # messages received.
    MESSAGE_THRESHOLD = 300

    def _init_cache(self):
        return from_dict({
            'backend': 'cache_new.SQLiteCache',
            'location': os.path.join(CACHE_DIR, "summarygenerator.sqlite"),
            'timeout': 0,
            'key_prefix': '',
        })

    def on_message_status(self, message, status):
        if status != cmsReceived:
            return

        chat_name = message.Chat.Name

        cached_messages = self.cache.get(chat_name) or list()

        if len(message.Body.split()) > 1:
            cached_messages.append(message.Body)
            self.cache.set(chat_name, cached_messages)

        cached_messages_count = len(cached_messages)

        if not cached_messages_count % 50 and cached_messages_count:
            self.logger.info("Accumulated %s/%s messages at %s",
                             cached_messages_count, self.MESSAGE_THRESHOLD,
                             chat_name)

        if cached_messages_count >= self.MESSAGE_THRESHOLD:
            text = ' '.join([sanitize_string(s) for s in cached_messages])
            mc = MarkovChain.from_string(text)
            output = '\n'.join(mc.generate_sentences())
            self.logger.info("Generating gibberish for %s", chat_name)
            self.output.append(ChatMessage(chat_name, output))
            self.logger.info("Flushing cache for %s", chat_name)
            self.cache.set(chat_name, list())

        return message, status


if __name__ == '__main__':
    import doctest
    doctest.testmod()
