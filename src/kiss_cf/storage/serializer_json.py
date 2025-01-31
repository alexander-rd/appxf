import base64
import json
import re

from collections import OrderedDict

from .serializer import Serializer

# Alternatives
#
# There is jsonpickler to support basically any type. However, like with the
# CompactSerializer and pickle, the supported types must be constrained to
# remain secure. Also, what is the point in a human readable JSON that starts
# storing arbitrary complex objects and containing extra notations? "keep it
# simple" concerning the maintained data structures in user application was
# guiding the design. Let's see when we need to face pandas or numpy.
#
# Other libraries where checked but none of them supported arbitrary key types
# where I wanted to have bytes as a valid key type. There is also a PR for json
# to enable key conversion https://github.com/python/cpython/pull/117392. But
# this is not in, yet. This was the main reason to TRANSFORM THE OBJECTS before
# encoding and after decoding LEADING TO A FULL COPY of the object.
#
# For the above reasons, the JsonSerializer is not an efficient implementation.


class JsonSerializer(Serializer):
    ''' Store class dictionary as human readable JSON

    JsonSerializer always uses OrderedDict when decoding. Encoding to JSON and
    decoding again will alter a dict into an OrderedDict (which is a derivative
    of dict).
    '''
    # Since OrderedDict is always used for decoding, dict and OrderedDict are
    # not distinguished when encoding.

    @classmethod
    def serialize(cls, data: object) -> bytes:
        json_out = json.dumps(cls.encode_transform(data),
                              indent=4, separators=(',', ': '))
        # postprocessing to remove newlines for custom type JSON objects like
        # "__bytes__":
        json_out = re.sub(r'\{\s*(\S+):\s*(\S+)\s*\}', r'{\1: \2}', json_out)
        # and for two-element arrays that are used for dictionaries with
        # non-trivial key types:
        json_out = re.sub(r'\[\s*(\S+),\s*(\S+)\s*\]', r'[\1, \2]', json_out)
        return bytes(json_out, encoding='utf-8')

    @classmethod
    def deserialize(cls, data: bytes):
        return cls.decode_transform(
            json.loads(
                data.decode('utf-8'),
                object_pairs_hook=OrderedDict
                ))

    SimpleTypes = (bool, int, float, str, type(None))

    @classmethod
    def encode_transform(cls,
                         obj: object,
                         log_tree: list | None = None) -> object:
        ''' Transform object for JSON encoding

        This function will alter the dictionary to consist only of OrderedDict,
        list and JSON supported base types.
        '''
        if log_tree is None:
            log_tree = ['root']

        if isinstance(obj, dict):
            if all(isinstance(key, cls.SimpleTypes) for key in obj.keys()):
                return {
                    key: cls.encode_transform(value, log_tree + [key])
                    for key, value in obj.items()}
            dict_type = '__dict__'
            return {dict_type: [
                [cls.encode_transform(key, log_tree+[key]),
                 cls.encode_transform(value, log_tree+[f'value for {key}'])]
                for key, value in obj.items()]}


        if isinstance(obj, (list, tuple, set)):
            encoded_list = [
                cls.encode_transform(element, log_tree + [str(element)])
                for element in obj]
            if type(obj) == list:
                return encoded_list
            if type(obj) == set:
                return {'__set__': encoded_list}
            if type(obj) == tuple:
                return {'__tuple__': encoded_list}
        if isinstance(obj, bytes):
            return {'__bytes__': cls._encode_bytes(obj)}
        if isinstance(obj, cls.SimpleTypes):
            return obj
        raise TypeError(f'Cannot serialize type {type(obj)} trace: {log_tree}.')

    @classmethod
    def decode_transform(cls,
                         obj: object,
                         log_tree: list | None = None) -> object:
        ''' Transform object after JSON decoding

        Reverts the transformations of encode_transform.
        '''
        if log_tree is None:
            log_tree = ['root']

        if (isinstance(obj, dict) and len(obj) == 1):
            key, value = next(iter(obj.items()))
            if key == '__bytes__':
                return cls._decode_bytes(value)
            if key == '__tuple__':
                return tuple(cls.decode_transform(value, log_tree + ['tuple']))
            if key == '__set__':
                return set(cls.decode_transform(value, log_tree + ['set']))
            #if key == '__OrderedDict__':
            #    # nothing to do, the JSON object within was already decoded as OrderedDict:
            #    return value
            if key == '__dict__':
                # this was a dict with non trivial key types that come as list
                # of two-element lists:
                decode_dict = OrderedDict(
                    (cls.decode_transform(dict_element[0], log_tree+[key]),
                     cls.decode_transform(dict_element[1], log_tree+[f'value for key'])
                     )
                    for dict_element in value)
                return decode_dict

        if isinstance(obj, dict):
            for key, value in obj.items():
                obj[key] = cls.decode_transform(value, log_tree + [key])
            return obj
        if isinstance(obj, list):
            return [cls.decode_transform(element, log_tree + [str(element)]) for element in obj]
        if isinstance(obj, cls.SimpleTypes):
            return obj
        # the following error should never be reached since a decoded JSON will
        # only containt he above checked types
        raise TypeError(f'Cannot decode object {obj} of type {obj}, trace: {log_tree}') # pragma: no cover

    @classmethod
    def _encode_bytes(cls, obj: bytes) -> str:
        return base64.b64encode(obj).decode('utf-8')
    @classmethod
    def _decode_bytes(cls, obj: str) -> bytes:
        return base64.b64decode(obj)
