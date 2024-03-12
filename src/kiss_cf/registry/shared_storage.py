''' Security layer for files shared between users

Classes:
    PublicEncryptedStorageMethod: Public key encryption (to allow others access)
    EnvelopeStorageMethod: Envelope to control writing permissions and
        provide information for manual inspection
    SignedStorageMethod: Signature for authenticity SecureSharedStorageMethod:
        A class collecting all above feature into the common approach that
        should be used.
    SecureSharedStorageMethod: Recommended method for shared storage, including
        all above mechanisms.
'''

# allow class name being used before being fully defined (like in same class):
from __future__ import annotations

from kiss_cf.storage import StorageLocation, LocationStorageMethod, DerivingStorageMethod
from kiss_cf.storage import serialize, deserialize
from kiss_cf.security import Security
from .user_db import UserDatabase

class PublicEncryptedStorageMethod(DerivingStorageMethod):
    def __init__(self,
                 base_method: LocationStorageMethod,
                 security: Security,
                 user_database: UserDatabase,
                 # TODO: align default role nomenclature "user" versus "USER"
                 as_role: str = 'USER'
                 ):
        super().__init__(base_method)
        self._security = security
        self._user_database = user_database
        self._as_role = as_role

    def load(self) -> bytes:
        print(f'Loading from {self.__class__.__name__}')
        # self._location._load(self._file + '.keys', b'')
        return self._base_method.load()

    def store(self, data: bytes):
        print(f'Storing from {self.__class__.__name__}')
        self._location._store(self._file + '.keys', b'')
        self._base_method.store(data)

class EnvelopeStorageMethod(DerivingStorageMethod):
    def __init__(self,
                 base_method: LocationStorageMethod,
                 security: Security,
                 user_database: UserDatabase,
                 # TODO: align default role nomenclature "user" versus "USER"
                 as_role: str = 'USER',
                 to_roles: list[str] = []
                 ):
        super().__init__(base_method)
        self._security = security
        self._user_database = user_database
        self._as_role = as_role
        self._to_roles = to_roles

    def load(self) -> bytes:
        print(f'Loading1 from {self.__class__.__name__}')
        # self._location._load(self._file + 'keys', b'')
        return self._base_method.load()

    def store(self, data: bytes):
        print(f'Storing1 from {self.__class__.__name__}')
        self._base_method.store(data)
        self._location._store(self._file + '.envelope', b'')

class Signature:
    def __init__(self):
        self._version = 1
        self._pub_key = b''
        self._signature = b''
        pass

    @property
    def public_key(self):
        return self._pub_key
    @property
    def signature(self):
        return self._signature

    @classmethod
    def from_data(cls, public_key: bytes, signature: bytes) -> Signature:
        obj = cls()
        obj._pub_key = public_key
        obj._signature = signature
        return obj

    @classmethod
    def from_bytes(cls, data: bytes) -> Signature:
        obj = cls()
        print(f'Deserialized: {deserialize(data)}')
        obj.__dict__.update(deserialize(data))
        return obj

    @classmethod
    def from_location(cls, location: StorageLocation, file: str) -> Signature:
        print(f'Loading2 from {cls.__name__} with {location} and {file}')
        data = location._load(file + '.signature')
        print(f'Got data: {data}')
        return cls.from_bytes(data)

    def to_bytes(self) -> bytes:
        data = serialize(self.__dict__)
        print(f'Serialized: {data}')
        return data

    def store(self, location: StorageLocation, file: str):
        print(f'Storing2 from {self.__class__.__name__}')
        data = self.to_bytes()
        location._store(file + '.signature', data)

    # TODO: ^^ double-check usage of store() versus _store() (and load)


class SignedStorageMethod(DerivingStorageMethod):
    ''' Adding a signature to a StorageMethod

    Signatures are required for authenticity. This StorageMethod adds a
    signature file to the StorageLocation when storing data and verifies the
    signature when loading. It requires a UserDatabase for this check.

    The signature can include the content of other data, added by deriving
    StorageMethods (provided by include_extensions parameter)
    '''

    def __init__(self,
                 base_method: LocationStorageMethod,
                 security: Security,
                 user_database: UserDatabase,
                 include_extensions: list[str] =  []):
        super().__init__(base_method)
        self._security = security
        self._user_database = user_database
        self._extensions = include_extensions

    def load(self) -> bytes:
        print(f'Loading3 from {self.__class__.__name__}')
        data = self._base_method.load()

        ## signature handling
        # load signature:
        signature = Signature.from_location(self._location, self._file)
        # load data:
        sign_data = self._get_signature_data(data)
        # verify:
        if not self._security.verify(
            sign_data, signature.signature, signature.public_key
            ):
            # TODO: this requires an exception
            pass

        return data

    def store(self, data: bytes):
        print(f'Storing3 from {self.__class__.__name__}')
        self._base_method.store(data)

        data = self._security.encrypt_to_bytes(data)

        ## signature handling
        # accumulate to-be-signed data and sign:
        signature = self._security.sign(self._get_signature_data(data))
        # need to provide public key for signature:
        public_key = self._security.get_signing_public_key()
        Signature.from_data(public_key, signature).store(self._location, self._file)


    def _get_signature_data(self, data: bytes) -> bytes:
        sign_data = data
        for ext in self._extensions:
            data += self._location.load(self._file + '.' + ext)
        return sign_data


class SecureSharedStorageMethod(SignedStorageMethod):
    ''' Typical setup for shared storage

    The typical setup consists of the layers:
      1) Public key encryption (to allow others access)
      2) Envelope to control writing permissions and
         provide information for manual inspection
      3) Signature for authenticity
    '''
    def __init__(self,
                 base_method: LocationStorageMethod,
                 security: Security,
                 user_database: UserDatabase,
                 as_role: str = 'USER',
                 to_roles: list[str] = []
                 ):
        # default method is encapsulating multiple steps.
        encrypted = PublicEncryptedStorageMethod(
            base_method,
            security,
            user_database,
            as_role)
        with_envelope = EnvelopeStorageMethod(
            encrypted,
            security,
            user_database,
            as_role,
            to_roles
        )
        # final step is being signed:
        super().__init__(
            with_envelope,
            security,
            user_database,
            include_extensions=['keys', 'envelope'])

    # TODO UPGRADE: the below should not be required when deriving from signed class:
    #def load(self) -> bytes:
    #    print(f'Loading4 from {self.__class__.__name__}')
    #    return self._base_method.load()

    #def store(self, data: bytes):
    #    print(f'Storing4 from {self.__class__.__name__}')
    #    self._base_method.store(data)
