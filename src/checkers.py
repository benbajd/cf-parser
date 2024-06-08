'''Implements the checkers for the runners to use.'''

from typing import Protocol, Optional, Literal
from enum import IntEnum
from dataclasses import dataclass
from paths import File
import execution
from execution import Execution


class CheckerResultType(IntEnum):
    '''The result type of the checker.'''
    ACCEPTED = 0  # the output was correct
    WRONG_ANSWER = 1  # the output was incorrect
    CHECKER_RUNTIME_ERROR = 2  # runtime error of the checker
    CHECKER_TIME_LIMIT_EXCEEDED = 3  # checker exceeded the time limit


@dataclass
class CheckerResult:
    '''The result of the checker.'''
    result_type: CheckerResultType  # the result type of the checker
    wrong_answer_reason: Optional[str]  # the reason why the checker returned WRONG_ANSWER if needed


class Checker(Protocol):
    '''An immutable checker class.'''

    one_char_name: Literal['t'] | Literal['y'] | Literal['c']  # one char name
    checker_file: Optional[File]  # the checker .cpp file when custom or None otherwise
    checker_file_out: Optional[File]  # the checker .out file when custom or None otherwise

    def check(self, io_input: str, expected_output: str, user_output: str, time_limit: float) -> CheckerResult:
        '''
        Check if the user output is correct given the input and the expected output.
        :param io_input: the testcase input
        :param expected_output: the expected output
        :param user_output: the user output
        :param time_limit: the time limit in seconds, should be a positive number
        :return: the result of the check
        '''


class CheckerTokens(Checker):
    '''Implements the token checker.'''

    one_char_name: Literal['t']
    checker_file: None  # None since the checker isn't custom
    checker_file_out: None  # None since the checker isn't custom

    def __init__(self) -> None:
        '''
        Init CheckerTokens.
        '''
        self.one_char_name = 't'
        self.checker_file = None
        self.checker_file_out = None

    def check(self, io_input: str, expected_output: str, user_output: str,
              time_limit: Optional[float] = None) -> CheckerResult:
        '''
        Check if the user output is correct by comparing only the tokens of the two outputs and ignoring all whitespace.
        Ignores the time limit since the checker is simple enough.
        :param io_input: the testcase input
        :param expected_output: the expected output
        :param user_output: the user output
        :param time_limit: the time limit in seconds, should be a positive number
        :return: the result of the check
        '''
        expected_tokens = expected_output.split()
        user_tokens = user_output.split()
        if expected_tokens == user_tokens:
            result_type = CheckerResultType.ACCEPTED
            wrong_answer_reason = None
        elif len(expected_tokens) != len(user_tokens):
            result_type = CheckerResultType.WRONG_ANSWER
            wrong_answer_reason = f'Expected {len(expected_tokens)} tokens, got {len(user_tokens)}'
        else:  # expected_tokens != user_tokens
            result_type = CheckerResultType.WRONG_ANSWER
            wrong_token_index = [one != two for one, two in zip(expected_tokens, user_tokens)].index(True)
            wrong_answer_reason = (
                f'Expected "{expected_tokens[wrong_token_index]}", got "{user_tokens[wrong_token_index]}" '
                f'at token {wrong_token_index + 1}'
            )
        return CheckerResult(result_type, wrong_answer_reason)


class CheckerYesNo(Checker):
    '''Implements the yes/no checker.'''

    one_char_name: Literal['y']
    checker_file: None  # None since the checker isn't custom
    checker_file_out: None  # None since the checker isn't custom

    def __init__(self) -> None:
        '''
        Init CheckerYesNo.
        '''
        self.one_char_name = 'y'
        self.checker_file = None
        self.checker_file_out = None

    def check(self, io_input: str, expected_output: str, user_output: str,
              time_limit: Optional[float] = None) -> CheckerResult:
        '''
        Check if the user output is correct by comparing yes/no tokens and ignoring case.
        To be used when the expected output only contains yes/no tokens.
        Ignores the time limit since the checker is simple enough.
        :param io_input: the testcase input
        :param expected_output: the expected output, should only contain yes/no tokens
        :param user_output: the user output
        :param time_limit: the time limit in seconds, should be a positive number
        :return: the result of the check
        '''
        # check that all tokens in user_output are yes/no
        user_tokens = user_output.lower().split()
        for token_number, user_token in enumerate(user_tokens):
            if user_token not in ['yes', 'no']:
                return CheckerResult(
                    CheckerResultType.WRONG_ANSWER,
                    f'Expected "yes"/"no", got "{user_token}" at token {token_number + 1}'
                )

        # call the tokens checker
        return CheckerTokens().check(io_input, expected_output.lower(), user_output.lower())


class CheckerCustom(Checker):
    '''Implements the custom checker.'''

    one_char_name: Literal['c']
    checker_file: File  # the checker .cpp file
    checker_file_out: File  # the checker .out file

    def __init__(self, checker_file: File, checker_file_out: File) -> None:
        '''
        Init CheckerCustom.
        :param checker_file: the checker .cpp file
        :param checker_file_out: the checker .out file
        '''
        self.one_char_name = 'c'
        self.checker_file = checker_file
        self.checker_file_out = checker_file_out

    def check(self, io_input: str, expected_output: str, user_output: str, time_limit: float) -> CheckerResult:
        '''
        Check if the user output is correct by running a .cpp custom checker.
        Expects the checker_file to be compiled to checker_file_out.
        The checker_file should output nothing when it determines that the output is accepted
        or the reason why it determined it is wrong answer otherwise (the output should be non-empty in that case).
        :param io_input: the testcase input
        :param expected_output: the expected output
        :param user_output: the user output
        :param time_limit: the time limit in seconds, should be a positive number
        :return: the result of the check
        '''
        io_delim = '---'  # join io with a delim to ensure the checker reads the right io
        run_result = Execution.run(
            self.checker_file_out,
            f'\n{io_delim}\n'.join([io_input, user_output, expected_output]),
            time_limit
        )

        result_type: Optional[CheckerResultType] = None
        wrong_answer_reason: Optional[str] = None

        if run_result.result_type == execution.RunResultType.SUCCESS:
            if run_result.output == '':
                result_type = CheckerResultType.ACCEPTED
            else:
                result_type = CheckerResultType.WRONG_ANSWER
                wrong_answer_reason = run_result.output
        elif run_result.result_type == execution.RunResultType.RUNTIME_ERROR:
            result_type = CheckerResultType.CHECKER_RUNTIME_ERROR
        elif run_result.result_type == execution.RunResultType.TIME_LIMIT_EXCEEDED:
            result_type = CheckerResultType.CHECKER_TIME_LIMIT_EXCEEDED

        return CheckerResult(result_type, wrong_answer_reason)
