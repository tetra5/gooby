#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`application` --- Generic third-party Skype application
============================================================
"""


__docformat__ = "restructuredtext en"


import sys

import Skype4Py
from Skype4Py.enums import apiAttachSuccess


class Application(object):
    """
    Skype third-party application. This class takes care of starting Skype
    client window, attaching to it, and so on. Essentially it behaves like
    a Skype plugin. Which is what it is.

    .. seealso::
        :mod:`gooby` - Gooby module for more advanced usage.
    """

    def __init__(self, app_name=None):
        """
        Initializes Skype4Py library.

        .. note::
            Skype4Py uses X11 transport for inter-process communication
            instead of default D-Bus one, as the D-Bus IPC is really unstable
            and causes frequent segmentation faults.

        :param app_name: optional application name that will be shown on Skype
            API Access Control settings page. **Default:** class name.
            POSIX only
        :type app_name: `unicode`
        """

        self._app_name = app_name or self.__class__.__name__

        if any(sys.platform.startswith(p) for p in ("linux", "darwin")):
            self._skype = Skype4Py.Skype(Transport="x11")
        else:
            self._skype = Skype4Py.Skype()

        self._skype.FriendlyName = self._app_name

    def attach_to_skype(self, protocol=8, wait=True):
        """
        Attach to Skype window.

        :param protocol: Skype protocol version (8 is the highest one)
        :type protocol: `int`. **Default:** 8

        :param wait: If set to False, blocks forever until the connection is
            established. Otherwise, timeouts after the `Timeout`
        :type wait: `bool`

        :raises: :class:`Skype4Py.skype.SkypeAPIError`
        """

        try:
            self._skype.Attach(Protocol=protocol, Wait=wait)
        except:
            raise

    def start_skype(self, minimized=True, nosplash=True):
        try:
            self._skype.Client.Start(Minimized=minimized, Nosplash=nosplash)
        except:
            raise

    def is_attached(self):
        return self._skype.AttachmentStatus == apiAttachSuccess
