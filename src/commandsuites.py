'''Implements command suites.'''

import math
from typing import Optional, Protocol, TypeVar
from enum import IntEnum
from arguments import PositionalArgument, PositionalArgumentMode, OptionalArgument, OptionalArgumentMode
from commands import Command
from messages import Messages


T = TypeVar('T')


class CommandSuite(Protocol[T]):
    '''An immutable command suite defining commands.'''
    all_commands: list[Command[T]]  # the list of commands
    message: Messages  # the message object that handles printing

    def parse(self, args: list[str]) -> Optional[tuple[T, dict[str, str]]]:
        '''
        Parse the given command and args.
        :param args: the given command and args
        :return: the command and parsed args if parsed successfully or None otherwise
        '''

    def print_help_strings(self, command_name: Optional[str]) -> None:
        '''
        Print the short help strings for all commands if command is not given
        or the long help string for command otherwise.
        :param command_name: the command to print the help string for
        '''


class CommandsProblem(IntEnum):
    '''The commands for problem.'''
    EDIT = 1  # e, edit problems[*] [--all] [-f file]
    CUSTOM_INVOCATION = 2  # c, custom-invocation [-f file]
    RUN = 3  # r, run [-t tl] [-m multitest-mode] [-c checker] [-n]
    SET = 4  # s, set [-t tl] [-m multitest-mode] [-c checker]
    INPUT_OUTPUT = 5  # io, input-output [-r rm_cnt] [-k keep_cnt] [--multitests tc?] [--add] [--view tc?]
    RANDOM = 6  # n, random num [-t tl] [-c checker] [-s total-timeout]
    PASTE = 7  # p, paste
    MOVE = 8  # m, move problem
    HELP = 9  # h, help command[?]
    QUIT = 10  # q, quit
    # TODO: the debug command


