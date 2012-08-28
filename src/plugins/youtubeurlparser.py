#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
@author: tetra5 <tetra5dotorg@gmail.com>
"""


__version__ = "2012.2"


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


_cache = {}


class APIError(Exception):
    pass


def get_video_id(url):
    """Parses specified URL string and returns either YouTube video ID or None.

    @param url: YouTube URL, examples:
    https://www.youtube.com/watch?v=XXXXXXXXXXX
    http://youtu.be/XXXXXXXXXXX

    >>> get_video_id("https://www.youtube.com/watch?v=XXXXXXXXXXX")
    'XXXXXXXXXXX'
    >>> get_video_id("http://youtu.be/XXXXXXXXXXX")
    'XXXXXXXXXXX'
    >>> get_video_id("http://www.youtube.com/watch?feature=&v=XXXXXXXXXXX")
    'XXXXXXXXXXX'
    >>> get_video_id("http://youtu.be/YYYYYYYYYY") is None
    True
    >>> get_video_id("https://www.youtube.com/watch?v=") is None
    True
    """
    if "youtu.be" in url:
        video_id = [chunk for chunk in url.split("/") if chunk][-1]
        return video_id if len(video_id) == 11 else None

    if "youtube.com" in url:
        queries = urlparse.parse_qs(urlparse.urlparse(url).query)
        v = queries.get("v")
        try:
            video_id = v[0]
        except:
            return None
        if len(video_id) != 11:
            return None
        return video_id


def get_video_title(video_id):
    """Retrieves YouTube video title by its ID.

    Raises APIError on connection or parse error.

    @param video_id: YouTube video ID.
    """
    global _cache

    cached = _cache.get(video_id)
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

    _cache.update({video_id: video_title})
    return video_title


class YouTubeURLParser(Plugin):
    """This plugin monitors received messages and outputs video title if a
    message contains YouTube video URL.
    """
    def __init__(self, parent):
        super(YouTubeURLParser, self).__init__(parent)
        self._pattern = re.compile(r"(https?://\S+)")

    def on_message_status(self, message, status):
        if status == cmsReceived:
            if "youtu.be" in message.Body or "youtube.com" in message.Body:

                global _cache

                chat = message.Chat

                video_ids = []
                for url in re.findall(self._pattern, message.Body):
                    video_id = get_video_id(url)
                    if video_id:
                        video_ids.append(video_id)

                video_titles = []
                try:
                    for video_id in video_ids:
                        video_titles.append(get_video_title(video_id))
                except APIError, e:
                    chat.SendMessage(e)
                    return

                output = ", ".join(video_titles)

                chat.SendMessage(u"[YouTube] %s" % output)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
