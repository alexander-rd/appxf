''' Tests for class Security in security module

Rely on Security helpers from tests._fixtures.appxf_objects to avoid spinning
up the full application harness. Paths are isolated per test via the sandbox
fixture.
'''

import os
import pytest
from kiss_cf.security import SecurePrivateStorage, Security
from kiss_cf.storage import LocalStorage, Storage

from tests._fixtures import test_sandbox, appxf_objects

TEST_PASSWORD = 'test-registry-password'

# TODO UPGRADE: store bytecode for version 1 files and add test cases that
# those files can still be loaded. Well, consider not adding garbage into
# current files - a file verisoning is only then required if APPXF needs to
# start distinguishing versions. Also, then, compatibilty tests are missing.

# TODO LATER: test case for failing loading (use a file encrypted from a different
# user with different password)

@pytest.fixture(autouse=True)
def test_setup(request):
    Storage.reset()
    test_sandbox.init_test_sandbox_from_fixture(request, cleanup=True)

@pytest.fixture()
def sandbox_path(request):
    return test_sandbox.init_test_sandbox_from_fixture(request, cleanup=True)

def get_data_storage_factory(root_path, sec: Security):
    data_path = os.path.join(root_path, 'data')
    return SecurePrivateStorage.get_factory(
        base_storage_factory=LocalStorage.get_factory(path=data_path),
        security=sec)


# Uninitialized test location should indicate as not user initialized.
def test_security_uninitialized(sandbox_path):
    sec = appxf_objects.get_security(sandbox_path)
    assert not sec.is_user_initialized()
    # also not unlocked
    assert not sec.is_user_unlocked()

# Initialize a user (write file and authenticate)
def test_security_init(sandbox_path):
    sec = appxf_objects.get_security(sandbox_path)
    sec.init_user(TEST_PASSWORD)
    # file should now be present:
    assert os.path.exists(os.path.join(sandbox_path, 'user'))
    # and user should be initialized:
    assert sec.is_user_initialized()
    # user is unlocked after initialization
    assert sec.is_user_unlocked()
    # unlock (should not throw error) and check
    sec.unlock_user(TEST_PASSWORD)
    assert sec.is_user_unlocked()

# Unlock a user
def test_security_unlock(sandbox_path):
    # prepare initialized user on disk
    sec = appxf_objects.get_security_initialized(sandbox_path, TEST_PASSWORD)
    assert sec.is_user_initialized()
    assert not sec.is_user_unlocked()
    # unlock:
    sec.unlock_user(TEST_PASSWORD)
    assert sec.is_user_unlocked()

# Store and load
def test_security_store_load(sandbox_path):
    sec = appxf_objects.get_security_unlocked(sandbox_path, TEST_PASSWORD)
    data = b'123456ABC!'
    storage = get_data_storage_factory(sandbox_path, sec)('some_file')
    # store
    storage.store(data)
    # load
    data_loaded = storage.load()
    assert data == data_loaded
    # try to read from new security object
    sec = appxf_objects.get_security(sandbox_path)
    assert not sec.is_user_unlocked()
    sec.unlock_user(TEST_PASSWORD)
    # Note: need to delete prior storage object. Storage locations do not allow
    # two methods covering the same file.
    del storage
    storage = get_data_storage_factory(sandbox_path, sec)('some_file')
    data_loaded = storage.load()
    assert data == data_loaded

# TODO UPGRADE: test case to get public keys and always get same keys again after
# reloading security material.

# TODO UPGRADE: manual verification with cryptography algorithms. (1) Let
# implementation sign and manual verify. (2) Manual sign and let implementation
# verify.

def test_security_store_assymetric_keys(sandbox_path):
    sec = appxf_objects.get_security_unlocked(sandbox_path, TEST_PASSWORD)

    # get public keys. Note that they might be generated on first time
    # accessing them.
    signing_public_key = sec.get_signing_public_key()
    encryp_public_key = sec.get_encryption_public_key()

    # Take new security, unlock and check agains the ones above. Note that the
    # data already needs to be stored before tear down of the security above.
    # The use case is quite unusual and not supported: having two Security
    # objects accessing the same data.
    security = appxf_objects.get_security(sandbox_path)
    security.unlock_user(TEST_PASSWORD)
    assert signing_public_key == security.get_signing_public_key()
    assert encryp_public_key == security.get_encryption_public_key()

# Verify cycle
def test_security_sign_verify(sandbox_path):
    sec = appxf_objects.get_security_unlocked(sandbox_path, TEST_PASSWORD)

    data = b'To Be Signed'
    signature = sec.sign(data)
    signatureFalse = sec.sign(data + b'x')

    assert sec.verify_signature(data, signature, sec.get_signing_public_key())
    # verificytion on false signature
    assert not sec.verify_signature(data, signatureFalse, sec.get_signing_public_key())
    # verification on false public key (using encryption public key)
    assert not sec.verify_signature(data, signature, sec.get_encryption_public_key())

# Hybrid encrypt/decrypt cycle:
def test_security_hybrid_encrypt_decrypt(sandbox_path):
    sec = appxf_objects.get_security_unlocked(sandbox_path, TEST_PASSWORD)

    data = b'To be encrypted'
    data_encrpted, key_blob_map = sec.hybrid_encrypt(
        data, {1: sec.get_encryption_public_key()})

    data_decrypted = sec.hybrid_decrypt(
        data_encrpted, key_blob_map, blob_identifier=1)

    assert data != data_encrpted
    assert data == data_decrypted
