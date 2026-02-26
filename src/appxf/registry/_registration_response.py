# Copyright 2024-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
''' Registration Response based on bytes

The class RegistrationResponse serializes and deserializes a registration
response form admin to user. It is expected to be handled as an encrypted file
which is not in scope of this class.
'''
from __future__ import annotations

from typing import Any, TypedDict

from appxf.storage import CompactSerializer

# TODO: apply DictStorable here but keep the get_bytes interface.


class AppxfExceptionRegistrationResponse(Exception):
    ''' Error with handling a registration response '''


class RegistrationResponseData(TypedDict):
    version: int
    user_id: int
    user_db: bytes
    config_sections: dict[str, dict[str, Any]]


class RegistrationResponse():
    def __init__(self, data: RegistrationResponseData, **kwargs):
        super().__init__(**kwargs)
        self._data = data

    @property
    def user_id(self):
        return self._data['user_id']

    @property
    def user_db_bytes(self):
        return self._data['user_db']

    @property
    def config_sections(self):
        return self._data['config_sections']

    @classmethod
    def new(cls,
            user_id: int,
            user_db: bytes,
            config_sections: dict[str, dict[str, Any]],
            ) -> RegistrationResponse:
        data: RegistrationResponseData = {
            'version': 1,
            'user_id': user_id,
            'user_db': user_db,
            'config_sections': config_sections
            }
        return cls(data)

    @classmethod
    def from_response_bytes(cls,
                            registration_response: bytes
                            ) -> RegistrationResponse:
        data: RegistrationResponseData = (
            CompactSerializer.deserialize(registration_response))
        return cls(data)

    def get_response_bytes(self) -> bytes:
        ''' Get serialized bytes for sending to user '''
        return CompactSerializer.serialize(self._data)
