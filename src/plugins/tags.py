'''
Created on 24 aug 2012

@author: gleyur
'''

__version__ = "2012.1"

from plugin import ChatCommandPlugin
from Skype4Py.enums import cmsSent

class TagsManager(ChatCommandPlugin):
    '''
    classdocs
    '''
    tag_separator = "[x]"
    tags = []

    def __init__(self, parent):
            super(TagsManager, self).__init__(parent)
            self._commands = {
                self.tag_separator: self.on_tag_command,
                }
            
        
    def on_tag_command(self, message):
        strMsg = str(message.Body)
        newTags = strMsg.split(self.tag_separator)
        for tag in newTags:
            self._logger.debug(tag)
            tag = str(tag).strip()
        newTags.pop() # Remove all after tags
        self.tags.extend(newTags)
        for tag in self.tags:
            self._logger.debug("All tags: " + tag)
        #chat = message.Chat
        #chat.SendMessage("Added")
            
    def on_message_status(self, message, status):
        super(TagsManager, self).on_message_status(message, status)
        if status == cmsSent:
            strMessage = str(message.Body)
            for command, callback in self._commands.iteritems():
                if strMessage.find(self.tag_separator) < 0:
                    self._logger.debug("we are here")
                    continue
                if callable(callback):
                    callback(message)
        