#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`youtubeurlparser` --- Threaded conference poll plugin
===========================================================
"""


# FIXME: this module is obsolete and has to be rewritten.


from __future__ import unicode_literals


__docformat__ = "restructuredtext en"


import re
from threading import Timer

from plugin import ChatCommandPlugin


class Poll(ChatCommandPlugin):
    def __init__(self, parent):
        super(Poll, self).__init__(parent)
        self._commands = {
            "!poll": self.on_poll_command,
            "!vote": self.on_vote_command,
        }
        self._polls = {}

    def stop_poll(self, chat):
        chat_name = chat.Name
        if chat_name in self._polls:
            poll = self._polls.get(chat_name)
            yes_count = sum(poll.get("voters").itervalues())
            no_count = len(poll.get("voters")) - yes_count
            line = u"Poll has ended. Results for '%s' by %s\nyes: %d | no: %d"
            chat.SendMessage(line % (poll.get("subject"), poll.get("owner"),
                                     yes_count, no_count))
            del self._polls[chat_name]

    def on_poll_command(self, message):
        """Voting system.
        To start a new poll type: !poll start <minutes> <subject>
        Vote time is limited to 10 minutes, with a minimum of 1.
        To prematurely stop currently running poll type: !poll stop
        Poll can only be stopped by the same person who started it.
        To show currently running poll type: !poll show
        """

        chat = message.Chat
        chat_name = message.ChatName

        pattern = ur"!poll\s+(start|show|stop)(?:\s+(\d{1,2})\s+(.*))?"
        match = re.match(pattern, message.Body, re.UNICODE)

        if not match:
            chat.SendMessage(self.on_poll_command.__doc__)
            return

        action = match.group(1)

        if action == "start":
            if not match.group(2) or not match.group(3):
                chat.SendMessage(self.on_poll_command.__doc__)
                return
            vote_time = int(match.group(2))
            if vote_time <= 0:
                vote_time = 1
            elif vote_time > 10:
                vote_time = 10

            if chat_name in self._polls:
                chat.SendMessage("Poll is already running")
                return

            thread = Timer(vote_time * 60, self.stop_poll, args=(chat,))
            poll = {
                "voters": {},
                "owner": message.FromHandle,
                "subject": match.group(3),
                "thread": thread,
                }

            thread.daemon = True
            thread.start()
            self._polls.update({chat_name: poll})
            line = (u"%s has started a new poll for next %d minute(s):\n'%s'\n"
                    "Type '!vote yes' or '!vote no' to participate")

            chat.SendMessage(line % (message.FromHandle, vote_time,
                                     match.group(3)))

        elif action == "stop":
            poll = self._polls.get(chat_name)

            if not poll:
                chat.SendMessage("No active polls")
                return

            if poll.get("owner") != message.FromHandle:
                chat.SendMessage("You are not allowed to stop this poll")
                return

            self.stop_poll(chat)

        elif action == "show":
            poll = self._polls.get(chat_name)

            if not poll:
                chat.SendMessage("No active polls")
                return

            chat.SendMessage("Current poll is '%(subject)s' by %(owner)s" %
                             self._polls.get(chat_name))

    def on_vote_command(self, message):
        """Vote in a currently running Poll. !vote <yes|no>"""
        chat = message.Chat
        chat_name = message.ChatName

        if chat_name not in self._polls:
            chat.SendMessage("No active polls")
            return

        if message.FromHandle in self._polls.get(chat_name).get("voters"):
            chat.SendMessage("%s, you have already voted this time" %
                             message.FromHandle)
            return

        if message.Body.startswith("!vote yes"):
            vote = True
        elif message.Body.startswith("!vote no"):
            vote = False

        voter = {message.FromHandle: vote}
        self._polls.get(chat_name).get("voters").update(voter)
