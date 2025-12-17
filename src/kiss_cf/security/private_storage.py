''' Secure Storage for private (non-shared) usage '''
from kiss_cf.storage import StorageToBytes, Storage

from .security import Security


class SecurePrivateStorage(StorageToBytes):
    ''' Add private key encryption to any bytes based storage

    This storage adds encrption/decryption to the provided byte based storage
    (typically files). The encryption is based on a symmetric key, generated at
    user initialization time according to the security module. The user unlocks
    this key with his password.
    '''
    def __init__(self,
                 base_storage: StorageToBytes,
                 security: Security,
                 ):
        super().__init__(name=base_storage.name,
                         location=base_storage.location,
                         base_storage=base_storage)
        self._security = security
        # silence type warnings that _base_storage may be None (_base_storage
        # is already written by Storage.__init__())
        self._base_storage = base_storage

    @classmethod
    def get(cls,
            base_storage: StorageToBytes,
            security: Security,
            ) -> Storage:
        ''' Get a known storage object or create one. '''
        # The below is a sample implementation:
        return super().get(
            name=base_storage.name, location=base_storage.location,
            storage_init_fun=lambda: SecurePrivateStorage(
                base_storage=base_storage, security=security
                ))

    @classmethod
    def get_factory(cls, base_storage_factory: Storage.Factory,
                    security: Security) -> Storage.Factory:
        return super().get_factory(
            base_storage=base_storage_factory,
            storage_get_fun=lambda name: SecurePrivateStorage.get(
                base_storage=base_storage_factory(name),
                security=security))

    # Define mandatory Storage functions by relying on base_storage.
    def exists(self) -> bool:
        return self._base_storage.exists()

    def load_raw(self) -> bytes:
        byte_data: bytes = self._base_storage.load_raw()
        if byte_data == b'':
            return b''
        byte_data = self._security.decrypt_from_bytes(byte_data)
        return byte_data
        # Storage implementation of load() uses deserialization

    def store_raw(self, data: bytes):
        # Storage implementation of store() has already applied serializazion.
        byte_data = self._security.encrypt_to_bytes(data)
        self._base_storage.store_raw(byte_data)
