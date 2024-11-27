from collections.abc import Iterator
from typing import Any
import base64
import json

from .serializer import Serializer, KissSerializerError

# TODO: testing may show problems with int/float. As soon as this happens, this
# implementation should start being based on properties.

# Following restrictions in contrast to CompactSerializer:
#   * tuple is not (yet) supported, it would deserialize into a list
#   * set is generally not JSON serializable
supported_types = {
    int, float, str, bytes,
    list, dict,
    bool, type(None)}
# Additional restrictions, not by the supported types:
#   * non-string


class _RestrictedJsonEncoder(json.JSONEncoder):
    def _type_check(self, o: Any):
        if type(o) not in supported_types:
            raise KissSerializerError(
                f'Cannot serialize {type(o)}, '
                f'supported are: {supported_types}')
        # Ensure that all keys of a dict are strings. Decoding would not work
        # properly, otherwise
        if isinstance(o, dict):
            if not all(isinstance(key, str) for key in o.keys()):
                raise KissSerializerError(
                    f'Cannot serialize: keys must be str but are {list(o.keys())}. '
                    f'Deserializing would not work as expected.')

    def default(self, o: Any) -> Any:
        if isinstance(o, bytes):
            return {'__bytes__': base64.b64encode(o).decode('utf-8')}
        self._type_check(o)
        return super().default(o)

    def encode(self, o: Any) -> str:
        self._type_check(o)
        return super().encode(o)

    def iterencode(self, o: Any, _one_shot: bool = False) -> Iterator[str]:
        self._type_check(o)
        return super().iterencode(o, _one_shot)


class JsonSerializer(Serializer):
    ''' Store class dictionary as human readable JSON

    Comments from DictStorable apply likewise to JsonDictStorable.

    Additionally, JSON needs to serialize all data types. The data types are
    taken from the current values of the dictionaries. You have to:
      * always initialize all fields with a rigth data type
      * keep the data types consistent at all times
    '''
    @classmethod
    def _decode_custom(cls, data: dict[str, Any]) -> Any:
        if '__bytes__' in data:
            return base64.b64decode(data['__bytes__'])
        return data

    @classmethod
    def serialize(cls, data: object) -> bytes:
        try:
            json_out = json.dumps(data,
                                  cls=_RestrictedJsonEncoder,
                                  indent=4, separators=(',', ': '))
        except TypeError as error:
            message = str(error) + (
                ' - JsonSerializer from kiss_cf includes some conversions '
                'before storing as JSON. The one mentioned is not '
                'supported.')
            raise TypeError(message)

        return bytes(json_out, encoding='utf-8')

    @classmethod
    def deserialize(cls, data: bytes):
        return json.loads(
            data.decode('utf-8'),
            object_hook=cls._decode_custom)
