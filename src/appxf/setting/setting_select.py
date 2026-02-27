# Copyright 2024-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
"""Implementation of SettingSelect, selecting a value from a predefined list"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from .setting import AppxfSettingError, Setting, _BaseTypeT
from .setting_extension import SettingExtension, _BaseSettingT

# Intent is to support data like long text templates by selecting and
# referencing it by a title.
#
# The following differences apply to standard settings:
#   * Input is a string from a predefined list (drop down, no reason for other
#     types since it's purpose is "name for the setting value")
#   * SettingSelect internally maintains an additional Setting object as base
#     setting. It can be configured to (1) store this value upon get_state()
#     as well as (2) returning it as it's value.
#
# SettingSelect can also be configured to have a changable selection list.

# Simple Use Case: Text Templates.
#
# An application provides template texts for Emails that can be displayed and
# choosen from a SettingSelect. The select would be too long to reference the
# whole text such that only a title appears in the list.

# Storable Use Case: Storable Email Templates
#
# An application would allow to compose and store new text templates for Emails
# (see simple use case).

# Storable Focus Use Case: Translations
#
# The transtlation keywords (list selection keys) are fixed but the user can
# edit the translations (the values SettingSelect list items).

# Given from the above examples, there is different behavior that may or may
# not be possible:
#   1) Adding or removing new selectable items >> mutable_items
#   2) Changing the value behind a selectable item
#
# If neither (1) or (2) is possible, the selection list is known at
# construction time and no storage of the selection list is necessary. Only (1)
# possible is not reasonable, but only (2) has valid use cases (see
# translations use case).


class SettingSelect(SettingExtension[_BaseSettingT, _BaseTypeT]):
    """Setting restricted to a named, predefined set

    You typically provide the available options during construction, like:
    [sel = AppxfSetting.new('int', options={'one': 1, 'two': 2})].
    """

    # This AppxfSetting class is an extention on an existing AppxfSetting type
    # which is marked by this class attribute:
    setting_extension = "select"
    # The class can be instantiated either by AppxfSetting.new('int_select')
    # for string based type selection or via AppxfSetting[AppxfInt]() for
    # direct type based initialization.

    @dataclass(eq=False, order=False)
    class Options(Setting.Options):
        """options for setting select"""

        # update value options - None
        #
        # select_map and base_setting are potential value_options. But this
        # depends on the control options mutable_items, mutable_list and
        # custom_value.

        # update display options:
        #  * setting select will use larger entries by default:
        display_width: int = 60

        # update control options:
        #  * the values behind existing items can be changed:
        mutable_items: bool = True
        #  * items can be added to or removed from the selection list:
        mutable_list: bool = True
        #  * the value after selection from the list can be customized. The
        #    returned value of SettingSelect becomes this costomized value and
        #    the customized value is included in get_state():
        custom_value: bool = True
        # The default behavior has everything enabled. There was no clear
        # candidate for "the most common usage" such that the main argument to
        # enable all behavior is "people dont read the documentation" to know
        # what is possible. Once they see behavior they don't want, they should
        # be able to find the option to disable.
        control_options = Setting.Options.control_options + [
            "mutable_items",
            "mutable_list",
            "custom_value",
        ]

    def __init__(
        self,
        base_setting: _BaseSettingT,
        value: str | None = None,
        select_map: dict[str, Any] | None = None,
        **kwargs,
    ):
        # Initialization sequence matters quite a bit, be careful with changes!

        # SettingExtension places base_setting attribute before trying to set
        # the default value and _validated_conversion handles the base setting
        # first.
        super().__init__(base_setting=base_setting, **kwargs)

        # If select_map was already applied during intialization, we have to
        # pass it through add_option() to perform validations but we can just
        # re-apply them. The strange next line is just to fix the type hints.
        self.options: SettingSelect.Options = self.options
        self.select_map: dict[str, Any] = {}
        if select_map is not None:
            for key, map_value in select_map.items():
                self.add_select_item(key, map_value, ignore_mutable_options=True)

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
        # but the resulting value from the select_map is also applied to the
        # base_setting
        self.base_setting.value = self._value

    def _validated_conversion(self, value: str) -> tuple[bool, _BaseTypeT]:
        if value == self.base_setting.get_default():
            return True, self.base_setting.get_default()
        if value in self.select_map:
            return True, self.select_map[value]
        return False, self.base_setting.get_default()

    def get_state(self, **kwarg) -> dict:
        # we export as defined in setting
        out = super().get_state(**kwarg)
        # we have to export the select_map if either mutable_list or
        # mutable_items is True. Those options make the select_map part of the
        # user controlled values.
        if self.options.mutable_list or self.options.mutable_items:
            if isinstance(out, dict):
                out["select_map"] = deepcopy(self.select_map)
            else:
                out = {"value": out, "select_map": deepcopy(self.select_map)}
        # Like above, if custom_value is true, this base setting must be stored
        # as well. Currently, we store it with the same ExportOptions as the
        # SettingSelect, allowing no more fine grained control.
        if self.options.custom_value:
            if isinstance(out, dict):
                out["base_setting"] = self.base_setting.get_state(**kwarg)
            else:
                out = {
                    "value": out,
                    "base_setting": self.base_setting.get_state(**kwarg),
                }
        return out

    def set_state(self, data: dict, **kwarg):
        # extract setting_select specific data before forwarding to setting.
        # Note that option handling would throw warnings on unknown keys such
        # that keys from data must be removed:
        select_map = data.pop("select_map", None)
        base_setting = data.pop("base_setting", None)

        # select_map must be restored before loading the other values since
        # setting the value will perform a validation against the select_map:
        if select_map is not None:
            self.select_map = deepcopy(select_map)

        super().set_state(data, **kwarg)
        # catch base setting and apply - it must be applied afterwards since a
        # value for SettingSelect from above would also write the value of
        # base_setting.
        if base_setting is not None:
            self.base_setting.set_state(base_setting, **kwarg)

    # #################/
    # Option Handling
    # /
    def get_select_keys(self) -> list[str]:
        """Get list of selectable options

        The list is sorted alphabetically.
        """
        return sorted(list(self.select_map.keys()))

    def get_select_value(self, option: str) -> Any:
        """Get the value for a selectable item"""
        return self.select_map.get(option, self.base_setting.get_default())

    def delete_select_key(self, option: str):
        """Delete a selectable item by its key name"""
        if option not in self.select_map:
            raise AppxfSettingError(
                f'Cannot delete item "{option}" '
                f"since it does not exist for "
                f'"{self.options.name}".'
            )
        if not self.options.mutable_list:
            raise AppxfSettingError(
                f'Cannot delete item "{option}" '
                f"since mutable_list is False for "
                f'"{self.options.name}".'
            )
        original_options = self.get_select_keys()
        if option in self.select_map:
            self.select_map.pop(option)
        if option == self.input:
            index = original_options.index(option)
            new_list = self.get_select_keys()
            if not new_list:
                self.value = ""
            elif index < len(new_list):
                self.value = new_list[index]
            else:
                self.value = new_list[-1]

    def add_select_item(
        self, option: str, value: Any, ignore_mutable_options: bool = False
    ):
        """Add a new item to the select list by key and value"""
        if option not in self.select_map:
            if not self.options.mutable_list and not ignore_mutable_options:
                raise AppxfSettingError(
                    f'Cannot add the new item "{option}" '
                    f"since mutable_list is False for "
                    f'"{self.options.name}".'
                )
            # no check for mutable_item since a complete new one is added
        else:
            # no check for mutable_list since an existing one is being altered:
            if not self.options.mutable_items and not ignore_mutable_options:
                raise AppxfSettingError(
                    f'Cannot change item "{option}" since '
                    f"mutable_items is False for "
                    f'"{self.options.name}".'
                )
        # We try to set the value and take error message from there:
        if not self.base_setting.validate(value):
            raise AppxfSettingError(
                f"Cannot add option [{option}] with value {value} of type "
                f"{value.__class__.__name__} because the value is not valid."
            )
        # We also take the readily transformed value, not just the input
        self.select_map[option] = value
