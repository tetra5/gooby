#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`duplicateurlchecker` - Duplicate URL Checker
==================================================
"""


__docformat__ = "restructuredtext en"


import re
from datetime import datetime
from time import time

from Skype4Py.enums import cmsReceived

from plugin import Plugin


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


def truncate(s, max_len, end):
    """
    >>> assert truncate("http://www.derp.com", 15, "!") == "http://www.derp!"
    >>> assert truncate("test", 10, "...") == "test"
    """

    return s if len(s) <= max_len else "{0}{1}".format(s[:max_len], end)


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
            if url not in self.cache:
                self.cache[url] = (message.FromHandle, time())
            else:
                try:
                    posted_by, ts = self.cache[url]
                except (KeyError, ValueError):
                    pass
                else:
                    if posted_by != message.FromHandle:
                        s = "{0} has been originally posted by {1} on {2}"
                        msg = s.format(
                            truncate(url, max_len=15, end="..."),
                            posted_by,
                            datetime.fromtimestamp(ts).strftime("%A, %x at %X")
                        )
                        output.append(msg)

        if not output:
            return

        if len(output) is 1:
            msg = u"[Duplicate URL] {0}".format("".join(output))
        else:
            msg = u"[Duplicate URL]\n{0}".format("\n".join(output))
        message.Chat.SendMessage(msg)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
