from datetime import datetime

from .meta_data import MetaData
from ._meta_data_storable import MetaDataStorable

from .storage_master import StorageMaster
from .storage_dummy import StorageDummy
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
    def __init__(self,
                 name: str = 'mock',
                 **kwargs):
        self._name = name
        # While not having a StorageMaster registry, for fiels to appear as
        # "were stored", every generated storage must be recorded.
        self._mock_registry: dict[str, StorageMock] = {}
        super().__init__(**kwargs)

    def print_storages(self):
        print(f'[{self.id()}] with following files: ')
        for storage in self._mock_registry.values():
            empty_str = 'existing' if storage.exists() else 'not existing'
            print(f'  {empty_str} {storage.id()}')

    def id(self, name: str = '') -> str:
        name = f'::{name}' if name else ''
        return f'{self.__class__.__name__}({self._name}){name}'

    def _get_storage(self, name: str, **kwargs) -> Storage:
        if name in self._mock_registry:
            return self._mock_registry[name]
        storage = StorageMock(storage=self, name=name)
        self._mock_registry[name] = storage
        return storage

    def get_meta_data(self, name: str) -> MetaData:
        # TODO: this is no reasonable MetaData behavior. It shoud use the
        # timestamp/uuid behavior from storage which needs to be implemented.
        return self._get_storage(name).get_meta_data()


class StorageMock(Storage):
    def __init__(self,
                 storage: StorageMasterMock,
                 name: str,
                 **kwargs):
        super().__init__(storage=storage, name=name, **kwargs)
        self._data = None
        self.meta_data = MetaDataStorable(storage=StorageDummy())

    def get_meta_data(self) -> MetaData:
        return self.meta_data

    def exists(self) -> bool:
        return self._data is not None

    def load(self) -> object:
        return deepcopy(self._data)

    def store(self, data: object):
        self.meta_data.new_content()
        self._data = deepcopy(data)
