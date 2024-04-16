''' Provide KissPropertyDict '''

from typing import Any
from collections import UserDict
from kiss_cf.storage import Storable, Storage
from .property import KissProperty, KissPropertyError

# TODO: Review if the "keep values as separate dict" behavior is worth
# splitting into a separate class in the conrext of property handling and
# corresponding GUI. What would remain for the config section?? Just the
# storage behavior??

# TODO: Storage behavior.


# Implementatino could not use UserDict as first class since UserData
# implementation does not use super().__init__(), blocking the call of
# Storable.__init__(). Deriving from dict has too many pitfalls, deriving from
# MutableMapping would have resolved in re-implementing UserDict details.
# Result: putting UserDict last.
class KissPropertyDict(Storable, UserDict):
    ''' Maintain a dictionary of config options

    The class supports normal dictionary behavior.

    Relations to other classes:
        Config -- Aggregates sections to an application configuration.
        Option -- Type and display options
    '''

    def __init__(self, data: dict | None = None, **kwargs):
        ''' KissPropertyDict

        Initializations supports initialization by key/value pairs or by a
        dictionary. The values may be one of:
          * A value of a supported type. Example: 42 as integer would then use
            KissInt.
          * A KissProperty class like KissInt. The value would be initialized
            with the default value.
          * A KissProperty object. The value would be taken over.
          * A tuple like (int, 42) or ('int', 42) that provide the type and
            value parameters for a KissProperty.new() call.
              * Note 1: passing additional parameters is not yet supported.
              * Note 2: You may also use (int,) as tuple with only one element
                to only specify the type. The value would then be the default
                value.
        Not yet supported is the dict initialization by iterables.
        '''

        # TODO: support for iterable input like [(key1, value1), (key2,
        # value2)].

        # TODO: support tuples with additional named value options

        # Define KissPropertyDict specific details
        self._property_dict: dict[Any, KissProperty] = {}
        # Initialize dict details
        super().__init__(**kwargs)
        # Cunsume data manually:
        if data is not None:
            self.update(data)
        # Storable will initialize with default storage
        #Storable.__init__(self)
        print(f'>>dict init>>: {self.__dict__}')
        print(f'MRO: {[x.__name__ for x in KissPropertyDict.__mro__]}')

    def set_storage(self, storage: Storage):
        ''' Set storage to support store()/load() '''
        self._storage = storage

    def __setitem__(self, key, value) -> None:
        print(f'>> setitem for {key} and {value}')
        if not self.__contains__(key):
            self._new_item(key, value)
            print(f'setitem via new_item for key={key}: {self[key]}')
            return
        # Value already exists. Try to set new value into KissProperty, if this
        # is OK, take value from there:
        self._property_dict[key].value = value
        super().__setitem__(key, self._property_dict[key].value)

    def _new_item(self, key, value):
        print(f'>> new_item for {key} and {value} type {type(value)}')
        # Generate a KissProperty object if only the class or a type is
        # provided:
        if isinstance(value, type):
            if issubclass(value, KissProperty):
                value = value()
            else:
                value = KissProperty.new(value)
        # If input is a tuple of two, first should be the type and second the
        # value:
        if isinstance(value, tuple):
            if len(value) == 1:
                value = KissProperty.new(value[0])
            elif len(value) == 2:
                value = KissProperty.new(value[0], value=value[1])
            else:
                raise KissPropertyError(
                    f'KissPropertyDict can only store KissProperties which '
                    f'do not model complex data types like tuples. Tuples are '
                    f'interpreted as [0] providing the type and [1] the '
                    f'initial value. The input tuple had length '
                    f'{len(value)}.')

        # Use the KissProperty object if one is provided
        if isinstance(value, KissProperty):
            super().__setitem__(key, value.value)
            self._property_dict[key] = value
            return

        # No type or KissProperty is provided, we try to determine the
        # KissProperty from the type of the value:
        prop_type = type(value)
        prop = KissProperty.new(prop_type, value=value)
        # Fall back again to the code from above
        self._new_item(key, prop)

    def __delitem__(self, key: Any) -> None:
        if self.__contains__(key):
            del self._property_dict[key]
            super().__delitem__(key)

    def get_property(self, key) -> KissProperty:
        ''' Access KissProperty object '''
        # reuse error handling of dict by accessing the value
        super().__getitem__(key)
        return self._property_dict[key]
