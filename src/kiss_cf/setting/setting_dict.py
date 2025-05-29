''' SettingDict

Surprise: it bundles Settings to a dictionary behavior. ;)
'''
from collections import OrderedDict
from copy import deepcopy
from typing import Any, Callable
from collections.abc import Mapping, MutableMapping
from kiss_cf.storage import Storable, Storage, RamStorage
from .setting import Setting, AppxfSettingError

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

        Initializing supports maps {key: setting} as well as assignments
        setting_dict[key] = setting with setting being one of:
         * Setting object, replacing an eventually existing setting object
         * Setting class for which a Setting object will be created with
           default value (see above).
         * Any tuple (type, value) for which a new Setting object will be
           created via Setting.new(type, value). Value is optional like (type,)
           such that the default value for the type applies.
         * Any plain value (not a Setting object/class and not a tuple). For
           existing keys the value will be applied like: setting.value = value.
           For non existing keys, the Setting object is created like
           Setting.new(type(value), value).
        '''
        # take over value which should be settings (extended behavior during init)
        if settings is None and 'value' in kwargs:
            settings = kwargs['value']
            del kwargs['value']
        # Cover None arguments
        if storage is None:
            storage = RamStorage()
        # initialize setting_dict since parent initialization of Setting will
        # rely on it. Since SettingDict is also a Setting, it must be stored as
        # _value:
        self._value: OrderedDict[Any, Setting] = OrderedDict()
        self._input: Any = OrderedDict()
        self.export_options = Setting.ExportOptions()
        # initialize parents
        super().__init__(storage=storage, **kwargs)

        # Storable will initialize with default storage
        self._on_load_unknown = 'ignore'
        self._store_setting_object = False

        ### Consume settings input
        if settings is None:
            return
        # handle empty input
        if (settings == '' or
            (isinstance(settings, Mapping) and not settings)
            ):
            self._value = OrderedDict()
            # the following line just satisfies the test_setting cases:
            self._input = settings
            return
        if isinstance(settings, Mapping):
            for key, value in settings.items():
                self._set_item(
                    key, value,
                    f'Cannot set key {key} from {settings} '
                    f'of type {settings.__class__} '
                    f'provided to SettingDict.__init__(). ')
            return
        # error, otherwise
        raise AppxfSettingError(
            f'Cannot set/initialize SettingDict. '
            f'See documentation of __init__ for expected input. '
            f'You provided {settings} of type {settings.__class__}.')

    def __len__(self):
        return self._value.__len__()

    def __iter__(self):
        return self._value.__iter__()

    def __getitem__(self, key: str):
        return self._value[key].value

    def _set_item(self, key, value, pre_message):
        ''' Setting expects certain error message behavior

        To satisfy this also for .value assignments and for __init__(), this
        function is abstracted to incorporate information of the whole setting
        structure in error messages.

        Intend of this function is otherwise identical to __setitem__().
        '''
        # reject keys that are not strings
        if not isinstance(key, str):
            raise AppxfSettingError(pre_message + (
                f'Only string keys are supported. '
                f'You provided: {key}'))
        # values that are Settings are always accepted
        if isinstance(value, Setting):
            # transfering key name to setting if setting name is empty
            if not value.options.name:
                value.options.name = key
            self._value[key] = value
            self._input[key] = value
            return
        # setting classes are applies with default values
        if isinstance(value, type) and issubclass(value, Setting):
            self._input[key] = value
            self._value[key] = value()
            return
        # If input is a tuple, first should be the type and the second,
        # optional element, the value.
        if isinstance(value, tuple):
            if not value or len(value) > 2:
                raise AppxfSettingError(
                    f'SettingDict items that are tuples must contain a '
                    f'Setting type as the first element. And, optionally '
                    f'a value as the second type. You provided {value}.')
            if len(value) > 0:
                tmp_type = value[0]
            if len(value) > 1:
                tmp_value = value[1]
            else:
                tmp_value = None

            self._input[key] = value
            if tmp_value is None:
                self._value[key] = Setting.new(tmp_type)
            else:
                self._value[key] = Setting.new(tmp_type, value=tmp_value)
            return
        # What is left is not a tuple (type, value) nor a Setting class/object.
        # The key must exist and the value is applied to the existing Setting's
        # value:
        if key in self._value:
            self._value[key].value = value
            self._input[key] = value
        # Or, the new Setting object is created:
        else:
            self._value[key] = Setting.new(type(value),value=value)
    # TODO: there should be a try/catch at least for the last two settings to
    # add the failing key to the error message from Setting. Like "Cannot set
    # key {key} with following error message from the Setting class. "

    def __setitem__(self, key, value) -> None:
        self._set_item(key, value, '')

    def __delitem__(self, key):
        del self._value[key]

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
        return {key: self._value[key] for key in self._value.keys()}

    def _validated_conversion(self, value: Any) -> tuple[bool, Any]:
        # SettingDict works with dict[str, Setting] on the .value interface
        # which will also be the basis for validation. Note that __init__ still
        # allows a more flexible usage that is consistent with A[key] = value
        # handling.
        if isinstance(value, str) and not value:
            # empty string is OK for a default initialization with {}
            return True, {}
        if not isinstance(value, Mapping):
            return False, {}
        out_value = OrderedDict()
        for key, setting in value.items():
            if not isinstance(key, str):
                return False, {}
            if not isinstance(setting, Setting):
                return False, {}
            out_value[key] = setting
        # Note that out_value creates a new dict from the input but does NOT
        # copy the settings.
        return True, out_value

    def to_string(self) -> str:
        # Return empty string in case SettingDict does not contain settings:
        if not self._value:
            return ''
        return str(self.value)