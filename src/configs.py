'''Implements storing the config file for basic configs.'''

from paths import Folder, File

# TODO: store locally and check when starting the parser

config_folder = Folder(['~', '.config', 'cf-parser'])

competitive_programming_folder = Folder()
codeforces_folder = Folder()

username = ''

cpp_compiler = ''

code_editor_command = []

text_editor_command_wait = []

input_history = competitive_programming_folder.down_file('input_history.txt')
parser_history = competitive_programming_folder.down_file('parser_history.txt')

history_commandsuite_problem: File = config_folder.down_file('commandsuite_problem_history')
history_two_options: File = config_folder.down_file('two_options_history')
