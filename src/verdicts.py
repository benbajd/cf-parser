'''Implements enums for compile and run verdicts.'''

from enum import IntEnum


class CompileVerdict(IntEnum):
    '''The compile verdict.'''
    COMPILING = -1  # still compiling
    SUCCESS = 0  # compiled successfully
    COMPILATION_ERROR = 1  # compilation error


class RunVerdict(IntEnum):
    '''The run verdict.'''
    RUNNING = -1  # still running
    ACCEPTED = 0  # accepted
    WRONG_ANSWER = 1  # wrong answer
    RUNTIME_ERROR = 2  # runtime error
    TIME_LIMIT_EXCEEDED = 3  # time limit exceeded
    CHECKER_RUNTIME_ERROR = 4  # checker runtime error
    CHECKER_TIME_LIMIT_EXCEEDED = 5  # checker time limit exceeded
