#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
:mod:`couburlparser` --- COUB URL parser plugin
=================================================

.. note::
    This module requires `lxml library <http://lxml.de/>'_
"""
from __future__ import unicode_literals
__docformat__ = "restructuredtext en"

import urllib2
import re

from lxml import etree
from lxml.etree import XMLSyntaxError

from Skype4Py.enums import cmsReceived, cmsSent

from plugin import Plugin
from utils import retry_on_exception
from output import ChatMessage

class CoubURLParser(Plugin):
    """
    This plugin monitors received messages and outputs video titles(s) if that
    message contains a valid Coub video URL(s).
    http://coub.com/api/oembed.xml?url=http://coub.com/view/51cf5
    """
    _api_url = "http://coub.com/api/oembed.xml?url=http://{0}"
    _pattern = re.compile(ur"(coub\.com/\S+)", re.IGNORECASE)
    _headers = {
        "User-Agent": "Googlebot/2.1 (+http://www.googlebot.com/bot.html)",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "Keep-Alive",
    }
    _opener = urllib2.build_opener()
    _opener.addheaders = [(k, v) for k, v in _headers.iteritems()]

    def get_video_title(self, video_id):
        """
        Retrieves Coub video title by its url.
        >>> plugin = CoubURLParser()
        >>> plugin.get_video_title(http://coub.com/view/51cf5)
        u'METACHAOS'
        """
        cached_title = self._cache.get(video_id)
        if cached_title is not None:
            return cached_title

        url = self._api_url.format(video_id)

        @retry_on_exception((urllib2.URLError, urllib2.HTTPError), tries=2,
                            backoff=0, delay=2)
        def retrieve_xml():
            response = self._opener.open(url)
            buf = response.read()
            try:
                return etree.fromstring(buf)
            except XMLSyntaxError:
                return

        xml = retrieve_xml()

        try:
            title = xml.find("title").text

        except AttributeError:
            return None

        else:
            title = unicode(title)
            self._cache.set(video_id, title)
            return title

    def on_message_status(self, message, status):
        if status not in (cmsReceived, cmsSent):
            return

        if "coub.com/" not in message.Body:
            return

        found = re.findall(self._pattern, message.Body.strip())
        if not found:
            return

        titles = []

        for url in found:
            video_id = url

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
            msg = u"[Coub] {0}".format("".join(titles))
        else:
            msg = u"[Coub]\n{0}".format("\n".join(titles))
        #message.Chat.SendMessage(msg)
        self.output.append(ChatMessage(message.Chat.Name, msg))
        return message, status


if __name__ == "__main__":
    import doctest
    doctest.testmod()