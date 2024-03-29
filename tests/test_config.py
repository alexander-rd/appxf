
from kiss_cf.mock import StorageLocationMock
from kiss_cf.storage import LocationStorageFactory
from kiss_cf.config import Config

def test_config_initialization_state():
    location = StorageLocationMock()
    factory = LocationStorageFactory(location)
    #config = Config(factory)