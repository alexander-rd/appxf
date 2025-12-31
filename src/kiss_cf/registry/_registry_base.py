from abc import ABC, abstractmethod


class RegistryBase(ABC):
    ''' Abstracted Registry Interface for Shared Storage

    The abstraction is required since SecureSharedStorage depends on the
    registry method while the registry depends on SecureSharedStorage to sync
    the USER_DB.
    '''
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    @abstractmethod
    def user_id(self):
        ''' Get user ID

        Method will raise KissExceptionUserId if registry is not completed.
        See: is_initialized().
        '''

    @abstractmethod
    def is_initialized(self) -> bool:
        ''' User is initialized with a user id '''

    @abstractmethod
    def get_roles(self, user_id: int | None = None) -> list[str]:
        ''' Get roles for a user ID

        If no user ID is provided, all existing roles are returned. Note that
        roles are case insensitive and 'USER' as well as 'ADMIN' being default
        roles always being present.
        '''

    @abstractmethod
    def get_encryption_keys(self, roles: list[str] | str) -> list[bytes]:
        ''' Get list of encryption keys from list of roles '''
