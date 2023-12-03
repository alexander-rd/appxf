import os
import pytest
import shutil

from kiss_cf import security

class Environment():
    def __init__(self):
        self.dir = './testing'
        self.password = 'password'
        self.sec = security.Security(
            salt='test',
            storage=self.dir)

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
    env.sec = security.Security(salt='test', storage=env.dir)
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
    assert os.path.exists(os.path.join(env.dir, 'user.key')) == True
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
    file = os.path.join(env.dir, 'test.dat')
    storage = env.sec.get_storage_method()
    storage.set_file(file)

    # store
    storage.store(data)
    # load
    data_loaded = storage.load()
    assert data == data_loaded

    # try to read from new security
    env = Environment()
    assert env.sec.is_user_unlocked() == False
    env.sec.unlock_user(env.password)
    storage = env.sec.get_storage_method()
    storage.set_file(file)
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