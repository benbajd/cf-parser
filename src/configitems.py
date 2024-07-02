'''Implements config items.'''

from typing import Generic, TypeVar, Protocol, Callable, Optional
import subprocess
from messages import Messages
from paths import File

T = TypeVar('T')


class ConfigItem(Protocol[T]):
    '''A mutable config item.'''
    name: str  # the name of the config item
    value: Optional[T]  # the current value of the item or None if not set yet
    value_str: Optional[str]  # the current value as the inputted str or None if not set yet
    check: Callable[[str], tuple[bool, str]]  # checks if the inputted str is a T, returns (success, not reason)
    get: Callable[[str], T]  # get value from a string, check should be called first and return success
    message: Messages  # the message object that handles printing

    def change_value(self, set_up: bool) -> None:
        '''
        Change the value of the config item by getting user input.
        :param set_up: True if the config item is being set for the first time or False otherwise
        '''


class ConfigItemTerminal(ConfigItem[T]):
    '''A mutable config item the user edits in the terminal.'''
    name: str  # the name of the config item
    value: Optional[T]  # the current value of the item or None if not set yet
    value_str: Optional[str]  # the current value as the inputted str or None if not set yet
    check: Callable[[str], tuple[bool, str]]  # checks if the inputted str is a T, returns (success, fail reason)
    get: Callable[[str], T]  # get value from a string, check should be called first and return success
    message: Messages  # the message object that handles printing

    def __init__(self, name: str, previous_value: Optional[str],
                 check: Callable[[str], tuple[bool, str]], get: Callable[[str], T], message: Messages) -> None:
        '''
        Init ConfigItemTerminal.
        :param name: config item's name
        :param previous_value: the previous value if previously set or None otherwise
        :param check: the check function that checks if the inputted str is a T and returns (success, fail reason)
        :param get: the get function that gets a value from a string once check is called and returns success
        :param message: the message object that handles printing
        '''
        self.name = name
        self.value = None
        self.value_str = None
        self.check = check
        self.get = get
        self.message = message

        # use previous value if given
        if previous_value is not None:
            assert self.check(previous_value)[0]  # check should return success
            self.value = self.get(previous_value)
            self.value_str = previous_value

        # get user input otherwise
        else:
            self.change_value(True)

    def change_value(self, set_up: bool) -> None:
        '''
        Change the value of the config item by getting user input.
        :param set_up: True if the config item is being set for the first time or False otherwise
        '''
        # get user's decision on editing if value was set previously
        if not set_up:
            assert self.value_str is not None  # assert value was set previously when editing
            if not self.message.config_item_edit_option(self.name, self.value_str):
                return

        # get the new value
        while True:
            user_input = self.message.get_config_item(self.name, set_up)
            success, fail_reason = self.check(user_input)
            if success:
                break
            else:
                self.message.config_item_failed(user_input, fail_reason)

        # set the new value
        self.value = self.get(user_input)
        self.value_str = user_input


class ConfigItemFile(ConfigItem[T]):
    '''A mutable config item the user edits as a file.'''
    name: str  # the name of the config item
    file_edit: File  # the file the user edits
    value: Optional[T]  # the current value of the item or None if not set yet
    value_str: Optional[str]  # the current value as the inputted str or None if not set yet
    check: Callable[[str], tuple[bool, str]]  # checks if the inputted str is a T, returns (success, fail reason)
    get: Callable[[str], T]  # get value from a string, check should be called first and return success
    message: Messages  # the message object that handles printing
    default: str  # the default item the user can choose to use without editing
    text_editor_command_wait: list[str]  # the command that opens a text editor for editing

    def __init__(self, name: str, file_edit: File,
                 check: Callable[[str], tuple[bool, str]], get: Callable[[str], T], message: Messages,
                 default: str, text_editor_command_wait: list[str]) -> None:
        '''
        Init ConfigItemFile.
        :param name: config item's name
        :param file_edit: the file the user edits, shouldn't be created unless already set
        :param check: the check function that checks if the inputted str is a T and returns (success, fail reason)
        :param get: the get function that gets a value from a string once check is called and returns success
        :param message: the message object that handles printing
        :param text_editor_command_wait: the command that opens a text editor for editing
        '''
        self.name = name
        self.file_edit = file_edit
        self.value = None
        self.value_str = None
        self.check = check
        self.get = get
        self.message = message
        self.default = default
        self.text_editor_command_wait = text_editor_command_wait

        # check on default should return success
        assert self.check(self.default)[0]

        # use previous value if the file exists
        if self.file_edit.file_exists():
            file_str = self.file_edit.read_file()
            assert self.check(file_str)[0]  # check should return success
            self.value = self.get(file_str)
            self.value_str = file_str

        # get user input otherwise
        else:
            self.change_value(True)

    def change_value(self, set_up: bool) -> None:
        '''
        Change the value of the config item by opening the file for editing.
        :param set_up: True if the config item is being set for the first time or False otherwise
        '''
        # create the file with the default value if it doesn't exist
        if not self.file_edit.file_exists():
            self.file_edit.write_file(self.default)

        # get the user decision on editing the file
        if self.message.config_item_file_edit(self.name, set_up):
            while True:
                # edit the file
                self.message.config_item_file_editing(self.name)
                subprocess.run(self.text_editor_command_wait + [str(self.file_edit)])  # TODO: call execution
                # check user input
                user_input = self.file_edit.read_file()
                success, fail_reason = self.check(user_input)
                if success:
                    break
                else:
                    self.message.config_item_file_failed(fail_reason)

        # set the new value
        file_str = self.file_edit.read_file()
        self.value = self.get(file_str)
        self.value_str = file_str
