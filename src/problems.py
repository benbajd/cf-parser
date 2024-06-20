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
from commandsuites import CommandSuiteProblem, CommandsProblem
from execution import Execution
import configs


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
        self.dirs.get_bruteforce().write_file(basefiles.BRUTEFORCE_CPP)
        self.dirs.get_generator().write_file(basefiles.GENERATOR_CPP)
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

    def process_commands(self, problem_ids: list[str]) -> tuple[CommandsProblem, dict[str, str]]:
        '''
        Process commands until a command not executable in problem is given.
        :param problem_ids: the problem ids in this contest
        :return: the first parsed command and args not executable in problem
        '''
        command_suite = CommandSuiteProblem(self.message, problem_ids, len(self.all_testcases))

        while True:
            # print the header and get the args
            args = self.message.get_command_problem(
                self.contest_id, self.problem_id,
                self.time_limit, self.count_testcases(),
                'o' if self.testcase_mode == TestCaseMode.ONE else 'm', self.checker.one_char_name
            )

            # parse the args
            parsed_command_args = command_suite.parse(args)

            # continue on errors
            if parsed_command_args is None:
                continue

            # execute the command
            command, parsed_args = parsed_command_args

            if command == CommandsProblem.EDIT:
                return command, parsed_args  # process by the contest

            elif command == CommandsProblem.CUSTOM_INVOCATION:
                # get the file name and file pair
                one_char_name: Literal['m', 'c', 'b', 'g'] = json.loads(parsed_args['file'])
                long_name = {'m': 'main', 'c': 'checker', 'b': 'bruteforce', 'g': 'generator'}[one_char_name]
                file_cpp, file_out = self.get_cpp_file_pair(one_char_name)

                # compile and run in custom invocation
                self.runner.custom_invocation(file_cpp, file_out, one_char_name, long_name)
                continue

    def get_cpp_file_pair(self, file: Literal['m', 'c', 'b', 'g']) -> tuple[File, File]:
        '''
        Get the .cpp and the .out pair of a file.
        :param file: the file, one of main, checker, bruteforce, or generator
        :return: the .cpp and the .out file pair
        '''
        file_pairs = {
            'm': (self.dirs.get_main(), self.dirs.get_main_compiled()),
            'c': (self.dirs.get_custom_checker(), self.dirs.get_custom_checker_compiled()),
            'b': (self.dirs.get_bruteforce(), self.dirs.get_bruteforce_compiled()),
            'g': (self.dirs.get_generator(), self.dirs.get_generator_compiled())
        }
        return file_pairs[file]

    def edit(self, file_cpp: Literal['m', 'c', 'b', 'g']) -> None:
        '''
        Edit the .cpp file of file_cpp.
        :param file_cpp: the .cpp file to edit, one of main, checker, bruteforce, or generator
        '''
        file_edit = self.get_cpp_file_pair(file_cpp)[0]
        Execution.execute(configs.code_editor_command + [str(file_edit)], None)

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

    def count_testcases(self) -> tuple[int, int]:
        '''
        Count the number of testcases in both testcase modes.
        :return: the number of testcases and the number of multitests or 0 if not split correctly
        '''
        num_testcases = len(self.all_testcases)
        num_multitests = 0
        if all(testcase.set_multitest_mode() for testcase in self.all_testcases):
            num_multitests = sum(len(testcase.get_testcases(TestCaseMode.MULTIPLE)) for testcase in self.all_testcases)
        return num_testcases, num_multitests
