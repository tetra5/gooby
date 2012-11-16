#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`urlunshortener` --- URL unshortener plugin
================================================
"""


import httplib
import urlparse
import re

from Skype4Py.enums import cmsReceived

from plugin import Plugin


class URLUnshortener(Plugin):
    def __init__(self, parent):
        super(URLUnshortener, self).__init__(parent)
        self._shorteners = [
            "http://tinyurl.com",
            "http://bit.ly",
            "http://t.co",
            "http://ls.gd",
            "http://goo.gl",
            "http://bitly.com",
            "http://ow.ly",
            ]
        self._pattern = re.compile(r"(http://[^ ]+)", re.UNICODE)

    def on_message_status(self, message, status):
        if status != cmsReceived:
            return

        chat = message.Chat

        source = None
        destination = message.Body
        while any(s in destination for s in self._shorteners):
            match = re.search(self._pattern, destination)
            if not match:
                return
            if not source:
                source = match.group(1)
            url = urlparse.urlparse(match.group(1))
            connection = httplib.HTTPConnection(url.netloc)
            connection.request("GET", url.path)
            response = connection.getresponse()
            destination = response.getheader("Location")

        if source:
            chat.SendMessage(u"{0} -> {1}".format(source, destination))
