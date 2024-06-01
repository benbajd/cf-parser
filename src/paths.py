'''Implements paths.'''

from typing import Optional
import os


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
        Move one level lower to the folder down_folder.
        :param down_folder: the folder to move into
        :returns: the folder down_folder one level lower than the current one
        '''
        return Folder(self.path + [down_folder])

    def down_file(self, down_file: str) -> "File":
        '''
        Move one level lower to the file down_file
        :param down_file: the file to move into
        :returns: the file down_file one level lower than the current folder
        '''
        return File(self.path + [down_file])

    def create_folder(self) -> None:
        '''
        Create the directory, requires the directory to not exist and the parent directory to exist.
        '''
        os.mkdir(str(self))

    def delete_folder(self) -> None:
        '''
        Delete the directory, requires the directory to exist and be empty.
        '''
        os.rmdir(str(self))

    def folder_exists(self) -> bool:
        '''
        Check if the folder exists.
        :returns: true if the folder exists else false
        '''
        return os.path.isdir(str(self))


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
        with open(str(self), 'r', encoding='utf-8') as f:
            return f.read()

    def write_file(self, contents: str) -> None:
        '''
        Write contents to the file, overriding if the file isn't empty. Creates the file if it doesn't exist.
        :param contents: the contents to write
        '''
        with open(str(self), 'w', encoding='utf-8') as f:
            f.write(contents)

    def append_file(self, contents: str) -> None:
        '''
        Append contents to the end of the file. Creates the file if it doesn't exist.
        :param contents: the contents to append
        '''
        with open(str(self), 'a', encoding='utf-8') as f:
            f.write(contents)

    def delete_file(self) -> None:
        '''
        Delete the file, requires the file to exist.
        '''
        os.remove(str(self))
