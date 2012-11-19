#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`urldiscoverer` --- URL unshortener plugin
===============================================
"""


import httplib
import urlparse
import re

from Skype4Py.enums import cmsReceived

from plugin import Plugin


def truncate_url(url, start=7, length=20):
    url = url[start:]
    return url if len(url) <= length else url[:length] + "..."


class URLDiscoverer(Plugin):
    def __init__(self, parent):
        super(URLDiscoverer, self).__init__(parent)
        self._shorteners = [
            "http://tinyurl.com",
            "http://bit.ly",
            "http://t.co",
            "http://ls.gd",
            "http://goo.gl",
            "http://bitly.com",
            "http://ow.ly",
            "http://fb.me",
            "http://is.gd",
            "http://tr.im",
            "http://cli.gs",
            "http://tiny.cc",
            "http://short.to",
            ]
        self._pattern = re.compile(r"(http://[^ ]+)", re.UNICODE)

    def on_message_status(self, message, status):
        if status != cmsReceived:
            return

        chat = message.Chat

        output = []
        for destination in re.findall(self._pattern, message.Body):
            source = None
            valid = True
            while any(s in destination for s in self._shorteners):
                match = re.search(self._pattern, destination)
                if not match:
                    break
                if not source:
                    source = match.group(1)
                url = urlparse.urlparse(source)
                connection = httplib.HTTPConnection(url.netloc)
                connection.request("GET", url.path)
                response = connection.getresponse()
                destination = response.getheader("Location")
                if destination is None:
                    msg = u"{0} -> unable to resolve".format(
                        truncate_url(source)
                    )
                    valid = False
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
