# Copyright 2024-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
'''Storage to Raw Bytes

This module merges serializers with Storage as a basis for any file storage.
'''

# allow class name being used before being fully defined (like in same class):
from __future__ import annotations

from abc import ABC, abstractmethod

from .serializer import Serializer
from .serializer_compact import CompactSerializer
from .serializer_json import JsonSerializer
from .storage import AppxfStorageError, Storage


class StorageToBytes(Storage, ABC):
    '''Storage class with convertion to bytes as raw storage type'''

    def __init__(self, serializer: type[Serializer] = CompactSerializer, **kwargs):
        super().__init__(**kwargs)
        self._serializer = serializer

    # To allow meta files to specify the serialization type, the following
    # dictionary is used:
    _meta_serializer_dict: dict[str, type[Serializer]] = {}

    # This dict will be the SAME even in derived classses. The following
    # interface will allow the setting:
    @classmethod
    def set_meta_serializer(cls, meta: str, serializer: type[Serializer]):
        if meta in cls._meta_serializer_dict:
            raise AppxfStorageError(
                f'Serializer {cls._meta_serializer_dict[meta].__name__} is '
                f'already defined as serializer for {meta}'
            )
        cls._meta_serializer_dict[meta] = serializer

    # overloading the converion functions to apply the serializer
    def convert_from_raw(self, data: bytes) -> object:
        if data == b'':
            return None
        if self._meta in self._meta_serializer_dict:
            return self._meta_serializer_dict[self._meta].deserialize(data)
        return self._serializer.deserialize(data)

    def convert_to_raw(self, data: object) -> bytes:
        if self._meta in self._meta_serializer_dict:
            return self._meta_serializer_dict[self._meta].serialize(data)
        return self._serializer.serialize(data)

    @abstractmethod
    def store_raw(self, data: bytes):
        '''Store interface to the actual storage'''

    @abstractmethod
    def load_raw(self) -> bytes:
        '''Load interface to the actual storage'''


# define serializer for MetaData:
StorageToBytes.set_meta_serializer('meta', JsonSerializer)
