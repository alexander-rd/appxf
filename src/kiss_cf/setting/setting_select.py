''' Settings selecting a value from a predefined list '''
from __future__ import annotations
from typing import Any
from dataclasses import dataclass, field

from .setting import Setting, SettingExtension
from .setting import _BaseTypeT, _BaseSettingT, AppxfSettingError


# Intent is to support complex data like long text templates by selecting and
# referencing it by a title.
#
# The following differences apply to standard settings:
#   * Input is a string from a predefined list (drop down, no reason for other
#     types since it's purpose is "name for the setting value")
#   * It will be uncommon or not even possible to set the value directly
#
# A further extention is a configurable and storable selection. For standard
# settings, the application only knows the type of the setting. Select settings
# will have a changeable list of options which can be stored along or separate
# to the setting.

# TODO: should the custom type be the "storable" selection or at least
# something that supports the serialization?

# Simple Use Case: Text Inspection.
#
# The tool provides a set of Email texts that can be displayed by a list
# select. The select would be too long to reference the whole text such that
# only a title appears in the list.

# Storable Use Case: Storable Email Templates
#
# The tool user can store Email text templates into the configuration for
# reuse.

# Storable Focus Use Case: Translations
#
# The transtlation keywords (list selection keys) are fixed but the user can
# edit the translations (the values behind an AppxfStringSelection). The tool
# would use use the AppxfStringSelect conversions.

# Given from the above examples, there is different behavior that may or may
# not be possible:
#   1) Adding or removing new selectable items
#   2) Changing the value behind a selectable item
#
# If neither (1) or (2) is possible, the selection list is known at
# construction time and no storage is necessary. Only (1) possible is not
# reasonable, but only (2) has valid use cases.


class SettingSelect(SettingExtension[_BaseSettingT, _BaseTypeT]):
    ''' Setting restricted to a named, predefined set

    You typically provide the available options during construction, like:
    [sel = AppxfSetting.new('int', options={'one': 1, 'two': 2})].
    '''
    # This AppxfSetting class is an extention on an existing AppxfSetting type
    # which is marked by this class attribute:
    setting_extension = 'select'
    # The class can be instantiated either by AppxfSetting.new('int_select')
    # for string based type selection or via AppxfSetting[AppxfInt]() for
    # direct type based initialization.

    @dataclass(eq=False, order=False)
    class Options(Setting.Options):
        ''' options for setting select '''
        # update value options
        select_map: dict[str, Any] = field(default_factory=dict)
        value_options = Setting.Options.value_options + ['select_map']

        # update display options:
        #  * setting select will use larger entries by default:
        display_width: int = 60

        # update control options:
        #  * items can be added or removed to/from the select list:
        mutable_items: bool = True
        #  * the value after seletion can be customized and the customized
        #    value is stored additionally to the list of select items:
        custom_value: bool = False
        control_options = (Setting.Options.control_options +
                           ['mutable_items', 'custom_value'])
        # TODO: in contrast to the TWO options above, a fine grained options
        # would distinguish "being able to edit existing template items"
        # (without the ability to change the item names) and the full
        # capability to also add/remove and rename items in the select list.

    def __init__(self,
                 base_setting: _BaseSettingT,
                 value: str | None = None,
                 **kwargs):
        # Initialization sequence matters quite a bit, be careful with changes!

        # SettingExtension places base_setting attribute before trying to set
        # the default value and _validated_conversion handles default version
        # first.
        super().__init__(base_setting=base_setting,
                         **kwargs)

        # If select_map was already applied during intialization, we have to
        # pass it through add_option() to perform validations but we can just
        # reapply them. The strange next line is just to fix the typehints.
        self.options: SettingSelect.Options = self.options
        for key, map_value in self.options.select_map.items():
            self.add_option(key, map_value)

        # finally, set the intended value which may be one of the added options
        # above which is why value was not passed to the parent __init__()
        if value is not None:
            self.value = value
        else:
            self.value = self.base_setting.get_default()

    @property
    def value(self) -> _BaseTypeT:
        # return value depends on custom_value setting in options
        if self.options.custom_value:
            return self.base_setting.value
        # Any value writing will also update the base_setting's value. Only if
        # the base_value is updated directly, the above can make a difference.
        return self._value

    @value.setter
    def value(self, value: Any):
        # first step is like in setting implementation
        Setting.value.fset(self, value)  # type: ignore
        # but the result is also applied to the base_setting
        self.base_setting.value = self._value

    def _validated_conversion(self, value: str) -> tuple[bool, _BaseTypeT]:
        if value == self.base_setting.get_default():
            return True, self.base_setting.get_default()
        if value in self.options.select_map:
            return True, self.options.select_map[value]
        return False, self.base_setting.get_default()

    def get_state(self, **kwarg) -> object:
        # we export as defined in setting
        out = super().get_state(**kwarg)
        # but we may need to add the base_setting if the base setting is
        # maintained
        if self.options.custom_value:
            if isinstance(out, dict):
                out['base_setting'] = self.base_setting.get_state(**kwarg)
            else:
                out = {'value': out,
                       'base_setting': self.base_setting.get_state(**kwarg)}
        return out

    def set_state(self, data: object, **kwarg):
        super().set_state(data, **kwarg)
        # catch base setting and apply - it must be applied afterwards since
        # obtained value will be writtens
        if isinstance(data, dict) and 'base_setting' in data:
            self.base_setting.set_state(data['base_setting'], **kwarg)

    # #################/
    # Option Handling
    # /
    def get_options(self) -> list[str]:
        ''' Get list of selectable options

        The list is sorted alphabetically.
        '''
        return sorted(list(self.options.select_map.keys()))

    def get_option_value(self, option: str) -> Any:
        ''' Get the value for an option '''
        return self.options.select_map.get(option,
                                           self.base_setting.get_default())

    def delete_option(self, option: str):
        ''' Delete an option from selectable items '''
        original_options = self.get_options()
        if option in self.options.select_map:
            self.options.select_map.pop(option)
        if option == self.input:
            index = original_options.index(option)
            new_list = self.get_options()
            if not new_list:
                self.value = ''
            elif index < len(new_list):
                self.value = new_list[index]
            else:
                self.value = new_list[-1]

    def add_option(self, option: str, value: Any):
        ''' Add an option to the selectable items '''
        # We try to set the value and take error message from there:
        if not self.base_setting.validate(value):
            raise AppxfSettingError(
                f'Cannot add option [{option}] with value {value} of type '
                f'{value.__class__.__name__} because the value is not valid.')
        # We also take the readily transformed value, not just the input
        self.options.select_map[option] = value
