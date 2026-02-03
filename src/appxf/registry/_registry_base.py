# Copyright 2024-2026 the contributors of APPXF (github.com/alexander-rd/appxf)
# SPDX-License-Identifier: Apache-2.0
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
    def user_id(self) -> int:
        ''' Get user ID

        Method will raise AppxfExceptionUserId if registry is not completed.
        See: is_initialized().
        '''

    @abstractmethod
    def is_initialized(self) -> bool:
        ''' User is initialized with a user id '''

    @abstractmethod
    def get_roles(self, user_id: int | None = None) -> list[str]:
        ''' Get roles for a USER ID as a list of strings

        If no user ID is provided, all existing roles are returned. Note that
        roles are case insensitive and 'USER' as well as 'ADMIN' being default
        roles always being present.

        Keyword arguments:
        user_id -- a valid positive user ID -OR- 0 for the roles of current
            user -OR- '' or None for all known roles
        '''

    @abstractmethod
    def hybrid_encrypt(
            self,
            data: bytes,
            roles: str | list[str]
            ) -> tuple[bytes, dict[int, bytes]]:
        ''' Hybrid encryption returning encrypted data and key blob dict

        The data will be encrypted with a generated symmetric key. This
        password will be encrypted, resulting in one key blob for every member
        of the mentioned roles. The key blobs are returned in a dictionary that
        is indexed by the corresponding USER IDs.

        All admins and yourself are always added to the encryption keys.

        Keyword arguments:
        data -- the data to encrypt
        roles -- the roles which shall be able to read the data

        Returns: a tuple of the encrypted bytes and a dictionary mapping the
            USER IDs to the key blobs.
        '''

    @abstractmethod
    def hybrid_decrypt(
            self,
            data: bytes,
            key_blob_dict: dict[int, bytes]
            ) -> bytes:
        ''' Hybrid decryption returning decrypted data

        Your USER ID must be included in the key blob dict. Your private
        assymetric encyption key will then be used to decrypt the symmetric key
        from the key blob. Afterwards, the data will be decrypted by this
        symmeric key.

        Keyword arguments:
        data -- the data to be decrypted
        key_blob_dict -- a dictionary of key blobs, indexed by USER ID
        '''
