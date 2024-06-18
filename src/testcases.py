'''Implements the TestCase class.'''

from enum import IntEnum
from typing import Optional
from paths import File
from dataclasses import dataclass
from messages import Messages
from execution import Execution
import configs


class TestCaseType(IntEnum):
    '''The type of testcase.'''
    SCRAPED = 0  # scraped from the platform
    USER_ADDED = 1  # added by the user
    RANDOM = 2  # found by random testing


class TestCaseMode(IntEnum):
    '''The mode for running testcases.'''
    ONE = 0  # run as an entire testcase
    MULTIPLE = 1  # split into multiple testcases when possible


@dataclass
class IOPair:
    '''The input output pair of a testcase.'''
    io_input: File  # the input
    io_output: File  # the output


@dataclass
class TestCaseRun:
    '''The testcase data needed for running.'''
    id: str  # testcase's id, 't' for one tests or 't-s' for multitests
    io_input: str  # testcase's input
    io_output: str  # testcase's output


MULTITEST_HEADER = '''\
# io split instructions:
# * add exactly one empty line after the first line of input that contains t
# * add exactly one empty line on splits
# * there should be exactly one empty line between the header and the io and one at the end
#   (both should already be there)
# * do not add any other comments nor change this header

'''


class TestCase:
    '''An immutable testcase.'''
    testcase_id: int  # the testcase's id
    testcase_type: TestCaseType  # the testcase's type
    entire_testcase: IOPair  # the entire testcase
    multiple_testcases: Optional[IOPair]  # the split testcases if testcase type is scraped
    message: Messages  # the message object that handles printing

    def __init__(self, testcase_id: int, testcase_type: TestCaseType,
                 entire_testcase: IOPair, multiple_testcases: Optional[IOPair], message: Messages,
                 multitests_inputs: Optional[list[str]] = None, multitests_outputs: Optional[list[str]] = None) -> None:
        '''
        Init TestCase.
        Both multitests_inputs and multitests_outputs should be None when parsing offline.
        multitests_inputs should have length one longer than multitests_outputs when both given
        to also contain num_testcases as the first element.
        Neither of multitests_inputs and multitests_outputs should contain newlines at the end of each multitest.
        :param testcase_id: the testcase's id
        :param testcase_type: the testcase's type
        :param entire_testcase: the entire testcase
        :param multiple_testcases: the multitest files if testcase type is scraped, or None otherwise
        :param message: the message object that handles printing
        :param multitests_inputs: the multitests inputs if split successfully or None otherwise
        :param multitests_outputs: the multitests outputs if split successfully or None otherwise
        '''
        self.testcase_id = testcase_id
        self.testcase_type = testcase_type
        self.testcase = entire_testcase
        self.multiple_testcases = multiple_testcases if multiple_testcases is not None else None
        self.message = message

        # check that multiple_testcases are given when type is scraped
        assert bool(self.testcase_type == TestCaseType.SCRAPED) == bool(self.multiple_testcases is not None)

        # check that multitests_inputs and multitests_outputs are not given when type isn't scraped
        if self.testcase_type != TestCaseType.SCRAPED:
            assert multitests_inputs is None and multitests_outputs is None

        # rewrite the multitest files if needed
        if self.testcase_type == TestCaseType.SCRAPED:
            # get the current multitest input and output
            assert self.multiple_testcases is not None
            multitest_input = self.multiple_testcases.io_input.read_file()
            multitest_output = self.multiple_testcases.io_output.read_file()

            # input
            if not multitest_input.startswith(MULTITEST_HEADER):
                if multitests_inputs is not None:  # the input was split
                    self.multiple_testcases.io_input.write_file(MULTITEST_HEADER + '\n\n'.join(multitests_inputs))
                else:  # the input wasn't split, use io_input
                    self.multiple_testcases.io_input.write_file(MULTITEST_HEADER + self.testcase.io_input.read_file())

            # output
            if not multitest_output.startswith(MULTITEST_HEADER):
                if multitests_outputs is not None:  # the output was split
                    self.multiple_testcases.io_output.write_file(MULTITEST_HEADER + '\n\n'.join(multitests_outputs))
                else:  # the output wasn't split, use io_output
                    self.multiple_testcases.io_output.write_file(MULTITEST_HEADER + self.testcase.io_output.read_file())

    def check_multitests(self) -> tuple[bool, bool]:
        '''
        Check if the multitest files are split correctly. Can only be called if type is scraped.
        :return: for both input and output, True if split correctly or False otherwise
        '''
        # assert scraped type and read multitest files without the header
        assert self.multiple_testcases is not None
        multitest_input = self.multiple_testcases.io_input.read_file().removeprefix(MULTITEST_HEADER)
        multitest_output = self.multiple_testcases.io_output.read_file().removeprefix(MULTITEST_HEADER)

        # find the number of multitests
        first_input_line = multitest_input.splitlines()[0]
        if not first_input_line.isdigit():  # not a multitest problem since the first line isn't t
            return False, False
        num_multitests = int(first_input_line)

        # check the double newline counts
        return (
            bool(multitest_input.count('\n\n') == num_multitests),  # split at t
            bool(multitest_output.count('\n\n') == num_multitests - 1)  # no t in the output
        )

    def get_multitests(self) -> list[tuple[str, str]]:
        '''
        Get the multitest input output str pairs.
        Can only be called if type is scraped and check_multitests() returns (True, True)
        :return: the multitest input output str pairs
        '''
        # assert scraped type and multitests are split
        assert self.multiple_testcases is not None
        assert all(self.check_multitests())

        # read multitest files
        multitest_input = self.multiple_testcases.io_input.read_file()
        multitest_output = self.multiple_testcases.io_output.read_file()

        # remove the header and the final newline
        multitest_input = multitest_input.removeprefix(MULTITEST_HEADER).removesuffix('\n')
        multitest_output = multitest_output.removeprefix(MULTITEST_HEADER).removesuffix('\n')

        # find the number of multitests
        num_multitests = int(multitest_input.splitlines()[0])

        # get the multitests
        multitest_inputs = [
            '1\n' + io_input + '\n'  # add t=1 as the first line and the final newline
            for io_input in multitest_input.split('\n\n')[1:]  # remove the first line with t
        ]
        multitest_outputs = [
            io_output + '\n'  # add the final newline
            for io_output in multitest_output.split('\n\n')
        ]

        # returns io pairs as strings
        return list(zip(multitest_inputs, multitest_outputs))

    def split_multitests(self, only_necessary: bool, shortcircuit: bool) -> bool:
        '''
        Attempts to split the io files into multitests.
        If only_necessary is True, only the io files that aren't correctly split will be split,
        otherwise both input and output will be split.
        Can only be called if the testcase type is scraped.
        :param only_necessary: split only the necessary io files or both input and output
        :param shortcircuit: when True, returns False immediately when an io file stays not split correctly
        :return: True if all files are split correctly, False otherwise
        '''
        assert self.multiple_testcases is not None  # assert scraped type

        # check whether split correctly initially
        input_check, output_check = self.check_multitests()

        # attempt split on both input and output
        both_io_tuples = [
            ('input', input_check, self.multiple_testcases.io_input, 0),
            ('output', output_check, self.multiple_testcases.io_output, 1)
        ]
        for io_file, io_file_check, multitest_file, check_id in both_io_tuples:
            if not io_file_check or not only_necessary:  # only attempt split if necessary
                decision_str = [
                    f'testcase {self.testcase_id} {io_file} ',
                    'is' if io_file_check else 'isn\'t',
                    ' split, would you like to split it?'
                ]
                if self.message.input_two_options(decision_str):  # user wants to split
                    # wait on the user to edit the multitests in the text editor
                    Execution.execute(
                        configs.TEXT_EDITOR_COMMAND_WAIT + [str(multitest_file)],
                        None
                    )
                    # check if split correctly
                    split_result = self.check_multitests()[check_id]
                    self.message.multitests_split_result(self.testcase_id, io_file, split_result)
                    if not split_result and shortcircuit:
                        return False
                else:  # user doesn't want to split
                    if not io_file_check and shortcircuit:
                        return False

        # check if both split correctly
        return all(self.check_multitests())

    def set_multitest_mode(self) -> bool:
        '''
        Check if the multitest mode can be set.
        :return: True if the multitest mode can be set, False otherwise
        '''
        # multitest mode can be set when multitests are split correctly with scraped or type isn't scraped
        return self.testcase_type != TestCaseType.SCRAPED or all(self.check_multitests())

    def get_testcases(self, mode: TestCaseMode) -> list[TestCaseRun]:
        '''
        Get the testcases to run.
        :param mode: the mode of running testcases, can only be multiple if io files are split correctly
        :return: the list of testcases to run,
                 ids are 't' when mode is ONE or the testcases isn't scraped or 't-s' otherwise
        '''
        # if mode is MULTIPLE and testcase type is scraped, check that it's split correctly
        if mode == TestCaseMode.MULTIPLE and self.testcase_type == TestCaseType.SCRAPED:
            assert all(self.check_multitests())

        # get the testcases
        if mode == TestCaseMode.ONE or self.testcase_type != TestCaseType.SCRAPED:
            # get the entire testcase
            entire_testcase = TestCaseRun(
                str(self.testcase_id),
                self.testcase.io_input.read_file(),
                self.testcase.io_output.read_file()
            )
            return [entire_testcase]
        else:
            # split into multitests
            return [
                TestCaseRun(f'{self.testcase_id}-{idx + 1}', io_input, io_output)
                for idx, (io_input, io_output) in enumerate(self.get_multitests())
            ]
