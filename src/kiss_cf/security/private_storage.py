''' Secure StorageMethod for private (non-shared) usage '''

from kiss_cf.storage import Storage, StorageMaster, DerivingStorageMaster

from .security import Security


class SecurePrivateStorageMethod(Storage):
    ''' Storage method for local file storage.

    Intended usage via the StorageMaster
    '''

    def __init__(self,
                 file: str,
                 storage: StorageMaster,
                 security: Security):
        super().__init__()
        self._file = file
        self._base_storage = storage.get_storage(file, register=False)
        self._security = security

    def exists(self) -> bool:
        return self._base_storage.exists()

    def load(self) -> bytes:
        data = self._base_storage.load()
        return self._security.decrypt_from_bytes(data)

    def store(self, data: bytes):
        data = self._security.encrypt_to_bytes(data)
        self._base_storage.store(data)


class SecurePrivateStorageMaster(DerivingStorageMaster):
    ''' Add security layer to any location storage

    The produced storage methods add encrption/decryption to the provided
    location storage. The encryption is based on a symmetric key, generated at
    user initialization time. The user unlocks this key with his password.

    Consider SecureSharedStorageMaster if the secured data needs to be
    accessed by others.
    '''
    def __init__(self,
                 storage: StorageMaster,
                 security: Security):
        super().__init__(storage)
        self._security = security

    def _get_storage(self, file: str) -> Storage:
        return SecurePrivateStorageMethod(
            file,
            storage=self._storage,
            security=self._security)
