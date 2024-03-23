''' Basic Storage Locations '''

# allow class name being used before being fully defined (like in same class):
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timedelta

import uuid

from kiss_cf import logging
from .storage_method import StorageMethod

# TODO: Collect an inventory. __init__ of this base class shall collect all
# __init__'s and be able to report (a) all locations (as a list) and (b) all
# locations including all files (map with key being location and value being
# list of files)

# TODO RELEASE: StorageLocation should support some sync_with_timestamps().
# That returns True when the StorageLocation can ensure that new files will
# always have a newer timestamp. For example: by delaying a write operation or
# repeating it when the resulting time stamp did not change.

# TODO: Add an option upon __init__ if this location can be synced. If it
# cannot be synced, neither registration nor UUID is required. Same applies to
# time stamps. The option shall be added to avoid the overhead of UUID files -
# other overhead should not be a major concern.


class StorageLocationException(Exception):
    ''' Basic StorageLocation Exception '''


class StorageLocation(ABC):

    log = logging.getLogger(__name__ + '.StorageLocation')

    def __init__(self):
        self.timedelta_location_minus_system: timedelta | None = None
        self.test_count = 0
        self._file_map: dict[str, StorageMethod] = {}
        self.update_time_offset()

    def __str__(self):
        return f'[{self.get_id()}]'

    # TODO: there is no need to "add" a file via this. The StorageMethod for
    # this location should automatically use this "add_file" instead.
    #
    # Also the '.' checking should be part of the Storable implementation.
    #
    # A check to '/' must also be added!
    def register_file(self, file: str, method: StorageMethod):
        ''' Add storable for synchronization
        '''
        if '.' in file:
            raise StorageLocationException(
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
        if file in self._file_map.keys():
            raise StorageLocationException(
                f'You already have added {file} to this storage location as '
                f'{type(self._file_map[file])}. You now try to register same '
                f'file as {type(method)}. '
                'You are likely trying to use two StorageMethods via '
                'get_storage_method() for the same file'
                )

        self._file_map[file] = method

    def deregister_file(self, file: str):
        if file not in self._file_map.keys():
            raise StorageLocationException(
               f'Cannot remove {file}. It was never added. '
               'Use get_storage_method() to safely interact '
               'with storage locations.')
        # TODO LATER: like for add_file, this should be logged in debug.
        # But at teardown there were problems in the logger. Add logging
        # here and run tests to try to reproduce the issue.
        self._file_map.pop(file)

    def is_registered(self, file: str) -> bool:
        return file in self._file_map

    @abstractmethod
    def get_id(self, file: str = '') -> str:
        ''' String representing the specific location or file

        Used in logging to indicate which location is failing. Example for FTP
        location, this might be "ftp.your-url.com/path/of/location". Also used
        for synchronization to indicate the source of the file.
        '''

    @abstractmethod
    def exists(self, file: str) -> bool:
        ''' Does the file or path already exist?
        '''

    def get_timestamp(self, file: str) -> datetime | None:
        ''' Get file timestamp in terms of system time '''
        timestamp = self._get_location_timestamp(file)
        if timestamp and self.timedelta_location_minus_system:
            return (timestamp -
                    self.timedelta_location_minus_system)
        return None

    @abstractmethod
    def _get_location_timestamp(self, file: str) -> datetime | None:
        ''' Get modification time stamp as UTC

        This function is used by SyncLocation to determine time delta between
        local operating system and the sync location.
        '''

    # TODO: reconsider if UUID should be part of the storage location. It's
    # required for sync, not for general storage. If not done here, the sync
    # algorithm would need to set/determine the UUID. >> this would also allow
    # to remove the store/_store and load/_load combos.
    def store(self, file: str, data: bytes, straight=False):
        ''' Store bytes into file

        Arguments:
            file -- the file name to store
            data -- data to write to the file

        Keyword Arguments:
            straight -- Only write the file, no additions (default: {False})
        '''
        self._store(file, data)
        if not straight and self.is_registered(file):
            self._set_new_uuid(file)

    def _set_new_uuid(self, file: str):
        # since uuid needs to be serialized as well, we directly generate a
        # string copmatible one (36 bytes instead of 16):
        str_uuid = str(uuid.uuid4())
        self._store(file + '.uuid', str_uuid.encode('utf-8'))

    @abstractmethod
    def _store(self, file: str, data: bytes):
        ''' Store bytes into file '''

    def get_uuid(self, file: str) -> bytes:
        ''' Get UUID of file '''
        if not self.exists(file):
            return b''
        if not self.exists(file + '.uuid'):
            # this should not happen unless the file is stored outside of the
            # StorageLocation implementation
            self._set_new_uuid(file)
        return self._load(file + '.uuid')

    def load(self, file: str) -> bytes:
        ''' Load bytes from file '''
        return self._load(file)

    @abstractmethod
    def _load(self, file: str) -> bytes:
        ''' Load bytes from file '''

    # TODO: the remove should ensure that all .* files are also removed.
    @abstractmethod
    def _remove(self, file: str):
        ''' Remove a file'''

    def _log_error_on_file_operation(self, message: str):
        ''' Log message after a file operation before raising the exception

        This function adds logging information before an exception is raised.
        DO NOT raise an exeption when substituting this function.

        Example: an FTP location might add the server messages that were
        exchanged.
        '''
        self.log.error(message)

    def update_time_offset(self):
        ''' Update potential time offset

        The synchronization mechanism relies on time stamps of the
        StorageLocation and the Storable. Example: this might be a local path
        and an FTP server where the UTC time stamps could differ.
        '''
        file = 'timestamp_test_file.' + str(uuid.uuid4())
        if self.test_count > 2:
            message = 'Was not able to self-test for two times now. Quitting'
            self.log.error(message, exc_info=True)
        # ensure file does not exist
        if self.exists(file):
            # file collision - try again:
            self.log.warning(
                'Test file [%s] already exists on [%s]',
                file, self.get_id())
            self.update_time_offset()
        # put file (and remember time):
        timestamp_one = datetime.utcnow()
        self._store(file, b'')
        timestamp_two = datetime.utcnow()
        timestamp = timestamp_one + 0.5*(timestamp_two - timestamp_one)
        # get timestamp of file:
        file_timestamp = self._get_location_timestamp(file)
        # compute time offset:
        if not file_timestamp:
            self._log_error_on_file_operation(
                'Got None timestamp for test file. This should not happen.'
                )
        try:
            self.timedelta_location_minus_system = file_timestamp - timestamp
        except Exception as e:
            message = (
                f'Got timestamp {file_timestamp} from get_utc_timestamp(). '
                f'Something might have gone wrong, there.')
            self._log_error_on_file_operation(message)
            raise e
        # remove tmp file again:
        self._remove(file)

    def get_storage_method(self, file: str,
                           create: bool = True,
                           register: bool = True) -> StorageMethod:
        ''' Get sotrage method for files in location

        Arguments:
            file -- the file name of the storage method (shall be without
                    extensions)

        Keyword Arguments:
            create -- create new basic location method if True
                      (default: {True})

        Returns:
            Either a new StorageMethod or the one that is already
            registered
        '''
        if file not in self._file_map:
            if create:
                method = LocationStorageMethod(self, file)
                if register:
                    self.register_file(file, method)
                return method
            raise StorageLocationException(
                f'File {file} is not yet registered with a storage method. '
                'Either do not use create=False for this call or user '
                'register_file() before.'
                )
        return self._file_map[file]


class LocationStorageMethod(StorageMethod):
    ''' Storage method based on a Storage Location

    This class only provides the most basic storage method. Consider adding a
    security layer when storing data.
    '''
    def __init__(self, location: StorageLocation, file: str):
        super().__init__()
        self._location = location
        self._file = file

    def exists(self):
        return self._location.exists(self._file)

    def store(self, data: bytes):
        self._location.store(self._file, data)

    def load(self):
        return self._location.load(self._file)
