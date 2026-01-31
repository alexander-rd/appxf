''' Test all serializer classes '''
import pytest

from appxf_private.storage import JsonSerializer, Serializer

from tests.storage.test_serializer_base import BaseSerializerTest

class TestJsonSerializer(BaseSerializerTest):
    def _get_serializer(self) -> Serializer:
        return JsonSerializer()
