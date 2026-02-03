# Copyright 2024-2026 the contributors of APPXF (github.com/alexander-rd/appxf)
# SPDX-License-Identifier: Apache-2.0
''' Provide a dummy serialization
'''

from .serializer import Serializer


class RawSerializer(Serializer):
    ''' Dummy serializer that does not change data '''

    @classmethod
    def serialize(cls, data: object) -> bytes:
        if not isinstance(data, bytes):
            raise TypeError('Input data must already be bytes')
        return data

    @classmethod
    def deserialize(cls, data: bytes) -> object:
        return data
