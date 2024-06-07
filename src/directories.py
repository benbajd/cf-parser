'''Handles the directory structure.'''

from paths import Folder, File


class DirsPlatform:
    '''An immutable object that handles the directory structure of a platform.'''
    folder_platform: Folder

    def __init__(self, folder_platform: Folder) -> None:
        '''
        Init the DirsPlatform.
        :param folder_platform: the folder of the platform
        '''
        self.folder_platform = folder_platform

    def get_contest(self, contest_id: str) -> Folder:
        '''
        Get the folder of a contest.
        :param contest_id: the contest
        :returns: the folder of the contest
        '''
        return self.folder_platform.down(contest_id)


class DirsContest:
    '''An immutable object that handles the directory structure of a contest.'''
    folder_contest: Folder

    def __init__(self, folder_contest: Folder) -> None:
        '''
        Init the DirsContest.
        :param folder_contest: the folder of the contest
        '''
        self.folder_contest = folder_contest

    def get_problem(self, problem_id: str) -> Folder:
        '''
        Get the folder of a problem.
        :param problem_id: the problem
        :returns: the folder of the problem
        '''
        return self.folder_contest.down(problem_id)

    def get_contest_data(self) -> File:
        '''
        Get the contest data file.
        :returns: the contest data file
        '''
        return self.folder_contest.down_file('contest_data.json')


class DirsProblem:
    '''An immutable object that handles the directory structure of a problem.'''
    folder_problem: Folder
    contest_id: str
    problem_id: str

    def __init__(self, folder_problem: Folder, contest_id: str, problem_id: str) -> None:
        '''
        Init the DirsProblem.
        :param folder_problem: the folder of the problem
        :param contest_id: the contest
        :param problem_id: the problem
        '''
        self.folder_problem = folder_problem
        self.contest_id = contest_id
        self.problem_id = problem_id

    def get_main(self) -> File:
        '''
        Get the main file.
        :returns: the main file
        '''
        return self.folder_problem.down_file(f'{self.contest_id}{self.problem_id}.cpp')

    def get_main_compiled(self) -> File:
        '''
        Get the main file compiled.
        :returns: the main file compiled
        '''
        return self.folder_problem.down_file(f'{self.contest_id}{self.problem_id}.out')

    def get_input(self, io_id: int) -> File:
        '''
        Get the input file.
        :param io_id: the id of the io
        :returns: the input file
        '''
        return self.folder_problem.down_file(f'{self.problem_id}_{io_id}.in')

    def get_output(self, io_id: int) -> File:
        '''
        Get the output file.
        :param io_id: the id of the io
        :returns: the output file
        '''
        return self.folder_problem.down_file(f'{self.problem_id}_{io_id}.out')

    def get_input_multitest(self, io_id: int, io_sub_id: int) -> File:
        '''
        Get the input file of a multitest.
        :param io_id: the id of the io
        :param io_sub_id: the sub id of the io
        :return: the input file of a multitest
        '''
        return self.folder_problem.down_file(f'{self.problem_id}_{io_id}-{io_sub_id}.in')

    def get_output_multitest(self, io_id: int, io_sub_id: int) -> File:
        '''
        Get the output file of a multitest.
        :param io_id: the id of the io
        :param io_sub_id: the sub id of the io
        :return: the output file of a multitest
        '''
        return self.folder_problem.down_file(f'{self.problem_id}_{io_id}-{io_sub_id}.out')

    def get_custom_checker(self) -> File:
        '''
        Get the custom checker file.
        :return: the custom checker file
        '''
        return self.folder_problem.down_file(f'{self.contest_id}{self.problem_id}_checker.cpp')

    def get_custom_checker_compiled(self) -> File:
        '''
        Get the custom checker file compiled.
        :return: the custom checker file compiled
        '''
        return self.folder_problem.down_file(f'{self.contest_id}{self.problem_id}_checker.out')

    def get_problem_data(self) -> File:
        '''
        Get the problem data file.
        :returns: the problem data file
        '''
        return self.folder_problem.down_file('problem_data.json')
