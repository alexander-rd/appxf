''' Test all serializer classes '''
import pytest
import pickle

from appxf.storage import Serializer, CompactSerializer

from tests.storage.test_serializer_base import BaseSerializerTest, DummyClassNotSerializable

class TestJsonSerializer(BaseSerializerTest):
    def _get_serializer(self) -> Serializer:
        return CompactSerializer()

def test_serializer_safe_unpickle():
    # test the test implementation by an object that works
    obj = {'data': 42}
    obj_bytes = pickle.dumps(obj)
    assert obj == CompactSerializer.deserialize(obj_bytes)
    # manually pickle the undefined class
    obj = {'data': DummyClassNotSerializable}
    obj_bytes = pickle.dumps(obj)
    with pytest.raises(TypeError) as exc_info:
        CompactSerializer.deserialize(obj_bytes)
    assert 'Cannot deserialize' in str(exc_info)
    assert 'DummyClassNotSerializable' in str(exc_info)
