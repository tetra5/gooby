#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`steamstoreparser` --- Steam Store parser plugin
=====================================================
"""


from __future__ import unicode_literals


__docformat__ = "restructuredtext en"


import urllib2
import urllib
import re
import datetime
import json

from Skype4Py.enums import cmsReceived, cmsSent

from plugin import Plugin
from output import ChatMessage


_p = re.compile(r'store\.steampowered\.com/app/(\d+)', re.I | re.U)


class SteamStoreParser(Plugin):
    _api_url = 'http://store.steampowered.com/api/appdetails/'
    _api_default_args = dict(l='english', v=1)
    _default_cc = 'ru'

    _headers = {
        "User-Agent": "Googlebot/2.1 (+http://www.googlebot.com/bot.html)",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "Keep-Alive",
    }
    _opener = urllib2.build_opener()
    _opener.addheaders = [(k, v) for k, v in _headers.iteritems()]

    def retrieve_app_infos(self, app_ids):
        """
        # >>> plugin = SteamStoreParser()
        # >>> list(plugin.retrieve_app_infos(['570', '236430', '305620']))
        # ''
        """
        appids = ','.join(app_ids)
        args = dict()
        args.update(self._api_default_args)
        args.update(dict(appids=appids))
        url = ''.join((self._api_url, '?', urllib.urlencode(args)))
        data = json.loads(self._opener.open(url).read())
        for appid in app_ids:
            if not data[appid]['success']:
                yield None
                continue

            app_data = data[appid]['data']
            early_access = False
            for genre in app_data['genres']:
                if genre['description'] == 'Early Access':
                    early_access = True
                    break

            name = app_data['name']
            coming_soon = app_data['release_date']['coming_soon']
            try:
                release_date = app_data['release_date']['date']
                fmt = '%d %b, %Y'
                try:
                    release_date = datetime.datetime.strptime(release_date, fmt)
                except ValueError:
                    pass
            except KeyError:
                release_date = None

            try:
                price = (
                    app_data['price_overview']['currency'],
                    app_data['price_overview']['initial'] / 100.0,
                    app_data['price_overview']['discount_percent'],
                    app_data['price_overview']['final'] / 100.0,
                )
            except KeyError:
                price = "Free to play"
            yield name, coming_soon, release_date, price, early_access

    def on_message_status(self, message, status):
        if status not in (cmsReceived, cmsSent):
            return

        found = re.findall(_p, message.Body)
        if not found:
            return

        output = []

        self._logger.info("Retrieving {0} for {1}".format(", ".join(found),
                                                          message.FromHandle))
        for app_info in self.retrieve_app_infos(found):
            name, coming_soon, release_date, price, early_access = app_info
            if early_access:
                name = " ".join(("[Early Access]", name))

            if release_date:
                try:
                    release_date = release_date.strftime('%d.%m.%Y')
                except (ValueError, AttributeError):
                    pass
            if coming_soon:
                if release_date:
                    release_date = ", ".join(("Coming soon", release_date))
                else:
                    release_date = "Coming soon"

            if isinstance(price, tuple):
                currency, initial, discount_percent, final = price
                if discount_percent != 0:
                    price_fmt = "{0} - {1}% = {2} {3}"
                    price = price_fmt.format(initial, discount_percent,
                                             final, currency)
                else:
                    price_fmt = "{0} {1}"
                    price = price_fmt.format(final, currency)

            out = "{0} ({1}) {2}"
            output.append(out.format(name, release_date, price))

        if not output:
            return

        if len(output) is 1:
            msg = u"Steam -> {0}".format(''.join(output))
        else:
            msg = u"Steam ->\n{0}".format('\n'.join(output))

        self.output.append(ChatMessage(message.Chat.Name, msg))
        return message, status


if __name__ == '__main__':
    import doctest
    doctest.testmod()
