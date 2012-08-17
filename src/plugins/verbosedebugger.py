#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
Created on 09.08.2012

@author: tetra5 <tetra5dotorg@gmail.com>
"""


__version__ = "0.1.0"


from plugin import Plugin


class VerboseDebugger(Plugin):
    def on_message_status(self, message, status):
        self._logger.debug("Message received: %s, status: %s" %
                           (message, status))
