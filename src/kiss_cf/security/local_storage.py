''' Storage method intended for files stored on the local system '''

from kiss_cf.storage import LocationStorageMethod
from .security import Security


class LocalSecuredStorageMethod(LocationStorageMethod):
    '''Storage method for local file storage.

    This storage method is based on a symmetric key, generated at user
    initialization time. User unlocks this key with his password.

    Consider RemoteSecuredStorage method if the secured data needs to be
    accessed by others.
    '''

    def __init__(self,
                 base_method: LocationStorageMethod,
                 security: Security):
        # as deriving class, we have to already set the location to skip the
        # add_file in derived class:
        self._location = base_method.location
        super().__init__(location=base_method.location, file=base_method.file)
        self._base_method = base_method
        self._security = security

    def load(self) -> bytes:
        data = self._base_method.load()
        return self._security.decrypt_from_bytes(data)

    def store(self, data: bytes):
        data = self._security.encrypt_to_bytes(data)
        self._base_method.store(data)
