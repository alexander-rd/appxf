from typing import NamedTuple

from kiss_cf.storage import StorageMaster, sync

from .registry import Registry
from .shared_storage import SecureSharedStorageMaster

class KissSharedSyncError(Exception):
    ''' General Error in Shared Sync '''


class SyncPair(NamedTuple):
    local: StorageMaster
    remote: SecureSharedStorageMaster
    writing: list[str]
    additional_reading: list[str]


class SharedSync():
    ''' Collect synchronization pairs.

    Synchornization pairs define writing and reading roles that impact allowed
    sync directions. The provided Registry provides the user's role
    permissions.

    Common usage would be based on Secured storage from the security module and
    SecureShared storage from the registry module.
    '''

    def __init__(self, registry: Registry):
        self._registry = registry
        self._sync_pairs: list[SyncPair] = []

    def add_sync_pair(self,
                      local: StorageMaster,
                      remote: SecureSharedStorageMaster,
                      writing_roles: list[str] | None = None,
                      additional_readers: list[str] | None = None):
        ''' Register two storages for synchronization '''
        # adapt None input:
        if writing_roles is None:
            writing_roles = []
        if additional_readers is None:
            additional_readers = []
        readers = list(set(writing_roles + additional_readers))
        self._sync_pairs.append(
            SyncPair(local, remote, writing_roles, readers))

    def sync(self):
        ''' Synchronize all registered pairs '''
        user_roles_set = set(self._registry.get_roles())
        for sync_pair in self._sync_pairs:
            writing = False
            reading = False
            if user_roles_set.union(sync_pair.writing):
                writing = True
                reading = True
            elif user_roles_set.union(sync_pair.additional_reading):
                reading = True

            if not reading and not writing:
                continue
            # note: "writing" but "not reading" does not exist
            # TODO: add and allow directional sync. For now, not supported:
            if not writing:
                raise KissSharedSyncError(
                    f'Uni-directional sync is not supported, use has roles '
                    f'{user_roles_set} but would need one of {sync_pair.writing}')
            sync(sync_pair.local, sync_pair.remote)
