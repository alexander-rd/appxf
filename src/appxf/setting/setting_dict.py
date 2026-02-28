# Copyright 2024-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
"""SettingDict

Surprise: it bundles Settings to a dictionary behavior. ;)
"""

# allow class name being used before being fully defined (like in same class):
from __future__ import annotations

import warnings
from collections import OrderedDict
from collections.abc import Callable, Mapping, MutableMapping
from dataclasses import dataclass
from typing import Any

from appxf.storage import RamStorage, Storable, Storage

from .setting import AppxfSettingConversionError, AppxfSettingError, Setting


class AppxfSettingWarning(Warning):
    """Warning for AppxfSettings"""

    pass


class SettingDict(Setting[dict], Storable, MutableMapping[str, Setting]):
    """Maintain a dictionary of settings

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
    """

    @dataclass(eq=False, order=False)
    class Options(Setting.Options):
        """options for setting select"""

        # update value options - None: SettingDict does not have any own
        # validity except what is fixed (like keys being strings)

        # update display options:
        display_columns: int = 1

        # update control options:
        #  * the default mutable is for adding, removing, rearranging or
        #    renaming items. No extra option (like mutable_dict is added)

        display_options = Setting.Options.display_options + ["display_columns"]

    @dataclass(eq=False, order=False)
    class ExportOptions(Setting.ExportOptions):
        # An import via set_state() may discover an inconsistency between input
        # data and available keys. The following options control whether an
        # exception will be raised on (1) missing keys or (2) new keys.
        exception_on_missing_key: bool = True
        exception_on_new_key: bool = True
        # The type option could have been used to define whether new keys from
        # the input data are supposed to be taken over into the SettingDict
        # (True == add the new keys) but a corresponding option for removing
        # missing keys would have been missing. Therefore, importing uses the
        # following options while exporting remains using type.
        remove_missing_keys: bool = False
        add_new_keys: bool = False
        # Interpretation of option combinations:
        #  * remove/add and exception: Key will be added to (removed from)
        #    SettingDict and a warning message will be logged.
        #  * remove/add and NO exception: Key will be added to (removed from)
        #    Setting dict without any logging.
        #  * NO remove/add and NO exception: missing or new keys in input data
        #    will be silently ignored.
        #  * NO remove/add and exception: Exceptions on missing (or new) keys
        #    will be raised.
        #
        # Rationale on default values. There is not realy a most likely case
        # from the use cases listed above. However, add_new_keys cannot be set
        # to True without setting the type to true since importing a missing
        # key cannot work without having type information. Type was not set to
        # True since Setting implementation focused on a minumum get_state().
        # Hence, add_new_keys and remove_missing_keys are set to False. Setting
        # the exceptions to True was then selected for transprency to avoid
        # silent "misbehavior" just because of a type in JSON files.

    FullExport = ExportOptions(
        name=True,
        type=True,
        value_options=True,
        display_options=True,
        control_options=True,
        export_defaults=True,
        exception_on_missing_key=False,
        exception_on_new_key=False,
        remove_missing_keys=True,
        add_new_keys=True,
    )

    def __init__(
        self,
        settings: Mapping[str, Any] | None = None,
        storage: Storage | None = None,
        **kwargs,
    ):
        """Settings collected as dicitonary

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
        """
        # take over settings into kwarg values:
        if settings is not None and "value" not in kwargs:
            kwargs["value"] = settings
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
        self.default_constructor: None | Callable[[], Setting] = None

    def __len__(self):
        return self._value.__len__()

    def __iter__(self):
        return self._value.__iter__()

    def __getitem__(self, key: str):
        return self._value[key].value

    def _resolve_tuple(self, t: tuple) -> Setting:
        if not t or len(t) > 2:
            raise AppxfSettingError(
                f"SettingDict items that are tuples must contain a "
                f"Setting type as the first element. And, optionally "
                f"a value as the second type. You provided {t}."
            )
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
        """separated behavior to avoid too deep nesting

        Note that this is called from __init__() and __setitem__ in a
        try/except to add further error details. Intend of this function is
        otherwise identical to __setitem__().
        """
        # reject keys that are not strings
        if not isinstance(key, str):
            raise AppxfSettingError(
                f"Only string keys are supported. "
                f"You provided: {key} of type {type(key)}"
            )
        # reject new keys AND key replacement if not mutable:
        if not self.options.mutable:
            if key not in self._value:
                raise AppxfSettingError(
                    f"SettingDict({self.options.name}) "
                    f"mutable option is False. "
                    f"New keys cannot be added. You provided "
                    f"key {key} as new key"
                )
            if (
                isinstance(value, Setting)
                or (isinstance(value, type) and issubclass(value, Setting))
                or (isinstance(value, tuple))
            ):
                raise AppxfSettingError(
                    f"SettingDict({self.options.name}) "
                    f"mutable option is False and "
                    f"settings cannot be replaced. "
                    f"You provided for key {key}: {value}"
                )
        if isinstance(value, Setting):
            # transfering key name to setting if setting name is empty
            if not value.options.name:
                value.options.name = key
            self._value[key] = value
            return
        # setting classes are applied with default values
        if isinstance(value, type) and issubclass(value, Setting):
            self._value[key] = value()
            self._value[key].options.name = key
            return
        # If input is a tuple, first should be the type and the second,
        # optional element, the value.
        if isinstance(value, tuple):
            self._value[key] = self._resolve_tuple(value)
            if not self._value[key].options.name:
                self._value[key].options.name = key
            return
        # What is left is not a tuple (type, value) nor a Setting class/object.
        # The key must exist and the value is applied to the existing Setting's
        # value:
        if key in self._value.keys():
            self._value[key].value = value
        # Or, the new Setting object is created:
        else:
            self._value[key] = Setting.new(type(value), value=value)
        # apply name:
        if not self._value[key].options.name:
            self._value[key].options.name = key

    # TODO: there should be a try/catch at least for the last two settings to
    # add the failing key to the error message from Setting. Like "Cannot set
    # key {key} with following error message from the Setting class. "

    def __setitem__(self, key, value) -> None:
        try:
            self._set_item(key, value)
        except (AppxfSettingError, AppxfSettingConversionError) as err:
            raise AppxfSettingError(
                f"Cannot set {key} in SettingDict({self.options.name}). "
                f"You provided value {value} of type {value.__class__}."
            ) from err

    def __delitem__(self, key):
        if self.options.mutable:
            del self._value[key]
        else:
            raise AppxfSettingError(
                f"SettingDict({self.options.name}) "
                f"mutable option is False and "
                f"items cannot be deleted. "
                f"You tried to delete key {key}"
            )

    def get_setting(self, key) -> Setting:
        """Access Setting object"""
        return self._value[key]

    def sort(self, reverse: bool = False):
        """Sort the keys of the SettingDict"""
        self._value = OrderedDict(
            sorted(self._value.items(), key=lambda item: item[0], reverse=reverse)
        )

    # ## Storage Behavior

    def set_storage(self, storage: Storage):
        """Set storage to support store()/load()"""
        self._storage = storage

    _state_version = 2

    def get_state(
        self, options: SettingDict.ExportOptions | None = None, **kwargs
    ) -> object:
        # handle export options:
        if options is None:
            export_options = self.ExportOptions.new_from_kwarg(kwargs)
        else:
            kwargs["options"] = options
            export_options = self.ExportOptions.new_from_kwarg(kwarg_dict=kwargs)
        Setting.ExportOptions.raise_error_on_non_empty_kwarg(kwargs)

        # build up the settings part (value field in normal settings):
        settings = OrderedDict()
        for key, setting in self._value.items():
            this_data = setting.get_state(options=export_options)
            # strip name if name is key - to avoid cluttering output by
            # maintaining the name twice.
            if (
                isinstance(this_data, OrderedDict)
                and "name" in this_data
                and this_data["name"] == key
            ):
                this_data.pop("name")
            # there are some specialties for dictionary handling (value field
            # is a dict):
            if isinstance(setting, SettingDict):
                # top-level SettingDict get_state() must have '_version' field
                # but dict of dict shall not have it. If must be removed in
                # this loop:
                this_data.pop("_version")
                # top-level setting dict shall not have the type but dict of
                # dict shall declare it (if requested). It must be added
                # here:
                if export_options.type:
                    if "_settings" in this_data:
                        this_data["type"] = self.get_type()
                        this_data.move_to_end("type", last=False)
                    else:
                        this_data = OrderedDict(
                            {"type": self.get_type(), "_settings": this_data}
                        )
            else:
                # only if value is not a dict, the value field is stripped
                # (simplified JSON export) if it's the only field:
                if list(this_data.keys()) == ["value"]:
                    this_data = this_data["value"]

            settings[key] = this_data
        # settings are not yet put into data - this will depend on the point
        # whether the dictionary to export does have further options..
        #
        # ..and for options, we rely on get_state() from Setting implementation
        option_data = super().get_state(options=export_options)
        # the value included in there must be removed again (already handled
        # above):
        option_data.pop("value", None)
        # type shall not be exported on the top-level:
        option_data.pop("type", None)

        if not option_data:
            # simple output:
            data = settings
            data["_version"] = self._state_version
            data.move_to_end("_version", last=False)
        else:
            # output for dict with options:
            data = OrderedDict({"_version": self._state_version, "_settings": settings})
            data.update(option_data)
        return data

    def set_state(
        self, data: Mapping, options: SettingDict.ExportOptions | None = None, **kwargs
    ):
        # handle export options:
        if options is None:
            export_options = self.ExportOptions.new_from_kwarg(kwargs)
        else:
            kwargs["options"] = options
            export_options = self.ExportOptions.new_from_kwarg(kwargs)
        Setting.ExportOptions.raise_error_on_non_empty_kwarg(kwargs)

        # handle unexpected input:
        if not isinstance(data, MutableMapping):
            raise AppxfSettingError("Input to set_state must be a dictionary.")
        if "_version" not in data:
            raise AppxfSettingError(
                "Cannot determine data version, "
                'input data is not a dict with field "_version".'
            )
        if not data["_version"] == self._state_version:
            raise AppxfSettingError(
                f"Cannot handle version {data['_version']} of data, "
                f"supported is version {self._state_version} only."
            )

        # obtain the settings (either directly in data, or in "_settings")
        if "_settings" in data:
            settings = data.pop("_settings")
            setting_keys = list(settings.keys())
            # options must be updated:
            data.pop("_version", None)
            self.options.update_from_kwarg(data)
        else:
            settings = data
            setting_keys = [key for key in data.keys() if key not in ["_version"]]

        # check mismatch of keys:
        current_keys = set(self._value.keys())
        input_keys = set(setting_keys)
        new_keys = input_keys - current_keys
        missing_keys = current_keys - input_keys
        # key list to handle starts with the full set of keys (available and
        # input):
        key_list = current_keys | input_keys
        # hanlde missing keys:
        if missing_keys:
            message = (
                f"The following keys are maintained by "
                f"SettingDict({self.options.name}) "
                f"but not included in data. Missing are: {missing_keys}."
            )
            if not export_options.exception_on_missing_key:
                # nothing to report
                pass
            elif export_options.remove_missing_keys:
                # warning message, only:
                warnings.warn(AppxfSettingWarning(message))
            else:
                # exception expected:
                raise AppxfSettingError(message)

            if export_options.remove_missing_keys:
                for key in missing_keys:
                    del self._value[key]
            # in either case, the key list to handle stuff must not include
            # those missing keys:
            key_list = key_list - missing_keys

        # handle new keys:
        if new_keys:
            message = (
                f"The following keys are included in "
                f"set_state() data but not yet "
                f"maintained in SettingDict({self.options.name}). "
                f"Consider setting export option "
                f'"add_missing_keys" to True or '
                f'"exception_on_new_key" to False or '
                f"add the missing keys to the input data. "
                f"Missing keys are: {new_keys}."
            )
            if not export_options.exception_on_new_key:
                # nothing to report
                pass
            elif export_options.add_new_keys:
                # warning message, only:
                warnings.warn(AppxfSettingWarning(message))
            else:
                # exception expected:
                raise AppxfSettingError(message)

            if export_options.add_new_keys:
                for key in new_keys:
                    # to create the new setting, the type must be present or a
                    # default type must be set.
                    if (
                        not isinstance(settings[key], dict)
                        or "type" not in settings[key].keys()
                    ):
                        if self.default_constructor is None:
                            raise AppxfSettingError(
                                f"Key {key} does not yet exist in "
                                f"SettingDict({self.options.name}) "
                                f"but import data does not include "
                                f"type information. "
                                f"Data only comprises: {settings[key]}"
                            )
                        else:
                            self._value[key] = self.default_constructor()
                    else:
                        self._value[key] = Setting.new(settings[key]["type"])
                    # also restore setting name:
                    self._value[key].options.name = key
            else:
                # strip new keys from keys to be updated
                key_list = key_list - new_keys

        # cycle through settings that must be taken over (key_list):
        for key in key_list:
            # correct simplified format for plain values that are not nested
            # dicts:
            if isinstance(settings[key], dict):
                this_setting_data = settings[key]
            else:
                this_setting_data = {"value": settings[key]}

            # setting value and options from setting data input
            if key in key_list:
                # ensure the setting type is correct:
                if "type" in this_setting_data and export_options.type:
                    this_type = this_setting_data["type"]
                    supported_types = self._value[key].get_supported_types()
                    if (
                        this_type not in supported_types
                        and this_type != self._value[key].get_type()
                    ):
                        raise AppxfSettingError(
                            f'Cannot set_state() key "{key}" in '
                            f"SettingDict({self.options.name}). "
                            f"Setting is of type "
                            f"{self._value[key].__class__.__name__} "
                            f"while provided type is "
                            f"{this_setting_data['type']}."
                        )

                # ensure _version being available in nested dicts. Note that
                # correct state_version is already checked above.
                if isinstance(self._value[key], SettingDict):
                    this_setting_data["_version"] = self._state_version

                self._value[key].set_state(this_setting_data, options=export_options)
                # restore setting name:
                if not self._value[key].options.name:
                    self._value[key].options.name = key
                # TODO: is the above actually necessary? If SettingDict is
                # implemented as expected, any Setting that is adde will have
                # the right name.

    def set_default_constructor_for_new_keys(
        self, default_constructor: None | Callable[[], Setting]
    ):
        """Set the constructor for new keys upon set_state/load

        This constructor is used when a new key is supposed to be loaded that
        would have no type information. This setting only applies on this level
        and the default type is not known to any nested dicts. The default type
        must support default construction ().

        This option is commonly used for SettingDicts that represent a database
        to entries of the same type. This setting allows storage of the
        database without adding type information.
        """
        self.default_constructor = default_constructor

    # ## Setting behavior

    @classmethod
    def get_default(cls) -> Any:
        return {}

    @classmethod
    def get_supported_types(cls) -> list[type | str]:
        return ["dictionary", "dict", MutableMapping]

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
                f"Cannot set value of type {type(value)} "
                f"for SettingDict({self.options.name}): "
                f"{value}. See subsequent error message."
            ) from err
        # detect removed keys:
        if not self.options.mutable:
            for key in self._value:
                if key not in value:
                    raise AppxfSettingError(
                        f"SettingDict({self.options.name}) mutable option "
                        f"is False and "
                        f"items cannot be deleted. "
                        f"Input value did not contain key {key}."
                    )

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
                f"Value must be a Mapping. You provided {value} of type {type(value)}."
            )
        for key, setting in value.items():
            if not isinstance(key, str):
                return False, AppxfSettingError(
                    f"Only string keys are supported. "
                    f"You provided: {key} of type {type(key)}"
                )
            if isinstance(setting, Setting):
                continue
            if isinstance(setting, type) and issubclass(setting, Setting):
                continue
            if isinstance(setting, tuple) or key not in self._value:
                try:
                    tmp_setting = SettingDict()
                    tmp_setting["err"] = setting
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
                else:
                    # pragma: no cover  # Rationale: the above else path is
                    # defensive code. See "this should not happen" in error
                    # message.
                    raise AppxfSettingError(
                        f"Value for {key} was invalid but did not throw an "
                        f"error when trying to set. This should not happen"
                    )

        return True, None

    def to_string(self) -> str:
        # Return empty string in case SettingDict does not contain settings:
        if not self._value:
            return ""
        return str(self.value)
