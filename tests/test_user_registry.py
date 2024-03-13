import os
import pytest
import shutil

from kiss_cf.config import Config
from kiss_cf.storage.local import LocalStorageLocation
from kiss_cf.security import Security
from kiss_cf.registry import UserDatabase

from tests.fixtures.application_mock import ApplicationMock
from tests.fixtures.env_base import env_base
from tests.fixtures.application import app_unlocked_user_admin_pair
#from tests.fixtures.env_storage import env_test_directory
#from tests.fixtures.application import app_unlocked_user

# define default context/environment
@pytest.fixture
def Xenv_uninitialized(env_test_directory):
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

def test_user_registry_basic_cycle(app_unlocked_user_admin_pair):
    app_user: ApplicationMock = app_unlocked_user_admin_pair['app_user']
    app_admin: ApplicationMock = app_unlocked_user_admin_pair['app_admin']

    # registration request
    request_bytes = app_user.perform_registration_get_request()

    # admin registration handling
    request = app_admin.registry.get_request_data(request_bytes)
    assert app_user.config.get('USER') == request.user_data
    # admin would now inspect the user data of the reuquest, likely in a GUI.
    # Most important check: does the user already exist and does it need to be
    # mapped to an existing ID?
    #
    # TODO: add functionality to registry to check is user may already exist
    #
    # admin adding to user DB
    user_id = app_admin.registry.add_user_from_request(request)
    assert user_id == 1
    # TODO: reconsider the interfacing. user_db appears to be hiden behind
    # registry. This makes sense but suddenly requires interface forwarding.
    # Possibly, the logic should move to registry while USER_DB is pure storage
    # handling (load/store/initialize) with direct member access. - Storable
    # dictionary??
    assert app_admin.registry._user_db.has_role(user_id, 'user')
    assert not app_admin.registry._user_db.has_role(user_id, 'admin')
    # TODO: consistency validation_key versus signing_key
    assert app_admin.registry._user_db.get_validation_key(user_id) == app_user.security.get_signing_public_key()
    assert app_admin.registry._user_db.get_encryption_key(user_id) == app_user.security.get_encryption_public_key()
    # admin sending back user_id and config data sections
    response_bytes = app_admin.registry.get_response_bytes(user_id, ['TEST'])

    # user getting response
    app_user.registry.set_response_bytes(response_bytes)
    assert app_user.registry._user_id.id == user_id
    assert app_user.config.get('TEST') == app_admin.config.get('TEST')

# TODO: test cycle with registration for an already existing user.