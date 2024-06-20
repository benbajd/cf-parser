'''Implements the messages class for printing messages and getting user input.'''

from typing import TypeVar, Optional, Literal
from prints import Print, StylizedStr, Colors, get_terminal_width
from verdicts import CompileVerdict, RunVerdict
import configs

HEADER_USERNAME_COLOR = Colors.ORANGE
HEADER_CONTEST_COLOR = Colors.GREEN
HEADER_PROBLEM_COLOR = Colors.PINK
HEADER_MODES_COLOR = Colors.LIGHT_BLUE
HEADER_MODES_DELIM_COLOR = Colors.GRAY

# the colors for compile verdicts
COMPILE_VERDICT_COLORS: dict[CompileVerdict, Colors] = {
    CompileVerdict.SUCCESS: Colors.DEFAULT,
    CompileVerdict.COMPILATION_ERROR: Colors.SOFT_BLUE
}

# the colors for run verdicts
RUN_VERDICT_COLORS: dict[RunVerdict, Colors] = {
    RunVerdict.ACCEPTED: Colors.GREEN,
    RunVerdict.WRONG_ANSWER: Colors.RED,
    RunVerdict.RUNTIME_ERROR: Colors.SEMI_DARK_BLUE,
    RunVerdict.TIME_LIMIT_EXCEEDED: Colors.GOLD,
    RunVerdict.CHECKER_RUNTIME_ERROR: Colors.SOFT_BLUE,
    RunVerdict.CHECKER_TIME_LIMIT_EXCEEDED: Colors.SOFT_BLUE
}

TESTCASE_HEADER_COLOR = Colors.DEFAULT
WRONG_ANSWER_REASON_COLOR = Colors.GRAY

IO_HEADER_COLOR = Colors.LIME
MAX_IO_LINES = 50  # max number of io lines before cutting off the end
SHORT_IO_LINES = 20  # number of io lines displayed when over the limit

COMMAND_COLOR = Colors.LIGHT_GREEN
ARGUMENT_COLOR = Colors.PINK


