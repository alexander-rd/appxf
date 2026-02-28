# Copyright 2023-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
"""Sync Method and Sync Location base classes"""

# allow class name being used before being fully defined (like in same class):
from __future__ import annotations

from appxf import logging

from .meta_data import MetaData
from .serializer_json import JsonSerializer
from .storable import Storable
from .storage import Storage
from .storage_to_bytes import StorageToBytes

log = logging.get_logger(__name__)


class AppxfStorageSyncError(Exception):
    """General exception from storage Sync"""


class AppxfChangeOnBothSidesError(Exception):
    """Files were changed on both storage locations sides when executing
    synchronization."""


StorageToBytes.set_meta_serializer("sync", JsonSerializer)


class SyncData(Storable):
    """Synchronization data (as in: <some file>.sync)

    Synchronization data is stored in human readable JSON files to allow manual
    inspection.

    Data in ['sync_pair'] is with respect to the synchronization partner. When
    looking at file.sync in location A and seeing a UUID for location B, this
    implies: the latest sync between A and B was done based on the file state
    with this UUID.
    """

    def __init__(self, this_storage: Storage, meta_storage: Storage, **kwargs):
        super().__init__(storage=meta_storage, **kwargs)
        self._version = 1
        self._this_storage = this_storage
        self.sync_pair_dict: dict[str, dict] = {}
        self.storage: dict[str, dict[str, dict]] = {}

    # TODO: The dict in sync_pair_dict should be according to MetaData. << Old
    # comment >> Not clear anymore but I think this was about making the
    # snyc_pair_template consistent to MetaData. Likely, the set uuid may
    # become a set MetaData, starting to store all available MetaData for
    # potential algorithm changes.

    @classmethod
    def _get_sync_pair_template(cls) -> dict:
        """Template for sync pair data"""
        # IMORTANT: if you change details here, you might need to update the
        # version in __init__ and handle for compatibility.
        return {
            # UUID is the main decision criterium for the sync algorithm.
            "uuid": "",
            # Timestamp was origingally intended to be used but is not reliable
            # in cases where updates/sync happen within seconds (as visible in
            # automated test cases). It is still kept and maintained since it
            # is valuable for manual inspections.
            "timestamp": None,
        }

    def set_location_uuid(self, other_storage: Storage, uuid: bytes):
        """Set UUID of file in other location."""
        sync_pair = f"{self._this_storage.user}--{other_storage.location}"
        if sync_pair not in self.sync_pair_dict:
            self.sync_pair_dict[sync_pair] = self._get_sync_pair_template()
        self.sync_pair_dict[sync_pair]["uuid"] = uuid

    def get_location_uuid(self, other_storage: Storage) -> bytes:
        """Get UUID of file in other location.

        Returns b'' if location is not known within this sync file.
        """
        sync_pair = f"{self._this_storage.user}--{other_storage.location}"
        if sync_pair not in self.sync_pair_dict:
            return b""
        return self.sync_pair_dict[sync_pair]["uuid"]

    # get_state()/set_state() can be taken from Storable/Stateful but
    # attribute_mask must be extenden:
    attribute_mask = Storable.attribute_mask + ["_this_storage"]


# Pyhon dirsync:
# https://github.com/tkhyn/dirsync/blob/develop/dirsync/syncer.py
#  * Uses timestamps (stat)
#  * Uses filecmp (stat: type, size, modification time; plus eventually
#    content)

# TODO: How does the sync consider removing files again??

# TODO: storage has to resolve concurrent access problems (reading while
# writing, writing while reading, two writing)


def sync(
    storage_a: Storage | list[Storage] | Storage.Factory,
    storage_b: Storage | list[Storage] | Storage.Factory,
    only_a_to_b: bool = False,
):
    """Synchronize items from two storage factories

    Check timestamps of files on both locations and forward to the refined
    SyncMechanism.sync(). Files on the remote location that do not match a
    Storable will be ignored.
    """
    if isinstance(storage_a, Storage) and isinstance(storage_b, Storage):
        return _sync_storage(storage_a, storage_b, only_a_to_b)
    if isinstance(storage_a, Storage.Factory) and isinstance(
        storage_b, Storage.Factory
    ):
        # TODO: this case is not "fair" it could also take all from B and then
        # constract in A.
        print(f"Syncing {storage_a} with {storage_b}")
        for storage in storage_a(Storage.AllRegistered):
            _sync_storage(storage, storage_b(storage.name), only_a_to_b)
    else:
        # TODO: add support again for sync of storage masters
        raise AppxfStorageSyncError(
            f"Sync between types {type(storage_a)} (A) and {type(storage_b)} "
            f"(B) is not supported. Both must be either a Storage or a "
            f"storage factory"
        )