class CommandSuiteProblem(CommandSuite[CommandsProblem]):
    '''An immutable command suite for problems.'''
    all_commands: list[Command[CommandsProblem]]  # the list of commands
    message: Messages  # the message object that handles printing
    command_names: dict[str, Command[CommandsProblem]]  # the dict of command names to commands

    def __init__(self, message: Messages, problem_ids: list[str], num_testcases: int) -> None:
        '''
        Init Command SuiteProblem.
        :param message: the message object that handles printing
        :param problem_ids: the list of problem ids
        :param num_testcases: the number of testcases
        '''
        # set message and make problem_ids lowercase
        self.message: Messages = message
        problem_ids = [problem_id.lower() for problem_id in problem_ids]

        # edit command
        # e, edit problems[*] [--all] [-f file]
        arg_edit_problems = PositionalArgument(
            'problem-ids', 'problem_ids',
            '*', PositionalArgumentMode.CHOICES, self.message,
            f'problem ids, any of {problem_ids}',
            choices=problem_ids
        )
        arg_edit_all = OptionalArgument(
            '-a', '--all', 'all',
            0, OptionalArgumentMode.BOOL_FLAG, self.message,
            'all problems',
            ['False']
        )
        arg_edit_file = OptionalArgument(
            '-f', '--file', 'file',
            1, OptionalArgumentMode.CHOICES, self.message,
            'the file to edit, one of "m" for main, "c" for checker, "b" for bruteforce, or "g" for generator',
            ['m'],
            choices=['m', 'c', 'b', 'g']
        )
        command_edit = Command(
            'e', 'edit', CommandsProblem.EDIT,
            [arg_edit_problems], [arg_edit_all, arg_edit_file], False,
            self.message,
            [
                'Edit the .cpp files of', arg_edit_problems.get_name_short(), ', or all if', arg_edit_all.short_flag,
                'is set. Also always edits the current problem even if not given. '
                'When', arg_edit_file.short_flag, 'is not given, edit main, otherwise edit the file',
                arg_edit_file.get_name_short(), '.'
             ]
        )

        # custom invocation command
        # c, custom-invocation [-f file]
        arg_custom_invocation_file = OptionalArgument(
            '-f', '--file', 'file',
            1, OptionalArgumentMode.CHOICES, self.message,
            'the file to run, one of "m" for main, "c" for checker, "b" for bruteforce, or "g" for generator',
            ['m'],
            choices=['m', 'c', 'b', 'g']
        )
        command_custom_invocation = Command(
            'c', 'custom-invocation', CommandsProblem.CUSTOM_INVOCATION,
            [], [arg_custom_invocation_file], False,
            self.message,
            [
                'Run .cpp file in a new shell. When', arg_custom_invocation_file.short_flag,
                'is not given, run main, otherwise run', arg_custom_invocation_file.get_name_short(), '.'
            ]
        )

        # run command
        # r, run [-t tl] [-m multitest-mode] [-c checker] [-n]
        arg_run_time_limit = OptionalArgument(
            '-t', '--time-limit', 'time-limit',
            1, OptionalArgumentMode.FLOAT_RANGE, self.message,
            'the time limit',
            None,
            num_range=(0.1, math.inf)
        )
        arg_run_multitest_mode = OptionalArgument(
            '-m', '--multitest-mode', 'multitest-mode',
            1, OptionalArgumentMode.CHOICES, self.message,
            'the multitest mode to use, one of "o" for entire testcases or "m" for multitests',
            None,
            choices=['o', 'm']
        )
        arg_run_checker = OptionalArgument(
            '-c', '--checker', 'checker',
            1, OptionalArgumentMode.CHOICES, self.message,
            'the checker to use, one of "t" for tokenize (compare tokens without whitespace), '
            '"y" for yes/no checker (case-insensitive), or "c" for custom checker',
            None,
            choices=['t', 'y', 'c']
        )
        arg_run_no_override = OptionalArgument(
            '-n', '--no-override', 'no-override',
            0, OptionalArgumentMode.BOOL_FLAG, self.message,
            'when set, the selected options and modes aren\'t overridden',
            ['False']
        )
        command_run = Command(
            'r', 'run', CommandsProblem.RUN,
            [], [
                arg_run_time_limit, arg_run_multitest_mode, arg_run_checker, arg_run_no_override
            ], False,
            self.message,
            [
                'Run the testcases. When', arg_run_time_limit.short_flag, 'is given, set the time limit to',
                arg_run_time_limit.get_name_short(), '. When', arg_run_multitest_mode.short_flag,
                'is given, set the multitest mode to', arg_run_multitest_mode.get_name_short(),
                '. When', arg_run_checker.short_flag, 'is given, set the checker to', arg_run_checker.get_name_short(),
                '. Unless', arg_run_no_override.short_flag,
                'is set, override the default problem options and modes with the given ones.'
            ]
        )

        # set command
        # s, set [-t tl] [-m multitest-mode] [-c checker]
        arg_set_time_limit = OptionalArgument(
            '-t', '--time-limit', 'time-limit',
            1, OptionalArgumentMode.FLOAT_RANGE, self.message,
            'the time limit',
            None,
            num_range=(0.1, math.inf)
        )
        arg_set_multitest_mode = OptionalArgument(
            '-m', '--multitest-mode', 'multitest-mode',
            1, OptionalArgumentMode.CHOICES, self.message,
            'the multitest mode to use, one of "o" for entire testcases or "m" for multitests',
            None,
            choices=['o', 'm']
        )
        arg_set_checker = OptionalArgument(
            '-c', '--checker', 'checker',
            1, OptionalArgumentMode.CHOICES, self.message,
            'the checker to use, one of "t" for tokenize (compare tokens without whitespace), '
            '"y" for yes/no checker (case-insensitive), or "c" for custom checker',
            None,
            choices=['t', 'y', 'c']
        )
        command_set = Command(
            's', 'set', CommandsProblem.SET,
            [], [
                arg_set_time_limit, arg_set_multitest_mode, arg_set_checker
            ], False,
            self.message,
            [
                'Set the default options and modes of the problem. When', arg_set_time_limit.short_flag,
                'is given, set the time limit to', arg_set_time_limit.get_name_short(),
                '. When', arg_set_multitest_mode.short_flag, 'is given, set the multitest mode to',
                arg_set_multitest_mode.get_name_short(), '. When', arg_set_checker.short_flag,
                'is given, set the checker to', arg_set_checker.get_name_short(), '.'
            ]
        )

        # input output command
        # io, input-output [-r rm_cnt] [-k keep_cnt] [--multitests tc?] [--add] [--view tc?]
        arg_input_output_remove = OptionalArgument(
            '-r', '--remove', 'remove',
            1, OptionalArgumentMode.INT_RANGE, self.message,
            'the number of testcases to remove from the end',
            None,
            num_range=(1, num_testcases)
        )
        arg_input_output_keep = OptionalArgument(
            '-k', '--keep', 'keep',
            1, OptionalArgumentMode.INT_RANGE, self.message,
            'the number of testcases to keep from the start',
            None,
            num_range=(0, num_testcases - 1)
        )
        arg_input_output_multitests = OptionalArgument(
            '-m', '--multitests', 'multitests',
            '?', OptionalArgumentMode.INT_RANGE, self.message,
            'the testcase whose multitests to edit or all if not specified',
            None,
            num_range=(1, num_testcases)
        )
        arg_input_output_add = OptionalArgument(
            '-a', '--add', 'add',
            0, OptionalArgumentMode.BOOL_FLAG, self.message,
            'add a custom testcase',
            ['False']
        )
        arg_input_output_view = OptionalArgument(
            '-v', '--view', 'view',
            '?', OptionalArgumentMode.INT_RANGE, self.message,
            'the testcase to view or all if not specified',
            None,
            num_range=(1, num_testcases)
        )
        command_input_output = Command(
            'io', 'input-output', CommandsProblem.INPUT_OUTPUT,
            [], [
                arg_input_output_remove, arg_input_output_keep, arg_input_output_multitests,
                arg_input_output_add, arg_input_output_view
            ], True,
            self.message,
            [
                'The testcase command. If', arg_input_output_remove.short_flag, 'is given, remove the last',
                arg_input_output_remove.get_name_short(), 'testcases. If', arg_input_output_keep.short_flag,
                'is given, keep the first', arg_input_output_keep.get_name_short(),
                'testcases and remove the rest. If', arg_input_output_multitests.short_flag,
                'is given, edit the multitests of', arg_input_output_multitests.get_name_short(),
                'if specified, or all scraped testcases otherwise. If', arg_input_output_add.short_flag,
                'is set, add a custom testcase. If', arg_input_output_view.short_flag, 'is given, view the testcase',
                arg_input_output_view.get_name_short(), 'if specified, or all testcases otherwise.'
            ]
        )

        # random command
        # n, random num [-t tl] [-c checker] [-s total-timeout]
        arg_random_num = PositionalArgument(
            'num', 'num',
            1, PositionalArgumentMode.INT_RANGE, self.message,
            'the number of testcases to run',
            num_range=(1, 10000)
        )
        arg_random_time_limit = OptionalArgument(
            '-t', '--time-limit', 'time-limit',
            1, OptionalArgumentMode.FLOAT_RANGE, self.message,
            'the time limit for each testcase',
            None,
            num_range=(0.1, math.inf)
        )
        arg_random_checker = OptionalArgument(
            '-c', '--checker', 'checker',
            1, OptionalArgumentMode.CHOICES, self.message,
            'the checker to use, one of "t" for tokenize (compare tokens without whitespace), '
            '"y" for yes/no checker (case-insensitive), or "c" for custom checker',
            None,
            choices=['t', 'y', 'c']
        )
        arg_random_total_timeout = OptionalArgument(
            '-s', '--total-timeout', 'total-timeout',
            1, OptionalArgumentMode.FLOAT_RANGE, self.message,
            'the total timeout for the random command',
            None,
            num_range=(0.1, math.inf)
        )
        command_random = Command(
            'n', 'random', CommandsProblem.RANDOM,
            [arg_random_num], [
                arg_random_time_limit, arg_random_checker, arg_random_total_timeout
            ], False,
            self.message,
            [
                'Run the problem on', arg_random_num.get_name_short(), 'random testcases. When',
                arg_random_time_limit.short_flag, 'is given, set the time limit to',
                arg_random_time_limit.get_name_short(), '. When', arg_random_checker.short_flag,
                'is given, set the checker to', arg_random_checker.get_name_short(), '. When',
                arg_random_total_timeout.short_flag, 'is given, limit the total execution time of the command to',
                arg_random_total_timeout.get_name_short(), '. Note that this command '
                'doesn\'t override problem\'s default options and modes.'
            ]
        )

        # paste command
        # p, paste
        command_paste = Command(
            'p', 'paste', CommandsProblem.PASTE,
            [], [], False,
            self.message,
            [
                'Copy the code of the problem to clipboard.'
            ]
        )

        # move command
        # m, move problem
        arg_move_problem = PositionalArgument(
            'problem-id', 'problem_id',
            1, PositionalArgumentMode.CHOICES, self.message,
            f'problem id to move to, one of {problem_ids}',
            choices=problem_ids
        )
        command_move = Command(
            'm', 'move', CommandsProblem.MOVE,
            [arg_move_problem], [], False,
            self.message,
            [
                'Move to the problem', arg_move_problem.get_name_short(), '.'
            ]
        )

        # command help
        # h, help command[?]
        arg_help_command = PositionalArgument(
            'command', 'command',
            '?', PositionalArgumentMode.CHOICES, self.message,
            'the command to display help for if specified or all otherwise',
            [
                command_edit.short_name, command_edit.long_name,
                command_custom_invocation.short_name, command_custom_invocation.long_name,
                command_run.short_name, command_run.long_name,
                command_set.short_name, command_set.long_name,
                command_input_output.short_name, command_input_output.long_name,
                command_random.short_name, command_random.long_name,
                command_paste.short_name, command_paste.long_name,
                command_move.short_name, command_move.long_name,
                'h', 'help',
                'q', 'quit'
            ]
        )
        command_help = Command(
            'h', 'help', CommandsProblem.HELP,
            [arg_help_command], [], False,
            self.message,
            [
                'If', arg_help_command.get_name_short(), 'is not given, show short help strings for all commands. '
                'Otherwise, show long help string for', arg_help_command.get_name_short(), '.'
            ]
        )

        # quit command
        # q, quit
        command_quit = Command(
            'q', 'quit', CommandsProblem.QUIT,
            [], [], False,
            self.message,
            [
                'Quit the contest.'
            ]
        )

        # set all_commands
        self.all_commands = [
            command_edit,
            command_custom_invocation,
            command_run,
            command_set,
            command_input_output,
            command_random,
            command_paste,
            command_move,
            command_help,
            command_quit
        ]

        # set command_names
        self.command_names: dict[str, Command[CommandsProblem]] = {}
        for command in self.all_commands:
            self.command_names |= {
                command.short_name: command,
                command.long_name: command
            }

    def parse(self, args: list[str]) -> Optional[tuple[CommandsProblem, dict[str, str]]]:
        '''
        Parse the command and arguments.
        :param args: the given arguments
        :return: the parsed command and arguments if parsed successfully or None otherwise
        '''
        # no command given
        if len(args) == 0:
            self.message.command_suite_no_command_given()
            return None

        # TODO: aliases

        # no command with that name
        if args[0] not in self.command_names:
            self.message.command_suite_not_a_command(args[0])
            return None

        # parse the args
        command = self.command_names[args[0]]
        parsed_args = command.parse(args[1:])
        if parsed_args is not None:
            return command.command, parsed_args
        else:
            return None

    def print_help_strings(self, command_name: Optional[str]) -> None:
        '''
        Print the short help strings for all commands if command is not given
        or the long help string for command otherwise.
        :param command_name: the command to print the help string for, must be the name of one of the commands
        '''
        if command_name is None:
            for command in self.all_commands:
                command.print_help_str_short()
        else:
            assert command_name in self.command_names
            self.command_names[command_name].print_help_str_long()
