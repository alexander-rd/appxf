# Copyright 2024-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
"""Provide public key encryption (to allow others access)"""

from __future__ import annotations

from typing import Any

from appxf.storage import Storable, Storage

from ._registry_base import RegistryBase


class PublicEncryption(Storable):
    def __init__(
        self, storage: Storage, registry: RegistryBase, to_roles: str = "user", **kwargs
    ):
        super().__init__(storage, **kwargs)
        self._registry = registry
        self._to_roles = to_roles
        self._key_blob_dict: dict[int, bytes] = {}

    def get_state(self) -> dict[Any, Any]:
        return self._key_blob_dict

    def set_state(self, data: dict[bytes, bytes]):
        self._key_blob_dict = data

    def encrypt(self, data: bytes) -> bytes:
        data, key_blob_dict = self._registry.hybrid_encrypt(data, self._to_roles)
        self._key_blob_dict = key_blob_dict
        self.store()
        return data

    def decrypt(self, data: bytes) -> bytes:
        self.load()
        return self._registry.hybrid_decrypt(data, self._key_blob_dict)
