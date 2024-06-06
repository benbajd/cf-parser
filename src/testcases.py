'''Implements the TestCase class.'''

from enum import IntEnum
from typing import Optional
from paths import File
from dataclasses import dataclass


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


class TestCase:
    '''An immutable testcase.'''
    testcase_id: int  # the testcase's id
    testcase_type: TestCaseType  # the testcase's type
    entire_testcase: IOPair  # the entire testcase
    multiple_testcases: Optional[list[IOPair]]  # the split testcases if the testcase is a multiple testcase

    def __init__(self, testcase_id: int, testcase_type: TestCaseType,
                 entire_testcase: IOPair, multiple_testcases: Optional[list[IOPair]]) -> None:
        '''
        Init TestCase.
        :param testcase_id: the testcase's id
        :param testcase_type: the testcase's type
        :param entire_testcase: the entire testcase
        :param multiple_testcases: a list of split testcases if it's a multiple testcase else None
        '''
        self.testcase_id = testcase_id
        self.testcase_type = testcase_type
        self.testcase = entire_testcase
        self.multiple_testcases = multiple_testcases.copy() if multiple_testcases is not None else None

    def get_testcases(self, mode: TestCaseMode) -> list[IOPair]:
        '''
        Get the testcases to run.
        :param mode: the mode of running testcases
        :return: the entire testcase when the mode is ONE or the testcase isn't a multiple testcase
                 or the multiple testcases otherwise
        '''
        if mode == TestCaseMode.ONE or self.multiple_testcases is None:
            return [self.testcase]
        else:
            return self.multiple_testcases.copy()
