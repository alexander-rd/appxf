# Copyright 2024-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
''' signature behavior for authenticity '''

from datetime import datetime
import uuid


class MetaData():
    ''' Hold storage meta data

    Meta data is mainly required for synchonization algorithms.
    '''

    def __init__(self,
                 valid: bool = True,
                 state: dict | None = None):
        if state is not None:
            self.__dict__.update(state)
        else:
            self._version = 1
            self.uuid: bytes = uuid.uuid4().bytes
            self.hash: bytes = b''
            self.timestamp: str | None = None
            if valid:
                self.timestamp = datetime.now().isoformat()

    def get_state(self) -> dict:
        return self.__dict__

    # Consider version handling via _get_state() and _set_state() when
    # extending this class.. ..which should then be done in MetaDataStorage.
