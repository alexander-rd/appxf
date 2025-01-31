''' Test all serializer classes '''

import pytest
import math

from abc import ABC, abstractmethod

from typing import get_origin, get_args, Union, ForwardRef
from types import UnionType

from kiss_cf import Stateful
from kiss_cf.storage import Serializer, JsonSerializer
from collections import OrderedDict

class DummyClassNotSerializable:
    ''' Just a custom classs that will not be serializeable '''

samples = [
    # strings with some special words and characters:
    'test', '', 'True', 'true', 'False', 'false',
    'NaN', 'nan', 'Infinity', 'infinity', '-Infinity',
    '!"§$%&/()=?', '`\'*\'_:;,.-#+',

    # basic types:
    True, False, None, float('infinity'), float('-infinity'), float('nan')
    -1, 1, 42, 1234567890, -1234567890,
    1.123456789, -1.123456789, 123456789.01, -123456789.01,

    # bytes:
    b'', b'1234', bytes('Hallo 12340', 'utf-8'),

    # simple list and dict:
    [1, 2, 3], {'A': 1, 'B': 2}, OrderedDict({'A': 3, 'B': 4}),

    # arbitrary elements types in containers:
    [True, 42, 1.25, 'some', None, b'a'],
    (True, 42, 1.25, 'some', None, b'a'),
    {True, 42, 1.25, 'some', None, b'a'},
    # arbitrary key and value types in dict:
    {True: True, 42:42, 3.14: 3.14, 'string': 'string', 'none': None, b'a': b'b'},
    # recursion of dict in dict:
    {'dict': {True: True, 42: 42, 3.14: 3.14, 'a':'a', b'b': b'C', 'none': None},
     'list': [True, 'some', None, 1.25, b'a'],
     'tuple': (True, 'some', None, 1.25, b'a'),
     'set': set([True, 'some', None, 1.25, b'a'])},
    # nested empty things:
    [{}, [], (), set(), [(set())], {'list-nest': [[[]]], 'tuple nest': (((()),),)}],
]

invalid_samples = [
    DummyClassNotSerializable(),
    {'A': DummyClassNotSerializable(), 'B': 42},
    {DummyClassNotSerializable(): 'invalid key'}
]

class BaseSerializerTest(ABC):
    @abstractmethod
    def _get_serializer(self) -> Serializer:
        ''' Return specific serializer for testing '''

    @pytest.mark.parametrize('value', samples)
    def test(self, value):
        print(f'Test for value: {value}')
        obj_bytes = self._get_serializer().serialize(value)
        if isinstance(self._get_serializer(), JsonSerializer):
            print(f'Result: {obj_bytes.decode()}')

        deserialized_value = self._get_serializer().deserialize(obj_bytes)
        if isinstance(value, float) and math.isnan(value):
            assert math.isnan(deserialized_value)
        else:
            assert deserialized_value == value

    @pytest.mark.parametrize('obj', invalid_samples)
    def test_invalid(self, obj):
        # serialize must not be possible and mention class name as well as
        # appropriate error message must be printed
        with pytest.raises(TypeError) as exc_info:
            self._get_serializer().serialize(obj)
        assert 'Cannot serialize' in str(exc_info)
        assert 'DummyClassNotSerializable' in str(exc_info)

def test_stateful_interface_contract():
    ''' Serializer tests must include all types from Stateful '''
    # we will cycle throught the types but also need the following helper for
    # recursions
    def verify_type_tested(this_type,
                           test_samples,
                           tree: list[type] | None = None):
        if tree is None:
            tree = []
        if not tree:
            tree.append(this_type)
        # resolve a forward references and string referenced types
        if str(this_type) in ["ForwardRef('DefaultStateType')", 'DefaultStateType']:
            this_type = Stateful.DefaultStateType
        # identify kind of type:
        type_origin = get_origin(this_type)
        type_args = get_args(this_type)
        # catch unions
        if type_origin is UnionType or type_origin is Union:
            for that_type in type_args:
                verify_type_tested(that_type, test_samples,
                                   tree + [that_type])
            return
        # we now extract the tested samples that match the origin or base type:
        def tree_to_str(tree):
            if len(tree) > 1:
                more = '\n -> '.join([str(item) for item in tree[1:]])
                return f'{tree[0]}: {more}'
            return str(tree[0])
        print(f'Testing type {tree_to_str(tree)}')
        type_base = this_type if type_origin is None else type_origin
        included = []
        for this_sample in test_samples:
            if isinstance(this_sample, type_base):
                included.append(this_sample)
        # fail if not empty
        assert included, (
            f'Type is not (fully) covered by samples. '
            f'Type tree: {tree_to_str(tree)}, '
            f'Current base type: {type_base} '
            f'with args {type_args}')

        # we are done if this_type was a basic type
        if type_origin is None:
            return
        # we are also done if the complex type was already recursed into:
        if type_origin in tree:
            return
        # if not, we need to iterate into them
        if len(type_args) == 1:
            # this is any simple container and we just jump into the container content types:
            if not isinstance(type_args[0], list):
                type_list = [type_args[0]]
            else:
                type_list = type_args[0]
            for that_type in type_list:
                verify_type_tested(
                    that_type,
                    [sample for container in included for sample in container],
                    tree+[type_origin, f'Element({that_type})'])
            return
        if type_origin in [dict]:
            # dict like classes need to iterate into the keys:
            if not isinstance(type_args[0], list):
                type_list = [type_args[0]]
            else:
                type_list = type_args[0]
            for that_type in type_list:
                verify_type_tested(
                    that_type,
                    [sample for some_dict in included for sample in some_dict.keys()],
                    tree+[type_origin, f'Key({that_type})'])
            # and into the arguments:
            if not isinstance(type_args[1], list):
                type_list = [type_args[1]]
            else:
                type_list = type_args[1]
            for that_type in type_list:
                verify_type_tested(
                    that_type,
                    [sample for some_dict in included for sample in some_dict.values()],
                    tree+[type_origin, f'Value({that_type})'])
            return

        assert False, (
            f'Failing: {this_type} as origin {type_origin} '
            f'with arguments {type_args}')


    # we cycle through the DefaultState type:
    for this_type in get_args(Stateful.DefaultStateType):
        verify_type_tested(this_type, samples)