import pytest

from kiss_cf.setting import Setting, SettingSelect

def test_init_default():
    setting = SettingSelect(Setting.new(str))
    assert setting.options.mutable_items
    assert not setting.options.custom_value
    assert setting.get_options() == []

def test_init_with_items():
    setting = SettingSelect(
        Setting.new(str),
        value='A',
        select_map={'A': 'One', 'C': 'Three', 'B': 'Two'})
    # obtions are always sorted alphabetically:
    assert setting.get_options() == ['A', 'B', 'C']
    assert setting.value == 'One'

def test_add_delete_cycle():
    setting = SettingSelect(
        Setting.new(str),
        value='B',
        select_map={'A': 'One', 'B': 'Two', 'D': 'Four'})
    assert setting.get_options() == ['A', 'B', 'D']
    assert setting.value == 'Two'
    # adding D:
    setting.add_option('C', 'Three')
    assert setting.get_options() == ['A', 'B', 'C', 'D']
    assert setting.value == 'Two'
    # removing B:
    setting.delete_option('B')
    assert setting.get_options() == ['A', 'C', 'D']
    # removing B drops the selection to the next available option (C)
    assert setting.value == 'Three'
    # removing C drops back to D
    setting.delete_option('C')
    assert setting.get_options() == ['A', 'D']
    assert setting.value == 'Four'
    # removing D now drops to A:
    setting.delete_option('D')
    assert setting.get_options() == ['A']
    assert setting.value == 'One'

def test_allowed_values_for_default():
    setting = SettingSelect(
        Setting.new(str),
        select_map={'A': 'One', 'B': 'Two'})
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
            select_map={'A': 'One', 'B': 'Two'},
            custom_value=True)
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
    restored_setting = SettingSelect(Setting.new(str))
    restored_setting.set_state(data)
    # to ensure the restored select_map is copied over, the following test is
    # added. But option handling automatically removes stuff from data such
    # that we only have to check that select_map is not included anymore
    # instead of tinkering with it:
    assert isinstance(data, dict)
    assert 'select_map' not in data

    assert restored_setting.get_options() == ['A', 'B']
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
    assert restored_setting.get_options() == ['A', 'B']
    assert restored_setting.value == 'something'