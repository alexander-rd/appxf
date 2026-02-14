# Copyright 2024-2026 the contributors of APPXF (github.com/alexander-rd/appxf)
# SPDX-License-Identifier: Apache-2.0
''' Testing LocalStorage

Utilizing BaseStorageTest for test cases. See test_storage_base.py
'''
import pytest
from appxf.storage import LocalStorage, Storage

from tests.storage.test_storage_base import BaseStorageTest
from tests._fixtures import test_sandbox

# TODO: test for right place of meta storage

# TODO: test for used disk space of raw object but also of meta data.

# Define fixture here to get it executed before setup_method which must have
# self.env to be passed to _get_storage().
@pytest.fixture(autouse=True)
def setup_local(request):
    Storage.reset()
    request.instance.env = {'dir': test_sandbox.init_test_sandbox_from_fixture(request)}

class TestLocalStorage(BaseStorageTest):
    ''' run basic Storage tests for RamStorage '''

    def _get_storage(self) -> Storage:
        return LocalStorage(file='test', path=self.env['dir'])
        #return LocalStorage.get(file='test', path=self.env['dir'])
        #factory = LocalStorage.get_factory(path=self.env['dir'])
        #return factory('test')

