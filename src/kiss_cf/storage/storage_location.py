''' Basic Storage Locations '''

# allow class name being used before being fully defined (like in same class):
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import uuid

from kiss_cf import logging
from kiss_cf.storage import StorageMethod

class StorageLocationException(Exception):
    ''' Basic StorageLocation Exception '''

# TODO: Collect an inventory. __init__ of this base class shall collect all
# __init__'s and be able to report (a) all locations (as a list) and (b) all
# locations including all files (map with key being location and value being
# list of files)

class StorageLocation(ABC):

    log = logging.getLogger(__name__ + '.StorageLocation')

    def __init__(self):
        self.timedelta_location_minus_system: timedelta | None = None
        self.test_count = 0
        self.file_list: list[str] = []
        self.update_time_offset()

    # TODO: there is no need to "add" a file via this. The StorageMethod for
    # this location should automatically use this "add_file" instead.
    #
    # Also the '.' checking should be part of the Storable implementation.
    #
    # A check to '/' must also be added!
    def register_file(self, file: str):
        ''' Add storable for synchronization
        '''
        if '.' in file:
            raise StorageLocationException(
                'File names must not contain \'.\'. Recommended is to use \'_\' instead. '
                'Reason: kiss_cf uses files like [some_file.signature] in scope of security '
                'implementation which could lead to conflincts.')
        if file in self.file_list:
            raise StorageLocationException(
                f'You already have added {file} to this storage location. '
                'You are likely trying to use two StorageMethods via get_storage_method() '
                'for the same file'
                )
        else:
            self.log.debug(f'Adding file {file} to [{self.get_id()}]')
            self.file_list.append(file)

    def __str__(self):
        return f'[{self.get_id()}]'

    def deregister_file(self, file: str):
        if file not in self.file_list:
            raise StorageLocationException(
               f'Cannot remove {file}. It was never added. '
               'Use get_storage_method() to safely interact with storage locations.')
        else:
            # TODO LATER: like for add_file, this should be logged in debug.
            # But at teardown there were problems in the logger. Add logging
            # here and run tests to try to reproduce the issue.
            self.file_list.remove(file)

    @abstractmethod
    def get_id(self, file: str = '') -> str:
        ''' String representing the specific location or file

        Used in logging to indicate which location is failing. Example for FTP
        location, this might be "ftp.your-url.com/path/of/location". Also used
        for synchronization to indicate the source of the file.
        '''

    @abstractmethod
    def file_exists(self, file: str) -> bool:
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

    def store(self, file: str, data: bytes):
        ''' Store bytes into file '''
        self._store(file, data)
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
        if not self.file_exists(file):
            return b''
        if not self.file_exists(file + '.uuid'):
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
        if self.file_exists(file):
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
            message = (f'Got timestamp {file_timestamp} from get_utc_timestamp(). '
                       'Something might have gone wrong, there.')
            self._log_error_on_file_operation(message)
            raise e
        # remove tmp file again:
        self._remove(file)

    def get_storage_method(self, file: str) -> LocationStorageMethod:
        ''' Get sotrage method for files in location '''
        return LocationStorageMethod(self, file)


class LocationStorageMethod(StorageMethod):
    ''' Storage method based on a Storage Location

    Note that this class only provides the most basic storage method. Consider
    adding a security layer when storing data.
    '''
    def __init__(self, location: StorageLocation, file: str):
        super().__init__()
        # allow derived storage methods to skip the add_file() call that is
        # intended not to be called twice.
        if not hasattr(self, '_location'):
            self._location = location
            self._location.register_file(file)
        self._file = file

    # define properties to make the fields read only
    @property
    def location(self) -> StorageLocation:
        ''' Location associated with this StorageMethod '''
        return self._location
    @property
    def file(self) -> str:
        ''' File associated with this StorageLocation based StorageMethod '''
        return self._file

    def __del__(self):
        self._location.deregister_file(self.file)

    def store(self, data: bytes):
        self._location.store(self.file, data)

    def load(self):
        return self._location.load(self.file)


class DerivingStorageMethod(LocationStorageMethod):
    ''' Helper class to not repeating the common __init__

    StorageMethods can be cascaded to add functionality while remaining
    modular. To achieve this, each deriving StorageMethod needs to be a
    LocationStorageMethod. Since StorageLocation maintains a list of files for
    which StorageMethods exist, this procedure requires a special __init__.
    This class just avoids implementatio overhead on this peculiarity.
    '''
    def __init__(self,
                 base_method: LocationStorageMethod):
        # as deriving class, we have to already set the location to skip the
        # add_file in derived class:
        self._location = base_method.location
        super().__init__(location=base_method.location, file=base_method.file)
        self._base_method = base_method
        self._file = base_method._file

    # like above for add_file(), the destructor must be overwritten to not call
    # remove_file:
    def __del__(self):
        pass
