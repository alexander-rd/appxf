import pytest
from unittest.mock import patch

from kiss_cf.storage import Storage, CompactSerializer
from kiss_cf.registry import Registry, KissRegistryError

from tests._fixtures import appxf_objects
import tests._fixtures.test_sandbox

#! TODO: those getters should be moved into appxf_objects as functions and not
#  as fixtures

# TODO: test cases on size of registry with multiple users and roles (may be
# part of application testing)

@pytest.fixture
def fresh_registry(request):
    ''' Provide an uninitialized registry '''
    Storage.reset()
    # Usually, testing uses RAM objects (quicker)
    path = None
    # For debugging, you may want to use real files:
    path = tests._fixtures.test_sandbox.init_test_sandbox_from_fixture(request)
    print(path)
    #path = env_base['dir']
    return appxf_objects.get_fresh_registry(
        path=path,
        security=appxf_objects.get_security_unlocked(path),
        config=appxf_objects.get_dummy_config())

@pytest.fixture
def admin_initialized_registry(fresh_registry):
    ''' Provide an admin-initialized registry '''
    reg: Registry = fresh_registry
    reg.initialize_as_admin()
    return reg

@pytest.fixture
def admin_user_initialized_registry_pair(request):
    Storage.reset()
    # Usually, testing uses RAM objects (quicker)
    path = None
    # For debugging, you may want to use real files:
    path = tests._fixtures.test_sandbox.init_test_sandbox_from_fixture(request)

    Storage.switch_context('admin')
    admin_config = appxf_objects.get_dummy_user_config()
    print(f'FANCY INIT obtained config for admin: {admin_config}')
    admin_registry = appxf_objects.get_fresh_registry(
        path=path,
        security=appxf_objects.get_security_unlocked(path),
        config=admin_config,
        local_name='local_registry_admin',
        remote_name='remote_registry')
    # Note: admin and user have their own config and security objects since
    # both are not file based.
    Storage.switch_context('user')
    user_config = appxf_objects.get_dummy_user_config()
    print(f'FANCY INIT obtained config for admin: {user_config}')
    user_registry = appxf_objects.get_fresh_registry(
        path=path,
        security=appxf_objects.get_security_unlocked(path),
        config=user_config,
        local_name='local_registry_user',
        remote_name='remote_registry')
    Storage.switch_context('')

    # initialize admin:
    admin_registry.initialize_as_admin()

    # transfer admin keys
    admin_key_bytes = admin_registry.get_admin_key_bytes()
    user_registry.set_admin_key_bytes(admin_key_bytes)

    # initialize user via admin:
    request_bytes = user_registry.get_request_bytes()
    print(f'Size of user request: {len(request_bytes)}')
    request = admin_registry.get_request_data(request_bytes)
    user_id = admin_registry.add_user_from_request(request=request, roles=['user', 'new'])
    response = admin_registry.get_response_bytes(user_id)
    print(f'Size of response: {len(response)}')
    user_registry.set_response_bytes(response)

    yield admin_registry, user_registry

    # Testing used context swtiching, ensure proper state for anything after:
    Storage.switch_context('')
    Storage.reset()

def test_registry_init(fresh_registry):
    registry: Registry = fresh_registry
    # exactly adming and user should be present
    assert 'admin' in registry.get_roles()
    assert 'user' in registry.get_roles()
    assert len(registry.get_roles()) == 2

    assert not registry.is_initialized()
    # no one should be registered
    assert not registry.get_users()


def test_registry_admin_init(admin_initialized_registry):
    registry: Registry = admin_initialized_registry
    assert registry.is_initialized()

    assert len(registry.get_users('admin')) == 1
    assert len(registry.get_users('user')) == 1
    # user ID for initialized admin should be 0
    assert 'admin' in registry.get_roles(1)
    assert 'user' in registry.get_roles(1)
    # self USER_ID should be known
    assert 'admin' in registry.get_roles(0)
    assert 'user' in registry.get_roles(0)

def test_registry_user_init(admin_user_initialized_registry_pair):
    admin_registry: Registry = admin_user_initialized_registry_pair[0]
    user_registry: Registry = admin_user_initialized_registry_pair[1]
    #assert user_registry.is_initialized()

    # verify user ID's
    assert admin_registry.user_id == 1
    assert user_registry.user_id == 2

    # check roles of new user that should have ID 2
    assert 'user' in admin_registry.get_roles(2)
    assert 'new' in admin_registry.get_roles(2)
    # general roles
    assert 'new' in admin_registry.get_roles()
    assert len(admin_registry.get_roles()) == 3

    # SAME on user side check roles of new user that should have ID 2 - but
    # using 0 for current user:
    assert 'user' in user_registry.get_roles(0)
    assert 'new' in user_registry.get_roles(0)
    # general roles
    assert 'new' in user_registry.get_roles()
    assert len(user_registry.get_roles()) == 3

