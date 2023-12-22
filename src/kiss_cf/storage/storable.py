''' Class definitions for storage handling. '''

from abc import ABC, abstractmethod
import pickle
import builtins
import io
import json

from kiss_cf.storage import StorageMethod, StorageMethodDummy

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

    def __init__(self, storage_method: StorageMethod = StorageMethodDummy()):
        self.storage = storage_method

    @abstractmethod
    def _get_bytestream(self) -> bytes:
        ''' Provide bytes representing the Storable state '''

    @abstractmethod
    def _set_bytestream(self, data: bytes):
        ''' Restore Storable state from bytes '''

    def load(self):
        ''' Restore Storable with bytes from StorageMethod '''
        self._set_bytestream(self.storage.load())

    def store(self):
        ''' Store bytes representing the Storable state '''
        self.storage.store(self._get_bytestream())


# TODO UPGRADE: review this class. It is currently not used.
class ClassDictStorable(Storable):
    ''' Pickles/Unpickles class attributes in __dict__

    Use this helper with care. It is recommended to add a version attribute to
    the class to catch incompatibilities by arising later code changes.

    This class can be used for unencrypted storage. Note that unencrypted data
    needs some protection to securely load via pickle. This is handled in
    _set_bytestream() via RestrictedUnpickler according to pickle
    documentation:
    https://docs.python.org/3/library/pickle.html#restricting-globals
    '''
    def __init__(self, storage: StorageMethod):
        super().__init__(storage)

    class RestrictedUnpickler(pickle.Unpickler):
        '''Class to disable unwanted symbols.'''
        def find_class(self, module, name):
            # Only allow safe classes from builtins.
            if module == "builtins" and name in []:
                return getattr(builtins, name)
            # Forbid everything else.
            raise pickle.UnpicklingError(
                f'global "{module}.{name}" is forbidden', module, name)

    def _get_bytestream(self) -> bytes:
        return pickle.dumps(self.__dict__)

    def _set_bytestream(self, data: bytes):
        self.__dict__ = self.RestrictedUnpickler(io.BytesIO(data)).load()
