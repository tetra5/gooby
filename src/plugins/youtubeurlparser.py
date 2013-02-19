#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`youtubeurlparser` --- YouTube URL parser plugin
=====================================================

.. note::
    This module optionally uses `lxml library <http://lxml.de/>`_ if it's
    available, otherwise falls back to default (and much slower) xml.etree
    parser.
"""


__docformat__ = "restructuredtext en"


import re
import urllib2
import urlparse

try:
    from lxml import etree
except ImportError:
    try:
        from xml.etree import cElementTree as etree
    except ImportError:
        from xml.etree import ElementTree as etree

from Skype4Py.enums import cmsReceived

from plugin import Plugin
from utils import retry_on_exception


def get_video_id(url):
    """
    Parses video URL and returns its ID.

    :param url: YouTube video URL
    :type url: `unicode`

    :returns: YouTube video ID
    :rtype: `unicode` or `None`

    >>> get_video_id("https://www.youtube.com/watch?v=XXXXXXXXXXX")
    'XXXXXXXXXXX'
    >>> get_video_id("https://www.youtube.com/watch?v=XXXXXXXXXXXZ")
    'XXXXXXXXXXX'
    >>> get_video_id("https://www.youtube.com///watch?v=XXXXXXXXXXX///")
    'XXXXXXXXXXX'
    >>> get_video_id("youtube.com/watch?v=XXXXXXXXXXX")
    'XXXXXXXXXXX'
    >>> get_video_id("http://youtu.be/XXXXXXXXXXX")
    'XXXXXXXXXXX'
    >>> get_video_id("http://www.youtube.com/watch?feature=&v=XXXXXXXXXXX")
    'XXXXXXXXXXX'
    >>> get_video_id("http://youtu.be/YYYYYYYYYY") is None
    True
    >>> get_video_id("https://www.youtube.com/watch?v=") is None
    True
    >>> get_video_id("https://www.youtube.com/watch?v=X") is None
    True
    >>> get_video_id("http://youtu.be/XXXXXXXXXXX?t=0m00s")
    'XXXXXXXXXXX'
    >>> get_video_id("http://youtu.be///X///") is None
    True
    >>> get_video_id("http://youtu.be///XXXXXXXXXXX///")
    'XXXXXXXXXXX'
    >>> get_video_id("http://youtu.be///XXXXXXXXXXXZ///")
    'XXXXXXXXXXX'
    >>> get_video_id("http://www.youtube.com") is None
    True
    >>> get_video_id("youtube.com/watch?v=XXXXXXXXXXX&feature=youtu.be")
    'XXXXXXXXXXX'
    >>> get_video_id("youtube.com/watch?feature=youtu.be&v=XXXXXXXXXXX")
    'XXXXXXXXXXX'
    """

    vid_id = ""

    if "youtube.com" in url:
        queries = urlparse.parse_qs(urlparse.urlparse(url).query)
        v = queries.get("v")
        try:
            vid_id = v[0].strip("/")[:11]
        except (IndexError, TypeError):
            return

    elif "youtu.be" in url:
        vid_id = [chunk.strip() for chunk in url.split("/") if chunk][-1][:11]

    return vid_id if len(vid_id) is 11 else None


class YouTubeURLParser(Plugin):
    """This plugin monitors received messages and outputs video title if that
    message contains a valid YouTube video URL.
    """

    _api_url = "http://gdata.youtube.com/feeds/api/videos/{0}"

    _pattern = re.compile(ur"((?:youtube\.com|youtu\.be)/\S+)")

    _headers = {
        "User-Agent": "Googlebot/2.1 (+http://www.googlebot.com/bot.html)",
        "Accept-Language": "en-US,en;q=0.5",
    }
    _opener = urllib2.build_opener()
    _opener.addheaders = [(k, v) for k, v in _headers.iteritems()]

    def get_video_title(self, video_id):
        """Retrieves YouTube video title by its ID.

        :param video_id: YouTube video ID
        :type video_id: `unicode` or None
        """

        cached = self._cache.get(video_id)
        if cached:
            return cached

        url = self._api_url.format(video_id)

        @retry_on_exception((urllib2.URLError, urllib2.HTTPError), tries=2,
                            backoff=0, delay=1)
        def retrieve_xml():
            response = self._opener.open(url)
            buf = response.read()
            return etree.fromstring(buf)

        xml = retrieve_xml()

        try:
            title = xml.find("{http://www.w3.org/2005/Atom}title").text
            self._cache.update({video_id: title})
        except (AttributeError, etree.ParseError):
            return

        return title

    def on_message_status(self, message, status):
        if status != cmsReceived:
            return

        if not any(s in message.Body for s in ("youtu.be", "youtube.com")):
            return

        found = re.findall(self._pattern, message.Body)
        if not found:
            return

        titles = []

        for url in found:
            video_id = get_video_id(url)

            if video_id is None:
                continue

            self._logger.info("Retrieving {0} for {1} ({2})".format(
                video_id, message.FromDisplayName, message.FromHandle
            ))

            title = self.get_video_title(video_id)

            if title is not None:
                titles.append(title)
            else:
                msg = "Unable to retrieve video title for {0}".format(video_id)
                titles.append(msg)

                msg = "Unable to retrieve {0} for {1} ({2})".format(
                    video_id, message.FromDisplayName, message.FromHandle
                )
                self._logger.error(msg)

        if not titles:
            return

        message.Chat.SendMessage(u"[YouTube] {0}".format(", ".join(titles)))


if __name__ == "__main__":
    import doctest
    doctest.testmod()
