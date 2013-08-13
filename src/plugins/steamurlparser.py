#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`steamurlparser` --- Steam URL parser plugin
=================================================

.. note::
    This module requires `lxml library <http://lxml.de/>'_
"""


__docformat__ = "restructuredtext en"


import os
import urllib
import urllib2
import cookielib
import re
import gzip

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

import lxml.html
from Skype4Py.enums import cmsReceived

from plugin import Plugin
from utils import retry_on_exception
from config import HOME_DIR


class GzipHandler(urllib2.BaseHandler):
    """
    A handler that enhances urllib2's capabilities with transparent gzipped
    data handling support.
    """

    def http_request(self, request):
        request.add_header("Accept-Encoding", "gzip")
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


class MyHandler(urllib2.BaseHandler):
    """
    Just a bunch of extra HTTP headers for urllib2 to inject into HTTP
    requests. Conveniently stored inside a separate handler class.
    """

    _headers = {
        "User-Agent": "Googlebot/2.1 (+http://www.googlebot.com/bot.html)",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "Keep-Alive",
        "Cache-Control": "max-age=0",
        "Referrer": "http://store.steampowered.com/",
    }

    def http_request(self, request):
        for k, v in self._headers.iteritems():
            request.add_header(k, v)
        return request

    https_request = http_request


class MyCookieHandler(urllib2.HTTPCookieProcessor):
    _cookiejar_path = os.path.join(HOME_DIR, "steam.cookies")

    def __init__(self):
        self.cookiejar = cookielib.LWPCookieJar(self._cookiejar_path)
        try:
            self.cookiejar.load()
        except (IOError, cookielib.LoadError):
            pass

    def http_response(self, request, response):
        self.cookiejar.extract_cookies(response, request)
        self.cookiejar.save(ignore_expires=True, ignore_discard=True)
        return response

    https_response = http_response


class SteamURLParser(Plugin):
    _api_url = "http://store.steampowered.com/app/{0}/?cc=ru"

    _pattern = re.compile(
        r"""
        store\.steampowered\.com/app/
        (?P<id>
            \d+
        )
        /?
        """,
        re.UNICODE | re.IGNORECASE | re.VERBOSE)

    _opener = urllib2.build_opener()
    _opener.add_handler(GzipHandler())
    _opener.add_handler(MyHandler())
    _opener.add_handler(MyCookieHandler())
    _opener.add_handler(urllib2.HTTPRedirectHandler())

    def get_app_info(self, app_id):
        """
        http://store.steampowered.com/app/239030

        >>> plugin = SteamURLParser()
        >>> plugin.get_app_info("239030")
        ('Papers, Please', '8 Aug 2013', u'249 p\u0443\u0431.')

        >>> plugin.get_app_info("218620")
        ('PAYDAY 2', '13 Aug 2013', u'499 p\u0443\u0431.')
        """
        @self.cache.get_cached(app_id)
        def _do_get_app_info():
            url = self._api_url.format(app_id)

            @retry_on_exception((urllib2.URLError, urllib2.HTTPError), tries=2,
                                backoff=0, delay=1)
            def retrieve_html(url, data=None):
                if data is None:
                    response = self._opener.open(url)
                else:
                    data = urllib.urlencode(data.copy())
                    response = self._opener.open(url, data)
                buf = response.read()
                return lxml.html.fromstring(buf)

            html = retrieve_html(url)

            # Age verification is necessary.
            # <div id="agegate_box">...
            try:
                html.get_element_by_id("agegate_box")

            except KeyError:
                pass

            else:
                # Sends POST data and stores relevant cookies for the future.
                api_url = "http://store.steampowered.com/agecheck/app/{0}/"
                url = api_url.format(app_id)
                data = {
                    "snr": "1_agecheck_agecheck__age-gate",
                    "ageDay": "1",
                    "ageMonth": "January",
                    "ageYear": "1900",
                }
                html = retrieve_html(url, data)

            try:
                # <div class="apphub_AppName">...
                path = ".//div[@class='apphub_AppName']"
                title = html.find(path).text

                # <div class="game_purchase_price price" itemprop="price">...
                try:
                    price = html.find_class("price")[0].text.strip()

                except IndexError:
                    price = "price hasn't been set yet"

                # There's an active discount on that item currently.
                # <div class="discount_pct">...
                try:
                    path = ".//div[@class='discount_pct']"
                    discount = html.find(path).text.lstrip("-")

                except AttributeError:
                    pass

                else:
                    # <div class="discount_original_price">...
                    path = ".//div[@class='discount_original_price']"
                    original = html.find(path).text

                    # <div class="discount_final_price" itemprop="price">...
                    path = ".//div[@class='discount_final_price']"
                    final = html.find(path).text

                    price = "{0} - {1} = {2}".format(original, discount, final)

                # Release date.
                # Second <div> inside <div class="glance_details">.
                # <div class="glance_details"><div></div><div>...
                try:
                    root = html.find(".//div[@class='glance_details']")
                    released = root.findall(".//div")[1].text.strip()
                    released = released.replace("Release Date: ", "")

                except IndexError:
                    released = "unknown release date"

            except AttributeError:
                return None

            return title, released, price

        return _do_get_app_info()

    def on_message_status(self, message, status):
        if status != cmsReceived:
            return

        if "store.steampowered.com/app/" not in message.Body:
            return

        found = re.findall(self._pattern, message.Body)
        if not found:
            return

        titles = []

        for app_id in found:
            msg = "Retrieving {0} for {1}".format(app_id, message.FromHandle)
            self._logger.info(msg)

            info = self.get_app_info(app_id)

            if info is not None:
                title = "{0} ({1}) {2}".format(*info)
                titles.append(title)
            else:
                msg = "Unable to retrieve info for {0}".format(app_id)
                titles.append(msg)

                msg = "Unable to retrieve {0} for {1}".format(
                    app_id, message.FromHandle
                )
                self._logger.error(msg)

        if not titles:
            return

        if len(titles) is 1:
            msg = u"[Steam] {0}".format("".join(titles))
        else:
            msg = u"[Steam]\n{0}".format("\n".join(titles))
        message.Chat.SendMessage(msg)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
