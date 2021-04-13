import discord
import time

class Table:
    """A class representing a RP table"""
    
    def __init__(self,
        author: discord.Member,
        title: str,
        description: str,
        player_role: discord.Role,
        gm_role: discord.Role,
        inscription_time: int = None,
        creation_time: int = None,
        announced: int = None,
        announcement_msg: discord.Message = None
        ):
        self._author: discord.Member = author
        self._title: str = title
        self._description: str = description

        if creation_time is None:
            self._creation_time: int = int(time.time())
        else:
            self._creation_time = creation_time

        self._player_role: discord.Role = player_role
        self._gm_role: discord.Role = gm_role
        self._inscription_time: int = inscription_time
        self._announced: int = announced
        self._announcement_msg: discord.Message = announcement_msg
    
    def get_author(self) -> discord.Member:
        """Returns the author of the table"""
        return self._author
    
    def set_author(self, author: discord.Member) -> None:
        """Sets the author of the table"""
        if not isinstance(author,discord.Member):
            raise TypeError(f"Expected author to be a Member! (got {type(author)} instead)")
        
        self._author = author
    
    def get_title(self) -> str:
        """Returns the table's title"""
        return self._title
    
    def set_title(self, title: str) -> None:
        """Sets the table's title"""
        if not isinstance(title, str):
            raise TypeError(f"Expected title to be a string! (got {type(title)} instead)")
        
        self._title = title
    
    def get_description(self) -> str:
        """Returns the description of the table"""
        return self._description
    
    def set_description(self, description: str) -> None:
        """Sets the description of the table"""
        if not isinstance(title, str):
            raise TypeError(f"Expected description to be a string! (got {type(description)} instead)")
        
        self._description = description
    
    def set_announcement_message(self, message: discord.Message) -> None:
        if not isinstance(message, discord.Message):
            raise TypeError(f"Expected a discord Message! (got {type(message)} instead)")
        self._announcement_msg = message
        self._announced = int(time.time())
    
    def get_annoucement_message(self) -> discord.Message:
        """Returns the announcement message or None if the Table hasn't been announced yet"""
        if not self.is_announced():
            return None
        else:
            return self._announcement_msg
        

    def get_creation_time(self) -> int:
        """Returns the time of creation of the Table (sec. since epoch)"""
        return self._creation_time

    def get_player_role(self) -> discord.Role:
        """Returns the role associated to the players"""
        return self._player_role
    
    def get_gm_role(self) -> discord.Role:
        """Returns the role associated to the GM"""
        return self._gm_role

    def is_announced(self) -> bool:
        return self._announced
    
    def set(self, **kwargs) -> None:
        """
        Sets Table values based on the given keyword arguments
            Available keys:
                author:             `discord.Member`
                title:              `str`
                description:        `str`
                announced           `int/False`
                announcement_msg:   `discord.Message`
        """
        for key, value in kwargs.items():
            if   key == "author":
                self.set_author(value)
            elif key == "title":
                self.set_title(value)
            elif key == "description":
                self.set_description(value)
            elif key == "announcement_msg":
                self.set_announcement_message(value)
            elif key == "announced":
                self._announced = value
            else:
                raise KeyError(f"The attribute {key} does not exist or cannot be set")

    def to_dict(self) -> dict:
        """Returns the dict equivalent of the table"""
        data = {}
        data["author_id"] = self._author.id
        data["title"] = self._title
        data["description"] = self._description
        data["creation_time"] = self._creation_time
        data["player_role_id"] = self._player_role.id
        data["gm_role_id"] = self._gm_role.id
        data["inscription_time"] = self._inscription_time
        data["announced"] = self._announced
        data["announcement_channel_id"] = self._announcement_msg.channel.id
        data["announcement_message_id"] = self._announcement_msg.id
        return data
