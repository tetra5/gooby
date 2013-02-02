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
from utils import retry_on_exception


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
            "Accept-Language": "en-US,en;q=0.5",
        }
        opener = urllib2.build_opener()
        opener.addheaders = [(k, v) for k, v in headers.iteritems()]

        titles = []

        for url in found:
            url = "http://www.{0}/".format(url.rstrip("/"))

            @retry_on_exception((urllib2.URLError, urllib2.HTTPError))
            def retrieve_html():
                response = opener.open(url)
                buf = response.read(1024)
                opener.close()
                try:
                    return lxml.html.fromstring(buf)
                except:
                    return

            html = retrieve_html()

            if html is None:
                titles.append("Unable to retrieve movie title for {0}".format(
                    url
                ))
            else:
                titles.append(html.find("head/title").text[:-7])

        ids = [url.split("/")[-1] for url in found]
        self._logger.info("Retrieving {0} for {1} ({2})".format(
            ", ".join(ids), message.FromDisplayName, message.FromHandle
        ))
        message.Chat.SendMessage(u"[IMDb] {0}".format(", ".join(titles)))


if __name__ == "__main__":
    import doctest
    doctest.testmod()
