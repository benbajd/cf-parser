'''Implements the command class.'''

from typing import Generic, TypeVar, Optional
from more_itertools import split_before
from messages import Messages
from arguments import Argument, PositionalArgument, OptionalArgument


T = TypeVar('T')


class Command(Generic[T]):
    '''An immutable command class.'''
    short_name: str  # the short name of the command
    long_name: str  # the long name of the command
    command: T  # the command's enum
    positional_arguments: list[PositionalArgument]  # positional arguments
    optional_arguments: list[OptionalArgument]  # optional arguments
    mutually_exclusive: bool  # are optional arguments mutually exclusive
    message: Messages  # the message object that handles printing
    help_str: list[str]  # the help string, odd indices contain short names or short flags of arguments

    def __init__(self, short_name: str, long_name: str, command: T, positional_arguments: list[PositionalArgument],
                 optional_arguments: list[OptionalArgument], mutually_exclusive: bool,
                 message: Messages, help_str: list[str]) -> None:
        '''
        Init Command. The dict_name values of all arguments must be distinct.
        :param short_name: the command's short name
        :param long_name: the command's long name
        :param command: the command
        :param positional_arguments: the positional arguments
        :param optional_arguments: the optional arguments
        :param mutually_exclusive: are optional arguments mutually exclusive
        :param message: the message object that handles printing
        :param help_str: the help string, odd indices contain short names or short flags of arguments, no spaces at ends
        '''
        self.short_name = short_name
        self.long_name = long_name
        self.command = command
        self.positional_arguments = positional_arguments
        self.optional_arguments = optional_arguments
        self.mutually_exclusive = mutually_exclusive
        self.message = message
        self.help_str = help_str

        # check that all dict_name values are distinct
        assert (len({argument.dict_name for argument in self.positional_arguments} |
                    {argument.dict_name for argument in self.optional_arguments})
                == len(self.positional_arguments) + len(self.optional_arguments))

    def get_name(self) -> str:
        '''
        Get command's name for help strings and error messages.
        :return: the command's name
        '''
        return ', '.join([self.short_name, self.long_name])

    def parse(self, args: list[str]) -> Optional[dict[str, str]]:
        '''
        Parse the arguments.
        :param args: the given arguments
        :return: the dict of parsed arguments (dict_name, value) if successfully parsed or None otherwise
        '''
        parsed_args: dict[str, str] = {}
        positional_index = 0  # the next positional argument to parse
        optional_parsed: list[bool] = [False for _ in self.optional_arguments]  # which optional arguments were parsed

        def process_argument(argument: Argument, args_given: Optional[list[str]]) -> tuple[int, bool]:
            '''
            Process the argument with given args.
            :param argument: the argument
            :param args_given: the given args or None when an optional argument isn't given
            :return: a tuple with the number of parsed args
                     and a bool True if the argument was parsed successfully, False otherwise
            '''
            if args_given is not None:
                num_args = argument.get_num_args(len(args_given))
                parsed_arg = argument.parse(args_given[:num_args])
            else:
                num_args = 0
                parsed_arg = argument.parse(None)
            if parsed_arg is not None:
                parsed_args[argument.dict_name] = parsed_arg
                return num_args, True
            else:
                return num_args, False

        def process_positional_args(positional_args: list[str]) -> bool:
            '''
            Process the current subset of positional arguments.
            :param positional_args: the current subset of positional arguments to parse
            :return: True if the positional arguments were successfully parsed, False otherwise
            '''
            nonlocal positional_index

            while len(positional_args) > 0:
                # check that there's still positional arguments to parse
                if positional_index >= len(self.positional_arguments):
                    self.message.command_too_many_positional_args(self.get_name(), positional_args[0])
                    return False

                # get the current positional argument
                positional_argument = self.positional_arguments[positional_index]
                positional_index += 1

                # parse the args
                num_parsed, success = process_argument(positional_argument, positional_args)
                if not success:
                    return False
                positional_args = positional_args[num_parsed:]  # remove the parsed args

            return True

        def get_optional_argument(flag: str) -> Optional[int]:
            '''
            Get the index of the optional argument with the given flag.
            :param flag: the flag given
            :return: the index of the optional argument or None if none of the arguments matches the flag
            '''
            for idx, optional_argument in enumerate(self.optional_arguments):
                if optional_argument.short_flag == flag or optional_argument.long_flag == flag:
                    return idx
            return None

        def process_optional_group(optional_args_group: list[str]) -> bool:
            '''
            Process the current optional group.
            :param optional_args_group: the optional group of args, first arg must be a positional argument flag
            :return: True if the optional group is successfully parsed, False otherwise
            '''
            # parse the optional argument
            optional_idx = get_optional_argument(optional_args_group[0])
            if optional_idx is None:
                self.message.command_flag_is_not_optional_argument(self.get_name(), optional_args_group[0])
                return False
            optional_args_group = optional_args_group[1:]  # remove the flag
            optional_argument = self.optional_arguments[optional_idx]
            if optional_parsed[optional_idx]:
                self.message.command_repeated_optional_argument(self.get_name(), optional_argument.get_name_long())
                return False
            if optional_parsed.count(True) == 1 and self.mutually_exclusive:
                self.message.command_too_many_optional_arguments_mutually_exclusive(self.get_name())
                return False
            optional_parsed[optional_idx] = True
            num_parsed, success = process_argument(optional_argument, optional_args_group)
            if not success:
                return False

            # parse the rest as positional args
            if not process_positional_args(optional_args_group[num_parsed:]):
                return False
            return True

        # parse the args
        # group by optional arguments, e.g. [['a', 'b'], ['-n', 'c'], ['-m', 'd', 'e'], ['-q']]
        grouped_args = list(split_before(args, lambda arg: OptionalArgument.is_flag(arg)))

        # args start with only positional arguments, process the first group
        if len(args) > 0 and not OptionalArgument.is_flag(args[0]):
            if not process_positional_args(grouped_args[0]):
                return None
            grouped_args = grouped_args[1:]

        # all remaining groups now have an optional argument as the first arg
        for arg_group in grouped_args:
            if not process_optional_group(arg_group):
                return None

        # parse the remaining arguments
        # positional arguments get no args
        for remaining_positional_argument in self.positional_arguments[positional_index:]:
            _, remaining_success = process_argument(remaining_positional_argument, [])
            if not remaining_success:
                return None
        # optional arguments get None
        for optional_index, remaining_optional_argument in enumerate(self.optional_arguments):
            if not optional_parsed[optional_index]:
                _, remaining_success = process_argument(remaining_optional_argument, None)
                if not remaining_success:
                    return None

        return parsed_args

        # TODO: failing to parse a command prints a message on previous line

    def print_help_str_short(self) -> None:
        '''
        Print the short help string that doesn't show argument descriptions.
        '''
        self.message.command_help_str(
            self.get_name(),
            [(argument.get_name_short(), str(argument.num_args)) for argument in self.positional_arguments],
            [
                (argument.get_name_short(), argument.short_flag, str(argument.num_args))
                for argument in self.optional_arguments
            ],
            self.help_str,
            self.mutually_exclusive
        )

    def print_help_str_long(self) -> None:
        '''
        Print the long help string that shows argument descriptions.
        '''
        # print the command help string
        self.print_help_str_short()

        # print the argument help strings
        for positional_argument in self.positional_arguments:
            positional_argument.print_help_str()
        for optional_argument in self.optional_arguments:
            optional_argument.print_help_str()
