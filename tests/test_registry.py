import pytest

from tests.fixtures.application_mock import ApplicationMock
from tests.fixtures.env_base import env_base
from tests.fixtures.application import app_unlocked_user_admin_pair

def test_registry_basic_cycle(app_unlocked_user_admin_pair):
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