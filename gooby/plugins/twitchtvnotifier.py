#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`twitchtvnotifier` --- Twitch.tv Notification Plugin
=========================================================
"""


from __future__ import unicode_literals


__docformat__ = "restructuredtext en"


import urllib2
import urllib
import json
import atexit
from threading import Timer

# from Skype4Py.enums import cmsReceived, cmsSent

from plugin import Plugin
from output import ChatMessage
from dispatcher import dispatcher
from pluginmanager import chat_is_whitelisted
import signals


_timer = None

DEFAULT_CHECK_INTERVAL = 60

STATUS_ONLINE = 1
STATUS_OFFLINE = 0

MESSAGE_TEMPLATE = "{display_name} is now streaming {game} at {url}"


class TwitchTvNotifier(Plugin):
    _api_url = 'https://api.twitch.tv/kraken/streams'

    _headers = {
        "User-Agent": "Googlebot/2.1 (+http://www.googlebot.com/bot.html)",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "Keep-Alive",
    }
    _opener = urllib2.build_opener()
    _opener.addheaders = [(k, v) for k, v in _headers.iteritems()]

    @staticmethod
    @atexit.register
    def _cleanup():
        global _timer
        try:
            _timer.cancel()
            _timer.join()
        except AttributeError:
            pass
        finally:
            del _timer

    def _check_streams(self):
        if not self.stream_names:
            return

        global _timer
        output = []
        data = self.retrieve_stream_data(self.stream_names)
        for stream, params in data.iteritems():
            if not params:
                self.cache.set(stream, STATUS_OFFLINE)
                continue
            previous_state = self.cache.get(stream)
            if previous_state in (None, STATUS_OFFLINE):
                output.append(MESSAGE_TEMPLATE.format(**data))
            self.cache.set(stream, STATUS_ONLINE)

        if self.whitelist:
            message = "\n".join(output)
            responses = dispatcher.send(signals.REQUEST_CHATS)
            chats = responses[0]
            for chat in chats:
                if chat_is_whitelisted(chat, self.whitelist):
                    self.output.append(ChatMessage(chat, message))
        _timer = Timer(self.check_interval, self._check_streams)
        _timer.daemon = True
        _timer.start()

    def __init__(self, priority=0, whitelist=None, **kwargs):
        super(TwitchTvNotifier, self).__init__(priority, whitelist, **kwargs)
        self.check_interval = self.options.get('check_interval',
                                               DEFAULT_CHECK_INTERVAL)
        self.stream_names = self.options.get('streams', list())
        self.logger.info("Watching %s", self.stream_names)
        self._check_streams()

    def retrieve_stream_data(self, channels):
        """
        >>> plugin = TwitchTvNotifier()
        >>> data = plugin.retrieve_stream_data(['pingeee', 'beyondthesummit'])
        >>> data  #doctest: +NORMALIZE_WHITESPACE
        {u'beyondthesummit': {}, u'pingeee':
        {u'url': u'http://www.twitch.tv/pingeee', u'game':
        u'Heroes of the Storm', u'display_name': u'Pingeee'}}
        """

        args = dict()
        args.update({'channel': ','.join(channels)})
        url = ''.join((self._api_url, '?', urllib.urlencode(args)))
        data = json.loads(self._opener.open(url).read())
        streams = dict()
        for stream_data in data.get('streams'):
            try:
                name = stream_data.get('channel').get('name')
            except AttributeError:
                continue
            streams.setdefault(name, {
                'display_name': stream_data.get('channel').get('display_name'),
                'url': stream_data.get('channel').get('url'),
                'game': stream_data.get('game'),
            })
        for channel in channels:
            if channel not in streams:
                streams.update({channel: dict()})
        return streams

if __name__ == '__main__':
    import doctest
    doctest.testmod()
