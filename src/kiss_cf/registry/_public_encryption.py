''' Provide public key encryption (to allow others access) '''

from __future__ import annotations
from typing import Any

from kiss_cf.storage import Storage, DictStorable
from kiss_cf.security import Security
from .registry import Registry


class PublicEncryption(DictStorable):
    def __init__(self,
                 storage_method: Storage,
                 security: Security,
                 registry: Registry,
                 # TODO: align default role nomenclature "user" versus "USER"
                 to_roles: str = 'USER'
                 ):
        super().__init__(storage_method)
        self._security = security
        self._registry = registry
        self._to_roles = to_roles
        self._keys: dict[bytes, bytes] = {}

    def _get_dict(self) -> dict[Any, Any]:
        return self._keys

    def _set_dict(self, data: dict[bytes, bytes]):
        self._keys = data

    # TODO: adapt encrypt() to rewrite public keys as integer user ID's from
    # registry. Upon decrypt() check if user ID is valid and abort already
    # there, otherwise: present security only with the one public key that
    # matters.

    def encrypt(self, data: bytes) -> bytes:
        pub_key_list = self._registry.get_encryption_keys(self._to_roles)
        data, keys = self._security.hybrid_encrypt(data, pub_key_list)
        self._keys = keys
        self.store()
        return data

    def decrypt(self, data: bytes) -> bytes:
        self.load()
        data = self._security.hybrid_decrypt(data, self._keys)
        return data
