#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
@author: tetra5 <tetra5dotorg@gmail.com>
"""


__version__ = "2012.3"


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

from plugin import ChatCommandPlugin


_cache = {}
# Cache time to live in seconds.
_cache_ttl = 1200


class APIError(Exception):
    pass


def country_code_to_language_code(country_code):
    """Converts ISO 3166 Country Code (which is used by Skype) to ISO 639
    Language Code.
    Why would anybody need this? Google API supports "hl" (language code)
    request variable. It's possible to get localized API response granted if
    language code is provided.

    More on this topic:
    http://en.wikipedia.org/wiki/ISO_3166-1
    http://en.wikipedia.org/wiki/List_of_ISO_639-1_codes
    http://docs.oracle.com/cd/E13214_01/wli/docs92/xref/xqisocodes.html
    http://msdn.microsoft.com/en-us/library/cc233965.aspx
    """
    # Key: Country Code, value: Language Code, sorted by language.
    codes = {
        "za": "af", # South African, Afrikaans
        "al": "sq", # Albania, Albanian
        # "fr": "gsw", # France, Alsatian
        "et": "am", # Ethiopia, Amharic
        "dz": "ar", # Algeria, Arabic
        "bh": "ar", # Bahrain, Arabic
        "eg": "ar", # Egypt, Arabic
        "iq": "ar", # Iraq, Arabic
        "jo": "ar", # Jordan, Arabic
        "kw": "ar", # Kuwait, Arabic
        "lb": "ar", # Lebanon, Arabic
        "ly": "ar", # Libya, Arabic
        "ma": "ar", # Morocco, Arabic
        "om": "ar", # Oman, Arabic
        "qa": "ar", # Qatar, Arabic
        "sa": "ar", # Saudi Arabia, Arabic
        "sy": "ar", # Syria, Arabic
        "tn": "ar", # Tunisia, Arabic
        "ae": "ar", # U.A.E., Arabic
        "ye": "ar", # Yemen, Arabic
        "am": "hy", # Armenia, Armenian
        # "in": "as", # India, Assamese
        "az": "az", # Azerbaijan, Azerbaijani (Cyrillic/Latin)
        "bd": "bn", # Bangladesh, Bangla
        # "in": "bn", # India, Bangla
        # "ru": "ba", # Russia, Bashkir
        # "es": "eu", # Spain, Basque
        "by": "be", # Belarus, Belarusian
        "ba": "bs", # Bosnia and Herzegovina, Bosnian (Cyrillic/Latin)
        # "fr": "br", # France, Breton
        "bg": "bg", # Bulgaria, Bulgarian
        # "es": "ca", # Spain, Catalan
        # "iq": "ku", # Iraq, Central Kurdish
        # "us": "chr", # United States, Cherokee
        "cn": "zh", # People's Republic of China, Chinese (Simplified)
        "sg": "zh", # Singapore, Chinese (Simplified)
        "hk": "zh", # Hong Kong S.A.R., Chinese (Traditional)
        "mo": "zh", # Macao S.A.R., Chinese (Traditional)
        "tw": "zh", # Taiwan, Chinese (Traditional)
        # "fr": "co", # France, Corsican
        "hr": "hr", # Croatia, Croatian
        # "ba": "hr", # Bosnia and Herzegovina, Croatian (Latin)
        "cz": "cs", # Czech Republic, Czech
        "dk": "da", # Denmark, Danish
        "af": "prs", # Afghanistan, Dari
        "mv": "dv", # Maldives, Divehi
        "be": "nl", # Belgium, Dutch
        "nl": "nl", # Netherlands, Dutch
        "au": "en", # Australia, English
        "bz": "en", # Belize, English
        "da": "en", # Canada, English
        "029": "en", # Caribbean, English. FIXME: seems legit.
        # "in": "en", # India, English
        # "ie": "en", # Ireland, English
        "jm": "en", # Jamaica, English
        # "my": "en", # Malaysia, English
        "nz": "en", # New Zealand, English
        # "ph": "en", # Republic of the Philippines, English
        # "sg": "en", # Singapore, English
        # "za": "en", # South Africa, English
        "tt": "en", # Trinidad and Tobago, English
        "gb": "en", # United Kingdom, English
        "us": "en", # United States, English
        "zw": "en", # Zimbabwe, English
        "ee": "et", # Estonia, Estonian
        "fo": "fo", # Faroe Islands, Faroese
        "ph": "fil", # Philippines, Filipino
        "fi": "fi", # Finland, Finnish
        # "be": "fr", # Belgium, French
        # "ca": "fr", # Canada, French
        "fr": "fr", # France, French
        # "lu": "fr", # Luxembourg, French
        "mc": "fr", # Principality of Monaco, French
        # "ch": "fr", # Switzerland, French
        # "nl": "fy", # Netherlands, Frisian
        # "sn": "ff", # Senegal, Fulah
        # "es": "gl", # Spain, Galician
        "ge": "ka", # Georgia, Georgian
        "at": "de", # Austria, German
        "de": "de", # Germany, German
        "li": "de", # Liechtenstein, German
        # "lu": "de", # Luxembourg, German
        "ch": "de", # Switzerland, German
        "gr": "el", # Greece, Greek
        "gl": "kl", # Greenland, Greenlandic
        # "in": "gu", # India, Gujarati
        "ng": "ha", # Nigeria, Hausa (Latin)
        # "us": "haw", # United States, Hawaiian
        "il": "he", # Israel, Hebrew
        "in": "hi", # India, Hindi
        "hu": "hu", # Hungary, Hungarian
        "is": "is", # Iceland, Icelandic
        #"ng": "ig", # Nigeria, Igbo
        "id": "id", # Indonesia, Indonesian
        # "ca": "iu", # Canada, Inuktitut (Latin/Syllabics)
        "ie": "ga", # Ireland, Irish
        "it": "it", # Italy, Italian
        # "ch": "it", # Switzerland, Italian
        "jp": "ja", # Japan, Japanese
        # "gt": "qut", # Guatemala, K'iche
        # "in": "kn", # India, Kannada
        "kz": "kk", # Kazakhstan, Kazakh
        "kh": "km", # Cambodia, Khmer
        "rw": "rw", # Rwanda, Kinyarwanda
        "ke": "sw", # Kenya, Kiswahili
        # "in": "kok", # India, Konkani
        "kr": "ko", # Korea, Korean
        "kg": "ky", # Kyrgyzstan, Kyrgyz
        "la": "lo", # Lao P.D.R., Lao
        "lv": "lv", # Latvia, Latvian
        "lt": "lt", # Lithuania, Lithuanian
        # "de": "dsb", # Germany, Lower Sorbian
        "lu": "lb", # Luxembourg, Luxembourgish
        "mk": "mk", # Macedonia, Macedonian
        "bn": "ms", # Brunei Darussalam, Malay
        "my": "ms", # Malaysia, Malay
        # "in": "ml", # India, Malayalam
        "mt": "mt", # Malta, Maltese
        # "nz": "mi", # New Zealand, Maori
        # "cl": "arn", # Chile, Mapudungun
        # "in": "mr", # India, Marathi
        # "ca": "moh", # Canada, Mohawk
        "mn": "mn", # Mongolia, Mongolian (Cyrillic)
        # "cn": "mn", # People's Republic of China, Mongolian (Traditional)
        "np": "ne", # Nepal, Nepali
        "no": "nb", # Norway, Norwegian (Borkmal)
        # "no": "nn", # Norway, Norwegian (Nynorsk)
        # "fr": "oc", # France, Occitan
        # "in": "or", # India, Odia
        # "af": "ps", # Afghanistan, Pashto
        "ir": "fa", # Iran, Persian
        "pl": "pl", # Poland, Polish
        "br": "pt", # Brazil, Portuguese
        "pt": "pt", # Portugal, Portuguese
        # "in": "pa", # India, Punjabi
        # "pk": "pa", # Islamic Republic of Pakistan, Punjabi
        # "bo": "quz", # Bolivia, Quechua
        # "ec": "quz", # Ecuador, Quechua
        # "pe": "quz", # Peru, Quechua
        "ro": "ro", # Romania, Romanian
        # "ch": "rm", # Switzerland, Romansh
        "ru": "ru", # Russia, Russian
        # "ru": "sah", # Russia, Sakha
        # "fi": "smn", # Finland, Sami (Inari)
        # "no": "smj", # Norway, Sami (Lule)
        # "fi": "se", # Finland, Sami (Northern)
        # "no": "se", # Norway, Sami (Northern)
        # "se": "se", # Sweden, Sami (Northern)
        # "fi": "sms", # Finland, Sami (Skolt)
        # "no": "sma", # Norway, Sami (Southern)
        # "se": "sma", # Sweden, Sami (Southern)
        # "in": "sa", # India, Sanskrit
        # "gb": "gd", # United Kingdom, Scottish Gaelic
        # "ba": "sr", # Bosnia and Herzegovina, Serbian (Cyrillic/Latin)
        "me": "sr", # Montenegro, Serbian (Cyrillic/Latin)
        "rs": "sr", # Serbia, Serbian (Cyrillic/Latin)
        "cs": "sr", # Serbia and Montenegro (Former), Serbian (Cyrillic/Latin)
        # "za": "nso", # South Africa, Sesotho sa Leboa
        "bw": "tn", # Botswana, Setswana
        # "za": "tn", # South Africa, Setswana
        # "pk": "sd", # Islamic Republic of Pakistan, Sindhi
        "lk": "si", # Sri Lanka, Sinhala
        "sk": "sk", # Slovakia, Slovak
        "si": "sl", # Slovenia, Slovenian
        "ar": "es", # Argentina, Spanish
        "ve": "es", # Bolivarian Republic of Venezuela, Spanish
        "bo": "es", # Bolivia, Spanish
        "cl": "es", # Chile, Spanish
        "co": "es", # Colombia, Spanish
        "cr": "es", # Costa Rica, Spanish
        "do": "es", # Dominican Republic, Spanish
        "ec": "es", # Ecuador, Spanish
        "sv": "es", # El Salvador, Spanish
        "gt": "es", # Guatemala, Spanish
        "hn": "es", # Honduras, Spanish
        "mx": "es", # Mexico, Spanish
        "ni": "es", # Nicaragua, Spanish
        "pa": "es", # Panama, Spanish
        "py": "es", # Paraguay, Spanish
        "pe": "es", # Peru, Spanish
        "pr": "es", # Puerto Rico, Spanish
        "es": "es", # Spain, Spanish
        # "us": "es", # United States, Spanish
        "uy": "es", # Uruguay, Spanish
        # "fi": "sv", # Finland, Swedish
        "se": "sv", # Sweden, Swedish
        "sy": "syr", # Syria, Syriac
        "tj": "tg", # Tajikistan, Tajik (Cyrillic)
        "dz": "tzm", # Algeria, Tamazight (Latin)
        # "in": "ta", # India, Tamil
        # "lk": "ta", # Sri Lanka, Tamil
        # "ru": "tt", # Russia, Tatar
        # "in": "te", # India, Telugu
        "th": "th", # Thailand, Thai
        # "cn": "bo", # People's Republic of China, Tibetan
        "er": "ti", # Eritrea, Tigrinya
        "et": "ti", # Ethiopia, Tigrinya
        "tr": "tr", # Turkey, Turkish
        "tm": "tk", # Turkmenistan, Turkmen
        "ua": "uk", # Ukraine, Ukrainian
        # "de": "hsb", # Germany, Upper Sorbian
        "pk": "ur", # Islamic Republic of Pakistan, Urdu
        # "cn": "ug", # People's Republic of China, Uyghur
        "uz": "uz", # Uzbekistan, Uzbek (Cyrillic/Latin)
        "valencia": "ca", # Spain, Valencian
        "vn": "vi", # Vietnam, Vietnamese
        # "gb": "cy", # United Kingdom, Welsh
        "sn": "wo", # Senegal, Wolof
        # "cn": "ii", # People's Republic of China, Yi
        # "ng": "yo", # Nigeria, Yoruba
        # "za": "xh", # South Africa, Xhosa
        # "za": "zu", # South Africa, Zulu
        }

    return codes.get(country_code)


def retry(exception, tries=10, delay=3, backoff=1):
    """Retries a function or method until it stops generating specified
    exception.

    @param exception: Exception generated by decorated function or method.
    @param tries: Number of tries.
    @param delay: Delay between tries in seconds.
    @param backoff: Factor by which the delay should lengthen after each
    failure.
    """
    def wrapper(f):
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 0:
                try:
                    return f(*args, **kwargs)
                except exception:
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return
        return f_retry
    return wrapper


def fahrenheit_to_celsius(temp_f):
    """Fahrenheit to Celsius degrees conversion.

    @param temp_f: Temperature in Fahrenheit degrees.

    >>> fahrenheit_to_celsius("98.6")
    37
    >>> fahrenheit_to_celsius(98.6)
    37
    """
    if temp_f is None:
        return
    if not isinstance(temp_f, float):
        temp_f = float(temp_f)
    return int((temp_f - 32) * 5 / 9)


def celsius_to_fahrenheit(temp_c):
    """Celsius to Fahrenheit degrees conversion.

    @param temp_c: Temperature in Celsius degrees.

    >>> celsius_to_fahrenheit("37")
    98
    >>> celsius_to_fahrenheit(37)
    98
    """
    if temp_c is None:
        return
    if not isinstance(temp_c, float):
        temp_c = float(temp_c)
    return int(temp_c * 9 / 5 + 32)


def get_google_weather_forecast(location, language="en"):
    """Google Weather API client.

    @param location: ZIP code, city, city + country, latitude/longitude,
    probably some more. Whatever Google is able to handle.
    @param language: ISO 639-1 Language code.
    http://en.wikipedia.org/wiki/List_of_ISO_639-1_codes

    Returns parsed data dictionary.

    Raises APIError exception when:
    a) it was impossible to retrieve API response;
    b) API has returned empty response (unknown/incorrect location).

    >>> data = get_google_weather_forecast(location="moscow", language="en")
    >>> city = data["forecast_information"]["city"]
    >>> city in ("Moscow, Moscow", "Moscow, Moskva")
    True
    """
    global _cache
    global _chache_ttl

    cache = _cache.get(location)
    if cache:
        cache_time, data = cache
        if time.time() - cache_time <= _cache_ttl:
            return data

    api_url = "http://www.google.com/ig/api?"

    location = location.encode("utf-8")
    url = api_url + urllib.urlencode({"weather": location, "hl": language})

    headers = {
        "User-Agent": "Googlebot/2.1 (+http://www.googlebot.com/bot.html)",
        }
    opener = urllib2.build_opener()
    opener.addheaders = [(k, v) for k, v in headers.iteritems()]

    @retry((urllib2.URLError, urllib2.HTTPError, etree.ParseError))
    def retrieve_and_process_response():
        response = opener.open(fullurl=url, timeout=2)
        element_tree = etree.ElementTree()
        return element_tree.parse(response)

    root = retrieve_and_process_response()
    if root is None:
        raise APIError("Unable to retrieve weather forecast.")

    """
    Typical weather forecast report structure.

    structure = {
        "forecast_information": {
            # Unit system could be either US or SI.
            "unit_system": "",
            "city": "",
            },
        "current_conditions": {
            "condition": "",
            "temp_c": "",
            "humidity": "",
            "wind_condition": "",
            },
        "forecast_conditions": [
                # Forecast conditions are repeated for every each of one 4 days
                # ahead.
                {
                    # Low and High temperatures are either of Fahrenheit or
                    # Celsius scale depending on Unit system.
                    "low": "",
                    "high": "",
                    "day_of_week": "",
                    "condition": "",
                 },
            ],
        }
    """

    def element_to_dict(element):
        output = {}
        try:
            element = root.find(element)
        except TypeError:
            pass

        if element is None:
            raise APIError("Unable to retrieve weather forecast for %s" %
                           location)

        for el in list(element):
            # Skips unnecessary information fields.
            if el.tag in ("icon", "latitude_e6", "longitude_e6", "postal_code",
                          "current_date_time", "forecast_date", "temp_f"):
                continue
            output.update({el.tag: el.get("data") or None})
        return output

    # Parses XML.
    forecast_information = element_to_dict("weather/forecast_information")
    current_conditions = element_to_dict("weather/current_conditions")

    forecasts = []
    for element in root.findall("weather/forecast_conditions"):
        forecast = element_to_dict(element)
        forecasts.append(forecast)

    # Populates forecast data.
    data = {}

    if None not in current_conditions.values():
        data.update({"current_conditions": current_conditions})

    data.update({"forecast_information": forecast_information})

    unit_system = data.get("forecast_information").get("unit_system")
    forecasts_list = []
    for forecast in forecasts:
        # Skips corrupted forecast data.
        if None in forecast.values():
            continue

        if unit_system == "US":
            high = forecast.get("high")
            low = forecast.get("low")
            high, low = map(fahrenheit_to_celsius, (high, low))
            forecast.update({"high": high, "low": low})

        forecasts_list.append(forecast)

    if forecasts_list:
        data.update({"forecasts": forecasts_list})

    _cache.update({location: (time.time(), data)})
    return data


class WeatherForecast(ChatCommandPlugin):
    """Google Weather API conference chat informer plugin."""
    def __init__(self, parent):
        super(WeatherForecast, self).__init__(parent)
        self._commands = {
            "!weather": self.on_weather_command,
            }

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
            line = (u"%s, city of your location has not been set in your "
                    "Skype profile. Specify the location with !weather "
                    "<location> command.") % message.FromDisplayName
            chat.SendMessage(line)
            return

        # Searches substitutes dictionary for known locations.
        # TODO: probably move this dictionary to external configuration file
        # along with other plugin settings.
        loc = location.lower().strip()
        if loc in substitutes:
            location = substitutes.get(loc)

        country_code = message.Sender.CountryCode
        language = country_code_to_language_code(country_code) or "en"

        try:
            forecast = get_google_weather_forecast(location, language)
        except APIError, e:
            chat.SendMessage(e)
            return

        # Populates output.
        output = []

        forecast_information = forecast.get("forecast_information")
        output.append(u"Weather forecast for %(city)s" % forecast_information)

        current_conditions = forecast.get("current_conditions")
        if current_conditions:
            line = (u"Current conditions: %(temp_c)s °C, %(condition)s, "
                    "%(humidity)s, %(wind_condition)s") % current_conditions
            output.append(line)

        forecasts = forecast.get("forecasts")
        if forecasts:
            output.append(u"Forecast conditions:")
            for forecast in forecasts:
                line = (u"%(day_of_week)s: %(high)s | %(low)s °C, "
                        "%(condition)s") % forecast
                output.append(line)

        chat.SendMessage("\n".join(output))
        return


if __name__ == "__main__":
    import doctest
    doctest.testmod()
