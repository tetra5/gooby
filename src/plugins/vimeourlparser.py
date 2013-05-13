#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`vimeourlparser` --- Vimeo URL parser plugin
=================================================
"""


__docformat__ = "restructuredtext en"


import urllib2
import re

from lxml import etree
from lxml.etree import XMLSyntaxError
from Skype4Py.enums import cmsReceived

from plugin import Plugin
from utils import retry_on_exception


class VimeoURLParser(Plugin):
    """
    This plugin monitors received messages and outputs video titles(s) if that
    message contains a valid Vimeo video URL(s).
    """

    _api_url = "http://vimeo.com/api/v2/video/{0}.xml"

    _pattern = re.compile(ur"vimeo\.com/(\d+)", re.IGNORECASE)

    _headers = {
        "User-Agent": "Googlebot/2.1 (+http://www.googlebot.com/bot.html)",
        "Accept-Language": "en-US,en;q=0.5",
    }
    _opener = urllib2.build_opener()
    _opener.addheaders = [(k, v) for k, v in _headers.iteritems()]

    def on_message_status(self, message, status):
        if status != cmsReceived:
            return

        if "vimeo.com/" not in message.Body:
            return

        found = re.findall(self._pattern, message.Body)
        if not found:
            return

        titles = []

        for video_id in found:
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
                titles.append(xml.find("video/title").text)

                self._logger.info("Retrieving {0} for {1}".format(
                    video_id, message.FromHandle
                ))
            except AttributeError:
                titles.append("Unable to retrieve video title for {0}".format(
                    video_id
                ))

                msg = "Unable to retrieve {0} for {1} ({2})".format(
                    video_id, message.FromDisplayName, message.FromHandle
                )
                self._logger.error(msg)

        message.Chat.SendMessage(u"[Vimeo] {0}".format(", ".join(titles)))


if __name__ == "__main__":
    import doctest
    doctest.testmod()
