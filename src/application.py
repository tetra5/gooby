#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`application` --- Generic third-party Skype application
============================================================
"""


__docformat__ = "restructuredtext en"


import sys

import Skype4Py


class Application(object):
    """
    Skype third-party application. This class takes care of starting Skype
    client window, attaching to it, and so on. Essentially it behaves like
    a Skype plugin. Which is what it is.

    ..seealso::
        :mod:`gooby` - Gooby module for more advanced usage.
    """

    def __init__(self, app_name=None):
        """
        Initializes Skype4Py library.

        ..note::
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

    def attach_to_skype(self):
        try:
            self._skype.Attach(Protocol=8)
        except:
            raise

    def start_skype(self):
        try:
            self._skype.Client.Start(Minimized=True, Nosplash=True)
        except:
            raise

    def is_attached(self):
        return self._skype.AttachmentStatus == 0
