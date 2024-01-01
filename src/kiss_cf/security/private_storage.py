''' Secure StorageMethod for private (non-shared) usage '''

from kiss_cf.storage import LocationStorageMethod, DerivingStorageMethod
from .security import Security


class SecurePrivateStorageMethod(DerivingStorageMethod):
    '''Storage method for local file storage.

    This storage method is based on a symmetric key, generated at user
    initialization time. User unlocks this key with his password.

    Consider RemoteSecuredStorage method if the secured data needs to be
    accessed by others.
    '''

    def __init__(self,
                 base_method: LocationStorageMethod,
                 security: Security):
        super().__init__(base_method)
        self._security = security

    def load(self) -> bytes:
        data = self._base_method.load()
        return self._security.decrypt_from_bytes(data)

    def store(self, data: bytes):
        data = self._security.encrypt_to_bytes(data)
        self._base_method.store(data)
