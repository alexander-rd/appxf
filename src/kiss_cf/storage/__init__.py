''' Facade for storage related classes '''

# Only the abstract/general classes and the specific implementations should be
# public. Intermediate classes like a LocationStorageMethod is considered
# within the location implementations but shall only be treated as
# StorageMethod when used elsewhere. Rationale: keep the external interface
# simple.

# flake8: noqa F401

# Abstract/General Classes
from .storable import Storable
from .storage_method import StorageMethod
from .storage_location import StorageLocation
from .storage_factory import StorageFactory, DerivingStorageFactory, KissStorageFactoryError

# Specific Storage Locations
from .local import LocalStorageLocation
from .ftp import FtpLocation
from .sync import sync

# Helpers
from .storage_method import StorageMethodDummy
from .serialize import serialize, deserialize
