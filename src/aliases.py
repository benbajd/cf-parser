'''Implements the aliases class.'''

from typing import Optional
import json
from paths import File
from messages import Messages


class Aliases:
    '''A mutable aliases class.'''
    file: File  # the file storing aliases
    message: Messages  # the message object that handles printing
    aliases: dict[str, str]  # the aliases

    def __init__(self, file: File, message: Messages) -> None:
        '''
        Init Aliases.
        :param file: the file storing aliases
        :param message: the message object that handles printing
        '''
        self.file = file
        self.message = message
        self.aliases = {}
        if self.file.file_exists():
            self.aliases = json.loads(self.file.read_file())
        else:
            self.update_aliases()

    def update_aliases(self) -> None:
        '''
        Update the aliases file.
        '''
        self.file.write_file(json.dumps(self.aliases))

    def add_alias(self, alias_name: str, alias_str: str) -> None:
        '''
        Add an alias or update one if it already exists.
        :param alias_name: alias' name
        :param alias_str: alias' string
        '''
        self.aliases[alias_name] = alias_str
        self.update_aliases()

    def remove_alias(self, alias_name: str) -> None:
        '''
        Remove an alias.
        :param alias_name: alias' name
        '''
        if alias_name in self.aliases:
            del self.aliases[alias_name]
            self.update_aliases()

    def __contains__(self, alias_name: str) -> bool:
        '''
        Check whether an alias exists.
        :param alias_name: alias' name
        :return: True if alias exists or False otherwise
        '''
        return alias_name in self.aliases

    def __getitem__(self, alias_name: str) -> str:
        '''
        Get an alias.
        :param alias_name: alias' name, must be one of the aliases
        :return: the alias
        '''
        if alias_name in self.aliases:
            return self.aliases[alias_name]
        else:
            assert False  # alias_name must be one of the aliases

    def get_alias_names(self) -> list[str]:
        '''
        Get a list of alias names.
        :return: a list of alias names
        '''
        return list(self.aliases.keys())

    def print_help_strings(self, alias_name: Optional[str]) -> None:
        '''
        Print the help strings for all aliases if alias is not given
        or the help string for alias otherwise.
        :param alias_name: the alias to print the help string for, must be one of the aliases
        '''
        if alias_name is None:
            self.message.alias_all_help_str(self.aliases.copy())
        else:
            self.message.alias_help_str(alias_name, self.aliases[alias_name])
