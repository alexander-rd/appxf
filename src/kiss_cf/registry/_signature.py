''' signature behavior for authenticity '''

from __future__ import annotations

from kiss_cf.storage import Storable, Storage
from kiss_cf.storage import serialize, deserialize
from kiss_cf.security import Security


class SignatureData():
    ''' Hold signature data '''

    def __init__(self):
        self._version = 1
        self.pub_key: bytes = b''
        self.signature: bytes = b''

    @classmethod
    def from_bytes(cls, data: bytes) -> SignatureData:
        ''' Construct signature data from bytes '''
        obj = cls()
        struct = deserialize(data)
        print(f'Deserialized: {struct}')
        obj.__dict__.update(struct)
        return obj

    def to_bytes(self) -> bytes:
        ''' Get bytes to store signature '''
        data = serialize(self.__dict__)
        print(f'Serialized: {data}')
        return data


class Signature(Storable):
    ''' Maintain public key and signature

    Generated is a class that knows a Security object for signing/verification
    and a StorageMethod to store/load the signature data.

    sign() will take a public key and data to fill this class. The class can
    then be stored.

    load() will load a public key and signature. The class can then be used
    to verify() data.
    '''
    def __init__(self,
                 storage_method: Storage,
                 security: Security):
        super().__init__(storage_method)
        self._security = security
        self._signature: SignatureData = SignatureData()

    @property
    def public_key(self):
        return self._signature.pub_key

    def _get_bytestream(self) -> bytes:
        return self._signature.to_bytes()

    def _set_bytestream(self, data: bytes):
        self._signature = SignatureData.from_bytes(data)

    def verify(self, data: bytes):
        ''' Verify loaded signature

        load() has to be executed, before.'''
        return self._security.verify(
            data=data,
            signature=self._signature.signature,
            public_key_bytes=self._signature.pub_key)

    def sign(self, data: bytes):
        ''' Sign data based on public key in Security object

        Intended is to store() the signature afterwards '''
        self._signature.pub_key = self._security.get_signing_public_key()
        self._signature.signature = self._security.sign(data)
