''' Tests for class Security in security module

Test cases use the security object from the application mock to re-use path
setup within the application.
'''

import os
import pytest
from kiss_cf.security import Security

from tests._fixtures import application, test_sandbox


# TODO UPGRADE: Is the "user" in interface name "is_user_unlocked" necessary?
# Same for "user.keys" Class implementation should be checked for any usage of
# "user"

# TODO UPGRADE: store bytecode for version 1 files and add test cases that those files
# can still be loaded.

# TODO LATER: test case for failing loading (use a file encrypted from a different
# user with different password)

# TODO LATER: "fresh" and "initialized" user folders appear for each test case.
# I guess this is not intended and they are actually there to be copied (and
# not re-created) each time. -- ALSO -- If those folders are for later version
# testing (reloading application data after implementation changes).. ..then
# there is probably more to do.

@pytest.fixture(autouse=True)
def test_setup(request):
    test_sandbox.init_test_sandbox_from_fixture(request, cleanup=True)


# Uninitialized test location should indicate as not user initialized.
def test_app_10_security_uninitialized(request):
    app = application.get_fresh_application(request)
    assert not app.security.is_user_initialized()
    # also not unlocked
    assert not app.security.is_user_unlocked()

# Initialize a user (write file and authenticate)
def test_app_10_security_init(request):
    app = application.get_fresh_application(request)
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
def test_app_10_security_unlock(request):
    app = application.get_application_login_initialized(request)
    assert app.security.is_user_initialized()
    assert not app.security.is_user_unlocked()
    # unlock:
    app.security.unlock_user(app.password)
    assert app.security.is_user_unlocked()

# Store and load
def test_app_10_security_store_load(request):
    app = application.get_unlocked_application(request)
    data = b'123456ABC!'
    storage = app.storagef_data('some_file')
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
    storage = app.storagef_data('some_file')
    data_loaded = storage.load()
    assert data == data_loaded

# TODO UPGRADE: test case to get public keys and always get same keys again after
# reloading security material.

# TODO UPGRADE: manual verification with cryptography algorithms. (1) Let
# implementation sign and manual verify. (2) Manual sign and let implementation
# verify.

def test_app_10_security_store_assymetric_keys(request):
    app = application.get_unlocked_application(request)

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
def test_app_10_security_sign_verify(request):
    app = application.get_unlocked_application(request)

    data = b'To Be Signed'
    signature = app.security.sign(data)
    signatureFalse = app.security.sign(data + b'x')

    assert app.security.verify(data, signature)
    assert not app.security.verify(data, signatureFalse)

# Hybrid encrypt/decrypt cycle:
def test_app_10_security_hybrid_encrypt_decrypt(request):
    app = application.get_unlocked_application(request)

    data = b'To be encrypted'
    data_encrpted, key_map = app.security.hybrid_encrypt(data)

    data_decrypted = app.security.hybrid_decrypt(data_encrpted, key_map)

    assert data != data_encrpted
    assert data == data_decrypted

# TODO: Those two test cases belong in the unit testing context:
#  * test_app_10_security_sign_verify
#  * test_app_10_security_hybrid_encrypt_decrypt
#
# Currently, unit tests are probably covering this via the BDD sync test cases
# which should be on APP level.
