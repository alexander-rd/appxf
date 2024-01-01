'''Define security algorithms.'''

### General imports
import os.path
import pickle

### Cryptography related imports
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


class KissSecurityException(Exception):
    ''' General security related errors. '''

def _get_default_key_dict():
    return {
        'version': 1,
        'symmetric_key': b'',
        'validation_pub_key': b'',
        'validation_priv_key': b'',
        'encryption_pub_key': b'',
        'encryption_priv_key': b'',
    }

class Security():
    '''Maintaining consistent encryption.

    This class defines the security algorithms used and will hold the
    secret_key's
    '''

    def __init__(self, salt: str, file='./data/security/user.keys'):
        '''Get security context.

        The salt used to generate secret keys from password is set with
        something but you should provide your own salt. Any string does.
        '''
        super().__init__()
        self._salt = salt
        self._file = file
        self._derived_key = b''
        self.key_dict = _get_default_key_dict()

    def __write_keys(self):
        '''Write key_dict to encrypted file

        Encryption is based on user's password (derived key)
        '''
        data = pickle.dumps(self.key_dict)
        self.__encrypt_to_file(self._derived_key, data, self._file)

    def __verify_version(self):
        ''' Verify correct version

        This code might catch later version adaptions.
        '''
        if 'version' not in self.key_dict.keys():
            raise KissSecurityException('Not a KISS security file: no version information')
        if self.key_dict['version'] != 1:
            raise KissSecurityException(
                f'Keys stored in version {self.key_dict["version"]}, expected is version 1')

    def __load_keys(self):
        '''Read key_dict from encrypted file

        Encryption is based on user's password (derived key)
        '''
        data = self.__decrypt_from_file(self._derived_key, self._file)
        self.key_dict = pickle.loads(data)
        self.__verify_version()

    def is_user_initialized(self):
        '''Check if user secret key is initialized.

        If this returns false, you need to get a password to provide to
        init_user(). The class login.Login also provides a GUI for this.
        '''
        return os.path.exists(self._file)

    def is_user_unlocked(self):
        '''Return if user security context is unlocked.

        If this returns true, encrypt_to_file and decrypt_to_file can be used.
        You can use the GUI from login.Login to unlock a user or you use
        Security.unlock_user() directly.
        '''
        return bool(self.key_dict['symmetric_key'])

    def init_user(self, password):
        '''Initialize user secret key.

        A key is derived from the password (derived key). A secret key, not
        tied to the pasword is generated (secret key). Then, the derived key is
        used to persist the secret key on the file system. The password is not
        stored.

        This step does also unlock the security context to encrypt or decrypt
        user data.
        '''
        # Do not overwrite existing keys:
        if self.is_user_initialized():
            raise KissSecurityException('Keys are already initialized.')
        self._derived_key = self.__derive_key(password)
        self.key_dict['symmetric_key'] = self.__generate_key()
        self.__write_keys()

    def unlock_user(self, password):
        '''Unlock encryp/decrypt for user context by password.

        Loads the user's secret key. See init_user() on how it is stored. If
        the key is not correct, the underlying algorihms throws an exception
        which should be cought to handle wrong passwords.
        '''
        if not self.is_user_initialized():
            raise Exception(
                'User is not initialized. Run init_user() '
                f'if file {self._file} was lost.')
        self._derived_key = self.__derive_key(password)
        self.__load_keys()

    def _get_symmetric_key(self):
        if not self.is_user_unlocked():
            raise Exception(
                f'Trying to encrypt {self.file} before '
                'succeeding with unlock_user()')
        return self.key_dict['symmetric_key']

    def encrypt_to_file(self, data, file):
        self.__encrypt_to_file(self._get_symmetric_key(), data, file)

    def encrypt_to_bytes(self, data) -> bytes:
        return self.__encrypt_to_bytes(self._get_symmetric_key(), data)

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
            f.write(self.__encrypt_to_bytes(key, data))

    def __encrypt_to_bytes(self, key, data) -> bytes:
        return Fernet(key).encrypt(data)

    def decrypt_from_file(self, file) -> bytes:
        return self.__decrypt_from_file(self._get_symmetric_key(), file)

    def decrypt_from_bytes(self, data: bytes) -> bytes:
        return self.__decrypt_from_bytes(self._get_symmetric_key(), data)

    def __decrypt_from_file(self, key, file) -> bytes:
        if not isinstance(file, list):
            file = [file]
        # read encrypted data
        with open(os.path.join(*file), 'rb') as f:
            data_encrypted = f.read()

        return self.__decrypt_from_bytes(key, data_encrypted)

    def __decrypt_from_bytes(self, key, data: bytes) -> bytes:
        # Note that Fernet will also validate the data on decryption. If the
        # algorithm is changed, it needs to be ensured that the decryption is
        # validated before returning it back to the caller (like using a hash
        # on the data)
        return Fernet(key).decrypt(data)

    def get_validation_public_key(self) -> bytes:
        return b'validation_public_key'
        # TODO UPGRADE: implement
        if not self.is_user_unlocked():
            raise Exception(
                'Trying to access public key before '
                'succeeding with unlock_user()')
        if not self.__rsa_keys_exist():
            self.__generate_rsa_keys()

        return self.decrypt_from_file(self._public_key_file)

    def get_encryption_public_key(self) -> bytes:
        return b'encrption_public_key'
        # TODO UPGRADE: implement

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
        return b'a signature'
        # TODO UPGRADE: redo implementation
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

    def verify(self, data, signature, public_key_bytes=None) -> bool:
        return bool(signature == 'a signature')
        # TODO UPGRADE: implementation
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
