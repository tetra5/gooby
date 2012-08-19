#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
@author: tetra5 <tetra5dotorg@gmail.com>
"""


__all__ = ["Plugin", "ConferenceCommandPlugin", ]

__version__ = "2012.1"


import logging

from Skype4Py.enums import cmsReceived


"""This module contains base Plugin classes."""


class Plugin(object):
    """
    TODO: rewrite on_* methods docstrings.
    Right now they're almost entirely copy-pasted from Skype4Py documentation.
    """
    def __init__(self, parent):
        self._logger_name = self.__class__.__name__
        self._log_level = logging.DEBUG
        self._logger = None
        self._parent = parent

    def get_logger_name(self):
        return self._logger_name

    def set_logger_name(self, value):
        self._logger_name = value
        self.init_logging()

    def get_log_level(self):
        return self._log_level

    def set_log_level(self, value):
        self._log_level = value
        self.init_logging()

    def get_logger(self):
        return self._logger

    def get_parent(self):
        return self._parent

    def set_parent(self, value):
        self._parent = value

    parent = property(get_parent, set_parent)

    logger_name = property(get_logger_name, set_logger_name)

    logger = property(get_logger)

    log_level = property(get_log_level, set_log_level)

    def init_logging(self):
        self._logger = logging.getLogger(self._logger_name)
        self._logger.setLevel(self._log_level)
        self._logger.debug("Initializing logging facility ...")

    def on_message_status(self, message, status):
        """
        This event is caused by a change in chat message status.

        @param message: Skype4Py.chat.ChatMessage object.
        @param status: (Skype4Py.enums.cms*) new status of the chat message.
        """

    def on_online_status(self, user, status):
        """
        This event is caused by a change in the online status of a user.

        @param user: Skype4Py.user.User object.
        @param status: (Skype4Py.enums.ols*) new online status of the user.
        """

    def on_user_mood(self, user, mood_text):
        """
        This event is caused by a change in the mood text of the user.

        @param user: Skype4Py.user.User object
        @param mood_text: (unicode) new mood text.
        """

    def on_user_authorization_request_received(self, user):
        """
        This event occurs when user sends you an authorization request.

        @param user: Skype4Py.user.User object.
        """

    def on_call_status(self, call, status):
        """
        This event is caused by a change in call status.

        @param call: Skype4Py.call.Call object.
        @param status: (Skype4Py.enums.cls*) new status of the call.
        """

    def on_call_seen_status_changed(self, call, seen):
        """
        This event occurs when the seen status of a call changes.

        See Skype4Py.call.Call.Seen.

        @param call: Skype4Py.call.Call object.
        @param seen: (bool) True if call was seen.
        """

    def on_call_input_status_changed(self, call, active):
        """
        This event is caused by a change in the Call voice input status
        change.

        @param call: Skype4Py.call.Call object.
        @param active: (bool) new voice input status (active when True).
        """

    def on_call_transfer_status_changed(self, call, status):
        """
        This event occurs when a call transfer status changes.

        @param call: Skype4Py.call.Call object.
        @param status: (Skype4Py.enums.cls*) new status of the call transfer.
        """

    def on_call_dtfm_received(self, call, code):
        """
        This event is caused by a call DTMF event.

        @param call: Skype4Py.call.Call object.
        @param code: received DTMF code.
        """

    def on_call_video_status_changed(self, call, status):
        """
        This event occurs when a call video status changes.

        @param call: Skype4Py.call.Call object.
        @param status: (Skype4Py.enums.cvs*) new video status of the call.
        """

    def on_call_video_send_status_changed(self, call, status):
        """
        This event occurs when a call video send status changes.

        @param call: Skype4Py.call.Call object.
        @param status: (Skype4Py.enums.vss*) new video send status of the call.
        """

    def on_call_video_receive_status_changed(self, call, status):
        """
        This event occurs when a call video receive status changes.

        @param call: Skype4Py.call.Call object.
        @param status: (Skype4Py.enums.vss*) new video receive status of the
            call.
        """

    def on_chat_members_changed(self, chat, members):
        """
        This event occurs when a list of chat members change.

        @param chat: Skype4Py.chat.Chat object.
        @param members: Skype4Py.user.UserCollection object - chat members.
        """

    def on_chat_window_state(self, chat, state):
        """
        This event occurs when chat window is opened or closed.

        @param chat: Skype4Py.chat.Chat object
        @param state: (bool) True if the window was opened or False if closed.
        """

    def on_chat_member_role_changed(self, member, role):
        """
        This event occurs when a chat member role changes.

        @param member: Skype4Py.chat.ChatMember object
        @param role: (Skype4Py.enums.chatMemberRole*) new member role.
        """

    def on_application_connecting(self, app, users):
        """
        This event is triggered when list of users connecting to an
        application changes.

        @param app: Skype4Py.application.Application object.
        @param users: Skype4Py.user.UserCollection object.
        """

    def on_application_streams(self, app, streams):
        """
        This event is triggered when list of application streams changes.

        @param app: Skype4Py.application.Application object.
        @param streams: Skype4Py.application.ApplicationStreamCollection:
            stream colleciton.
        """

    def on_application_datagram(self, app, stream, text):
        """
        This event is caused by the arrival of an application datagram.

        @param app: Skype4Py.application.Application object.
        @param stream: Skype4Py.application.ApplicationStream object that
            received the datagram.
        @param text: (unicode) datagram text.
        """

    def on_application_sending(self, app, streams):
        """
        This event is triggered when list of application sending streams
        changes.

        @param app: Skype4Py.application.Application object.
        @param streams: Skype4Py.application.ApplicationStreamCollection:
            stream collection.
        """

    def on_application_receiving(self, app, streams):
        """
        This event is triggered when list of application receiving streams
        changes.

        @param app: Skype4Py.application.Application object.
        @param streams: Skype4Py.application.ApplicationStreamCollection:
            stream collection.
        """

    def on_group_visible(self, group, visible):
        """
        This event is caused by a user hiding/showing a group in the
        contacts tab.

        @param group: Skype4Py.group.Group object.
        @param visible: (bool) tells if group is visible or not.
        """

    def on_group_expanded(self, group, expanded):
        """
        This event is caused by a user expanding or collapsing a group in
        the contacts tab.

        @param group: Skype4Py.group.Group object.
        @param expanded: (bool) tells if group is expanded (True) or collapsed
            (False).
        """

    def on_group_users(self, group, count):
        """
        This event is caused by a change in a contact group members.

        @param group: Skype4Py.group.Group object.
        @param count: (int) number of group members.

        This event is different from its Skype4COM equivalent in that the
        second parameter is number of users instead of
        Skype4Py.user.UserCollection object. This object may be obtained using
        Skype4Py.group.Group.Users property.
        """

    def on_sms_message_status_changed(self, message, status):
        """
        This event is caused by a change in the SMS message status.

        @param message: Skype4Py.sms.SmsMessage object.
        @param status: (Skype4Py.enums.smsMessageStatus*) new status of the
            SMS message.
        """

    def on_file_transfer_status_changed(self, transfer, status):
        """
        This event occurs when a file transfer status changes.

        @param transfer: Skype4Py.filetransfer.FileTransfer object.
        @param status: (Skype4Py.enums.fileTransferStatus*) new status of the
            file transfer.
        """

    def on_async_search_users_finished(self, cookie, users):
        """
        This event occurs when an asynchronous search is completed.

        @param cookie: (int) Search identifier as returned by
            Skype4Py.skype.Skype.AsyncSearchUsers.
        @param users: Skype4Py.user.UserCollection object.
        """

    def on_attachment_status(self, status):
        """
        This event is caused by a change in the status of an
        attachment to the Skype API.

        @param status: (Skype4Py.enums.apiAttach) new status.
        """

    def on_auto_away(self, automatic):
        """
        This event is caused by a change of auto away status.

        @param automatic: (bool) new auto away status.
        """

    def on_call_history(self):
        """
        This event is caused by a change in call history.
        """

    def on_client_window_state(self, state):
        """
        This event occurs when the state of the client window changes.

        @param state: (Skype4Py.enums.wnd*) new window state.
        """

    def on_command(self, command):
        """
        This event is triggered when a command is sent to the Skype API.

        @param command: Skype4Py.api.Command object.
        """

    def on_connection_status(self, status):
        """
        This event is caused by a connection status change.

        @param status: (Skype4Py.enums.con*) new connection status.
        """

    def on_contacts_focused(self, username):
        """
        This event is caused by a change in contacts focus.

        @param username: (str) Name of the user that was focused or empty
            string if focus was lost.
        """

    def error(self, command, number, description):
        """
        This event is triggered when an error occurs during execution
        of an API command.

        @param command: Skype4Py.api.Command object that caused the error.
        @param number: (int) error number returned by Skype API.
        @param description: (unicode) description of the error.
        """

    def on_group_deleted(self, group_id):
        """
        This event is caused by a user deleting a custom contact group.

        @param group_id: (int) ID of the deleted group.
        """

    def on_message_history(self, username):
        """
        This event is caused by a change in message history.

        @param username: (str) name of the user whose message history changed.
        """

    def on_mute(self, mute):
        """
        This event is caused by a change in mute status.

        @param mute: (bool) new mute status.
        """

    def on_notify(self, notification):
        """
        This event is triggered whenever Skype client sends a notification.

        Use this even only if there is no dedicated one.

        @param notification: (unicode) notification string.
        """

    def on_plugin_event_clicked(self, event):
        """
        This event occurs when a user clicks on a plug-in event.

        @param event: Skype4Py.client.PluginEvent object.
        """

    def on_plugin_menu_item_clicked(self, menu_item, users, plugin_context,
                                    context_id):
        """
        This event occurs when a user clicks on a plug-in menu item.

        See Skype4Py.client.PluginMenuItem.

        @param menu_item: Skype4Py.PluginMenuItem object.
        @param users: Skype4Py.user.UserCollection object. Users this item
            refers to.
        @param plugin_context: (unicode) plugin context.
        @param context_id: (str or int) context ID. Chat name for chat context
            or Call ID for call context.
        """

    def on_reply(self, command):
        """
        This event is triggered when the API replies to a command object.

        @param command: Skype4Py.api.Command object.
        """

    def on_silent_mode_status_changed(self, silent):
        """
        This event occurs when a silent mode is switched off.

        @param silent: (bool) Skype client silent status.
        """

    def on_sms_target_status_changed(self, target, status):
        """
        This event is caused by a change in the SMS target status.

        @param target: Skype4Py.sms.SmsTarget object
        @param status: (Skype4Py.enums.smsTargetStatus*) new status of the SMS
            target.
        """

    def on_user_status(self, status):
        """
        This event is caused by a user status change.

        @param status: (Skype4Py.enums.cus*) new user status.
        """

    def on_voicemail_status(self, mail, status):
        """
        This event is caused by a change in voicemail status.

        @param mail: Skype4Py.voicemail.VoiceMail object.
        @param status: (Skype4Py.enums.vms*) new status of the voicemail.
        """

    def on_wallpaper_changed(self, path):
        """
        This event occurs when client wallpaper changes.

        @param path: (str) path to new wallpaper bitmap.
        """


class ConferenceCommandPlugin(Plugin):
    def __init__(self, parent):
        """
        TODO: not sure if name mangling is nescessary here. It's better to
        just stick to manual callback assignments. Probably in future but
        oh well.

        Please keep in mind that if your plugin is triggered by a chat
        command, it's better to use "self._commands" dictionary.
        Note that you are free to modify this behaviour in the way you like.
        Check more plugins derived from this class for more explaination.

        This class serves as "framework-ish" environment for common tasks
        regarding receiving and sending Skype conference messages, but you are
        free to inherit base Plugin class instead.
        """
        super(ConferenceCommandPlugin, self).__init__(parent)

        # Example plugin dictionary, where keys are trigger strings and values
        # are callback methods:
        # self._commands = {
        #     "!foo": self.on_foo_command,
        #     "!bar": self.on_bar_command,
        #     }
        # Every callback methods accepts 1 argument which is
        # Skype4Py.chat.ChatMessage object.
        self._commands = dict()

    def get_commands(self):
        return self._commands

    def set_commands(self, value):
        self._commands = value

    commands = property(get_commands, set_commands)

    def on_message_status(self, message, status):
        if status == cmsReceived:
            for command, callback in self._commands.iteritems():
                if not message.Body.startswith(command):
                    continue
                if callable(callback):
                    callback(message)
