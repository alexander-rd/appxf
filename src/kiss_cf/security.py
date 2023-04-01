'''Define security algorithms.'''

import os.path

# generate crypt key from password
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
# synchronous encryption:
from cryptography.fernet import Fernet


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
        used to persist the secret key on the file systen. The password is not
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

    def decrypt_from_file(self, file):
        if not self.is_user_unlocked():
            raise Exception(
                'Trying to decrypt {file} before '
                'succeeding with unlock_user()')
        return self.__decrypt_from_file(self._user_secret_key, file)

    def __decrypt_from_file(self, key, file):
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
