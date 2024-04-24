'''Sync Method and Sync Location base classes'''

# allow class name being used before being fully defined (like in same class):
from __future__ import annotations

from appxf import logging
from .storage import Storage, StorageMasterBase
from .storable import Storable
from .storage_master import StorageMaster, DerivingStorageMaster
from .serializer_json import JsonSerializer
from .meta_data import MetaData


class KissStorageSyncException(Exception):
    ''' General exception from storage Sync '''


class KissChangeOnBothSidesException(Exception):
    ''' Files were changed on both storage locations sides when executing
    synchronization. '''


class SyncData(Storable):
    ''' Synchronization data (as in: <some file>.sync)

    Synchronization data is stored in human readable JSON files to allow manual
    inspection.

    Data in ['location'] is with respect to the synchronization partner. When
    looking at file.sync in location A and seeing a UUID for location B, this
    implies: the latest sync between A and B was done based on the file state
    with this UUID.
    '''
    def __init__(self,
                 storage: Storage,
                 this_master: StorageMasterBase,
                 **kwargs):
        super().__init__(storage=storage, **kwargs)
        self._version = 1
        self.location: dict[str, dict] = {}
        self.storage: dict[str, dict[str, dict]] = {}
        self._this_master = this_master

    # TODO: The dict in location should be according to MetaData.

    @classmethod
    def _get_location_template(cls) -> dict:
        ''' Template for location data '''
        # IMORTANT: if you change details here, you might need to update the
        # version in __init__ and handle for compatibility.
        return {
            # UUID is the main decision criterium for the sync algorithm.
            'uuid': '',
            # Timestamp was origingally intended to be used but is not reliable
            # in cases where updates/sync happen within seconds (as visible in
            # automated test cases). It is still kept and maintained since it
            # is valuable for manual inspections.
            'timestamp': None
            }

    def set_location_uuid_old(self, storage: StorageMasterBase, uuid: bytes):
        ''' Set UUID of file in other location. '''
        loc_id = storage.id()
        if loc_id not in self.location:
            self.location[loc_id] = self._get_location_template()
        self.location[loc_id]['uuid'] = uuid

    def set_location_uuid(self,
                          other_storage_master: StorageMasterBase,
                          uuid: bytes):
        ''' Set UUID of file in other location. '''
        this_id = self._this_master.id()
        other_id = other_storage_master.id()
        if this_id not in self.storage:
            self.storage[this_id] = {}
        if other_id not in self.storage[this_id]:
            self.storage[this_id][other_id] = self._get_location_template()
        self.storage[this_id][other_id]['uuid'] = uuid

    def get_location_uuid_old(self, storage: StorageMasterBase) -> bytes:
        ''' Get UUID of file in other location.

        Returns b'' if location is not known within this sync file.
        '''
        loc_id = storage.id()
        if loc_id not in self.location:
            return b''
        return self.location[loc_id]['uuid']

    def get_location_uuid(self,
                          other_storage_master: StorageMasterBase) -> bytes:
        ''' Get UUID of file in other location.

        Returns b'' if location is not known within this sync file.
        '''
        this_id = self._this_master.id()
        other_id = other_storage_master.id()
        if this_id not in self.storage:
            return b''
        if other_id not in self.storage[this_id]:
            return b''
        return self.storage[this_id][other_id]['uuid']

    def _get_state(self) -> object:
        data: dict = super()._get_state()
        del data['_this_master']
        return data

    # _set_state does not need an overload. The stored data will just not
    # contain what was removed above.


log = logging.getLogger(__name__)


# Pyhon dirsync:
# https://github.com/tkhyn/dirsync/blob/develop/dirsync/syncer.py
#  * Uses timestamps (stat)
#  * Uses filecmp (stat: type, size, modification time; plus eventually
#    content)

# TODO: How does the sync consider removing files again??

# TODO: storage has to resolve concurrent access problems (reading while
# writing, writing while reading, two writing)


def sync(storage_a: Storage | StorageMasterBase,
         storage_b: Storage | StorageMasterBase,
         only_a_to_b: bool = False):
    ''' Synchronize items from two StorageMasters

    Check timestamps of files on both locations and forward to the refined
    SyncMechanism.sync(). Files on the remote location that do not match a
    Storable will be ignored.
    '''
    if isinstance(storage_a, Storage) and isinstance(storage_b, Storage):
        return _sync_storage(storage_a, storage_b, only_a_to_b)
    elif isinstance(storage_a, StorageMaster) and isinstance(storage_b, StorageMaster):
        file_list = set(
            list(storage_a.get_registered_list()) +
            list(storage_b.get_registered_list()))

        log.debug(f'Starting sync:'
                  f'\nA: {storage_a.id()}\nB: {storage_b.id()}')

        for file in file_list:
            _sync_storage(
                storage_a.get_storage(file),
                storage_b.get_storage(file),
                only_a_to_b)
    else:
        raise KissStorageSyncException(
            f'Sync between types {type(storage_a)} (A) and {type(storage_b)} '
            f'(B) is not supported. Both must be either a Storage or a '
            f'StorageMaster')


