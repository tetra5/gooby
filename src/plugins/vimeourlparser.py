#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`vimeourlparser` --- Vimeo URL parser plugin
=================================================

.. note::
    This module requires `lxml library <http://lxml.de/>'_
"""


__docformat__ = "restructuredtext en"


import urllib2
import re

from lxml import etree
from lxml.etree import XMLSyntaxError
from Skype4Py.enums import cmsReceived

from plugin import Plugin
from utils import retry_on_exception


def get_video_id(url):
    """
    Parse Vimeo video URL and return its ID.

    >>> assert get_video_id("http://vimeo.com/123") is 123

    >>> assert get_video_id("http://www.vimeo.com/123") is 123

    >>> assert get_video_id("vimeo.com/123/") is 123
    """

    retval = None
    match = re.search(ur"vimeo\.com/(\d+)", url, re.IGNORECASE)
    if match:
        retval = int(match.group(1))
    return retval


class VimeoURLParser(Plugin):
    """
    This plugin monitors received messages and outputs video titles(s) if that
    message contains a valid Vimeo video URL(s).
    """

    _api_url = "http://vimeo.com/api/v2/video/{0}.xml"

    _pattern = re.compile(ur"(vimeo\.com/\d+)", re.IGNORECASE)

    _headers = {
        "User-Agent": "Googlebot/2.1 (+http://www.googlebot.com/bot.html)",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "Keep-Alive",
    }
    _opener = urllib2.build_opener()
    _opener.addheaders = [(k, v) for k, v in _headers.iteritems()]

    def get_video_title(self, video_id):
        """
        Retrieves Vimeo video title by its ID.

        >>> plugin = VimeoURLParser()
        >>> plugin.get_video_title(16056709)
        u'METACHAOS'
        """

        cached_title = self._cache.get(video_id)
        if cached_title is not None:
            return cached_title

        url = self._api_url.format(video_id)

        @retry_on_exception((urllib2.URLError, urllib2.HTTPError), tries=2,
                            backoff=0, delay=1)
        def retrieve_xml():
            response = self._opener.open(url)
            buf = response.read()
            try:
                return etree.fromstring(buf)
            except XMLSyntaxError:
                return

        xml = retrieve_xml()

        try:
            title = xml.find("video/title").text

        except AttributeError:
            return None

        else:
            title = unicode(title)
            self._cache.set(video_id, title)
            return title

    def on_message_status(self, message, status):
        if status != cmsReceived:
            return

        if "vimeo.com/" not in message.Body:
            return

        found = re.findall(self._pattern, message.Body.strip())
        if not found:
            return

        titles = []

        for url in found:
            video_id = get_video_id(url)

            if video_id is None:
                continue

            self._logger.info("Retrieving {0} for {1}".format(
                video_id, message.FromHandle
            ))

            title = self.get_video_title(video_id)

            if title is not None:
                titles.append(title)
            else:
                msg = "Unable to retrieve video title for {0}".format(video_id)
                titles.append(msg)

                msg = "Unable to retrieve {0} for {1}".format(
                    video_id, message.FromHandle
                )
                self._logger.error(msg)

        if not titles:
            return

        if len(titles) is 1:
            msg = u"[Vimeo] {0}".format("".join(titles))
        else:
            msg = u"[Vimeo]\n{0}".format("\n".join(titles))
        message.Chat.SendMessage(msg)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
