# Copyright 2024-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
"""Provide Base Class for Storage Testing

See specific test files for storage object related tests and implementation
specific tests. Like in storage module: RamStorage or LocalStorage.
"""

from abc import ABC, abstractmethod
from datetime import datetime

from appxf.storage import MetaData, Storage

# TODO: test cases need to be added to cover general derivation behavior when
# it comes to object creation and registry. In particular: ensure that
# instances are properly unregistered on reset() when having a derviced class
# on a raw storage.

# TODO: add test that reset() actually also resets the storage. This was a
# problem for RamStorage.

# TODO: Storages must be tested for __init__, get() and get_factory().
# Currently, only get() is tested.

# TODO: There have to be non-functional tests on object generation timing for
# storage objects (also in context of storables or config menus that rely now
# on RAM).


class BaseStorageTest(ABC):
    @abstractmethod
    def _get_storage(self) -> Storage:
        """provide a storage"""

    # TODO: alter this interface to provide the kwarg arguments instead. This
    # enables testing with constructor, get() or factory().

    def setup_method(self):
        self.storage = self._get_storage()

        assert self.storage.exists() is False
        assert self.storage.load() is None

    def teardown_method(self):
        pass

    def test_setup_only_state(self):
        pass

    def test_basic_store_load(self):
        """Check 2 store/load cycles"""
        self.storage.store("init")
        assert self.storage.load() == "init"
        # second read must work also:
        assert self.storage.load() == "init"

        self.storage.store("new")
        assert self.storage.load() == "new"

    def test_item_meta_data(self):
        # Nothing there means nothing stored
        meta = self.storage.get_meta_data()
        assert meta is None
        # Also metadata is expected to be None:
        assert self.storage.get_meta_data() is None

        # stored should have a uuid and a close-enough timestamp
        self.storage.store("data")
        meta: MetaData = self.storage.get_meta_data()
        assert isinstance(meta, MetaData)
        timestamp = meta.timestamp
        uuid_one = meta.uuid
        time_diff = datetime.now() - datetime.fromisoformat(timestamp)
        assert time_diff.total_seconds() < 1

        # second store must have differt uuid
        self.storage.store("new data")
        meta = self.storage.get_meta_data()
        uuid_two = meta.uuid
        assert uuid_one != uuid_two

    def test_other_meta_data(self):
        assert self.storage.get_meta("other").load() is None

        # store only meta data - while storing meta without actual object may
        # not be reasonable, there is no reason to block this
        other_one = {"test", 42}
        self.storage.get_meta("other").store(other_one)
        other_one_reload = self.storage.get_meta("other").load()
        assert other_one == other_one_reload
        # the returned object cannot and should not be the same:
        assert other_one is not other_one_reload

        # write another value and test again
        other_two = ["other", 42]
        self.storage.get_meta("other").store(other_two)
        other_two_reload = self.storage.get_meta("other").load()
        assert other_two == other_two_reload
        assert other_two is not other_two_reload
