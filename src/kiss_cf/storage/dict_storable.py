
from typing import Any

from .storage import Storage, StorageMethodDummy
from .storable import Storable
from .serialize import serialize, deserialize


class DictStorable(Storable):
    ''' Store class state as dictionaty.

    By default implementation, it stores the classes __dict__ which contains
    all class fields. You may update _set_dict() and _get_dict() to store
    another dictionary or perform modifications.

    It is recommended that the deriving class applies a _version field. Onc a
    new version is introduced and you want to achieve compatibility, you can
    overload _set_dict().
    '''
    def __init__(self,
                 storage: Storage = StorageMethodDummy()
                 ):
        super().__init__(storage)

    def _get_dict(self) -> dict[str, Any]:
        data = self.__dict__.copy()
        # strip storage and settings
        del data['_storage']
        return data

    def _set_dict(self, data: dict[Any, Any]):
        self.__dict__.update(data)

    def _get_bytestream(self) -> bytes:
        data = self._get_dict()
        return serialize(data)

    def _set_bytestream(self, data: bytes):
        dict_data: dict[str, Any] = deserialize(data)
        self._set_dict(dict_data)
