''' Basic Storage Methods '''

from abc import ABC, abstractmethod


class StorageMethod(ABC):
    ''' Abstract class to model a storage method.

    The StorageMethod class is responsible for storing data to a file system
    and loading it from there. It abstracts details like used encrpytion
    mechanisms.

    The Storable class will get a StorageMethod upon construction, take a
    deepcopy and set the file name to represent a specific storage. It will
    then rely on the load() and store() implementation by consuming/providing a
    byte stream.
    '''
    def __init__(self):
        pass

    @abstractmethod
    def load(self) -> bytes:
        ''' Load data from Storage'''

    @abstractmethod
    def store(self, data: bytes):
        ''' Store data to Storage '''


class StorageMethodDummy(StorageMethod):
    ''' Storage dummy as default behavior.

    To allow Storable implementations to always assume having a StorageMethod,
    this class provides a silent replacement. It is recommended if the Storable
    class still uses load()/store() even when not being set up for storage.

    Note: The _set_bytestream() of the Storable must be robust to receive an
    empty bytestream as indication for "no Storage defined".
    '''
    def load(self) -> bytes:
        return b''

    def store(self, data: bytes):
        pass
