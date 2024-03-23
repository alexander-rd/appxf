from __future__ import annotations

from kiss_cf.storage import Storable, StorageMethod
from kiss_cf.storage import serialize, deserialize
from kiss_cf.security import Security
from .registry import Registry

class PublicEncryptionData():
    ''' Hold signature data '''

    @classmethod
    def __init__(self):
        self._version = 1
        self.key_map: dict[int, bytes] = {}

    @classmethod
    def from_bytes(cls, data: bytes) -> PublicEncryptionData:
        ''' Construct signature data from bytes '''
        obj = cls()
        struct = deserialize(data)
        print(f'Deserialized KEYS: {struct}')
        obj.__dict__.update(struct)
        return obj

    def to_bytes(self) -> bytes:
        ''' Get bytes to store signature '''
        data = serialize(self.__dict__)
        print(f'Serialized KEYS: {data}')
        return data


class PublicEncryption(Storable):
    def __init__(self,
                 storage_method: StorageMethod,
                 security: Security,
                 registry: Registry,
                 # TODO: align default role nomenclature "user" versus "USER"
                 to_roles: str = 'USER'
                 ):
        super().__init__(storage_method)
        self._security = security
        self._registry = registry
        self._to_roles = to_roles
        # self._encryption_data = PublicEncryptionData()
        self._keys: dict[bytes, bytes] = {}

    def _get_bytestream(self) -> bytes:
        return serialize(self._keys)

    def _set_bytestream(self, data: bytes):
        keys = deserialize(data)
        print(f'>> Loaded keys: {keys}')
        self._keys = keys

    def encrypt(self, data: bytes) -> bytes:
        pub_key_list = self._registry.get_encryption_keys(self._to_roles)
        data, keys = self._security.hybrid_encrypt(data, pub_key_list)
        self._keys = keys
        self.store()
        return data

    def decrypt(self, data: bytes) -> bytes:
        self.load()
        data = self._security.hybrid_decrypt(data, self._keys)
        return data