def test_registry_get_admin_keys(admin_initialized_registry):
    registry: Registry = admin_initialized_registry
    admin_val_key = registry._user_db.get_verification_key(1)
    admin_enc_key = registry._user_db.get_encryption_key(1)

    key_data_bytes = registry.get_admin_key_bytes()

    # manual unpacking:
    key_data: list[tuple] = CompactSerializer.deserialize(key_data_bytes)

    assert len(key_data) == 1, 'There should only be one admin key pair'
    assert len(key_data[0]) == 3, 'There should only be the USER ID, a validataion and an encryption key'
    assert key_data[0][0] == registry.user_id, 'First in tuple should be user ID'
    assert key_data[0][1] == admin_val_key, 'Second in tuple should be validataion key'
    assert key_data[0][2] == admin_enc_key, 'Third in tuple should be encryption key'

    # also include the error message when using the set_admin_key_bytes on the admin instance.
    with pytest.raises(KissRegistryError) as exc_info:
        registry.set_admin_key_bytes(key_data_bytes)
    assert 'Cannot set admin keys' in str(exc_info.value)
    assert 'initialized registry' in str(exc_info.value)

def test_registry_set_admin_keys(fresh_registry):
    registry: Registry = fresh_registry
    assert len(registry.get_users()) == 0
    # manually build admin key data just using the users public keys:
    data = [(1,
             registry._security.get_signing_public_key(),
             registry._security.get_encryption_public_key())]
    data_bytes = CompactSerializer.serialize(data)

    registry.set_admin_key_bytes(data_bytes)
    assert len(registry.get_users()) == 1
    assert registry.get_users(role='admin') == {data[0][0]}
    assert registry._user_db.get_verification_key(1) == data[0][1]
    assert registry._user_db.get_encryption_key(1) == data[0][2]

def test_registry_existing_user(admin_user_initialized_registry_pair):
    admin_registry: Registry = admin_user_initialized_registry_pair[0]
    user_registry: Registry = admin_user_initialized_registry_pair[1]
    user_id = user_registry.user_id

    # user current roles
    user_roles = admin_registry.get_roles(user_id)
    assert 'user' in user_roles
    assert 'new' in user_roles
    assert 2 == len(user_roles)

    request_bytes = user_registry.get_request_bytes()
    request = user_registry.get_request_data(request_bytes)
    assert user_id == admin_registry.add_user_from_request(
        request, 'user')

    # check again the user DB at admin side on the changed roles
    user_roles = admin_registry.get_roles(user_id)
    assert 'user' in user_roles
    assert 1 == len(user_roles)

def test_registy_inconsistent_user(admin_user_initialized_registry_pair):
    admin_registry: Registry = admin_user_initialized_registry_pair[0]
    user_registry: Registry = admin_user_initialized_registry_pair[1]

    # request differs in encryption key:
    request_bytes = user_registry.get_request_bytes()
    request = user_registry.get_request_data(request_bytes)
    request._data['encryption_key'] = request.encryption_key + b'.'
    assert admin_registry.add_user_from_request(request, 'user') < 0
    # request differs in signing key:
    request_bytes = user_registry.get_request_bytes()
    request = user_registry.get_request_data(request_bytes)
    request._data['signing_key'] = request.signing_key + b'.'
    assert admin_registry.add_user_from_request(request, 'user') < 0


def test_verify_signature_membership_and_roles(admin_user_initialized_registry_pair):
    admin_registry: Registry = admin_user_initialized_registry_pair[0]
    user_registry: Registry = admin_user_initialized_registry_pair[1]

    data = b'important bytes'

    # admin signs data, registry should validate for admin user
    _, sig_admin = admin_registry.sign(data)
    assert admin_registry.verify_signature(
        data=data,
        signing_user=admin_registry.user_id,
        signature=sig_admin
    )

    # unknown signing user should be rejected
    assert not admin_registry.verify_signature(
        data=data,
        signing_user=99999,
        signature=sig_admin
    )

    # user signs data but does not have admin role -> role check should fail
    _, sig_user = user_registry.sign(data)
    assert not admin_registry.verify_signature(
        data=data,
        signing_user=user_registry.user_id,
        signature=sig_user,
        roles=['admin']
    )


# TODO: test case adding a second user and information being transferred to
# first user.

# TODO: test case of adding a second admin
