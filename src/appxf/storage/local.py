# Copyright 2023-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import os.path

from .storage_to_bytes import CompactSerializer, Serializer, Storage, StorageToBytes


class LocalStorage(StorageToBytes):
    """Maintain files in a local path."""

    def __init__(
        self,
        file: str,
        path: str,
        serializer: type[Serializer] = CompactSerializer,
    ):
        # Ensure the path will exist
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        # Important: super().__init__() already utilizes the specific
        # implementation. Attributes must be available.
        super().__init__(
            name=file,
            location=path,
            serializer=serializer,
        )
        self._path = path

    @classmethod
    def get(
        cls,
        file: str,
        path: str,
        serializer: type[Serializer] = CompactSerializer,
    ) -> Storage:
        return super().get(
            name=file,
            location=path,
            storage_init_fun=lambda: LocalStorage(
                file=file, path=path, serializer=serializer
            ),
        )

    @classmethod
    def get_factory(
        cls, path: str, serializer: type[Serializer] = CompactSerializer
    ) -> Storage.Factory:
        return super().get_factory(
            location=path,
            storage_get_fun=lambda name: LocalStorage.get(
                file=name, path=path, serializer=serializer
            ),
        )

    def _get_file_path(self, create_dir: bool):
        if self._meta:
            path = os.path.join(self._path, ".meta")
            if create_dir and not os.path.exists(path):
                os.makedirs(path)
            return os.path.join(path, self._name + "." + self._meta)
        return os.path.join(self._path, self._name)

    def exists(self) -> bool:
        return os.path.exists(self._get_file_path(create_dir=False))

    def store_raw(self, data: bytes):
        with open(self._get_file_path(create_dir=True), "wb") as f:
            f.write(data)

    def load_raw(self) -> bytes:
        path = self._get_file_path(create_dir=False)
        if not os.path.exists(path):
            return b""
        with open(path, "rb") as f:
            return f.read()

    def _remove(self, file: str):
        full_path = os.path.join(self._path, file)
        if os.path.exists(full_path):
            os.remove(full_path)
