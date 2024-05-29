from typing import Optional


class Folder:
    '''An immutable path to a folder.'''
    path: list[str]

    def __init__(self, path: Optional[list[str]] = None) -> None:
        '''
        Init the Folder.
        :param path: the path to the folder
        '''
        self.path = [] if path is None else path.copy()

    def __str__(self) -> str:
        '''
        Return the macOS string representation of the path to the folder.
        :returns: the string representation of the path
        '''
        return '/' + '/'.join(self.path) + '/'

    def up(self, up_count: int = 1) -> "Folder":
        '''
        Move cnt levels higher.
        :param up_count: the number of levels to move
        :returns: the folder cnt levels higher or root if the depth is less than cnt
        '''
        return Folder(self.path[:-up_count])

    def down(self, down_folder: str) -> "Folder":
        '''
        Move one level lower to the folder nxt.
        :param down_folder: the folder to move into
        :returns: the folder nxt one level lower than the current one
        '''
        return Folder(self.path + [down_folder])


class File:
    '''An immutable path to a file.'''
    path: list[str]

    def __init__(self, path: list[str]) -> None:
        '''
        Init the File.
        :param path: the path to the file
        '''
        self.path = path.copy()

    def __str__(self) -> str:
        '''
        Return the macOS string representation of the path to the file.
        :returns: the string representation of the path
        '''
        return '/' + '/'.join(self.path)

    def up(self, up_count: int = 1) -> Folder:
        '''
        Move cnt levels higher.
        :param up_count: the number of levels to move
        :returns: the folder cnt levels higher or root if the depth is less than cnt
        '''
        return Folder(self.path[:-up_count])

    def read_file(self) -> str:
        '''
        Read the contents of the file.
        :returns: the file contents
        '''
        with open(str(self), 'r') as f:
            return f.read()

    def write_file(self, contents: str) -> None:
        '''
        Write contents to the file, overriding if the file isn't empty.
        :param contents: the contents to write
        '''
        with open(str(self), 'w') as f:
            f.write(contents)
