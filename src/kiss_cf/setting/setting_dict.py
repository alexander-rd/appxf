''' SettingDict

Surprise: it bundles Settings to a dictionary behavior. ;)
'''
from collections import OrderedDict
from dataclasses import dataclass
from copy import deepcopy
from typing import Any
from collections.abc import Mapping, MutableMapping
from kiss_cf.storage import Storable, Storage, RamStorage
from .setting import Setting, AppxfSettingError, AppxfSettingConversionError

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

    SettingDict is also implemented as an AppxfSetting. The value property
    returns values of maintained settings as a dict (likewise for the .input
    interface). Value accepts anything __init__ accepts and nonexisting keys
    would be removed. Note that this interface is not designed for a normal
    user interface - it works but it is not efficient.
    '''
    # TODO: add Options and add a replacement for "default_visibility" (viewed
    # in context of a configuration) - must also scan for usage of this option
    # since it's meaning may change. Note that if "default visibility" only
    # having a meaning withing context of Config, it does not belong into the
    # SettingDict options. But it may be similar to a setting name.

    @dataclass(eq=False, order=False)
    class Options(Setting.Options):
        ''' options for setting select '''
        # update value options - None: SettingDict does not have any own
        # validity except what is fixed (like keys being strings)

        display_columns: int = 1

        # update control options:
        #  * the default mutable is for adding, removing, rearranging or
        #    renaming items. No extra option (like mutable_dict is added)

        display_options = (Setting.Options.display_options + [
            'display_columns'])
        control_options = (Setting.Options.control_options + [
            'mutable_dict'])

    @dataclass(eq=False, order=False)
    class ExportOptions(Setting.ExportOptions):
        # An import via set_state() may discover an inconsistency within the
        # imported data. The option was added in context of SettingDict where
        # loading a stored set of settings should not be blocked by one setting
        # having a failure. This option allows a silent failure.
        exception_on_missing_key: bool = True
        exception_on_new_key: bool = True

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
        # take over settings into kwarg values:
        if settings is not None and 'value' not in kwargs:
            kwargs['value'] = settings
        # Cover None arguments
        if storage is None:
            storage = RamStorage()
        # initialize setting_dict since parent initialization of Setting will
        # rely on it. Since SettingDict is also a Setting, it must be stored as
        # _value:
        self._value: OrderedDict[Any, Setting] = OrderedDict()
        # initialize parents
        super().__init__(storage=storage, **kwargs)

        # The strange next line is just to fix the type hints.
        self.options: SettingDict.Options = self.options
        self.export_options: SettingDict.ExportOptions = self.export_options

    def __len__(self):
        return self._value.__len__()

    def __iter__(self):
        return self._value.__iter__()

    def __getitem__(self, key: str):
        return self._value[key].value

    def _resolve_tuple(self, t: tuple) -> Setting:
        if not t or len(t) > 2:
            raise AppxfSettingError(
                f'SettingDict items that are tuples must contain a '
                f'Setting type as the first element. And, optionally '
                f'a value as the second type. You provided {t}.')
        tmp_type = t[0]
        if len(t) > 1:
            tmp_value = t[1]
        else:
            tmp_value = None

        if tmp_value is None:
            return Setting.new(tmp_type)
        else:
            return Setting.new(tmp_type, value=tmp_value)

    def _set_item(self, key, value):
        ''' separated behavior to avoid too deep nesting

        Note that this is called from __init__() and __setitem__ in a
        try/except to add further error details. Intend of this function is
        otherwise identical to __setitem__().
        '''
        # reject keys that are not strings
        if not isinstance(key, str):
            raise AppxfSettingError(
                f'Only string keys are supported. '
                f'You provided: {key} of type {type(key)}')
        # reject new keys AND key replacement if not mutable:
        if not self.options.mutable:
            if key not in self._value:
                raise AppxfSettingError(
                    f'SettingDict({self.options.name}) mutable option is False. '
                    f'New keys cannot be added. You provided '
                    f'key {key} as new key')
            if (isinstance(value, Setting) or
                (isinstance(value, type) and issubclass(value, Setting)) or
                (isinstance(value, tuple))
                ):
                raise AppxfSettingError(
                    f'SettingDict({self.options.name}) mutable option is False and '
                    f'settings cannot be replaced. '
                    f'You provided for key {key}: {value}')
        # values that are Settings are always accepted
        if isinstance(value, Setting):
            # transfering key name to setting if setting name is empty
            if not value.options.name:
                value.options.name = key
            self._value[key] = value
            return
        # setting classes are applies with default values
        if isinstance(value, type) and issubclass(value, Setting):
            self._value[key] = value()
            return
        # If input is a tuple, first should be the type and the second,
        # optional element, the value.
        if isinstance(value, tuple):
            self._value[key] = self._resolve_tuple(value)
            return
        # What is left is not a tuple (type, value) nor a Setting class/object.
        # The key must exist and the value is applied to the existing Setting's
        # value:
        if key in self._value:
            self._value[key].value = value
        # Or, the new Setting object is created:
        else:
            self._value[key] = Setting.new(type(value), value=value)
    # TODO: there should be a try/catch at least for the last two settings to
    # add the failing key to the error message from Setting. Like "Cannot set
    # key {key} with following error message from the Setting class. "

    def __setitem__(self, key, value) -> None:
        try:
            self._set_item(key, value)
        except (AppxfSettingError, AppxfSettingConversionError) as err:
            raise AppxfSettingError(
                f'Cannot set {key} in SettingDict({self.options.name}). '
                f'You provided value {value} of type {value.__class__}.'
                ) from err

    def __delitem__(self, key):
        if self.options.mutable:
            del self._value[key]
        else:
            raise AppxfSettingError(
                f'SettingDict({self.options.name}) mutable option is False and '
                f'items cannot be deleted. '
                f'You tried to delete key {key}')

    def get_setting(self, key) -> Setting:
        ''' Access Setting object '''
        return self._value[key]

    # ## Storage Behavior

    def set_storage(self,
                    storage: Storage | None = None
                    ):
        ''' Set storage to support store()/load() '''
        if storage is not None:
            self._storage = storage

    def get_state(self, **kwarg) -> object:
        # options are handled equivalent to settings
        export_options = deepcopy(self.export_options)
        export_options.update_from_kwarg(kwarg)
        Setting.ExportOptions.raise_error_on_non_empty_kwarg(kwarg)

        data: OrderedDict[str, Any] = OrderedDict({'_version': 2})
        for key, setting in self._value.items():
            data[key] = setting.get_state(options=export_options)
            # strip name if name is key - to avoid cluttering output by
            # maintaining the name twice.
            if (
                isinstance(data[key], OrderedDict) and
                'name' in data[key] and
                data[key]['name'] == key
            ):
                data[key].pop('name')
                # resolve structure if value is the only entry
                if list(data[key].keys()) == ['value']:
                    data[key] = data[key]['value']
        return data

    def set_state(self, data: Mapping, **kwargs):
        if not isinstance(data, Mapping):
            raise AppxfSettingError(
                'Input to set_state must be a dictionary.')
        if '_version' not in data:
            raise AppxfSettingError(
                'Cannot determine data version, '
                'input data is not a dict with field "_version".')
        if not data['_version'] == 2:
            raise AppxfSettingError(
                f'Cannot handle version {data["_version"]} of data, '
                f'supported is version 2 only.')
        export_options: SettingDict.ExportOptions = deepcopy(
            self.export_options)
        export_options.update_from_kwarg(kwargs)

        data_keys = [key for key in data.keys()
                     if key not in ['_version']]

        # define list of settings to be handled
        if export_options.type:
            # only if type is TRUE, it is expected to also load the keys from
            # the imported data and the corresponding keys are appended.
            key_list = self._value.keys() | data_keys
        else:
            # throw error if any key in data does not yet exist:
            failing_key = None
            if export_options.exception_on_new_key:
                for key in data_keys:
                    if key not in self:
                        failing_key = key
                        break
            if failing_key is not None:
                raise AppxfSettingError(
                    f'Key {key} is included in set_state() data but is not yet '
                    f'maintained in SettingDict({self.options.name}). '
                    f'Consider setting export option "type" or '
                    f'"import_fail_silently" to True.')

            # See above - it is only expected to laod the existing keys:
            key_list = self._value.keys()

        # cycle through options and set states:
        for key in key_list:
            # keys maintained in SettingDict but not in data
            if key not in data and export_options.exception_on_missing_key:
                raise AppxfSettingError(
                    f'Key {key} is maintained by SettingDict({self.options.name}) but not included in data. '
                    f'Data for set_state() only included the keys: {data.keys()}.')
            # keys in data that are to be added (type import options was TRUE)
            # and key not yet existing:
            if key not in self._value:
                print(f'SET_STATE: detected key {key} not in _value')
                # to create the new setting, the type must be present:
                if not isinstance(data[key], dict) or 'type' not in data[key].keys():
                    print(f'SET_STATE: detected no type information')
                    if not export_options.exception_on_new_key:
                        print(f'SET_STATE: continue')
                        continue
                    raise AppxfSettingError(
                        f'Key {key} does not yet exist in SettingDict({self.options.name}) '
                        f'but import data does not include type information. '
                        f'Data only comprises: {data[key]}')
                print(f'SET_STATE: failed')
                self._value[key] = Setting.new(data[key]['type'])

            if key in data:
                # ensure the setting type is correct:
                if ((isinstance(data[key], dict) and
                     'type' in data[key] and
                     export_options.type) and (
                         data[key]['type'] not in self._value[key].get_supported_types()
                     )):
                    raise AppxfSettingError(
                        f'Cannot set_state() key "{key}" in '
                        f'SettingDict({self.options.name}). '
                        f'Setting is of type {self._value[key].__class__.__name__} '
                        f'while provided type is {data[key]["type"]}. ')

                self._value[key].set_state(data[key], export_options=export_options)
                # restore setting name:
                if not self._value[key].options.name:
                    self._value[key].options.name = key

    # ## Setting behavior

    @classmethod
    def get_default(cls) -> Any:
        return {}

    @classmethod
    def get_supported_types(cls) -> list[type | str]:
        return ['dictionary', 'dict', MutableMapping]

    @property
    def value(self) -> dict[str, Any]:
        return {key: self._value[key].value for key in self._value.keys()}

    # The setter needs to be overwritten since the mutable option has a more
    # refined meaning within SettingDict. We can still change the values of
    # maintained settings but not extend or delete items in the SettingDict.
    @value.setter
    def value(self, value: Any):
        valid, err = self._validated_conversion(value)
        if not valid:
            raise AppxfSettingError(
                f'Cannot set value of type {type(value)} '
                f'for SettingDict({self.options.name}): {value}. See subsequent error message.'
                ) from err
        # detect removed keys:
        if not self.options.mutable:
            for key in self._value:
                if key not in value:
                    raise AppxfSettingError(
                        f'SettingDict({self.options.name}) mutable option is False and '
                        f'items cannot be deleted. '
                        f'Input value did not contain key {key}.')

        # validation already confirmed the input being a mapping
        for key, setting in value.items():
            self[key] = setting

    # Input returns the same as value. Rationale: the actual input is in the
    # Setting objects and there is no apparent benefit to maintain anything on
    # top of this. Note that the Setting base class still maintains a _input
    # property which remains unused with this implementation.
    @Setting.input.getter
    def input(self) -> dict[str, Any]:
        return {key: self._value[key].input for key in self._value.keys()}

    def _validated_conversion(self, value: Any) -> tuple[bool, Any]:
        # This function will only validate. In contrast to normal settings, the
        # prepared (converted) value that can be returned will remain unused
        # and, instead, a detailed error is returned. For actual setting a new
        # value, _set_value() will be overwritten as well which will use the
        # returned detailed error.
        if not isinstance(value, Mapping):
            return False, AppxfSettingError(
                f'Value must be a Mapping. You provided {value} of type {type(value)}.')
        for key, setting in value.items():
            if not isinstance(key, str):
                return False, AppxfSettingError(
                    f'Only string keys are supported. '
                    f'You provided: {key} of type {type(key)}')
            if isinstance(setting, Setting):
                continue
            if isinstance(setting, type) and issubclass(setting, Setting):
                continue
            if isinstance(setting, tuple) or key not in self._value:
                try:
                    tmp_setting = SettingDict()
                    tmp_setting['err'] = setting
                except (AppxfSettingError, AppxfSettingConversionError) as err:
                    return False, err
                continue
            # Above are all options that would create a NEW key (including the
            # general case of the key not being existent). What remains is key
            # is existing and setting being a value.
            if not self._value[key].validate(setting):
                # setting is not valid but the detailed error message shall be
                # returned
                try:
                    self._value[key].value = setting
                except (AppxfSettingError, AppxfSettingConversionError) as err:
                    return False, err
                else: # pragma: no cover  # Rationale: the above else path is
                      # defensive code. See "this should not happen" in error
                      # message.
                    raise AppxfSettingError(
                        f'Value for {key} was invalid but did not throw an '
                        f'error when trying to set. This should not happen')

        return True, None

    def to_string(self) -> str:
        # Return empty string in case SettingDict does not contain settings:
        if not self._value:
            return ''
        return str(self.value)