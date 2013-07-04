#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`markasseen`
=================
"""


__docformat__ = "restructuredtext en"


from Skype4Py.enums import cmsReceived

from plugin import Plugin


class MarkAsSeen(Plugin):
    def on_message_status(self, message, status):
        if status == cmsReceived:
            message.MarkAsSeen()
