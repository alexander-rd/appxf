''' signature behavior for authenticity '''

from abc import ABC, abstractmethod

from datetime import datetime
import uuid


class MetaData(ABC):
    ''' Hold meta data '''

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._version = 1
        self.uuid: bytes = uuid.uuid4().bytes
        self.hash: bytes = b''
        self.timestamp: datetime | None = None

    # Consider version handling via _get_state() and _set_state() when
    # extending this class.. ..which should then be done in MetaDataStorage.

    def new_content(self):
        self.timestamp = datetime.now()
        self.uuid = uuid.uuid4().bytes
        self.update()
        # TODO: hash not yet supported

    @abstractmethod
    def update(self):
        ''' Store updated meta data '''
