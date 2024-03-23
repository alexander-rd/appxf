''' Provide a security layer to your application

Security is mostly relevant for stored data such. This module covers login
mechanism and handling GUI and provides security algorithms. It can be used to
secure StorageMethods from the storage module.
'''

# flake8: noqa F401

from .security import Security, KissSecurityException
from .private_storage import SecurePrivateStorageFactory
