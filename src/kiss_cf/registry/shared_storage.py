''' Security layer for files shared between users '''
# allow class name being used before being fully defined (like in same class):
from __future__ import annotations

from kiss_cf.storage import Storage, DerivingStorageMaster, StorageMaster
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
                 ):
        # TODO: "to roles" is missing input

        # TODO: Reconsider how "allowed writing roles" are considered. I would
        # expect the factory collecting "allowed writers" and "additional
        # readers", assuming writers always must be readers.

        super().__init__()
        self._file = file
        self._base_storage = storage.get_storage(file, register=False)
        self._security = security
        self._registry = registry
        self._signature = Signature(
            storage_method=storage.get_storage(
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

    def exists(self) -> bool:
        return self._base_storage.exists()

    def store(self, data: bytes):
        print(f'Storing from {self.__class__.__name__} for {self._file}')
        # encryption
        data = self._public_encryption.encrypt(data)
        self._public_encryption.store()
        # signing (encrypted data)
        self._signature.sign(data)
        self._signature.store()
        self._base_storage.store(data)

    # Overloading
    def load(self) -> bytes:
        print(f'Loading from {self.__class__.__name__} for {self._file}')
        data = self._base_storage.load()
        self._signature.load()
        if not self._signature.verify(data):
            # TODO: test case for failing signature
            # TODO: KissException
            # TODO: extend error message with infos like file
            raise Exception('Verification signature failed')
        # decryption
        self._public_encryption.load()
        data = self._public_encryption.decrypt(data)
        return data


# TODO: validate the concept that only particular roles are allowed to write
# data. It shall be possible to get files that are configured individually.
class SecureSharedStorageMaster(DerivingStorageMaster):
    ''' Get secured and shared storage methods '''
    def __init__(self,
                 storage: StorageMaster,
                 security: Security,
                 registry: Registry):
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

    def _get_storage(self, file: str) -> Storage:
        return SecureSharedStorageMethod(
            file,
            storage=self._storage,
            security=self._security,
            registry=self._registry
        )
