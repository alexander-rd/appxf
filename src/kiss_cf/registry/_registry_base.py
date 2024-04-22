from abc import ABC, abstractmethod


class RegistryBase(ABC):
    ''' Abstracted Registry Interface for Shared Storage

    The abstraction is required since SecureSharedStorage depends on the
    registry method while the registry depends on SecureSharedStorage to sync
    the USER_DB.
    '''
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @abstractmethod
    def get_roles(self, id: int | None = None) -> list[str]:
        ''' Get roles for a user ID '''

    @abstractmethod
    def get_encryption_keys(self, roles: list[str] | str) -> list[bytes]:
        ''' Get list of encryption keys from list of roles '''
