#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`lentaurlparser` - Lenta.ru URL parser plugin
==================================================

.. note::
    This module requires `lxml library <http://lxml.de/>'_
"""


from __future__ import unicode_literals


__docformat__ = "restructuredtext en"


import codecs
import urllib2
import re
import gzip
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

import lxml.html
from Skype4Py.enums import cmsReceived, cmsSent

from plugin import Plugin
from output import ChatMessage


_p = re.compile(
    r"""
    (?P<url>
        (http://)?
        lenta.ru/news/
        (?P<year>
            \d{4}
        )/
        (?P<month>
            \d{2}
        )/
        (?P<day>
            \d{2}
        )/
        (?P<id>
            \w+
        )
    )
    \S
    """, re.VERBOSE | re.UNICODE | re.IGNORECASE)


def find_article_urls(s):
    """
    >>> s = '''http://lenta.ru/news/2014/02/28/herp,
    ... lenta.ru/news/2014/02/28/derp/asdf'''
    >>> found = list(find_article_urls(s))
    >>> expected = ["http://lenta.ru/news/2014/02/28/herp",
    ... "http://lenta.ru/news/2014/02/28/derp"]
    >>> assert sorted(found) == sorted(expected)
    """

    for match in re.finditer(_p, s):
        url = match.group("url")
        if not url.startswith("http://"):
            url = "http://{0}".format(url)
        yield url


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


class LentaHeaderHandler(urllib2.BaseHandler):
    """
    Just a bunch of extra HTTP headers for urllib2 to inject into HTTP
    requests. Conveniently stored inside a separate handler class.
    """

    _headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Charset": "utf-8",
        "Connection": "Keep-Alive",
        "Cache-Control": "max-age=0",
        "Referer": "http://lenta.ru/",
        "Host": "lenta.ru",
    }

    def http_request(self, request):
        for k, v in self._headers.iteritems():
            request.add_header(k, v)

        return request

    https_request = http_request


class LentaURLParser(Plugin):
    """
    A module which resolves "http://lenta.ru/news/<YYYY>/<MM>/<DD>/<id>/"
    URLs to article titles.
    """

    _opener = urllib2.build_opener()
    _opener.add_handler(GzipHandler())
    _opener.add_handler(LentaHeaderHandler())

    def get_article_title(self, lenta_url):
        cached_title = self._cache.get(lenta_url)
        if cached_title is not None:
            return cached_title

        response = self._opener.open(lenta_url)
        reader = codecs.getreader("utf-8")
        html_string = reader(response).read()
        html = lxml.html.fromstring(html_string)

        path = ".//h1[@class='b-topic__title']"
        try:
            title = html.find(path).text.strip()
        except AttributeError:
            title = "#skip#"

        self._cache.set(lenta_url, title)
        return title

    def on_message_status(self, message, status):
        if status not in (cmsReceived, cmsSent):
            return

        if "lenta.ru" not in message.Body.lower():
            return

        found = list(find_article_urls(message.Body.strip()))

        if not found:
            return

        titles = []

        for url in found:
            self._logger.info("Resolving {0} for {1}".format(
                url, message.FromHandle))

            title = self.get_article_title(url)

            if title == "#skip#":
                msg = "No clue, skipping".format(message.FromHandle)
                self._logger.info(msg)
            else:
                titles.append(title)
                self._logger.info("-> {0}".format(title))

        if not titles:
            return

        if len(titles) is 1:
            msg = "[Lenta] {0}".format("".join(titles))
        else:
            msg = "[Lenta]\n{0}".format("\n".join(titles))
        self.output.append(ChatMessage(message.Chat.Name, msg))
        return message, status


if __name__ == "__main__":
    import doctest
    doctest.testmod()
