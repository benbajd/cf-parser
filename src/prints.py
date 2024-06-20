'''Implements printing methods.'''

from enum import Enum, IntEnum
from typing import Protocol, Optional, Callable
from dataclasses import dataclass
import os
from functools import partial
from paths import File
import gnureadline as readline


class Colors(IntEnum):
    '''Colors and their corresponding 8-bit ansi escape code values.'''
    DEFAULT = -1  # no color, ie. the terminal default
    ORANGE = 208
    GREEN = 76
    RED = 196
    BLUE = 39
    PINK = 206
    LIGHT_GREEN = 154
    LIME = 190
    YELLOW = 11
    GOLD = 220
    DARK_GREEN = 28
    DEEP_BLUE = 21
    GRAY = 244
    SOFT_BLUE = 105
    DARK_BLUE = 27
    SEMI_DARK_BLUE = 33
    LIGHT_BLUE = 74


class EscapeCodes(Enum):
    '''ANSI escape codes for stylized printing and cursor movement in the terminal.'''
    COLORED: Callable[[Colors], str] = partial(lambda color: f'\033[38;5;{color}m')  # 8-bit color
    BOLD: str = '\033[1m'  # bold
    RESET: str = '\033[0m'  # reset all styles and colors
    ERASE_LINE_FULL: str = '\033[2K'  # erase the entire current line
    ERASE_LINE_TO_END: str = '\033[0K'  # erase from cursor to end of line
    ERASE_LINE_TO_START: str = '\033[1K'  # erase from start of line to cursor
    MOVE_UP: Callable[[int], str] = partial(lambda num_rows: f'\033[{num_rows}A')  # move cursor num_rows lines up
    MOVE_DOWN: Callable[[int], str] = partial(lambda num_rows: f'\033[{num_rows}B')  # move cursor num_rows lines down
    MOVE_RIGHT: Callable[[int], str] = partial(lambda num_cols: f'\033[{num_cols}C')  # move cursor num_cols cols right
    MOVE_LEFT: Callable[[int], str] = partial(lambda num_cols: f'\033[{num_cols}D')  # move cursor num_cols cols left
    MOVE_TO_COLUMN: Callable[[int], str] = partial(lambda col: f'\033[{col}G')  # move cursor to column col
    HIDE_CURSOR: str = '\033[?25l'  # hide cursor
    SHOW_CURSOR: str = '\033[?25h'  # show cursor


@dataclass
class StylizedBaseStr:
    '''An immutable uniformly stylized str.'''
    string: str  # the string
    color: Colors = Colors.DEFAULT  # the color
    bold: bool = False  # bold

    def __len__(self) -> int:
        '''
        Find the length of the string.
        :returns: the length of the string
        '''
        return len(self.string)

    def plain_string(self) -> str:
        '''
        Get the plain string.
        :returns: the plain string
        '''
        return self.string


class StylizedStr:
    '''An immutable stylized str.'''
    string: list[StylizedBaseStr]

    def __init__(self, string: str = '', color: Colors = Colors.DEFAULT, bold: bool = False) -> None:
        '''
        Init a stylized string.
        :param string: the string
        :param color: the color
        :param bold: True if the string is bold else False
        '''
        self.string = [StylizedBaseStr(string, color, bold)] if string != '' else []

    @staticmethod
    def make_stylized_string(string: Optional[list[StylizedBaseStr]] = None) -> "StylizedStr":
        '''
        A factory function to create a stylized string.
        :param string: a list of stylized base strings
        :returns: the stylized string
        '''
        new_string = StylizedStr()
        new_string.string = string.copy() if string is not None else []
        return new_string

    def __len__(self) -> int:
        '''
        Find the length of the string.
        :returns: the length of the string
        '''
        return sum(len(base_string) for base_string in self.string)

    def plain_string(self) -> str:
        '''
        Get the plain string.
        :returns: the plain string
        '''
        return ''.join(base_string.plain_string() for base_string in self.string)

    def __add__(self, other: "StylizedStr") -> "StylizedStr":
        '''
        Add two stylized strings together without changing the current one.
        :param other: the other stylized string to add, can be a stylized base string
        :returns: the concatenation of the two stylized strings
        '''
        return StylizedStr.make_stylized_string(self.string + other.string)

    def __iadd__(self, other: "StylizedStr") -> "StylizedStr":
        '''
        Add the other stylized string to the current one by creating a new stylized string.
        :param other: the other stylized string to add, can be a stylized base string
        :returns: the modified current stylized string
        '''
        return self.__add__(other)


