#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`test_dispatcher` --- Dispatcher unit tests
================================================
"""


from __future__ import unicode_literals


__docformat__ = "restructuredtext en"


import unittest

import tests
from gooby.dispatcher import dispatcher, _id


SIGNAL = "test_signal"
ANOTHER_SIGNAL = "herp derp"


class DispatcherTestCase(unittest.TestCase):
    def tearDown(self):
        dispatcher.connections.clear()

    def test_connection(self):
        def receiver():
            pass

        receiver_id = _id(receiver)
        dispatcher.connect(receiver, SIGNAL)
        receivers = dispatcher.connections.get(SIGNAL)
        self.assertEqual(len(receivers), 1)
        r_id, _ = receivers[-1]
        self.assertEqual(r_id, receiver_id)

    def test_multiple_connections(self):
        def receiver():
            pass

        def another_receiver():
            pass

        class Test(object):
            def __init__(self):
                dispatcher.connect(self.test, ANOTHER_SIGNAL, False)

            def test(self):
                pass

        Test()

        dispatcher.connect(receiver, SIGNAL)
        dispatcher.connect(another_receiver, SIGNAL)
        self.assertEqual(len(dispatcher.connections), 2)
        self.assertEqual(len(dispatcher.connections.get(SIGNAL)), 2)
        self.assertEqual(len(dispatcher.connections.get(ANOTHER_SIGNAL)), 1)

    def test_disconnect(self):
        def receiver():
            pass

        def another_receiver():
            pass

        another_receiver_id = _id(another_receiver)
        dispatcher.connect(receiver, SIGNAL)
        dispatcher.connect(another_receiver, SIGNAL)
        dispatcher.disconnect(receiver, SIGNAL)
        receivers = dispatcher.connections.get(SIGNAL)
        r_id, _ = receivers[-1]
        self.assertEqual(r_id, another_receiver_id)

    def test_send(self):
        def receiver(*args, **kwargs):
            return "derp", args, kwargs

        def another_receiver(*args, **kwargs):
            return 42

        class Test(object):
            def __init__(self):
                dispatcher.connect(self.test, SIGNAL, False)

            def test(self, *args, **kwargs):
                return "works!", args[0]

        Test()

        dispatcher.connect(receiver, SIGNAL)
        dispatcher.connect(another_receiver, SIGNAL)
        responses = dispatcher.send(SIGNAL, 42, herp="derp")
        expected = [
            ("works!", 42),
            42,
            ("derp", (42,), {'herp': u'derp'}),
        ]
        self.assertItemsEqual(expected, responses)


if __name__ == "__main__":
    unittest.main()
