''' signature behavior for authenticity '''

from __future__ import annotations
from datetime import datetime
import uuid

from .storage import Storage
from .json_dict_storable import JsonDictStorable


class MetaData(JsonDictStorable):
    ''' Hold meta data '''

    def __init__(self, storage: Storage):
        super().__init__(storage=storage)
        self._version = 1
        self.uuid: bytes = uuid.uuid4().bytes
        self.hash: bytes = b''
        self.timestamp: datetime | None = None

    # Consider version handling via _get_dict() and _set_dict() when extending
    # this class.
