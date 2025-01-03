''' Class definitions for storage handling. '''

from kiss_cf import Stateful
from .ram import RamStorage
from .storage import Storage


class AppxfStorableError(Exception):
    ''' General storable exception '''


class Storable(Stateful):
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

    # taking over get_state()/set_state() from Stateful

    def exists(self):
        ''' Storage file exists (call before load()) '''
        return self._storage.exists()

    def load(self):
        ''' Load from provided Storage '''
        if not self._storage.exists():
            # Protect deriving classes treating empty data like b''.
            raise AppxfStorableError('Storage does not exist.')
        self.set_state(self._storage.load()) # type: ignore  # see store()

    def store(self):
        ''' Store to provided Storage '''
        self._storage.store(self.get_state())

# 1) It makes sense that anything storable has a store()/load() and before
#    load() an exist()
# 2) A basic storable could provide those interfaces WITHOUT coupling to
#    storage >> Storable would become independent of storage. But Why? The
#    concept is Storable=What and Storage=How.
#
# Sticking with the name "Storable", separating from Storage does not seem
# reasonable. Even though get_state()/set_state() already indicate something
# that could be stored and restored.. ..but does not yet know _how_.