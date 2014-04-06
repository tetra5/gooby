#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`duplicateurlchecker` - Duplicate URL Checker
==================================================
"""


from __future__ import unicode_literals


__docformat__ = "restructuredtext en"


import re
from datetime import datetime
from time import time

from Skype4Py.enums import cmsReceived

from plugin import Plugin
from output import ChatMessage
from plugins.youtubeurlparser import get_video_id


def find_urls(s):
    """
    >>> s = '''http://test.com www.test.co.uk http://www.herpderp.org
    ... bit.ly/derp https://derp.com/a?derp=herp#anchor just.testing/derpface'''
    >>> expected = (["http://test.com", "www.test.co.uk", "bit.ly/derp",
    ... "http://www.herpderp.org", "https://derp.com/a?derp=herp#anchor"])
    >>> found = find_urls(s)
    >>> assert sorted(found) == sorted(expected)
    """

    # http://daringfireball.net/2010/07/improved_regex_for_matching_urls
    pattern = re.compile(
        r"""
        (?P<url>
            (?P<protocol_or_www>
                https?://
                |
                www\d{0,3}[.]
                |
                [a-z0-9.\-]+[.][a-z]{2,4}/
            )
            (?P<path_parts>
                [^\s()<>]+
                |
                \(([^\s()<>]+|(\([^\s()<>]+\)))*\)
            )+
            (?P<ending>
                \(([^\s()<>]+|(\([^\s()<>]+\)))*\)
                |
                [^\s`!()\[\]{};:'".,<>?«»“”‘’]
            )
        )
        """,
        re.UNICODE | re.IGNORECASE | re.VERBOSE)

    retval = []
    for found in re.findall(pattern, s):
        retval.append(found[0])
    return retval


def chop(s, max_len, ending=""):
    """
    >>> assert chop("http://www.derp.com", 15, "!") == "http://www.derp!"
    >>> assert chop("test", 10, "...") == "test"
    """

    return s if len(s) <= max_len else "{0}{1}".format(s[:max_len], ending)


class DuplicateURLChecker(Plugin):
    def on_message_status(self, message, status):
        if status != cmsReceived:
            return

        if "gooby" in message.Body.lower():
            return

        found = find_urls(message.Body)

        if not found:
            return

        output = []

        for url in found:
            if any(s in url for s in ("youtu.be", "youtube.com")):
                video_id = get_video_id(url)
                if video_id is not None:
                    url = "https://www.youtube.com/watch?v={0}".format(video_id)

            if url not in self.cache:
                self.cache[url] = (message.FromHandle,
                                   message.FromDisplayName,
                                   time())
            else:
                try:
                    posted_by, full_name, ts = self.cache[url]
                except (KeyError, ValueError):
                    pass
                else:
                    if posted_by == message.FromHandle:
                        return

                    if full_name in message.Body:
                        return

                    if posted_by in message.Body:
                        return

                    m = "{0} has been originally posted by {1} on {2}".format(
                        chop(url, max_len=15, ending="..."),
                        full_name,
                        datetime.fromtimestamp(ts).strftime("%d.%m.%Y at %X"))
                    output.append(m)

                    m = "URL dupe by {0}, originally posted by {1}".format(
                        message.FromHandle, posted_by)
                    self._logger.info(m)

        if not output:
            return

        if len(output) is 1:
            msg = u"[Duplicate URL] {0}".format("".join(output))
        else:
            msg = u"[Duplicate URL]\n{0}".format("\n".join(output))
        self.output.append(ChatMessage(message.Chat.Name, msg))
        #message.Chat.SendMessage(msg)
        return message, status


if __name__ == "__main__":
    import doctest
    doctest.testmod()