class Print(Protocol):
    '''An immutable class that handles printing to the terminal or a file and getting user input.'''

    def print(self, string: StylizedStr) -> None:
        '''
        Print the string.
        :param string: the string to print
        '''

    def get_input(self, string: StylizedStr, input_style: StylizedStr, history_file: File) -> str:
        '''
        Prompt a string and get user input.
        :param string: the prompt
        :param input_style: the style of the input, the string should be empty
        :param history_file: the history file with previous input
        :return: the user input
        '''

    def status_updates(self, string: StylizedStr, final: bool = False) -> None:
        '''
        Keeps printing status updates (a value that is updated for some amount of time),
        designed to be called in succession with the last call setting final=True.
        :param string: the current status update string
        :param final: should be True on the last call and False before that
        '''

    def update_previous(self, string: StylizedStr) -> None:
        '''
        Update the previous print call by printing a string to the end of it.
        :param string: the string to add to the previous printed string
        '''

    def handle_input(self, string: StylizedStr) -> None:
        '''
        Process the input string. Should only be called by get_input.
        :param string: the input string
        '''


class PrintTerminal(Print):
    '''Implements Print in the terminal.'''

    def print_base(self, string: StylizedBaseStr) -> str:
        '''
        Print a stylized base string to the terminal.
        :param string: the string to print
        :return: the string to print as a python string with ansi escape codes
        '''
        print_str = ''

        # remove any previous styling
        print_str += EscapeCodes.RESET.value

        # set current styling
        if string.color != Colors.DEFAULT:
            print_str += EscapeCodes.COLORED.value(string.color)
        if string.bold:
            print_str += EscapeCodes.BOLD.value

        # add the string
        print_str += string.string

        return print_str

    def print(self, string: StylizedStr) -> None:
        '''
        Print a stylized string to the terminal with a newline at the end and flush the output.
        :param string: the string to print
        '''
        # get the string to print
        print_str = ''.join(self.print_base(base_string) for base_string in string.string)

        # print the string with a newline and flush the output
        print(print_str, flush=True)

    def get_input(self, string: StylizedStr, input_style: StylizedStr, history_file: File) -> str:
        '''
        Prompt a string and get user input.
        :param string: the prompt
        :param input_style: the style of the input, the string should be empty
        :param history_file: the history file with previous input
        :return: the user input
        '''
        # set the input history
        readline.clear_history()
        readline.read_history_file(str(history_file))

        # print the prompt and get user input
        prompt_str = ''.join(self.print_base(base_string) for base_string in string.string)
        prompt_str += ''.join(self.print_base(base_style) for base_style in input_style.string)
        user_input = input(prompt_str)

        # handle input and write the updated history file
        self.handle_input(StylizedStr(user_input))
        readline.set_history_length(100)  # store up to 100 previous commands
        readline.write_history_file(str(history_file))

        # return user input
        return user_input

    def status_updates(self, string: StylizedStr, final: bool = False) -> None:
        '''
        Keep printing status updates (a value that is updated for some amount of time)
        by rewriting the line each time, then printing a newline and flushing once called with final=True
        with the cursor hidden throughout.
        Designed to be called in succession with the last call setting final=True.
        :param string: the string to print
        :param final: should be True on the last call and False before that
        '''
        # erase the current line and reset the cursor to the start of the line and make it hidden
        print(EscapeCodes.ERASE_LINE_FULL.value, end='')
        print(EscapeCodes.MOVE_TO_COLUMN.value(0), end='')
        print(EscapeCodes.HIDE_CURSOR.value, end='')

        # print the string
        for base_string in string.string:
            self.print_base(base_string)

        # add a newline and show the cursor if final=True and flush the output
        if final:
            print(end='\n')
            print(EscapeCodes.SHOW_CURSOR.value, end='')
        print(end='', flush=True)

    def update_previous(self, string: StylizedStr) -> None:
        '''
        Update the previous printed line by overwriting the end of it with string (right justified).
        :param string: the string to print
        '''
        # move cursor to the right column on the previous line
        terminal_width: int = os.get_terminal_size().columns
        print(EscapeCodes.MOVE_UP.value(1), end='')
        print(EscapeCodes.MOVE_TO_COLUMN.value(terminal_width - len(string)), end='')

        # print the string
        self.print(string)

    def handle_input(self, string: StylizedStr) -> None:
        '''
        Do nothing in the terminal case since the input string is already displayed. Should only be called by get_input.
        :param string: the input string
        '''
        pass


