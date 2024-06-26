'''Implements the TestCase class.'''

from enum import IntEnum
from typing import Optional, Literal, TypeVar, Iterator
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
    '''A mutable testcase.'''
    testcase_id: int  # the testcase's id
    testcase_type: TestCaseType  # the testcase's type
    entire_testcase: IOPair  # the entire testcase
    multiple_testcases: Optional[IOPair]  # the split testcases if testcase type is scraped
    message: Messages  # the message object that handles printing

    def __init__(self, testcase_id: int, testcase_type: TestCaseType,
                 entire_testcase: IOPair, multiple_testcases: Optional[IOPair], message: Messages,
                 init_mode: Literal['online', 'offline', 'not_scraped'], io_pair: Optional[tuple[str, str]] = None,
                 multitests_inputs: Optional[list[str]] = None, multitests_outputs: Optional[list[str]] = None) -> None:
        '''
        Init TestCase.
        All of io, multitests_inputs and multitests_outputs should be None when parsing offline.
        multitests_inputs should have length one longer than multitests_outputs when both given
        to also contain num_testcases as the first element.
        Neither of multitests_inputs and multitests_outputs should contain newlines at the end of each multitest.
        :param testcase_id: the testcase's id
        :param testcase_type: the testcase's type
        :param entire_testcase: the entire testcase
        :param multiple_testcases: the multitest files if testcase type is scraped, or None otherwise
        :param message: the message object that handles printing
        :param init_mode: the init mode, 'online' or 'offline' when parsing or 'not_scraped' when not scraped
        :param io_pair: the (io_input, io_output) pair or None when parsing offline
        :param multitests_inputs: the multitests inputs if split successfully or None otherwise
        :param multitests_outputs: the multitests outputs if split successfully or None otherwise
        '''
        self.testcase_id = testcase_id
        self.testcase_type = testcase_type
        self.entire_testcase = entire_testcase
        self.multiple_testcases = multiple_testcases
        self.message = message

        # asserts
        # check that the type isn't scraped when init_mode is 'not_scraped'
        if init_mode == 'not_scraped':
            assert testcase_type != TestCaseType.SCRAPED
        # check that io is given when parsing online or not scraped
        if init_mode == 'online' or init_mode == 'not_scraped':
            assert io_pair is not None
        # check that none of io, multitests_inputs, and multitests_outputs is given when parsing offline
        if init_mode == 'offline':
            assert io_pair is None and multitests_inputs is None and multitests_outputs is None
        # check that multiple_testcases are given when type is scraped
        assert bool(self.testcase_type == TestCaseType.SCRAPED) == bool(self.multiple_testcases is not None)
        # check that multitests_inputs and multitests_outputs are not given when type isn't scraped
        if self.testcase_type != TestCaseType.SCRAPED:
            assert multitests_inputs is None and multitests_outputs is None

        # create io files
        if init_mode == 'online' or init_mode == 'not_scraped':
            assert io_pair is not None
            self.create_io_files(io_pair)

        # rewrite the multitest files if needed
        if self.testcase_type == TestCaseType.SCRAPED:
            self.set_multitest_files(multitests_inputs, multitests_outputs)

    def create_io_files(self, io: tuple[str, str]) -> None:
        '''
        Create testcase's io files.
        :param io: the (io_input, io_output) pair
        '''
        self.entire_testcase.io_input.write_file(io[0])
        self.entire_testcase.io_output.write_file(io[1])
        if self.testcase_type == TestCaseType.SCRAPED:
            assert self.multiple_testcases is not None  # assert scraped type
            self.multiple_testcases.io_input.write_file('')
            self.multiple_testcases.io_output.write_file('')

    def check_multitest_files(self) -> tuple[bool, bool]:
        '''
        Check if each multitest file starts with the header and contains the right tokens.
        Can only be called if type is scraped.
        :return: for both input and output,
                 True if it starts with the header and contains the right tokens or False otherwise
        '''
        # get the current multitest input and output
        assert self.multiple_testcases is not None  # assert scraped type
        multitest_input = self.multiple_testcases.io_input.read_file()
        multitest_output = self.multiple_testcases.io_output.read_file()

        # get the tokens from the entire testcase
        entire_input_tokens = self.entire_testcase.io_input.read_file().split()
        entire_output_tokens = self.entire_testcase.io_output.read_file().split()

        # check the header and tokens
        return (
            multitest_input.startswith(MULTITEST_HEADER)
            and multitest_input.removeprefix(MULTITEST_HEADER).split() == entire_input_tokens,
            multitest_output.startswith(MULTITEST_HEADER)
            and multitest_output.removeprefix(MULTITEST_HEADER).split() == entire_output_tokens
        )

    def set_multitest_files(self, multitests_inputs: Optional[list[str]] = None,
                            multitests_outputs: Optional[list[str]] = None) -> None:
        '''
        Set multitest files.
        When parsing online, multitests_inputs and multitests_outputs can be given when split successfully.
        Can also be called to fix the multitest headers.
        multitests_inputs should have length one longer than multitests_outputs when both given
        to also contain num_testcases as the first element.
        Neither of multitests_inputs and multitests_outputs should contain newlines at the end of each multitest.
        Can only be called if type is scraped.
        :param multitests_inputs: the multitests inputs if parsing online and split successfully or None otherwise
        :param multitests_outputs: the multitests outputs if parsing online and split successfully or None otherwise
        '''
        # check multitest files
        assert self.multiple_testcases is not None  # assert scraped type
        check_multitest_input, check_multitest_output = self.check_multitest_files()

        # input
        if not check_multitest_input:
            if multitests_inputs is not None:  # the input was split
                self.multiple_testcases.io_input.write_file(MULTITEST_HEADER + '\n\n'.join(multitests_inputs))
            else:  # the input wasn't split, use io_input
                self.multiple_testcases.io_input.write_file(
                    MULTITEST_HEADER + self.entire_testcase.io_input.read_file()
                )

        # output
        if not check_multitest_output:
            if multitests_outputs is not None:  # the output was split
                self.multiple_testcases.io_output.write_file(MULTITEST_HEADER + '\n\n'.join(multitests_outputs))
            else:  # the output wasn't split, use io_output
                self.multiple_testcases.io_output.write_file(
                    MULTITEST_HEADER + self.entire_testcase.io_output.read_file()
                )

    def get_name(self) -> str:
        '''
        Get the testcase's name with its id and type.
        :return: the testcase's name
        '''
        type_char = {
            TestCaseType.SCRAPED: 's',
            TestCaseType.USER_ADDED: 'u',
            TestCaseType.RANDOM: 'n',
        }
        return f'{self.testcase_id}{type_char[self.testcase_type]}'

    def check_multitests(self) -> tuple[bool, bool]:
        '''
        Check if the multitest files are split correctly. Can only be called if type is scraped.
        :return: for both input and output, True if split correctly or False otherwise
        '''
        # read multitest files without the header and check them
        assert self.multiple_testcases is not None  # assert scraped type
        multitest_input = self.multiple_testcases.io_input.read_file().removeprefix(MULTITEST_HEADER)
        multitest_output = self.multiple_testcases.io_output.read_file().removeprefix(MULTITEST_HEADER)
        check_multitest_input, check_multitest_output = self.check_multitest_files()

        # if input check is False, neither can be split correctly
        if not check_multitest_input:
            return False, False

        # find the number of multitests
        multitest_input_line = multitest_input.splitlines()
        first_input_line = multitest_input_line[0] if len(multitest_input_line) >= 1 else ''
        if first_input_line == '' or not first_input_line.isdigit():
            # not a multitest problem since the first line isn't t
            return False, False
        num_multitests = int(first_input_line)

        # check no double empty lines and the double newline counts
        return (
            multitest_input.find('\n\n\n') == -1  # no double empty lines
            and bool(multitest_input.count('\n\n') == num_multitests),  # split at t
            multitest_output.find('\n\n\n') == -1  # no double empty lines
            and check_multitest_output  # header and tokens check
            and bool(multitest_output.count('\n\n') == num_multitests - 1)  # no t in the output
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

        # assert the lengths of multitest inputs and outputs
        assert len(multitest_inputs) == num_multitests and len(multitest_outputs) == num_multitests

        # returns io pairs as strings
        return list(zip(multitest_inputs, multitest_outputs))

    def edit_multitests(self, only_necessary: bool, shortcircuit: bool) -> bool:
        '''
        Attempt to split the io files into multitests.
        If only_necessary is True, only the io files that aren't correctly split will be split,
        otherwise both input and output will be split.
        Can only be called if the testcase type is scraped.
        :param only_necessary: split only the necessary io files or both input and output
        :param shortcircuit: when True, returns False immediately when an io file stays not split correctly
        :return: True if all files are split correctly, False otherwise
        '''
        assert self.multiple_testcases is not None  # assert scraped type

        # set multitest files
        self.set_multitest_files()

        # attempt split on both input and output
        both_io_tuples: list[tuple[Literal['input', 'output'], File, int]] = [
            ('input', self.multiple_testcases.io_input, 0),
            ('output', self.multiple_testcases.io_output, 1)
        ]
        for io_file, multitest_file, check_id in both_io_tuples:
            io_file_check = self.check_multitests()[check_id]  # check if split correctly
            if not io_file_check or not only_necessary:  # only attempt split if necessary
                if self.message.multitests_edit_option(self.testcase_id, io_file, io_file_check):  # user wants to split
                    # wait on the user to edit the multitests in the text editor
                    Execution.execute(
                        configs.text_editor_command_wait + [str(multitest_file)],
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

    def check_multitest_mode(self) -> bool:
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
                self.entire_testcase.io_input.read_file(),
                self.entire_testcase.io_output.read_file()
            )
            return [entire_testcase]
        else:
            # split into multitests
            return [
                TestCaseRun(f'{self.testcase_id}-{idx + 1}', io_input, io_output)
                for idx, (io_input, io_output) in enumerate(self.get_multitests())
            ]

    def delete(self) -> None:
        '''
        Delete the testcase.
        '''
        # delete all io files
        self.entire_testcase.io_input.delete_file()
        self.entire_testcase.io_output.delete_file()
        if self.testcase_type == TestCaseType.SCRAPED:
            assert self.multiple_testcases is not None  # assert scraped type
            self.multiple_testcases.io_input.delete_file()
            self.multiple_testcases.io_output.delete_file()


class TestCaseSet:
    '''A mutable testcase set.'''
    all_testcases: list[TestCase]  # the testcases
    message: Messages  # the message object that handles printing

    def __init__(self, num_testcases: int, init_mode: Literal['online', 'offline'], message: Messages,
                 entire_testcases: list[IOPair], multiple_testcases: list[Optional[IOPair]],
                 io_pairs: Optional[list[tuple[str, str]]],
                 io_multitest_inputs: Optional[list[list[str]]], io_multitest_outputs: Optional[list[list[str]]],
                 testcase_types: Optional[list[TestCaseType]]) -> None:
        '''
        Init TestCaseSet.
        io_multitest_inputs and io_multitest_outputs shouldn't be given when parsing offline.
        The lengths of all lists should be num_testcases when not None.
        :param num_testcases: the number of testcases
        :param init_mode: the init mode, 'online' when parsing online or 'offline' when parsing offline
        :param message: the message object that handles printing
        :param entire_testcases: the entire testcase files
        :param multiple_testcases: the multiple testcase files for scraped problems or None for not scraped ones
        :param io_pairs: (io_input, io_output) pairs for each testcase, should be given when parsing online
        :param io_multitest_inputs: the multitests inputs if split successfully or None otherwise
        :param io_multitest_outputs: the multitests outputs if split successfully or None otherwise
        :param testcase_types: the testcases types, should be given when parsing offline
        '''
        # assert the lengths match
        T = TypeVar('T')

        def check_len(list_arg: Optional[list[T]]) -> None:
            '''
            Assert that the length of the list is num_testcases when not None.
            :param list_arg: the list
            '''
            if list_arg is not None:
                assert len(list_arg) == num_testcases

        check_len(entire_testcases)
        check_len(multiple_testcases)
        check_len(io_pairs)
        check_len(io_multitest_inputs)
        check_len(io_multitest_outputs)

        # assert the right arguments are given for each mode
        assert bool(init_mode == 'online') == bool(io_pairs is not None)
        if init_mode == 'offline':
            assert io_multitest_inputs is None and io_multitest_outputs is None
        assert bool(init_mode == 'offline') == bool(testcase_types is not None)

        # set message and all_testcases
        self.message = message
        self.all_testcases: list[TestCase] = []

        # parsing online
        if init_mode == 'online':
            assert io_pairs is not None  # given when parsing online
            for io_id in range(num_testcases):
                # get testcase data
                entire_testcase = entire_testcases[io_id]
                multiple_testcase = multiple_testcases[io_id]
                io_pair = io_pairs[io_id]
                io_multitest_input: Optional[list[str]] = None
                if io_multitest_inputs is not None:
                    io_multitest_input = io_multitest_inputs[io_id]
                io_multitest_output: Optional[list[str]] = None
                if io_multitest_outputs is not None:
                    io_multitest_output = io_multitest_outputs[io_id]

                # create the testcase
                self.all_testcases.append(
                    TestCase(
                        io_id + 1, TestCaseType.SCRAPED,
                        entire_testcase, multiple_testcase,
                        self.message, 'online',
                        io_pair, io_multitest_input, io_multitest_output
                    )
                )

        # parsing offline
        if init_mode == 'offline':
            assert testcase_types is not None  # given when parsing offline
            for io_id in range(num_testcases):
                # get testcase data
                entire_testcase = entire_testcases[io_id]
                multiple_testcase = multiple_testcases[io_id]
                testcase_type = testcase_types[io_id]

                # create the testcase
                self.all_testcases.append(
                    TestCase(
                        io_id + 1, testcase_type,
                        entire_testcase, multiple_testcase,
                        self.message, 'offline',
                        None, None, None  # testcases are in the files
                    )
                )

    def __iter__(self) -> Iterator[TestCase]:
        '''
        Iterate over all testcases.
        :return: an iterator of the testcases
        '''
        return iter(self.all_testcases.copy())

    def __len__(self) -> int:
        '''
        Get the number of testcases.
        :return: the number of testcases
        '''
        return len(self.all_testcases)

    def get_scraped_testcases(self) -> list[TestCase]:
        '''
        Get the list of scraped testcases.
        :return: the list of scraped testcases
        '''
        return [testcase for testcase in self.all_testcases if testcase.testcase_type == TestCaseType.SCRAPED]

    def get_num_multitests(self) -> int:
        '''
        Get the number of multitests or 0 if not split correctly.
        :return: the number of multitests
        '''
        if all(testcase.check_multitest_mode() for testcase in self.all_testcases):
            return sum(len(testcase.get_testcases(TestCaseMode.MULTIPLE)) for testcase in self.all_testcases)
        else:
            return 0

    def check_multitest_mode(self) -> bool:
        '''
        Check if the multitest mode can be set.
        :return: True if the multitest mode can be set for all testcases, False otherwise
        '''
        return all(testcase.check_multitest_mode() for testcase in self.all_testcases)

    def set_multitest_mode(self) -> bool:
        '''
        Attempt to set testcase mode to multitests.
        :return: True if multitest mode can be set, False otherwise
        '''
        # check if multitest mode can be set
        if all(testcase.check_multitest_mode() for testcase in self.all_testcases):
            return True

        # try split
        self.message.setting_multitest_mode_needs_split()
        if all(testcase.edit_multitests(True, True) for testcase in self.get_scraped_testcases()):
            self.message.multitest_mode_set_successfully()
            return True
        else:
            self.message.multitest_mode_set_unsuccessfully()
            return False

    def get_testcase_types(self) -> list[TestCaseType]:
        '''
        Get the types of the testcases.
        :return: the types of the testcases
        '''
        return [testcase.testcase_type for testcase in self.all_testcases]

    def get_num_scraped(self) -> int:
        '''
        Get the number of scraped testcases.
        :return: the number of scraped testcases
        '''
        return sum(1 if testcase.testcase_type == TestCaseType.SCRAPED else 0 for testcase in self.all_testcases)

    def delete_remove_testcases(self, remove_cnt: int) -> None:
        '''
        Delete the last remove_cnt testcases.
        :param remove_cnt: the number of testcases to remove, can't include scraped testcases
        '''
        if self.message.io_remove_keep_testcases(
            [testcase.get_name() for testcase in self.all_testcases[-remove_cnt:]]
        ):
            for io_id in range(len(self) - remove_cnt, len(self)):
                self.all_testcases[io_id].delete()
            self.all_testcases = self.all_testcases[:-remove_cnt]

    def delete_keep_testcases(self, keep_cnt: int) -> None:
        '''
        Keep the first keep_cnt testcases and delete the rest.
        :param keep_cnt: the number of testcases to keep, the deleted ones can't include scraped testcases
        '''
        if self.message.io_remove_keep_testcases(
                [testcase.get_name() for testcase in self.all_testcases[keep_cnt:]]
        ):
            for io_id in range(keep_cnt, len(self)):
                self.all_testcases[io_id].delete()
            self.all_testcases = self.all_testcases[:keep_cnt]

    def edit_multitests(self, testcase_id: Optional[int]) -> None:
        '''
        Edit multitests.
        :param testcase_id: the testcase whose multitests to edit, should be scraped, or None if all should be edited
        '''
        if testcase_id is None:  # edit all
            for testcase in self.all_testcases:
                if testcase.testcase_type == TestCaseType.SCRAPED:
                    testcase.edit_multitests(False, False)
        else:  # edit one
            self.all_testcases[testcase_id - 1].edit_multitests(False, False)

    def add_user_testcase(self, entire_testcase: IOPair) -> None:
        '''
        Add a user created testcase.
        :param entire_testcase: the entire testcase files
        '''
        # create the testcase
        testcase_id = len(self) + 1
        new_testcase = TestCase(
            testcase_id, TestCaseType.USER_ADDED,
            entire_testcase, None,
            self.message, 'not_scraped',
            ('', ''), None, None
        )
        self.all_testcases.append(new_testcase)

        # edit input and output
        both_pairs: list[tuple[Literal['input', 'output'], File]] = [
            ('input', entire_testcase.io_input),
            ('output', entire_testcase.io_output)
        ]
        for io_file, edit_file in both_pairs:
            self.message.editing_testcase(new_testcase.get_name(), io_file, True)
            Execution.execute(configs.text_editor_command_wait + [str(edit_file)], None)

    def edit_testcase(self, testcase_id: int) -> None:
        '''
        Edit a testcase.
        :param testcase_id: testcase's id, can't be scraped
        '''
        # get the testcase and assert it isn't scraped
        testcase = self.all_testcases[testcase_id - 1]
        assert testcase.testcase_type != TestCaseType.SCRAPED

        # edit input and output
        both_pairs: list[tuple[Literal['input', 'output'], File]] = [
            ('input', testcase.entire_testcase.io_input),
            ('output', testcase.entire_testcase.io_output)
        ]
        for io_file, edit_file in both_pairs:
            self.message.editing_testcase(testcase.get_name(), io_file, False)
            Execution.execute(configs.text_editor_command_wait + [str(edit_file)], None)

    def view_testcases(self, testcase_mode: TestCaseMode, testcase_id: Optional[int]) -> None:
        '''
        View testcases.
        :param testcase_mode: the testcase mode
        :param testcase_id: the testcase id if only viewing one or None if viewing all testcases
        '''
        # get the testcases to view
        view_testcases = self.all_testcases if testcase_id is None else [self.all_testcases[testcase_id - 1]]

        # get the testcase names, testcase ids, and io_pairs
        testcase_names = [testcase.get_name() for testcase in view_testcases]
        view_testcases_run = sum((testcase.get_testcases(testcase_mode) for testcase in view_testcases), [])
        testcase_ids = [view_testcase.id for view_testcase in view_testcases_run]
        io_pairs = [(view_testcase.io_input, view_testcase.io_output) for view_testcase in view_testcases_run]

        # print the testcases
        self.message.view_testcases(testcase_names, testcase_ids, io_pairs)
