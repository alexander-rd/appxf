import os
import pytest
import shutil

from kiss_cf.security import Security, LocalSecuredStorageMethod
from kiss_cf.storage import LocalStorageLocation

# TODO UPGRADE: store bytecode for version 1 files and add test cases that those files
# can still be loaded.

# TODO LATER: test case for failing loading (use a file encrypted from a different
# user with different password)

class Environment():
    def __init__(self):
        self.dir = './testing'
        self.key_file = './testing/USER.keys'
        self.data_file = 'some_data'
        self.password = 'password'
        self.sec = Security(
            salt='test',
            file=self.key_file)
        self.location = LocalStorageLocation(self.dir)
        self.storage_method = self.location.get_storage_method(self.data_file)

@pytest.fixture
def empty_test_location():
    env = Environment()
    if os.path.exists(env.dir):
        shutil.rmtree(env.dir)
    yield env
    if os.path.exists(env.dir):
        shutil.rmtree(env.dir)
    del env

@pytest.fixture
def initialized_test_location(empty_test_location):
    env = empty_test_location
    env.sec.init_user(env.password)
    # Start with fresh security object. The one before was already used to
    # initialize the user.
    env.sec = Security(salt='test', file=env.key_file)
    yield env
    # no cleanup: cleanup from empty_test_location

# Uninitialized test location should indicate as not user initialized.
def test_uninitialized_location(empty_test_location):
    env = empty_test_location
    assert env.sec.is_user_initialized() == False
    # also not unlocked
    assert env.sec.is_user_unlocked() == False

# Initialize a user (write file and authenticate)
def test_user_init(empty_test_location):
    env = empty_test_location
    env.sec.init_user('some_password')
    # file should now be present:
    assert os.path.exists(env.key_file) == True
    # and user should be initialized:
    assert env.sec.is_user_initialized() == True
    # user is still not unlocked
    assert env.sec.is_user_unlocked() == True
    # unlock (should not throw error) and check
    env.sec.unlock_user('some_password')
    assert env.sec.is_user_unlocked() == True

# Unlock a user
def test_unlock_user(initialized_test_location):
    env = initialized_test_location
    assert env.sec.is_user_initialized() == True
    assert env.sec.is_user_unlocked() == False
    # unlock:
    env.sec.unlock_user(env.password)
    assert env.sec.is_user_unlocked() == True

# Store and load
def test_store_load(initialized_test_location):
    env = initialized_test_location
    env.sec.unlock_user(env.password)

    data = b'123456ABC!'
    storage = LocalSecuredStorageMethod(env.storage_method, env.sec)

    # store
    storage.store(data)
    # load
    data_loaded = storage.load()
    assert data == data_loaded

    # try to read from new security
    env = Environment()
    assert env.sec.is_user_unlocked() is False
    env.sec.unlock_user(env.password)
    storage = LocalSecuredStorageMethod(env.storage_method, env.sec)
    data_loaded = storage.load()
    assert data == data_loaded

# Verify cycle
def test_sign_verify(initialized_test_location):
    env = initialized_test_location
    env.sec.unlock_user(env.password)

    data = b'To Be Signed'
    signature = env.sec.sign(data)
    signatureFalse = env.sec.sign(data + b'x')
    #assert env.sec.verify(data, signatureFalse) == False
    #assert env.sec.verify(data, signature) == True