#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`urldiscoverer` --- URL unshortener plugin
===============================================
"""


import httplib
import urlparse

from Skype4Py.enums import cmsReceived

from plugin import Plugin


def truncate_url(url, start=7, length=20):
    url = url[start:]
    return url if len(url) <= length else url[:length] + "..."


class URLDiscoverer(Plugin):
    def __init__(self, parent):
        super(URLDiscoverer, self).__init__(parent)
        self._shorteners = [
            "tinyurl.com",
            "bit.ly",
            "t.co",
            "ls.gd",
            "goo.gl",
            "bitly.com",
            "ow.ly",
            "fb.me",
            "is.gd",
            "tr.im",
            "cli.gs",
            "tiny.cc",
            "short.to",
            "trib.al",
            "nblo.gs",
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
            if not destination.startswith("http://"):
                destination = "http://" + destination
            while any("http://" + s in destination for s in self._shorteners):
                if not source:
                    source = destination
                url = urlparse.urlparse(destination)
                connection = httplib.HTTPConnection(url.netloc, timeout=5)
                connection.request("GET", url.path)
                response = connection.getresponse()
                destination = response.getheader("Location")
                if destination is None:
                    valid = False
                    msg = u"{0} -> unable to resolve".format(
                        truncate_url(source)
                    )
                    output.append(msg)
                    log_msg = u"Unable to resolve {0}".format(source)
                    self._logger.error(log_msg)
                    break
            if source and valid:
                output.append(u"{0} -> {1}".format(
                    truncate_url(source), destination
                ))

        if output:
            chat.SendMessage(", ".join(output))
