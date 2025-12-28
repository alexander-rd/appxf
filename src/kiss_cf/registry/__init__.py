''' Provide a security layer to your application

Security is mostly relevant for stored data such. This module covers login
mechanism and handling GUI and provides security algorithms. It can be used to
secure Storages from the storage module.
'''

# flake8: noqa F401

from .registry import Registry, KissRegistryError
from .shared_storage import SecureSharedStorage
from .shared_sync import SharedSync
