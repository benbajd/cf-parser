'''Implements the parser to run parser commands.'''

import json
from typing import Optional
from scraper import ScraperCodeforces
from contests import Contest
from directories import DirsPlatform
from configs import Configs
from prints import PrintTerminal, PrintFile, PrintFileInputOnly, PrintBatched
from messages import Messages
from commandsuites import CommandsParser, CommandSuiteParser
from paths import Folder


class Parser:
    '''An immutable parser.'''
    dirs: DirsPlatform  # parser's dirs handler
    message: Messages  # the message object that handles printing
    config: Configs  # the configs object storing configs

    def __init__(self) -> None:
        '''
        Init Parser.
        '''
        # create .config folder
        configs_parent_folder = Folder(['~', '.config'])
        if not configs_parent_folder.folder_exists():
            configs_parent_folder.create_folder()

        # get a temporary config object with a temporary output to a terminal only
        configs_folder = configs_parent_folder.down('cf-parser')
        temp_config = Configs(configs_folder, Messages(PrintTerminal()), True)  # TODO: store the temporary file outputs

        # create the dirs and message
        self.dirs = DirsPlatform(temp_config.codeforces_folder)
        self.message = Messages(
            PrintBatched(
                PrintTerminal(),
                [
                    PrintFile(temp_config.parser_history),
                    PrintFileInputOnly(temp_config.input_history),
                ]
            )
        )

        # create the config object with output to the terminal and files
        self.config = Configs(configs_folder, self.message, False)

    def process_commands(self) -> None:
        '''
        Process commands.
        '''
        while True:
            # get the command suite, print the header, and get the args
            command_suite = CommandSuiteParser(self.message, self.config)
            args = self.message.get_command_parser(self.config.username)

            # parse the args
            parsed_command_args = command_suite.parse(args)

            # continue on errors
            if parsed_command_args is None:
                continue

            # execute the command
            command, parsed_args = parsed_command_args

            if command == CommandsParser.CODEFORCES:
                contest_id: str = json.loads(parsed_args['contest-id'])
                parse_offline = bool(json.loads(parsed_args['offline'])[0] == 'True')

                contest = Contest(
                    contest_id, self.dirs.get_contest(contest_id),
                    self.message, self.config,
                    ScraperCodeforces, parse_offline
                )
                contest.process_commands()

            elif command == CommandsParser.CONFIG:
                self.config.edit_configs()
                self.dirs = DirsPlatform(self.config.codeforces_folder)  # update dirs

            elif command == CommandsParser.ALIAS:
                alias_name_parsed_args: list[str] = json.loads(parsed_args['command'])
                alias_str_parsed_args: list[str] = json.loads(parsed_args['args'])
                command_suite.process_alias_command(
                    alias_name_parsed_args[0] if len(alias_name_parsed_args) == 1 else None,
                    alias_str_parsed_args[0] if len(alias_str_parsed_args) == 1 else None,
                    json.loads(parsed_args['unalias'])[0] == 'True'
                )

            elif command == CommandsParser.HELP:
                help_args = json.loads(parsed_args['command'])
                command_name: Optional[str] = None if len(help_args) == 0 else help_args[0]
                command_suite.print_help_strings(command_name)

            elif command == CommandsParser.QUIT:
                self.message.quit_parser()
                break

            else:
                assert False  # needs more commands
