# -*- coding: utf-8 -*-

'''
Created on 24 aug 2012

@author: gleyur
'''

__version__ = "2012.1"


from plugin import ChatCommandPlugin
from Skype4Py.enums import cmsReceived


class TagsManager(ChatCommandPlugin):
    tag_separator = u"[x]"
    tag_english = u"!tags"
    tag_russian = u"!жепки"

    tags_limit = 20
    tags = []

    def __init__(self, parent):
            super(TagsManager, self).__init__(parent)
            self._commands = {
                self.tag_separator: self.on_tag_command,
                self.tag_english: self.on_tag_display_command,
                self.tag_russian: self.on_tag_display_command,
                }

    #Сохраняет жепки в массив, не больше tags_limit штук (20)
    def on_tag_command(self, message):
        strMsg = message.Body
        newTags = strMsg.split(self.tag_separator)

        for index, tag in enumerate(newTags):
            newTags[index] = tag.strip()
        newTags.pop() # Убрать всё после жепок

        self.tags.extend(newTags) #добавить жепки в массив

        if len(self.tags) >= self.tags_limit:
            del self.tags[0:len(self.tags) - self.tags_limit]

        for tag in self.tags:
            self._logger.debug(u"All tags: " + tag) #показать жепки в консоль
        self.on_tag_display_command(message)

    def on_tag_display_command(self, message):
        tags_message = u""
        for tag in self.tags:
            tags_message += tag + u" [x] "
        chat = message.Chat
        #chat.SendMessage(tags_message)
        chat.SendMessage(u"Жепки: " + tags_message)

    def on_message_status(self, message, status):
        super(TagsManager, self).on_message_status(message, status)
        if status == cmsReceived:
            strMessage = message.Body
            for command, callback in self._commands.iteritems():
                if strMessage.find(command) < 0:
                    continue
                if callable(callback):
                    callback(message)
