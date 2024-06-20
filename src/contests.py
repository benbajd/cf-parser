'''Implements the contest class.'''

import json
from typing import Type, Literal
from problems import Problem
from scraper import Scraper
from paths import Folder
from directories import DirsContest
from messages import Messages
from commandsuites import CommandsProblem
import json


class Contest:
    '''A mutable contest class.'''
    contest_id: str  # contest's id
    folder: Folder  # contest's folder
    dirs: DirsContest  # contest's dirs handler
    message: Messages  # the message object that handles printing
    scraper: Type[Scraper]  # the scraper to be used when initializing a new contest
    problems: dict[str, Problem]  # the problems in the contest, a mapping of problem_ids to problems

    def __init__(self, contest_id: str, folder: Folder, message: Messages, scraper: Type[Scraper]) -> None:
        '''
        Init the contest using the online data if the folder doesn't exist or the offline data otherwise.
        :param contest_id: contest's id
        :param folder: contest's folder
        :param message: the message object that handles printing
        :param scraper: the scraper to use when initializing a new contest
        '''
        self.contest_id = contest_id
        self.folder = folder
        self.dirs = DirsContest(folder)
        self.message = message
        self.scraper = scraper
        self.problems = {}
        if not self.folder.folder_exists():
            self.folder.create_folder()
            self.init_online()
        else:
            self.init_offline()

    def init_online(self) -> None:
        '''
        Init the contest by scraping.
        '''
        # TODO: handle no problems
        # scrape and create the problems
        for scraped_data in self.scraper.scrape_problems(self.contest_id, self.message):
            problem_id = scraped_data['id']
            self.problems[problem_id] = Problem(
                problem_id,
                self.contest_id,
                self.dirs.get_problem(problem_id),
                self.message,
                scraped_data
            )

        # TODO: print which problems don't have multitests

        # save the contest data
        problem_ids: list[str] = list(self.problems.keys())
        self.dirs.get_contest_data().write_file(json.dumps(problem_ids))

    def init_offline(self) -> None:
        '''
        Init the contest offline.
        '''
        # read the contest data
        problem_ids: list[str] = json.loads(self.dirs.get_contest_data().read_file())
        # create the problems
        for problem_id in problem_ids:
            self.problems[problem_id] = Problem(
                problem_id,
                self.contest_id,
                self.dirs.get_problem(problem_id),
                self.message,
                None
            )

    def process_commands(self) -> None:
        '''
        Process commands.
        '''
        current_problem = list(self.problems.keys())[0]

        while True:
            command, parsed_args = self.problems[current_problem].process_commands(list(self.problems.keys()))
            if command == CommandsProblem.EDIT:
                # get the list of problem ids to edit
                problems_edit: list[str] = [problem_id.upper() for problem_id in json.loads(parsed_args['problem_ids'])]
                if current_problem not in problems_edit:
                    problems_edit.append(current_problem)
                problems_edit.sort()
                flag_all = bool(json.loads(parsed_args['all'])[0] == 'True')
                if flag_all:
                    problems_edit = list(self.problems.keys())

                # get the file to edit
                file_cpp: Literal['m', 'c', 'b', 'g'] = json.loads(parsed_args['file'])

                # print the edit str
                self.message.edit_problem_files(problems_edit, file_cpp)

                # edit each of them
                for problem_id in problems_edit:
                    self.problems[problem_id].edit(file_cpp)

                # focus on the current problem
                self.problems[current_problem].edit(file_cpp)
