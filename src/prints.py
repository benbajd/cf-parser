'''Implements printing methods.'''

from enum import Enum, IntEnum
from typing import Protocol, Optional, Callable
from dataclasses import dataclass
import os
from functools import partial
from paths import File


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
    '''A mutable stylized str.'''
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
        new_string.string = string if string is not None else []
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
        Add the other stylized string to the current one in-place.
        :param other: the other stylized string to add, can be a stylized base string
        :returns: the modified current stylized string
        '''
        self.string = (self + other).string
        return self


class Print(Protocol):
    '''An immutable class that handles printing to the terminal or a file.'''

    def print(self, string: StylizedStr, end_newline: bool = True) -> None:
        '''
        Print the string.
        :param string: the string to print
        :param end_newline: True if a newline should be printed at the end or False otherwise
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
        Process the input string.
        :param string: the input string
        '''


class PrintTerminal(Print):
    '''Implements Print in the terminal.'''

    def print_base(self, string: StylizedBaseStr) -> None:
        '''
        Print a stylized base string to the terminal.
        :param string: the string to print
        '''
        # remove any previous styling
        print(EscapeCodes.RESET.value, end='')

        # set current styling
        if string.color != Colors.DEFAULT:
            print(EscapeCodes.COLORED.value(string.color), end='')
        if string.bold:
            print(EscapeCodes.BOLD.value, end='')

        # print the string
        print(string.string, end='')

    def print(self, string: StylizedStr, end_newline: bool = True) -> None:
        '''
        Print a stylized string to the terminal with a newline at the end and flush the output.
        :param string: the string to print
        :param end_newline: True if a newline should be printed at the end or False otherwise
        '''
        # print the string
        for base_string in string.string:
            self.print_base(base_string)

        # print a newline and flush the output
        print(end=('\n' if end_newline else ''), flush=True)

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
        Do nothing in the terminal case since the input string is already displayed.
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

    def print(self, string: StylizedStr, end_newline: bool = True) -> None:
        '''
        Print a stylized string to the file, omitting all styles.
        :param string: the string to print
        :param end_newline: True if a newline should be printed at the end or False otherwise
        '''
        self.file.append_file(string.plain_string() + ('\n' if end_newline else ''))

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
        Print the input string to the file by omitting all styles.
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

    def print(self, string: StylizedStr, end_newline: bool = True) -> None:
        '''
        Don't print the string since it only logs input.
        :param string: the string to print
        :param end_newline: True if a newline should be printed at the end or False otherwise
        '''
        pass

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
        :param string: thw string to print
        '''
        pass

    def handle_input(self, string: StylizedStr) -> None:
        '''
        Print the string to the file by omitting all styles and add a timestamp.
        :param string: the input string
        '''
        # TODO: add a timestamp
        self.file.append_file(string.plain_string() + '\n')


class PrintBatched(Print):
    '''Implements Print to multiple output targets.'''
    targets: list[Print]

    def __init__(self, targets: list[Print]) -> None:
        '''
        Init the PrintBatched.
        :param targets: the output targets
        '''
        self.targets = targets.copy()

    def print(self, string: StylizedStr, end_newline: bool = True) -> None:
        '''
        Print the string.
        :param string: the string to print
        :param end_newline: True if a newline should be printed at the end or False otherwise
        '''
        for target in self.targets:
            target.print(string, end_newline)

    def status_updates(self, string: StylizedStr, final: bool = False) -> None:
        '''
        Keeps printing status updates (a value that is updated for some amount of time),
        designed to be called in succession with the last call setting final=True.
        :param string: the current status update string
        :param final: should be True on the last call and False before that
        '''
        for target in self.targets:
            target.status_updates(string, final)

    def update_previous(self, string: StylizedStr) -> None:
        '''
        Update the previous print call by printing a string to the end of it.
        :param string: the string to add to the previous printed string
        '''
        for target in self.targets:
            target.update_previous(string)

    def handle_input(self, string: StylizedStr) -> None:
        '''
        Process the input string.
        :param string: the input string
        '''
        for target in self.targets:
            target.handle_input(string)
