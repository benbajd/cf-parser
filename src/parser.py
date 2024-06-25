'''Implements the parser to run parser commands.'''

import json
from typing import Optional
from scraper import ScraperCodeforces
from contests import Contest
from directories import DirsPlatform
import configs
from prints import PrintTerminal, PrintFile, PrintFileInputOnly, PrintBatched
from messages import Messages
from commandsuites import CommandsParser, CommandSuiteParser


class Parser:
    '''An immutable parser.'''
    dirs: DirsPlatform  # parser's dirs handler
    message: Messages  # the message object that handles printing

    def __init__(self) -> None:
        '''
        Init Parser.
        '''
        self.dirs = DirsPlatform(configs.codeforces_folder)
        self.message = Messages(
            PrintBatched(
                PrintTerminal(),
                [
                    PrintFile(configs.parser_history),
                    PrintFileInputOnly(configs.input_history),
                ]
            )
        )

    def process_commands(self) -> None:
        '''
        Process commands.
        '''
        while True:
            # get the command suite, print the header, and get the args
            command_suite = CommandSuiteParser(self.message)
            args = self.message.get_command_parser()

            # parse the args
            parsed_command_args = command_suite.parse(args)

            # continue on errors
            if parsed_command_args is None:
                continue

            # execute the command
            command, parsed_args = parsed_command_args
