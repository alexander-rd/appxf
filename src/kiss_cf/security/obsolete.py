import builtins
import io
import os
import pickle

from kiss_cf.security.security import Security
from kiss_cf.storage.storage_method import Storable, StorageMethod


class SecureRemoteStorageMethod(StorageMethod):
    '''Storage method to share information with other tool users.

    To ensure authenticity, the data is signed on store() based on the users
    secret key. On load() the signature is checked against the user database.

    To ensure confidentiality, the data is encrypted with a randomly generated
    symetric key. This key is encrypted with the public key of each expected
    recipient plus the creator of the data.

    The user database is typcially also created based on this class. The user
    database input to this class when verifying needs a trusted source.

    !! Where does the user database come from and how is it encrypted ???

    Remote storage includes the following security features:
     * Data is encrypted and keys are only available to known recipients
     * Data is signed by the person that issued the data
    '''
    def __init__(self,
                 security: Security,
                 user_database: UserDatabase,
                 recipients_public_keys: UserDatabase):
        self.security = security

    def load(self) -> bytes:
        if self.file is None:
            Exception('set_file() for Storage base class was never called.')
        if not os.path.isfile(self.file):
            Exception(
                f'File {self.file} does not exist. '
                f'Check usage of storage -> load() before store().')

        # TODO: the above is pretty much generic. But I think load() should
        # behave gracefully.
        return self.security.decrypt_from_file(self.file)

    def store(self, data: bytes):
        if self.file is None:
            Exception('set_file() for Storage base class was never called.')

        self.security.encrypt_to_file(data, self.file)
