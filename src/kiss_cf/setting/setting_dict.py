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
                 settings: Mapping[str, Any] | tuple[tuple[str, Any]] | None = None,
                 storage: Storage | None = None,
                 **kwargs):
        ''' Settings collected as dicitonary

        Recommended initialization is by a dictionary like {key: setting} with
        setting being an AppxfSetting object because this let's you apply
        setting options upon initialization of the SettingDict. Otherwise, you
        would need setting_dict.get_setting(key).options.<...>.

        Initializing supports maps {key: setting} and lists of tuples [(key,
        setting)] as well as assignments setting_dict[key] = setting with
        setting being one of:
         * Setting object being valid for new and existing keys (would replace
           existing keys)
         * Setting class being valid only for new keys. Default value applies.
         * Any tuple (type, value) being valid only for new keys. They will
           receive a Setting.new(type, value). Value can be left empty like
           (type,) such that the default value for the type applies.
         * Any python type (except Setting, tuple or dict) being valid only
           for new keys. Default values from Setting.new(type) applies.
         * Any plain value (not a pythong type) being valid for new and
           existing keys. For existing keys the value will be applied like:
           setting.value = value. For new keys, Setting.new(value) will be
           used.
        '''
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

        # Consume settings input
        if settings is not None:
            self._handle_settings(
                settings,
                lambda self, key, value: self._set_item(
                    key, value,
                    f'Cannot set value {settings} of type '
                    f'{settings.__class__} for SettingDict. '),
                variant='set')

    # Two function definitions to support type hinting. Only one type would
    # have been preferred - also for the _handle_setting() interface but this
    # would have required output arguments for _set_item() without any need in
    # scope of _set_item().
    ElementSetFcn = Callable[['SettingDict', str, Any], None]
    ElementValidateFcn = Callable[['SettingDict', str, Any], tuple[bool, str]]
    # The function _handle_settings is rather abstract due to the two different
    # use cases "set" a value and "validate" a value. Consistency of those
    # operations on the outer level was prioritized over a simple
    # implementation to exclude that a valid settings container cannot be set
    # or vice versa. The inconsistency still exists since _set_item() is still
    # a separate implementation from _validate_item().
    #
    # TODO: reconsider the function interfaces. The validate() return message
    # may not be used. The set_item use case may also return the message. And
    # if empty string '' it could also imply a validation being OK. >> Merging
    # the ElementSetFcf and ElementValidateFcn functions as a secondary effect.
    def _handle_settings(
        self, settings: Any,
        element_handler: ElementSetFcn | ElementValidateFcn,
        variant: str,
        ) -> tuple[bool, str]:
        ''' handle top level of the various input options

        This function resolves the outer Mapping or Tuple and is used for
        __init__, writing to setting_dict.value and validate(). Because of
        validate() it must return a boolean and cannot throw errors directly.
        But it returns the detailed error message as string.

        Variant is either "set" or "validate".
        '''
        # handle empty input
        if (settings == '' or
            ((isinstance(settings, Mapping) or isinstance(settings, tuple)
              ) and not settings
             )
            ):
            if variant == 'set':
                self._input = settings
                self._value = OrderedDict()
            return True, ''
        if isinstance(settings, Mapping):
            for key, value in settings.items():
                if variant == 'set':
                    element_handler(self, key, value)
                else:
                    out, message = element_handler(self, key, value)
                    if not out:
                        return False, message
            return True, ''
        if not isinstance(settings, tuple):
            message = (
                f'Cannot set value for SettingDict. '
                f'See documentation of __init__ for expected input. '
                f'You provided {settings} of type {settings.__class__}.')
            if variant == 'set':
                raise AppxfSettingError(message)
            else:
                return False, message
        # left is only a tuple settings:
        for element in settings:
            if not isinstance(element, tuple) or len(element) != 2:
                message = (
                    f'No second level tuple. SettingDict can '
                    f'be initialized a tuple of tuples where '
                    f'the inner tuple must be the key followed by'
                    f'the value: (key, value). '
                    f'You provided an item: {element}')
                if variant == 'set':
                    raise AppxfSettingError(message)
                else:
                    return False, message
            key = element[0]
            value = element[1]

            if variant == 'set':
                element_handler(self, key, value)
            else:
                out, message = element_handler(self, key, value)
                if not out:
                    return False, message
        return True, ''

    def __len__(self):
        return self._value.__len__()

    def __iter__(self):
        return self._value.__iter__()

    def __getitem__(self, key: str):
        return self._value[key].value

    def _get_setting_for_new_key(self, value) -> Setting:
        # setting classes are applies with default values (if the key does not
        # yet exist)
        if isinstance(value, type) and issubclass(value, Setting):
            return value()
        # If input is an tuple, first should be the type and the second,
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

            if tmp_value is None:
                return Setting.new(tmp_type)
            else:
                return Setting.new(tmp_type, value=tmp_value)
        # Generate a Setting object if only the class or a type is provided.
        # Again, only if the key does not yet exist.
        if isinstance(value, type):
            return Setting.new(value)
        # What is left is not a type and not a setting object or class. This
        # value will be applied. If not existing, we try to derive the setting
        # type from the value type:
        return Setting.new(type(value), value)

    def _set_item(self, key, value, pre_message):
        ''' Setting expects certain error message behavior

        To satisfy this also for .value assigbments and for __init__(), this
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
        if key not in self._value:
            self._value[key] = self._get_setting_for_new_key(value)
            self._input[key] = value
        else:
            # a few specific error messages:
            if isinstance(value, type) and issubclass(value, Setting):
                raise AppxfSettingError(pre_message + (
                    f'SettingDict does not support overwriting the existing '
                    f'key {key} with Setting class'
                    f'{value.__class__.__name__}.'))
            if isinstance(value, tuple):
                raise AppxfSettingError(pre_message + (
                    f'SettingDict does not support overwriting the existing '
                    f'key {key} with some tuple (type, value). You '
                    f'provided: {value}.'))
            if isinstance(value, type):
                raise AppxfSettingError(pre_message + (
                    f'SettingDict does not support overwriting the existing '
                    f'key {key} with a new Setting from type. You '
                    f'provided: {value.__class__.__name__}.'))
            self._value[key].value = value
            self._input[key] = value

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

    @property
    def value(self) -> dict[str, Any]:
        return {key: self._value[key].value for key in self._value.keys()}

    @value.setter
    def value(self, settings: Any):
        self._handle_settings(
            settings,
            lambda self, key, value: self._set_item(
                key, value,
                f'Cannot set value {settings} of type '
                f'{settings.__class__} for SettingDict. '),
            'set')
    # TODO: check - it should be better to override _set_value() instead. This
    # would keep the setter functionality of protecting from changes while not
    # being mutable.

    def _validated_conversion(self, value: Any) -> tuple[bool, Any]:
        # SettingDict cannot provide this function. The returned "value" must
        # retain the original setting objects because others like GUI elements
        # may reference them. But the new values cannot be "prepared" in the
        # existing Setting objects since there is no strategy implemented for
        # reverting this. >> Instead of making the Setting implementation more
        # flexible, dependent functions are overridden in the SettingDict
        # implementation.
        raise AppxfSettingError(
            'SettingDict does not support normal Setting behavior and this '
            'error should NOT have hapened. SettingDict implementation should '
            'have substituted corresponding behavior.')

    def _validate_item(self, key, value) -> tuple[bool, str]:
        if not isinstance(key, str):
            return False, (
                f'SettingDict keys must be strings. '
                f'You provided {key} of class '
                f'{key.__class__.__name__}')
        # Settings are always OK
        if isinstance(value, Setting):
            return True, ''
        if key not in self._value:
            # TODO: check if initialization would succeed?
            try:
                SettingDict(settings = {key: value})
            except Exception as e:
                print(e)
                return False, 'TBD error message'
                # TODO: clarify this open error message

        # key is existing and input is not a Setting (replaces). Only a value
        # for setting is left:
        return self._value[key].validate(value), ''

    def validate(self, settings: Any) -> bool:
        # the same procedure as for setting a value is applied to resolve the
        # outer structure, only the element-wise validation is re-implemented:
        out, message = self._handle_settings(
            settings,
            lambda self, key, value: self._validate_item(key, value),
            'validate')
        if not out:
            # TODO: proper logging
            print(message)
        return out

    def to_string(self) -> str:
        # Return empty string in case SettingDict does not contain settings:
        if not self._value:
            return ''
        return str(self.value)