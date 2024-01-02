import os
import pytest
import shutil

from kiss_cf.security import Security, SecurePrivateStorageMethod
from kiss_cf.storage import LocalStorageLocation

from tests.fixtures.env_base import env_base
from tests.fixtures.env_storage import env_test_directory

# define default context/environment
@pytest.fixture
def env_uninitialized(env_test_directory):
    env = env_test_directory
    # we will always need a location
    env['location'] = LocalStorageLocation(path=env['dir'])
    # there will be a default salt and password
    env['salt'] = 'test_salt'
    env['password'] = 'test_password'
    # and a pre-setup security object
    env['obj key file'] = os.path.join(env['dir'], 'user.key')
    env['security'] = Security(salt=env['salt'],
                          file=env['obj key file'])
    return env

@pytest.fixture
def env_initialized(env_uninitialized):
    env = env_uninitialized
    env['security'].init_user(env['password'])
    # Start with fresh security object. The one before was already used to
    # initialize the user.
    env['security'] = Security(salt=env['salt'],
                          file=env['obj key file'])
    # sanity checks
    assert os.path.exists(env['obj key file'])
    assert env['security'].is_user_initialized()

    return env

@pytest.fixture
def env_unlocked(env_initialized):
    env = env_initialized
    env['security'].unlock_user(env['password'])
    # sanity checks
    assert env['security'].is_user_unlocked()

    return env

# TODO UPGRADE: Is the "user" in interface name "is_user_unlocked" necessary?
# Same for "user.keys" Class implementation should be checked for any usage of
# "user"

# TODO UPGRADE: store bytecode for version 1 files and add test cases that those files
# can still be loaded.

# TODO LATER: test case for failing loading (use a file encrypted from a different
# user with different password)

# Uninitialized test location should indicate as not user initialized.
def test_security_uninitialized(env_uninitialized):
    env = env_uninitialized
    assert not env['security'].is_user_initialized()
    # also not unlocked
    assert not env['security'].is_user_unlocked()

# Initialize a user (write file and authenticate)
def test_security_init(env_uninitialized):
    env = env_uninitialized
    env['security'].init_user('some_password')
    # file should now be present:
    assert os.path.exists(env['obj key file'])
    # and user should be initialized:
    assert env['security'].is_user_initialized()
    # user is still not unlocked
    assert env['security'].is_user_unlocked()
    # unlock (should not throw error) and check
    env['security'].unlock_user('some_password')
    assert env['security'].is_user_unlocked()

# Unlock a user
def test_security_unlock(env_initialized):
    env = env_initialized
    assert env['security'].is_user_initialized()
    assert not env['security'].is_user_unlocked()
    # unlock:
    env['security'].unlock_user(env['password'])
    assert  env['security'].is_user_unlocked()

# Store and load
def test_security_store_load(env_unlocked):
    env = env_unlocked

    data = b'123456ABC!'
    storage = SecurePrivateStorageMethod(
        base_method=env['location'].get_storage_method('some_file'),
        security=env['security'])

    # store
    storage.store(data)
    # load
    data_loaded = storage.load()
    assert data == data_loaded

    # try to read from new security
    sec = Security(salt = env['salt'],
                   file = env['obj key file'])
    assert not sec.is_user_unlocked()
    sec.unlock_user(env['password'])
    # Note: need to delete prior storage object. Storage locations do not allow
    # two methods covering the same file.
    del storage
    storage = SecurePrivateStorageMethod(
        base_method=env['location'].get_storage_method('some_file'),
        security=env['security'])
    data_loaded = storage.load()
    assert data == data_loaded

# Verify cycle
def test_security_sign_verify(env_unlocked):
    env = env_unlocked

    data = b'To Be Signed'
    signature = env['security'].sign(data)
    signatureFalse = env['security'].sign(data + b'x')
    #assert env.sec.verify(data, signatureFalse) == False
    #assert env.sec.verify(data, signature) == True
