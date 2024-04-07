''' Reusable Storage Factory

The storage factory resolves registration details to a storage location to
support synchronization.
'''
from __future__ import annotations
from abc import ABC, abstractmethod

from .storage import Storage
from ._meta_data import MetaData


class KissStorageMasterError(Exception):
    ''' Error in StorageMaster handling. '''

# TODO: Collect an inventory. __init__ of this base class shall collect all
# __init__'s and be able to report (a) all locations (as a list) and (b) all
# locations including all files (map with key being location and value being
# list of files).


# Name selection: many options were considered. Starting point was
# StorageFactory that was focusing mainly on the aspect that this class
# provides Storage objects (formerly called StorageMethod). This naming did not
# reflect (1) the registration that is performed. This is done for (2)
# supporting synchronization. Considered alternative names were Provider, Admin
# or Registry.
class StorageMaster(ABC):
    ''' Get StorageMethod objects '''
    def __init__(self):
        self._file_map: dict[str, Storage] = {}

    def register_file(self, file: str, method: Storage):
        ''' Register a file to the StorageMaster

        This class is intended to be derived from, altering the storage
        mechanism. The registration is done with respect to all derived
        StorageFactories. A derived StorageMasterA cannot register a file
        AWESOME_CONTENT when it is already registered via StorageMasterB that
        was deriving from the same base StorageMaster.
        '''
        if ('/' in file) or ('\\' in file):
            raise KissStorageMasterError(
                'File names must not indicate paths by including \'\\\' '
                'or \'/\'. If files shall be placed in subdirectories, '
                'consider creating a new StorageMaster for this path.')
        if file in self._file_map:
            raise KissStorageMasterError(
                f'You already have added {file} to this storage location as '
                f'{type(self._file_map[file])}. You now try to register same '
                f'file as {type(method)}. '
                'You are likely trying to use two StorageMethods via '
                'get_storage() for the same file'
                )

        self._file_map[file] = method

    def deregister_file(self, file: str):
        ''' Deregister a file from this StorageMaster '''
        if file not in self._file_map.keys():
            raise KissStorageMasterError(
               f'Cannot remove {file}. It was never added. '
               'Use get_storage() to safely interact '
               'with storage locations.')

        self._file_map.pop(file)

    # TODO: This cannot work with derived storages
    def is_registered(self, file: str) -> bool:
        ''' Check if a file is registered to this StorageMaster '''
        return file in self._file_map

    def get_file_list(self) -> list[str]:
        ''' Return list of registered files '''
        return list(self._file_map.keys())

    def _get_registered_storage(self, file: str) -> Storage | None:
        ''' Get a registered storage (or None)

        Method was required to allow re-routing in DerivedStorageMaster. Not
        good to have this dependency but unblocking progress.'''
        if file not in self._file_map:
            return None
        return self._file_map[file]

    def get_storage(
            self, file: str,
            register=True,
            create=True) -> Storage:
        ''' Get a Storage object from this StorageMaster

        Arguments:
            file -- the file name for the storage method

        Keyword Arguments:
            register -- True registers the retrieved StorageMethod in the
                        StorageFactory to support synchronization of storages.
                        (default: {True})
            create -- True creates a new StorageMethod if none was registered,
                      yet. An Exception will be raised if no registered
                      StorageMethod exists.  (default: {True})

        Returns:
            Either a new StorageMethod or the one that was already registered
        '''
        # try to retrieve from registry:
        storage = self._get_registered_storage(file)
        if storage is None:
            if create:
                storage = self._get_storage(file)
            else:
                raise KissStorageMasterError(
                    f'Cannot return a storage. No Storage for file {file} is '
                    f'registered and "create" option is False.')
        if register and not self.is_registered(file):
            self.register_file(file, storage)
        return storage

    @abstractmethod
    def _get_storage(self, file: str) -> Storage:
        ''' Construct the storage method '''

    @abstractmethod
    def get_id(self, file: str = '') -> str:
        ''' String representing the specific location or file

        Used in logging to indicate which location is failing. Example for FTP
        location, this might be "ftp.your-url.com/path/of/location". Also used
        for synchronization to indicate the source of the file.
        '''

    @abstractmethod
    def get_meta_data(self, file: str) -> MetaData:
        ''' '''


class DerivingStorageMaster(StorageMaster, ABC):
    ''' Extend the storage behavior of existing StorageMaster classes

    By extending an existing StorageMaster, you may:
      1) Alter the data that is stored/loaded. An example is the applied
         encryption/decryption in the security module.
      2) Write and load additional files when storing/loading the base file by
         using a second, unregistered file from the base StorageMaster. An
         example are the signature files used in the SharedStorageMethod of the
         registry module.
    The derived class would collect required additional configuration options.

    The general strategy when extending a StorageMaster is:
      1) Create a new StorageMethod. It shall create an unregistered
         StorageMethod for the requested file. It will use the this
         unregistered StorageMethod's store/load to add functionality. It may
         also generate additional unregistered StorageMethod objects to store
         information in related files.
      2) Create a new StorageMaster deriving from this DerivingStorageMaster.
         Let _get_storage() return an object from the StorageMethod in
         (1).
      3) The get_storage() of this DerivingStorageMaster will handle
         the registration.
    '''
    def __init__(self, storage: StorageMaster | DerivingStorageMaster):
        StorageMaster.__init__(self)
        self._storage = storage
        # Handle potential multiple derivations
        if isinstance(storage, DerivingStorageMaster):
            self._base_storage = storage.get_root_master()
        else:
            self._base_storage = storage

    def get_root_master(self) -> StorageMaster:
        ''' Return the root StorageMaster

        DerivedStorageMaster objects would not return basic Storage operations.
        This function is supposed to be overwritten by deriving classes.'''
        return self._base_storage

    # ## Most methods of StorageMaster must be re-routed to the _base_storage
    def register_file(self, file: str, method: Storage):
        return self._base_storage.register_file(file, method)

    def deregister_file(self, file: str):
        return self._base_storage.deregister_file(file)

    def is_registered(self, file: str) -> bool:
        return self._base_storage.is_registered(file)

    def get_file_list(self) -> list[str]:
        return self._base_storage.get_file_list()

    def _get_registered_storage(self, file: str) -> Storage | None:
        return self._base_storage._get_registered_storage(file)

    def get_id(self, file: str = ''):
        return self._base_storage.get_id(file)

    # ## Implementation specific methods of StorageMaster
    def get_meta_data(self, file: str) -> MetaDataStorable:
        # MetaData from base storage applies
        return self._base_storage.get_meta_data(file)

    # get_storage(file, ...) remains abstract
