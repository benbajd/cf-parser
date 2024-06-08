from typing import TypeVar, Optional
from prints import Print, StylizedStr, Colors
from verdicts import CompileVerdict, RunVerdict
from testcases import IOPair

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

MAX_IO_LINES = 50  # max number of io lines before cutting off the end
SHORT_IO_LINES = 20  # number of io lines displayed when over the limit


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

    # RUNNER

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
        Print the runner finish after at least one file get a compilation error.
        :param compile_verdicts: the compile verdicts, first file is main, second is custom checker (optional)
        :param total_time: the total runner time elapsed
        '''
        # print time elapsed
        self.log.update_previous(StylizedStr(f'took {total_time:.3f}s'))

        # print the compilation error message
        final_str = StylizedStr('compilation error, stopping: ')
        file_names = ['main', 'checker']
        compilation_errors = [
            file_name for file_name, compile_verdict in zip(file_names, compile_verdicts)
            if compile_verdict == CompileVerdict.COMPILATION_ERROR
        ]
        final_str += StylizedStr(
            'CE: ' + ', '.join(compilation_errors),
            COMPILE_VERDICT_COLORS[CompileVerdict.COMPILATION_ERROR],
            True
        )
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

    def runner_finish_after_run(self, run_verdicts: list[RunVerdict], testcase_ids: list[str], to_run: list[IOPair],
                                main_outputs: list[str], wrong_answer_reasons: list[str], total_time: float) -> None:
        '''
        Print the runner finish by printing all io for testcases that weren't accepted.
        :param run_verdicts: the run verdicts
        :param testcase_ids: the ids of testcases, each should be 't' for one tests and 't-s' for multitests
        :param to_run: the inputs and expected outputs for each testcase
        :param main_outputs: the output of main on each of the testcases
        :param wrong_answer_reasons: the wrong answer reason on each of the testcases with wrong answer
        :param total_time: the total runner time elapsed
        :return:
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
            header_str = StylizedStr(f'testcase {testcase_id}: ', Colors.DEFAULT, True)
            header_str += StylizedStr(short_verdict_names[run_verdict], RUN_VERDICT_COLORS[run_verdict], True)
            if run_verdict != RunVerdict.WRONG_ANSWER:
                # only the header when not wrong answer
                self.log.print(header_str)
            else:
                # the header with the wrong answer reason and the io otherwise
                header_str += StylizedStr(': ' + wrong_answer_reason, Colors.GRAY, True)
                self.log.print(header_str)
                self.log.print(self.helper_io_one_testcase(
                    io_pair.io_input.read_file(), main_output, io_pair.io_output.read_file()
                ))

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
            formatted_io += f'\n[omitted {len(io_lines) - SHORT_IO_LINES}]'
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
            testcase_str += StylizedStr(io_name + '\n', Colors.LIME)
            testcase_str += StylizedStr(self.helper_io_format(io_str, io_id != 2))
        return testcase_str
