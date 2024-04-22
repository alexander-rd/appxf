from datetime import datetime

from kiss_cf.storage.meta_data import MetaData

from .storage_master import StorageMaster
from .storage import Storage

from copy import deepcopy


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
    def id(self, name: str = '') -> str:
        return self.__class__.__name__ + ': ' + name

    def _get_storage(self, name: str, **kwargs) -> Storage:
        return StorageMock(storage=self, name=name)

    def get_meta_data(self, name: str) -> MetaData:
        # TODO: this is no reasonable MetaData behavior. It shoud use the
        # timestamp/uuid behavior from storage which needs to be implemented.
        return MetaData(storage=self._get_registered_storage(name))


class StorageMock(Storage):
    def __init__(self,
                 storage: StorageMasterMock,
                 name: str,
                 **kwargs):
        super().__init__(storage=storage, name=name, **kwargs)
        self._data = None
        self._time: datetime = datetime.now()

    def id(self) -> str:
        return 'StorageMock'

    def exists(self) -> bool:
        return self._data is not None

    def load(self) -> object:
        return deepcopy(self._data)

    def store(self, data: object):
        self._time = datetime.now()
        self._data = deepcopy(data)
