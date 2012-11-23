#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
@author: tetra5 <tetra5dotorg@gmail.com>
"""


__all__ = ["Application", ]


import os
import sys
import socket

socket.setdefaulttimeout(3)

import Skype4Py

import plugin
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
            self._skype.FriendlyName = "Gooby"
            self._skype.Attach(Protocol=8)
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

    def is_attached(self):
        return self.skype.AttachmentStatus == 0

    def import_plugin_module(self, mod_name):
        return __import__(mod_name)

    def list_plugin_classes(self, module):
        plugin_classes = list()

        # Here we're trying to search and find plugin classes inside a
        # specified module. To do that properly we have to exclude base plugin
        # classes first.
        for entity in set(dir(module)).difference(dir(plugin)):
            attr = getattr(module, entity)
            # Checks if current attribute is a class which subclasses
            # the base one.
            if isinstance(attr, type) and issubclass(attr, plugin.Plugin):
                plugin_classes.append(attr)

        return plugin_classes

    def register_plugin(self, plugincls):
        """Complete Skype events list:

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
        if plugincls not in set(self._plugins):
            raise Exception("Invalid plugin class %s" % plugincls)

        pluginobj = plugincls(parent=self)

        # Set of dispensable attributes.
        s = set(dir(type)).union(["__weakref__"])

        # TODO: this could probably use some optimization.
        for event in set(dir(Skype4Py.skype.SkypeEvents)).difference(s):
            handler_name = "on_" + camelcase_to_underscore(event)
            try:
                handler = getattr(pluginobj, handler_name)
            except AttributeError:
                pass
            else:
                if callable(handler):
                    self.skype.RegisterEventHandler(event, handler)

        self._plugin_objects.append(pluginobj)
        return pluginobj
