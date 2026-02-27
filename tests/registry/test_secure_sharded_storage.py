# Copyright 2024-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
'''Testing RamStorage

Utilizing BaseStorageTest for test cases. See test_storage_base.py
'''

import pytest

import tests._fixtures.test_sandbox
from appxf.registry import SecureSharedStorage
from appxf.storage import LocalStorage, Storage
from tests._fixtures import appxf_objects
from tests.storage.test_storage_base import BaseStorageTest

# TODO: test signature and decryption manually to ensure formats and proper
# encryption. This will be a lot of duplicate code but the only way to test
# that files were stored encrypted. The test may even use the specific
# algorithms.

# TODO: test for used disk space of raw object but also of meta data.


# Define fixture here to get it executed before setup_method which must have
# self.env to be passed to _get_storage().
@pytest.fixture(autouse=True)
def setup_local(request):
    Storage.reset()
    env = {'dir': tests._fixtures.test_sandbox.init_test_sandbox_from_fixture(request)}
    env['config'] = appxf_objects.get_dummy_config()
    env['security'] = appxf_objects.get_security_unlocked(path=env['dir'])
    env['registry'] = appxf_objects.get_registry_admin_initialized(
        path=env['dir'], security=env['security'], config=env['config']
    )
    request.instance.env = env


class TestSecureSharedStorage(BaseStorageTest):
    '''run basic Storage tests for RamStorage'''

    def _get_storage(self) -> Storage:
        return SecureSharedStorage(
            base_storage=LocalStorage(file='test', path=self.env['dir']),
            security=self.env['security'],
            registry=self.env['registry'],
        )


# TODO: add test case that generates a matching local storage before the secure
# storage. This operation should cause an error.
