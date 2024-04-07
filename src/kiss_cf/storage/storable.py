''' Class definitions for storage handling. '''

from abc import ABC, abstractmethod

from .storage import Storage, StorageMethodDummy


class Storable(ABC):
    ''' Abstract storable class

    A class with storable behavior will derive from this class. It will
    generate a file name and Storage (typically by constructor parameters) to
    initialize this parent Storable object.

    This class provides a load()/store() functionality for the child object.
    Those functions rely on the child class provided _get_bytestream() and
    _set_bytestream() functions that provide/consume the class state as
    bytestream. A typical approach is to use pickle's dumps/loads.
    '''

    def __init__(self, storage: Storage = StorageMethodDummy()):
        self._storage = storage

    @abstractmethod
    def _get_bytestream(self) -> bytes:
        ''' Provide bytes representing the Storable state '''

    @abstractmethod
    def _set_bytestream(self, data: bytes):
        ''' Restore Storable state from bytes '''

    def exists(self):
        ''' Storage file exists (call before load()) '''
        return self._storage.exists()

    def load(self):
        ''' Restore Storable with bytes from StorageMethod '''
        self._set_bytestream(self._storage.load())

    def store(self):
        ''' Store bytes representing the Storable state '''
        self._storage.store(self._get_bytestream())
