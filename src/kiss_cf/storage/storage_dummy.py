from ._storage_master_base import StorageMasterBase
from .meta_data import MetaData
from .storage import Storage

class StorageDummyMaster(StorageMasterBase):
    ''' Dummy to satisfy StorageDummy dependencies '''
    def id(self, name: str = '') -> str:
        return 'StorageDummyMaster'

    def get_meta_data(self, name: str) -> MetaData:
        return MetaData()

class StorageDummy(Storage):
    ''' Storage dummy as default behavior.

    To allow Storable implementations to always assume having a Storage,
    this class provides a silent replacement. It is recommended if the Storable
    class still uses load()/store() even when not being set up for storage.

    Note: The _set_bytestream() of the Storable must be robust to receive an
    empty bytestream as indication for "no Storage defined".
    '''
    def __init__(self):
        super().__init__(storage=StorageDummyMaster(),
                         name='dummy')

    def id(self) -> str:
        return 'StorageDummy'

    def exists(self) -> bool:
        return False

    def load(self) -> object:
        return b''

    def store(self, data: object):
        pass
