''' Tests for class Security in security module

Test cases use the security object from the application mock to re-use path
setup within the application.
'''

import os
import pytest
import shutil

from kiss_cf.security import Security, SecurePrivateStorageMethod
from kiss_cf.storage import LocalStorageLocation

# Indirectly used environments still need to be importet
from tests.fixtures.env_base import env_base
from tests.fixtures.application import app_fresh_user, app_initialized_user, app_unlocked_user
from tests.fixtures.application_mock import ApplicationMock


# TODO UPGRADE: Is the "user" in interface name "is_user_unlocked" necessary?
# Same for "user.keys" Class implementation should be checked for any usage of
# "user"

# TODO UPGRADE: store bytecode for version 1 files and add test cases that those files
# can still be loaded.

# TODO LATER: test case for failing loading (use a file encrypted from a different
# user with different password)

# Uninitialized test location should indicate as not user initialized.
def test_security_uninitialized(app_fresh_user):
    app: ApplicationMock = app_fresh_user['app_user']
    assert not app.security.is_user_initialized()
    # also not unlocked
    assert not app.security.is_user_unlocked()

# Initialize a user (write file and authenticate)
def test_security_init(app_fresh_user):
    app: ApplicationMock = app_fresh_user['app_user']
    app.security.init_user('some_password')
    # file should now be present:
    assert os.path.exists(app.file_sec)
    # and user should be initialized:
    assert app.security.is_user_initialized()
    # user is still not unlocked
    assert app.security.is_user_unlocked()
    # unlock (should not throw error) and check
    app.security.unlock_user('some_password')
    assert app.security.is_user_unlocked()

# Unlock a user
def test_security_unlock(app_initialized_user):
    app: ApplicationMock = app_initialized_user['app_user']
    assert app.security.is_user_initialized()
    assert not app.security.is_user_unlocked()
    # unlock:
    app.security.unlock_user(app.password)
    assert app.security.is_user_unlocked()

# Store and load
def test_security_store_load(app_unlocked_user):
    app: ApplicationMock = app_unlocked_user['app_user']
    data = b'123456ABC!'
    storage = SecurePrivateStorageMethod(
        base_method=app.location_data.get_storage_method('some_file'),
        security=app.security)
    # store
    storage.store(data)
    # load
    data_loaded = storage.load()
    assert data == data_loaded
    # try to read from new security
    sec = Security(salt = app.salt,
                   file = app.file_sec)
    assert not sec.is_user_unlocked()
    sec.unlock_user(app.password)
    # Note: need to delete prior storage object. Storage locations do not allow
    # two methods covering the same file.
    del storage
    storage = SecurePrivateStorageMethod(
        base_method=app.location_data.get_storage_method('some_file'),
        security=app.security)
    data_loaded = storage.load()
    assert data == data_loaded

# TODO UPGRADE: test case to get public keys and always get same keys again after
# reloading security material.

# TODO UPGRADE: manual verification with cryptography algorithms. (1) Let
# implementation sign and manual verify. (2) Manual sign and let implementation
# verify.

def test_security_store_assymetric_keys(app_unlocked_user):
    app: ApplicationMock = app_unlocked_user['app_user']

    # get public keys. Note that they might be generated on first time
    # accessing them.
    signing_public_key = app.security.get_signing_public_key()
    encryp_public_key = app.security.get_encryption_public_key()

    # Take new security, unlock and check agains the ones above. Note that the
    # data already needs to be stored before tear down of the security above.
    # The use case is quite unusual and not supported: having two Security
    # objects accessing the same data.
    security = Security(app.salt, app.file_sec)
    security.unlock_user(app.password)
    assert signing_public_key == security.get_signing_public_key()
    assert encryp_public_key == security.get_encryption_public_key()

# Verify cycle
def test_security_sign_verify(app_unlocked_user):
    app: ApplicationMock = app_unlocked_user['app_user']

    data = b'To Be Signed'
    signature = app.security.sign(data)
    signatureFalse = app.security.sign(data + b'x')

    assert app.security.verify(data, signature)
    assert not app.security.verify(data, signatureFalse)

# Hybrid encrypt/decrypt cycle:
def test_security_hybrid_encrypt_decrypt(app_unlocked_user):
    app: ApplicationMock = app_unlocked_user['app_user']

    data = b'To be encrypted'
    data_encrpted, key_map = app.security.hybrid_encrypt(data)

    data_decrypted = app.security.hybrid_decrypt(data_encrpted, key_map)

    assert data != data_encrpted
    assert data == data_decrypted
