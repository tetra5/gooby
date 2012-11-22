#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`markasread`
=================
"""


__docformat__ = "restructuredtext en"


from Skype4Py.enums import cmsReceived

from plugin import Plugin


class MarkAsRead(Plugin):
    def __init__(self, parent):
        super(MarkAsRead, self).__init__(parent)

    def on_message_status(self, message, status):
        if not status == cmsReceived:
            return

        message.MarkAsSeen()