def _sync_storage(storage_a: Storage,
                  storage_b: Storage,
                  only_a_to_b: bool):
    # TODO: theoretically, this one could sync storage of DIFFERENT names,
    # potentially causing confision.

    # ## Decision Stage 1: File Existance
    exists_a = storage_a.exists()
    exists_b = storage_b.exists()
    if not exists_a and not exists_b:
        # can happen if file was not created, yet
        log.debug(f'Storage does not existing on both sides.'
                  f'\nA: {storage_a.id()}\nB: {storage_b.id()}')
        return
    if not exists_b:
        log.debug(f'Storage A does not existing on B'
                  f'\nA: {storage_a.id()}\nB: {storage_b.id()}')
        _execute_sync(storage_a, storage_b)
        return
    if not exists_a and not only_a_to_b:
        log.debug(f'Storage B does not existing on A'
                  f'\nA: {storage_a.id()}\nB: {storage_b.id()}')
        _execute_sync(storage_b, storage_a)
        return
    # Both files exist. We continue normally.

    # ## Decision Stage 2: Decision based on UUID
    # Get file uuid's
    meta_a = storage_a.get_meta_data()
    meta_b = storage_b.get_meta_data()
    #print(f'>> uuid_a: {meta_a.uuid}')
    #print(f'>> uuid_b: {meta_b.uuid}')
    # read sync data
    sync_data_a = _get_sync_data(storage_a)
    sync_data_b = _get_sync_data(storage_b)
    # timestamps and uuid in sync data
    last_uuid_a = sync_data_a.get_location_uuid(
        other_storage_master=storage_b.storage_master)
    #print(f'>> uuid result: {last_uuid_a}')
    last_uuid_b = sync_data_b.get_location_uuid(
        other_storage_master=storage_a.storage_master)
    #print(f'>> uuid result: {last_uuid_b}')

    # Defensive implementation: this case cannot happen.
    # StorageLocations should generate a UUID even if the file
    # initially has none.
    if only_a_to_b:
        if meta_a.uuid != last_uuid_a:
            _execute_sync(storage_a, storage_b)
        return
    if (not last_uuid_a or
            not last_uuid_b):
        raise KissStorageSyncException(
            f'Storage exists on both locations but at least one SyncData did '
            f'not return a UUID. This should not happen. Workaround is to '
            f'remove the file from one of the locations.'
            f'\nA: {storage_a.id()}\nB: {storage_b.id()}')
    if (meta_a.uuid != last_uuid_a and
            meta_b.uuid != last_uuid_b):
        raise KissChangeOnBothSidesException(
            f'Storage changed on both sides. Not yet supported.'
            f'\nA: {storage_a.id()}\nB: {storage_b.id()}')
    if meta_a.uuid != last_uuid_a:
        _execute_sync(storage_a, storage_b)
        # logging in _execute_sync
    elif meta_b.uuid != last_uuid_b:
        _execute_sync(storage_b, storage_a)
        # logging in _execute_sync
    else:
        log.debug(f'Storages did not change.'
                  f'\nA: {storage_a.id()}\nB: {storage_b.id()}')


def _execute_sync(
    source: Storage,
    target: Storage):

    log.info(f'Updating {source.name} from {source.storage_master.id()} to {target.storage_master.id()}')

    # TODO UPGRADE: mark files "not readable" during sync
    # self.__mark_file_in_sync

    # get data
    data = source.load()
    # source_timestamp = source._get_location_timestamp(file)
    # source_uuid = source.get_uuid(file)
    source_sync_data = _get_sync_data(source)

    # write data
    target.store(data)
    # update meta data:
    target_meta = target.get_meta_data()
    source_meta = source.get_meta_data()
    target_meta.uuid = source_meta.uuid
    target_meta.update()
    # target_timestamp = target._get_location_timestamp(file)
    target_sync_data = _get_sync_data(target)

    # update source sync data:
    # source_sync_data.set_location_timestamp(target, target_timestamp)
    source_sync_data.set_location_uuid(
        other_storage_master=target.storage_master,
        uuid=source_meta.uuid)
    source_sync_data.store()
    # update target sync data: source location must now contain timestamp
    # of newly written data
    # target_sync_data.set_location_timestamp(source, source_timestamp)
    target_sync_data.set_location_uuid(
        other_storage_master=source.storage_master,
        uuid=source_meta.uuid)
    target_sync_data.store()

    # TODO UPGRADE: unmark files "not readable"
    # self.__mark_sync_done(file, data)


def _get_sync_data(storage: Storage) -> SyncData:
    ''' Get SyncData from StorageMaster '''
    if isinstance(storage.storage_master, DerivingStorageMaster):
        file_storage = storage.storage_master.get_root_master().get_storage(
            storage.name + '.sync', register=False,
            serializer=JsonSerializer)
    elif isinstance(storage.storage_master, StorageMaster):
        file_storage = storage.storage_master.get_storage(
            storage.name + '.sync', register=False,
            serializer=JsonSerializer)
    else:
        raise KissStorageSyncException(
            f'Cannot handle StorageMaster type {type(storage.storage_master)}.'
            f'This should not happen.')

    sync_data = SyncData(
        storage=file_storage,
        this_master=storage.storage_master)
    if sync_data.exists():
        sync_data.load()
    return sync_data
