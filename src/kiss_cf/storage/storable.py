''' Class definitions for storage handling. '''

from .ram import RamStorage
from .storage import Storage


class AppxfStorableError(Exception):
    ''' General storable exception '''


class Storable(object):
    ''' Abstract storable class

    A class with storable behavior defines _what_ is stored on store() via
    _get_state() and provides _set_state() to restore it's state upon load().
    The Storage class handles _how_ data is stored, like: serializing it to
    bytes and writing to a file.

    When deriving from this class, the default behavior would store the classes
    __dict__ which contains all class attributes. Overload _set_state() and
    _get_state() to change the behavior. Stay simplistic with the types you
    hand over to a storage. Serializers only support a limited set of objects
    either because of implementation complexity (JSON) or because loading
    arbitrary objects is not safe (pickle).

    It is recommended that the deriving class adds version information to be
    stored. When the storable implementation changes and you need
    compatibility, you can then adapt _set_dict() to handle legacy data.
    '''
    def __init__(self, storage: Storage | None = None, **kwargs):
        if storage is None:
            storage = RamStorage()
        self._storage: Storage = storage
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
        ''' Load from provided Storage '''
        if not self._storage.exists():
            # Protect deriving classes treating empty data like b''.
            raise AppxfStorableError('Storage does not exist.')
        self._set_state(self._storage.load())

    def store(self):
        ''' Store to provided Storage '''
        self._storage.store(self._get_state())
