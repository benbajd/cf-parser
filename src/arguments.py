'''Implements the argument class.'''

from typing import Protocol, Optional, Literal
import re
import json
from enum import IntEnum
from messages import Messages


NumArgs = int | Literal['+', '*', '?']


class Argument(Protocol):
    '''An immutable argument class to parse arguments.'''
    dict_name: str  # the name in the dict
    num_args: NumArgs  # the number of arguments needed
    message: Messages  # the message object that handles printing
    help_str: str  # the help string

    def get_name_long(self) -> str:
        '''
        Get the argument's name for full descriptions in help strings and error messages.
        :return: the long name of the argument
        '''

    def get_name_short(self) -> str:
        '''
        Get the argument's name for short descriptions in help strings and error messages.
        :return: the short name of the argument
        '''

    def get_num_args(self, num_available: int) -> int:
        '''
        Get the number of arguments to parse for this argument, parse will be called next with that many args.
        :param num_available: the number of arguments available to parse
        :return: the number of arguments to parse
        '''

    def parse(self, args: Optional[list[str]]) -> Optional[str]:
        '''
        Parse the arguments.
        :param args: the arguments
        :return: the parsed argument if successfully parsed or None otherwise
        '''

    def print_help_str(self) -> None:
        '''
        Print the help string.
        '''


class PositionalArgumentMode(IntEnum):
    '''The positional argument mode.'''
    ANY = 1  # any argument can be given
    INT = 2  # int argument
    FLOAT = 3  # float argument
    CHOICES = 4  # argument has to be in a list of choices
    INT_RANGE = 5  # int argument in a range
    FLOAT_RANGE = 6  # float argument in a range


class PositionalArgument(Argument):
    '''An immutable positional argument class to parse positional arguments in order.'''
    name: str  # the name
    dict_name: str  # the name in the dict
    num_args: NumArgs  # the number of arguments needed
    mode: PositionalArgumentMode  # the mode to use
    message: Messages  # the message object that handles printing
    help_str: str  # the help string
    choices: Optional[list[str]]  # list of choices
    num_range: Optional[tuple[float, float]]  # the possible range [l, r]

    def __init__(self, name: str, dict_name: str, num_args: NumArgs, mode: PositionalArgumentMode,
                 message: Messages, help_str: str,
                 choices: Optional[list[str]] = None, num_range: Optional[tuple[float, float]] = None) -> None:
        '''
        Init PositionalArgument.
        :param name: the argument's name
        :param dict_name: the argument's name in the dictionary
        :param num_args: the number of arguments, int when exact, or one of the '+', '*', or '?' modes (same as regex)
        :param mode: the mode to use when parsing
        :param message: the message object that handles printing
        :param help_str: the help string
        :param choices: list of choices, can only be not None when mode is 'choices'
        :param num_range: the possible range [l, r], can only be not None when mode is 'int_range' or 'float_range'
        '''
        self.name = name
        self.dict_name = dict_name
        self.num_args = num_args
        self.mode = mode
        self.message = message
        self.help_str = help_str
        self.choices = choices
        self.num_range = num_range

        # assert the mode has the required arguments
        assert bool(self.mode == PositionalArgumentMode.CHOICES) == bool(self.choices is not None)
        assert (bool(self.mode in [PositionalArgumentMode.INT_RANGE, PositionalArgumentMode.FLOAT_RANGE])
                == bool(self.num_range is not None))

        # positional arguments can't have num_args == 0
        assert self.num_args != 0

    def get_name_long(self) -> str:
        '''
        Get the argument's name for full descriptions in help strings and error messages.
        :return: the long name of the argument
        '''
        return self.name

    def get_name_short(self) -> str:
        '''
        Get the argument's name for short descriptions in help strings and error messages.
        :return: the short name of the argument
        '''
        return self.name

    def get_num_args(self, num_available: int) -> int:
        '''
        Get the number of arguments to parse for this argument, parse will be called next with that many args.
        :param num_available: the number of arguments available to parse
        :return: the number of arguments to parse
        '''
        if isinstance(self.num_args, int):
            return min(num_available, self.num_args)
        elif self.num_args == '?':
            return min(num_available, 1)
        else:
            assert self.num_args == '+' or self.num_args == '*'
            return num_available

    def parse(self, args: Optional[list[str]]) -> Optional[str]:
        '''
        Parse the arguments.
        :param args: the given arguments, len(args) <= num_args (1 for '?', infinity for '+' and '*'), args is not None
        :return: the json encoded arguments if successfully parsed
                 (a list when num_args != 1 and the element when num_args == 1) or None otherwise
        '''
        assert args is not None  # args have to be given for positional arguments

        # check that enough arguments were given
        if isinstance(self.num_args, int) and len(args) < self.num_args:
            self.message.not_enough_args_given(self.get_name_long(), self.num_args, len(args))
            return None
        if self.num_args == '+' and len(args) == 0:
            self.message.expected_at_least_one_argument(self.get_name_long())

        # check the mode conditions and parse the arguments
        if self.mode == PositionalArgumentMode.ANY:
            pass
        elif self.mode == PositionalArgumentMode.INT:
            for arg in args:
                if not is_int(arg):
                    self.message.argument_not_int(self.get_name_long(), arg)
                    return None
        elif self.mode == PositionalArgumentMode.FLOAT:
            for arg in args:
                if not is_float(arg):
                    self.message.argument_not_float(self.get_name_long(), arg)
                    return None
        elif self.mode == PositionalArgumentMode.CHOICES:
            assert self.choices is not None  # choices should be given when mode is 'choices'
            for arg in args:
                if arg not in self.choices:
                    self.message.argument_not_in_choices(self.get_name_long(), arg, self.choices)
                    return None
        elif self.mode == PositionalArgumentMode.INT_RANGE:
            assert self.num_range is not None  # num_range should be given when mode is 'int_range'
            for arg in args:
                if not is_int(arg):
                    self.message.argument_not_int(self.get_name_long(), arg)
                    return None
                if not self.num_range[0] <= int(arg) <= self.num_range[1]:
                    self.message.argument_not_in_range(self.get_name_long(), arg, self.num_range)
                    return None
        elif self.mode == PositionalArgumentMode.FLOAT_RANGE:
            assert self.num_range is not None  # num_range should be given when mode is 'float_range'
            for arg in args:
                if not is_float(arg):
                    self.message.argument_not_float(self.get_name_long(), arg)
                    return None
                if not self.num_range[0] <= float(arg) <= self.num_range[1]:
                    self.message.argument_not_in_range(self.get_name_long(), arg, self.num_range)
                    return None
        else:
            assert False

        # return the parsed arguments
        if self.num_args == 1:
            return json.dumps(args[0])
        else:
            return json.dumps(args)

    def print_help_str(self) -> None:
        '''
        Print the help string.
        '''
        self.message.argument_help_str(self.get_name_long(), self.help_str)


