from kiss_cf.storage.dict_storable import DictStorable
from kiss_cf.storage.storage import Storage, StorageMethodDummy


import base64
import json
from typing import Any

# TODO: testing will show problems with int/float. As soon as this happens,
# this implementation should start being based on properties.

# TODO: the conversions will be problematic as soon as (1) users don't set data
# according to default data types or (2) they may want to apply type unions
# like: str | None. Only solution: catch this as good as possible on writing.

class JsonDictStorable(DictStorable):
    ''' Store class dictionary as human readable JSON

    Comments from DictStorable apply likewise to JsonDictStorable.

    Additionally, JSON needs to serialize all data types. The data types are
    taken from the current values of the dictionaries. You have to:
      * always initialize all fields with a rigth data type
      * keep the data types consistent at all times
    '''
    def __init__(self,
                 storage: Storage = StorageMethodDummy()
                 ):
        super().__init__(storage)

    def _serialize_field(self, value: Any) -> Any:
        if type(value) is bytes:
            return base64.b64encode(value).decode('utf-8')
        return value

    def _deserialize_field(self, value: Any, default_value: Any):
        if type(default_value) is bytes:
            return base64.b64decode(value)
        return value

    def _get_bytestream(self) -> bytes:
        data = self._get_dict()

        data = {
            key: self._serialize_field(value)
            for key, value in data.items()}
        try:
            json_out = json.dumps(data, indent=4, separators=(',', ': '))
        except TypeError as error:
            message = str(error) + (
                ' - JsonStorable from kiss_cf includes some conversions before '
                'storing as JSON. The one mentioned is not supported.')
            raise TypeError(message)

        return bytes(json_out, encoding='utf-8')

    def _set_bytestream(self, data: bytes):
        dict_data: dict[str, Any] = json.loads(data.decode('utf-8'))
        dict_data = {
            key: self._deserialize_field(value, self.__dict__[key])
            for key, value in dict_data.items()}
        self._set_dict(dict_data)
