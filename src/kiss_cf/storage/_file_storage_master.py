''' Basic Storage Locations '''

# allow class name being used before being fully defined (like in same class):
from __future__ import annotations

from abc import ABC, abstractmethod

from kiss_cf import logging
from .storage import Storage
from .storage_master import StorageMaster
from .serializer import Serializer
from .serializer_compact import CompactSerializer
from .serializer_json import JsonSerializer
from ._meta_data import MetaData

# TODO RELEASE: StorageLocation should support some sync_with_timestamps().
# That returns True when the StorageLocation can ensure that new files will
# always have a newer timestamp. For example: by delaying a write operation or
# repeating it when the resulting time stamp did not change.


class FileStorageMaster(StorageMaster, ABC):
    ''' Abstraction of File and Path based storage '''

    log = logging.getLogger(__name__ + '.StorageLocation')

    def __init__(self,
                 default_serializer: type[Serializer] = CompactSerializer):
        StorageMaster.__init__(self)
        self._default_serializer = default_serializer

    def __str__(self):
        return f'[{self.get_id()}]'

    def store(self, file: str, data: bytes):
        ''' Store bytes into file
        '''
        if self.is_registered(file):
            # TODO: need to extend StorageMaster and storage classes to be
            # able to generate subdirectories. In this case: .sync
            meta_storage = self._get_storage(file + '.meta',
                                             serializer=JsonSerializer)
            # construction automatically sets a UUID
            meta = MetaData(storage=meta_storage)
            meta.store()
            # TODO: the hash or file content should be analyzed before
            # generating a new UUID
        self._store(file, data)

    def get_meta_data(self, file: str) -> MetaData:
        meta_storage = self._get_storage(file + '.meta',
                                         serializer=JsonSerializer)
        meta = MetaData(storage=meta_storage)
        if meta_storage.exists():
            meta.load()
        return meta

    def load(self, file: str) -> bytes:
        ''' Load bytes from file '''
        # Abstracted for consistency to store(). There are currently no special
        # operations required.
        return self._load(file)

    # ## StorageMaster related functions
    def _get_storage(self,
                     file: str,
                     serializer: type[Serializer] | None = None,
                     ) -> Storage:
        if serializer is None:
            serializer = self._default_serializer
        return LocationStorageMethod(self, file, serializer=serializer)

    # ## Implemenation dependent abstractions
    @abstractmethod
    def exists(self, file: str) -> bool:
        ''' Does the file or path already exist?
        '''

    @abstractmethod
    def _store(self, file: str, data: bytes):
        ''' Implementation specific storing of bytes to file '''

    @abstractmethod
    def _load(self, file: str) -> bytes:
        ''' Implementation specific loading of bytes from file '''

    # TODO: the remove should ensure that all meta files are also removed. Or
    # better to say: the meta files are adapted such that a sync can perform
    # the remove on any other side.
    #
    # It is currently unused, anyways
    #
    # @abstractmethod
    # def _remove(self, file: str):
    #     ''' Remove a file'''

    def _log_error_on_file_operation(self, message: str):
        ''' Log message after a file operation before raising the exception

        This function adds logging information before an exception is raised.
        DO NOT raise an exeption when substituting this function.

        Example: an FTP location might add the server messages that were
        exchanged.
        '''
        self.log.error(message)


class LocationStorageMethod(Storage):
    ''' Storage method based on a Storage Location

    This class only provides the most basic storage method. Consider adding a
    security layer when storing data.
    '''
    def __init__(self,
                 location: FileStorageMaster,
                 file: str,
                 serializer: type[Serializer]):
        super().__init__()
        self._location = location
        self._file = file
        self._serializer = serializer

    def exists(self):
        return self._location.exists(self._file)

    def store(self, data: object):
        byte_data = self._serializer.serialize(data)
        self._location.store(self._file, byte_data)

    def load(self):
        byte_data = self._location.load(self._file)
        return self._serializer.deserialize(byte_data)
