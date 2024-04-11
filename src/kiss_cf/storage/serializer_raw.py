''' Provide a dummy serialization
'''

from .serializer import Serializer, KissSerializerError


class RawSerializer(Serializer):
    ''' Dummy serializer that does not change data '''

    @classmethod
    def serialize(cls, data: object) -> bytes:
        if not isinstance(data, bytes):
            raise KissSerializerError('Input data must already be bytes')
        return data

    @classmethod
    def deserialize(cls, data: bytes) -> object:
        return data
