#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`urldiscoverer` --- URL unshortener plugin
===============================================
"""


__docformat__ = "restructuredtext en"


import urllib2
import re

from Skype4Py.enums import cmsReceived

from plugin import Plugin


_p = re.compile(ur"[\W_]+")


def find_shortened_urls(shorteners, haystack=""):
    """
    Generator.

    Yields every valid shortened URL found in haystack string. Does not prepend
    "http://" part to result. Converts all non-letter characters to
    underscores.

    .. note::
        URL path part is case-sensitive.

    >>> shorteners = ["t.co", "tinyurl.com", "bit.ly", "goo.gl"]
    >>> haystack = '''t.co/derp,     BiT.Ly/HerP http://tinyURL.com/TEST
    ... www.goo.gl/herpDERP/derpwww.bit.ly/herpDERP goo.gl/Test/WoNtWoRk
    ... testbit.ly/123.jpg'''
    >>> found = list(find_shortened_urls(shorteners, haystack))
    >>> expected = ['bit.ly/herpDERP', 't.co/derp', 'bit.ly/HerP',
    ... 'tinyurl.com/TEST']
    >>> sorted(found) == sorted(expected)
    True
    """

    for s in shorteners:
        func = map(lambda x: filter(None, x[x.lower().find(s):].split("/")),
                   haystack.split())
        for host, path in filter(lambda x: len(x) is 2, func):
            if "." not in path:
                path = re.sub(_p, "_", path).strip("_")
                yield "{0}/{1}".format(host.lower(), path)


class URLDiscoverer(Plugin):
    """
    This plugin monitors incoming chat messages for common short URLs,
    handling their redirection, and then outputs resolved results to the chat.
    """

    _shorteners = [
        "bit.ly",
        "bitly.com",
        "cli.gs",
        "fb.me",
        "go.ign.com",
        "goo.gl",
        "is.gd",
        "kck.st",
        "ls.gd",
        "nblo.gs",
        "ow.ly",
        "short.to",
        "t.co",
        "tiny.cc",
        "tinyurl.com",
        "tr.im",
        "trib.al",
        "vk.cc",
        "whrt.it",
    ]

    _headers = {
        "User-Agent": "Googlebot/2.1 (+http://www.googlebot.com/bot.html)",
        "Accept-Language": "en-US,en;q=0.5",
    }
    _opener = urllib2.build_opener(urllib2.HTTPRedirectHandler)
    _opener.addheaders = [(k, v) for k, v in _headers.iteritems()]

    def on_message_status(self, message, status):
        if status != cmsReceived:
            return

        if not any(s in message.Body.lower() for s in self._shorteners):
            return

        found = list(find_shortened_urls(self._shorteners, message.Body))

        if not found:
            return

        resolved = []

        for url in found:
            try:
                self._logger.info(u"Resolving {0} for {1} ({2})".format(
                    url, message.FromDisplayName, message.FromHandle
                ))
                location = self._opener.open("http://{0}".format(url)).url
                resolved.append(u"{0} -> {1}".format(url, location))

            except (urllib2.HTTPError, urllib2.URLError) as e:
                m = u"Unable to resolve {0} for {1} ({2}): {3}".format(
                    url, message.FromDisplayName, message.FromHandle, str(e)
                )
                self._logger.error(m)
                resolved.append(u"{0} -> unable to resolve ({1})".format(
                    url, str(e)
                ))

        if not resolved:
            return

        message.Chat.SendMessage(u"[Redirect] {0}".format("\n".join(resolved)))


if __name__ == "__main__":
    import doctest
    doctest.testmod()
