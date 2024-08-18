'''Implements the problem class.'''

import json
from typing import TypedDict, Optional, Literal
from scraper import ProblemOnline
from directories import DirsProblem
from paths import Folder, File
import basefiles
from messages import Messages
from testcases import TestCase, TestCaseMode, TestCaseType, IOPair, TestCaseSet
import checkers
from checkers import Checker
from runners import Runner
from commandsuites import CommandSuiteProblem, CommandsProblem
from execution import Execution
from configs import Configs


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
    config: Configs  # the configs object storing configs
    time_limit: float  # problem's time limit
    testcase_set: TestCaseSet  # problem's testcases
    testcase_mode: TestCaseMode  # the mode of running testcases
    checker: Checker  # the checker
    runner: Runner  # the runner

    def __init__(self, problem_id: str, contest_id: str, folder: Folder, message: Messages, config: Configs,
                 scraped_data: Optional[ProblemOnline]) -> None:
        '''
        Init the problem using the online data if scraped_data is provided or the offline data otherwise.
        :param problem_id: the problem
        :param contest_id: the contest
        :param folder: the problem's folder
        :param message: the message object that handles printing
        :param config: the configs object storing configs
        :param scraped_data: the online data if scraped initially
        '''
        self.problem_id = problem_id
        self.contest_id = contest_id
        self.folder = folder
        self.message = message
        self.config = config
        self.dirs = DirsProblem(folder, contest_id, problem_id)
        self.runner = Runner(self.message, self.config)
        if scraped_data is not None:
            self.init_online(scraped_data)
        else:
            self.init_offline()

    def init_online(self, scraped_data: ProblemOnline) -> None:
        '''
        Init the problem using the online data.
        :param scraped_data: the online data
        '''
        # create the folder
        self.folder.create_folder()

        # creating the edit files
        # TODO: move creating files into classes
        cpp_header = self.config.cpp_header.rstrip('\n') + '\n\n'  # the cpp header with an empty line at the end
        self.dirs.get_main().write_file(cpp_header + basefiles.MAIN_CPP)
        self.dirs.get_custom_checker().write_file(cpp_header + basefiles.CHECKER_CPP)
        self.dirs.get_bruteforce().write_file(cpp_header + basefiles.BRUTEFORCE_CPP)
        self.dirs.get_generator().write_file(cpp_header + basefiles.GENERATOR_CPP)

        # set the testcase set
        num_testcases = len(scraped_data['io'])
        self.testcase_set = TestCaseSet(
            num_testcases, 'online', self.message, self.config,
            [
                IOPair(self.dirs.get_input(io_id + 1), self.dirs.get_output(io_id + 1))
                for io_id in range(num_testcases)
            ],
            [
                IOPair(self.dirs.get_input_multitest(io_id + 1), self.dirs.get_output_multitest(io_id + 1))
                for io_id in range(num_testcases)
            ],
            scraped_data['io'], scraped_data['io_multitest_inputs'], scraped_data['io_multitest_outputs'],
            None
        )

        # set the problem data
        self.problem_name = scraped_data['name']
        self.time_limit = scraped_data['time_limit']
        self.testcase_mode = (  # multiple if all testcases have multitests else one
            TestCaseMode.MULTIPLE if self.testcase_set.check_multitest_mode()
            else TestCaseMode.ONE
        )
        self.checker = checkers.get_checker('t')  # tokens by default

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
        self.checker = checkers.get_checker(
            problem_data['checker_type'],
            self.dirs.get_custom_checker(),
            self.dirs.get_custom_checker_compiled()
        )

        # set the testcase_set
        num_testcases = len(problem_data['testcase_types'])
        self.testcase_set = TestCaseSet(
            num_testcases, 'offline', self.message, self.config,
            [
                IOPair(self.dirs.get_input(io_id + 1), self.dirs.get_output(io_id + 1))
                for io_id in range(num_testcases)
            ],
            [
                (
                    IOPair(self.dirs.get_input_multitest(io_id + 1), self.dirs.get_output_multitest(io_id + 1))
                    if TestCaseType(problem_data['testcase_types'][io_id]) == TestCaseType.SCRAPED
                    else None
                )
                for io_id in range(num_testcases)
            ],
            None, None, None,
            list(map(TestCaseType, problem_data['testcase_types']))
        )

    def update_problem_data(self) -> None:
        '''
        Update the problem data file.
        '''
        problem_data: ProblemOffline = {
            'name': self.problem_name,
            'time_limit': self.time_limit,
            'testcase_types': self.testcase_set.get_testcase_types(),
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
        while True:
            # get the command suite
            command_suite = CommandSuiteProblem(
                self.message,
                self.config,
                problem_ids,
                self.testcase_set.get_num_scraped(),
                len(self.testcase_set)
            )

            # print the header and get the args
            args = self.message.get_command_problem(
                self.config.username, self.contest_id, self.problem_id,
                self.time_limit, (len(self.testcase_set), self.testcase_set.get_num_multitests()),
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
                file_one_char_name: Literal['m', 'c', 'b', 'g'] = json.loads(parsed_args['file'])
                long_name = {'m': 'main', 'c': 'checker', 'b': 'bruteforce', 'g': 'generator'}[file_one_char_name]
                file_cpp, file_out = self.get_cpp_file_pair(file_one_char_name)

                # compile and run in custom invocation
                self.runner.custom_invocation(file_cpp, file_out, file_one_char_name, long_name)
                continue

            elif command == CommandsProblem.RUN:
                # get the time limit
                run_time_limit = self.time_limit
                if json.loads(parsed_args['time-limit']) is not None:
                    run_time_limit = float(json.loads(parsed_args['time-limit']))

                # get the testcase mode
                run_testcase_mode = self.testcase_mode
                if json.loads(parsed_args['multitest-mode']) is not None:
                    run_testcase_mode = (
                        TestCaseMode.ONE if json.loads(parsed_args['multitest-mode']) == 'o'
                        else TestCaseMode.MULTIPLE
                    )
                    # if user chooses multitests, check if they can be set
                    if run_testcase_mode == TestCaseMode.MULTIPLE and not self.testcase_set.set_multitest_mode():
                        run_testcase_mode = TestCaseMode.ONE

                # get the checker
                run_checker = self.checker
                if json.loads(parsed_args['checker']) is not None:
                    checker_one_char_name: Literal['t', 'y', 'c'] = json.loads(parsed_args['checker'])
                    run_checker = checkers.get_checker(
                        checker_one_char_name,
                        self.dirs.get_custom_checker(),
                        self.dirs.get_custom_checker_compiled()
                    )

                # run
                self.runner.run(
                    self.testcase_set,
                    self.dirs.get_main(), self.dirs.get_main_compiled(),
                    run_time_limit, run_checker, run_testcase_mode
                )

                # override the modes and update problem data if not-override isn't set
                if json.loads(parsed_args['no-override'])[0] == 'False':
                    self.time_limit = run_time_limit
                    self.testcase_mode = run_testcase_mode
                    self.checker = run_checker
                    self.update_problem_data()
                continue

            elif command == CommandsProblem.SET:
                # get the time limit
                if json.loads(parsed_args['time-limit']) is not None:
                    self.time_limit = float(json.loads(parsed_args['time-limit']))

                # get the testcase mode
                if json.loads(parsed_args['multitest-mode']) is not None:
                    set_testcase_mode = (
                        TestCaseMode.ONE if json.loads(parsed_args['multitest-mode']) == 'o'
                        else TestCaseMode.MULTIPLE
                    )
                    # if user chooses multitests, check if they can be set
                    if set_testcase_mode == TestCaseMode.MULTIPLE and not self.testcase_set.set_multitest_mode():
                        set_testcase_mode = TestCaseMode.ONE
                    self.testcase_mode = set_testcase_mode

                # get the checker
                if json.loads(parsed_args['checker']) is not None:
                    checker_one_char_name = json.loads(parsed_args['checker'])  # Literal['t', 'y', 'c']
                    self.checker = checkers.get_checker(
                        checker_one_char_name,
                        self.dirs.get_custom_checker(),
                        self.dirs.get_custom_checker_compiled()
                    )

                # update problem data
                self.update_problem_data()

            elif command == CommandsProblem.INPUT_OUTPUT:
                num_testcases = len(self.testcase_set)
                # remove
                if json.loads(parsed_args['remove']) is not None:
                    remove_cnt = int(json.loads(parsed_args['remove']))
                    self.testcase_set.delete_remove_testcases(remove_cnt)
                # keep
                elif json.loads(parsed_args['keep']) is not None:
                    keep_cnt = int(json.loads(parsed_args['keep']))
                    self.testcase_set.delete_keep_testcases(keep_cnt)
                # multitests
                elif json.loads(parsed_args['multitests']) is not None:
                    # edit multitests
                    multitest_args = json.loads(parsed_args['multitests'])
                    if len(multitest_args) == 0:  # edit multitests of all scraped testcases
                        self.testcase_set.edit_multitests(None)
                    else:
                        testcase_id = int(multitest_args[0])
                        self.testcase_set.edit_multitests(testcase_id)
                    # check the testcase mode
                    if self.testcase_mode == TestCaseMode.MULTIPLE and not self.testcase_set.check_multitest_mode():
                        self.testcase_mode = TestCaseMode.ONE
                        self.message.multitest_mode_can_no_longer_be_used()
                # add
                elif json.loads(parsed_args['add'])[0] == 'True':
                    testcase_id = len(self.testcase_set) + 1
                    self.testcase_set.add_user_testcase(
                        IOPair(self.dirs.get_input(testcase_id), self.dirs.get_output(testcase_id))
                    )
                # edit
                elif json.loads(parsed_args['edit']) is not None:
                    testcase_id = int(json.loads(parsed_args['edit']))
                    self.testcase_set.edit_testcase(testcase_id)
                # view
                elif json.loads(parsed_args['view']) is not None:
                    view_args = json.loads(parsed_args['view'])
                    view_testcase_id: Optional[int] = None if len(view_args) == 0 else int(view_args[0])
                    self.testcase_set.view_testcases(self.testcase_mode, view_testcase_id)
                # no flags
                else:
                    self.message.input_output_no_flags_given()

                # update problem data
                self.update_problem_data()
                continue

            elif command == CommandsProblem.RANDOM:
                # get the number of random testcases
                random_num_testcases = int(json.loads(parsed_args['num']))

                # get the time limit
                random_time_limit = self.time_limit
                if json.loads(parsed_args['time-limit']) is not None:
                    random_time_limit = float(json.loads(parsed_args['time-limit']))

                # get the checker
                random_checker = self.checker
                if json.loads(parsed_args['checker']) is not None:
                    checker_one_char_name = json.loads(parsed_args['checker'])  # Literal['t', 'y', 'c']
                    random_checker = checkers.get_checker(
                        checker_one_char_name,
                        self.dirs.get_custom_checker(),
                        self.dirs.get_custom_checker_compiled()
                    )

                # get the total timeout
                random_total_timeout: Optional[float] = None
                if json.loads(parsed_args['total-timeout']) is not None:
                    random_total_timeout = float(json.loads(parsed_args['total-timeout']))

                # random
                self.message.hi()
                # TODO: implement random
                # TODO: update problem data if a testcase is added

            elif command == CommandsProblem.PASTE:
                Execution.execute(['pbcopy'], self.dirs.get_main().read_file())
                self.message.paste_problem(self.problem_id)

            elif command == CommandsProblem.MOVE:
                return command, parsed_args  # process by the contest

            elif command == CommandsProblem.ALIAS:
                alias_name_parsed_args: list[str] = json.loads(parsed_args['command'])
                alias_str_parsed_args: list[str] = json.loads(parsed_args['args'])
                command_suite.process_alias_command(
                    alias_name_parsed_args[0] if len(alias_name_parsed_args) == 1 else None,
                    alias_str_parsed_args[0] if len(alias_str_parsed_args) == 1 else None,
                    json.loads(parsed_args['unalias'])[0] == 'True'
                )

            elif command == CommandsProblem.HELP:
                help_args = json.loads(parsed_args['command'])
                command_name: Optional[str] = None if len(help_args) == 0 else help_args[0]
                command_suite.print_help_strings(command_name)

            elif command == CommandsProblem.QUIT:
                return command, parsed_args  # process by the contest

            else:
                assert False  # needs more commands

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
        Execution.execute(self.config.code_editor_command + [str(file_edit)], None)
