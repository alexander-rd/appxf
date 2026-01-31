''' Facade for storage related classes '''

# Only the abstract/general classes and the specific implementations should be
# public. Intermediate classes like a LocalStorage is considered
# within the location implementations but shall only be treated as
# Storage when used elsewhere. Rationale: keep the external interface
# simple.

# flake8: noqa F401

# Abstract/General Classes
from .serializer import Serializer
from .storable import Storable, AppxfStorableError
from .storage import Storage
from .storage import AppxfStorageError, AppxfStorageWarning

# Serializer Implementations:
from .serializer_raw import RawSerializer
from .serializer_compact import CompactSerializer
from .serializer_json import JsonSerializer
from .storage_to_bytes import StorageToBytes

# Storage Implementations
from .local import LocalStorage
#from .ftp import FtpStorage
from .ram import RamStorage

# Helpers
from .meta_data import MetaData

# Synchronization
from .sync import sync
