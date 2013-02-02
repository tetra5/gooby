#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`imdburlparser` --- IMDb URL parser plugin
===============================================
"""


__docformat__ = "restructuredtext en"


import urllib2
import re

import lxml.html

from Skype4Py.enums import cmsReceived

from plugin import Plugin


class IMDbURLParser(Plugin):
    """
    This plugin monitors received messages and outputs movie title(s) if that
    message contains a valid IMDb movie URL(s).
    """

    def on_message_status(self, message, status):
        if status != cmsReceived:
            return

        if "imdb.com/title/tt" not in message.Body:
            return

        p = ur"(imdb\.com/title/tt\d{7,})"
        pattern = re.compile(p, re.IGNORECASE)

        found = re.findall(pattern, message.Body)
        if not found:
            return

        headers = {
            "User-Agent": "Googlebot/2.1 (+http://www.googlebot.com/bot.html)",
        }
        opener = urllib2.build_opener()
        opener.addheaders = [(k, v) for k, v in headers.iteritems()]

        titles = []

        for url in found:
            url = "http://www.{0}/".format(url.rstrip("/"))

            response = opener.open(url)
            buf = response.read(1024)
            opener.close()

            html = lxml.html.fromstring(buf)
            titles.append(html.find("head/title").text[:-7])

        message.Chat.SendMessage(u"[IMDb] {0}".format(", ".join(titles)))


if __name__ == "__main__":
    import doctest
    doctest.testmod()
