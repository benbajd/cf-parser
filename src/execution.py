'''Implements execution of commands in the shell.'''

import subprocess
from dataclasses import dataclass
from typing import Optional
from enum import IntEnum
from paths import File


@dataclass
class ExecuteResult:
    '''The result of execute.'''
    stdout: str  # the standard output
    stderr: str  # the standard error
    return_code: int  # the return code


@dataclass
class CompileResult:
    '''The result of compile.'''
    success: bool  # compiled successfully


class RunResultType(IntEnum):
    '''The result type of the run.'''
    SUCCESS = 0  # ran successfully
    RUNTIME_ERROR = 1  # runtime error
    TIME_LIMIT_EXCEEDED = 2  # time limit exceeded


@dataclass
class RunResult:
    '''The result of run.'''
    result_type: RunResultType  # the result type of the run
    output: str  # the output


class Execution:
    '''Implements execution of commands in the shell.'''

    @staticmethod
    def execute(args: list[str], input_str: Optional[str]) -> ExecuteResult:
        '''
        Execute a command with optional input passed to it.
        :param args: the command
        :param input_str: the input string passed as stdin or None if no input should be passed
        :return: the result of execute
        '''
        encoded_input_str: Optional[bytes] = input_str.encode('utf-8') if input_str is not None else None
        completed = subprocess.run(args, input=encoded_input_str, capture_output=True, check=False)
        return ExecuteResult(
            completed.stdout.decode(encoding='utf-8'),
            completed.stderr.decode(encoding='utf-8'),
            completed.returncode
        )

    @staticmethod
    def compile(file: File, file_out: File) -> CompileResult:
        '''
        Compile a .cpp program.
        :param file: the .cpp file to compile
        :param file_out: the output .out file
        :return: the result of compile
        '''
        execute_result = Execution.execute(['g++-13', '-std=c++20', str(file), '-o', str(file_out)], None)
        return CompileResult(execute_result.return_code == 0)

    @staticmethod
    def run(file: File, io_input: str, time_limit: float) -> RunResult:
        '''
        Run a .cpp program with input and a time limit.
        :param file: the .out file to run
        :param io_input: the input
        :param time_limit: the time limit in seconds
        :return: the result of run
        '''
        execute_result = Execution.execute(['timeout', str(time_limit), str(file)], io_input)
        result_type = (  # timeout returns 124 when time limit exceeded or the return code of the command otherwise
            RunResultType.SUCCESS if execute_result.return_code == 0 else (
                RunResultType.RUNTIME_ERROR if execute_result.return_code not in [0, 124]
                else RunResultType.TIME_LIMIT_EXCEEDED
            )
        )
        return RunResult(result_type, execute_result.stdout)
