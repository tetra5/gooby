#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`dispatcher` --- Multi-consumer multi-producer dispatching mechanism
=========================================================================

A rather simple and straightforward implementation. Keeping things as
transparent as possible.

Based on heavily modified PyDispatcher code (BSD license).
http://pydispatcher.sourceforge.net/
See original license.txt for more details.

Usage
-----

    >>> from dispatcher import dispatcher
    >>> def receiver(*args, **kwargs):
    ...     return args, kwargs
    >>> def test(*args, **kwargs):
    ...     return 42

    >>> dispatcher.connect(receiver, "my signal")
    >>> dispatcher.connect(test, "my signal")
    >>> responses = dispatcher.send("my signal", 42, herp="derp")
    >>> responses
    [((42,), {'herp': u'derp'}), 42]
"""


from __future__ import unicode_literals


__docformat__ = "restructuredtext en"


import weakref
import threading


WEAKREF_TYPES = (weakref.ReferenceType,)


_id = lambda target: id(target)


class _Dispatcher(object):
    def __init__(self):
        self.connections = dict()
        self.lock = threading.Lock()

    def connect(self, receiver, signal, weak=True):
        lookup_id = _id(receiver)
        if weak:
            receiver = weakref.ref(receiver, self._remove_receiver)
        with self.lock:
            receivers = self.connections.setdefault(signal, list())
            for r_id, _ in receivers:
                if r_id == lookup_id:
                    break
            else:
                receivers.append((lookup_id, receiver))

    def disconnect(self, receiver, signal):
        lookup_id = _id(receiver)
        with self.lock:
            receivers = self.connections.get(signal)
            for index in xrange(len(receivers)):
                r_id, _ = receivers[index]
                if r_id == lookup_id:
                    del receivers[index]
                    break

    def send(self, signal, *args, **kwargs):
        responses = list()
        for receiver in self._real_receivers(signal):
            responses.append(receiver(*args, **kwargs))
        return responses

    def _real_receivers(self, signal):
        for r_id, receiver in self.connections.get(signal):
            if isinstance(receiver, WEAKREF_TYPES):
                receiver = receiver()
            yield receiver

    def _remove_receiver(self, receiver):
        with self.lock:
            to_remove = list()
            for signal, receivers in self.connections.iteritems():
                for r_id, r in receivers:
                    if r == receiver:
                        to_remove.append(r_id)
                for lookup_id in to_remove:
                    # Enumerate in reversed order to avoid index errors while
                    # deleting list elements.
                    last_index = len(receivers) - 1
                    for index, (r_id, _) in enumerate(reversed(receivers)):
                        if r_id == lookup_id:
                            del receivers[last_index - index]


dispatcher = _Dispatcher()


if __name__ == "__main__":
    import doctest
    doctest.testmod()
