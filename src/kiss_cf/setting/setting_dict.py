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


class SettingDict(Setting[dict], Storable, MutableMapping[str, Setting]):
    ''' Maintain a dictionary of settings

    SettingDict maintains AppxfSettings for every dict entry such that
    setting_dict[key] = value may lead to AppxfSettingConversionError if the
    input is not valid for the configured setting.

    setting_dict[key] returns the setting's value. To access the setting
    object, use setting_dict.get_setting(key). Writing to setting_dict[key]
    would accept an AppxfSetting to replace or add a new setting to a
    SettingDict.

    SettingDict is also implemented as an AppxfSetting with behavior for .value
    to support nested data structures and corporate with Setting extensions.
    However, .value is not a user interface. Use with care!
    '''
    # TODO: add Options and add a replacement for "default_visibility" (viewed
    # in context of a configuration) - must also scan for usage of this option
    # since it's meaning may change. Note that if "default visibility" only
    # having a meaning withing context of Config, it does not belong into the
    # SettingDict options. But it may be similar to a setting name.

    def __init__(self,
                 settings: Mapping[str, Any] | None = None,
                 storage: Storage | None = None,
                 **kwargs):
        ''' Settings collected as dicitonary

        Recommended initialization is by a dictionary like {key: setting} with
        setting being an AppxfSetting object because this let's you apply
        setting options upon initialization of the SettingDict. Otherwise, you
        would need setting_dict.get_setting(key).options.<...>.

        See documentation of add() for any further support of setting_dict
        input.
        '''
        # Cover None arguments
        if storage is None:
            storage = RamStorage()
        # initialize setting_dict since parent initialization of Setting will
        # rely on it. Since SettingDict is also a Setting, it must be stored as
        # _value:
        self._value: OrderedDict[Any, Setting] = OrderedDict()
        self.export_options = Setting.ExportOptions()
        # initialize parents
        super().__init__(storage=storage, **kwargs)

        # Storable will initialize with default storage
        self._on_load_unknown = 'ignore'
        self._store_setting_object = False

        # Cunsume data and kwargs manually:
        if settings is not None:
            self.add(settings)

    def __len__(self):
        return self._value.__len__()

    def __iter__(self):
        return self._value.__iter__()

    def __getitem__(self, key: str):
        return self._value[key].value

    # TODO: allow new element creation when value is an AppxfSetting
    def __setitem__(self, key, value) -> None:
        # reject keys that are not strings
        if not isinstance(key, str):
            raise AppxfSettingError(
                f'SettingDict only accepts strings as keys. You provided: {key}')
        # instead of relying on KeyError, we provide a more helpful error
        # message to use add() for new keys. This is made required to
        # have the underlying Setting generated more explicitly.
        if not self.__contains__(key):
            raise AppxfSettingError(
                f'Key {key} does not exist. Consider SettingDict.add() '
                f'for adding new settings.')

        # furhter errot handling per maintained setting's value
        # assignment:
        self._value[key].value = value

    def __delitem__(self, key):
        del self._value[key]

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

        The following other variants for
        setting are also supported:
         * A value of a type supported by AppxfSetting. Example: 42 as integer
           would use SettingInt.
         * A Setting class like SettingInt. The value would be initialized with
           the default value.

        You can use any iterable of tuples like [(key, value)] to initialize.
        The tuple may be like ('str', 'appxf') to specify type and value or
        just ('email',) to specify the type while the default value applies.

        The dictionary initialization supports the following for "setting"
        '''
        # TODO: the above documentation is not correct anymore (direct
        # assignment now possible)
        #
        # TODO: there is an inconsistency which interface variant supports what:
        # setting as            {key: setting}      [(key, setting)]
        # AppxfSetting          Yes+                No
        # direct value (42)     Yes                 No

        # why does {key: value} support value as AppxfSetting and direct
        # value but NOT simplified type declaration.
        #
        # TODO: is "add" the appropriate interface? Shouldn't we rather
        # overwrite "update"? If so, shouldn't we allow setting new values via
        # setting_dict[key] = AppxfSetting? This would be without any conflict
        # and would allow an update of SettingDict from another SettingDict. >>
        # Test case for update()
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
        # TODO: below and above: is forwarding to NEW item good? It's add() but
        # if item is already present, it should not overwrite the setting.
        for key, value in kwargs.items():
            self._new_item(key, value)

    def _new_item(self, key: str, value):
        # reject keys that are not strings
        if not isinstance(key, str):
            raise AppxfSettingError(
                f'SettingDict only accepts strings as keys. You provided: {key}')
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
            self._value[key] = value
            return

        # No type or Setting is provided, we try to determine the Setting from
        # the type of the value:
        setting_type = type(value)
        setting = Setting.new(setting_type, value=value)
        # Fall back again to the code from above
        self._new_item(key, setting)

    def get_setting(self, key) -> Setting:
        ''' Access Setting object '''
        return self._value[key]

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
        for key, setting in self._value.items():
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
            key_list = self._value.keys()
        else:
            raise AppxfSettingError(
                f'on_load_unknown option is not supported. '
                f'Supported options: {self.valid_on_load_unknown}')
        # cycle through options and set states:
        for key in key_list:
            if key in data:
                self._value[key].set_state(data[key])
                # restore setting name:
                if not self._value[key].options.name:
                    self._value[key].options.name = key

    # ## Setting behavior

    @classmethod
    def get_default(cls) -> Any:
        return {}

    @classmethod
    def get_supported_types(cls) -> list[type | str]:
        return {'dictionary', 'dict', MutableMapping}

    @Setting.value.getter
    def value(self) -> dict[str, Any]:
        return {key: self._value[key].value for key in self._value.keys()}

    #@value.setter
    #def value(self, value: Any):
    #    valid, _value = self._validated_conversion(value)
    #    self._value = _value

    def _validated_conversion(self, value: Any) -> tuple[bool, Any]:
        # Empty string as default input
        if value == '':
            return True, {}
        # Empty mapping being the default value
        if isinstance(value, MutableMapping) and not value:
            return True, {}
        # Input is a dictionary:
        if isinstance(value, Mapping):
            # I could rely on a add() which already applies all, but this must
            # consider:
            #  1) the already existing values
            #  2) must not yet apply the new values
            # Doubts: this may be a lot of operations (especially in deep nesting)
            # and I may need to reconsider the use cases (GUI validation and direct setting)

            #for key, this_value in value.items():
            #    if not isinstance(key, str):
            #        raise AppxfSettingError(
            #            f'SettingDict.value assignments must be dictionaries '
            #            f'with string keys, you provied as one of the '
            #            f'keys: {key}')
            tmp = deepcopy(self)
            try:
                print(f'--SPECIAL: trying')
                for key, this_value in value.items():
                    tmp[key] = this_value
                    print(f'--SPECIAL: {key} set')
                print(f'--SPECIAL: OK with {tmp.get_state()}')
                return True, tmp.get_state()
            except Exception as e:
                # nothing special is cought here, the result will just be invalid
                print(str(e))
                return False, {}
            # TODO: review the above assignment again
        return False, {}

    def to_string(self) -> str:
        # Return empty string in case SettingDict does not contain settings:
        if not self._value:
            return ''
        return str(self.value)