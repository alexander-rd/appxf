''' Test all serializer classes '''

import pytest
import math
from itertools import product
import pickle

from kiss_cf.storage import Serializer, CompactSerializer, JsonSerializer, KissSerializerError


class DummyClassNotSerializable:
    ''' Just a custom classs that will not be serializeable '''

serializers = [CompactSerializer, JsonSerializer]
objects_both = [
    'test', '', 'True', 'true', 'False', 'false',
    'NaN', 'nan', 'Infinity', 'infinity', '-Infinity',
    '!"§$%&/()=?', '`\'*\'_:;,.-#+',
    True, False, None, float('infinity'), float('-infinity'), float('nan')
    -1, 1, 42, 1234567890, -1234567890,
    1.123456789, -1.123456789, 123456789.01, -123456789.01,
    b'', b'1234', bytes('Hallo 12340', 'utf-8'),
    [1, 2, 3], {'A': 1, 'B': 2},
]
# Objects only supported by raw but not JSON
objects_raw = [
    # [0-1]: no tuples or sets
    (1, 2, 3), {1, 2, 3},
    # [2-3]: no dicts with non-string keys:
    {1: 'A', 2: 'B'}, {b'a': 1, b'b': 2},
]

type_test_param = (list(product(serializers, objects_both)) +
                   list(product([CompactSerializer], objects_raw)))
@pytest.mark.parametrize('serializer, value', type_test_param)
def test_serializer_types(serializer: Serializer, value):
    print(f'Test for value: {value}')
    obj_bytes = serializer.serialize(value)
    deserialized_value = serializer.deserialize(obj_bytes)
    if isinstance(value, float) and math.isnan(value):
        assert math.isnan(deserialized_value)
    else:
        assert deserialized_value == value

objects_invalid = [
    DummyClassNotSerializable(),
    {'A': DummyClassNotSerializable(), 'B': 42}]
@pytest.mark.parametrize('serializer, obj', product(serializers, objects_invalid))
def test_serializer_invalid_class(serializer: Serializer, obj):
    # serialize must not be possible and mention class name as well as
    # appropriate error message must be printed
    with pytest.raises(KissSerializerError) as exc_info:
        serializer.serialize(obj)
    assert 'Cannot serialize' in str(exc_info)
    assert 'KissSerializerError' in str(exc_info)

@pytest.mark.parametrize('value', objects_raw)
def test_serializer_json_not_supported(value):
    # serialize must not be possible and mention class name as well as
    # appropriate error message must be printed
    print(f'Test for value: {value}')
    with pytest.raises((KissSerializerError, TypeError)) as exc_info:
        JsonSerializer.serialize(value)
    print(f'Exception text: {exc_info}')
    if isinstance(value, dict):
        # Dicts must use str as key
        assert 'keys must be' in str(exc_info)
        assert 'str' in str(exc_info)
    else:
        assert 'Cannot serialize' in str(exc_info)
        assert str(type(value)) in str(exc_info)

def test_serializer_safe_unpickle():
    # test the test implementation by an object that works
    obj = {'data': 42}
    obj_bytes = pickle.dumps(obj)
    assert obj == CompactSerializer.deserialize(obj_bytes)
    # manually pickle the undefined class
    obj = {'data': DummyClassNotSerializable}
    obj_bytes = pickle.dumps(obj)
    with pytest.raises(KissSerializerError) as exc_info:
        CompactSerializer.deserialize(obj_bytes)
    assert 'Cannot deserialize' in str(exc_info)
    assert 'DummyClassNotSerializable' in str(exc_info)
