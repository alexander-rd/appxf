''' Reusable Storage Factory

The storage factory resolves registration details to a storage location to
support synchronization.
'''
from __future__ import annotations
from abc import ABC, abstractmethod

from .storage_method import StorageMethod


class KissStorageFactoryError(Exception):
    ''' Error in StorageFactory handling. '''


class StorageFactory(ABC):
    ''' Get StorageMethod objects '''
    def __init__(self):
        self._file_map: dict[str, StorageMethod] = {}

    # TODO: there is no need to "add" a file via this. The StorageMethod for
    # this location should automatically use this "add_file" instead.
    #
    # Also the '.' checking should be part of the Storable implementation.
    #
    # A check to '/' must also be added!
    def register_file(self, file: str, method: StorageMethod):
        ''' Register a file to the factory

        This class is intended to be derived from, altering the storage
        mechanism. The registration is done with respect to all derived
        StorageFactories. A derived StorageFactoryA cannot register a file
        AWESOME_CONTENT when it is already registered via StorageFactoryB that
        was deriving from the same base StorageFactory.
        '''
        if '.' in file:
            raise KissStorageFactoryError(
                'File names must not contain \'.\'. '
                'Recommended is to use \'_\' instead. '
                'Reason: kiss_cf uses files like [some_file.signature] '
                'in scope of security implementation which could lead '
                'to conflincts.')
        # TODO: consider removing this check. It may be intended usage to
        # overwrite a registration. Maybe, this check should go into the scope
        # of the factory? Also, if the factory checks again that retrieved data
        # types match, the reason behind this check would be covered. The
        # reason was: "Avoid the same resource accidently being registered with
        # different storage methods .. such that sync() would lead to
        # unexpected results."
        if file in self._file_map:
            raise KissStorageFactoryError(
                f'You already have added {file} to this storage location as '
                f'{type(self._file_map[file])}. You now try to register same '
                f'file as {type(method)}. '
                'You are likely trying to use two StorageMethods via '
                'get_storage_method() for the same file'
                )

        self._file_map[file] = method

    def deregister_file(self, file: str):
        ''' Deregister a file from the factory '''
        if file not in self._file_map.keys():
            raise KissStorageFactoryError(
               f'Cannot remove {file}. It was never added. '
               'Use get_storage_method() to safely interact '
               'with storage locations.')

        self._file_map.pop(file)

    def is_registered(self, file: str) -> bool:
        ''' Check if a file is registered to the factory '''
        return file in self._file_map

    @abstractmethod
    def get_storage_method(
            self, file: str,
            register=True,
            create=True) -> StorageMethod:
        ''' Get a storage method from the factory

        Arguments:
            file -- the file name for the storage method

        Keyword Arguments:
            register -- block registration to the origin of the storage_method
                        (like StorageLocation) to support synchronization of
                        storages. (default: {True})
            create -- create new storage method if none was registered, yet.
                      Will raise exception if no registered storage method exists.
                      (default: {True})

        Returns:
            Either a new StorageMethod or the one that was already registered
        '''


class DerivingStorageFactory(StorageFactory, ABC):
    ''' Extend the storage behavior of existing StorageFactory classes

    By extending an existing StorageFactory, you may:
      1) Alter the data that is stored/loaded. An example is the applied
         encryption/decryption in the security module.
      2) Write and load additional files when storing/loading the base file by
         using a second, unregistered file from the base StorageFactory. An
         example are the signature files used in the SharedStorageMethod of the
         registry module.
    The derived class would collect required additional configuration options.

    The general strategy when extending a StorageFactory is:
      1) Create a new StorageMethod. It shall create an unregistered
         StorageMethod for the requested file. It will use the this
         unregistered StorageMethod's store/load to add functionality. It may
         also generate additional unregistered StorageMethod objects to store
         information in related files.
      2) Create a new StorageFactory deriving from this DerivingStorageFactory.
         Let _get_storage_method() return an object from the StorageMethod in
         (1).
      3) The get_storage_method() of this DerivingStorageFactory will handle
         the registration.
    '''
    def __init__(self, storage: StorageFactory):
        StorageFactory.__init__(self)
        self._storage = storage

    def get_storage_method(
            self, file: str,
            register=True,
            create=True) -> StorageMethod:
        # TODO: resolve parameters and distribute functionality properly
        if self._storage.is_registered(file):
            storage = self._storage.get_storage_method(
                file, register=register, create=create)
            # TODO: reactivate this check
            # if type(storage) is not self._method_class:
            #     raise KissStorageFactoryError(
            #         f'Storage type should be {self._method_class} but '
            #         f'retrieved was {type(storage)}')
        else:
            storage = self._get_storage_method(file)
            self._storage.register_file(file, storage)
        return storage

    @abstractmethod
    def _get_storage_method(self, file: str) -> StorageMethod:
        ''' Construct the storage method '''
