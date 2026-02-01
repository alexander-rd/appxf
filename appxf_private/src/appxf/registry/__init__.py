'''Facade for APPXF registry module'''

from .registry import Registry, \
    AppxfRegistryError, AppxfRegistryUnknownUser, AppxfRegistryRoleError
from .shared_storage import SecureSharedStorage
from .shared_sync import SharedSync
