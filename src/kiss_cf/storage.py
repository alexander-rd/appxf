''' Class definitions for storage handling. '''

from abc import ABC, abstractmethod
import os.path

class Storage(ABC):
    ''' Abstract class to model a storage.

    The Storage class is responsible for storing data to a file system and
    loading it from there. It abstracts details like used encrpytion
    mechanisms.

    The Storable class will know a Storage upon construction and sets the
    Storage's file name. It will then rely on the load() and store()
    implementation by digesting/providing a a byte stream.
    '''
    def __init__(self):
        self.file = None

    @abstractmethod
    def load(self) -> bytes:
        pass

    @abstractmethod
    def store(self, data: bytes):
        pass

    def set_file(self, file: str):
        self.file = file


class Storable(ABC):
    ''' Abstract storable class

    A class with storable behavior will derive from this class. It will
    generate a file name and Storage (typically by constructor parameters) to
    initialize this parent Storable object.

    This class provides a load()/store() functionality for the child object.
    Those functions rely on the child class provided _get_bytestream() and
    _set_bytestream() functions that provide/digest the class state as
    bytestream. A typical approach is to use pickle's dumps/loads.
    '''

    def __init__(self, storage: Storage | None, file: str):
        if storage is None:
            storage = StorageDummy()
        self.storage = storage
        self.file = file
        self.storage.set_file(file)

    @abstractmethod
    def _get_bytestream(self) -> bytes:
        pass

    @abstractmethod
    def _set_bytestream(self, data: bytes):
        pass

    def load(self):
        # only load if file exists
        if os.path.isfile(self.file):
            self._set_bytestream(self.storage.load())

    def store(self):
        self.storage.store(self._get_bytestream())


class StorageDummy(Storage):
    ''' Storage dummy as default behavior.

    To allow Storage implementations to always assume having a Storage, this
    class provides a silent replacement which is recommended if the Storage
    class still uses load()/store() even when not being set up for storage.

    In this case, the _set_bytestream() function must be robust to receive an
    empty bytestream as indication for "no Storage defined".
    '''
    def load(self) -> bytes:
        return b''

    def store(self, data: bytes):
        pass