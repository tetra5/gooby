#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`guessthepicture`
======================

.. note::
    This module requires `lxml library <http://lxml.de/>'_
"""


from __future__ import unicode_literals


__docformat__ = "restructuredtext en"


import codecs
import gzip
import urllib2
import re
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

import lxml.html
from Skype4Py.enums import cmsReceived, cmsSent

from plugin import Plugin
from utils import retry_on_exception
from output import ChatMessage


class GzipHandler(urllib2.BaseHandler):
    """
    A handler that enhances urllib2's capabilities with transparent gzipped
    data handling support.
    """

    def http_request(self, request):
        request.add_header("Accept-Encoding", "gzip, deflate")

        return request

    https_request = http_request

    def http_response(self, request, response):
        new_response = response
        if response.headers.get("Content-Encoding") == "gzip":
            gzipped = gzip.GzipFile(
                fileobj=StringIO(response.read()), mode="r")
            new_response = urllib2.addinfourl(
                gzipped, response.headers, response.url, response.code)
            new_response.msg = response.msg

        return new_response

    https_response = http_response


class GoogleHeaderHandler(urllib2.BaseHandler):
    """
    Just a bunch of extra HTTP headers for urllib2 to inject into HTTP
    requests. Conveniently stored inside a separate handler class.
    """

    _headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Charset": "utf-8",
        #"Connection": "Keep-Alive",
        #"Cache-Control": "max-age=0",
        #"Referer": "http://www.google.com",
        #"Host": "www.google.com",
    }

    def http_request(self, request):
        for k, v in self._headers.iteritems():
            request.add_header(k, v)

        return request

    https_request = http_request


def find_urls(s):
    """
    >>> s = '''http://test.com/a.jpeg www.test.com/derp.gif
    ... http://www.test.com/.gif http://www.test.com/test.gif.png
    ... http://www.youtube.com/watch?v=dQw4w9WgXcQ'''
    >>> expected = (["http://test.com/a.jpeg", "www.test.com/derp.gif",
    ... "http://www.test.com/test.gif.png", "http://www.test.com/.gif"])
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
        for ext in ("gif", "png", "jpg", "jpeg"):
            if found[0].endswith(".{0}".format(ext)):
                retval.append(found[0])
    return retval


class GuessThePicture(Plugin):
    _api_url = "http://www.google.com/searchbyimage?image_url={0}"

    _opener = urllib2.build_opener()
    #_opener.add_handler(urllib2.HTTPRedirectHandler())
    _opener.add_handler(GzipHandler())
    _opener.add_handler(GoogleHeaderHandler())

    def guess_the_picture(self, image_url):
        """
        >>> plugin = GuessThePicture()

        >>> url = "http://d24w6bsrhbeh9d.cloudfront.net/photo/a09n4Yq_460sa_v1.gif"
        >>> plugin.guess_the_picture(url)
        'firewood processor'

        >>> url = "http://armarium.org/u/2014/02/13/JRbC65Q.gif"
        >>> plugin.guess_the_picture(url)
        'family guy fart'
        """

        cached_guess = self._cache.get(image_url)
        if cached_guess is not None:
            return cached_guess

        url = self._api_url.format(image_url)

        @retry_on_exception((urllib2.URLError, urllib2.HTTPError), tries=2,
                            backoff=0, delay=1)
        def retrieve_html():
            response = self._opener.open(url)
            reader = codecs.getreader("utf-8")
            html_string = reader(response).read()
            return lxml.html.fromstring(html_string)

        html = retrieve_html()

        path = ".//div[@class='qb-bmqc']/a[@class='qb-b']"

        try:
            guess = html.find(path).text.strip()

        except AttributeError:
            guess = "#skip#"

        self._cache.set(image_url, guess)
        return guess

    def on_message_status(self, message, status):
        if status not in (cmsReceived, cmsSent):
            return

        found = find_urls(message.Body)

        if not found:
            return

        output = []

        for url in found:
            self._logger.info("Guessing {0} for {1}".format(
                url, message.FromHandle))

            guess = self.guess_the_picture(url)

            if guess == "#skip#":
                msg = "No clue, skipping".format(message.FromHandle)
                self._logger.info(msg)
            else:
                output.append(guess)
                self._logger.info("-> {0}".format(guess))

        if not output:
            return

        #if len(output) is 1:
        #    msg = "^ etot about {0}".format("".join(output))
        #else:
        #    msg = "^ etot about\n{0}".format("\n".join(output))

        msg = "^ etot about {0}".format(", ".join(output))

        self.output.append(ChatMessage(message.Chat.Name, msg))
        #message.Chat.SendMessage(msg)
        return message, status


if __name__ == "__main__":
    import doctest
    doctest.testmod()
