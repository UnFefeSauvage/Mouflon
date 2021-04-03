import discord
import logging

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(name)-12.12s] [%(levelname)-5.5s]  %(message)s")
handler.setFormatter(logFormatter)
logger.addHandler(handler)

class ReactionListener:
    """Classe permettant de surveiller les réactions sur des messages donnés et d'éxécuter des callbacks"""
    # messages: {
    #   "0123456789": {
    #       "reactions": {
    #           "smiley": {
    #               "add_callbacks": function[],
    #               "rm_callbacks": function[]
    #           }
    #       }
    #    }
    # }
    #

    def __init__(self):
        self._messages: dict = {}
    
    def _add_message(self, msg_id: str):
        """Creates space for a new message"""
        if not msg_id in self._messages:
            self._messages[msg_id] = {
                "reactions": {}
            }
        else:
            raise ValueError("Tried to create space for an already existing message!")

    def _add_emoji_listener(self, msg_id: str, emoji: str):    
        """Creates space for emoji listeners"""
        if not emoji in self._messages[msg_id]["reactions"]:
            self._messages[msg_id]["reactions"][emoji] = {
                "add_callbacks": [],
                "rm_callbacks": []
            }
        else:
            raise ValueError("Tried to create space for an already existing listener!")


    def add_callbacks(self, msg_id: str, emoji: str, add_callbacks: list[callable], rm_callbacks: list[callable]):
        """Adds listeners to a message for a given emoji"""
        # Conversion of int for convenience
        if isinstance(msg_id, int):
            msg_id = str(msg_id)

        if not isinstance(msg_id, str):
            raise ValueError(f"Expected a message id but got a '{type(msg_id)}' instead!")
        
        if not isinstance(emoji, str):
            raise ValueError(f"Expected a stringified emoji but got a '{type(emoji)}' instead!")
        
        # If no reaction is yet associated to the message, create the structure
        if not msg_id in self._messages:
            self._add_message(msg_id)
        
        # If no listener is yet associated to the emoji, create the structure
        if not emoji in self._messages[msg_id]["reactions"]:
            self._add_emoji_listener(msg_id, emoji)

        for callback in add_callbacks:
            if not isinstance(callback, callable):
                raise ValueError("Expected a list of callables!")

        for callback in rm_callbacks:
            if not isinstance(callback, callable):
                raise ValueError("Expected a list of callables!")
        
        for callback in add_callbacks:
            self._messages[msg_id]["reactions"][emoji]["add_callbacks"].append(callback)
        
        for callback in rm_callbacks:
            self._messages[msg_id]["reactions"][emoji]["add_callbacks"].append(callback)

    def clear_callbacks(self, msg_id: str = None, emoji: str = None):
        """Removes all callbacks from everywhere/a message/an emoji on a message"""
        # Conversion of int for convenience
        if isinstance(msg_id, int):
            msg_id = str(msg_id)

        if not isinstance(msg_id, str):
            raise ValueError(f"Expected a message id but got a '{type(msg_id)}' instead!")
        
        if not isinstance(emoji, str):
            raise ValueError(f"Expected a stringified emoji but got a '{type(emoji)}' instead!")

        if msg_id is None:
            self._messages = {}
            return
        elif emoji is None:
            if msg_id in self._messages:
                del self._messages[msg_id]
            else:
                raise KeyError(f"Message '{msg_id}' is not listened to!")
        else:
            if not msg_id in self._messages:
                raise KeyError(f"Message '{msg_id}' is not listened to!")
            
            if not emoji in self._messages[msg_id]["reactions"]:
                raise KeyError(f"Message '{msg_id}' had no listener for emoji '{emoji}'!")
            
            del self._messages[msg_id]["reactions"][emoji]

    async def process(self, msg_id: str, emoji: str, member: discord.Member, add: bool):
        """Processes the reaction event"""
        logger.debug(f"Processing reaction: [ add: {add}, msg_id: {msg_id}, emoji: {emoji}, member: {member} ]")
        if not msg_id in self._messages:
            logger.debug("The message was not listened to.")
            return
        
        if not emoji in self._messages[msg_id]["reactions"]:
            logger.debug("The emoji wasn't listened to.")
            return
        
        logger.debug("The reaction is listened to! Calling callbacks!")

        if add:
            callbacks = self._messages[msg_id]["reactions"][emoji]["add_callbacks"]
        else:
            callbacks = self._messages[msg_id]["reactions"][emoji]["rm_callbacks"]
        
        for callback in callbacks:
            await callback(msg_id=msg_id, emoji=emoji, member=member)
