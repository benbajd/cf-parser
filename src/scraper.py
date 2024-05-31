'''Scraper protocol with implementations for each platform.'''

import json
from typing import Protocol, TypedDict, Tuple
from itertools import batched
import requests
from bs4 import BeautifulSoup


class ProblemOnline(TypedDict):
    '''A type representing an online problem.'''
    id: str  # problem's id
    name: str  # problem's name
    io: list[Tuple[str, str]]  # problem's io where each tuple is (input, output) of a testcase


class Scraper(Protocol):
    '''Scraper for a given platform.'''

    @staticmethod
    def scrape_contests() -> list[str]:
        '''
        Scrapes all contests.
        :returns a list of their ids
        '''

    @staticmethod
    def scrape_problems(contest_id: str) -> list[ProblemOnline]:
        '''
        Scrapes all problems for a given contest id.
        :param contest_id: the contest id
        :returns a list of problems represented as ProblemDummy
        '''


class ScraperCodeforces:
    '''Implements a Scraper for Codeforces.'''

    @staticmethod
    def scrape_contests() -> list[str]:
        '''
        Scrapes all contests on Codeforces.
        :returns a list of their ids
        '''
        all_contests = json.loads(read_online('https://codeforces.com/api/contest.list?gym=false'))['result']
        return [contest['id'] for contest in all_contests]

    @staticmethod
    def scrape_problems(contest_id: str) -> list[ProblemOnline]:
        '''
        Scrapes all problems for a given Codeforces contest id.
        :param contest_id: the contest id
        :returns a list of problems represented as ProblemDummy
        '''
        soup = BeautifulSoup(read_online(f'https://codeforces.com/contest/{contest_id}/problems'), 'html.parser')
        problem_tags = soup.find_all(attrs={'class': 'problemindexholder'})
        problems: list[ProblemOnline] = []
        for problem_tag in problem_tags:
            problem: ProblemOnline = {
                'id': problem_tag['problemindex'],
                'name': problem_tag.find(class_='header').find(class_='title').string,
                'io': []
            }
            for io_input_raw, io_output_raw in batched(problem_tag.find_all('pre'), n=2):
                io_input = io_prettify('\n'.join(io_input_raw.strings))
                io_output = io_prettify('\n'.join(io_output_raw.strings))
                problem['io'].append((io_input, io_output))
            problems.append(problem)
        return problems


def read_online(url: str) -> str:
    '''
    Read the contents of a website url.
    :param url: the website url
    :returns: the contents of the website
    '''
    response = requests.get(url)
    while response.status_code != 200:
        response = requests.get(url)
    return response.text


def io_prettify(io: str) -> str:
    '''
    Make the io pretty by removing redundant newlines.
    :param io: the io
    :returns: the prettified io
    '''
    io = io.strip('\n')
    io += '\n' if (not io or io[-1] != '\n') else ''
    return io
