from datetime import datetime

from kiss_cf.storage._meta_data import MetaData

from .storage_master import StorageMaster
from .storage import Storage


class StorageMasterMock(StorageMaster):
    ''' Functional Mock to replace StorageLocations

    store/load will act on a buffer. Obtained behavior:
     * exists() will return True if there is something in the buffer
     * _get_location_timestamp will return the timestamp of the last store()
     * _store() will write into the buffer
     * _load() will read from the buffer
     * _remove() will purge the buffer

    You can access the buffer with:
      get_buffer(file)
      set_buffer(file, data)
      set_buffer_timestamp(file, datetime)
    '''
    def get_id(self, name: str = '') -> str:
        return self.__class__.__name__ + ': ' + name

    def _get_storage(self, name: str, **kwargs) -> Storage:
        return StorageMock()

    def get_meta_data(self, name: str) -> MetaData:
        # TODO: this is no reasonable MetaData behavior. It shoud use the
        # timestamp/uuid behavior from storage which needs to be implemented.
        return MetaData(storage=self._get_registered_storage(name))


class StorageMock(Storage):
    def __init__(self):
        self._data = None
        self._time: datetime = datetime.now()
        super().__init__()

    def exists(self) -> bool:
        return self._data is not None

    def load(self) -> object:
        return self._data

    def store(self, data: object):
        self._time = datetime.now()
        self._data = data
