import discord
import time

class Table:
    """A class representing a RP table"""
    
    def __init__(self,
        author: discord.Member = None,
        title: str = None,
        description: str = None,
        creation_time: int = None,
        player_role: discord.Role = None,
        gm_role: discord.Role = None,
        inscription_time: int = None,
        annouced: int = None
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
        self._annouced: int = annouced
    
    def get_author(self) -> discord.Member:
        """Returns the author of the table"""
        return self._author
    
    def set_author(self, author: discord.Member) -> None:
        """Sets the author of the table"""
        if not isinstance(author,discord.Member):
            raise ValueError(f"Expected author to be a Member! (got {type(author)} instead)")
        
        self._author = author
    
    def get_title(self) -> str:
        """Returns the table's title"""
        return self._title
    
    def set_title(self, title: str) -> None:
        """Sets the table's title"""
        if not isinstance(title, str):
            raise ValueError(f"Expected title to be a string! (got {type(title)} instead)")
        
        self._title = title
    
    def get_description(self) -> str:
        """Returns the description of the table"""
        return self._description
    
    def set_description(self, description: str) -> None:
        """Sets the description of the table"""
        if not isinstance(title, str):
            raise ValueError(f"Expected description to be a string! (got {type(description)} instead)")
        
        self._description = description
    
    def get_creation_time(self) -> int:
        """Returns the time of creation of the Table (sec. since epoch)"""
        return self._creation_time

    def get_player_role(self) -> discord.Role:
        return self._player_role
    
    def get_gm_role(self) -> discord.Role:
        return self._gm_role

    def is_announced(self) -> bool:
        return self._annouced
    
    def set(self, **kwargs) -> None:
        """Sets Table values based on the given keyword arguments"""
        for key, value in kwargs.items():
            if   key == "author":
                self.set_author(value)
            elif key == "title":
                self.set_title(value)
            elif key == "description":
                self.set_description(value)
            else:
                raise KeyError(f"The attribute ${key} does not exist or cannot be set")