class Messages:
    '''An immutable object for printing messages and getting user input.'''
    log: Print  # the combination of terminal and files to print to

    def __init__(self, log: Print) -> None:
        '''
        Init Messages.
        :param log: the combination of terminal and files to print to
        '''
        self.log = log

    # HI

    def hi(self) -> None:
        '''
        Prints 'hi'.
        '''
        self.log.print(StylizedStr('hi'))

    # GETTING USER INPUT

    def get_command_problem(self, contest_id: str, problem_id: str, time_limit: float, num_testcases: tuple[int, int],
                            testcase_mode: str, checker: str) -> list[str]:
        '''
        Print the command suite problem header and get the args.
        :param contest_id: contest's id
        :param problem_id: problem's id
        :param time_limit: the time limit
        :param num_testcases: the number of testcases and the number of multitests or 0 if not split correctly
        :param testcase_mode: the mode of running testcases
        :param checker: the checker
        :return: the args
        '''
        modes_delim = StylizedStr('|', HEADER_MODES_DELIM_COLOR)
        header_str = (
            StylizedStr(configs.username, HEADER_USERNAME_COLOR) + StylizedStr('/')  # username
            + StylizedStr(contest_id, HEADER_CONTEST_COLOR) + StylizedStr('/')  # contest
            + StylizedStr(problem_id, HEADER_PROBLEM_COLOR) + StylizedStr(' ')  # problem
            + StylizedStr('[')
            + StylizedStr('tl', HEADER_MODES_COLOR)  # time limit
            + StylizedStr(str(time_limit)) + modes_delim
            + StylizedStr('io', HEADER_MODES_COLOR)  # num testcases
            + StylizedStr(f'{num_testcases[0]}+{num_testcases[1]}') + modes_delim
            + StylizedStr('tm', HEADER_MODES_COLOR)  # testcase mode
            + StylizedStr(testcase_mode) + modes_delim
            + StylizedStr('ch', HEADER_MODES_COLOR)  # checker
            + StylizedStr(checker)
            + StylizedStr('] ')
            + StylizedStr('% ')
        )
        args_str = self.log.get_input(header_str, StylizedStr(), configs.history_commandsuite_problem)
        return args_str.split()

    def input_two_options(self, decision_str_list: list[str], first_option: str = 'y', second_option: str = 'n') -> bool:
        '''
        Get user's decision from one of two options, case-insensitive.
        :param decision_str_list: ''.join(decision_str) is the description of the decision, odd indices will be bold
        :param first_option: the first option of the decision, should be a char
        :param second_option: the second option of the decision, should be a char
        :return: True if the first option was selected or False of any other string was given
        '''
        # print the decision str
        decision_str = StylizedStr()
        for idx, decision_str_part in enumerate(decision_str_list):
            decision_str += StylizedStr(decision_str_part, Colors.DEFAULT, bool(idx % 2 == 1))
        decision_str += StylizedStr(f' [{first_option}/[{second_option}]] ')

        # read the input and check if it matches the first option
        input_str = self.log.get_input(decision_str, StylizedStr(), configs.history_two_options)
        return input_str.lower() == first_option.lower()

    # HELPER FUNCTIONS

    def helper_get_plural(self, word: str, num: int) -> str:
        '''
        Get the correct singular or plural form of a word.
        :param word: the word
        :param num: the number
        :return: the singular or plural form of a word
        '''
        return word + ('s' if num != 1 else '')

    def helper_add_to_end(self, string: StylizedStr, end_string: StylizedStr) -> StylizedStr:
        '''
        Add an end string to a string so that it appears right justified.
        :param string: the string
        :param end_string: the end string
        :return: the string with the end string right justified
        '''
        # find the number of spaces to make end_string right justified
        num_spaces = get_terminal_width() - len(string) - len(end_string) - 1

        # add spaces between string and end_string
        return string + StylizedStr(' ' * num_spaces) + end_string


    # PROBLEM EDIT

    def edit_problem_files(self, problem_ids: list[str], file_cpp: Literal['m', 'c', 'b', 'g']) -> None:
        '''
        Print that the files are now open for editing.
        :param problem_ids: the problem ids to edit
        :param file_cpp: the .cpp file to edit, one of main, checker, bruteforce, or generator
        '''
        # get the file str
        edit_str = StylizedStr('editing ')
        edit_str += StylizedStr(
            {'m': 'main', 'c': 'checker', 'b': 'bruteforce', 'g': 'generator'}[file_cpp],
            bold=True
        )

        # get the problem str
        edit_str += StylizedStr(f' of {self.helper_get_plural('problem', len(problem_ids))} ')
        for idx, problem_id in enumerate(problem_ids):
            if idx > 0:
                edit_str += StylizedStr(', ')
            edit_str += StylizedStr(problem_id, HEADER_PROBLEM_COLOR)

        # print the edit str
        self.log.print(edit_str)

    # RUNNER HELPERS

    T = TypeVar('T', CompileVerdict, RunVerdict)

    def helper_get_bracket_verdicts(self, verdicts: list[T], one_char_names: list[str], colors: dict[T, Colors],
                                    running_verdict: T, bracket_verdict: Optional[T]) -> StylizedStr:
        '''
        A helper function to get the compile or run verdict string
        where each file or testcase is a '.' if it's still running or its colored one char name otherwise.
        :param verdicts: the compile or run verdicts
        :param one_char_names: one char names to print once compile or run finishes
        :param colors: the colors to use for each verdict
        :param running_verdict: the verdict corresponding to running
        :param bracket_verdict: the bracket verdict if all runs are finished or None otherwise
        :return: the compile or run verdict string
        '''
        bracket_str = StylizedStr()
        bracket_str += (
            StylizedStr('[') if bracket_verdict is None
            else StylizedStr('[', colors[bracket_verdict], True)
        )
        for verdict, one_char_name in zip(verdicts, one_char_names):
            bracket_str += (
                StylizedStr('.') if verdict == running_verdict
                else StylizedStr(one_char_name, colors[verdict], True)
            )
        bracket_str += (
            StylizedStr(']') if bracket_verdict is None
            else StylizedStr(']', colors[bracket_verdict], True)
        )
        return bracket_str

    def helper_get_compilation_error_string(self, file_names: list[str]) -> StylizedStr:
        '''
        Get the compilation error string.
        :param file_names: the names of files that got a compilation error
        :return: the compilation error string
        '''
        compilation_error_str = StylizedStr('compilation error, stopping: ')
        compilation_error_str += StylizedStr(
            'CE: ' + ', '.join(file_names),
            COMPILE_VERDICT_COLORS[CompileVerdict.COMPILATION_ERROR],
            True
        )
        return compilation_error_str

    # PROBLEM CUSTOM INVOCATION

    def custom_invocation_start(self, one_char_name: str) -> None:
        '''
        Print the custom invocation start.
        :param one_char_name: one char name of the file that is compiling
        '''
        start_str = self.helper_get_bracket_verdicts(
            [CompileVerdict.COMPILING],
            [one_char_name],
            COMPILE_VERDICT_COLORS,
            CompileVerdict.COMPILING,
            None
        )
        start_str = self.helper_add_to_end(start_str, StylizedStr('compiling'))
        self.log.status_updates(start_str)

    def custom_invocation_finish(self, one_char_name: str, file_name: str,
                                 compile_verdict: CompileVerdict, total_time: float) -> None:
        '''
        Print the custom invocation finish.
        :param one_char_name: one char name of the file that finished compiling
        :param file_name: the name of the file that finished compiling
        :param compile_verdict: the compile verdict
        :param total_time: the total compile time elapsed
        '''
        # print the bracket verdicts
        finish_str = self.helper_get_bracket_verdicts(
            [compile_verdict],
            [one_char_name],
            COMPILE_VERDICT_COLORS,
            CompileVerdict.COMPILING,
            compile_verdict
        )
        self.log.status_updates(finish_str, True)

        # print the total time elapsed
        self.log.update_previous(StylizedStr(f'took {total_time:.3f}s'))

        # print the running in custom invocation string if compiled successfully
        # or the compilation error string otherwise
        if compile_verdict == CompileVerdict.SUCCESS:
            run_str = StylizedStr('running ')
            run_str += StylizedStr(file_name, bold=True)
            run_str += StylizedStr(' in custom invocation')
            self.log.print(run_str)
        elif compile_verdict == CompileVerdict.COMPILATION_ERROR:
            compilation_error_str = self.helper_get_compilation_error_string([file_name])
            self.log.print(compilation_error_str)

    # RUNNER

    def runner_start(self, compile_count: int, run_count: int) -> None:
        '''
        Print the runner start.
        :param compile_count: number of files to compile
        :param run_count: number of testcases to run
        '''
        start_str = f'[{'.' * compile_count}] [{'.' * run_count}]'
        self.log.status_updates(StylizedStr(start_str))

    def runner_compile_update(self, compile_verdicts: list[CompileVerdict], run_count: int) -> None:
        '''
        Print the runner compile update every time a file finishes compilation.
        :param compile_verdicts: the compile verdicts, first file is main, second is custom checker (optional)
        :param run_count: number of testcases to run
        '''
        # compile verdicts
        one_char_names = ['m', 'c']  # main and custom checker
        update_str = self.helper_get_bracket_verdicts(
            compile_verdicts, one_char_names, COMPILE_VERDICT_COLORS, CompileVerdict.COMPILING, None
        )

        # run verdicts (empty)
        update_str += StylizedStr(f' [{'.' * run_count}]')

        # print the string
        self.log.status_updates(update_str)

    def runner_compile_finish(self, compile_verdicts: list[CompileVerdict], compile_bracket_verdict: CompileVerdict,
                              run_count: int) -> None:
        '''
        Print the runner compile finish by coloring the compile brackets.
        :param compile_verdicts: the compile verdicts, first file is main, second is custom checker (optional)
        :param compile_bracket_verdict: the verdict whose color to use for coloring compile brackets
        :param run_count: number of testcases to run
        '''
        # compile verdicts
        one_char_names = ['m', 'c']  # main and custom checker
        finish_str = self.helper_get_bracket_verdicts(
            compile_verdicts, one_char_names, COMPILE_VERDICT_COLORS, CompileVerdict.COMPILING, compile_bracket_verdict
        )

        # run verdicts (empty)
        finish_str += StylizedStr(f' [{'.' * run_count}]')

        # print the string and do final update if one of the compilations failed
        self.log.status_updates(finish_str, compile_bracket_verdict == CompileVerdict.COMPILATION_ERROR)

    def runner_finish_after_compile(self, compile_verdicts: list[CompileVerdict], total_time: float) -> None:
        '''
        Print the runner finish after at least one file gets a compilation error.
        :param compile_verdicts: the compile verdicts, first file is main, second is custom checker (optional)
        :param total_time: the total runner time elapsed
        '''
        # print time elapsed
        self.log.update_previous(StylizedStr(f'took {total_time:.3f}s'))

        # print the compilation error message
        file_names = ['main', 'checker']
        compilation_errors = [
            file_name for file_name, compile_verdict in zip(file_names, compile_verdicts)
            if compile_verdict == CompileVerdict.COMPILATION_ERROR
        ]
        final_str = self.helper_get_compilation_error_string(compilation_errors)
        self.log.print(final_str)

    def runner_run_update(self, compile_verdicts: list[CompileVerdict], compile_bracket_verdict: CompileVerdict,
                          run_verdicts: list[RunVerdict], testcase_ids: list[str]) -> None:
        '''
        Print the runner run update every time a testcase finishes running.
        :param compile_verdicts: the compile verdicts, first file is main, second is custom checker
        :param compile_bracket_verdict: the verdict whose color to use for coloring compile brackets
        :param run_verdicts: the run verdicts
        :param testcase_ids: the ids of testcases, each should be 't' for one tests and 't-s' for multitests
        :return:
        '''
        # compile verdicts
        one_char_names = ['m', 'c']  # main and custom checker
        update_str = self.helper_get_bracket_verdicts(
            compile_verdicts, one_char_names, COMPILE_VERDICT_COLORS, CompileVerdict.COMPILING, compile_bracket_verdict
        )
        update_str += StylizedStr(' ')

        # run verdicts
        one_char_names = [testcase_id[(testcase_id + '-').index('-') - 1] for testcase_id in testcase_ids]
        update_str += self.helper_get_bracket_verdicts(
            run_verdicts, one_char_names, RUN_VERDICT_COLORS, RunVerdict.RUNNING, None
        )

        # print the string
        self.log.status_updates(update_str)

    def runner_finish(self, compile_verdicts: list[CompileVerdict], compile_bracket_verdict: CompileVerdict,
                      run_verdicts: list[RunVerdict], testcase_ids: list[str], run_bracket_verdict: RunVerdict) -> None:
        '''
        Print the runner finish by coloring the run brackets and the time the entire run took.
        :param compile_verdicts: the compile verdicts, first file is main, second is custom checker
        :param compile_bracket_verdict: the verdict whose color to use for coloring compile brackets
        :param run_verdicts: the run verdicts
        :param testcase_ids: the ids of testcases, each should be 't' for one tests and 't-s' for multitests
        :param run_bracket_verdict: the verdict whose color to use for coloring run brackets
        '''
        # compile verdicts
        one_char_names = ['m', 'c']  # main and custom checker
        update_str = self.helper_get_bracket_verdicts(
            compile_verdicts, one_char_names, COMPILE_VERDICT_COLORS, CompileVerdict.COMPILING, compile_bracket_verdict
        )
        update_str += StylizedStr(' ')

        # run verdicts
        one_char_names = [testcase_id[(testcase_id + '-').index('-') - 1] for testcase_id in testcase_ids]
        update_str += self.helper_get_bracket_verdicts(
            run_verdicts, one_char_names, RUN_VERDICT_COLORS, RunVerdict.RUNNING, run_bracket_verdict
        )

        # print the string
        self.log.status_updates(update_str, True)

    def runner_finish_after_run(self, run_verdicts: list[RunVerdict], testcase_ids: list[str],
                                to_run: list[tuple[str, str]], main_outputs: list[str],
                                wrong_answer_reasons: list[str], total_time: float) -> None:
        '''
        Print the runner finish by printing all io for testcases that weren't accepted.
        :param run_verdicts: the run verdicts
        :param testcase_ids: the ids of testcases, each should be 't' for one tests and 't-s' for multitests
        :param to_run: the inputs and expected outputs for each testcase
        :param main_outputs: the output of main on each of the testcases
        :param wrong_answer_reasons: the wrong answer reason on each of the testcases with wrong answer
        :param total_time: the total runner time elapsed
        '''
        # print time elapsed
        self.log.update_previous(StylizedStr(f'took {total_time:.3f}s'))

        # print all testcases that weren't accepted
        short_verdict_names = {
            RunVerdict.ACCEPTED: 'AC',
            RunVerdict.WRONG_ANSWER: 'WA',
            RunVerdict.RUNTIME_ERROR: 'RTE',
            RunVerdict.TIME_LIMIT_EXCEEDED: 'TLE',
            RunVerdict.CHECKER_RUNTIME_ERROR: 'checker RTE',
            RunVerdict.CHECKER_TIME_LIMIT_EXCEEDED: 'checker TLE'
        }

        all_iterator = zip(run_verdicts, testcase_ids, to_run, main_outputs, wrong_answer_reasons)
        for run_verdict, testcase_id, io_pair, main_output, wrong_answer_reason in all_iterator:
            header_str = StylizedStr(f'testcase {testcase_id}: ', TESTCASE_HEADER_COLOR, True)
            header_str += StylizedStr(short_verdict_names[run_verdict], RUN_VERDICT_COLORS[run_verdict], True)
            if run_verdict != RunVerdict.WRONG_ANSWER:
                # only the header when not wrong answer
                self.log.print(header_str)
            else:
                # the header with the wrong answer reason and the io otherwise
                header_str += StylizedStr(': ' + wrong_answer_reason, WRONG_ANSWER_REASON_COLOR, True)
                self.log.print(header_str)
                self.log.print(self.helper_io_one_testcase(
                    io_pair[0], main_output, io_pair[1]
                ))

    # MULTITESTS

    def multitests_split_result(self, testcase_id: int, io_file: str, split_result: bool) -> None:
        '''
        Print whether the split was successful.
        :param testcase_id: testcase's id
        :param io_file: one of 'input' or 'output'
        :param split_result: True if the io_file was split successfully or False otherwise
        '''
        split_str = StylizedStr(f'split testcase {testcase_id} {io_file} ')
        split_str += StylizedStr(('' if split_result else 'un') + 'successfully', Colors.DEFAULT, True)
        self.log.print(split_str)

    # IO

    def helper_io_format(self, io: str, end_with_newline: bool) -> str:
        '''
        Format the io string for printing by removing redundant newlines and omitting lines if there are too many.
        :param io: the io string
        :param end_with_newline: True if the formatted io should finish with a newline or False otherwise
        :return: the formatted io string
        '''
        io = io.rstrip('\n')
        io_lines = io.split('\n')
        if len(io_lines) > MAX_IO_LINES:
            formatted_io = '\n'.join(io_lines[:SHORT_IO_LINES])
            formatted_io += f'\n[omitted {len(io_lines) - SHORT_IO_LINES}/{len(io_lines)} lines]'
        else:
            formatted_io = io
        return formatted_io + ('\n' if end_with_newline else '')

    def helper_io_one_testcase(self, io_input: str, user_output: str, expected_output: str) -> StylizedStr:
        '''
        Get the string containing input, user output, and expected output for one testcase.
        :param io_input: the input
        :param user_output: the user output
        :param expected_output: the expected output
        :return: the io string for one testcase
        '''
        testcase_str = StylizedStr()
        io_names = ['input', 'output', 'expected']
        for io_id, (io_name, io_str) in enumerate(zip(io_names, [io_input, user_output, expected_output])):
            testcase_str += StylizedStr(io_name + '\n', IO_HEADER_COLOR)
            testcase_str += StylizedStr(self.helper_io_format(io_str, io_id != 2))
        return testcase_str

    # ARGUMENTS

    def helper_error_argument_header(self, arg_name: str) -> StylizedStr:
        '''
        Get the header for printing argument errors.
        :param arg_name: argument's name
        :return: the header for printing argument errors
        '''
        return StylizedStr('argument ') + StylizedStr(arg_name, ARGUMENT_COLOR)

    def expected_at_least_one_argument(self, arg_name: str) -> None:
        '''
        Print that the positional argument was not given.
        :param arg_name: argument's name
        '''
        self.log.print(
            self.helper_error_argument_header(arg_name)
            + StylizedStr(' expected at least 1 argument, got 0')
        )

    def not_enough_args_given(self, arg_name: str, num_args: int, num_given: int) -> None:
        '''
        Print that not enough arguments were given.
        :param arg_name: argument's name
        :param num_args: expected number of arguments
        :param num_given: number of arguments given
        '''
        self.log.print(
            self.helper_error_argument_header(arg_name)
            + StylizedStr(f' expected {num_args} {self.helper_get_plural('argument', num_args)}, got {num_given}')
        )

    def argument_not_int(self, arg_name: str, arg: str) -> None:
        '''
        Print that the argument was not an int.
        :param arg_name: argument's name
        :param arg: the argument given
        '''
        self.log.print(
            self.helper_error_argument_header(arg_name)
            + StylizedStr(f' expected an int, got "{arg}"')
        )

    def argument_not_float(self, arg_name: str, arg: str) -> None:
        '''
        Print that the argument was not a float.
        :param arg_name: argument's name
        :param arg: the argument given
        '''
        self.log.print(
            self.helper_error_argument_header(arg_name)
            + StylizedStr(f' expected a float, got "{arg}"')
        )

    def argument_not_in_choices(self, arg_name: str, arg: str, choices: list[str]) -> None:
        '''
        Print that the argument was not one of the choices.
        :param arg_name: argument's name
        :param arg: the argument given
        :param choices: the list of choices
        '''
        self.log.print(
            self.helper_error_argument_header(arg_name)
            + StylizedStr(f' expected one of ["{'", "'.join(choices)}"], got "{arg}"')
        )

    def argument_not_in_range(self, arg_name: str, arg: str, num_range: tuple[float, float]) -> None:
        '''
        Print that the argument was not in range.
        :param arg_name: argument's name
        :param arg: the argument given
        :param num_range: the range
        '''
        self.log.print(
            self.helper_error_argument_header(arg_name)
            + StylizedStr(f' expected to be in range [{num_range[0]}, {num_range[1]}], got "{arg}"')
        )

    def argument_help_str(self, arg_name: str, help_str: str) -> None:
        '''
        Print the help string for the argument.
        :param arg_name: argument's name
        :param help_str: the help string
        '''
        self.log.print(
            self.helper_error_argument_header(arg_name)
            + StylizedStr(f': {help_str}')
        )

    # COMMANDS

    def helper_error_command_header(self, command_name: str) -> StylizedStr:
        '''
        Get the header for printing command errors.
        :param command_name: command's name
        :return: the header for printing command errors
        '''
        return StylizedStr('command ') + StylizedStr(command_name, COMMAND_COLOR)

    def command_too_many_positional_args(self, command_name: str, first_extra_arg: str) -> None:
        '''
        Print that too many positional arguments were given.
        :param command_name: command's name
        :param first_extra_arg: the first extra positional argument given
        '''
        self.log.print(
            self.helper_error_command_header(command_name) +
            StylizedStr(f': too many positional arguments were given, first extra one was "{first_extra_arg}"')
        )

    def command_repeated_optional_argument(self, command_name: str, arg_name: str) -> None:
        '''
        Print that the optional argument was repeated.
        :param command_name: command's name
        :param arg_name: argument's name
        '''
        self.log.print(
            self.helper_error_command_header(command_name) + StylizedStr(': ')
            + self.helper_error_argument_header(arg_name)
            + StylizedStr(f' was repeated')
        )

    def command_flag_is_not_optional_argument(self, command_name: str, flag: str) -> None:
        '''
        Print that the flag isn't an optional argument.
        :param command_name: command's name
        :param flag: the given flag
        '''
        self.log.print(
            self.helper_error_command_header(command_name)
            + StylizedStr(f': flag "{flag}" is not an optional argument')
        )

    def command_too_many_optional_arguments_mutually_exclusive(self, command_name: str) -> None:
        '''
        Print that more than one optional argument was given even though they are mutually exclusive.
        :param command_name: command's name
        '''
        self.log.print(
            self.helper_error_command_header(command_name)
            + StylizedStr(': at least two optional arguments were given but they are mutually exclusive')
        )

    def helper_command_positional_argument_usage(self, arg_name: str, arg_type: str) -> StylizedStr:
        '''
        Get the usage str for a positional argument.
        :param arg_name: argument's name
        :param arg_type: argument's type
        :return: the usage str for a positional argument
        '''
        usage_str = StylizedStr(arg_name, ARGUMENT_COLOR)
        if arg_type != '1':
            usage_str += StylizedStr(f'[{arg_type}]')
        return usage_str

    def helper_command_optional_argument_usage(self, flag: str, short_name: str, arg_type: str,
                                               brackets: bool = True) -> StylizedStr:
        '''
        Get the usage str for an optional argument.
        :param flag: argument's short flag
        :param short_name: argument's short name
        :param arg_type: argument's type
        :param brackets: whether to print within brackets
        :return: the usage str for an optional argument
        '''
        usage_str = StylizedStr()
        if brackets:
            usage_str += StylizedStr('[')
        usage_str += StylizedStr(flag, ARGUMENT_COLOR)
        if arg_type != '0':
            usage_str += StylizedStr(f' {short_name}')
            if arg_type != '1':
                usage_str += StylizedStr(f'[{arg_type}]')
        if brackets:
            usage_str += StylizedStr(']')
        return usage_str

    def helper_command_help_str(self, help_str: list[tuple[str, str]]) -> StylizedStr:
        '''
        Get the help string for the command. arg_type is 'f' when arg_name is a flag
        :param help_str: the help string, even indices contain (help_str, ""), odd ones contain (arg_name, arg_type)
        :return: the help string for the command
        '''
        help_stylized_str = StylizedStr()
        for idx, help_str_pair in enumerate(help_str):
            if idx != 0 and (len(help_str_pair[0]) == 0 or help_str_pair[0][0] not in (',', '.')):  # no space on '.,'
                help_stylized_str += StylizedStr(' ')
            if idx % 2 == 0:  # help str
                help_stylized_str += StylizedStr(help_str_pair[0])
            else:  # argument
                short_name, arg_type = help_str_pair
                help_stylized_str += StylizedStr(short_name, ARGUMENT_COLOR)
                assert arg_type != '0'  # can't print num_args == 0
                if arg_type not in ('f', '1'):
                    help_stylized_str += StylizedStr(f'[{arg_type}]')
        return help_stylized_str

    def command_help_str(self, command_name: str, positional_arguments: list[tuple[str, str]],
                         optional_arguments: list[tuple[str, str, str]], help_str: list[str],
                         mutually_exclusive: bool) -> None:
        '''
        Print the help string for the command.
        :param command_name: the command's name
        :param positional_arguments: the positional arguments, list of (short_name, arg_type)
        :param optional_arguments: the optional arguments, list of (short_name, short_flag, arg_type)
        :param help_str: the help string, odd indices contain arguments' short names or short flags
        :param mutually_exclusive: are optional arguments mutually exclusive
        '''
        # the usage str
        usage_str = StylizedStr(command_name, COMMAND_COLOR)
        for short_name, arg_type in positional_arguments:
            usage_str += StylizedStr(' ') + self.helper_command_positional_argument_usage(short_name, arg_type)
        if not mutually_exclusive or len(optional_arguments) == 0:  # print one by one
            for short_name, flag, arg_type in optional_arguments:
                usage_str += StylizedStr(' ')
                usage_str += self.helper_command_optional_argument_usage(flag, short_name, arg_type, True)
        else:  # print together since mutually exclusive
            usage_str += StylizedStr(' [')
            for idx, (short_name, flag, arg_type) in enumerate(optional_arguments):
                if idx > 0:
                    usage_str += StylizedStr(' | ')
                usage_str += self.helper_command_optional_argument_usage(flag, short_name, arg_type, False)
            usage_str += StylizedStr(']')
        self.log.print(usage_str)

        # the help str
        arg_types: dict[str, str] = (
            {short_name: arg_type for short_name, arg_type in positional_arguments}
            | {short_name: arg_type for short_name, _, arg_type in optional_arguments}
            | {flag: 'f' for _, flag, _ in optional_arguments}
        )
        help_str_pairs: list[tuple[str, str]] = [
            (help_str_pair, '') if idx % 2 == 0 else (help_str_pair, arg_types[help_str_pair])
            for idx, help_str_pair in enumerate(help_str)
        ]
        self.log.print(self.helper_command_help_str(help_str_pairs))

    # COMMAND SUITES

    def command_suite_no_command_given(self) -> None:
        '''
        Print that no command was given.
        '''
        self.log.print(StylizedStr('no command was given'))

    def command_suite_not_a_command(self, command_name: str) -> None:
        '''
        Print that the given command is not a command.
        :param command_name: the given command
        '''
        self.log.print(StylizedStr(f'"{command_name}" is not a command'))
