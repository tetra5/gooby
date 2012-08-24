#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
@author: tetra5 <tetra5dotorg@gmail.com>
"""


__version__ = "2012.1"


import httplib
import urlparse
import re

from Skype4Py.enums import cmsReceived

from plugin import Plugin


class URLDiscoverer(Plugin):
    def __init__(self, parent):
        super(URLDiscoverer, self).__init__(parent)
        self._services = [
            "tinyurl.com",
            "bit.ly",
            "t.co",
            "ls.gd",
            "goo.gl",
            ]
        self._pattern = re.compile(r"(http://[^ ]+)", re.UNICODE)

    def on_message_status(self, message, status):
        chat = message.Chat

        if status != cmsReceived:
            return

        for service in self._services:
            if service in message.Body:
                match = re.match(self._pattern, message.Body)
                if not match:
                    return

                url = urlparse.urlparse(match.group(1))

                connection = httplib.HTTPConnection(url.netloc)
                connection.request("GET", url.path)
                response = connection.getresponse()
                location = response.getheader("Location")
                chat.SendMessage(u"%s -> %s" % (match.group(1), location))
                return