def _sync_storage(storage_a: Storage, storage_b: Storage, only_a_to_b: bool):
    # TODO: theoretically, this one could sync storage of DIFFERENT names,
    # potentially causing confision.
    log.debug(f"Syncing:\nA={storage_a.id()}\nB={storage_b.id()}")

    # ## Decision Stage 1: File Existance
    exists_a = storage_a.exists()
    exists_b = storage_b.exists()
    if not exists_a and not exists_b:
        # can happen if file was not created, yet
        log.debug(
            f"Storage does not existing on both sides."
            f"\nA: {storage_a.id()}\nB: {storage_b.id()}"
        )
        return
    if not exists_a and only_a_to_b:
        # nothing can be done is A does not exist
        return
    if not exists_a:
        # b exists and it is not only_a_to_b, so we try to sync:
        log.debug(
            f"Storage B does not existing on A"
            f"\nA: {storage_a.id()}\nB: {storage_b.id()}"
        )
        _execute_sync(storage_b, storage_a)
        return
    if not exists_b:
        log.debug(
            f"Storage A does not existing on B"
            f"\nA: {storage_a.id()}\nB: {storage_b.id()}"
        )
        _execute_sync(storage_a, storage_b)
        return

    # Both files exist. We continue normally.

    # ## Decision Stage 2: Decision based on UUID
    # Get file uuid's
    meta_a: MetaData = storage_a.get_meta_data()
    meta_b: MetaData = storage_b.get_meta_data()
    # read sync data
    sync_data_a = _get_sync_data(storage_a)
    sync_data_b = _get_sync_data(storage_b)
    # timestamps and uuid in sync data
    last_uuid_a = sync_data_a.get_location_uuid(other_storage=storage_b)
    last_uuid_b = sync_data_b.get_location_uuid(other_storage=storage_a)

    # Defensive implementation: this case cannot happen.
    # StorageLocations should generate a UUID even if the file
    # initially has none.
    if only_a_to_b:
        if meta_a.uuid != last_uuid_a:
            _execute_sync(storage_a, storage_b)
        return
    if not last_uuid_a or not last_uuid_b:
        raise AppxfStorageSyncError(
            f"Storage exists on both locations but at least one SyncData did "
            f"not return a UUID. This should not happen. Workaround is to "
            f"remove the file from one of the locations."
            f"\nA: {storage_a.id()}\nB: {storage_b.id()}"
        )
    if meta_a.uuid != last_uuid_a and meta_b.uuid != last_uuid_b:
        raise AppxfChangeOnBothSidesError(
            f"Storage changed on both sides. Not yet supported."
            f"\nA: {storage_a.id()}\nB: {storage_b.id()}"
        )
    if meta_a.uuid != last_uuid_a:
        _execute_sync(storage_a, storage_b)
        # logging in _execute_sync
    elif meta_b.uuid != last_uuid_b:
        _execute_sync(storage_b, storage_a)
        # logging in _execute_sync
    else:
        log.debug(f"Storages did not change.\nA: {storage_a.id()}\nB: {storage_b.id()}")


def _execute_sync(source: Storage, target: Storage):

    log.info(f"Updating from {source.id()} to {target.id()}")

    # TODO UPGRADE: mark files "not readable" during sync
    # self.__mark_file_in_sync

    # get data
    data = source.load()
    source_sync_data = _get_sync_data(source)

    # write data
    target.store(data)
    # update meta data:
    target_meta: MetaData = target.get_meta_data()
    source_meta: MetaData = source.get_meta_data()
    target_meta.uuid = source_meta.uuid
    target.set_meta_data(target_meta)
    target_sync_data = _get_sync_data(target)

    # update source sync data:
    # source_sync_data.set_location_timestamp(target, target_timestamp)
    source_sync_data.set_location_uuid(other_storage=target, uuid=source_meta.uuid)
    source_sync_data.store()
    # update target sync data: source location must now contain timestamp
    # of newly written data
    # target_sync_data.set_location_timestamp(source, source_timestamp)
    target_sync_data.set_location_uuid(other_storage=source, uuid=source_meta.uuid)
    target_sync_data.store()

    # TODO UPGRADE: unmark files "not readable"
    # self.__mark_sync_done(file, data)


def _get_sync_data(storage: Storage) -> SyncData:
    """Get SyncData from Storage"""

    file_storage = storage.get_meta("sync")

    sync_data = SyncData(this_storage=storage, meta_storage=file_storage)
    if sync_data.exists():
        sync_data.load()
    return sync_data
