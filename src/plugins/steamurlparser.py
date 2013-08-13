#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`steamurlparser` --- Steam URL parser plugin
=================================================

.. note::
    This module requires `lxml library <http://lxml.de/>'_
"""


__docformat__ = "restructuredtext en"


import urllib2
import re

import lxml.html
from Skype4Py.enums import cmsReceived

from plugin import Plugin
from utils import retry_on_exception


class SteamURLParser(Plugin):
    _api_url = "http://store.steampowered.com/app/{0}/?cc=us"

    _pattern = re.compile(
        r"""
        store\.steampowered\.com/app/
        (?P<id>
            \d+
        )
        /?
        """,
        re.UNICODE | re.IGNORECASE | re.VERBOSE)

    _headers = {
        "User-Agent": "Googlebot/2.1 (+http://www.googlebot.com/bot.html)",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "Keep-Alive",
        "Cache-Control": "max-age=0",
        "Referrer": "http://store.steampowered.com/",
    }
    _opener = urllib2.build_opener()
    _opener.addheaders = [(k, v) for k, v in _headers.iteritems()]

    def get_app_info(self, app_id):
        """
        http://store.steampowered.com/app/239030

        >>> plugin = SteamURLParser()
        >>> plugin.get_app_info("239030")
        ('Papers, Please', 'Aug 8, 2013', '$9.99')
        """
        @self.cache.get_cached(app_id)
        def _do_get_app_info():
            url = self._api_url.format(app_id)

            @retry_on_exception((urllib2.URLError, urllib2.HTTPError), tries=2,
                                backoff=0, delay=1)
            def retrieve_html():
                response = self._opener.open(url)
                buf = response.read(65536)
                return lxml.html.fromstring(buf)

            html = retrieve_html()

            try:
                # <div class="apphub_AppName">...
                title = html.find(".//div[@class='apphub_AppName']").text

                # <div class="game_purchase_price price" itemprop="price">...
                try:
                    price = html.find_class("price")[0].text.strip()
                except IndexError:
                    price = "price hasn't been set yet"

                # <div class="discount_pct">...
                try:
                    discount = html.find(".//div[@class='discount_pct']")
                    discount = discount.text.lstrip("-")
                except AttributeError:
                    pass
                else:
                    # <div class="discount_original_price">...
                    orig = html.find(".//div[@class='discount_original_price']")
                    orig = orig.text

                    # <div class="discount_final_price" itemprop="price">...
                    final = html.find(".//div[@class='discount_final_price']")
                    final = final.text

                    price = "{0} - {1} = {2}".format(orig, discount, final)

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

            info = self.get_app_info()

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
