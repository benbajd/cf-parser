'''Implements the runner class.'''

import time
from paths import File
from verdicts import CompileVerdict, RunVerdict
from messages import Messages
from testcases import TestCase, TestCaseMode, TestCaseRun
from checkers import Checker, CheckerResultType
from threading import Thread
import queue
import execution
from execution import Execution


class Runner:
    '''An immutable runner.'''
    message: Messages  # the message object that handles printing

    def __init__(self, message: Messages) -> None:
        '''
        Init Runner.
        :param message: the message object that handles printing
        '''
        self.message = message

    def run(self, run_testcases: list[TestCase], main: File, main_out: File,
            time_limit: float, checker: Checker, testcase_mode: TestCaseMode) -> None:
        '''
        Run the solution on the testcases.
        :param run_testcases: the testcases to run
        :param main: the main .cpp file
        :param main_out: the main .out file
        :param time_limit: time limit in seconds, should be a positive number
        :param checker: the checker to use
        :param testcase_mode: the testcases mode
        '''
        # COMPILATION

        # initial message
        start_time = time.perf_counter()
        compile_count = 1 + int(checker.checker_file is not None)
        run_count = sum(len(testcase.get_testcases(testcase_mode)) for testcase in run_testcases)
        self.message.runner_start(compile_count, run_count)

        # prepare files to compile
        to_compile: list[tuple[File, File]] = [(main, main_out)]
        if checker.checker_file is not None:
            assert checker.checker_file_out is not None  # checker_file and checker_file_out have the same type
            to_compile.append((checker.checker_file, checker.checker_file_out))

        # prepare verdicts, queue, and the compile thread target
        compile_verdicts: list[CompileVerdict] = [CompileVerdict.COMPILING for _ in range(compile_count)]
        compile_queue: queue.Queue[int] = queue.Queue()

        def compile_thread_target(compile_index: int) -> None:
            '''
            The function to run in compile threads.
            Compile the file compile_index, update compile_verdicts with the verdict,
            and add to the compile_queue once done.
            :param compile_index: the index of the file to compile
            '''
            compile_result = Execution.compile(*to_compile[compile_index])
            compile_verdicts[compile_index] = (  # no lock needed since only one thread writes to this index
                CompileVerdict.SUCCESS if compile_result.success
                else CompileVerdict.COMPILATION_ERROR
            )
            compile_queue.put(compile_index)

        # prepare the threads and start them
        compile_threads = [
            Thread(target=compile_thread_target, args=(compile_index,))
            for compile_index in range(compile_count)
        ]
        for thread in compile_threads:
            thread.start()

        # wait on the threads to finish
        for _ in range(compile_count):
            finished_index = compile_queue.get()
            self.message.runner_compile_update(compile_verdicts, run_count)

        compile_bracket_verdict = (
            CompileVerdict.SUCCESS if CompileVerdict.COMPILATION_ERROR not in compile_verdicts
            else CompileVerdict.COMPILATION_ERROR
        )
        self.message.runner_compile_finish(compile_verdicts, compile_bracket_verdict, run_count)

        # check that all files compiled successfully
        if CompileVerdict.COMPILATION_ERROR in compile_verdicts:
            end_time = time.perf_counter()
            self.message.runner_finish_after_compile(compile_verdicts, end_time - start_time)
            return

        # RUN

        # prepare testcases to run and their ids
        to_run: list[tuple[str, str]] = []  # inputs and expected outputs
        testcase_ids: list[str] = []

        for testcase_number, testcase in enumerate(run_testcases):
            multitests: list[TestCaseRun] = testcase.get_testcases(testcase_mode)
            to_run.extend([(multitest.io_input, multitest.io_output) for multitest in multitests])
            testcase_ids.extend([multitest.id for multitest in multitests])

        # prepare verdicts, queue, and the run thread target
        main_outputs: list[str] = ['' for _ in range(run_count)]
        wrong_answer_reasons: list[str] = ['' for _ in range(run_count)]
        run_verdicts: list[RunVerdict] = [RunVerdict.RUNNING for _ in range(run_count)]
        run_queue: queue.Queue[int] = queue.Queue()

        def run_thread_target(run_index: int) -> None:
            '''
            The function to run in run threads.
            Run testcase run_index, update run_verdicts with the verdict, and add to the run_queue once done.
            :param run_index: the index of the testcase to run
            '''
            # get io and run main
            io_input, io_output = to_run[run_index]
            run_result = Execution.run(main_out, io_input, time_limit)

            # if one of runtime error or time limit exceeded happens, return
            if run_result.result_type == execution.RunResultType.RUNTIME_ERROR:
                # no lock is needed in any run_verdicts updates since only one thread writes to this index
                run_verdicts[run_index] = RunVerdict.RUNTIME_ERROR
                run_queue.put(run_index)
                return
            if run_result.result_type == execution.RunResultType.TIME_LIMIT_EXCEEDED:
                run_verdicts[run_index] = RunVerdict.TIME_LIMIT_EXCEEDED
                run_queue.put(run_index)
                return

            # otherwise we have success, hence run the checker
            assert run_result.result_type == execution.RunResultType.SUCCESS
            main_output = run_result.output
            main_outputs[run_index] = main_output

            checker_result = checker.check(
                io_input,
                io_output,
                main_output,
                3 * time_limit  # give custom checkers extra time for double output
            )

            # if the checker fails, return
            if checker_result.result_type == CheckerResultType.CHECKER_RUNTIME_ERROR:
                run_verdicts[run_index] = RunVerdict.CHECKER_RUNTIME_ERROR
                run_queue.put(run_index)
                return
            if checker_result.result_type == CheckerResultType.CHECKER_TIME_LIMIT_EXCEEDED:
                run_verdicts[run_index] = RunVerdict.CHECKER_TIME_LIMIT_EXCEEDED
                run_queue.put(run_index)
                return

            # if wrong answer, store the reason
            if checker_result.result_type == CheckerResultType.WRONG_ANSWER:
                run_verdicts[run_index] = RunVerdict.WRONG_ANSWER
                assert checker_result.wrong_answer_reason is not None
                wrong_answer_reasons[run_index] = checker_result.wrong_answer_reason
                run_queue.put(run_index)
                return

            # accepted
            assert checker_result.result_type == CheckerResultType.ACCEPTED
            run_verdicts[run_index] = RunVerdict.ACCEPTED
            run_queue.put(run_index)

        # prepare the threads and start them
        run_threads = [
            Thread(target=run_thread_target, args=(run_index,))
            for run_index in range(run_count)
        ]
        for thread in run_threads:
            thread.start()

        # wait on the threads to finish and determine the overall verdict
        overall_verdict = RunVerdict.ACCEPTED  # the first non accepted verdict or accepted otherwise
        for _ in range(run_count):
            finished_index = run_queue.get()
            if run_verdicts[finished_index] != RunVerdict.ACCEPTED and overall_verdict == RunVerdict.ACCEPTED:
                overall_verdict = run_verdicts[finished_index]
            self.message.runner_run_update(compile_verdicts, compile_bracket_verdict, run_verdicts, testcase_ids)

        self.message.runner_finish(
            compile_verdicts, compile_bracket_verdict, run_verdicts, testcase_ids, overall_verdict
        )

        end_time = time.perf_counter()
        self.message.runner_finish_after_run(
            run_verdicts, testcase_ids, to_run, main_outputs, wrong_answer_reasons, end_time - start_time
        )
