''' Secure StorageMethod for private (non-shared) usage '''

from kiss_cf.storage import Storage, StorageMaster, DerivingStorageMaster
from kiss_cf.storage import Serializer, RawSerializer, CompactSerializer

from .security import Security

# TODO: check Kiss errors and reduce to one per module or, at least, to one per
# base class if not required otherwise.


class SecurePrivateStorageMethod(Storage):
    ''' Storage method for local file storage.

    Intended usage via the StorageMaster
    '''

    def __init__(self,
                 file: str,
                 storage: StorageMaster,
                 security: Security,
                 serializer: type[Serializer]):
        super().__init__()
        self._file = file
        self._base_storage = storage.get_storage(file,
                                                 register=False,
                                                 serializer=RawSerializer)
        self._security = security
        self._serializer = serializer

    def exists(self) -> bool:
        return self._base_storage.exists()

    def load(self) -> object:
        byte_data: bytes = self._base_storage.load()
        byte_data = self._security.decrypt_from_bytes(byte_data)
        return self._serializer.deserialize(byte_data)

    def store(self, data: object):
        byte_data = self._serializer.serialize(data)
        byte_data = self._security.encrypt_to_bytes(byte_data)
        self._base_storage.store(byte_data)


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
                 security: Security,
                 default_serializer: type[Serializer] = CompactSerializer):
        super().__init__(storage)
        self._security = security
        self._default_serializer = default_serializer

    def _get_storage(self,
                     file: str,
                     serializer: type[Serializer] | None = None,
                     ) -> Storage:
        if serializer is None:
            serializer = self._default_serializer
        return SecurePrivateStorageMethod(
            file,
            storage=self._storage,
            security=self._security,
            serializer=serializer)
