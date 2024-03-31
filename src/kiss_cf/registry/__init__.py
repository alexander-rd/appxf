''' Provide a security layer to your application

Security is mostly relevant for stored data such. This module covers login
mechanism and handling GUI and provides security algorithms. It can be used to
secure StorageMethods from the storage module.
'''

# flake8: noqa F401

from .shared_storage import SecureSharedStorageMaster
from .registry import Registry
