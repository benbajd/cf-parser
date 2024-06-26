'''Scraper protocol with implementations for each platform.'''

import json
from typing import Protocol, TypedDict, Optional
from itertools import batched
import requests
from bs4 import BeautifulSoup
from messages import Messages
import configs
from more_itertools import split_before


class ProblemOnline(TypedDict):
    '''A type representing an online problem.'''
    id: str  # problem's id
    name: str  # problem's name
    time_limit: float  # problem's time limit
    io: list[tuple[str, str]]  # problem's io where each tuple is (input, output) of a testcase
    io_multitest_inputs: Optional[list[list[str]]]  # problem's multitest inputs if split successfully
    io_multitest_outputs: Optional[list[list[str]]]  # problem's multitest outputs if split successfully


class Scraper(Protocol):
    '''Scraper for a given platform.'''

    @staticmethod
    def scrape_contests(message: Messages) -> list[str]:
        '''
        Scrapes all contests.
        :param message: the message object that handles printing
        :returns a list of their ids
        '''

    @staticmethod
    def get_contest_url(contest_id: str) -> str:
        '''
        Gets the url for a given contest id.
        :param contest_id: the contest id
        :return: the url
        '''

    @staticmethod
    def scrape_problems(contest_id: str, message: Messages, html_data: Optional[str] = None) -> list[ProblemOnline]:
        '''
        Scrapes all problems for a given contest id.
        :param contest_id: the contest id
        :param message: the message object that handles printing
        :param html_data: the html data if the contest was parsed offline else None
        :returns a list of problems represented as ProblemDummy
        '''