class PrintFile(Print):
    '''Implements Print in a file which logs all output and input.'''
    file: File  # the file to write to
    status_updates_temp_string: str  # a temporary string to print to file in status_updates

    def __init__(self, file: File) -> None:
        '''
        Init the PrintFile.
        :param file: the file to write to
        '''
        self.file = file
        self.status_updates_temp_string = ''

    def print(self, string: StylizedStr) -> None:
        '''
        Print a stylized string to the file, omitting all styles.
        :param string: the string to print
        '''
        self.file.append_file(string.plain_string() + '\n')

    def get_input(self, string: StylizedStr, input_style: StylizedStr, history_file: File) -> str:
        '''
        Prompt a string omitting all styles but don't get user input since this is a file.
        :param string: the prompt
        :param input_style: the style of the input, the string should be empty
        :param history_file: the history file with previous input
        :return: the empty string
        '''
        self.file.append_file(string.plain_string() + '\n')
        return ''

    def status_updates(self, string: StylizedStr, final: bool = False) -> None:
        '''
        Keep printing status updates (a value that is updated for some amount of time)
        to the file by adding each update on a new line and omitting all styles.
        The file writing is delayed until the last call for performance.
        Designed to be called in succession with the last call setting final=True.
        :param string: the string to print
        :param final: should be True on the last call and False before that
        '''
        # store temporarily
        self.status_updates_temp_string += (string.plain_string() + '\n')

        # print to file on last call
        if final:
            self.file.append_file(self.status_updates_temp_string)
            self.status_updates_temp_string = ''

    def update_previous(self, string: StylizedStr) -> None:
        '''
        Update the previous printed line by printing the string to the file
        in the current next line and omitting all styles.
        :param string: the string to print
        '''
        self.file.append_file(string.plain_string() + '\n')

    def handle_input(self, string: StylizedStr) -> None:
        '''
        Print the input string to the file by omitting all styles. Should only be called by get_input.
        :param string: the input string
        '''
        self.file.append_file(string.plain_string() + '\n')


class PrintFileInputOnly(Print):
    '''Implements Print in a file which only logs input.'''
    file: File  # the file to write to

    def __init__(self, file: File) -> None:
        '''
        Init the PrintFile.
        :param file: the file to write to
        '''
        self.file = file

    def print(self, string: StylizedStr) -> None:
        '''
        Don't print the string since it only logs input.
        :param string: the string to print
        '''
        pass

    def get_input(self, string: StylizedStr, input_style: StylizedStr, history_file: File) -> str:
        '''
        Don't print the string or get user input since it only logs input.
        :param string: the prompt
        :param input_style: the style of the input, the string should be empty
        :param history_file: the history file with previous input
        :return: the empty string
        '''
        return ''

    def status_updates(self, string: StylizedStr, final: bool = False) -> None:
        '''
        Do not print status updates (a value that is updated for some amount of time) since it only logs input.
        Designed to be called in succession with the last call setting final=True.
        :param string: the string to print
        :param final: should be True on the last call and False before that
        '''
        pass

    def update_previous(self, string: StylizedStr) -> None:
        '''
        Do not print the string since it only logs input.
        :param string: the string to print
        '''
        pass

    def handle_input(self, string: StylizedStr) -> None:
        '''
        Print the string to the file by omitting all styles and add a timestamp. Should only be called by get_input.
        :param string: the input string
        '''
        # TODO: add a timestamp
        self.file.append_file(string.plain_string() + '\n')


class PrintBatched(Print):
    '''Implements Print to multiple output targets.'''
    target_terminal: PrintTerminal
    target_files: list[PrintFile | PrintFileInputOnly]

    def __init__(self, target_terminal: PrintTerminal, target_files: list[PrintFile | PrintFileInputOnly]) -> None:
        '''
        Init the PrintBatched.
        :param target_terminal: the target terminal
        :param target_files: the target files
        '''
        self.target_terminal = target_terminal
        self.target_files = target_files.copy()

    def print(self, string: StylizedStr) -> None:
        '''
        Print the string.
        :param string: the string to print
        '''
        self.target_terminal.print(string)
        for target_file in self.target_files:
            target_file.print(string)

    def get_input(self, string: StylizedStr, input_style: StylizedStr, history_file: File) -> str:
        '''
        Prompt a string and get user input.
        :param string: the prompt
        :param input_style: the style of the input, the string should be empty
        :param history_file: the history file with previous input
        :return: the user input
        '''
        # get input from the terminal
        user_input = self.target_terminal.get_input(string, input_style, history_file)

        # handle input in all the files
        self.handle_input(StylizedStr(user_input))

        # return user input
        return user_input

    def status_updates(self, string: StylizedStr, final: bool = False) -> None:
        '''
        Keeps printing status updates (a value that is updated for some amount of time),
        designed to be called in succession with the last call setting final=True.
        :param string: the current status update string
        :param final: should be True on the last call and False before that
        '''
        self.target_terminal.status_updates(string, final)
        for file_target in self.target_files:
            file_target.status_updates(string, final)

    def update_previous(self, string: StylizedStr) -> None:
        '''
        Update the previous print call by printing a string to the end of it.
        :param string: the string to add to the previous printed string
        '''
        self.target_terminal.update_previous(string)
        for file_target in self.target_files:
            file_target.update_previous(string)

    def handle_input(self, string: StylizedStr) -> None:
        '''
        Process the input string. Should only be called by get_input.
        :param string: the input string
        '''
        # only handle input in target files since the target terminal already did when calling its get_input
        for file_target in self.target_files:
            file_target.handle_input(string)
