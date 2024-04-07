from kiss_cf.storage.dict_storable import DictStorable
from kiss_cf.storage.storage import Storage, StorageMethodDummy


import base64
import json
from typing import Any

# TODO: testing may show problems with int/float. As soon as this happens, this
# implementation should start being based on properties.


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

    def _encode_custom(self, value: Any):
        if type(value) is bytes:
            return {'__bytes__': base64.b64encode(value).decode('utf-8')}
        return value

    def _decode_custom(self, data: dict[str, Any]) -> Any:
        if '__bytes__' in data:
            return base64.b64decode(data['__bytes__'])
        return data

    def _get_bytestream(self) -> bytes:
        data = self._get_dict()

        try:
            json_out = json.dumps(data,
                                  default=self._encode_custom,
                                  indent=4, separators=(',', ': '))
        except TypeError as error:
            message = str(error) + (
                ' - JsonStorable from kiss_cf includes some conversions '
                'before storing as JSON. The one mentioned is not '
                'supported.')
            raise TypeError(message)

        return bytes(json_out, encoding='utf-8')

    def _set_bytestream(self, data: bytes):
        dict_data: dict[str, Any] = json.loads(
            data.decode('utf-8'),
            object_hook=self._decode_custom)
        self._set_dict(dict_data)
