''' AppxfSettingDict

Surprise: it bundles AppxfSettings to a dictionary behavior. ;)
'''

from typing import Any
from collections.abc import Mapping, MutableMapping
from kiss_cf.storage import Storable, Storage, RamStorage
from .setting import AppxfSetting, AppxfSettingError

# TODO: support tuples with additional named value options

# TODO: Storing the AppxfSetting objects. This would be required for a
# "configurable config".

# TODO: Loading modes 'add' and 'error'

class SettingDict(Storable, MutableMapping[str, AppxfSetting]):
    ''' Maintain a dictionary of settings

    While normal dictionary behavior is supported, be aware that writing to
    this dictionary can fail with AppxfSettingConversionError if the input is
    not valid for a setting.
    '''

    def __init__(self,
                 data: Mapping[str, Any] | None = None,
                 storage: Storage | None = None,
                 default_visibility: bool = True,
                 **kwargs):
        ''' AppxfSettings collected as dicitonary

        Recommended initialization is by a dictionary like {key: setting}.
        Supported are also the other two ways to initialize a dictionary:
          * initialization by key/value pairs (key=setting). This is limited by
            the already named arguments
          * by iterables of iterables [(key, setting)].
        The most typical setting specification is a tuple of the setting type
        and value like ('str', 'appxf') or ('email',) which only specifies the
        type and uses the default value. Other options are:
          * A value of a supported type. Example: 42 as integer. It would use
            AppxfInt.
          * An AppxfSetting class like AppxfInt. The value would be initialized
            with the default value.
          * An AppxfSetting object. The value would be taken over.
        Note: If you need to pass additional arguments to an AppxfSetting, you
        need to provide the AppxfSetting object.
        '''
        # Define SettingDict specific details
        self._setting_dict: dict[Any, AppxfSetting] = {}
        # Initialize dict details
        if storage is None:
            storage = RamStorage()
        # **kwargs cannot be forwarded. All are resolved into dictionary construction.
        super().__init__(storage=storage)

        # Cunsume data and kwargs manually:
        if data is not None:
            self.add(data)
        if kwargs:
            self.add(**kwargs)
        # Storable will initialize with default storage
        self._on_load_unknown = 'ignore'
        self._store_setting_object = False

        # TODO: add GUI element concept and derive/aggregate from there
        self.default_visibility = default_visibility

    def __len__(self):
        return self._setting_dict.__len__()

    def __iter__(self):
        return self._setting_dict.__iter__()

    def __getitem__(self, key: str):
        return self._setting_dict[key].value

    def __setitem__(self, key, value) -> None:
        if not self.__contains__(key):
            raise AppxfSettingError(
                f'Key {key} does not exist. Consider SettingDict.add() '
                f'for adding new settings.')
        # Value already exists. Try to set new value into AppxfSetting, if this
        # is OK, take value from there:
        self._setting_dict[key].value = value

    def __delitem__(self, key):
        del self._setting_dict[key]

    def add(self, data: Mapping[str, Any] | None = None, **kwargs):
        ''' Add new settings to the setting dictionary

        New settings cannot be written in the same way new elements would be
        written to a normal dictionaries:
          propety_dict['new property'] = 42
        This has two reasons:
          1) Adding a new value may not include the otherwise normal validity
             check. Example: AppxfEmail is initialized with an empty string
             (invalid empty Email address)
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
                        raise AppxfSettingError(
                            'No second level iterable. SettingDict can '
                            'be initialized by iterables of iterables where '
                            'the inner iterables must be the key followed by'
                            'the value.')
                    inner_iter = iter(element)
                    key = next(inner_iter, None)
                    value = next(inner_iter, None)
                    if key is None or value is None:
                        raise AppxfSettingError(
                            'No key and/or value provided. '
                            'SettingDict can '
                            'be initialized by iterables of iterables where '
                            'the inner iterables must be the key followed by'
                            'the value.')
                    self._new_item(key, value)
                    # we just ignore anything else
            else:
                raise AppxfSettingError(
                    f'Invalid initialization input of type {type(data)}. '
                    f'Initialize with a dictionary of key/value '
                    f'specifications.')
        for key, value in kwargs.items():
            self._new_item(key, value)

    def _new_item(self, key, value):
        # Generate a AppxfSetting object if only the class or a type is
        # provided:
        if isinstance(value, type):
            if issubclass(value, AppxfSetting):
                value = value()
            else:
                value = AppxfSetting.new(value)
        # If input is a tuple of two, first should be the type and second the
        # value:
        if isinstance(value, tuple):
            if len(value) == 1:
                value = AppxfSetting.new(value[0])
            elif len(value) == 2:
                value = AppxfSetting.new(value[0], value=value[1])
            else:
                raise AppxfSettingError(
                    f'SettingDict can only store AppxfSetting object which '
                    f'do not model complex data types like tuples. Tuples are '
                    f'interpreted as [0] providing the type and [1] the '
                    f'initial value. The input tuple had length '
                    f'{len(value)}.')

        # Use the AppxfSetting object if one is provided
        if isinstance(value, AppxfSetting):
            # transfer key name to setting if setting name is empty:
            if not value.options.name:
                value.options.name = key
            self._setting_dict[key] = value
            return

        # No type or AppxfSetting is provided, we try to determine the
        # AppxfSetting from the type of the value:
        setting_type = type(value)
        setting = AppxfSetting.new(setting_type, value=value)
        # Fall back again to the code from above
        self._new_item(key, setting)

    def get_setting(self, key) -> AppxfSetting:
        ''' Access AppxfSetting object '''
        return self._setting_dict[key]

    # ## Storage Behavior

    valid_on_load_unknown = ['ignore']

    def set_storage(self,
                    storage: Storage | None = None,
                    on_load_unknown: str | None = 'ignore',
                    store_setting_object: bool | None = False
                    ):
        ''' Set storage to support store()/load() '''
        if storage is not None:
            self._storage = storage


        if (isinstance(on_load_unknown, str) and
                on_load_unknown in self.valid_on_load_unknown):
            self._on_load_unknown = 'ignore'
        else:
            raise AppxfSettingError(
                f'on_load_unknown supports None (no change) '
                f'and: {self.valid_on_load_unknown}. Extensions may be added.'
            )

        if store_setting_object is not None:
            if store_setting_object:
                raise AppxfSettingError(
                    'Storing the setting objects is not '
                    'yet supported.')
            if isinstance(store_setting_object, bool):
                self._store_setting_object = False
            else:
                raise AppxfSettingError(
                    f'store_setting_object supports None (no change) '
                    f'and True. Extension for False may be added.'
                )

    def get_state(self) -> object:
        data: dict[str, Any] = {'_version': 2}
        for key, setting in self._setting_dict.items():
            data[key] = setting.get_state()
            # strip name if name is key
            if (isinstance(data[key], dict) and
                'options' in data[key] and
                'name' in data[key]['options'] and
                data[key]['options']['name'] == key
                ):
                data[key]['options'].pop('name')
        return data

    def set_state(self, data: Mapping):
        if not isinstance(data, Mapping) or '_version' not in data:
            raise AppxfSettingError(
                'Cannot determine data version, '
                'input data is not a dict with field "_verision".')
        if not data['_version'] == 2:
            raise AppxfSettingError(
                f'Cannot handle version {data["_version"]} of data, '
                f'supported is version 2 only.')
        # define list of settings to be handled
        if self._on_load_unknown == 'ignore':
            key_list = self._setting_dict.keys()
        else:
            raise AppxfSettingError(
                f'on_load_unknown option is not supported. '
                f'Supported options: {self.valid_on_load_unknown}')
        # cycle through options and set states:
        for key in key_list:
            if key in data:
                self._setting_dict[key].set_state(data[key])
                # restore setting name:
                if not self._setting_dict[key].options.name:
                    self._setting_dict[key].options.name = key
