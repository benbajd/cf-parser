'''Implements the contest class.'''

import json
from typing import Type
from problems import Problem
from scraper import Scraper
from paths import Folder
from directories import DirsContest


class Contest:
    '''A mutable contest class.'''
    contest_id: str  # contest's id
    folder: Folder  # contest's folder
    dirs: DirsContest  # contest's dirs handler
    scraper: Type[Scraper]  # the scraper to be used when initializing a new contest
    problems: dict[str, Problem]  # the problems in the contest, a mapping of problem_ids to problems

    def __init__(self, contest_id: str, folder: Folder, scraper: Type[Scraper]) -> None:
        '''
        Init the contest using the online data if the folder doesn't exist or the offline data otherwise.
        :param contest_id: contest's id
        :param folder: contest's folder
        :param scraper: the scraper to use when initializing a new contest
        '''
        self.contest_id = contest_id
        self.folder = folder
        self.dirs = DirsContest(folder)
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
        for scraped_data in self.scraper.scrape_problems(self.contest_id):
            problem_id = scraped_data['id']
            self.problems[problem_id] = Problem(
                problem_id,
                self.contest_id,
                self.dirs.get_problem(problem_id),
                scraped_data
            )
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
                None
            )
