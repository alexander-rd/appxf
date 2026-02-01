''' Testing SecurePrivateStorage

Utilizing BaseStorageTest for test cases. See storage/test_storage_base.py
'''
import pytest
from appxf.storage import Storage, LocalStorage
from appxf.security import SecurePrivateStorage

import tests._fixtures.test_sandbox
from tests.storage.test_storage_base import BaseStorageTest
from tests._fixtures import appxf_objects

# Test manual decryption to ensure that details are stored with encryption.
# Manual decryption should define the algorithms that were used as a regression
# testing when algoirhms change.

# Define fixture here to get it executed before setup_method which must have
# self.env to be passed to _get_storage().
@pytest.fixture(autouse=True)
def setup_local(request):
    Storage.reset()
    env = {'dir': tests._fixtures.test_sandbox.init_test_sandbox_from_fixture(request)}
    env['security'] = appxf_objects.get_security_unlocked(env['dir'])
    request.instance.env = env


# TODO: test for used disk space of raw object but also of meta data.


class TestSecureStorage(BaseStorageTest):
    ''' run basic Storage tests for RamStorage '''

    def _get_storage(self) -> Storage:
        return SecurePrivateStorage(
            base_storage=LocalStorage(
                file='test',
                path=self.env['dir']),
            security=self.env['security'])

# TODO: add test case that generates a matching local storage before the secure
# storage. This operation should cause an error.
