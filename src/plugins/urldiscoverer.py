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


def find_shortened_urls(shorteners=[], haystack=""):
    """
    Generator.
    Yields every valid shortened URL found in haystack string. Does not append
    "http://" part to result. Strips all non-letters from URL path.

    >>> shorteners = ["t.co", "tinyurl.com", "bit.ly", "goo.gl"]
    >>> haystack = '''t.co/derp,     BiT.Ly/HerP http://tinyURL.com/TEST
    ... www.goo.gl/herpDERP/derpwww.bit.ly/herpderp'''
    >>> found = list(find_shortened_urls(shorteners, haystack))
    >>> expected = ['bit.ly/herpderp', 't.co/derp', 'BiT.Ly/HerP',
    ... 'tinyURL.com/TEST']
    >>> sorted(found) == sorted(expected)
    True
    """

    for s in shorteners:
        f = map(lambda x: filter(None, x[x.lower().find(s):].split("/")),
                haystack.split())
        for host, path in filter(lambda x: len(x) is 2, f):
            yield "{0}/{1}".format(host, re.sub(_p, "_", path).strip("_"))


class URLDiscoverer(Plugin):
    """
    This plugin monitors incoming chat messages and recursively "unshortens"
    common URL shortener services. Long source URLs are being truncated to
    suppress potentially excessive output.
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
