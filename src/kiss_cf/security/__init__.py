''' Provide a security layer to your application

Security is mostly relevant for stored data such. This module covers login
mechanism and handling GUI and provides security algorithms. It can be used to
secure StorageMethods from the storage module.
'''

from .security import Security, KissSecurityException
from .local_storage import LocalSecuredStorageMethod