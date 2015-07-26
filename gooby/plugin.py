#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`plugin` --- Base plugin classes collection
================================================
"""


from __future__ import unicode_literals


__docformat__ = "restructuredtext en"


# TODO: Spam protection system.


import logging

from Skype4Py.enums import cmsReceived

import cache


__all__ = [
    "Plugin",
    "ChatCommandPlugin",
]


DEFAULT_PLUGIN_CONFIG = {
    "priority": 0,
    "whitelist": None,
}


class Plugin(object):
    """
    Base plugin class. Should be inherited by any other plugins. Contains
    different overloadable methods which are bound to corresponding Skype
    events, e.g.: :meth:`on_message_status` method binds to
    **OnMessageStatus** event.

    Complete events list:

    >>> import Skype4Py
    >>> s = set(dir(type)).union(["__weakref__"])
    >>> events = list(set(dir(Skype4Py.skype.SkypeEvents)).difference(s))

    >>> assert u"CallSeenStatusChanged" in events

    >>> assert u"ApplicationConnecting" in events

    >>> assert u"VoicemailStatus" in events

    >>> assert u"SmsMessageStatusChanged" in events

    >>> assert u"GroupUsers" in events

    >>> assert u"CallDtmfReceived" in events

    >>> assert u"UserAuthorizationRequestReceived" in events

    >>> assert u"ChatMembersChanged" in events

    >>> assert u"ApplicationSending" in events

    >>> assert u"WallpaperChanged" in events

    >>> assert u"Reply" in events

    >>> assert u"CallStatus" in events

    >>> assert u"CallVideoReceiveStatusChanged" in events

    >>> assert u"ApplicationReceiving" in events

    >>> assert u"PluginMenuItemClicked" in events

    >>> assert u"ChatWindowState" in events

    >>> assert u"ConnectionStatus" in events

    >>> assert u"ApplicationStreams" in events

    >>> assert u"SmsTargetStatusChanged" in events

    >>> assert u"CallVideoSendStatusChanged" in events

    >>> assert u"MessageStatus" in events

    >>> assert u"CallVideoStatusChanged" in events

    >>> assert u"PluginEventClicked" in events

    >>> assert u"ClientWindowState" in events

    >>> assert u"CallHistory" in events

    >>> assert u"CallInputStatusChanged" in events

    >>> assert u"AsyncSearchUsersFinished" in events

    >>> assert u"AttachmentStatus" in events

    >>> assert u"UserStatus" in events

    >>> assert u"GroupExpanded" in events

    >>> assert u"Command" in events

    >>> assert u"Error" in events

    >>> assert u"ChatMemberRoleChanged" in events

    >>> assert u"AutoAway" in events

    >>> assert u"ContactsFocused" in events

    >>> assert u"Mute" in events

    >>> assert u"OnlineStatus" in events

    >>> assert u"CallTransferStatusChanged" in events

    >>> assert u"MessageHistory" in events

    >>> assert u"ApplicationDatagram" in events

    >>> assert u"GroupVisible" in events

    >>> assert u"SilentModeStatusChanged" in events

    >>> assert u"Notify" in events

    >>> assert u"GroupDeleted" in events

    >>> assert u"UserMood" in events

    >>> assert u"FileTransferStatusChanged" in events

    .. seealso::
        ``plugins`` package for plugins derived from this class, e.g.:
        :class:`~youtubeurlparser.YouTubeURLParser`
    """

    def __init__(self, priority=0, whitelist=None, **kwargs):
        self._logger = self._init_logger()
        self._logger.debug("Logger initialized")
        self._cache = self._init_cache()
        self._logger.debug("Cache initialized")

        self.priority = priority
        self.whitelist = whitelist
        self.options = kwargs
        self.output = list()

    def _init_logger(self):
        self._logger_name = "Gooby.Plugin." + self.__class__.__name__
        return logging.getLogger(self._logger_name)

    def _init_cache(self):
        return cache.get_cache(self.__class__.__name__)

    def flush_output(self):
        output = self.output[:]
        self.output = list()
        return output

    def usage(self):
        return "No known usage for {0}".format(self.__class__.__name__)

    @property
    def logger(self):
        return self._logger

    @property
    def cache(self):
        return self._cache

    def on_message_status(self, message, status):
        """
        This event is caused by a change in chat message status.

        :param message: message object
        :type message: :class:`Skype4Py.chat.ChatMessage` object

        :param status: message status
        :type status: `string`; one of `Skype4Py.enums.cms*` constants
        """

    def on_online_status(self, user, status):
        """
        This event is caused by a change in the online status of a user.

        :param user: user object
        :type user: :class:`Skype4Py.user.User` object

        :param status: online status
        :type status: `string`; one of `Skype4Py.enums.ols*` constants
        """

    def on_user_mood(self, user, mood_text):
        """
        This event is caused by a change in the mood text of the user.

        :param user: user object
        :type user: :class:`Skype4Py.user.User` object

        :param mood_text: new mood text
        :type mood_text: `unicode`
        """

    def on_user_authorization_request_received(self, user):
        """
        This event occurs when user sends you an authorization request.

        :param user: user object
        :type user: :class:`Skype4Py.user.User` object
        """

    def on_call_status(self, call, status):
        """
        This event is caused by a change in call status.

        :param call: call object
        :type call: :class:`Skype4Py.call.Call` object

        :param status: new status of the call
        :type status: `string`; one of `Skype4Py.enums.cls*` constants
        """

    def on_call_seen_status_changed(self, call, seen):
        """
        This event occurs when the seen status of a call changes.

        .. seealso::

            :class:`Skype4Py.call.Call.Seen` documentation

        :param call: call object
        :type call: :class:`Skype4Py.call.Call` object

        :param seen: True if call was seen
        :type seen: `bool`
        """

    def on_call_input_status_changed(self, call, active):
        """
        This event is caused by a change in the Call voice input status.

        :param call: call object
        :type call: :class:`Skype4Py.call.Call` object

        :param active: new voice input status. Active when `True`
        :type active: `bool`
        """

    def on_call_transfer_status_changed(self, call, status):
        """
        This event occurs when a call transfer status changes.

        :param call: call object
        :type call: :class:`Skype4Py.call.Call` object

        :param status: new status of the call transfer
        :type status: `string`; one of `Skype4Py.enums.cls*` constants
        """

    def on_call_dtfm_received(self, call, code):
        """
        This event is caused by a call DTMF event.

        :param call: call object
        :type call: :class:`Skype4Py.call.Call` object

        :param code: received DTMF code
        :type code: `unicode`
        """

    def on_call_video_status_changed(self, call, status):
        """
        This event occurs when a call video status changes.

        :param call: call object
        :type call: :class:`Skype4Py.call.Call` object

        :param status: new video status of the call
        :type status: `string`; one of `Skype4Py.enums.cvs*` constants
        """

    def on_call_video_send_status_changed(self, call, status):
        """
        This event occurs when a call video send status changes.

        :param call: call object
        :type call: :class:`Skype4Py.call.Call` object

        :param status: new video send status of the call
        :type status: `string`; one of `Skype4Py.enums.vss*` constants
        """

    def on_call_video_receive_status_changed(self, call, status):
        """
        This event occurs when a call video receive status changes.

        :param call: call object
        :type call: :class:`Skype4Py.call.Call` object

        :param status: new video receive status of the call
        :type status: `string`; one of `Skype4Py.enums.vss*` constants
        """

    def on_chat_members_changed(self, chat, members):
        """
        This event occurs when a list of chat members change.

        :param chat: chat object
        :type chat: :class:`Skype4Py.chat.Chat` object

        :param members: chat members object
        :type members: :class:`Skype4Py.user.UserCollection` object
        """

    def on_chat_window_state(self, chat, state):
        """
        This event occurs when chat window is opened or closed.

        :param chat: chat object
        :type chat: :class:`Skype4Py.chat.Chat` object

        :param state: True or False whether the window was opened or closed
        :type state: `bool`
        """

    def on_chat_member_role_changed(self, member, role):
        """
        This event occurs when a chat member role changes.

        :param member: chat member object
        :type member: :class:`Skype4Py.chat.ChatMember` object

        :param role: new member role
        :type role: `string`; one of `Skype4Py.enums.chatMemberRole*` constants
        """

    def on_application_connecting(self, app, users):
        """
        This event is triggered when list of users connecting to an
        application changes.

        :param app: application object
        :type app: :class:`Skype4Py.application.Application` object

        :param users: user collection object
        :type users: :class:`Skype4Py.user.UserCollection` object
        """

    def on_application_streams(self, app, streams):
        """
        This event is triggered when list of application streams changes.

        :param app: application object
        :type app: :class:`Skype4Py.application.Application` object

        :param streams: stream collection object
        :type streams:
            :class:`Skype4Py.application.ApplicationStreamCollection` object
        """

    def on_application_datagram(self, app, stream, text):
        """
        This event is caused by the arrival of an application datagram.

        :param app: application object
        :type app: :class:`Skype4Py.application.Application` object

        :param stream: stream object that received the datagram
        :type stream: :class:`Skype4Py.application.ApplicationStream` object

        :param text: datagram text
        :type text: `unicode`
        """

    def on_application_sending(self, app, streams):
        """
        This event is triggered when list of application sending streams
        changes.

        :param app: application object
        :type app: :class:`Skype4Py.application.Application` object

        :param streams: stream collection object
        :type streams:
            :class:`Skype4Py.application.ApplicationStreamCollection` object
        """

    def on_application_receiving(self, app, streams):
        """
        This event is triggered when list of application receiving streams
        changes.

        :param app: application object
        :type app: :class:`Skype4Py.application.Application` object

        :param streams: stream collection object
        :type streams:
            :class:`Skype4Py.application.ApplicationStreamCollection` object
        """

    def on_group_visible(self, group, visible):
        """
        This event is caused by a user hiding/showing a group in the
        contacts tab.

        :param group: group object
        :type group: :class:`Skype4Py.group.Group` object

        :param visible: tells if group is visible or not
        :type visible: `bool`
        """

    def on_group_expanded(self, group, expanded):
        """
        This event is caused by a user expanding or collapsing a group in
        the contacts tab.

        :param group: group object
        :type group: :class:`Skype4Py.group.Group` object

        :param expanded: Tells if group is expanded or collapsed.
            ``True`` if group is expanded. ``False`` if group is collapsed.
        :type expanded: `bool`
        """

    def on_group_users(self, group, count):
        """
        This event is caused by a change in a contact group members.

        .. note::

            This event is different from its Skype4COM equivalent in that the
            second parameter is number of users instead of
            `Skype4Py.user.UserCollection` object. This object may be obtained
            using `Skype4Py.group.Group.Users` property.

        :param group: group object
        :type group: :class:`Skype4Py.group.Group` object

        :param count: number of group members
        :type count: `int`
        """

    def on_sms_message_status_changed(self, message, status):
        """
        This event is caused by a change in the SMS message status.

        :param message: SMS message object
        :type message: :class:`Skype4Py.sms.SmsMessage` object

        :param status: new status of the SMS message
        :type status: `string`; one of `Skype4Py.enums.smsMessageStatus*`
            constants
        """

    def on_file_transfer_status_changed(self, transfer, status):
        """
        This event occurs when a file transfer status changes.

        :param transfer: file transfer object
        :type transfer: :class:`Skype4Py.filetransfer.FileTransfer` object

        :param status: new status of the file transfer
        :type status: `string`; one of `Skype4Py.enums.fileTransferStatus*`
            constants
        """

    def on_async_search_users_finished(self, cookie, users):
        """
        This event occurs when an asynchronous search is completed.

        :param cookie: search identifier as returned by
            :meth:`Skype4Py.skype.Skype.AsyncSearchUsers()`
        :type cookie: `int`

        :param users: user collection object
        :type users: :class:`Skype4Py.user.UserCollection` object
        """

    def on_attachment_status(self, status):
        """
        This event is caused by a change in the status of an
        attachment to the Skype API.

        :param status: new attachment status
        :type status: `string`; one of `Skype4Py.enums.apiAttach*` constants
        """

    def on_auto_away(self, automatic):
        """
        This event is caused by a change of auto away status.

        :param automatic: new auto away status
        :type automatic: `bool`
        """

    def on_call_history(self):
        """
        This event is caused by a change in call history.
        """

    def on_client_window_state(self, state):
        """
        This event occurs when the state of the client window changes.

        :param state: new window state
        :type state: `string`; one of `Skype4Py.enums.wnd*` constants
        """

    def on_command(self, command):
        """
        This event is triggered when a command is sent to the Skype API.

        :param command: command object
        :type command: :class:`Skype4Py.api.Command` object
        """

    def on_connection_status(self, status):
        """
        This event is caused by a connection status change.

        :param status: new connection status
        :type status: `string`; one of `Skype4Py.enums.con*` constants
        """

    def on_contacts_focused(self, username):
        """
        This event is caused by a change in contacts focus.

        :param username: name of the user that was focused or empty string if
            focus was lost
        :type username: `str`
        """

    def on_error(self, command, number, description):
        """
        This event is triggered when an error occurs during execution
        of an API command.

        :param command: object that caused the error
        :type command: :class:`Skype4Py.api.Command` object

        :param number: error number returned by Skype API
        :type number: `int`

        :param description: description of the error
        :type description: `unicode`
        """

    def on_group_deleted(self, group_id):
        """
        This event is caused by a user deleting a custom contact group.

        :param group_id: ID of the deleted group
        :type group_id: `int`
        """

    def on_message_history(self, username):
        """
        This event is caused by a change in message history.

        :param username: name of the user whose message history changed
        :type username: `str`
        """

    def on_mute(self, mute):
        """
        This event is caused by a change in mute status.

        :param mute: new mute status
        :type mute: `bool`
        """

    def on_notify(self, notification):
        """
        This event is triggered whenever Skype client sends a notification.

        .. note::

            Use this only if there is no dedicated one.

        :param notification: notification string
        :type notification: `unicode`
        """

    def on_plugin_event_clicked(self, event):
        """
        This event occurs when a user clicks on a plug-in event.

        :param event: plugin event object
        :type event: :class:`Skype4Py.client.PluginEvent` object
        """

    def on_plugin_menu_item_clicked(self, menu_item, users, plugin_context,
                                    context_id):
        """
        This event occurs when a user clicks on a plug-in menu item.

        .. seealso::

            :class:`Skype4Py.client.PluginMenuItem` documentation.

        :param menu_item: plugin menu item object
        :type menu_item: :class:`Skype4Py.PluginMenuItem` object

        :param users: users collection object. Users this item refers to
        :type users: :class:`Skype4Py.user.UserCollection` object

        :param plugin_context: plugin context
        :type plugin_context: `unicode`

        :param context_id: context ID. Chat name for chat context or Call ID
            for call context.
        :type context_id: `str` or `int`
        """

    def on_reply(self, command):
        """
        This event is triggered when the API replies to a command object.

        :param command: command object
        :type command: :class:`Skype4Py.api.Command` object
        """

    def on_silent_mode_status_changed(self, silent):
        """
        This event occurs when a silent mode is switched off.

        :param silent: Skype client silent status
        :type silent: `bool`
        """

    def on_sms_target_status_changed(self, target, status):
        """
        This event is caused by a change in the SMS target status.

        :param target: SMS target object
        :type target: :class:`Skype4Py.sms.SmsTarget` object

        :param status: new status of the SMS target
        :type status: `string`; one of `Skype4Py.enums.smsTargetStatus*`
            constants
        """

    def on_user_status(self, status):
        """
        This event is caused by a user status change.

        :param status: new user status
        :type status: `string`; one of `Skype4Py.enums.cus*` constants
        """

    def on_voicemail_status(self, mail, status):
        """
        This event is caused by a change in voicemail status.

        :param mail: voice mail object
        :type mail: :class:`Skype4Py.voicemail.VoiceMail` object

        :param status: new status of the voice mail
        :type status: `string`; one of `Skype4Py.enums.vms*` constants
        """

    def on_wallpaper_changed(self, path):
        """
        This event occurs when client wallpaper changes.

        :param path: path to new wallpaper bitmap
        :type path: `str`
        """


class ChatCommandPlugin(Plugin):
    """
    This class serves as "framework-ish" environment for common tasks regarding
    receiving and sending Skype chat messages, but you are free to inherit base
    :class:`Plugin` class instead.

    While being as simple as possible, this class servers one purpose ---
    simplify the plugin development process, particulary those kinds which are
    to work with chat messages.

    Now, what it does: imagine someone types ``!mycommand`` message in chat,
    and you want to execute some kind of a function in response to that
    message.

    So basically everything you'll want to do is to write the following code:

    ::

        from plugin import ChatCommandPlugin
        from output import ChatMessage

        class MyPlugin(ChatCommandPlugin):
            def __init__(self, priority, whitelist, **kwargs):
                super(MyPlugin, self).__init__(priority, whitelist, **kwargs)

                self._commands = {
                    "!mycommand": self.on_my_command,
                    }

            def on_my_command(self, message):
                self.output.append(ChatMessage(message.Chat.Name, "herp derp"))

    The code above is pretty much self-explainatory:

    * inherit a base class
    * assign a ``self._commands`` `dict`, where keys are chat command triggers
      and values are callback methods
    * implement a callback method
    """

    def __init__(self, priority=0, whitelist=None, **kwargs):
        super(ChatCommandPlugin, self).__init__(priority, whitelist, **kwargs)
        self._commands = {}

    def on_message_status(self, message, status):
        """
        Overloaded :meth:`Plugin.on_message_status` method. There's no need to
        modify it.
        """

        if status == cmsReceived:
            for command, callback in self._commands.iteritems():
                if message.Body.lstrip().lower().startswith(command.lower()):
                    if callable(callback):
                        callback(message)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
