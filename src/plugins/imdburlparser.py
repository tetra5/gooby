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

    _api_url = "http://www.imdb.com/title/{0}"
    _pattern = re.compile(ur"imdb\.com/title/(tt\d{7,})", re.IGNORECASE)

    def on_message_status(self, message, status):
        if status != cmsReceived:
            return

        if "imdb.com/title/tt" not in message.Body:
            return

        found = re.findall(self._pattern, message.Body)
        if not found:
            return

        headers = {
            "User-Agent": "Googlebot/2.1 (+http://www.googlebot.com/bot.html)",
            "Accept-Language": "en-US,en;q=0.5",
        }
        opener = urllib2.build_opener()
        opener.addheaders = [(k, v) for k, v in headers.iteritems()]

        titles = []

        for movie_id in found:
            url = self._api_url.format(movie_id)

            @retry_on_exception((urllib2.URLError, urllib2.HTTPError), tries=2,
                                backoff=0, delay=1)
            def retrieve_html():
                response = opener.open(url)
                buf = response.read(1024)
                return lxml.html.fromstring(buf)

            html = retrieve_html()

            try:
                titles.append(html.find("head/title").text[:-7])

                self._logger.info("Retrieving {0} for {1} ({2})".format(
                    movie_id, message.FromDisplayName, message.FromHandle
                ))
            except AttributeError:
                titles.append("Unable to retrieve movie title for {0}".format(
                    movie_id
                ))

                msg = "Unable to retrieve {0} for {1} ({2})".format(
                    movie_id, message.FromDisplayName, message.FromHandle
                )
                self._logger.error(msg)

        message.Chat.SendMessage(u"[IMDb] {0}".format(", ".join(titles)))


if __name__ == "__main__":
    import doctest
    doctest.testmod()
