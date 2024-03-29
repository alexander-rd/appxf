''' Secure StorageMethod for private (non-shared) usage '''

from kiss_cf.storage import StorageMethod, StorageFactory, DerivingStorageFactory

from .security import Security


class SecurePrivateStorageMethod(StorageMethod):
    ''' Storage method for local file storage.

    Intended usage via the storage factory
    '''

    def __init__(self,
                 file: str,
                 storage: StorageFactory,
                 security: Security):
        super().__init__()
        self._file = file
        self._base_storage = storage.get_storage_method(file, register=False)
        self._security = security

    def exists(self) -> bool:
        return self._base_storage.exists()

    def load(self) -> bytes:
        data = self._base_storage.load()
        return self._security.decrypt_from_bytes(data)

    def store(self, data: bytes):
        data = self._security.encrypt_to_bytes(data)
        self._base_storage.store(data)


class SecurePrivateStorageFactory(DerivingStorageFactory):
    ''' Add security layer to any location storage

    The produced storage methods add encrption/decryption to the provided
    location storage. The encryption is based on a symmetric key, generated at
    user initialization time. The user unlocks this key with his password.

    Consider SecureSharedStorageFactory if the secured data needs to be
    accessed by others.
    '''
    def __init__(self,
                 storage: StorageFactory,
                 security: Security):
        super().__init__(storage)
        self._security = security

    def _get_storage_method(self, file: str) -> StorageMethod:
        return SecurePrivateStorageMethod(
            file,
            storage=self._storage,
            security=self._security)
