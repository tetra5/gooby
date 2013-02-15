#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`urldiscoverer` --- URL unshortener plugin
===============================================
"""


__docformat__ = "restructuredtext en"


import httplib
import urlparse
import urllib2

from Skype4Py.enums import cmsReceived

from plugin import Plugin


def truncate_url(url, max_path_length=20):
    """
    Truncates URL path component to `max_path_length` characters.

    :param url: URL
    :type url: `unicode`

    :param max_path_length: maximum URL path length
    :type max_path_length: `int`

    :return: truncated URL
    :rtype: `unicode`

    :raise: ValueError if URL isn't a valid one.

    .. note::
        There's a limited Cyrillic URLs support (currently limited to URL
        path only). Skype won't recognize Cyrillic domain name parts anyway.

    ::

        >>> truncate_url("http://test.me/XXXXX", 3)
        'test.me/XXX...'
        >>> truncate_url("http://test.me/XXXXX")
        'test.me/XXXXX'
        >>> truncate_url("http://test.me/ссылка", 12)
        'test.me/%D1%81%D1%81...'
    """

    url = urlparse.urlparse(url)
    if not url.netloc:
        raise ValueError, "Invalid URL: {0}".format(url)
    try:
        quoted_path = urllib2.quote(url.path.encode("utf-8"))
    except UnicodeDecodeError:
        quoted_path = urllib2.quote(url.path)
    if len(quoted_path) < max_path_length:
        return url.netloc + quoted_path
    return url.netloc + quoted_path[:max_path_length + 1] + "..."


class URLDiscoverer(Plugin):
    """
    This plugin monitors incoming chat messages and recursively "unshortens"
    common URL shortener services. Long source URLs are being truncated to
    suppress potentially excessive output.
    """

    def __init__(self, parent):
        super(URLDiscoverer, self).__init__(parent)
        self._shorteners = [
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

    def on_message_status(self, message, status):
        if status != cmsReceived:
            return

        if not any(s in message.Body for s in self._shorteners):
            return

        chat = message.Chat

        output = []

        destinations = []
        for chunk in message.Body.split():
            if any(s in chunk.lower() for s in self._shorteners):
                destinations.append(chunk)

        for destination in destinations:
            valid = True
            source = None
            scheme = "http://"

            if destination.startswith("https://"):
                scheme = "https://"

            destination = destination.replace(scheme, "")

            destination = scheme + destination
            while any(scheme + s in destination for s in self._shorteners):
                if not source:
                    source = destination
                url = urlparse.urlparse(destination)
                connection = httplib.HTTPConnection(url.netloc, timeout=5)
                try:
                    path = url.path.encode("utf-8")
                except UnicodeError:
                    path = url.path
                connection.request("GET", urllib2.quote(path))
                response = connection.getresponse()
                destination = response.getheader("Location")
                if destination is None:
                    valid = False
                    msg = u"{0} -> unable to resolve".format(
                        truncate_url(source)
                    )
                    output.append(msg)
                    log_msg = u"Unable to resolve {0} for {1} ({2})".format(
                        source, message.FromHandle, message.FromDisplayName
                    )
                    self._logger.error(log_msg)
                    break

            if source and valid:
                output.append(u"{0} -> {1}".format(
                    truncate_url(source), destination
                ))
                self._logger.info("Resolving {0} for {1} ({2})".format(
                    truncate_url(source), message.FromDisplayName,
                    message.FromHandle
                ))

        if output:
            chat.SendMessage(", ".join(output))


if __name__ == "__main__":
    import doctest
    doctest.testmod()
