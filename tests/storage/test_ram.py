# Copyright 2024-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
'''Testing RamStorage

Utilizing BaseStorageTest for test cases. See test_storage_base.py
'''

import pytest
from appxf.storage import RamStorage, Storage

from tests.storage.test_storage_base import BaseStorageTest


@pytest.fixture(autouse=True)
def setup_local():
    RamStorage.reset()


# TODO: There have to be non-functional tests on object generation timing for
# storage objects (also in context of storables or config menus that rely now
# on RAM). SAME for store/load cycles of typical data (shor string, small dict,
# 100kB bytestream, complex and large dictionaty (100kB to 1MB))


class TestRamStorage(BaseStorageTest):
    '''run basic Storage tests for RamStorage'''

    def _get_storage(self) -> Storage:
        return RamStorage('test')
