'''Implements the problem class.'''

from typing import TypedDict, Optional
from scraper import ProblemOnline
from directories import DirsProblem
from paths import Folder, File
import basefiles
import json


class ProblemOffline(TypedDict):
    '''A type representing an offline problem.'''
    name: str  # problem's name
    time_limit: int  # the time limit
    io_count: int  # number of testcases


class Problem:
    '''A mutable problem class.'''
    problem_id: str  # problem's id
    problem_name: str  # problem's name
    contest_id: str  # contest of the problem
    folder: Folder  # problem's folder
    dirs: DirsProblem  # problem's dir handler
    time_limit: int  # problem's time limit
    io_count: int  # number of testcases

    def __init__(self, problem_id: str, contest_id: str, folder: Folder, scraped_data: Optional[ProblemOnline]) -> None:
        '''
        Init the problem using the online data if scraped_data is provided or the offline data otherwise.
        :param problem_id: the problem
        :param contest_id: the contest
        :param folder: the problem's folder
        :param scraped_data: the online data if scraped initially
        '''
        self.problem_id = problem_id
        self.contest_id = contest_id
        self.folder = folder
        self.dirs = DirsProblem(folder, contest_id, problem_id)
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
        for io_id, (io_input, io_output) in enumerate(scraped_data['io']):
            self.dirs.get_input(io_id + 1).write_file(io_input)
            self.dirs.get_output(io_id + 1).write_file(io_output)

        # set the problem data
        self.problem_name = scraped_data['name']
        self.time_limit = 1  # TODO: scrape time limits
        self.io_count = len(scraped_data['io'])

    def init_offline(self) -> None:
        '''
        Init the problem using the offline data.
        '''
        problem_data: ProblemOffline = json.loads(self.dirs.get_problem_data().read_file())
        self.problem_name = problem_data['name']
        self.time_limit = problem_data['time_limit']
        self.io_count = problem_data['io_count']

    def update_problem_data(self) -> None:
        '''
        Update the problem data file.
        '''
        problem_data: ProblemOffline = {
            'name': self.problem_name,
            'time_limit': self.time_limit,
            'io_count': self.io_count
        }
        self.dirs.get_problem_data().write_file(json.dumps(problem_data))
