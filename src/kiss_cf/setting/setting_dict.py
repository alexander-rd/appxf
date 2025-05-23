''' SettingDict

Surprise: it bundles Settings to a dictionary behavior. ;)
'''
from collections import OrderedDict
from copy import deepcopy
from typing import Any
from collections.abc import Mapping, MutableMapping
from kiss_cf.storage import Storable, Storage, RamStorage
from .setting import Setting, AppxfSettingError

# TODO: support tuples with additional named value options

# TODO: Storing the AppxfSetting objects. This would be required for a
# "configurable config".

# TODO: Loading modes 'add' and 'error'


class SettingDict(Setting, Storable, MutableMapping[str, Setting]):
    ''' Maintain a dictionary of settings

    While normal dictionary behavior is supported, be aware that writing to
    this dictionary can fail with AppxfSettingConversionError if the input is
    not valid for a setting.
    '''

    # TODO: add Options and add a replacement for "default_visibility" (viewed
    # in context of a configuration) - must also scan for usage of this option
    # since it's meaning may change. Note that if "default visibility" only
    # having a meaning withing context of Config, it does not belong into the
    # SettingDict options. But it may be similar to a setting name.

    def __init__(self,
                 setting_dict: Mapping[str, Any] | None = None,
                 storage: Storage | None = None,
                 **kwargs):
        ''' Settings collected as dicitonary

        Recommended initialization is by a dictionary like {key: setting}.
        Supported are also the other two ways to initialize a dictionary:
          * initialization by key/value pairs (key=setting). This is limited by
            the already named arguments
          * by iterables of iterables [(key, setting)].
        The most typical setting specification is a tuple of the setting type
        and value like ('str', 'appxf') or ('email',) which only specifies the
        type and uses the default value. Other options are:
          * A value of a supported type. Example: 42 as integer. It would use
            SettingInt.
          * An Setting class like SettingInt. The value would be initialized
            with the default value.
          * A Setting object. The value would be taken over.
        Note: If you need to pass additional arguments to a Setting, you
        need to provide the Setting object.
        '''
        # Cover None arguments
        if storage is None:
            storage = RamStorage()
        # initialize parents
        super().__init__(storage=storage, **kwargs)

        # initialize own data structures
        self._setting_dict: OrderedDict[Any, Setting] = OrderedDict()
        self.export_options = Setting.ExportOptions()
        # Storable will initialize with default storage
        self._on_load_unknown = 'ignore'
        self._store_setting_object = False

        # Cunsume data and kwargs manually:
        if setting_dict is not None:
            self.add(setting_dict)

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
        # Value already exists. Try to set new value into Setting, if this
        # is OK, take value from there:
        self._setting_dict[key].value = value

    def __delitem__(self, key):
        del self._setting_dict[key]

    def add(self, setting_dict: Mapping[str, Any] | None = None, **kwargs):
        ''' Add new settings to the setting dictionary

        New settings cannot be written in the same way new elements would be
        written to a normal dictionaries:
          propety_dict['new property'] = 42
        This has two reasons:
          1) Adding a new value may not include the otherwise normal validity
             check. Example: SettingEmail is initialized with an empty string
             (invalid empty Email address)
          2) Protect from unintentional usage
        '''
        if setting_dict is not None:
            if (hasattr(setting_dict, 'keys') and hasattr(setting_dict, '__getitem__')):
                # We have a mapping object and can cycle:
                for key in setting_dict.keys():
                    self._new_item(key, setting_dict[key])
            elif hasattr(setting_dict, '__iter__'):
                # The outer is already an iterable, lets iterate the inner and
                # expect a key and a value:
                for element in setting_dict:
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
                    f'Invalid initialization input of type {type(setting_dict)}. '
                    f'Initialize with a dictionary of key/value '
                    f'specifications.')
        for key, value in kwargs.items():
            self._new_item(key, value)

    def _new_item(self, key, value):
        # Generate a Setting object if only the class or a type is provided:
        if isinstance(value, type):
            if issubclass(value, Setting):
                value = value()
            else:
                value = Setting.new(value)
        # If input is a tuple of two, first should be the type and second the
        # value:
        if isinstance(value, tuple):
            if len(value) == 1:
                value = Setting.new(value[0])
            elif len(value) == 2:
                value = Setting.new(value[0], value=value[1])
            else:
                raise AppxfSettingError(
                    f'SettingDict can only store AppxfSetting object which '
                    f'do not model complex data types like tuples. Tuples are '
                    f'interpreted as [0] providing the type and [1] the '
                    f'initial value. The input tuple had length '
                    f'{len(value)}.')

        # Use the Setting object if one is provided
        if isinstance(value, Setting):
            # transfer key name to setting if setting name is empty:
            if not value.options.name:
                value.options.name = key
            self._setting_dict[key] = value
            return

        # No type or Setting is provided, we try to determine the Setting from
        # the type of the value:
        setting_type = type(value)
        setting = Setting.new(setting_type, value=value)
        # Fall back again to the code from above
        self._new_item(key, setting)

    def get_setting(self, key) -> Setting:
        ''' Access Setting object '''
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
                    'store_setting_object supports None (no change) '
                    'and True. Extension for False may be added.'
                )

    def get_state(self, **kwarg) -> object:
        # options are handled equivalent to settings
        export_options = deepcopy(self.export_options)
        export_options.update_from_kwarg(kwarg)
        Setting.ExportOptions.raise_error_on_non_empty_kwarg(kwarg)

        data: dict[str, Any] = {'_version': 2}
        for key, setting in self._setting_dict.items():
            data[key] = setting.get_state(options=export_options)
            # strip name if name is key
            if (
                isinstance(data[key], dict) and
                'options' in data[key] and
                'name' in data[key]['options'] and
                data[key]['options']['name'] == key
            ):
                data[key]['options'].pop('name')
        return data

    def set_state(self, data: Mapping, **kwarg):
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

    # ## Setting behavior

    @classmethod
    def get_default(cls) -> Any:
        return {}

    @classmethod
    def get_supported_types(cls) -> list[type | str]:
        return {'dictionary', 'dict', MutableMapping}

    def _validated_conversion(self, value: Any) -> tuple[bool, Any]:
        # Empty string as default input
        if value == '':
            return True, {}
        # Empty mapping being the default value
        if isinstance(value, MutableMapping) and not value:
            return True, {}
        return False, {}

    def to_string(self) -> str:
        # Return empty string in case SettingDict does not contain settings:
        if not self._setting_dict:
            return ''
        return str(self._setting_dict)