''' Storable user ID '''

from kiss_cf.storage import Storable, Storage


class KissExceptionUserId(Exception):
    ''' Load/Store error for user ID '''


class UserId(Storable):
    ''' Storable user ID '''
    def __init__(self,
                 storage_method: Storage,
                 **kwargs):
        super().__init__(storage_method, **kwargs)
        self._id: int = -1

    @property
    def id(self):
        ''' The USER ID

        Will be loaded from file if not yet done. Throws error
        KissExceptionUserId if file does not exist.
        '''
        # error if still unloaded
        if self._id < 0 and not self._storage.exists():
            raise KissExceptionUserId('Cannot access USER ID: not yet written')
        # ensure loaded
        if self._id < 0:
            self.load()
        return self._id

    @id.setter
    def id(self, user_id: int):
        self._id = user_id
        self.store()

    def set_state(self, data: bytes):
        self._id = int.from_bytes(data, 'big', signed=False)

    def get_state(self) -> bytes:
        return self._id.to_bytes(2, 'big', signed=False)
