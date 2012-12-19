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
from errors import APIError


def get_video_id(url):
    """
    Parses video URL and returns its ID.

    :param url: YouTube video URL
    :type url: `unicode`

    :returns: YouTube video ID
    :rtype: `unicode` or `None`

    >>> get_video_id("https://www.youtube.com/watch?v=XXXXXXXXXXX")
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
    >>> get_video_id("http://youtu.be/XXXXXXXXXXX?t=0m00s")
    'XXXXXXXXXXX'
    >>> get_video_id("http://youtu.be///XXXXXXXXXXX///")
    'XXXXXXXXXXX'
    >>> get_video_id("http://www.youtube.com") is None
    True
    >>> get_video_id("youtube.com/watch?v=XXXXXXXXXXX&feature=youtu.be")
    'XXXXXXXXXXX'
    """

    if "youtube.com" in url:
        queries = urlparse.parse_qs(urlparse.urlparse(url).query)
        v = queries.get("v")
        try:
            vid_id = v[0].strip("/")
        except:
            return None
        if len(vid_id) != 11:
            return None
        return vid_id

    if "youtu.be" in url:
        vid_id = [chunk.strip() for chunk in url.split("/") if chunk][-1][:11]
        return vid_id if len(vid_id) == 11 else None


class YouTubeURLParser(Plugin):
    """This plugin monitors received messages and outputs video title if that
    message contains a valid YouTube video URL.
    """

    def __init__(self, parent):
        super(YouTubeURLParser, self).__init__(parent)
        self._pattern = re.compile(r"((?:youtube\.com|youtu\.be)/\S+)")

    def get_video_title(self, video_id):
        """Retrieves YouTube video title by its ID.

        :raise: :class:`errors.APIError` on connection or parse error

        :param video_id: YouTube video ID
        :type video_id: `unicode`
        """

        cached = self._cache.get(video_id)
        if cached:
            return cached

        api_url = "http://gdata.youtube.com/feeds/api/videos/"
        url = api_url + video_id

        headers = {
            "User-Agent": "Googlebot/2.1 (+http://www.googlebot.com/bot.html)",
            }
        opener = urllib2.build_opener()
        opener.addheaders = [(k, v) for k, v in headers.iteritems()]

        @retry_on_exception((urllib2.URLError, urllib2.HTTPError,
                             etree.ParseError))
        def retrieve_and_process_response():
            response = opener.open(fullurl=url, timeout=2)
            element_tree = etree.ElementTree()
            return element_tree.parse(response)

        root = retrieve_and_process_response()
        if root is None:
            raise APIError("Unable to retrieve video title.")

        video_title = root.find("{http://www.w3.org/2005/Atom}title").text

        self._cache.update({video_id: video_title})
        return video_title

    def on_message_status(self, message, status):
        if status != cmsReceived:
            return

        if not any(s in message.Body for s in ("youtu.be", "youtube.com")):
            return

        titles = []
        video_ids = []
        for url in re.findall(self._pattern, message.Body):
            video_id = get_video_id(url)
            if video_id:
                video_ids.append(video_id)
                try:
                    titles.append(self.get_video_title(video_id))
                except APIError, e:
                    message.Chat.SendMessage(e)
                    self._logger.error("{0} for {1}".format(e, video_id))
                    return

        if titles:
            message.Chat.SendMessage(u"[YouTube] %s" % ", ".join(titles))
            self._logger.info("Retrieving {0} for {1} ({2})".format(
                " ,".join(video_ids), message.FromDisplayName,
                message.FromHandle
            ))


if __name__ == "__main__":
    import doctest
    doctest.testmod()
