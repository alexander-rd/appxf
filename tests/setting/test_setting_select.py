# Copyright 2025-2026 the contributors of APPXF (github.com/alexander-rd/appxf)
# SPDX-License-Identifier: Apache-2.0
import pytest

from appxf.setting import Setting, SettingSelect

def test_init_default():
    setting = SettingSelect(Setting.new(str))
    # see option definition in SettingSelect for reasons on the expected
    # values:
    assert setting.options.mutable_items
    assert setting.options.mutable_list
    assert setting.options.custom_value
    assert setting.get_select_keys() == []

def test_init_with_items():
    setting = SettingSelect(
        Setting.new(str),
        value='A',
        select_map={'A': 'One', 'C': 'Three', 'B': 'Two'})
    # obtions are always sorted alphabetically:
    assert setting.get_select_keys() == ['A', 'B', 'C']
    assert setting.value == 'One'

def test_add_delete_cycle():
    setting = SettingSelect(
        Setting.new(str),
        value='B',
        select_map={'A': 'One', 'B': 'Two', 'D': 'Four'})
    assert setting.get_select_keys() == ['A', 'B', 'D']
    assert setting.value == 'Two'
    # adding D:
    setting.add_select_item('C', 'Three')
    assert setting.get_select_keys() == ['A', 'B', 'C', 'D']
    assert setting.value == 'Two'
    # removing B:
    setting.delete_select_key('B')
    assert setting.get_select_keys() == ['A', 'C', 'D']
    # removing B drops the selection to the next available option (C)
    assert setting.value == 'Three'
    # removing C drops back to D
    setting.delete_select_key('C')
    assert setting.get_select_keys() == ['A', 'D']
    assert setting.value == 'Four'
    # removing D now drops to A:
    setting.delete_select_key('D')
    assert setting.get_select_keys() == ['A']
    assert setting.value == 'One'

def test_allowed_values_for_default():
    setting = SettingSelect(
        Setting.new(str),
        select_map={'A': 'One', 'B': 'Two'})
    setting.options.custom_value = False
    # initial value
    assert setting.value == ''
    assert setting.base_setting.value == ''
    # setting 'A' and 'B' is allowed
    setting.value = 'A'
    assert setting.value == 'One'
    assert setting.base_setting.value == 'One'
    setting.value = 'B'
    assert setting.value == 'Two'
    assert setting.base_setting.value == 'Two'

    # !! There is no blocking point from writing to base_setting directly. But
    #    it will not affect the value returned from the setting_select
    setting.base_setting.value = 'something'
    assert setting.base_setting.value == 'something'
    assert setting.value == 'Two'

def test_allowed_values_custom_value():
    setting = SettingSelect(
            Setting.new(str, name='base'),
            name='select',
            select_map={'A': 'One', 'B': 'Two'})
    setting.value = 'B'
    assert setting.value == 'Two'
    assert setting.base_setting.value == 'Two'
    # with custom_value being True, writing to the base_setting will return
    # it's content also in setting value:
    setting.base_setting.value = 'something'
    assert setting.base_setting.value == 'something'
    assert setting.value == 'something'


def test_get_set_cycle():
    setting = SettingSelect(
        Setting.new(str),
        name='select',
        select_map={'A': 'One', 'B': 'Two'})
    setting.value = 'A'
    data = setting.get_state(value_options=True)
    data_select_map = data['select_map']
    restored_setting = SettingSelect(Setting.new(str))
    restored_setting.set_state(data)
    # to ensure the restored select_map is fully copied from data, we overwrite
    # the corresponding data element with new content
    assert isinstance(data, dict)
    data_select_map['A'] = 'incorrectA'
    data_select_map['B'] = 'incorrectB'

    assert restored_setting.get_select_keys() == ['A', 'B']
    assert restored_setting.value == 'One'
    restored_setting.value = 'B'
    assert restored_setting.value == 'Two'

# TODO: test the state after REMOVING the data object. There is always the risk
# of taking only a reference to the select_map and not taking a deepcopy.

def test_get_set_with_custom_value():
    setting = SettingSelect(
        Setting.new(str, name='base'),
        name='select',
        select_map={'A': 'One', 'B': 'Two'},
        custom_value=True)
    setting.base_setting.value = 'something'
    assert setting.value == 'something'
    data = setting.get_state(value_options=True)
    restored_setting = SettingSelect(Setting.new(str), custom_value=True)
    restored_setting.set_state(data)
    assert restored_setting.get_select_keys() == ['A', 'B']
    assert restored_setting.value == 'something'