#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
@author: tetra5 <tetra5dotorg@gmail.com>
"""


# FIXME: this module is obsolete and has to be rewritten.


__version__ = "2012.1"


from plugin import ChatCommandPlugin


class Maintenance(ChatCommandPlugin):
    """
    Handles bot maintenance commands: "!version", "!help", "!plugins",
    "!commands"
    """
    def __init__(self, parent):
        super(Maintenance, self).__init__(parent)
        self._commands = {
            "!version": self.on_version_command,
            "!commands": self.on_commands_command,
            "!plugins": self.on_plugins_command,
            "!help": self.on_help_command,
            }

    def on_help_command(self, message):
        """Displays help information."""
        chat = message.Chat
        output = "Type '!commands' to display a list of supported commands"
        chat.SendMessage(output)

    def on_plugins_command(self, message):
        """Retrieves list of all registered plugins."""
        chat = message.Chat

        output = list()

        for pluginobj in self.parent.plugin_objects:
            output.append(pluginobj.__class__.__name__)

        chat.SendMessage("Registered plugins: " + ", ".join(output))

    def on_commands_command(self, message):
        """Retrieves list of all available commands from all successfully
        registered plugins."""
        chat = message.Chat

        output = ["Supported commands:", ]

        for pluginobj in self.parent.plugin_objects:
            if not hasattr(pluginobj, "commands"):
                continue

            for command, callback in pluginobj.commands.iteritems():
                print command, callback
                command_doc = callback.__doc__
                if command_doc is not None:
                    command_doc = command_doc.strip()
                else:
                    command_doc = "No help available."

                output.append("%s: %s" % (command, command_doc))

        chat.SendMessage("\n".join(output))

    def on_version_command(self, message):
        """Displays bot version."""
        from gooby import __version__ as gooby_version
        chat = message.Chat
        chat.SendMessage("Gooby version: '%s'" % gooby_version)
