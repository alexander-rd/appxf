''' Facade for storage related classes '''

# Abstract/General Classes
from .storage_method import StorageMethod, StorageMethodDummy
from .storable import Storable
from .storage_location import StorageLocation

# Specific Storage Locations
from .local import LocalStorageLocation
from .sync import sync
