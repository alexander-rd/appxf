''' interface contract for stateful classes '''
from __future__ import annotations
from copy import deepcopy
from typing import TypeAlias, Union


class Stateful():
    ''' base for classes that can provide and restore their state

    This class is an interface contract which is utilized in implementations
    for Options and Storable/Storage with it's default implementation.

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

    def _get_default_state_attributes(self,
                                     overwrite_attributes: list[str] | None = None,
                                     additional_attribute_mask: list[str] | None = None):
        ''' get states for get_state()/set_state()

        This function is also used internally for _get_state_default() and
        _set_state_default(). If you have attributes defined in class (not
        empty) or overwrite_attributes is not None, those lists are taken as
        the basis. If no basis can be derived from there, the list of
        attributes is taken from the object's __dict__. From this base list,
        any attribute from class attribute_mask or additional_mask is removed.
        '''
        # get defined attributes, if not overwritten:
        attributes = self.attributes
        if overwrite_attributes is not None:
            attributes = overwrite_attributes
        if not attributes:
            attributes = list(self.__dict__.keys())
        # get the right mask and apply:
        if additional_attribute_mask is None:
            additional_attribute_mask = []
        # return attribute list
        return [attr for attr in attributes if (
            attr not in self.attribute_mask and
            attr not in additional_attribute_mask
            )]
        # compile state from attributes with error handling and return

    def _get_state_default(self,
                           overwrite_attributes: list[str] | None = None,
                           additional_attribute_mask: list[str] | None = None) -> Stateful.DefaultStateType:
        ''' get object state - default implementation

        See _get_default_state_attributes() for the considered attributes. The
        values are obtained via getattr(). Note that the class must take care
        of eventually applying deepcopy().

        [overwrite_attributes] replaces the classes [attributes] setting while
        [additional_attributes_mask] extends the existing class [attribute_mask].
        '''
        attributes = self._get_default_state_attributes(
            overwrite_attributes=overwrite_attributes,
            additional_attribute_mask=additional_attribute_mask)
        # compile state from attributes with error handling and return
        data = {}
        for key in attributes:
            if not hasattr(self, key):
                raise TypeError(
                    f'Class {self.__class__} does not have attribute {key} for get_state()]')
            data[key] = deepcopy(getattr(self, key))
        return self._type_guard_default(data)

    def _set_state_default(self,
                           data: object,
                           overwrite_attributes: list[str] | None = None,
                           additional_attribute_mask: list[str] | None = None):
        ''' set object state - default implementation

        See _get_default_state_attributes() for the considered attributes. The
        values written via setattr(). Note that the class must take care of
        eventually applying deepcopy().

        [overwrite_attributes] replaces the classes [attributes] setting while
        [additional_attributes_mask] extends the existing class [attribute_mask].
        '''
        data = Stateful._type_guard_default(deepcopy(data))
        attributes = self._get_default_state_attributes(
            overwrite_attributes=overwrite_attributes,
            additional_attribute_mask=additional_attribute_mask)
        for attr in data:
            if attr not in attributes:
                raise Warning(
                    f'Import state for {self.__class__} '
                    f'includes attribute {attr} which is not expected - '
                    f'expected are {attributes} - ignoring this key'
                )
            setattr(self, attr, data[attr])
