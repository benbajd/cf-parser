'''Implements the problem class.'''

import json
from typing import TypedDict, Optional, Literal
from scraper import ProblemOnline
from directories import DirsProblem
from paths import Folder, File
import basefiles
from messages import Messages
from testcases import TestCase, TestCaseMode, TestCaseType, IOPair
from checkers import Checker, CheckerTokens, CheckerYesNo, CheckerCustom
from runners import Runner


class ProblemOffline(TypedDict):
    '''A type representing an offline problem.'''
    name: str  # problem's name
    time_limit: float  # the time limit
    testcase_types: list[TestCaseType]  # testcase types
    testcase_mode: TestCaseMode  # the mode of running testcases
    checker_type: Literal['t'] | Literal['y'] | Literal['c']  # the type of the checker


class Problem:
    '''A mutable problem class.'''
    problem_id: str  # problem's id
    problem_name: str  # problem's name
    contest_id: str  # contest of the problem
    folder: Folder  # problem's folder
    dirs: DirsProblem  # problem's dirs handler
    message: Messages  # the message object that handles printing
    time_limit: float  # problem's time limit
    all_testcases: list[TestCase]  # problem's testcases
    testcase_mode: TestCaseMode  # the mode of running testcases
    checker: Checker  # the checker
    runner: Runner  # the runner

    def __init__(self, problem_id: str, contest_id: str, folder: Folder, message: Messages,
                 scraped_data: Optional[ProblemOnline]) -> None:
        '''
        Init the problem using the online data if scraped_data is provided or the offline data otherwise.
        :param problem_id: the problem
        :param contest_id: the contest
        :param folder: the problem's folder
        :param message: the message object that handles printing
        :param scraped_data: the online data if scraped initially
        '''
        self.problem_id = problem_id
        self.contest_id = contest_id
        self.folder = folder
        self.message = message
        self.dirs = DirsProblem(folder, contest_id, problem_id)
        self.runner = Runner(message)
        if scraped_data is not None:
            self.init_online(scraped_data)
        else:
            self.init_offline()

    def init_online(self, scraped_data: ProblemOnline) -> None:
        '''
        Init the problem using the online data.
        :param scraped_data: the online data
        '''
        # creating the problem files for the first time
        self.folder.create_folder()
        self.dirs.get_main().write_file(basefiles.MAIN_CPP)
        self.dirs.get_custom_checker().write_file(basefiles.CHECKER_CPP)
        self.all_testcases: list[TestCase] = []
        for io_id, (io_input, io_output) in enumerate(scraped_data['io']):
            # get the entire testcase
            input_file = self.dirs.get_input(io_id + 1)
            output_file = self.dirs.get_output(io_id + 1)
            input_file.write_file(io_input)
            output_file.write_file(io_output)

            # create empty multitest files
            multitest_input_file = self.dirs.get_input_multitest(io_id + 1)
            multitest_output_file = self.dirs.get_output_multitest(io_id + 1)
            multitest_input_file.write_file('')
            multitest_output_file.write_file('')

            # get multitests
            multitests_inputs: Optional[list[str]] = None
            if scraped_data['io_multitest_inputs'] is not None:
                multitests_inputs = scraped_data['io_multitest_inputs'][io_id]
            multitests_outputs: Optional[list[str]] = None
            if scraped_data['io_multitest_outputs'] is not None:
                multitests_outputs = scraped_data['io_multitest_outputs'][io_id]

            # create the testcase
            self.all_testcases.append(
                TestCase(
                    io_id + 1,
                    TestCaseType.SCRAPED,
                    IOPair(input_file, output_file),
                    IOPair(multitest_input_file, multitest_output_file),
                    self.message,
                    multitests_inputs,
                    multitests_outputs
                )
            )

        # set the problem data
        self.problem_name = scraped_data['name']
        self.time_limit = scraped_data['time_limit']
        self.testcase_mode = (  # multiple if all testcases have multitests else one
            TestCaseMode.MULTIPLE if all(testcase.set_multitest_mode() for testcase in self.all_testcases)
            else TestCaseMode.ONE
        )
        self.checker = CheckerTokens()  # tokens by default

        # update the problem data file
        self.update_problem_data()

    def init_offline(self) -> None:
        '''
        Init the problem using the offline data.
        '''
        # get the problem data
        problem_data: ProblemOffline = json.loads(self.dirs.get_problem_data().read_file())

        # set the problem data
        self.problem_name = problem_data['name']
        self.time_limit = problem_data['time_limit']
        self.testcase_mode = TestCaseMode(problem_data['testcase_mode'])
        if problem_data['checker_type'] == 't':  # TODO: factory method in checkers
            self.checker = CheckerTokens()
        elif problem_data['checker_type'] == 'y':
            self.checker = CheckerYesNo()
        elif problem_data['checker_type'] == 'c':
            self.checker = CheckerCustom(self.dirs.get_custom_checker(), self.dirs.get_custom_checker_compiled())
        else:
            assert False  # need more options

        # set the testcases
        self.all_testcases: list[TestCase] = []
        for io_id, testcase_type_int in enumerate(problem_data['testcase_types']):
            # get the testcase type and io files
            testcase_type = TestCaseType(testcase_type_int)
            entire_testcase = IOPair(self.dirs.get_input(io_id + 1), self.dirs.get_output(io_id + 1))

            # multitests files exist when testcase type is scraped
            multiple_testcases: Optional[IOPair] = None
            if testcase_type == TestCaseType.SCRAPED:
                multiple_testcases = IOPair(
                    self.dirs.get_input_multitest(io_id + 1), self.dirs.get_output_multitest(io_id + 1)
                )

            # create the testcase
            self.all_testcases.append(TestCase(
                io_id + 1,
                TestCaseType(testcase_type),
                entire_testcase,
                multiple_testcases,
                self.message,
                None, None  # multitests are in the files
            ))

    def update_problem_data(self) -> None:
        '''
        Update the problem data file.
        '''
        problem_data: ProblemOffline = {
            'name': self.problem_name,
            'time_limit': self.time_limit,
            'testcase_types': [testcase.testcase_type for testcase in self.all_testcases],
            'testcase_mode': self.testcase_mode,
            'checker_type': self.checker.one_char_name,
        }
        self.dirs.get_problem_data().write_file(json.dumps(problem_data))

    def run(self) -> None:
        '''
        Run the problem.
        '''
        self.runner.run(
            self.all_testcases,
            self.dirs.get_main(),
            self.dirs.get_main_compiled(),
            self.time_limit,
            self.checker,
            self.testcase_mode
        )
