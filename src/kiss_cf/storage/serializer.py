''' Class definitions for storage handling. '''

from abc import ABC, abstractmethod


class Serializer(ABC):
    ''' Provide serialize and deserialize functionality '''

    @classmethod
    @abstractmethod
    def serialize(cls, data: object) -> bytes:
        ''' Provide bytes from python object

        Consider include a version number in your object data in case
        you change your stored data format later.
        '''

    @classmethod
    @abstractmethod
    def deserialize(cls, data: bytes) -> object:
        ''' Restore Python object from bytes

        Consider include a version number in your object data in case
        you change your stored data format later.'''
