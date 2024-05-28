class Path:
    '''basic file handling'''
    def __init__(self, path=None):
        '''inits the path'''
        self.path = [] if path is None else path

    def __str__(self):
        '''returns the string representation of the path'''
        return '/' + '/'.join(self.path) + ('/' if self.path and '.' not in self.path[-1] else '')

    def up(self, cnt=1):
        '''goes cnt levels higher'''
        self.path = self.path[:-cnt]

    def down(self, nxt):
        '''descend into the folder nxt'''
        self.path.append(nxt)
