''' Provide KissPropertyDict '''

from typing import Any
from collections.abc import Mapping
from collections import UserDict
from kiss_cf.storage import Storable, Storage
from kiss_cf.storage.storage_dummy import StorageDummy
from .property import KissProperty, KissPropertyError

# TODO: Review if the "keep values as separate dict" behavior is worth
# splitting into a separate class in the conrext of property handling and
# corresponding GUI. What would remain for the config section?? Just the
# storage behavior??

# TODO: support for iterable input like [(key1, value1), (key2, value2)].

# TODO: support tuples with additional named value options

# TODO: Storing properties. This would be required for a "configurable config".

# TODO: Loading modes 'add' and 'error'


# Implementatino could not use UserDict as first class since UserData
# implementation does not use super().__init__(), blocking the call of
# Storable.__init__(). Deriving from dict has too many pitfalls, deriving from
# MutableMapping would have resolved in re-implementing UserDict details.
# Result: putting UserDict last.
class KissPropertyDict(Storable, UserDict):
    ''' Maintain a dictionary of properties

    The class supports normal dictionary behavior.
    '''

    def __init__(self,
                 data: Mapping[str, Any] | None = None,
                 storage: Storage | None = None,
                 **kwargs):
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
        # Define KissPropertyDict specific details
        self._property_dict: dict[Any, KissProperty] = {}
        # Initialize dict details
        if storage is None:
            storage = StorageDummy()
        super().__init__(storage=storage)
        # Cunsume data and kwargs manually:
        if data is not None:
            self.add(data)
        if kwargs:
            self.add(**kwargs)
        # Storable will initialize with default storage
        self._on_load_unknown = 'ignore'
        self._store_property_config = False

    def __setitem__(self, key, value) -> None:
        if not self.__contains__(key):
            raise KissPropertyError(
                f'Key {key} does not exist. Consider KissPropertyDict.add() '
                f'for adding new properties.')
        # Value already exists. Try to set new value into KissProperty, if this
        # is OK, take value from there:
        self._property_dict[key].value = value
        super().__setitem__(key, self._property_dict[key].value)

    def add(self, data: Mapping[str, Any] | None = None, **kwargs):
        ''' Add new properties to the property dict

        New properties cannot be written in the same way new elements would be
        written to a normal dictionaries:
          propety_dict['new property'] = 42
        for two reasons:
          1) Adding a new value may not include the otherwise normal validity
             check. Example: KissEmail is initialized with an empty string
             (invalid Email address)
          2) Protect from unintentional usage
        '''
        if data is not None:
            if (hasattr(data, 'keys') and hasattr(data, '__getitem__')):
                # We have a mapping object and can cycle:
                for key in data.keys():
                    self._new_item(key, data[key])
            elif hasattr(data, '__iter__'):
                # The outer is already an iterable, lets iterate the inner and
                # expect a key and a value:
                for element in data:
                    if not hasattr(element, '__iter__'):
                        raise KissPropertyError(
                            'No second level iterable. KissPropertyDict can '
                            'be initialized by iterables of iterables where '
                            'the inner iterables must be the key followed by'
                            'the value.')
                    inner_iter = iter(element)
                    key = next(inner_iter, None)
                    value = next(inner_iter, None)
                    if key is None or value is None:
                        raise KissPropertyError(
                            'No key and/or value provided. '
                            'KissPropertyDict can '
                            'be initialized by iterables of iterables where '
                            'the inner iterables must be the key followed by'
                            'the value.')
                    self._new_item(key, value)
                    # we just ignore anything else
            else:
                raise KissPropertyError(
                    f'Invalid initialization input of type {type(data)}. '
                    f'Initialize with a dictionary of key/value '
                    f'specifications.')
        for key, value in kwargs.items():
            self._new_item(key, value)

    def _new_item(self, key, value):
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

    # ## Storage Behavior

    valid_on_load_unknown = ['ignore']

    def set_storage(self,
                    storage: Storage | None = None,
                    on_load_unknown: str | None = 'ignore',
                    store_property_config: bool | None = False
                    ):
        ''' Set storage to support store()/load() '''
        if storage is not None:
            self._storage = storage


        if (isinstance(on_load_unknown, str) and
                on_load_unknown in self.valid_on_load_unknown):
            self._on_load_unknown = 'ignore'
        else:
            raise KissPropertyError(
                f'on_load_unknown supports None (no change) '
                f'and: {self.valid_on_load_unknown}. Extensions may be added.'
            )

        if store_property_config is not None:
            if store_property_config:
                raise KissPropertyError(
                    'Storing the property configurations is not '
                    'yet supported.')
            if isinstance(store_property_config, bool):
                self._store_property_config = False
            else:
                raise KissPropertyError(
                    f'store_property_config supports None (no change) '
                    f'and True. Extensions may be added.'
                )

    def _get_state(self) -> object:
        if self._store_property_config:
            # not yet supported. te restricted unpickler would not be able to
            # load KissProperty objects. The KissProperties should provide a
            # public "get_state".
            data = {'_version': 1,
                    'properties': self._property_dict}
        else:
            # To properly restore the "input" from KissProperties, we need to
            # store those inputs and not just the values
            data = {'_version': 1,
                    'values': {key: prop.input
                               for key, prop
                               in self._property_dict.items()}}
        return data

    def _set_state(self, data: object):
        if self._on_load_unknown == 'ignore':
            # cycle through known options and load values
            for key in self.data:
                if key in data['values']:
                    self[key] = data['values'][key]
        else:
            raise KissPropertyError(
                f'on_load_unknown option is not supported. '
                f'Supported options: {self.valid_on_load_unknown}')
