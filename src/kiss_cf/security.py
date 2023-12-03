'''Define security algorithms.'''

import os.path

# cryptography error handling
from cryptography.exceptions import InvalidSignature
# generate crypt key from password
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
# synchronous encryption:
from cryptography.fernet import Fernet
# asynchronous encryption:
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from .storage import StorageMethod


class Security():
    '''Maintaining consistent encryption.

    This class defines the security algorithms used and will hold the
    secret_key's
    '''

    def __init__(self, salt='ABERFELDY', storage='./data/security'):
        '''Get security context.

        The salt used to generate secret keys from password is set with
        something but you should provide your own salt. Any string does.
        '''
        self._salt = salt
        self._user_key_file = os.path.join(storage, 'user.key')
        self._public_key_file =  os.path.join(storage, 'user.public.key')
        self._private_key_file =  os.path.join(storage, 'user.private.key')

        self._user_secret_key = ''

    def is_user_initialized(self):
        '''Check if user secret key is initialized.

        If this returns false, you need to get a password to provide to
        init_user(). The class login.Login also provides a GUI for this.
        '''
        return os.path.exists(self._user_key_file)

    def is_user_unlocked(self):
        '''Return if user security context is unlocked.

        If this returns true, encrypt_to_file and decrypt_to_file can be used.
        You can use the GUI from login.Login to unlock a user or you use
        Security.unlock_user() directly.
        '''
        if self._user_secret_key:
            return True
        else:
            return False

    def init_user(self, password):
        '''Initialize user secret key.

        A key is derived from the password (derived key). A secret key, not
        tied to the pasword is generated (secret key). Then, the derived key is
        used to persist the secret key on the file system. The password is not
        stored.

        This step does also unlock the security context to encrypt or decrypt
        user data.
        '''
        derived_key = self.__derive_key(password)
        self._user_secret_key = self.__generate_key()

        self.__encrypt_to_file(derived_key,
                               self._user_secret_key, self._user_key_file)

    def unlock_user(self, password):
        '''Unlock encryp/decrypt for user context by password.

        Loads the user's secret key. See init_user() on how it is stored. If
        the key is not correct, the underlying algorihms throws an exception
        which should be cought to handle wrong passwords.
        '''
        if not self.is_user_initialized():
            raise Exception(
                'User is not initialized. Run init_user() '
                f'if file {self._user_key_file} was lost.')
        derived_key = self.__derive_key(password)
        self._user_secret_key = self.__decrypt_from_file(
            derived_key, self._user_key_file)

    def get_storage_method(self) -> StorageMethod:
        '''Get StorageMethod object to use with Storable'''
        return SecureStorage(security=self)

    def encrypt_to_file(self, data, file):
        if not self.is_user_unlocked():
            raise Exception(
                f'Trying to encrypt {file} before '
                'succeeding with unlock_user()')
        self.__encrypt_to_file(self._user_secret_key, data, file)

    def __encrypt_to_file(self, key, data, file):
        # get file where file is allowed to be a list of strings to avoid
        # caller needing to use os.path:
        if not isinstance(file, list):
            file = [file]
        file = os.path.join(*file)
        # ensure path exists
        file_dir = os.path.dirname(file)
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)

        with open(file, 'wb') as f:
            f.write(Fernet(key).encrypt(data))

    def decrypt_from_file(self, file) -> bytes:
        if not self.is_user_unlocked():
            raise Exception(
                'Trying to decrypt {file} before '
                'succeeding with unlock_user()')
        return self.__decrypt_from_file(self._user_secret_key, file)

    def __decrypt_from_file(self, key, file) -> bytes:
        if not isinstance(file, list):
            file = [file]
        # read encrypted data
        with open(os.path.join(*file), 'rb') as f:
            data_encrypted = f.read()

        # Note that Fernet will also validate the data on decryption. If the
        # algorithm is changed, it needs to be ensured that the decryption is
        # validated before returning it back to the caller (like using a hash
        # on the data)
        data = Fernet(key).decrypt(data_encrypted)

        return data

    def get_public_key(self) -> bytes:
        if not self.is_user_unlocked():
            raise Exception(
                'Trying to access public key before '
                'succeeding with unlock_user()')
        if not self.__rsa_keys_exist():
            self.__generate_rsa_keys()

        return self.decrypt_from_file(self._public_key_file)

    def __rsa_keys_exist(self):
        if (os.path.exists(self._public_key_file) and
            os.path.exists(self._private_key_file)
            ):
            return True
        else:
            return False

    def __ensure_rsa_keys_exist(self):
        if not self.__rsa_keys_exist():
            self.__generate_rsa_keys()

    def __generate_rsa_keys(self):
        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048)
        private_key = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
            )
        self.encrypt_to_file(private_key, self._private_key_file)
        public_key = key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.PKCS1)
        self.encrypt_to_file(public_key, self._public_key_file)

    def sign(self, data: bytes) -> bytes:
        '''Sign a data byte stream'''
        self.__ensure_rsa_keys_exist()
        private_key = serialization.load_pem_private_key(
            self.decrypt_from_file(self._private_key_file),
            password=None
            )
        return private_key.sign(
            data,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                        ),
            hashes.SHA256())

    def verify(self, data, signature, public_key_bytes=None):
        if not self.__rsa_keys_exist():
            raise Exception(
                'Trying to verify data while no private/public key exists. '
                'Key files are lost or were never generated.')
        if public_key_bytes is None:
            public_key_bytes = self.decrypt_from_file(self._public_key_file)
        public_key = serialization.load_pem_public_key(
            public_key_bytes)
        try:
            public_key.verify(
                signature, data,
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                            salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256())
            return True
        except InvalidSignature:
            return False

    def __derive_key(self, pwd):
        '''Derive key from password.

        This should be done immediately after getting a password. The password
        itself should not remain in memory.

        If this algorithm changes, users will not be able to reach their secret
        keys anymore.
        '''
        kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=bytes(self._salt, 'utf-8'),
                iterations=480000,
                )
        return base64.urlsafe_b64encode(kdf.derive(bytes(pwd, 'utf-8')))

    def __generate_key(self):
        '''Generate key to encrypt/decrypt synchronously.

        As of now, this just forwards to Fernet's generate_key(). See here:
        https://cryptography.io/en/latest/fernet/.
        '''
        return Fernet.generate_key()


class SecureStorage(StorageMethod):
    def __init__(self,
                 security: Security):
        self.security = security

    def load(self) -> bytes:
        if self.file is None:
            Exception('set_file() for Storage base class was never called.')
        if not os.path.isfile(self.file):
            Exception(f'File {self.file} does not exist. Check usage of storage -> load() before store().')

        # TODO: the above is pretty much generic. But I think load() should behave gracefully.
        return self.security.decrypt_from_file(self.file)

    def store(self, data: bytes):
        if self.file is None:
            Exception('set_file() for Storage base class was never called.')

        self.security.encrypt_to_file(data, self.file)