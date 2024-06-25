'''Implements the contest class.'''

import json
from typing import Type, Literal
from problems import Problem
from scraper import Scraper
from paths import Folder
from directories import DirsContest
from messages import Messages
from commandsuites import CommandsProblem
from execution import Execution
import configs


class Contest:
    '''A mutable contest class.'''
    contest_id: str  # contest's id
    folder: Folder  # contest's folder
    dirs: DirsContest  # contest's dirs handler
    message: Messages  # the message object that handles printing
    scraper: Type[Scraper]  # the scraper to be used when initializing a new contest
    problems: dict[str, Problem]  # the problems in the contest, a mapping of problem_ids to problems

    def __init__(self, contest_id: str, folder: Folder, message: Messages,
                 scraper: Type[Scraper], parse_offline: bool) -> None:
        '''
        Init the contest using the online data if the folder doesn't exist or the offline data otherwise.
        :param contest_id: contest's id
        :param folder: contest's folder
        :param message: the message object that handles printing
        :param scraper: the scraper to use when initializing a new contest
        :param parse_offline: True if the contest should be parsed offline else False
        '''
        self.contest_id = contest_id
        self.folder = folder
        self.dirs = DirsContest(folder)
        self.message = message
        self.scraper = scraper
        self.problems = {}
        if not self.folder.folder_exists():
            self.folder.create_folder()
            self.init_online(parse_offline)
        else:
            self.init_offline()

    def init_online(self, parse_offline: bool) -> None:
        '''
        Init the contest by scraping.
        :param parse_offline: True if the contest should be parsed offline else False
        '''
        # scrape the problems
        if not parse_offline:  # read online
            self.message.contest_parsing_online(self.contest_id)
            scraped_problems = self.scraper.scrape_problems(self.contest_id, self.message)
        else:  # offline mode
            # print parsing offline
            self.message.contest_parsing_offline(self.contest_id)
            # copy to clipboard
            Execution.execute(['pbcopy'], self.scraper.get_contest_url(self.contest_id))
            # empty the html file and open it for editing
            configs.offline_html.write_file('')
            Execution.execute(configs.text_editor_command_wait + [str(configs.offline_html)], None)
            # scrape the problems
            scraped_problems = self.scraper.scrape_problems(
                self.contest_id, self.message, configs.offline_html.read_file()
            )

        # delete the folder and return if the contest doesn't exist
        if len(scraped_problems) == 0:
            self.message.contest_doesnt_exist(self.contest_id)
            self.folder.delete_folder()
            return

        # create the problems
        self.message.creating_contest(self.contest_id)
        for scraped_data in scraped_problems:
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
        self.message.contest_already_parsed(self.contest_id)
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
        Process commands or do nothing if the contest doesn't exist.
        '''
        # return if the contest doesn't exist
        if len(self.problems) == 0:
            return

        # set the current problem to the first problem
        current_problem = list(self.problems.keys())[0]

        # process commands
        while True:
            command, parsed_args = self.problems[current_problem].process_commands(list(self.problems.keys()))
            if command == CommandsProblem.EDIT:
                # get the list of problem ids to edit
                problems_edit: list[str] = [problem_id.upper() for problem_id in json.loads(parsed_args['problem-ids'])]
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
            elif command == CommandsProblem.MOVE:
                # get the problem id and print the move
                problem_id = json.loads(parsed_args['problem-id']).upper()
                self.message.move_problem(problem_id)

                # change the current problem
                current_problem = problem_id
            elif command == CommandsProblem.QUIT:
                # print the message and quit
                self.message.quit_contest(self.contest_id)
                break
            else:
                assert False  # needs more commands
