from datetime import datetime

from kiss_cf.storage import StorageLocation

class StorageLocationMock(StorageLocation):
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
    def __init__(self):
        self._data: dict[str, bytes] = {}
        self._time: dict[str, datetime] = {}
        super().__init__()

    def get_id(self, file: str = '') -> str:
        return self.__class__.__name__ + ': ' + file

    def exists(self, file: str) -> bool:
        return (file in self._data)

    def _get_location_timestamp(self, file: str) -> datetime | None:
        return self._time.get(file, None)

    def _store(self, file: str, data: bytes):
        self._time[file] = datetime.now()
        self._data[file] = data

    def _load(self, file: str) -> bytes:
        # Note that load() already makes an exist() check
        return self._data[file]

    def _remove(self, file: str):
        del self._time[file]
        del self._data[file]
