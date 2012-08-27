#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
@author: tetra5 <tetra5dotorg@gmail.com>
"""


__version__ = "2012.1"


import re
import time
import urllib2

try:
    from lxml import etree
except ImportError:
    try:
        from xml.etree import cElementTree as etree
    except ImportError:
        from xml.etree import ElementTree as etree

from Skype4Py.enums import cmsReceived

from plugin import Plugin


_cache = {}


# TODO: probaadd video author to output.

def retry(exception, tries=10, delay=3, backoff=1):
    """Retries a function or method until it stops generating specified
    exception.

    @param exception: Exception generated by decorated function or method.
    @param tries: Number of tries.
    @param delay: Delay between tries in seconds.
    @param backoff: Factor by which the delay should lengthen after each
    failure.
    """
    def wrapper(f):
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 0:
                try:
                    return f(*args, **kwargs)
                except exception:
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return
        return f_retry
    return wrapper


class YoutubeURLParser(Plugin):
    def __init__(self, parent):
        super(YoutubeURLParser, self).__init__(parent)
        p = (r"http(?:s?)://(?:www\.)?youtu(?:be\.com/watch\?v=|\.be/)"
             "([\w\-]+)(&(amp;)?[\w\?=]*)?")
        self._pattern = re.compile(p, re.UNICODE)

    def on_message_status(self, message, status):
        global _cache

        chat = message.Chat

        if status != cmsReceived:
            return

        match = re.search(self._pattern, message.Body)
        if not match:
            return

        video_id = match.group(1)

        if video_id not in _cache:
            api_url = "http://gdata.youtube.com/feeds/api/videos/"
            url = api_url + video_id

            headers = {
                "User-Agent":
                    "Googlebot/2.1 (+http://www.googlebot.com/bot.html)",
                }
            opener = urllib2.build_opener()
            opener.addheaders = [(k, v) for k, v in headers.iteritems()]

            @retry((urllib2.URLError, urllib2.HTTPError, etree.ParseError))
            def retrieve_and_process_response():
                response = opener.open(fullurl=url, timeout=2)
                element_tree = etree.ElementTree()
                return element_tree.parse(response)

            root = retrieve_and_process_response()
            if root is None:
                chat.SendMessage(u"Unable to retrieve video information")
                return

            video_title = root.find("{http://www.w3.org/2005/Atom}title").text
            _cache.update({video_id: video_title})

        video_title = _cache.get(video_id)
        chat.SendMessage(u"[YouTube] %s" % video_title)
