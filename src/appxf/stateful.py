# Copyright 2025-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
''' interface contract for stateful classes '''
from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from typing import TypeAlias, Union


class Stateful():
    ''' base for classes capable of providing and restoring their state

    This class is an interface contract which is utilized in implementations
    for Options and Storable/Storage with it's default implementation.

    Attributes:
        attributes: list of attributes that shall be exported or imported if
            any attribute is listed, no other attribute would be exported or
            imported
        attribute_mask: attributes that should not be exported or imported
    '''

    # init with kwargs is required to allow coorperative inheritance via
    # super().__init__(**kwargs).
    def __init__(self, **kwargs):
        pass

    # There is no particular __init__ required but the deriving class should
    # update the attribute_mask:
    attribute_mask: list[str] = []
    # or the attributes list:
    attributes: list[str] = []
    # They are used for the default implementaiton of get_state()/set_state().

    def get_state(self, **kwarg) -> object:
        ''' get object state

        See _get_state_default() for the default implementation with narrowed
        types.
        '''
        return self._get_state_default(**kwarg)

    def set_state(self, data: object, **kwarg):
        ''' set object state

        See _set_state_default() for the default implementation with narrowed
        types.
        '''
        self._set_state_default(data, **kwarg)

    # ######################## Default Implementation /
    #
    # Restrictions for this interface contract are motivated by the Storable
    # behavior (storage module):
    #   * Pickle (CompactSerializer) is restricted to protect from unpickling
    #     arbitrary objects.
    #   * Text based serializers (like JSON) cannot store and restore arbitrary
    #     objects without sacrificing human readability.
    #
    # Supported base types (medium risk for extensions since almost all
    # extensions will require specific handling from serializers):
    DefaultBaseType: TypeAlias = bool | int | float | bytes | str
    # The type that is supported for get_state()/set_state():
    #   * Dictionaries may contain BaseType as keys and recursively any
    #     StateType
    DefaultStateType: TypeAlias = Union[
        DefaultBaseType | None,
        dict[DefaultBaseType,
             Union[DefaultBaseType, 'DefaultStateType', None]],
        list[Union['DefaultStateType', None]],
        tuple[Union['DefaultStateType', None]],
        set[Union[DefaultBaseType, None]],  # set must be hashable
        dict[str, 'DefaultStateType'],  # explicit to resolve pylint issues
        ]
    # For testing, the type variables are be analyzed via get_origin() and
    # get_args() to ensure coverage for serializers.

    # Default implementation for get_state()/set_state() is based on the
    # __dict__ of a class and applies a type guard for error handling. This
    # type guard does not verify the types within the container classes and
    # uses a simplified TypeAlias:
    StateTypeDefaultForTypeCheck: TypeAlias = Union[
        DefaultBaseType, list, tuple, set, dict
        ]

    # The error class will just be normal TypeError
    @classmethod
    def type_guard_default(cls, data: object) -> dict[str, DefaultStateType]:
        ''' type guard for Stateful default implementation '''
        if not isinstance(data, dict):
            raise TypeError(
                f'APPXF Stateful default implentation of '
                f'get_state()/set_state() uses a '
                f'dict[str, StateType], you provided: '
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

    def get_default_state_attributes(self,
                                     attributes: list[str] | None = None,
                                     attribute_mask: list[str] | None = None
                                     ) -> list[str]:
        ''' get states for get_state()/set_state()

        This function is also used internally for _get_state_default() and
        _set_state_default(). It returns the list of attributes either based on
        attributes and attribute_mask lists from the input parameters (if not
        None) or from the corresponding class variables (parameters are None).
        In case attributes input parameter is None and the class attributes
        list is empty, the keys in __dict__ will be used.
        '''
        # get defined attributes, if not overwritten:
        if attributes is not None:
            out_attributes = attributes
        elif self.attributes:
            out_attributes = self.attributes
        else:
            # input parameter is None and class attributes is empty -> get
            # attributes from __dict__:
            out_attributes = list(self.__dict__.keys())

        # get the right mask and apply:
        if attribute_mask is None:
            attribute_mask = self.attribute_mask
        # return attribute list
        return [attr for attr in list(dict.fromkeys(out_attributes)) if
                attr not in attribute_mask]
        # compile state from attributes with error handling and return

    def _get_state_default(self,
                           attributes: list[str] | None = None,
                           attribute_mask: list[str] | None = None
                           ) -> OrderedDict[str, Stateful.DefaultStateType]:
        ''' get object state - default implementation

        See _get_default_state_attributes() for the considered attributes. The
        values are obtained via getattr(). Note that the class must take care
        of eventually applying deepcopy().

        attributes and attribute_mask replaces the corresponding class
        settings.
        '''
        attributes = self.get_default_state_attributes(
            attributes=attributes,
            attribute_mask=attribute_mask)
        # compile state from attributes with error handling and return
        data = OrderedDict()
        for key in attributes:
            if not hasattr(self, key):
                raise TypeError(
                    f'Class {self.__class__} does not have attribute '
                    f'{key} for get_state()]')
            data[key] = deepcopy(getattr(self, key))
        return self.type_guard_default(data)

    def _set_state_default(self,
                           data: object,
                           attributes: list[str] | None = None,
                           attribute_mask: list[str] | None = None):
        ''' set object state - default implementation

        See _get_default_state_attributes() for the considered attributes. The
        values are written via setattr(). Note that the class must take care of
        eventually applying deepcopy().

        attributes and attribute_mask replaces the corresponding class
        settings.
        '''
        data = Stateful.type_guard_default(deepcopy(data))
        attributes = self.get_default_state_attributes(
            attributes=attributes, attribute_mask=attribute_mask)
        for attr in data:
            if attr not in attributes:
                raise Warning(
                    f'State for set_state() of {self.__class__} '
                    f'includes attribute {attr} which is not expected - '
                    f'expected are {attributes} - ignoring this key.'
                    f'Check documentation for call stack to identify wrong '
                    'options to attributes or atribute_mask.'
                )
            setattr(self, attr, data[attr])