class ScraperCodeforces(Scraper):
    '''Implements a Scraper for Codeforces.'''

    @staticmethod
    def scrape_contests(message: Messages) -> list[str]:
        '''
        Scrapes all contests on Codeforces.
        :param message: the message object that handles printing
        :returns a list of their ids
        '''
        all_contests = json.loads(read_online('https://codeforces.com/api/contest.list?gym=false', message))['result']
        return [contest['id'] for contest in all_contests]

    @staticmethod
    def get_contest_url(contest_id: str) -> str:
        '''
        Gets the url for a given Codeforces contest id.
        :param contest_id: the contest id
        :return: the url
        '''
        return f'https://codeforces.com/contest/{contest_id}/problems'

    @staticmethod
    def scrape_problems(contest_id: str, message: Messages, html_data: Optional[str] = None) -> list[ProblemOnline]:
        '''
        Scrapes all problems for a given Codeforces contest id.
        :param contest_id: the contest id
        :param message: the message object that handles printing
        :param html_data: the html data if the contest was parsed offline else None
        :returns a list of problems
        '''
        soup = BeautifulSoup(
            read_online(ScraperCodeforces.get_contest_url(contest_id), message) if html_data is None else html_data,
            'html.parser'
        )
        problem_tags = soup.find_all(class_='problemindexholder')
        problems: list[ProblemOnline] = []
        for problem_tag in problem_tags:
            # create a problem and get id, name, and time limit
            problem: ProblemOnline = {
                'id': problem_tag['problemindex'],
                'name': problem_tag.find(class_='header').find(class_='title').string,
                'time_limit': float(str(problem_tag.find(class_='time-limit').contents[1]).split()[0]),
                'io': [],
                'io_multitest_inputs': None,
                'io_multitest_outputs': None
            }

            # get entire testcases and try getting multitests
            io_multitest_inputs_all: list[Optional[list[str]]] = []
            io_multitest_outputs_all: list[Optional[list[str]]] = []
            for io_input_tag, io_output_tag in batched(problem_tag.find_all('pre'), n=2):
                # input
                io_input = io_prettify('\n'.join(io_input_tag.strings))  # entire testcase
                io_multitest_inputs: Optional[list[str]] = None
                if io_input_tag.find('div') is not None:
                    multitests: dict[int, str] = {}
                    for line_tag in io_input_tag.find_all('div'):
                        multitest_num = int(str(line_tag['class'][2]).split('-')[-1])
                        multitests[multitest_num] = multitests.get(multitest_num, '') + line_tag.string + '\n'
                    if len(multitests) > 1:  # multitests
                        io_multitest_inputs = [one_input[:-1] for one_input in multitests.values()]  # remove '\n'
                io_multitest_inputs_all.append(io_multitest_inputs)

                # output
                io_output = io_prettify('\n'.join(io_output_tag.strings))
                io_multitest_outputs: Optional[list[str]] = None
                if io_multitest_inputs is not None:
                    num_multitests = int(io_multitest_inputs[0])  # first line is number of multitests
                    io_multitest_outputs = ScraperCodeforces.attempt_multitest_output(io_output, num_multitests)
                io_multitest_outputs_all.append(io_multitest_outputs)

                # add the entire testcase
                problem['io'].append((io_input, io_output))

            # set multitests
            if None not in io_multitest_inputs_all:  # all testcases have multitest inputs
                problem['io_multitest_inputs'] = [
                    io_multitest_inputs_one for io_multitest_inputs_one in io_multitest_inputs_all
                    if io_multitest_inputs_one is not None  # type checker, always true
                ]
            if None not in io_multitest_outputs_all:  # all testcases have multitest outputs
                problem['io_multitest_outputs'] = [
                    io_multitest_outputs_one for io_multitest_outputs_one in io_multitest_outputs_all
                    if io_multitest_outputs_one is not None  # type checker, always true
                ]

            # add the problem
            problems.append(problem)
        return problems

    @staticmethod
    def attempt_multitest_output(io_output: str, num_multitests: int) -> Optional[list[str]]:
        '''
        Attempts to split output into multitests.
        :param io_output: the output string
        :param num_multitests: the number of multitests obtained from the input string
        :return: the list of multitest outputs if split successfully or None otherwise
        '''
        # attempt one line
        attempt_one_line = ScraperCodeforces.attempt_multitest_output_one_line(io_output, num_multitests)
        if attempt_one_line is not None:
            return attempt_one_line
        # attempt yes/no
        attempt_yes_no = ScraperCodeforces.attempt_multitest_output_yes_no(io_output, num_multitests)
        if attempt_yes_no is not None:
            return attempt_yes_no
        # return None
        return None

    @staticmethod
    def attempt_multitest_output_one_line(io_output: str, num_multitests: int) -> Optional[list[str]]:
        '''
        Attempts to split output into multitests by assuming each multitest is one line long.
        :param io_output: the output string
        :param num_multitests: the number of multitests obtained from the input string
        :return: the list of multitest outputs if split successfully or None otherwise
        '''
        output_lines = io_output.strip('\n').splitlines()
        return output_lines if len(output_lines) == num_multitests else None

    @staticmethod
    def attempt_multitest_output_yes_no(io_output: str, num_multitests: int) -> Optional[list[str]]:
        '''
        Attempts to split output into multitests by assuming each multitest has its own yes/no line.
        :param io_output: the output string
        :param num_multitests: the number of multitests obtained from the input string
        :return: the list of multitest outputs if split successfully or None otherwise
        '''
        output_lines = io_output.strip('\n').splitlines()
        multitests = list(split_before(output_lines, lambda line: line.lower() in ['yes', 'no']))
        if len(output_lines) >= 1 and output_lines[0].lower() in ['yes', 'no'] and len(multitests) == num_multitests:
            return ['\n'.join(multitest) for multitest in multitests]
        else:
            return None


def read_online(url: str, message: Messages) -> str:
    '''
    Read the contents of a website url.
    :param url: the website url
    :param message: the message object that handles printing
    :returns: the contents of the website
    '''
    response = requests.get(url)
    while response.status_code != 200:
        response = requests.get(url)
    html_data = response.text
    configs.offline_html.write_file(html_data)
    return html_data
    # TODO: return after some amount of failed attempts


def io_prettify(io: str) -> str:
    '''
    Make the io pretty by removing redundant newlines.
    :param io: the io
    :returns: the prettified io
    '''
    io = io.strip('\n')
    io += '\n' if (not io or io[-1] != '\n') else ''
    return io
