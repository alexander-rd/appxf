import builtins
import io
import os
import pickle

from kiss_cf.security.local import Security
from kiss_cf.storage.storage import Storable, StorageMethod

# TODO (see: https://gist.github.com/major/8ac9f98ae8b07f46b208)
#
# Core: Each user for each role has a USER-ROLE certificate which is signed by
# some USER-ADMIN while the ADMIN certificates are only available online (only
# admins have) access to this.
#
# User grabs certificates AS NEEDED from the remote storage and verifies them
# in the process. Consequence: each certificate stored locally is verified. And
# this database is protected by local encryption.
#
# The registration process is now as follows:
#  1) User sends (in any way) its public key for registration (role or private)
#  2) Application helps the admin in generating the signed certificate. It is
#     signed with the admin's certificate (which has CA attribute).


class UserDataUnencryptedStorageMethod(StorageMethod):
    '''Unencrypted storage method for user data.

    Note that unencrypted data needs some protection to savely load via pickle.
    This is handled in load() via RestrictedUnpickler() according to pickle
    documentation:
    https://docs.python.org/3/library/pickle.html#restricting-globals
    '''
    def __init__(self):
        pass

    class RestrictedUnpickler(pickle.Unpickler):
        '''Class to disable unwanted symbols.'''
        def find_class(self, module, name):
            # Only allow safe classes from builtins.
            if module == "builtins" and name in []:
                return getattr(builtins, name)
            # Forbid everything else.
            raise pickle.UnpicklingError(
                "global '%s.%s' is forbidden" % (module, name))

    def load(self) -> bytes:
        if not self.file:
            Exception('set_file() for Storage base class was never called.')
        if not os.path.isfile(self.file):
            Exception(
                f'File {self.file} does not exist. '
                f'Check usage of storage -> load() before store().')

        with open(self.file, 'rb') as f:
            data_unpacked = f.read()

        return self.RestrictedUnpickler(io.BytesIO(data_unpacked)).load()

    def store(self, data: bytes):
        with open(self.file, 'wb') as f:
            f.write(data)


class UserDatabase(Storable):
    '''Minimal user database functionality'''
    def __init__(self, storage_method, file):
        super().__init__(storage=storage_method, file=file)
        self.key_map = {}

    # TODO: public key should only be valid for certain time interval: needs
    # additional input "timestamp"
    def get_public_key(self, user):
        if user in self.key_map:
            return self.key_map[user]
        else:
            raise Exception(f'User {user} not found.')

    def add_user(self, user, public_key):
        if user in self.key_map:
            raise Exception(f'User {user} already present')
        else:
            self.key_map[user] = public_key

    def remove_user(self, user):
        if user not in self.key_map:
            raise Exception(f'User {user} already present')
        else:
            del self.key_map[user]


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
