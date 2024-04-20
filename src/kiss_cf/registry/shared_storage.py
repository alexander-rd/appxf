''' Security layer for files shared between users '''
# allow class name being used before being fully defined (like in same class):
from __future__ import annotations

from kiss_cf.storage import Storage, DerivingStorageMaster, StorageMaster
from kiss_cf.storage import Serializer, RawSerializer, CompactSerializer
from kiss_cf.security import Security

from .registry import Registry
from ._signature import Signature
from ._public_encryption import PublicEncryption


class SecureSharedStorageMethod(Storage):
    ''' Typical setup for shared storage

    The typical setup consists of the layers:
      1) Public key encryption (to allow others access)
      2) Envelope to control writing permissions and
         provide information for manual inspection
      3) Signature for authenticity
    '''
    def __init__(self,
                 file: str,
                 storage: StorageMaster,
                 security: Security,
                 registry: Registry,
                 serializer: type[Serializer],
                 **kwargs
                 ):
        # TODO: "to roles" is missing input

        # TODO: Reconsider how "allowed writing roles" are considered. I would
        # expect the factory collecting "allowed writers" and "additional
        # readers", assuming writers always must be readers.

        super().__init__(**kwargs)
        self._file = file
        self._base_storage = storage.get_storage(file,
                                                 register=False,
                                                 serializer=RawSerializer)
        self._security = security
        self._registry = registry
        self._serializer = serializer
        self._signature = Signature(
            storage=storage.get_storage(
                file + '.signature', register=False),
            security=security)
        self._public_encryption = PublicEncryption(
            storage_method=storage.get_storage(
                file + '.keys', register=False),
            security=security,
            registry=registry)

    # Stacking concept: The classes used here shall only:
    #  1) process bytes input/output like encrypting/decrypting while
    #  2) adding additional files
    #
    # In the previous concept, the classes called some load/store instead of
    # getting the bytes.

    # Different concept would be: this class is handling ALL BYTES and the
    # reusable classes just generate new bytes from bytes. This class would
    # then be responsible for storing/loading also the supporting files. <<
    # this is the way to go!

    def id(self) -> str:
        return f'{self.__class__.__name__} based on {self._base_storage.id()}'

    def exists(self) -> bool:
        return self._base_storage.exists()

    def store(self, data: object):
        # encryption
        data_bytes = self._serializer.serialize(data)
        data_bytes = self._public_encryption.encrypt(data_bytes)
        self._public_encryption.store()
        # signing (encrypted data)
        self._signature.sign(data_bytes)
        self._signature.store()
        self._base_storage.store(data_bytes)

    def load(self) -> object:
        data_bytes: bytes = self._base_storage.load()
        self._signature.load()
        if not self._signature.verify(data_bytes):
            # TODO: test case for failing signature
            # TODO: KissException
            # TODO: extend error message with infos like file
            raise Exception('Verification signature failed')
        # decryption
        self._public_encryption.load()
        data_bytes = self._public_encryption.decrypt(data_bytes)
        return self._serializer.deserialize(data_bytes)


# TODO: validate the concept that only particular roles are allowed to write
# data. It shall be possible to get files that are configured individually.
class SecureSharedStorageMaster(DerivingStorageMaster):
    ''' Get secured and shared storage methods '''
    def __init__(self,
                 storage: StorageMaster,
                 security: Security,
                 registry: Registry,
                 default_serializer: type[Serializer] = CompactSerializer):
        ''' Get secured and shared storage methods

        Arguments:
            location -- the shared location in which files are stored
            security -- an unlocked security object to access private keys as
                        well as signing/encryption algorithms
            registry -- the user registry to access other users public keys and
                        role assignments
        '''
        super().__init__(storage=storage)
        self._security = security
        self._registry = registry
        self._default_serializer = default_serializer

    def _get_storage(self,
                     name: str,
                     serializer: type[Serializer] | None = None,
                     ) -> Storage:
        if serializer is None:
            serializer = self._default_serializer
        return SecureSharedStorageMethod(
            name,
            storage=self._storage,
            security=self._security,
            registry=self._registry,
            serializer=serializer)
