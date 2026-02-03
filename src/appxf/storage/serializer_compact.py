# Copyright 2024-2026 the contributors of APPXF (github.com/alexander-rd/appxf)
# SPDX-License-Identifier: Apache-2.0
''' Provide a serialization

This is a small wrapper around pickle to ensure "safe" unpacking the bytes from
the file.

"safe": Unpickling poses a risk of code injection. This is avoided in
deserialize() via RestrictedUnpickler according to pickle documentation:
https://docs.python.org/3/library/pickle.html#restricting-globals.
'''

import pickle
import io
from collections import OrderedDict

from .serializer import Serializer

supported_types = {
    int, float, str, bytes,
    list, tuple, set, dict, OrderedDict, type(OrderedDict),
    bool, type(None)}


class _RestrictedUnpickler(pickle.Unpickler):
    '''Class to disable unwanted symbols.'''
    def find_class(self, module, name):
        # Only allow safe classes from builtins.
        if module == 'collections' and name == 'OrderedDict':
            return OrderedDict
        # Forbid everything else.
        raise TypeError(
            f'Cannot deserialize "{module}.{name}". To protect from code '
            f'injection, serialization/deserialization was limited in APPXF')


class _RestrictedPickler(pickle.Pickler):
    def persistent_id(self, obj):
        # Catch types that are not supported
        if type(obj) not in supported_types:
            raise TypeError(f'Cannot serialize {obj} of type {type(obj)}')
        # Just return none since nothing special is required
        return None


class CompactSerializer(Serializer):
    ''' Use a raw byte based storage '''

    # In case this class is adapted, consider the following design goals that
    # were not evaluated in detail when selecting pickle:
    #   * wide support of data types
    #   * low footprint on storing objects
    #
    # Protection from code injection was added and would need to be
    # reconsidered when adapting the code.

    @classmethod
    def serialize(cls, data: object) -> bytes:
        with io.BytesIO() as f:
            _RestrictedPickler(f).dump(data)
            return f.getvalue()

    @classmethod
    def deserialize(cls, data: bytes) -> object:
        return _RestrictedUnpickler(io.BytesIO(data)).load()
