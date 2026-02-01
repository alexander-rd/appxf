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
from typing import Any, Iterable

from appxf_private.storage import CompactSerializer, Storage, LocalStorage

class AppxfSecurityException(Exception):
    ''' General security related errors. '''

class AppxfSecuritySignatureError(Exception):
    ''' Signature verification failed. '''
    def __init__(self, msg='Signature verification failed', *args, **kwargs):
        super().__init__(msg, *args, **kwargs)

def _get_default_key_dict():
    return {
        'version': 1,
        'symmetric_key': b'',
        'signing_pub_key': b'',
        'signing_priv_key': b'',
        'encryption_pub_key': b'',
        'encryption_priv_key': b'',
    }


class Security():
    '''Maintaining consistent encryption.

    This class defines the security algorithms used and will hold the
    secret_key's
    '''

    # TODO: allowing a path as storage would be nice such that users do not
    # have to deal with LocalStorage when needing a Security object.
    def __init__(self,
                 salt: str,
                 storage: Storage | str | None = None,
                 **kwargs):
        '''Get security context.

        The salt is used during password handling. It is a measure against
        rainbow table attacks. Any string will do it.

        If no storage is provided, a LocalStorage for the files system at
        ./data/security/keys is used. The keys will be encrypted by a key
        derived from the password.
        '''
        if storage is None:
            storage = LocalStorage(
                file='keys', path='./data/security')
        elif isinstance(storage, str):
            storage = LocalStorage.get(
                file='keys', path=storage)

        super().__init__(**kwargs)
        self._salt = salt
        self._storage = storage
        self._derived_key = b''
        self._key_dict = _get_default_key_dict()

    def _write_keys(self):
        '''Write key_dict to encrypted file

        Encryption is based on user's password (derived key)
        '''
        # dump data
        data = pickle.dumps(self._key_dict)
        # write file
        self._storage.store_raw(
            self._encrypt_to_bytes(self._derived_key, data))

    def _verify_version(self):
        ''' Verify correct version

        This code might catch later version adaptions.
        '''
        if 'version' not in self._key_dict.keys():
            raise AppxfSecurityException(
                'Not an APPXF security file: no version information')
        if self._key_dict['version'] != 1:
            raise AppxfSecurityException(
                f'Keys stored in version {self._key_dict["version"]}, '
                f'expected is version 1')

    def _load_keys(self):
        '''Read key_dict from encrypted file

        Encryption is based on user's password (derived key)
        '''
        data_encrypted = self._storage.load_raw()
        data = self._decrypt_from_bytes(self._derived_key, data_encrypted)
        self._key_dict = pickle.loads(data)
        self._verify_version()

    def is_user_initialized(self):
        '''Check if user secret key is initialized.

        If this returns false, you need to get a password to provide to
        security.init_user(). Recommended is using an APPXF provided user
        interface.
        '''
        return self._storage.exists()

    def is_user_unlocked(self):
        '''Return if user security context is unlocked.

        If this returns true, encrypt_to_file and decrypt_to_file can be used.
        Use Security.unlock_user() directly or an APPXF provided user interface.
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
            raise AppxfSecurityException('Keys are already initialized.')
        self._derived_key = self._derive_key(password)
        self._key_dict['symmetric_key'] = self._generate_key()
        self._write_keys()

    def unlock_user(self, password):
        '''Unlock encrypt/decrypt for user context by password.

        Loads the user's secret key. See init_user() on how it is stored. If
        the key is not correct, the underlying algorihms throws an exception
        which should be cought to handle wrong passwords.
        '''
        if not self.is_user_initialized():
            raise AppxfSecurityException(
                'User is not initialized. Run init_user().')
        self._derived_key = self._derive_key(password)
        self._load_keys()

    def _get_symmetric_key(self):
        if not self.is_user_unlocked():
            raise AppxfSecurityException(
                'Trying to access symmetric keys before '
                'succeeding with unlock_user()')
        return self._key_dict['symmetric_key']

    def encrypt_to_bytes(self, data: bytes) -> bytes:
        ''' Encrypt data bytes

        The private symmetric key is used to encrypted bytes.
        file -- path of the file as string, list of strings is also possible
            to avoid caller using os.path() to join them.
        '''
        return self._encrypt_to_bytes(self._get_symmetric_key(), data)

    @classmethod
    def _encrypt_to_bytes(cls, key: bytes, data: bytes) -> bytes:
        return Fernet(key).encrypt(data)


    def decrypt_from_bytes(self, data: bytes) -> bytes:
        ''' Decrypt from data bytes

        Decrypts data bytes based on the symmetric key.
        '''
        return self._decrypt_from_bytes(self._get_symmetric_key(), data)

    @classmethod
    def _decrypt_from_bytes(cls, key: bytes, data: bytes) -> bytes:
        # Note that Fernet will also validate the data on decryption. If the
        # algorithm is changed, it needs to be ensured that the decryption is
        # validated before returning it back to the caller (like using a hash
        # on the data)
        return Fernet(key).decrypt(data)

    def get_signing_public_key(self) -> bytes:
        ''' Get public key to verify signatures.

        Note that the signing public key remains private to the security
        module and only sign() is exposed.
        '''
        if not self.is_user_unlocked():
            raise AppxfSecurityException(
                'Trying to access public key before '
                'succeeding with unlock_user()')
        self._ensure_signing_keys_exist()
        return self._key_dict['signing_pub_key']

    def get_encryption_public_key(self) -> bytes:
        ''' Get public key to encrypt data for this user

        Note that the private keys for decryption remains private to the
        security module and only hybrid_decrypt() is exposed.
        '''
        if not self.is_user_unlocked():
            raise AppxfSecurityException(
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
            raise AppxfSecurityException(
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
            raise AppxfSecurityException(
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

    @classmethod
    def _serialize_public_key(cls, key: rsa.RSAPublicKey) -> bytes:
        return key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo)
        # Note: In a minor test, PEM encoding took 426 bytes. DER encoding took
        # 264 bytes. Key size is 2048 bit or 256 byte.

    @classmethod
    def _deserialize_public_key(cls, key_bytes: bytes) -> rsa.RSAPublicKey:
        # key = serialization.load_pem_public_key(key_bytes)
        key = serialization.load_der_public_key(key_bytes)
        if not isinstance(key, rsa.RSAPublicKey):
            raise AppxfSecurityException(
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
            raise AppxfSecurityException(
                f'Unexpected key class {key.__class__.__name__}. '
                f'Expected RSAPrivateKey.')
        return key

    def sign(self, data: bytes) -> bytes:
        '''Sign data bytes

        The data is signed with the private signing key. Others typically check
        the signature the public verification keys stored in the user registry.

        Keyword arguments:
        data -- the to be signed data
        '''
        self._ensure_signing_keys_exist()
        private_key = Security._deserialize_private_key(
            self._key_dict['signing_priv_key'])

        return private_key.sign(
            data,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                        ),
            hashes.SHA256())

    @classmethod
    def verify_signature(cls, data, signature, public_key_bytes: bytes) -> bool:
        ''' Verify signature and return boolean outcome

        If you need to verify your own signature, you need to call:
        verify_signature(data, signature, security.get_signing_public_key())

        Keyword arguments:
        data -- the data which was signed
        signature -- the signature
        public_key_bytes -- public key {bytes} to be used for verification
        '''
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

    @classmethod
    def hybrid_encrypt(cls,
                       data: bytes,
                       public_keys: Iterable[bytes] | dict[Any, bytes] | None = None,
                       ) -> tuple[bytes, dict[Any, bytes]]:
        ''' Hybrid encryption returning encrypted data and key blob dict

        The data will be encrypted with a generated symmetric key. This
        password will be encrypted with the provided public keys to result in
        key blobs. The key blobs are returned in a dictionary that is indexed
        by either the public keys (if public keys are provided by a list) or by
        the keys used when public keys are provided via a dictionary.

        Keyword arguments:
        data -- the data to encrypt
        public_key_list -- either a list of public keys OR a dictionary of
            public keys where the dictionary keys will be used to index the
            key blobs

        Returns: a tuple of the encrypted bytes and a dictionary mapping the
            dict keys or public keys to the key blobs.
        '''
        symmetric_key = cls._generate_key()
        data_encrypted = cls._encrypt_to_bytes(symmetric_key, data)

        key_blob_dict = {}
        if isinstance(public_keys, dict):
            for label, key in public_keys.items():
                key_encrypted = cls._encrypt_with_public_key_to_bytes(
                    symmetric_key, key)
                key_blob_dict[label] = key_encrypted
        else:
            # ensure unique list of public keys:
            public_keys = set(*public_keys)
            for key in public_keys:
                key_encrypted = cls._encrypt_with_public_key_to_bytes(
                    symmetric_key, key)
                key_blob_dict[key] = key_encrypted

        return data_encrypted, key_blob_dict

    def hybrid_decrypt(
            self,
            data: bytes,
            key_blob_dict: dict[Any, bytes],
            blob_identifier: Any = None
        ) -> bytes:
        ''' Hybrid decryption returning decrypted data

        PRECONDITION: From hybrid_encrypt(), you obtain a dictionary of key
        blobs. The correct key blob for THIS call must be identified from the
        caller. It is either the one matching your get_public_encryption_key()
        OR it is the one matching whatever keys you used for a dictionary of
        public keys.

        Your private assymetric encyption key will be used to decrypt the
        symmetric key from the key_blob. Afterwards, the data will be decrypted
        by this symmeric key.
        '''
        if blob_identifier is None:
            blob_identifier = self.get_encryption_public_key()
        if blob_identifier not in key_blob_dict:
            raise AppxfSecurityException(
                f'Key blobs do not include one for identity: {blob_identifier}. '
                f'Available are: {list(key_blob_dict.keys())}')
        key_blob = key_blob_dict[blob_identifier]

        symmetric_key = self._decrypt_with_private_key_from_byes(
            key_blob)

        return self._decrypt_from_bytes(symmetric_key, data)

    # TODO #42: Interfaces are inconsistent between hybrid_encrypt() above and
    # hybrid_signed_encrypt() below. The story is that hybrid_encrypt() was
    # designed for SecureSharedStorage which is using meta files to store
    # encryption and signature details. The functions below are designed to
    # support registration request/response as well as manual configuration
    # updates in registry. Having both interfaces increases overall code
    # complexity and one should be removed. Most important arguments:
    #
    #  * having a meta file for SecureSharedStorage allows to update key_blobs
    #    without re-writing the original data which could be large.
    #  * having a meta file makes the job for file snychronization more
    #    complicated since removed passwords may imply removing the data from a
    #    user location.
    #  * having a byte stream approach (bytes in, bytes out) makes the overall
    #    file handling concept more simple and only the sync and original meta
    #    file remains.
    #
    # As it currently looks like, the decision is mainly influenced by the
    # final synchronization mechanism (meta files) AND weighting "rewriting
    # (large) data files" against "less complexity in SharedStorage file
    # handling"
    #
    # All this goes along with switching to "signing before encryption".

    def hybrid_signed_encrypt(
            self,
            data: bytes,
            public_keys: Iterable[bytes] | dict[Any, bytes] | None = None,
        ) -> bytes:
        ''' Hybrid encryption with signed data

        Functions like hybrid_encrypt() but applies signature on data and packs
        everything to bytes.
        '''
        # sign and pack into signed data
        signature = self.sign(data)
        signed_data = {
            'data': data,
            'author': self.get_signing_public_key(),
            'signature': signature
        }
        signed_data_bytes = CompactSerializer.serialize(signed_data)

        # encrypt signed data
        encrypted_data_bytes, key_blob_dict = self.hybrid_encrypt(
            data = signed_data_bytes,
            public_keys=public_keys)
        return CompactSerializer.serialize({
            'data': encrypted_data_bytes,
            'key_blob_dict': key_blob_dict})

    def hybrid_signed_decrypt(
            self,
            data: bytes,
            blob_identifier: Any = None
        ) -> tuple[bytes, bytes]:
        '''Hybrid decryption with signature verification

        Functions like hybrid_decrypt() while it expects bytes generated from
        hybrid_signed_encryption() for which it verifies the data based on the
        the signature against the INCLUDED public key.

        IMPORTANT to ensure AUTHENTICITY: The CALLER HAS TO VERIFY the PUBLIC
        KEY being authorized to provide the data.

        Raises AppxfSecuritySignatureError if signature verification fails.
        This exception should be caught, adding information on the context of
        the call.

        Returns: a tuple of the decrypted data and the author's public key
        '''
        # unpack encrypted and signed data:
        encrypted_data = CompactSerializer.deserialize(data)
        encrypted_data_bytes = encrypted_data['data']
        key_blob_dict = encrypted_data['key_blob_dict']

        # decrypt to signed data:
        signed_data_bytes = self.hybrid_decrypt(
            encrypted_data_bytes, key_blob_dict, blob_identifier)
        signed_data: dict = CompactSerializer.deserialize(signed_data_bytes)

        # unpack signed data and verify signature:
        data = signed_data['data']
        author_pub_key = signed_data['author']
        signature = signed_data['signature']
        if not Security.verify_signature(
                data, signature, author_pub_key):
            raise AppxfSecuritySignatureError()

        return data, author_pub_key

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

    @classmethod
    def _generate_key(cls):
        '''Generate key to encrypt/decrypt synchronously.

        As of now, this just forwards to Fernet's generate_key(). See here:
        https://cryptography.io/en/latest/fernet/.
        '''
        return Fernet.generate_key()
