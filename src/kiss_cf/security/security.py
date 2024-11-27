'''Define security algorithms.'''

# ## General imports
import os.path
import pickle

# ## Cryptography related imports
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
        'signing_pub_key': b'',
        'signing_priv_key': b'',
        'encryption_pub_key': b'',
        'encryption_priv_key': b'',
    }


#! TODO: it would be helpful being able to construct a security object in RAM
#  for unit testing. Currently, any testing on SecurePrivate or SecureShared or
#  involving Security/Registry would have to use the file system.


class Security():
    '''Maintaining consistent encryption.

    This class defines the security algorithms used and will hold the
    secret_key's
    '''

    def __init__(self,
                 salt: str,
                 file: str = './data/security/keys',
                 **kwargs):
        '''Get security context.

        The salt used to generate secret keys from password is set with
        something but you should provide your own salt. Any string does.
        '''
        super().__init__(**kwargs)
        self._salt = salt
        self._file = file
        self._derived_key = b''
        self._key_dict = _get_default_key_dict()

    def _write_keys(self):
        '''Write key_dict to encrypted file

        Encryption is based on user's password (derived key)
        '''
        data = pickle.dumps(self._key_dict)
        self._encrypt_to_file(self._derived_key, data, self._file)

    def _verify_version(self):
        ''' Verify correct version

        This code might catch later version adaptions.
        '''
        if 'version' not in self._key_dict.keys():
            raise KissSecurityException(
                'Not a KISS security file: no version information')
        if self._key_dict['version'] != 1:
            raise KissSecurityException(
                f'Keys stored in version {self._key_dict["version"]}, '
                f'expected is version 1')

    def _load_keys(self):
        '''Read key_dict from encrypted file

        Encryption is based on user's password (derived key)
        '''
        data = self._decrypt_from_file(self._derived_key, self._file)
        self._key_dict = pickle.loads(data)
        self._verify_version()

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
        return bool(self._key_dict['symmetric_key'])

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
        self._derived_key = self._derive_key(password)
        self._key_dict['symmetric_key'] = self._generate_key()
        self._write_keys()

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
        self._derived_key = self._derive_key(password)
        self._load_keys()

    def _get_symmetric_key(self):
        if not self.is_user_unlocked():
            raise Exception(
                f'Trying to access symmetric keys before '
                'succeeding with unlock_user()')
        return self._key_dict['symmetric_key']

    def encrypt_to_file(self, data, file):
        self._encrypt_to_file(self._get_symmetric_key(), data, file)

    def encrypt_to_bytes(self, data) -> bytes:
        return self._encrypt_to_bytes(self._get_symmetric_key(), data)

    def _encrypt_to_file(self, key, data, file):
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
            f.write(self._encrypt_to_bytes(key, data))

    def _encrypt_to_bytes(self, key, data) -> bytes:
        return Fernet(key).encrypt(data)

    def decrypt_from_file(self, file) -> bytes:
        return self._decrypt_from_file(self._get_symmetric_key(), file)

    def decrypt_from_bytes(self, data: bytes) -> bytes:
        return self._decrypt_from_bytes(self._get_symmetric_key(), data)

    def _decrypt_from_file(self, key, file) -> bytes:
        if not isinstance(file, list):
            file = [file]
        # read encrypted data
        with open(os.path.join(*file), 'rb') as f:
            data_encrypted = f.read()

        return self._decrypt_from_bytes(key, data_encrypted)

    def _decrypt_from_bytes(self, key: bytes, data: bytes) -> bytes:
        # Note that Fernet will also validate the data on decryption. If the
        # algorithm is changed, it needs to be ensured that the decryption is
        # validated before returning it back to the caller (like using a hash
        # on the data)
        return Fernet(key).decrypt(data)

    def get_signing_public_key(self) -> bytes:
        if not self.is_user_unlocked():
            raise Exception(
                'Trying to access public key before '
                'succeeding with unlock_user()')
        self._ensure_signing_keys_exist()
        return self._key_dict['signing_pub_key']

    def get_encryption_public_key(self) -> bytes:
        if not self.is_user_unlocked():
            raise Exception(
                'Trying to access public key before '
                'succeeding with unlock_user()')
        self._ensure_encryption_keys_exist()
        return self._key_dict['encryption_pub_key']

    def _ensure_signing_keys_exist(self):
        ''' Create keys, if required '''
        if (not self._key_dict['signing_pub_key'] and
                not self._key_dict['signing_priv_key']):
            self._generate_signing_keys()
            return
        if (not self._key_dict['signing_pub_key'] or
                not self._key_dict['signing_priv_key']):
            raise KissSecurityException(
                'Only public or private validation key are set. '
                'This should not happen.'
                )

    def _ensure_encryption_keys_exist(self):
        ''' Create keys, if required '''
        if (not self._key_dict['encryption_pub_key'] and
                not self._key_dict['encryption_priv_key']):
            self._generate_encryption_keys()
            return
        if (not self._key_dict['encryption_pub_key'] or
                not self._key_dict['encryption_priv_key']):
            raise KissSecurityException(
                'Only public or private encryption key are set. '
                'This should not happen.'
                )

    def _generate_signing_keys(self):
        ''' Add validation keys '''
        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048)
        private_key = Security._serialize_private_key(key)
        public_key = Security._serialize_public_key(key.public_key())
        self._key_dict['signing_pub_key'] = public_key
        self._key_dict['signing_priv_key'] = private_key
        self._write_keys()

    def _generate_encryption_keys(self):
        ''' Add validation keys '''
        # TODO UPGRADE: Should there be different key variants/algorithms??
        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048)
        private_key = Security._serialize_private_key(key)
        public_key = Security._serialize_public_key(key.public_key())
        self._key_dict['encryption_pub_key'] = public_key
        self._key_dict['encryption_priv_key'] = private_key
        self._write_keys()

    # TODO COMMIT: serialized public keys are far too large
    @classmethod
    def _serialize_public_key(cls, key: rsa.RSAPublicKey) -> bytes:
        return key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo)
        # Note: In a minor test, PEM encoding took 426 bytes. DER encoding took
        # 264 bytes.

        # TODO COMMIT: reconsider the key map using the public keys to index.
        # With 100 users to encrypt for, the size is 25kB already for public
        # keys. An alternative are ID's maintained in the user_db. But ID's
        # would be one more indirection.

    @classmethod
    def _deserialize_public_key(cls, key_bytes: bytes) -> rsa.RSAPublicKey:
        # key = serialization.load_pem_public_key(key_bytes)
        key = serialization.load_der_public_key(key_bytes)
        if not isinstance(key, rsa.RSAPublicKey):
            raise KissSecurityException(
                f'Unexpected key class {key.__class__.__name__}. '
                f'Expected RSAPrivateKey.')
        return key

    @classmethod
    def _serialize_private_key(cls, key: rsa.RSAPrivateKey) -> bytes:
        return key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption())

    @classmethod
    def _deserialize_private_key(cls, key_bytes: bytes) -> rsa.RSAPrivateKey:
        key = serialization.load_pem_private_key(key_bytes, password=None)
        if not isinstance(key, rsa.RSAPrivateKey):
            raise KissSecurityException(
                f'Unexpected key class {key.__class__.__name__}. '
                f'Expected RSAPrivateKey.')
        return key

    def sign(self, data: bytes) -> bytes:
        '''Sign a data byte stream'''
        self._ensure_signing_keys_exist()
        private_key = Security._deserialize_private_key(
            self._key_dict['signing_priv_key'])

        return private_key.sign(
            data,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                        ),
            hashes.SHA256())

    # TODO: verification might not require a login and functionality should be
    # available as class function.
    def verify(self, data, signature, public_key_bytes=None) -> bool:
        if not public_key_bytes:
            self._ensure_signing_keys_exist()
            public_key_bytes = self._key_dict['signing_pub_key']
        public_key = Security._deserialize_public_key(public_key_bytes)

        try:
            public_key.verify(
                signature, data,
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                            salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256())
            return True
        except InvalidSignature:
            return False

    @classmethod
    def _encrypt_with_public_key_to_bytes(cls, data: bytes, key_bytes: bytes):
        public_key = cls._deserialize_public_key(key_bytes)
        return public_key.encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None)
            )

    def _decrypt_with_private_key_from_byes(self, data: bytes):
        private_key = self._deserialize_private_key(
            self._key_dict['encryption_priv_key'])
        return private_key.decrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None)
            )

    def hybrid_encrypt(self,
                       data: bytes,
                       public_key_list: list[bytes] = []
                       ) -> tuple[bytes, dict[bytes, bytes]]:

        public_key_set = set(public_key_list)
        public_key_set.add(self.get_encryption_public_key())

        symmetric_key = self._generate_key()
        data_encrypted = self._encrypt_to_bytes(symmetric_key, data)

        encrypted_key_map = {}
        for key in public_key_set:
            key_encrypted = self._encrypt_with_public_key_to_bytes(
                symmetric_key, key)
            encrypted_key_map[key] = key_encrypted

        return data_encrypted, encrypted_key_map

    # TODO UPGRADE: double-check interface consistency (order of keys and data)
    def hybrid_decrypt(self, data: bytes,
                       encrypted_key_map: dict[bytes, bytes]):
        # get encrypted symmetric key:
        if self.get_encryption_public_key() not in encrypted_key_map.keys():
            # TODO: more refined exception
            raise KissSecurityException(
                'Key list did not contain the public key for this Security '
                'object')

        symmetric_key_encrypted = encrypted_key_map[
            self.get_encryption_public_key()]
        symmetric_key = self._decrypt_with_private_key_from_byes(
            symmetric_key_encrypted)

        return self._decrypt_from_bytes(symmetric_key, data)

    def _derive_key(self, pwd):
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

    def _generate_key(self):
        '''Generate key to encrypt/decrypt synchronously.

        As of now, this just forwards to Fernet's generate_key(). See here:
        https://cryptography.io/en/latest/fernet/.
        '''
        return Fernet.generate_key()
