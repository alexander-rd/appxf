''' signature behavior for authenticity '''

from __future__ import annotations
from typing import Any
from datetime import datetime
import uuid

from .storable import Storable
from .storage import Storage
from .serialize import serialize, deserialize


class MetaData():
    ''' Hold meta data '''

    def __init__(self):
        self._version = 1
        self.uuid: bytes = uuid.uuid4().bytes
        self.hash: bytes = b''
        self.timestamp: datetime | None = None

    @classmethod
    def from_bytes(cls, data: bytes) -> MetaData:
        ''' Construct signature data from bytes '''
        obj = cls()
        struct: dict[str, Any] = deserialize(data)
        obj.__dict__.update(struct)
        return obj

    def to_bytes(self) -> bytes:
        ''' Get bytes to store signature '''
        data = serialize(self.__dict__)
        return data


class MetaDataStorable(Storable):
    ''' Maintain meta data
    '''
    def __init__(self,
                 storage_method: Storage):
        super().__init__(storage_method)
        self._data = MetaData()

    @property
    def uuid(self):
        return self._data.uuid

    @uuid.setter
    def uuid(self, new_uuid):
        self._data.uuid = new_uuid

    def _get_bytestream(self) -> bytes:
        return self._data.to_bytes()

    def _set_bytestream(self, data: bytes):
        self._data = MetaData.from_bytes(data)
