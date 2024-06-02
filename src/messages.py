from prints import Print, StylizedStr, Colors


class Messages:
    '''An immutable object for printing messages and getting user input.'''
    log: Print  # the combination of terminal and files to print to

    def __init__(self, log: Print) -> None:
        '''
        Init Messages.
        :param log: the combination of terminal and files to print to
        '''
        self.log = log

    def hi(self) -> None:
        '''
        Prints 'hi'.
        '''
        self.log.print(StylizedStr('hi'))
