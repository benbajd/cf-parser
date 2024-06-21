'''Implements storing the config file for basic configs.'''

from paths import Folder, File

# TODO: store locally and check when starting the parser

config_folder = Folder(['~', '.config', 'cf-parser'])

username = ''

cpp_compiler = ''

code_editor_command = []

text_editor_command_wait = []

history_commandsuite_problem: File = config_folder.down_file('commandsuite_problem_history')
history_two_options: File = config_folder.down_file('two_options_history')
