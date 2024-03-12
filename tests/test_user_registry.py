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
    #admin_registry = RegistrationRequest.from_request(request_bytes)
    #assert admin_registry._data['user_data'] == app_user.config.get('USER')




    # TODO: NEXT THING TO DO: Start using registry and initialize this as
    # admin. Then, embedd in application startup sequence. Then, things can
    # follow.




    # admin would now inspect the user data of the reuquest, likely in a GUI.
    # Most important check: does the user already exist and does it need to be
    # mapped to an existing ID?
    #
    # admin adding to user DB
    #user_id = env['user database'].add_new(
    #    validation_key=admin_registry.signing_key,
    #    encryption_key=admin_registry.encryption_key)
    #assert user_id == 0
    #assert env['user database'].has_role(user_id, 'user')
    #assert not env['user database'].has_role(user_id, 'admin')
    #assert env['user database'].get_validation_key(user_id) == env['security'].get_signing_public_key()
    #assert env['user database'].get_encryption_key(user_id) == env['security'].get_encryption_public_key()
    # admin sending back user_id and config data sections
    #admin_response = RegistrationResponse.new(user_id, {'TEST': env['config'].get('TEST')})
    #response_bytes = admin_response.get_response_bytes()

    # user getting response
    #response = RegistrationResponse.from_response_bytes(response_bytes)
    #assert response.user_id == user_id
    #assert response.config_sections['TEST']['test'] == env['config'].get('TEST', 'test')

    # The steps above were broken by trying to initialize the user_db and
    # seeing the initialization potentially beeing inconsistent to security
    # expectations: init needs to derive a secured storage method from storage
    # location (manually). Open questions to resolve:
    #   * When user get's it's user ID - how is this stored? The user_db would
    #     not contain this.
    #   * How is user information shared among other users (including admin who
    #     want's t know full details)?
    # Interesting insights:
    #   * Users may distribute their USER config to admins
    #   * Admins are responsible for the USER_DB and likely for redistribution
    #     of user information
    #   * Redistribution of user information is likely based on roles, like
    #     "admins know all users", "list responsible knows depot responsibles"
    # We do not want to write different USER_DB versions for each user.
    # Likewise, we do not want to write an information file for each user that
    # is encrypted for lot's of users. However, we want to use the default
    # shared file sync mechanism. This leaves:
    #   * Write bulks of user data information per role.
    # Consequences:
    #   * One file per ROLE (not per USER)
    #   * User information may be contained in multiple ROLE files.
    # If user information size is SIZE_UI and size of encryption data is SIZE_KEY, the
    # total size is:
    #   * For one file, each user: USERS * (SIZE_UI + AVG_USER_IN_ROLE * SIZE_KEY)
    #   * For one file, each group: ROLES * (AVG_USER_IN_ROLE * SIZE_UI + AVG_USER_IN_ROLE * SIZE_KEY)
    #   * Assuming AVG_USER_IN_ROLE ~ USERS/ROLES
    #       * First: USERS * SIZE_UI + USERS^2/ROLES * SIZE_KEY
    #           USERS * SIZE_UI >> guaranteed
    #           USERS^2/ROLES * SIZE_KEY >> certainly a problem
    #       * Second: USERS * SIZE_UI + USERS * SIZE_KEY
    #           USERS * SIZE_UI >> not correct admin will know all, depot
    #             responsibles will be known by most roles. Worst case:
    #             each role knows all users: USERS * ROLES * SIZE_UI.
    #           USERS * SIZE_KEY >> also not correct since users may know
    #             multiple roles input. Worst case here is, again:
    #             USERS * ROLES * SIZE_UI
    #       * Second corrected but worst case:
    #             ROLES * USERS * (SIZE_UI + SIZE_KEY)
    #
    # Number examples, assuming email (16 bytes) plus name (20 bytes) rounded
    # up to 50 bytes for SIZE_UI. And an encrpted key blob with 256 bytes.
    #   * 10 USERS shared with all users (worst case): 10*50 + 10*10*256 = 26k
    #   * 10 USERS shared with 5 ROLES: 10*5*50 + 10*5*256 = 15k
    #
    #   * 20 USERS shared with all users (worst case): 103k
    #   * 20 USERS shared with 5 roles: 31k

# TODO: test cycle with registration for an already existing user.