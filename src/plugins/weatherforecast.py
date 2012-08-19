#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
@author: tetra5 <tetra5dotorg@gmail.com>
"""


__version__ = "2012.1"


import re
import urllib
import urllib2
import time

try:
    from lxml import etree
except ImportError:
    try:
        from xml.etree import cElementTree as etree
    except ImportError:
        from xml.etree import ElementTree as etree

from plugin import ConferenceCommandPlugin


_cache = {}
# Cache time to live in seconds.
_cache_ttl = 600


def sanitize_temperature(temp):
    """
    >>> sanitize_temperature("10")
    '+10'
    >>> sanitize_temperature("-10")
    '-10'
    """
    temp = int(temp)
    return "+%s" % temp if temp > 0 else str(temp)


def fahrenheit_to_celsius(temp_f):
    """Converts temperature in degrees from Fahrenheit to Celsius.

    @param temp_f: Temperature in Fahrenheit degrees.

    >>> fahrenheit_to_celsius("98.6")
    37
    >>> fahrenheit_to_celsius(98.6)
    37
    """
    if not isinstance(temp_f, float):
        temp_f = float(temp_f)
    return int((temp_f - 32) * 5 / 9)


def celsius_to_fahrenheit(temp_c):
    """Converts temperature in degrees from Celsius to Fahrenheit.

    @param temp_c: Temperature in Celsius degrees.

    >>> celsius_to_fahrenheit("37")
    98
    >>> celsius_to_fahrenheit(37)
    98
    """
    if not isinstance(temp_c, float):
        temp_c = float(temp_c)
    return int(temp_c * 9 / 5 + 32)


def get_google_weather_forecast(location, language="en"):
    """Google Weather API client.

    @param location: ZIP code, city, city + country, latitude/longitude,
    whatever Google can handle.
    @param language: ISO 639-1 Language code.
    http://en.wikipedia.org/wiki/List_of_ISO_639-1_codes

    Returns parsed data dictionary.

    Raises urllib2.HTTPError if input XML has not been loaded successfully.

    Raises TypeError if location has not been set correctly (API response is
    empty).

    >>> data = get_google_weather_forecast(location="moscow", language="en")
    >>> data["forecast_information"]["city"]
    'Moscow, Moscow'
    >>> len(data["forecasts"])
    4
    """
    global _cache
    global _chache_ttl

    cached = _cache.get(location)
    if cached:
        if time.time() - cached[0] <= _cache_ttl:
            return cached[1]

    api_url = "http://www.google.com/ig/api?"
    url = api_url + urllib.urlencode({"weather": location, "hl": language})

    # Retrieves XML.
    headers = {
        # Completely unnescessary.
        "User-Agent": "Googlebot/2.1 (+http://www.googlebot.com/bot.html)",
        }
    opener = urllib2.build_opener()
    opener.addheaders = [(k, v) for k, v in headers.iteritems()]
    response = opener.open(fullurl=url, timeout=10)

    element_tree = etree.ElementTree()

    # Parses API response XML.
    root = element_tree.parse(response)

    def element_to_dict(element):
        output = {}
        try:
            element = root.find(element)
        except TypeError:
            pass
        for el in list(element):

            # Skips unnescessary information fields.
            if el.tag in ("icon", "latitude_e6", "longitude_e6", "postal_code",
                          "current_date_time", "forecast_date"):
                continue

            output.update({el.tag: el.get("data")})
        return output

    forecast_information = element_to_dict("weather/forecast_information")

    current_conditions = element_to_dict("weather/current_conditions")

    forecasts = list()

    for element in root.findall("weather/forecast_conditions"):
        forecast = element_to_dict(element)
        forecasts.append(forecast)

    data = {
        "forecast_information": forecast_information,
        "current_conditions": current_conditions,
        "forecasts": forecasts,
        }

    data["current_conditions"]["temp_c"] = \
        sanitize_temperature(data["current_conditions"]["temp_c"])

    # Checks if we need to convert Fahrenheit degrees to Celsius.
    is_si = True
    if data["forecast_information"]["unit_system"] == "US":
        is_si = False

    for forecast in data["forecasts"]:
        # Temperature is set to Fahrenheit degrees. Converts units to Celsius.
        if not is_si:
            forecast["high"] = fahrenheit_to_celsius(forecast["high"])
            forecast["low"] = fahrenheit_to_celsius(forecast["low"])

        forecast["high"] = sanitize_temperature(forecast["high"])
        forecast["low"] = sanitize_temperature(forecast["low"])

    _cache.update({location: (time.time(), data)})
    return data


class WeatherForecast(ConferenceCommandPlugin):
    """Google Weather API conference chat informer plugin."""
    def __init__(self, parent):
        super(WeatherForecast, self).__init__(parent)
        self._commands = {
            "!weather": self.on_weather_command,
            }

    @ConferenceCommandPlugin.log_request
    def on_weather_command(self, message):
        """Retrieves Google Weather API forecast information. Type
        !weather <location> to specify location which is otherwise taken from
        your Skype public profile."""
        substitutes = {
            u"дс": u"Moscow",
            u"dc": u"Moscow",
            u"default city": u"Moscow",
            u"дс2": u"Sankt-Peterburg",
            u"дс 2": u"Sankt-Peterburg",
            u"dc2": u"Sankt-Peterburg",
            u"dc 2": u"Sankt-Peterburg",
            u"spb": u"Sankt-Peterburg",
            u"спб": u"Sankt-Peterburg",
            }

        chat = message.Chat

        match = re.match(r"!weather\s+(.*)", message.Body, re.UNICODE)

        if not match:
            # Acquires location from user's Skype public profile.
            location = message.Sender.City
        else:
            location = match.group(1)

        if not location:
            chat.SendMessage(
                "%s, city of your location has not been set in your " \
                "Skype profile. Specify the location with !weather " \
                "<location> command." % message.FromDisplayName)
            return

        for k, v in substitutes.iteritems():
            if k.lower() in location.lower():
                location = v
                break

        language = message.Sender.CountryCode or "en"

        try:
            forecast = get_google_weather_forecast(location, language)
        except urllib2.HTTPError:
            chat.SendMessage(
                "Unable to receive response from Google Weather API. Try " \
                "again later.")
            return
        except TypeError:
            chat.SendMessage("Unable to get weather forecast for '%s'" %
                             location)
            return

        output = [
            u"Weather forecast for '%s'" %
                forecast["forecast_information"]["city"],

            u"Current conditions: %s °C, %s, %s, %s" % (
                forecast["current_conditions"]["temp_c"],
                forecast["current_conditions"]["condition"],
                forecast["current_conditions"]["humidity"],
                forecast["current_conditions"]["wind_condition"]),

            u"Forecast conditions:",
            ]

        forecasts = []
        for f in forecast["forecasts"]:
            day = u"%s: %s °C / %s °C, %s" % (
                f["day_of_week"], f["high"], f["low"], f["condition"])
            forecasts.append(day)

        output.append(" | ".join(forecasts))

        chat.SendMessage("\n".join(output))


if __name__ == "__main__":
    import doctest
    doctest.testmod()
    # print get_google_weather_forecast("moscow")
