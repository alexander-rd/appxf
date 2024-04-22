import pytest

from kiss_cf.config import Config
from kiss_cf.storage import StorageMasterMock
from kiss_cf.security import Security

from kiss_cf.registry import Registry


def test_registry_init():
    local_storage_mock = StorageMasterMock()
    remote_storage_mock = StorageMasterMock()
    security = Security(salt='test')
    config = Config()
    registry = Registry(
        local_base_storage=local_storage_mock,
        remote_base_storage=remote_storage_mock,
        security=security,
        config=config)

    # exactly adming and user should be present
    assert 'admin' in registry.get_roles()
    assert 'user' in registry.get_roles()
    assert len(registry.get_roles()) == 2

    # no one should be registered
    assert not registry.get_encryption_keys('admin')
    assert not registry.get_encryption_keys('user')