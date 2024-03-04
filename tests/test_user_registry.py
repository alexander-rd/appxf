import os
import pytest
import shutil

from kiss_cf.config import Config
from kiss_cf.storage.local import LocalStorageLocation
from kiss_cf.security import Security, UserDatabase, RegistrationRequest, RegistrationResponse

from tests.fixtures.env_base import env_base
from tests.fixtures.env_storage import env_test_directory

# define default context/environment
@pytest.fixture
def env_uninitialized(env_test_directory):
    env = env_test_directory
    # we will always need a location
    env['location'] = LocalStorageLocation(path=env['dir'])

    # we need a configuration
    config = Config(security = None, storage_dir=env['dir'])
    # we need to add some default user data
    env['default_user_email'] = 'default@null.void'
    config.add_option('USER', 'email', value=env['default_user_email'])
    env['config'] = config
    # we need to add a default section for testing
    config.add_option('TEST', 'test', value='42')

    # we need an initialized/unlocked security object
    env['salt'] = 'test_salt'
    env['password'] = 'test_password'
    env['obj key file'] = os.path.join(env['dir'], 'user.key')
    env['security'] = Security(salt=env['salt'],
                          file=env['obj key file'])
    env['security'].init_user(env['password'])
    assert env['security'].is_user_unlocked()

    # we need a use database
    env['user database'] = UserDatabase(env['location'].get_storage_method('user_db'))

    return env

def test_user_registry_basic_cycle(env_uninitialized):
    env = env_uninitialized

    # registration request
    registry = RegistrationRequest.new(
        user_data=env['config'].get('USER'),
        security=env['security'])
    request_bytes = registry.get_request_bytes()

    # admin registration handling
    admin_registry = RegistrationRequest.from_request(request_bytes)
    assert admin_registry._data['user_data'] == env['config'].get('USER')
    # admin would now inspect the user data of the reuquest, likely in a GUI.
    # Most important check: does the user already exist and does it need to be
    # mapped to an existing ID?
    #
    # admin adding to user DB
    user_id = env['user database'].add_new(
        validation_key=admin_registry.signing_key,
        encryption_key=admin_registry.encryption_key)
    assert user_id == 0
    assert env['user database'].has_role(user_id, 'user')
    assert not env['user database'].has_role(user_id, 'admin')
    assert env['user database'].get_validation_key(user_id) == env['security'].get_signing_public_key()
    assert env['user database'].get_encryption_key(user_id) == env['security'].get_encryption_public_key()
    # admin sending back user_id and config data sections
    admin_response = RegistrationResponse.new(user_id, {'TEST': env['config'].get('TEST')})
    response_bytes = admin_response.get_response_bytes()

    # user getting response
    response = RegistrationResponse.from_response_bytes(response_bytes)
    assert response.user_id == user_id
    assert response.config_sections['TEST']['test'] == env['config'].get('TEST', 'test')

# TODO: test cycle with registration for an already existing user.