#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`youtubeurlparser` --- YouTube URL parser plugin
=====================================================
"""


from __future__ import unicode_literals


__docformat__ = "restructuredtext en"


import re
import urllib2
import urllib
import urlparse
import json

from Skype4Py.enums import cmsReceived, cmsSent

from plugin import Plugin
from output import ChatMessage
import config


def get_video_id(url):
    """
    Parses video URL and returns its ID.

    :param url: YouTube video URL
    :type url: `str`

    :returns: YouTube video ID
    :rtype: `unicode` or `None`

    >>> get_video_id("https://www.youtube.com/watch?v=XXXXXXXXXXX")
    u'XXXXXXXXXXX'
    >>> get_video_id("https://www.youtube.com/watch?v=XXXXXXXXXXXZ")
    u'XXXXXXXXXXX'
    >>> get_video_id("https://www.youtube.com///watch?v=XXXXXXXXXXX///")
    u'XXXXXXXXXXX'
    >>> get_video_id("youtube.com/watch?v=XXXXXXXXXXX")
    u'XXXXXXXXXXX'
    >>> get_video_id("http://youtu.be/XXXXXXXXXXX")
    u'XXXXXXXXXXX'
    >>> get_video_id("http://www.youtube.com/watch?feature=&v=XXXXXXXXXXX")
    u'XXXXXXXXXXX'
    >>> get_video_id("http://youtu.be/YYYYYYYYYY") is None
    True
    >>> get_video_id("https://www.youtube.com/watch?v=") is None
    True
    >>> get_video_id("https://www.youtube.com/watch?v=X") is None
    True
    >>> get_video_id("http://youtu.be/XXXXXXXXXXX?t=0m00s")
    u'XXXXXXXXXXX'
    >>> get_video_id("http://youtu.be///X///") is None
    True
    >>> get_video_id("http://youtu.be///XXXXXXXXXXX///")
    u'XXXXXXXXXXX'
    >>> get_video_id("http://youtu.be///XXXXXXXXXXXZ///")
    u'XXXXXXXXXXX'
    >>> get_video_id("http://www.youtube.com") is None
    True
    >>> get_video_id("youtube.com/watch?v=XXXXXXXXXXX&feature=youtu.be")
    u'XXXXXXXXXXX'
    >>> get_video_id("youtube.com/watch?feature=youtu.be&v=XXXXXXXXXXX")
    u'XXXXXXXXXXX'
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


def get_duration(youtube_duration):
    """
    >>> get_duration('PT15M51S')
    951

    >>> get_duration('PT1H11M10S')
    4270

    :param unicode youtube_duration: YouTube weirdly formatted duration
    :return int: duration in seconds for the human beings!
    """

    youtube_duration = youtube_duration.lower()

    duration = 0

    pattern = re.compile(r'([0-9]+)([hms])', re.I | re.U)

    matches = re.finditer(pattern, youtube_duration)
    if not matches:
        return duration

    for match in matches:
        value, letter = match.groups()
        value = int(value)
        if letter == 'h':
            duration += value * 3600
        elif letter == 'm':
            duration += value * 60
        elif letter == 's':
            duration += value
        else:
            raise Exception("Unsupported letter: %s" % letter)

    return duration


class YouTubeURLParser(Plugin):
    """This plugin monitors received messages and outputs video title and its
    duration if that message contains a valid YouTube video URL.
    """

    _url_args = {
        'part': 'snippet,contentDetails',
        'fields': 'items(snippet(title),contentDetails(duration))',
        'key': config.GOOGLE_API_KEY,
    }

    _api_base_url = 'https://www.googleapis.com/youtube/v3/videos'

    _pattern = re.compile(ur"((?:youtube\.com|youtu\.be)/\S+)")

    _headers = {
        "User-Agent": "Gooby",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "Keep-Alive",
    }
    _opener = urllib2.build_opener()
    _opener.addheaders = [(k, v) for k, v in _headers.iteritems()]

    def get_video_title(self, video_id):
        """Retrieves YouTube video title by its ID.

        :param video_id: YouTube video ID
        :type video_id: `str` or None

        >>> plugin = YouTubeURLParser()
        >>> plugin.get_video_title("dQw4w9WgXcQ")
        u'Rick Astley - Never Gonna Give You Up [00:03:33]'
        """

        cached_title = self._cache.get(video_id)
        if cached_title is not None:
            return cached_title

        args = self._url_args.copy()
        args.update({'id': video_id})
        url = ''.join((self._api_base_url, '?', urllib.urlencode(args)))

        try:
            data = json.loads(self._opener.open(url).read())
        except urllib2.HTTPError:
            raise Exception("Check your Google API key")

        try:
            title = data['items'][0]['snippet']['title']
        except (IndexError, AttributeError):
            title = None

        try:
            duration = data['items'][0]['contentDetails']['duration']
        except (IndexError, AttributeError):
            duration = None

        if None in (title, duration):
            raise Exception("Unable to retrieve video title parts")

        duration = get_duration(duration)

        minutes, seconds = divmod(int(duration), 60)
        hours, minutes = divmod(minutes, 60)
        duration = "{0:02d}:{1:02d}:{2:02d}".format(hours, minutes, seconds)

        title = u"{0} [{1}]".format(title, duration)

        self._cache.set(video_id, title)
        return title

    def on_message_status(self, message, status):
        if status not in (cmsReceived, cmsSent):
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
            msg = u"[YouTube] {0}".format("".join(titles))
        else:
            msg = u"[YouTube]\n{0}".format("\n".join(titles))
        #message.Chat.SendMessage(msg)
        self.output.append(ChatMessage(message.Chat.Name, msg))

        return message, status


if __name__ == "__main__":
    import doctest
    doctest.testmod()
