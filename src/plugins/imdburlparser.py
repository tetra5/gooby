#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`imdburlparser` --- IMDb URL parser plugin
===============================================

.. note::
    This module requires `lxml library <http://lxml.de/>'_
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

    _pattern = re.compile(
        r"""
        imdb\.com/title/
        (?P<id>
            tt\d{7,}
        )
        /?
        """,
        re.UNICODE | re.IGNORECASE | re.VERBOSE)

    _headers = {
        "User-Agent": "Googlebot/2.1 (+http://www.googlebot.com/bot.html)",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "Keep-Alive",
    }
    _opener = urllib2.build_opener()
    _opener.addheaders = [(k, v) for k, v in _headers.iteritems()]

    def get_movie_title(self, movie_id):
        """
        >>> plugin = IMDbURLParser()

        >>> assert "tt0101420" not in plugin.cache

        >>> plugin.get_movie_title("tt0101420")
        u'Begotten (1990)'

        >>> assert "tt0101420" in plugin.cache
        """

        @self.cache.get_cached(movie_id)
        def _do_get_movie_title():
            url = self._api_url.format(movie_id)

            @retry_on_exception((urllib2.URLError, urllib2.HTTPError), tries=2,
                                backoff=0, delay=1)
            def retrieve_html():
                response = self._opener.open(url)
                buf = response.read(4096)
                return lxml.html.fromstring(buf)

            html = retrieve_html()

            try:
                title = u"{0}".format(html.find(".//title").text[:-7])

            except AttributeError:
                return None

            else:
                return title

        return _do_get_movie_title()

    def on_message_status(self, message, status):
        if status != cmsReceived:
            return

        if "imdb.com/title/tt" not in message.Body:
            return

        found = re.findall(self._pattern, message.Body)
        if not found:
            return

        titles = []

        for movie_id in found:
            msg = "Retrieving {0} for {1}".format(movie_id, message.FromHandle)
            self._logger.info(msg)

            title = self.get_movie_title(movie_id)

            if title is not None:
                titles.append(title)
            else:
                msg = "Unable to retrieve movie title for {0}".format(movie_id)
                titles.append(msg)

                msg = "Unable to retrieve {0} for {1}".format(
                    movie_id, message.FromHandle
                )
                self._logger.error(msg)

        if not titles:
            return

        if len(titles) is 1:
            msg = u"[IMDb] {0}".format("".join(titles))
        else:
            msg = u"[IMDb]\n{0}".format("\n".join(titles))
        message.Chat.SendMessage(msg)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
