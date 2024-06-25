'''Scraper protocol with implementations for each platform.'''

import json
from typing import Protocol, TypedDict, Optional
from itertools import batched
import requests
from bs4 import BeautifulSoup
from messages import Messages
import configs


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
        problem_tags = soup.find_all(attrs={'class': 'problemindexholder'})
        problems: list[ProblemOnline] = []
        for problem_tag in problem_tags:
            problem: ProblemOnline = {
                'id': problem_tag['problemindex'],
                'name': problem_tag.find(class_='header').find(class_='title').string,
                'time_limit': 1,  # TODO: scrape time limit
                'io': [],
                'io_multitest_inputs': None,
                'io_multitest_outputs': None
            }
            # TODO: handle multiple testcases
            for io_input_raw, io_output_raw in batched(problem_tag.find_all('pre'), n=2):
                io_input = io_prettify('\n'.join(io_input_raw.strings))
                io_output = io_prettify('\n'.join(io_output_raw.strings))
                problem['io'].append((io_input, io_output))
            problems.append(problem)
        return problems


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
