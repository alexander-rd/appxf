''' interface contract for stateful classes '''

from __future__ import annotations
from typing import TypeAlias, Union
from copy import deepcopy

# Restrictions for this interface contract originate from the Storable/Storage
# behavior:
#   * Pickle (CompactSerializer) is restricted to protect from unpickling
#     arbitrary objects.
#   * Text based serializers (like JSON) cannot store and restore arbitrary
#     objects. They may apply further limitations.
#
# Suppurted base types (medium risk for extensions but note that anything
# not being a string may need specific handling from serializers):
BaseType: TypeAlias = bool | int | float | bytes | str
# The type that is supported for get_state()/set_state():
#   * Dictionaries may contain BaseType as keys and recursively any StateType
#   * Iterables are restricted to BaseType (extensions may be feasible)
StateType: TypeAlias = Union[
    dict[BaseType, Union[BaseType, 'StateType', None]],
    list[BaseType | None], tuple[BaseType | None], set[BaseType | None],
    dict[str, 'StateType'], # explicit mention to resolve pylint typehint issues
    ]
# For testing, the type variable may be analyzed via __args__ to ensure
# coverage for serializers.

# Default implementation for get_state()/set_state() is based on the __dict__
# of a class and applies a type guard for error handling. This type guard does
# not verify the types within the container classes and uses a simplieifed
# TypeAlias:
StateTypeForTypeChecker: TypeAlias = Union[
    BaseType, list, tuple, set, dict
    ]
# The error class will just be normal TypeError
def type_guard_default(data: object) -> dict[str, StateType]:
    ''' type guard for Stateful default implementation '''
    if not isinstance(data, dict):
        raise TypeError(
            f'APPXF Stateful default implentation of get_state()/set_state() '
            f'uses a dict[str, StateType], you provided: '
            f'{data.__class__.__name__}')
    for key, value in data.items():
        if not isinstance(key, str):
            raise TypeError(
                f'APPXF Stateful default implentation of '
                f'get_state()/set_state() uses a dict[str, StateType], '
                f'you provided a key: {key} '
                f' of type {key.__class__.__name__}')
        if not isinstance(value, (StateTypeForTypeChecker)):
            raise TypeError(
                f'APPXF Stateful default implentation of '
                f'get_state()/set_state() uses a dict[str, StateType], '
                f'you provided a value for key={key} of type '
                f'{value.__class__.__name__}')
    return data

class Stateful():
    ''' base class supporting storing/restoring objects via dictionaries

    This class is an interface contract mainly utilized in the Storable/Storage
    implementation.
    '''

    # There is no particular __init__ required

    def get_state(self) -> StateType:
        ''' get object state

        The default implementation uses the class __dict__ which contains all
        class fields. You likely have to update this method for derived classes
        since not all entries in __dict__ will be part of the classes state.
        Especially aggregated classes whould typically be stripped.
        '''
        return type_guard_default(deepcopy(self.__dict__))

    def set_state(self, data: StateType):
        ''' Set object state

        The default implementation restores the classes __dict__ which contains
        all class fields. You may update this method to adapt the behavior.
        '''
        self.__dict__.update(type_guard_default(data))
