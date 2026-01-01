''' Provide public key encryption (to allow others access) '''

from __future__ import annotations
from typing import Any

from kiss_cf.storage import Storage, Storable
from kiss_cf.security import Security
from ._registry_base import RegistryBase


class PublicEncryption(Storable):
    def __init__(self,
                 storage: Storage,
                 security: Security,
                 registry: RegistryBase,
                 to_roles: str = 'user',
                 **kwargs):
        super().__init__(storage, **kwargs)
        self._security = security
        self._registry = registry
        self._to_roles = to_roles
        self._key_blob_dict: dict[int, bytes] = {}

    def get_state(self) -> dict[Any, Any]:
        return self._key_blob_dict

    def set_state(self, data: dict[bytes, bytes]):
        self._key_blob_dict = data


    def encrypt(self, data: bytes) -> bytes:
        pub_key_dict = self._registry.get_encryption_key_dict(self._to_roles)
        # always add own key:
        if self._registry.user_id not in pub_key_dict:
            pub_key_dict[self._registry.user_id] = (
                self._security.get_encryption_public_key())

        data, key_blob_dict = self._security.hybrid_encrypt(data, pub_key_dict)
        self._key_blob_dict = key_blob_dict
        self.store()
        return data

    def decrypt(self, data: bytes) -> bytes:
        self.load()
        # identify key blob
        if self._registry.user_id not in self._key_blob_dict:
            raise ValueError(
                f'Current user id {self._registry.user_id} is not included'
                f'in available key blobs. Available: '
                f'{self._key_blob_dict.keys()}')
        key_blob = self._key_blob_dict[self._registry.user_id]

        data = self._security.hybrid_decrypt(data=data, key_blob=key_blob)
        return data
