import pytest
from unittest.mock import patch

from kiss_cf.config import Config
from kiss_cf.storage import StorageMasterMock
from kiss_cf.security import SecurityMock

from kiss_cf.registry import Registry

def get_fresh_registry() -> Registry:
    ''' Provide a freshly initialized registry '''
    local_storage_mock = StorageMasterMock()
    remote_storage_mock = StorageMasterMock()
    security = SecurityMock()
    security.init_user('test')
    config = Config()
    registry = Registry(
        local_base_storage=local_storage_mock,
        remote_base_storage=remote_storage_mock,
        security=security,
        config=config,
        user_config_section='')
    return registry


@pytest.fixture
def fresh_registry():
    ''' Provide an uninitialized registry '''
    return get_fresh_registry()

@pytest.fixture
def admin_initialized_registry(fresh_registry):
    ''' Provide an admin-initialized registry '''
    registry = get_fresh_registry()
    registry.initialize_as_admin()
    return registry

@pytest.fixture
def admin_user_initialized_registry_pair(fresh_registry):
    ''' Provide pair of registries '''
    admin_registry = get_fresh_registry()
    admin_registry.initialize_as_admin()
    user_registry = get_fresh_registry()

    request = user_registry.get_request()
    user_id = admin_registry.add_user_from_request(request=request, roles=['user', 'new'])
    response = admin_registry.get_response_bytes(user_id)
    user_registry.set_response_bytes(response)
    return admin_registry, user_registry

def test_registry_init(fresh_registry):
    registry: Registry = fresh_registry
    # exactly adming and user should be present
    assert 'admin' in registry.get_roles()
    assert 'user' in registry.get_roles()
    assert len(registry.get_roles()) == 2

    assert not registry.is_initialized()
    # no one should be registered
    assert not registry.get_encryption_keys('admin')
    assert not registry.get_encryption_keys('user')


def test_registry_admin_init(admin_initialized_registry):
    registry: Registry = admin_initialized_registry
    assert registry.is_initialized()

    assert len(registry.get_encryption_keys('admin')) == 1
    assert len(registry.get_encryption_keys('user')) == 1
    # user ID for initialized admin should be 0
    assert 'admin' in registry.get_roles(0)
    assert 'user' in registry.get_roles(0)
    # self USER_ID should be known
    assert 'admin' in registry.get_roles(-1)
    assert 'user' in registry.get_roles(-1)

def test_registry_user_init(admin_user_initialized_registry_pair):
    admin_registry: Registry = admin_user_initialized_registry_pair[0]
    user_registry: Registry = admin_user_initialized_registry_pair[1]
    #assert user_registry.is_initialized()

    # check roles of new user that should have ID 1
    assert 'user' in admin_registry.get_roles(1)
    assert 'new' in admin_registry.get_roles(1)
    # general roles
    assert 'new' in admin_registry.get_roles()
    assert len(admin_registry.get_roles()) == 3
