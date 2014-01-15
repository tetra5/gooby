#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`steamurlparser` --- Steam URL parser plugin
=================================================

.. note::
    This module requires `lxml library <http://lxml.de/>'_
"""


__docformat__ = "restructuredtext en"


# import os
# import urllib
import urllib2
# import cookielib
import re
import gzip
import datetime
import calendar
import codecs
import urlparse
# import errno
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

import lxml.html
from Skype4Py.enums import cmsReceived

from plugin import Plugin
# from config import HOME_DIR


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


class SteamHeaderHandler(urllib2.BaseHandler):
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
        "Referer": "http://store.steampowered.com/",
        "Host": "store.steampowered.com",

        # Age check verification cookie.
        "Cookie": "birthtime=315561601",
    }

    def http_request(self, request):
        for k, v in self._headers.iteritems():
            request.add_header(k, v)

        return request

    https_request = http_request


# class SteamCookieHandler(urllib2.HTTPCookieProcessor):
#     def __init__(self, cookiejar=None):
#         urllib2.HTTPCookieProcessor.__init__(self, cookiejar)
#
#         if cookiejar is None:
#             cookiejar_path = os.path.join(HOME_DIR, "steam_cookies.txt")
#             cookiejar = cookielib.LWPCookieJar(cookiejar_path)
#
#         try:
#             cookiejar.load(ignore_expires=True, ignore_discard=True)
#         except (IOError, cookielib.LoadError) as e:
#             # No such file or directory.
#             if e.errno == errno.ENOENT:
#                 pass
#             else:
#                 raise
#
#         self.cookiejar = cookiejar
#
#     def http_response(self, request, response):
#         self.cookiejar.extract_cookies(response, request)
#         try:
#             # Makes cookie jar file output be more verbose.
#             self.cookiejar.save(ignore_expires=True, ignore_discard=True)
#             pass
#         except IOError:
#             raise
#
#         return response


class SteamAppError(Exception):
    pass


# Flags.
GAME = 1
SOFTWARE = 2
DLC = 4
DLC_AVAILABLE = 8
DISCOUNT_AVAILABLE = 16
FREE_TO_PLAY = 32
EARLY_ACCESS = 64
GREENLIT = 128
STEAM_BIG_PICTURE = 256


class SteamApp(object):
    """
    PAYDAY 2
    >>> app_id = "218620"

    # Dota 2
    # >>> app_id = "570"

    # Z3TA+ 2 (Software)
    # >>> app_id = "241790"

    # Rise of Flight: Channel Battles Edition
    # >>> app_id = "244050"

    # America's Army: Proving Grounds Beta
    # >>> app_id = "203290"

    # Ridge Racer Driftopia
    # >>> app_id = "226410"

    Tomb Raider
    # >>> app_id = "203160"

    # Rise of Flight: Channel Battles Edition
    # Mock; Game + DLC available + discount.
    # >>> with open(os.path.join(HOME_DIR, "244050.txt"), "r") as f:
    # ...     app = SteamApp.from_html_string(f.read())

    >>> app = SteamApp.from_id(app_id, cc="ru")

    >>> app  #doctest: +ELLIPSIS
    <...SteamApp object at...>

    >>> print app
    <Steam application #218620>

    >>> app.flags
    9

    >>> bool(app.flags & (SOFTWARE & ~FREE_TO_PLAY))
    False

    >>> app.real_id
    '218620'

    >>> app.title
    'PAYDAY 2'

    >>> app.developer
    'OVERKILL - a Starbreeze Studio.'

    >>> app.publisher
    '505 Games'

    >>> app.release_date
    datetime.datetime(2013, 8, 13, 4, 0)

    >>> app.price
    u'499 p\u0443\u0431.'

    >>> bool(app.flags & (GAME & ~FREE_TO_PLAY))
    True

    >>> app.genre
    ['Action', 'RPG']
    """

    _api_url = "http://store.steampowered.com/app/{0}/?cc={1}"
    _age_check_api_url = "http://store.steampowered.com/agecheck/app/{0}/"

    # Country Code for localized Store data.
    _default_cc = "us"

    # Stores root lxml.html.Element object for lazy parsing.
    _data = None

    _flags = None

    _real_id = None
    _url = None
    _title = None
    _genre = None
    _price = None
    _release_date = None
    _developer = None
    _publisher = None

    @classmethod
    def from_html_string(cls, html_string):
        obj = cls()
        obj._data = lxml.html.fromstring(html_string)
        getattr(obj, "flags")

        return obj

    @classmethod
    def from_url(cls, app_url):
        opener = urllib2.build_opener()
        opener.add_handler(urllib2.HTTPRedirectHandler())
        opener.add_handler(GzipHandler())
        opener.add_handler(SteamHeaderHandler())
        # opener.addheaders.append(("Cookie", "birthtime=315561601"))

        app_id, cc = cls.parse_app_url(app_url)
        if cc is None:
            cc = cls._default_cc
        app_url = cls._api_url.format(app_id, cc)
        response = opener.open(app_url)
        reader = codecs.getreader("utf-8")
        html_string = reader(response).read()

        # opener.add_handler(SteamCookieHandler())
        # # Submitting age verification POST data if necessary.
        # if "agegate_box" in html_string:
        #     post_data = {
        #         "snr": "1_agecheck_agecheck__age-gate",
        #         "ageDay": "1",
        #         "ageMonth": "January",
        #         "ageYear": "1900",
        #     }
        #     url = cls._age_check_api_url.format(app_id)
        #     response = opener.open(url, urllib.urlencode(post_data))
        #     html_string = reader(response).read()

        return cls.from_html_string(html_string)

    @classmethod
    def from_id(cls, app_id, cc=None):
        if cc is None:
            cc = cls._default_cc
        app_url = cls._api_url.format(app_id, cc)

        return cls.from_url(app_url)

    @staticmethod
    def parse_app_url(url):
        """
        Parses Steam Store App URL and returns a (app_id, country_code) tuple.

        >>> SteamApp.parse_app_url("http://store.steampowered.com/app/1")
        ('1', None)

        >>> SteamApp.parse_app_url("store.steampowered.com/app/42/?cc=us")
        ('42', 'us')

        >>> SteamApp.parse_app_url("store.steampowered.com/app/75?cc=&derp=42")
        ('75', None)

        >>> SteamApp.parse_app_url("store.steampowered.com/app/75/?a=b&cc=us")
        ('75', 'us')

        >>> SteamApp.parse_app_url("store.steampowered.com/app/75?x=y&CC=UK")
        ('75', 'uk')
        """

        pattern = re.compile(
            """
            store\.steampowered\.com/app/
            (?P<app_id>
                \d+
            )
            """,
            re.VERBOSE | re.IGNORECASE | re.UNICODE
        )

        result = re.search(pattern, url)
        try:
            app_id = result.group("app_id")
        except AttributeError:
            raise SteamAppError("could not parse application ID")

        parsed_url = urlparse.urlparse(url.lower())
        try:
            cc = urlparse.parse_qs(parsed_url.query).get("cc", None)[0].lower()
        except (TypeError, IndexError, AttributeError):
            cc = None

        return app_id, cc

    @property
    def flags(self):
        if self._flags is None:
            self._flags = 0

            # Check if Store item is a DLC.
            path = ".//div[@class='game_area_dlc_bubble game_area_bubble']"
            try:
                self._data.find(path).tag
            except AttributeError:
                pass
            else:
                self._flags |= DLC

            # Check whether Store item type is a Software or Game.
            path = ".//div[@class='breadcrumbs']/div[@class='blockbg']"
            try:
                root = self._data.find(path)
                path = ".//a"
                if "software" in root.findall(path)[0].text.lower():
                    self._flags |= SOFTWARE
                else:
                    self._flags |= GAME
            except AttributeError:
                pass

            # Check for discount availability.
            path = (".//div[@class='game_area_purchase_game_wrapper']/"
                    "div/div/div/div/div[@class='discount_prices']")
            try:
                self._data.find(path).tag
            except AttributeError:
                pass
            else:
                self._flags |= DISCOUNT_AVAILABLE

            # Check for DLC availability.
            path = ".//div[@class='game_area_dlc_section']"
            try:
                self._data.find(path).tag
            except AttributeError:
                pass
            else:
                self._flags |= DLC_AVAILABLE

            # Check for Free to Play feature.
            # By meta element.
            path = ".//meta[@content='$0.00']"
            try:
                self._data.find(path).tag
            except AttributeError:
                # By genre.
                path = ".//div[@class='glance_details']/div/a"
                try:
                    for el in self._data.findall(path):
                        if el.text.lower() == "free to play":
                            self._flags |= FREE_TO_PLAY
                            break
                except AttributeError:
                    pass
            else:
                self._flags |= FREE_TO_PLAY

            # Check for early access.
            path = ".//div[@class='early_access_header']/div[@class='heading']"
            try:
                self._data.find(path).tag
            except AttributeError:
                pass
            else:
                self._flags |= EARLY_ACCESS

            # Check for Greenlit status and Steam Big Picture feature support.
            path = ".//div[@class='game_area_description']/h2"
            try:
                for el in self._data.findall(path):
                    if el.text.lower() == "steam greenlight":
                        self._flags |= GREENLIT
                    elif el.text.lower() == "steam big picture":
                        self._flags |= STEAM_BIG_PICTURE
            except AttributeError:
                pass

            if self._flags is 0:
                raise SteamAppError("unable to parse app data")

        return self._flags

    @property
    def title(self):
        if self._title is None:
            path = ".//div[@class='apphub_AppName']"
            self._title = self._data.find(path).text

        return self._title

    @property
    def real_id(self):
        if self._real_id is None:
            path = ".//a[@class='btn_darkblue_white_innerfade btn_medium']"
            self._real_id = self._data.find(path).get("href").split("/")[-1]

        return self._real_id

    @property
    def release_date(self):
        """
        Returns one of the following:
            * datetime.datetime object;
            * string if time data doesn't match format "%d %b %Y";
            * empty string if release date is unknown or hasn't been set.
        """

        # HTTP server returns GMT time.
        # Timezone offset = 14400.

        if self._release_date is None:
            path = ".//div[@class='glance_details']"
            try:
                root = self._data.findall(path)[-1]
                if len(root) > 1:
                    d = root.findall(".//div")[-1].text.strip()
                    fmt = "Release Date: %d %b %Y"
                    try:
                        r_date = datetime.datetime.strptime(d, fmt)
                        r_date = calendar.timegm(r_date.utctimetuple())
                        r_date = datetime.datetime.fromtimestamp(r_date)
                        self._release_date = r_date

                    # TODO: add additional date formats.
                    except ValueError:
                        # raise SteamAppError("time data doesn't match format")
                        self._release_date = d.replace("Release Date: ", "")
                else:
                    # Store item has been released but its release date
                    # hasn't been set for some reason.
                    self._release_date = ""
            except IndexError:
                # Unknown release date.
                self._release_date = ""

        return self._release_date

    @property
    def developer(self):
        """
        Returns either string or empty string.
        """

        if self._developer is None:
            self._developer = ""
            path = ".//div[@itemprop='review']/div[@class='details_block']"
            try:
                for a in self._data.findall(path)[0].findall(".//a"):
                    if "developer" in a.get("href").lower():
                        self._developer = a.text.strip()
                        break
            except (AttributeError, IndexError):
                # raise SteamAppError("unable to parse item details block")
                pass

        return self._developer

    @property
    def publisher(self):
        """
        Returns either string or empty string.
        """

        if self._publisher is None:
            self._publisher = ""
            path = ".//div[@itemprop='review']/div[@class='details_block']"
            try:
                for a in self._data.findall(path)[0].findall(".//a"):
                    if "publisher" in a.get("href").lower():
                        self._publisher = a.text.strip()
                        break
            except (AttributeError, IndexError):
                # raise SteamAppError("unable to parse item details block")
                pass

        return self._publisher

    @property
    def genre(self):
        """
        Returns list of strings or empty list.
        """

        if self._genre is None:
            try:
                path = ".//div[@class='glance_details']/div/a"
                self._genre = [el.text for el in self._data.findall(path)]
            except AttributeError:
                # raise SteamAppError("unable to parse genre")
                self._genre = []

        return self._genre

    @property
    def price(self):
        """
        Returns one of the following:
            * price as a localized unicode string;
            * original price, discount percentage, final price as a tuple;
            * 0 (zero) for Free to Play games or if price hasn't been set or in
              some other possible special cases.
        """

        if self._price is None:
            if bool(self._flags & FREE_TO_PLAY):
                self._price = 0
                return self._price

            # Check whether game is Free to Play.
            # Workaround for "235340", "223390"...
            path = ".//meta[@content='$0.00']"
            try:
                self._data.find(path).tag
            except AttributeError:
                pass
            else:
                self._price = 0
                return self._price

            path = ".//div[@class='game_area_purchase_game_wrapper']"
            root = self._data.find(path)
            try:
                path = ".//div[@class='game_purchase_price price']"
                self._price = root.find(path).text.strip()
            except AttributeError:
                try:
                    # Original price.
                    path = ".//div[@class='discount_original_price']"
                    original_price = root.find(path).text.strip()
                    # Discount percentage.
                    path = ".//div[@class='discount_pct']"
                    discount_pct = root.find(path).text.strip(" %-")
                    # Final price.
                    path = ".//div[@class='discount_final_price']"
                    final_price = root.find(path).text.strip()
                    self._price = (original_price, discount_pct, final_price)
                except AttributeError:
                    self._price = 0

        return self._price

    def __cmp__(self, other):
        return self._data == other._data

    def __unicode__(self):
        return u"<Steam application #{0}>".format(self.real_id)

    def __str__(self):
        return unicode(self).encode("utf-8")


class SteamURLParser(Plugin):
    def get_app_info(self, app_id):
        """
        >>> plugin = SteamURLParser()

        >>> assert "239030" not in plugin.cache

        >>> plugin.get_app_info("239030")  # doctest: +NORMALIZE_WHITESPACE
        ('Papers, Please', datetime.datetime(2013, 8, 8, 4, 0),
        u'249 p\u0443\u0431.', 1)

        >>> assert "239030" in plugin.cache
        """

        @self.cache.get_cached(app_id)
        def _do_get_app_info():
            app = SteamApp.from_id(app_id, cc="ru")
            return app.title, app.release_date, app.price, app.flags

        return _do_get_app_info()

    def on_message_status(self, message, status):
        if status != cmsReceived:
            return

        if "store.steampowered.com/app/" not in message.Body:
            return

        output = []

        for chunk in message.Body.split():
            if "store.steampowered.com/app/" not in chunk:
                continue

            try:
                app_id, cc = SteamApp.parse_app_url(chunk)
            except ValueError:
                pass
            else:
                item_str = "{title} ({r_date}) {price}"
                item_vars = {}
                m = "Retrieving {0} for {1}".format(app_id, message.FromHandle)
                self._logger.info(m)
                try:
                    title, r_date, price, flags = self.get_app_info(app_id)
                except SteamAppError, urllib2.URLError:
                    m = "Unable to retrieve {0} for {1}"
                    self._logger.error(m.format(app_id, message.FromHandle))
                    m = "Unable to retrieve info for {0}"
                    output.append(m.format(app_id))
                    continue

                if flags & FREE_TO_PLAY:
                    item_vars["price"] = "free to play"
                elif price == 0:
                    item_vars["price"] = "price hasn't been set yet"
                else:
                    if isinstance(price, tuple):
                        price_fmt = "{0} - {1}% = {2}"
                        item_vars["price"] = price_fmt.format(*price)
                    else:
                        item_vars["price"] = price
                try:
                    item_vars["r_date"] = r_date.strftime("%d.%m.%Y")
                except AttributeError:
                    if r_date != "":
                        item_vars["r_date"] = r_date
                    else:
                        item_vars["r_date"] = "unknown release date"

                item_vars["title"] = title

                item_extras = []
                if flags & DLC and "dlc" not in title.lower():
                    item_extras.append("DLC")
                if item_extras:
                    item_vars["title"] = "{0}, {1}".format(
                        item_vars["title"], ", ".join(item_extras)
                    )

                if flags & EARLY_ACCESS:
                    item_vars["title"] = "[Early Access] {0}".format(
                        item_vars["title"]
                    )

                output.append(item_str.format(**item_vars))

        if not output:
            return

        if len(output) is 1:
            msg = u"[Steam] {0}".format("".join(output))
        else:
            msg = u"[Steam]\n{0}".format("\n".join(output))

        message.Chat.SendMessage(msg)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
