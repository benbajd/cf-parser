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


class CommandsProblem(IntEnum):
    '''The commands for problem.'''
    EDIT = 1  # e, edit problems[*] [--all] [-f file]
    CUSTOM_INVOCATION = 2  # c, custom-invocation [-f file]
    RUN = 3  # r, run [-t tl] [-c checker] [-m multitest-mode] [-n]
    SET = 4  # s, set [-t tl] [-c checker] [-m multitest-mode]
    INPUT_OUTPUT = 5  # io, input-output [-r rm_cnt] [-k keep_cnt] [--multitests tc?] [--add] [--view tc?]
    RANDOM = 6  # n, random num [-t tl] [-c checker] [-s total-timeout]
    PASTE = 7  # p, paste
    MOVE = 8  # m, move problem
    QUIT = 9  # q, quit


class CommandSuiteProblem(CommandSuite[CommandsProblem]):
    '''An immutable command suite for problems.'''
    all_commands: list[Command[CommandsProblem]]  # the list of commands
    message: Messages  # the message object that handles printing
    command_names: dict[str, Command[CommandsProblem]]  # the dict of command names to commands

    def __init__(self, message: Messages, problem_ids: list[str]) -> None:
        '''
        Init Command SuiteProblem.
        :param message: the message object that handles printing
        :param problem_ids: the list of problem ids
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
            ['main'],
            choices=['m', 'c', 'b', 'g']
        )
        command_edit = Command(
            'e', 'edit', CommandsProblem.EDIT,
            [arg_edit_problems], [arg_edit_all, arg_edit_file],
            self.message,
            [
                'Edit the .cpp files of', arg_edit_problems.get_name_short(), ', or all if', arg_edit_all.short_flag,
                'is set. When', arg_edit_file.short_flag, 'is not given, edit main, otherwise edit the file',
                arg_edit_file.get_name_short(), '.'
             ]
        )

        # custom invocation command
        # c, custom-invocation [-f file]
        arg_custom_invocation_file = OptionalArgument(
            '-f', '--file', 'file',
            1, OptionalArgumentMode.CHOICES, self.message,
            'the file to run, one of "m" for main, "c" for checker, "b" for bruteforce, or "g" for generator',
            ['main'],
            choices=['m', 'c', 'b', 'g']
        )
        command_custom_invocation = Command(
            'c', 'custom-invocation', CommandsProblem.CUSTOM_INVOCATION,
            [], [arg_custom_invocation_file],
            self.message,
            [
                'Run .cpp file in a separate shell. When', arg_custom_invocation_file.short_flag,
                'is not given, run main, otherwise run', arg_custom_invocation_file.get_name_short(), '.'
            ]
        )

        # run command
        # r, run [-t tl] [-c checker] [-m multitest-mode] [-n]
        arg_run_time_limit = OptionalArgument(
            '-t', '--time-limit', 'time-limit',
            1, OptionalArgumentMode.FLOAT_RANGE, self.message,
            'the time limit',
            None,
            num_range=(0.1, math.inf)
        )
        arg_run_checker = OptionalArgument(
            '-c', '--checker', 'checker',
            1, OptionalArgumentMode.CHOICES, self.message,
            'the checker to use, one of "t" for tokenize (compare tokens without whitespace), '
            '"y" for yes/no checker (case-insensitive), or "c" for custom checker',
            None,
            choices=['t', 'y', 'c']
        )
        arg_run_multitest_mode = OptionalArgument(
            '-m', '--multitest-mode', 'multitest-mode',
            1, OptionalArgumentMode.CHOICES, self.message,
            'the multitest mode to use, one of "o" for entire testcases or "m" for multitests',
            None,
            choices=['o', 'm']
        )
        arg_run_no_override = OptionalArgument(
            '-n', '--no-override', 'no-override',
            0, OptionalArgumentMode.BOOL_FLAG, self.message,
            'when set, the selected options and modes aren\'t overridden',
            ['False']
        )
        command_run = Command(
            'r', 'run', CommandsProblem.RUN,
            [], [arg_run_time_limit, arg_run_checker, arg_run_multitest_mode, arg_run_no_override],
            self.message,
            [
                'Run the testcases. When', arg_run_time_limit.short_flag, 'is given, set the time limit to',
                arg_run_time_limit.get_name_short(), '. When', arg_run_checker.short_flag,
                'is given, set the checker to', arg_run_checker.get_name_short(), '. When',
                arg_run_multitest_mode.short_flag, 'is given, set the multitest mode to',
                arg_run_multitest_mode.get_name_short(), '. Unless', arg_run_no_override.short_flag,
                'is set, override the default problem options and modes with the given ones.'
            ]
        )

        # set command
        # s, set [-t tl] [-c checker] [-m multitest-mode]
        arg_set_time_limit = OptionalArgument(
            '-t', '--time-limit', 'time-limit',
            1, OptionalArgumentMode.FLOAT_RANGE, self.message,
            'the time limit',
            None,
            num_range=(0.1, math.inf)
        )
        arg_set_checker = OptionalArgument(
            '-c', '--checker', 'checker',
            1, OptionalArgumentMode.CHOICES, self.message,
            'the checker to use, one of "t" for tokenize (compare tokens without whitespace), '
            '"y" for yes/no checker (case-insensitive), or "c" for custom checker',
            None,
            choices=['t', 'y', 'c']
        )
        arg_set_multitest_mode = OptionalArgument(
            '-m', '--multitest-mode', 'multitest-mode',
            1, OptionalArgumentMode.CHOICES, self.message,
            'the multitest mode to use, one of "o" for entire testcases or "m" for multitests',
            None,
            choices=['o', 'm']
        )
        command_set = Command(
            's', 'set', CommandsProblem.SET,
            [], [arg_set_time_limit, arg_set_checker, arg_set_multitest_mode],
            self.message,
            [
                'Set the default options and modes of the problem. When', arg_set_time_limit.short_flag,
                'is given, set the time limit to', arg_set_time_limit.get_name_short(), '. When',
                arg_set_checker.short_flag, 'is given, set the checker to', arg_set_checker.get_name_short(),
                '. When', arg_set_multitest_mode.short_flag, 'is given, set the multitest mode to',
                arg_set_multitest_mode.get_name_short(), '.'
            ]
        )

        # input output command
        # io, input-output [-r rm_cnt] [-k keep_cnt] [--multitests tc?] [--add] [--view tc?]
        arg_input_output_remove = OptionalArgument(
            '-r', '--remove', 'remove',
            1, OptionalArgumentMode.INT_RANGE, self.message,
            'the number of testcases to remove from the end',
            None,
            num_range=(1, math.inf)
        )
        arg_input_output_keep = OptionalArgument(
            '-k', '--keep', 'keep',
            1, OptionalArgumentMode.INT_RANGE, self.message,
            'the number of testcases to keep from the start',
            None,
            num_range=(0, math.inf)
        )
        arg_input_output_multitests = OptionalArgument(
            '-m', '--multitests', 'multitests',
            '?', OptionalArgumentMode.INT_RANGE, self.message,
            'the testcases whose multitests to edit or all if not specified',
            None,
            num_range=(1, math.inf)
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
            num_range=(1, math.inf)
        )
        command_input_output = Command(
            'io', 'input-output', CommandsProblem.INPUT_OUTPUT,
            [], [
                arg_input_output_remove, arg_input_output_keep, arg_input_output_multitests,
                arg_input_output_add, arg_input_output_view
            ],
            self.message,
            [
                'The testcase command. When', arg_input_output_remove.short_flag, 'is given, remove the last',
                arg_input_output_remove.get_name_short(), 'testcases. When', arg_input_output_keep.short_flag,
                'is given, keep the first', arg_input_output_keep.get_name_short(),
                'testcases and remove the rest. When', arg_input_output_multitests.short_flag,
                'is given, edit the multitests of', arg_input_output_multitests.get_name_short(),
                'if specified, or all scraped testcases otherwise. When', arg_input_output_add.short_flag,
                'is set, add a custom testcase. When', arg_input_output_view.short_flag, 'is given, view the testcase',
                arg_input_output_view.get_name_short(), 'if specified, or all testcases otherwise. '
                'When multiple flags are given, they are processed in the following order: first',
                arg_input_output_remove.short_flag, 'and', arg_input_output_keep.short_flag,
                'together, then', arg_input_output_multitests.short_flag, ',', arg_input_output_add.short_flag,
                ', and finally', arg_input_output_view.short_flag, '.'
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
            [arg_random_num], [arg_random_time_limit, arg_random_checker, arg_random_total_timeout],
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
            [], [],
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
            [arg_move_problem], [],
            self.message,
            [
                'Move to the problem', arg_move_problem.get_name_short(), '.'
            ]
        )

        # quit command
        # q, quit
        command_quit = Command(
            'q', 'quit', CommandsProblem.QUIT,
            [], [],
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
