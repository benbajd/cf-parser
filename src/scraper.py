import requests
import json
from bs4 import BeautifulSoup


def read_online(url):
    '''returns the contents of url'''
    r = requests.get(url)
    while r.status_code != 200:
        r = requests.get(url)
    return r.text


def io_prettify(io):
    '''returns the fixed scraped io string'''
    io = io[int(io[0] == '\n'):]
    io += '\n' if io[-1] != '\n' else ''
    return repr(io)


def cf_contests_scrape():
    '''returns a list of all contest ids'''
    all_contests = json.loads(read_online('https://codeforces.com/api/contest.list?gym=false'))['result']
    return [contest['id'] for contest in all_contests]


def cf_problems_scrape(contest_id):
    '''
    returns a list of problems of contest_id, each represented as a dict with:
    - id: the contest id
    - name: the problem name
    - io: list of io strings, paired as input and output
    '''
    soup = BeautifulSoup(read_online(f'https://codeforces.com/contest/{contest_id}/problems'), 'html.parser')
    problem_tags = soup.find_all(attrs={'class': 'problemindexholder'})
    problems = []
    for problem_tag in problem_tags:
        problem = {'id': problem_tag['problemindex'],
                   'name': problem_tag.find(class_='header').find(class_='title').string,
                   'io': []}
        for io in problem_tag.find_all('pre'):
            problem['io'].append(io_prettify('\n'.join(io.strings)))
        problems.append(problem)
    return problems
