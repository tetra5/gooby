#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
@author: tetra5 <tetra5dotorg@gmail.com>
"""


__version__ = "2012.1"

__all__ = ["Application", ]


import os
import sys
import socket

socket.setdefaulttimeout(2)

import Skype4Py

from plugin import Plugin
from utils import camelcase_to_underscore


class Application(object):
    """
    Skype bot application wireframe.
    """
    def __init__(self):
        self._skype = None
        self._plugins_dir = str()
        self._plugin_modules = list()
        self._plugins = list()
        self._plugin_objects = list()

    def get_plugins_dir(self):
        return self._plugins_dir

    def set_plugins_dir(self, value):
        self._plugins_dir = value
        if value not in sys.path:
            sys.path.append(value)

    def get_plugin_modules(self):
        return self._plugin_modules

    def get_plugins(self):
        if not self._plugins:
            self.init_plugins()

        return self._plugins

    def get_plugin_objects(self):
        return self._plugin_objects

    def get_skype(self):
        return self._skype

    plugins_dir = property(get_plugins_dir, set_plugins_dir)

    plugin_modules = property(get_plugin_modules)

    plugins = property(get_plugins)

    plugin_objects = property(get_plugin_objects)

    skype = property(get_skype)

    def attach_to_skype(self):
        try:
            self._skype = Skype4Py.Skype()
            self._skype.Attach()
        except:
            raise

    def init_plugins(self):
        self._plugins = list()

        if not self._plugins_dir:
            raise Exception("Plugins directory has not been set.")

        if not self._plugins_dir in sys.path:
            sys.path.append(self._plugins_dir)

        for mod_name in self.list_plugin_modules():
            imported = self.import_plugin_module(mod_name)
            plugin_classes = self.list_plugin_classes(imported)
            self._plugins.extend(plugin_classes)

    def list_plugin_modules(self):
        self._plugin_modules = list()

        for mod_path in os.listdir(self._plugins_dir):
            if mod_path.endswith(".py") and "__init__" not in mod_path:
                mod_name = mod_path[:-3]
                self._plugin_modules.append(mod_name)

        return self._plugin_modules

    def import_plugin_module(self, mod_name):
        return __import__(mod_name)

    def list_plugin_classes(self, module):
        plugin_classes = list()

        for entity in dir(module):

            attribute = getattr(module, entity)

            # Ensures that entity is of a class object and that class
            # subclasses base Plugin class.
            if isinstance(attribute, type) and issubclass(attribute, Plugin):
                # Really dirty hack here. We have to skip base Plugin classes
                # from dynamically imported module, so they won't load as
                # plugins, therefore we will convert class object name to
                # unicode string like for example "<class 'plugin.Plugin'>",
                # and see if it contains certain substring in it.
                # If it does then that class is considered to be a base one
                # and is getting skipped.
                # It works but there should be much better way of doing that.
                # TODO: Think of sane workaround!
                if unicode(attribute).startswith("<class 'plugin."):
                    continue

                plugin_classes.append(attribute)

        return plugin_classes

    def register_plugin(self, cls):
        """
        Complete Skype events list:

        ['ApplicationConnecting', 'ApplicationDatagram',
         'ApplicationReceiving', 'ApplicationSending',
         'ApplicationStreams', 'AsyncSearchUsersFinished',
         'AttachmentStatus', 'AutoAway', 'CallDtmfReceived',
         'CallHistory', 'CallInputStatusChanged', 'CallSeenStatusChanged',
         'CallStatus', 'CallTransferStatusChanged',
         'CallVideoReceiveStatusChanged', 'CallVideoSendStatusChanged',
         'CallVideoStatusChanged', 'ChatMemberRoleChanged',
         'ChatMembersChanged', 'ChatWindowState', 'ClientWindowState',
         'Command', 'ConnectionStatus', 'ContactsFocused', 'Error',
         'FileTransferStatusChanged', 'GroupDeleted', 'GroupExpanded',
         'GroupUsers', 'GroupVisible', 'MessageHistory', 'MessageStatus',
         'Mute', 'Notify', 'OnlineStatus', 'PluginEventClicked',
         'PluginMenuItemClicked', 'Reply', 'SilentModeStatusChanged',
         'SmsMessageStatusChanged', 'SmsTargetStatusChanged',
         'UserAuthorizationRequestReceived', 'UserMood', 'UserStatus',
         'VoicemailStatus', 'WallpaperChanged', ]
        """
        for plugincls in self._plugins:
            if plugincls is not cls:
                continue

            pluginobj = plugincls(parent=self)

            # Searches for Skype events, generates callback (event handler)
            # name, binds valid callbacks to a corresponding events for
            # each plugin.
            for skype_event in dir(Skype4Py.skype.SkypeEvents):
                if skype_event.startswith("__"):
                    continue

                callback_name = "on_" + camelcase_to_underscore(skype_event)

                try:
                    callback = getattr(pluginobj, callback_name)
                except AttributeError:
                    pass
                else:
                    if callable(callback):
                        self.skype.RegisterEventHandler(skype_event, callback)

            self._plugin_objects.append(pluginobj)

            return pluginobj
