''' Basic Storage Methods '''

from abc import ABC, abstractmethod


class Storage(ABC):
    ''' Abstract class to model a storage method.

    The Storage class represents _how_ data is stored (to a file system). It
    abstracts any details on:
      * the actual storage device (local disc, FTP, ..)
      * serialization (convert python objects to bytes)
      * encryption/decryption
      * supporting functionality like data synchronization
    In addition to store()/load(), a Storage object has a function exists() to
    determine if data may be loaded.

    A Storage class may work together with a Storable which represents _what_
    is to be stored. They collaborate by:
      1) The Storable get's a Storage object upon construction
      2) The Storable sets the file name of a Storage
    construction and set the file name to represent a specific storage. It will
    then rely on the load() and store() implementation by consuming/providing a
    byte stream.
    '''
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @abstractmethod
    def id(self) -> str:
        ''' ID for the storage object.

        The ID shall use the StorageMaster ID's which, themselves shall be
        unique. Main purpose of the id() is loggin.
        '''

    @abstractmethod
    def exists(self) -> bool:
        ''' Check existance of storage before loading '''

    @abstractmethod
    def load(self) -> object:
        ''' Load data from Storage '''

    @abstractmethod
    def store(self, data: object):
        ''' Store data to Storage '''


class StorageDummy(Storage):
    ''' Storage dummy as default behavior.

    To allow Storable implementations to always assume having a Storage,
    this class provides a silent replacement. It is recommended if the Storable
    class still uses load()/store() even when not being set up for storage.

    Note: The _set_bytestream() of the Storable must be robust to receive an
    empty bytestream as indication for "no Storage defined".
    '''
    def id(self) -> str:
        return 'StorageDummy'

    def exists(self) -> bool:
        return False

    def load(self) -> object:
        return b''

    def store(self, data: object):
        pass