class OptionalArgumentMode(IntEnum):
    '''The optional argument mode.'''
    ANY = 1  # any argument can be given
    INT = 2  # int argument
    FLOAT = 3  # float argument
    CHOICES = 4  # argument has to be in a list of choices
    INT_RANGE = 5  # int argument in a range
    FLOAT_RANGE = 6  # float argument in a range
    BOOL_FLAG = 7  # True when the flag is given, False otherwise


class OptionalArgument(Argument):
    '''An immutable optional argument class to parse optional arguments given with flags.'''
    short_flag: str  # the short one character flag with one dash at the start
    long_flag: str  # the long flag with two dashes at the start
    dict_name: str  # the name in the dict
    num_args: NumArgs  # the number of arguments needed
    mode: OptionalArgumentMode  # the mode to use
    message: Messages  # the message object that handles printing
    help_str: str  # the help string
    default: Optional[list[str]]  # the args to be used when flag is not given or None to use None in that case
    choices: Optional[list[str]]  # list of choices
    num_range: Optional[tuple[float, float]]  # the possible range [l, r]

    def __init__(self, short_flag: str, long_flag: str, dict_name: str, num_args: NumArgs,
                 mode: OptionalArgumentMode, message: Messages, help_str: str, default: Optional[list[str]],
                 choices: Optional[list[str]] = None, num_range: Optional[tuple[float, float]] = None) -> None:
        '''
        Init OptionalArgument.
        :param short_flag: the short one character flag with one dash at the start
        :param long_flag: the long flag with two dashes at the start
        :param dict_name: the argument's name in the dictionary
        :param num_args: the number of arguments, int when exact, or one of the '+', '*', or '?' modes (same as regex)
        :param mode: the mode to use when parsing
        :param message: the message object that handles printing
        :param help_str: the help string
        :param default: the default args to be used when flag is not given or None to use None in that case
        :param choices: list of choices, can only be not None when mode is 'choices'
        :param num_range: the possible range [l, r], can only be not None when mode is 'int_range'
        '''
        self.short_flag = short_flag
        self.long_flag = long_flag
        self.dict_name = dict_name
        self.num_args = num_args
        self.mode = mode
        self.message = message
        self.help_str = help_str
        self.default = default
        self.choices = choices
        self.num_range = num_range

        # assert the mode has the required arguments
        assert bool(self.mode == OptionalArgumentMode.CHOICES) == bool(self.choices is not None)
        assert (bool(self.mode in [OptionalArgumentMode.INT_RANGE, OptionalArgumentMode.FLOAT_RANGE])
                == bool(self.num_range is not None))
        if self.mode == OptionalArgumentMode.BOOL_FLAG:
            assert self.num_args == 0

    def get_name_long(self) -> str:
        '''
        Get the argument's name for full descriptions in help strings and error messages.
        :return: the long name of the argument
        '''
        return ', '.join([self.short_flag, self.long_flag])

    def get_name_short(self) -> str:
        '''
        Get the argument's name for short descriptions in help strings and error messages.
        :return: the short name of the argument
        '''
        return self.long_flag[2:]  # remove the two dashes at the start

    def get_num_args(self, num_available: int) -> int:
        '''
        Get the number of arguments to parse for this argument, parse will be called next with that many args.
        :param num_available: the number of arguments available to parse
        :return: the number of arguments to parse
        '''
        if isinstance(self.num_args, int):
            return min(num_available, self.num_args)
        elif self.num_args == '?':
            return min(num_available, 1)
        else:
            assert self.num_args == '+' or self.num_args == '*'
            return num_available

    def parse(self, args: Optional[list[str]]) -> Optional[str]:
        '''
        Parse the arguments.
        :param args: the given arguments, len(args) <= num_args (1 for '?', infinity for '+' and '*'), None if not given
        :return: the json encoded arguments if successfully parsed
                 (a list when num_args != 1 and the element when num_args == 1
                 or None when a flag without default isn't passed) or None otherwise
        '''
        # set default args if flag not given
        flag_given = bool(args is not None)
        if args is None:
            if self.default is not None:
                args = self.default
            else:
                # return None
                return json.dumps(None)

        # check that enough arguments were given
        if isinstance(self.num_args, int) and len(args) < self.num_args:
            self.message.not_enough_args_given(self.get_name_long(), self.num_args, len(args))
            return None
        if self.num_args == '+' and len(args) == 0:
            self.message.expected_at_least_one_argument(self.get_name_long())

        # check the mode conditions and parse the arguments
        if self.mode == OptionalArgumentMode.ANY:
            pass
        elif self.mode == OptionalArgumentMode.INT:
            for arg in args:
                if not is_int(arg):
                    self.message.argument_not_int(self.get_name_long(), arg)
                    return None
        elif self.mode == OptionalArgumentMode.FLOAT:
            for arg in args:
                if not is_float(arg):
                    self.message.argument_not_float(self.get_name_long(), arg)
                    return None
        elif self.mode == OptionalArgumentMode.CHOICES:
            assert self.choices is not None  # choices should be given when mode is 'choices'
            for arg in args:
                if arg not in self.choices:
                    self.message.argument_not_in_choices(self.get_name_long(), arg, self.choices)
                    return None
        elif self.mode == OptionalArgumentMode.INT_RANGE:
            assert self.num_range is not None  # num_range should be given when mode is 'int_range'
            for arg in args:
                if not is_int(arg):
                    self.message.argument_not_int(self.get_name_long(), arg)
                    return None
                if not self.num_range[0] <= int(arg) <= self.num_range[1]:
                    self.message.argument_not_in_range(self.get_name_long(), arg, self.num_range)
                    return None
        elif self.mode == OptionalArgumentMode.FLOAT_RANGE:
            assert self.num_range is not None  # num_range should be given when mode is 'float_range'
            for arg in args:
                if not is_float(arg):
                    self.message.argument_not_float(self.get_name_long(), arg)
                    return None
                if not self.num_range[0] <= float(arg) <= self.num_range[1]:
                    self.message.argument_not_in_range(self.get_name_long(), arg, self.num_range)
                    return None
        elif self.mode == OptionalArgumentMode.BOOL_FLAG:
            args = ['True' if flag_given else 'False']
        else:
            assert False

        # return the parsed arguments
        if self.num_args == 1:
            return json.dumps(args[0])
        else:
            return json.dumps(args)

    def print_help_str(self) -> None:
        '''
        Print the help string.
        '''
        self.message.argument_help_str(self.get_name_long(), self.help_str)

    @staticmethod
    def is_flag(arg: str) -> bool:
        '''
        Determine whether the argument is a flag or not.
        :param arg: the given argument
        :return: True if the argument is a flag, False otherwise
        '''
        return len(arg) >= 1 and arg[0] == '-' and all(c.isalpha() or c == '-' for c in arg)


def is_int(arg: str) -> bool:
    '''
    Check if the argument is an int.
    :param arg: the argument
    :return: true if the argument is an int, false otherwise
    '''
    return re.fullmatch(r'-?[0-9]+', arg) is not None


def is_float(arg: str) -> bool:
    '''
    Check if the argument is a float.
    :param arg: the argument
    :return: true if the argument is a float, false otherwise
    '''
    return re.fullmatch(r'-?([0-9]+|[0-9]*\.[0-9]+)', arg) is not None
