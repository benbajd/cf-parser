'''Implements storing the config file for basic configs.'''

import json
from paths import Folder, File
from configitems import ConfigItemTerminal, ConfigItemFile
from messages import Messages
import basefiles

# TODO: store locally and check when starting the parser

config_folder = Folder(['~', '.config', 'cf-parser'])

competitive_programming_folder = Folder()
codeforces_folder = Folder()

username = ''

cpp_compiler = ''

code_editor_command = []

text_editor_command_wait = []

offline_html: File = competitive_programming_folder.down_file('offline_html.html')
input_history: File = competitive_programming_folder.down_file('input_history.txt')
parser_history: File = competitive_programming_folder.down_file('parser_history.txt')

history_commandsuite_problem: File = config_folder.down_file('commandsuite_problem_history')
history_commandsuite_parser: File = config_folder.down_file('commandsuite_parser_history')
history_two_options: File = config_folder.down_file('two_options_history')

# TODO: all the folders and files should be created


class Configs:
    '''A mutable object that handles all config items.'''
    # the configs folder
    configs_folder: Folder  # the folder containing all config files
    configs_file: File  # the file containing the configs dict
    # the message object
    message: Messages  # the message object that handles printing
    # config items
    item_username: ConfigItemTerminal[str]  # the username
    item_competitive_programming_folder: ConfigItemTerminal[Folder]  # the competitive programming folder
    item_codeforces_folder: ConfigItemTerminal[Folder]  # the codeforces folder
    item_cpp_compiler: ConfigItemTerminal[str]  # the cpp compiler
    item_code_editor_command: ConfigItemTerminal[list[str]]  # the command that opens the code editor
    item_text_editor_wait_command: ConfigItemTerminal[list[str]]  # the command that open the text editor and waits
    item_cpp_header: ConfigItemFile[str]  # the cpp header
    # config item lists
    items_terminal: list[ConfigItemTerminal[str | Folder | list[str]]]  # list of all config items in the terminal
    items_file: list[ConfigItemFile[str]]  # list of all config items in a file

    def __init__(self, configs_folder: Folder, message: Messages) -> None:
        '''
        Init Configs.
        :param configs_folder: the folder containing all config files
        :param message: the message object that handles printing
        '''
        # set the configs folder and file
        self.configs_folder = configs_folder
        if not self.configs_folder.folder_exists():
            self.configs_folder.create_folder()
        self.configs_file = self.configs_folder.down_file('config_file')

        # set the message
        self.message = message
        self.message.running_config()

        # get the configs dict
        configs_dict: dict[str, str] = self.get_configs_dict()

        # the check and get functions
        def check_any(user_input: str) -> tuple[bool, str]:
            '''
            The check that always returns success.
            :param user_input: user_input
            :return: (True, '')
            '''
            return True, ''

        def get_str(user_input: str) -> str:
            '''
            The get function that returns the same string.
            :param user_input: user input
            :return: user input
            '''
            return user_input

        def get_list_str(user_input: str) -> list[str]:
            '''
            The get function that returns args from a string.
            :param user_input: user input
            :return: args from a string
            '''
            return user_input.split()

        def check_folder(user_input: str) -> tuple[bool, str]:
            '''
            Check if the user input is a folder.
            :param user_input: user input
            :return: the (success, fail_reason) tuple
            '''
            if Folder(user_input.split('/')).folder_exists():
                return True, ''
            else:
                return False, f'the folder "{user_input}" doesn\'t exist'

        def get_folder(user_input: str) -> Folder:
            '''
            Get a folder from the user input
            :param user_input: user input
            :return: the folder
            '''
            return Folder(user_input.split())

        # create all the config items
        self.item_username = ConfigItemTerminal(
            'username', configs_dict.get('username', None),
            check_any, get_str,
            self.message
        )
        self.item_competitive_programming_folder = ConfigItemTerminal(
            'competitive programming folder', configs_dict.get('competitive programming folder', None),
            check_folder, get_folder,
            self.message
        )
        self.item_codeforces_folder = ConfigItemTerminal(
            'codeforces folder', configs_dict.get('codeforces folder', None),
            check_folder, get_folder,
            self.message
        )
        self.item_cpp_compiler = ConfigItemTerminal(
            'cpp compiler', configs_dict.get('cpp compiler', None),
            check_any, get_str,
            self.message
        )
        self.item_code_editor_command = ConfigItemTerminal(
            'code editor command', configs_dict.get('code editor command', None),
            check_any, get_list_str,
            self.message
        )
        self.item_text_editor_wait_command = ConfigItemTerminal(
            'text editor wait command', configs_dict.get('text editor wait command', None),
            check_any, get_list_str,
            self.message
        )
        self.item_cpp_header = ConfigItemFile(
            'cpp header', self.configs_folder.down_file('cpp_header.cpp'),
            check_any, get_str,
            self.message,
            basefiles.HEADER_CPP,
            self.text_editor_wait_command
        )

        # create the list and set the configs dict
        self.items_terminal = [
            self.item_username,
            self.item_competitive_programming_folder,
            self.item_codeforces_folder,
            self.item_cpp_compiler,
            self.item_code_editor_command,
            self.item_text_editor_wait_command
        ]
        self.items_file = [
            self.item_cpp_header
        ]
        self.set_configs_dict()

    def edit_configs(self) -> None:
        '''
        Edit all config items.
        '''
        # edit all config items the user edits in the terminal
        for config_item_terminal in self.items_terminal:
            config_item_terminal.change_value(False)

        # edit all config items the user edits in files
        for config_item_file in self.items_file:
            config_item_file.text_editor_command_wait = self.text_editor_wait_command
            config_item_file.change_value(False)

        # set the configs dict
        self.set_configs_dict()

    def get_configs_dict(self) -> dict[str, str]:
        '''
        Get the configs dict from the configs file.
        :return: the configs dict
        '''
        if self.configs_file.file_exists():
            configs_dict: dict[str, str] = json.loads(self.configs_file.read_file())
            return configs_dict
        else:
            return {}

    def set_configs_dict(self) -> None:
        '''
        Update the configs file with the new configs dict.
        '''
        # get the configs dict
        configs_dict: dict[str, str] = {}
        for config_item_terminal in self.items_terminal:
            assert config_item_terminal.value_str is not None  # the value should already be set
            configs_dict[config_item_terminal.name] = config_item_terminal.value_str

        # set the configs dict
        self.configs_file.write_file(json.dumps(configs_dict))

    # the getters for all configs

    @property
    def username(self) -> str:
        '''
        Get the username.
        :return: the username
        '''
        assert self.item_username.value is not None
        return self.item_username.value

    @property
    def competitive_programming_folder(self) -> Folder:
        '''
        Get the competitive programming folder.
        :return: the competitive programming folder
        '''
        assert self.item_competitive_programming_folder.value is not None
        return self.item_competitive_programming_folder.value

    @property
    def codeforces_folder(self) -> Folder:
        '''
        Get the codeforces folder.
        :return: the codeforces folder
        '''
        assert self.item_codeforces_folder.value is not None
        return self.item_codeforces_folder.value

    @property
    def cpp_compiler(self) -> str:
        '''
        Get the cpp compiler.
        :return: the cpp compiler
        '''
        assert self.item_cpp_compiler.value is not None
        return self.item_cpp_compiler.value

    @property
    def code_editor_command(self) -> list[str]:
        '''
        Get the code editor command.
        :return: the code editor command
        '''
        assert self.item_code_editor_command.value is not None
        return self.item_code_editor_command.value

    @property
    def text_editor_wait_command(self) -> list[str]:
        '''
        Get the text editor wait command.
        :return: the text editor wait command
        '''
        assert self.item_text_editor_wait_command.value is not None
        return self.item_text_editor_wait_command.value

    @property
    def cpp_header(self) -> str:
        '''
        Get the cpp header.
        :return: the cpp header
        '''
        assert self.item_cpp_header.value is not None
        return self.item_cpp_header.value

    @property
    def offline_html(self) -> File:
        '''
        Get the offline html file.
        :return: the offline html file
        '''
        return self.competitive_programming_folder.down_file('offline_html.html')

    @property
    def input_history(self) -> File:
        '''
        Get the input history file.
        :return: the input history file
        '''
        return self.competitive_programming_folder.down_file('input_history.txt')

    @property
    def parser_history(self) -> File:
        '''
        Get the parser history file.
        :return: the parser history file
        '''
        return self.competitive_programming_folder.down_file('parser_history.txt')
