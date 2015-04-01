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
import datetime
import json
import atexit
from threading import Timer

from Skype4Py.enums import cmsReceived, cmsSent

from plugin import Plugin
from output import ChatMessage
from dispatcher import dispatcher
from pluginmanager import chat_is_whitelisted
import signals


_timer = None

DEFAULT_CHECK_INTERVAL = 60

ONLINE = 1
OFFLINE = 0


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
        global _timer
        output = []
        message_template = "{display_name} is now streaming {game} at {url}"
        stream_info = self.retrieve_stream_info(self.stream_names)
        for name, options in stream_info.iteritems():
            if not options:
                self.cache.set(name, OFFLINE)
                continue
            previous_state = self.cache.get(name)
            if previous_state in (None, OFFLINE):
                output.append(message_template.format(**stream_info))
            self.cache.set(name, ONLINE)

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

    def retrieve_stream_info(self, stream_names):
        """
        >>> plugin = TwitchTvNotifier()
        >>> info = plugin.retrieve_stream_info(['pingeee', 'beyondthesummit'])
        >>> info #doctest: +NORMALIZE_WHITESPACE
        {u'beyondthesummit': {u'url': u'http://www.twitch.tv/beyondthesummit',
        u'game': u'Dota 2', u'display_name': u'BeyondTheSummit'}, u'pingeee':
        {}}
        """

        args = dict()
        args.update(dict(channel=','.join(stream_names)))
        url = ''.join((self._api_url, '?', urllib.urlencode(args)))
        data = json.loads(self._opener.open(url).read())
        streams = dict()
        for stream_data in data.get('streams'):
            name = stream_data.get('channel').get('name')
            if name is None:
                continue
            stream = streams.setdefault(name, dict())
            stream.update({
                'display_name': stream_data.get('channel').get('display_name'),
                'url': stream_data.get('channel').get('url'),
                'game': stream_data.get('game'),
            })
        for stream_name in stream_names:
            if stream_name not in streams:
                streams.update({stream_name: dict()})
        return streams

if __name__ == '__main__':
    import doctest
    doctest.testmod()
