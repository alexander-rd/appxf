''' Class definitions for storage handling. '''

from .storage import Storage, StorageMethodDummy

# TODO: merge comments


class KissStorableError(Exception):
    ''' General storable exception '''


class Storable(object):
    ''' Abstract storable class

    A class with storable behavior defines _what_ is stored on store() via
    _set_state() and provides _get_state() to restore it's state upon load().
    The Storage class handles _how_ data is stored, like: serializing it to
    bytes and writing to a file.

    When deriving from this class, the default behavior would store the classes
    __dict__ which contains all class fields. Overload _set_state() and
    _get_state() to change the behavior. Typically, a dictionary is used.

    It is recommended that the deriving class applies a _version field. When
    the storable implementation changes and you need compatibility, you can
    then adapt _set_dict().
    '''

    def __init__(self, storage: Storage = StorageMethodDummy(), **kwargs):
        self._storage = storage
        super().__init__(**kwargs)


    def _get_state(self) -> object:
        ''' Get object state

        The default implementation uses the classes __dict__ which contains all
        class fields. You may update this method to adapt the behavior.
        '''
        data = self.__dict__.copy()
        # strip storage and settings
        del data['_storage']
        return data

    def _set_state(self, data: object):
        ''' Set object state

        The default implementation restores the classes __dict__ which contains
        all class fields. You may update this method to adapt the behavior.
        '''
        self.__dict__.update(data)  # type: ignore # see _get_state() for consistency

    def exists(self):
        ''' Storage file exists (call before load()) '''
        return self._storage.exists()

    def load(self):
        ''' Restore Storable with bytes from StorageMethod '''
        if not self._storage.exists():
            # Protect deriving classes treating empty data like b''.
            raise KissStorableError('Storage does not exist.')
        self._set_state(self._storage.load())
        # TODO: determine if this one needs an if _storage.exists()

    def store(self):
        ''' Store bytes representing the Storable state '''
        self._storage.store(self._get_state())
