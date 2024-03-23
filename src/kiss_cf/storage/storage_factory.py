''' Reusable Storage Factory

The storage factory resolves registration details to a storage location to
support synchronization.
'''

from .storage_method import StorageMethod
from .storage_location import StorageLocation, LocationStorageMethod


class KissStorageFactoryError(Exception):
    ''' Error in StorageFactory handling. '''


class LocationStorageFactory():
    ''' Access StorageLocation based StorageMethods

    The class collects configuration options to generate storage methods. This
    class is intended for extension. Strategy:
      1) Create a new StorageMethod class that initializes an unregistered
         StorageLocation based StorageMethod and utilizes this store/load to
         add functionality.
      2) Create a new LocationStorageFactory that derived from this or another
         factory and returns the new class from (1) to _get_storage_method.
    '''
    def __init__(self, location: StorageLocation):
        self._location = location
        # TODO: add again: self._method_class = method_class

    def get_storage_method(
            self, file: str,
            register=True,
            create=True) -> StorageMethod:
        ''' Get a storage method from the factory

        Arguments:
            file -- the file name of the storage method

        Keyword Arguments:
            register -- block registration to the origin of the storage_method
                        (like StorageLocation) to support synchronization of
                        locations. (default: {True})
            create -- create new storage method if none was regsitered
                      (default: {True})

        Returns:
            Either a new StorageMethod or the one that was already registered
        '''
        # TODO: resolve parameters and distribute functionality properly
        if self._location.is_registered(file):
            storage = self._location.get_storage_method(
                file, register=register, create=create)
            # TODO: reactivate this check
            # if type(storage) is not self._method_class:
            #     raise KissStorageFactoryError(
            #         f'Storage type should be {self._method_class} but '
            #         f'retrieved was {type(storage)}')
        else:
            storage = self._get_storage_method(file)
            self._location.register_file(file, storage)
        return storage

    def _get_storage_method(self, file: str) -> StorageMethod:
        ''' Construct the storage method '''
        return LocationStorageMethod(self._location, file)
