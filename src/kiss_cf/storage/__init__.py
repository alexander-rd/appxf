''' Facade for storage related classes '''

# Only the abstract/general classes and the specific implementations should be
# public. Intermediate classes like a LocationStorageMethod is considered
# within the location implementations but shall only be treated as
# StorageMethod when used elsewhere. Rationale: keep the external interface
# simple.

# flake8: noqa F401

# Abstract/General Classes
from .serializer import Serializer, KissSerializerError
from .storable import Storable
from .storage import Storage
from .storage_master import StorageMaster, DerivingStorageMaster, KissStorageMasterError

# Serializer Implementations:
from .serializer_raw import RawSerializer
from .serializer_compact import CompactSerializer
from .serializer_json import JsonSerializer

# Storage Locations
from .local import LocalStorageMaster
from .ftp import FtpLocation

# Helpers
from .storage import StorageMethodDummy
from .storage_master_mock import StorageMasterMock

# Synchronization
from .sync import sync
