''' interface contract for stateful classes '''
from __future__ import annotations
from copy import deepcopy
from typing import TypeAlias, Union


class Stateful():
    ''' base for classes that can provide and restore their state

    This class is an interface contract which is mainly utilized in the
    Storable/Storage implementation with it's default implementation.

    Attributes:
        attributes: list of attributes that shall be exported or imported if
            any attribute is listed, no other attribute would be exported or
            imported
        attribute_mask: attributes that should not be exported or imported
    '''

    # There is no particular __init__ required but the deriving class should to
    # update the attribute_mask:
    attribute_mask: list[str] = []
    # or the attributes list:
    attributes: list[str] = []
    # They are used for the default implementaiton of get_state()/set_state().

    def get_state(self) -> object:
        ''' get object state

        See _get_state_default() for the default implementation with narrowed
        types.
        '''
        return self._get_state_default()

    def set_state(self, data: object):
        ''' set object state

        See _set_state_default() for the default implementation with narrowed
        types.
        '''
        self._set_state_default(data)

    ##########################
    ## Default Implementation
    #/
    #
    # Restrictions for this interface contract are motivated by the Storable
    # behavior (storage module):
    #   * Pickle (CompactSerializer) is restricted to protect from unpickling
    #     arbitrary objects.
    #   * Text based serializers (like JSON) cannot store and restore arbitrary
    #     objects. They may apply further limitations.
    #
    # Supported base types (medium risk for extensions but note that anything
    # not being a string may need specific handling from serializers):
    DefaultBaseType: TypeAlias = bool | int | float | bytes | str
    # The type that is supported for get_state()/set_state():
    #   * Dictionaries may contain BaseType as keys and recursively any
    #     StateType
    #   * Iterables are restricted to BaseType (extensions may be feasible)
    DefaultStateType: TypeAlias = Union[
        DefaultBaseType | None,
        dict[DefaultBaseType, Union[DefaultBaseType, 'DefaultStateType', None]],
        list[DefaultBaseType | None], tuple[DefaultBaseType | None], set[DefaultBaseType | None],
        dict[str, 'DefaultStateType'], # explicit mention to resolve pylint typehint issues
        ]
    # For testing, the type variable may be analyzed via __args__ to ensure
    # coverage for serializers.

    # Default implementation for get_state()/set_state() is based on the
    # __dict__ of a class and applies a type guard for error handling. This
    # type guard does not verify the types within the container classes and
    # uses a simplieifed TypeAlias:
    StateTypeDefaultForTypeCheck: TypeAlias = Union[
        DefaultBaseType, list, tuple, set, dict
        ]
    # The error class will just be normal TypeError
    @classmethod
    def _type_guard_default(cls, data: object) -> dict[str, DefaultStateType]:
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
            if not isinstance(value, (Stateful.StateTypeDefaultForTypeCheck)):
                raise TypeError(
                    f'APPXF Stateful default implentation of '
                    f'get_state()/set_state() uses a dict[str, StateType], '
                    f'you provided a value for key={key} of type '
                    f'{value.__class__.__name__}')
        return data

    def _get_state_default(self) -> Stateful.DefaultStateType:
        ''' get object state

        The default implementation uses the class __dict__ which contains all
        class fields. You likely have to update this method for derived classes
        since not all entries in __dict__ will be part of the classes state.
        Especially aggregated classes whould typically be stripped.
        '''
        if self.attributes:
            data = {key: deepcopy(value)
                    for key, value in self.__dict__.items()
                    if key in self.attributes}
        else:
            data = deepcopy(self.__dict__)
        # attribute_mask always has to be applied in case of mixed usage of
        # attribute_mask and attributes:
        for key in self.attribute_mask:
            if key in data:
                data.pop(key)
        return self._type_guard_default(data)

    def _set_state_default(self, data: object):
        ''' Set object state

        The default implementation restores the classes __dict__ which contains
        all class fields. You may update this method to adapt the behavior.
        '''
        data = Stateful._type_guard_default(deepcopy(data))
        if self.attributes:
            for key in data.keys():
                if key not in self.attributes:
                    data.pop(key)
        # attribute mask always needs to apply in case of mixed usage of
        # attribute_mask and attributes:
        for key in self.attribute_mask:
            if key in data:
                data.pop(key)
        self.__dict__.update(data)
