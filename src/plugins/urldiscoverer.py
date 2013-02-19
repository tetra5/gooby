#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`urldiscoverer` --- URL unshortener plugin
===============================================
"""


__docformat__ = "restructuredtext en"


import urllib2

from Skype4Py.enums import cmsReceived

from plugin import Plugin


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

    _opener = urllib2.build_opener(urllib2.HTTPRedirectHandler)

    def on_message_status(self, message, status):
        if status != cmsReceived:
            return

        if not any(s in message.Body.lower() for s in self._shorteners):
            return

        # Build a list of clean URLs for every non-overlapping shortened URL
        # found in a message.
        # Domain part search is case-insensitive, whereas extra slashes are
        # being stripped. The resulting URL consists of URL scheme, domain
        # and path parts, i.e. "http://domain.com/SH0Rt".
        urls = []
        for s in self._shorteners:
            f = map(lambda x: filter(None, x[x.lower().find(s):].split("/")),
                    message.Body.split())
            for pair in filter(lambda x: len(x) is 2, f):
                urls.append("http://{0}".format("/".join(pair)))

        resolved = []

        for url in urls:
            u = url.split("http://")[-1]
            try:
                self._logger.info(u"Resolving {0} for {1} ({2})".format(
                    u, message.FromDisplayName, message.FromHandle
                ))
                destination = self._opener.open(url).url
                resolved.append(u"{0} -> {1}".format(
                    u, destination
                ))
            except (urllib2.HTTPError, urllib2.URLError) as e:
                m = u"Unable to resolve {0} for {1} ({2}): {3}".format(
                    u, message.FromDisplayName, message.FromHandle, str(e)
                )
                self._logger.error(m)
                resolved.append(u"{0} -> unable to resolve ({1})".format(
                    u, str(e)
                ))

        if resolved:
            message.Chat.SendMessage(", ".join(resolved))


if __name__ == "__main__":
    import doctest
    doctest.testmod()
