#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`test_pluginmanager` --- Plugin Manager unit tests
=======================================================
"""


from __future__ import unicode_literals


__docformat__ = "restructuredtext en"


import unittest

import tests
from gooby.plugin import Plugin
from gooby.pluginmanager import (PluginManager, camelcase_to_underscores,
                                 chat_is_whitelisted)


SAMPLE_CONFIG = {
    "tests.test_pluginmanager.TestPlugin": {
        "priority": 1,
        "whitelist": [
            "some_chat",
        ],
        "test": 123,
        "herp": "derp",
    },
    "tests.test_pluginmanager.YetAnotherPlugin": {
        "priority": 42,
        "whitelist": [
            "chat",
        ],
    },
    "tests.test_pluginmanager.DefaultConfigPlugin": {

    },
}


class TestPlugin(Plugin):
    def on_message_status(self, message, status):
        self.output.append("1")
        return message, status

    def on_call_history(self):
        pass


class YetAnotherPlugin(Plugin):
    def on_message_status(self, message, status):
        self.output.append("derp")
        message.Body = "{0}, modified".format(message.Body)
        return message, status


class DefaultConfigPlugin(Plugin):
    pass


class DummyChat(object):
    # Skype4Py Chat object stub.
    Name = ""


class DummyMessage(object):
    # Skype4Py Message object stub.
    Body = "message body"
    Chat = DummyChat()


class PluginManagerTestCase(unittest.TestCase):
    def setUp(self):
        self.pm = PluginManager(SAMPLE_CONFIG)

    def test_extra_plugin_options_are_set(self):
        options = None
        for p in self.pm.plugins:
            if p.__class__.__name__ == "TestPlugin":
                options = p.options
                break
        expected = {"test": 123, "herp": "derp"}
        self.assertEquals(options, expected)

    def test_handlers_for_event(self):
        handlers = []
        for handler, priority, whitelist in self.pm.handlers("MessageStatus"):
            handlers.append((handler.__name__, priority, whitelist))
        expected = [
            ("on_message_status", 1, ["some_chat"]),
            ("on_message_status", 42, ["chat"]),
            ("on_message_status", 0, None),
        ]
        self.assertItemsEqual(expected, handlers)

    def test_handlers_for_unknown_event(self):
        self.assertItemsEqual(list(), list(self.pm.handlers("UnknownEvent")))

    def test_handlers_sorted_by_priority_descending(self):
        priorities = []
        for _, priority, _ in self.pm.handlers("MessageStatus"):
            priorities.append(priority)
        self.assertEqual([42, 1, 0], priorities)

    def test_handler_exec_for_event_message_body_changed(self):
        message = DummyMessage()
        message.Chat.Name = "chat"
        status = 1337
        handler = self.pm.on_event("MessageStatus")
        handler(message, status)
        self.assertEqual("message body, modified", message.Body)

    def test_handler_exec_for_event_output(self):
        handler = self.pm.on_event("MessageStatus")
        message = DummyMessage()
        message.Chat.Name = "some_chat"
        status = 1337
        handler(message, status)
        output = list()
        for plugin in self.pm.plugins:
            output.extend(plugin.flush_output())
        expected = ["1"]
        self.assertEquals(expected, output)

    def test_skip_chat_if_not_whitelisted_while_whitelist_is_set(self):
        # Quick check whether "chat" is whitelisted for "YetAnotherPlugin".
        expected = ["chat"]
        self.assertEqual(expected, list(self.pm.plugins)[0].whitelist)

        handler = self.pm.on_event("MessageStatus")
        message = DummyMessage()
        # Chat name is set to "other_chat" so it won't appear on whitelist.
        message.Chat.Name = "other_chat"
        status = 1337
        handler(message, status)
        output = list()
        for plugin in self.pm.plugins:
            output.extend(plugin.flush_output())
        # No output expected since "other_chat" is not whitelisted anywhere.
        expected = list()
        self.assertEqual(expected, output)

    def test_return_values_and_initial_arguments_are_matched(self):
        handler = self.pm.on_event("MessageStatus")
        message = DummyMessage()
        status = 101
        args = (message, status)
        retvals = handler(*args)
        self.assertItemsEqual(args, retvals)

    def test_handler_call_without_arguments_returns_empty_tuple(self):
        handler = self.pm.on_event("CallHistory")
        self.assertEqual(tuple(), handler())

    def test_register_unknown_event_handler(self):
        def handler(arg1, arg2):
            return arg1, arg2
        event = "SomeEvent"
        registered = self.pm.register_event_handler(event, handler)
        # Method returns None for unknown events.
        self.failUnlessEqual(registered, None)

        def handler(message, status):
            return message, status
        event = "MessageStatus"
        registered = self.pm.register_event_handler(event, handler)
        # Method returns successfully registered handler.
        self.assertEqual(registered, handler)

        handlers = []
        for handler, priority, whitelist in self.pm.handlers("MessageStatus"):
            handlers.append((handler.__name__, priority, whitelist))
        expected = [
            ("on_message_status", 1, ["some_chat"]),
            ("on_message_status", 42, ["chat"]),
            ("on_message_status", 0, None),
            ("handler", 0, None),
        ]
        self.assertItemsEqual(handlers, expected)


class ChatIsWhitelistedTestCase(unittest.TestCase):
    def setUp(self):
        self.whitelist = [
            "#user1+/$user2=;0000000000000000",
            "0000000000000000",
            "2222222222222222",
            "#user1+/$user2=",
        ]

    def test_chat_is_whitelisted_by_name_with_id(self):
        chat_name1 = "#user1+/$user2=;0000000000000000"
        self.assertTrue(chat_is_whitelisted(chat_name1, self.whitelist))
        chat_name2 = "#user1+/$user2=;XXXXXXXXXXXXXXXX"
        self.assertTrue(chat_is_whitelisted(chat_name2, self.whitelist))

    def test_chat_is_whitelisted_by_name(self):
        chat_name1 = "#user1+/$user2=;XXXXXXXXXXXXXXXX"
        self.assertTrue(chat_is_whitelisted(chat_name1, self.whitelist))
        chat_name2 = "#user3*/$user4%;XXXXXXXXXXXXXXXX"
        self.assertFalse(chat_is_whitelisted(chat_name2, self.whitelist))

    def test_chat_is_whitelisted_by_id(self):
        chat_name1 = "#user3*/$user4%;0000000000000000"
        self.assertTrue(chat_is_whitelisted(chat_name1, self.whitelist))
        chat_name2 = "#user3*/$user4%;XXXXXXXXXXXXXXXX"
        self.assertFalse(chat_is_whitelisted(chat_name2, self.whitelist))
        chat_name3 = "#user3*/$user4%;2222222222222222"
        self.assertTrue(chat_is_whitelisted(chat_name3, self.whitelist))


class CamelCaseToUnderscoresTestCase(unittest.TestCase):
    def test_convert(self):
        s = "1MessageStatusHERPDerpDurr_123"
        expected = "1_message_status_herpderp_durr_123"
        self.assertEqual(expected, camelcase_to_underscores(s))


if __name__ == "__main__":
    unittest.main()
