from typing import NamedTuple

from kiss_cf.storage import StorageMaster

from .registry import Registry


class KissSharedSyncError(Exception):
    ''' General Error in Shared Sync '''


class SyncPair(NamedTuple):
    remote: StorageMaster
    local: StorageMaster
    writing: list[str]
    reading: list[str]


class SharedSync():

    def __init__(self, registry: Registry):
        self._registry = registry
        self._sync_pairs: list[SyncPair] = []

    def add_sync_pair(self,
                      remote: StorageMaster,
                      local: StorageMaster,
                      writing_roles: list[str] | None = None,
                      additional_readers: list[str] | None = None):
        ''' Register two storages for synchronization '''
        # adapt None input:
        if writing_roles is None:
            writing_roles = []
        if additional_readers is None:
            additional_readers = []
        self._sync_pairs.append(
            SyncPair(remote, local, writing_roles, additional_readers))

    def sync(self):
        ''' Synchronize all registered pairs '''
        for sync_pair in self._sync_pairs:
            pass
