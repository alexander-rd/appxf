# Copyright 2024-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0

import pytest
from collections import OrderedDict
from copy import deepcopy

from appxf.setting import SettingDict, Setting
from appxf.setting import AppxfSettingError, AppxfSettingWarning
from appxf.setting import SettingString, SettingInt, SettingFloat, SettingBool

from appxf.storage import RamStorage

# REQ: SettingDict shall be able to be filled with settings by:
#  1) settings parameter on constructor taking a dictionary {key: setting}
#  2) [] assignment (one by one): setting_dict[key] = setting
#  3) .value interface taking a dictionary {key: setting}
#
# REQ: Each setting above can be (1) a plain value, (2) a setting class, (3) a
# setting object or (4) a tuple (type) or (type, value).

# List of sample init values:
init_values = [
    # Key   Value                       Type        Value_Out       String_Out
    # Value based input
    ('v1', 'test', 'string', 'test', 'test'),
    ('v2', 42, 'int', 42, '42'),
    ('v3', 1.123, 'float', 1.123, '1.123'),
    ('v4', True, 'bool', True, '1'),
    # Setting class based input
    ('SC1', SettingString, 'string', '', ''),
    ('SC2', SettingInt, 'int', 0, '0'),
    ('SC3', SettingFloat, 'float', 0.0, '0.0'),
    ('SC4', SettingBool, 'bool', False, '0'),
    # Setting object based input
    ('SO1', Setting.new(str, 'test'), 'string', 'test', 'test'),
    ('SO2', Setting.new(int, 42), 'int', 42, '42'),
    ('SO3', Setting.new(float, 1.123), 'float', 1.123, '1.123'),
    ('SO4', Setting.new(bool, True), 'bool', True, '1'),
    # Tuple based input
    ('T1', ('pass', '123abc'), 'pass', '123abc', '123abc'),
    ('T2', ('email', 'some@one.com'), 'email', '', ''),
    ('T3', ('integer',), 'int', 0, '0'),
]


# construct a Setting object from one of the init_values tuples
def _get_setting_reference(t):
    if isinstance(t[1], tuple):
        # tuple based init with type+value
        if len(t[1]) == 2:
            return Setting.new(t[2], value=t[1][1])
        # tuple based init with type, only
        else:
            return Setting.new(t[2])
    if isinstance(t[1], type):
        # type based input
        return Setting.new(t[2])
    if isinstance(t[1], Setting):
        # Direct Setting based input
        return t[1]
    return Setting.new(t[2], value=t[1])


# verify a setting dict against the init_value tuples
def verify_setting_dict(setting_dict: SettingDict, t_list: list[tuple]):
    for t in t_list:
        setting_ref = _get_setting_reference(t)
        assert setting_dict[t[0]] == setting_ref.value
        assert isinstance(setting_dict.get_setting(t[0]), type(setting_ref))
        assert setting_dict.get_setting(t[0]).value == setting_ref.value
        assert setting_dict.get_setting(t[0]).to_string() == setting_ref.to_string()
        # checking input/value interfaces:
        assert setting_dict.value[t[0]] == setting_ref.value
        assert setting_dict.input[t[0]] == setting_ref.input


# manual filling
def test_setting_dict_init_and_fill():
    setting_dict = SettingDict()
    for t in init_values:
        setting_dict[t[0]] = t[1]
    verify_setting_dict(setting_dict, init_values)


# init by dict
def test_setting_dict_init_by_dict():
    # build dict:
    dict_input = {t[0]: t[1] for t in init_values}
    setting_dict = SettingDict(dict_input)
    verify_setting_dict(setting_dict, init_values)


# empty init, set by value
def test_setting_dict_init_by_value():
    setting_dict = SettingDict()
    setting_dict.value = {t[0]: t[1] for t in init_values}
    verify_setting_dict(setting_dict, init_values)


# Testing invalid inputs - three test cases, each - for __init__, [] and .value
# interfaces.

failure_cases = [
    # TC name   # settings input   # strings that must be in error message
    ('input type', 42, [f'42 of type {int}']),
    (
        'invalid key',
        {42: (str)},
        [f'42 of type {int}', 'Only string keys are supported'],
    ),
    ('invalid value', {'test': ('email', 'fail')}, []),
    ('empty tuple', {'test': tuple()}, ['()']),
    ('long tuple', {'test': (1, 2, 3)}, ['(1, 2, 3)']),
]


@pytest.mark.parametrize(
    'name, settings, error_parts', failure_cases, ids=[t[0] for t in failure_cases]
)
def test_setting_dict_invalid_init(name, settings, error_parts):
    with pytest.raises(AppxfSettingError) as exc_info:
        SettingDict(settings=settings)
    print(exc_info.value)
    print(exc_info.value.__cause__)
    assert 'Cannot set value' in str(exc_info.value)
    assert 'for SettingDict' in str(exc_info.value)
    for part in error_parts:
        assert part in str(exc_info.value) + str(exc_info.value.__cause__)


@pytest.mark.parametrize(
    'name, settings, error_parts', failure_cases, ids=[t[0] for t in failure_cases]
)
def test_setting_dict_invalid_value(name, settings, error_parts):
    setting_dict = SettingDict()
    with pytest.raises(AppxfSettingError) as exc_info:
        setting_dict.value = settings
    print(exc_info.value)
    print(exc_info.value.__cause__)
    assert 'Cannot set value' in str(exc_info.value)
    assert 'for SettingDict' in str(exc_info.value)
    for part in error_parts:
        assert part in str(exc_info.value) + str(exc_info.value.__cause__)


@pytest.mark.parametrize(
    'name, settings, error_parts', failure_cases, ids=[t[0] for t in failure_cases]
)
def test_setting_dict_invalid_setitem(name, settings, error_parts):
    setting_dict = SettingDict()
    if not isinstance(settings, dict):
        # those cases are only for __init__and value assignments
        return
    for key, value in settings.items():
        with pytest.raises(AppxfSettingError) as exc_info:
            setting_dict[key] = value
    print(exc_info.value)
    print(exc_info.value.__cause__)
    assert 'Cannot set ' in str(exc_info.value)
    assert 'in SettingDict' in str(exc_info.value)
    for part in error_parts:
        assert part in str(exc_info.value) + str(exc_info.value.__cause__)


def test_setting_dict_value_as_string():
    setting_dict = SettingDict({'test': 'some'})
    assert "{'test': 'some'}" == setting_dict.to_string()
    # Note that to_string() is a mandatory interface for Setting behavior.
    # There is no reason, yet to support __str__().


# ####################/
# Value Manipulations
# ///////////////////


def test_setting_dict_set_valid_value():
    setting_dict = SettingDict({'test': ('email', 'my@email.com')})
    setting_dict['test'] = 'new@email.com'
    assert setting_dict['test'] == 'new@email.com'
    assert setting_dict.get_setting('test').value == 'new@email.com'


def test_setting_dict_set_via_value():
    setting_dict = SettingDict({'test': ('email', 'my@email.com')})
    setting_dict.value = {'test': 'new@email.com'}
    assert setting_dict['test'] == 'new@email.com'
    assert setting_dict.get_setting('test').value == 'new@email.com'


def test_setting_dict_overwriting_by_setting_object():
    setting_dict = SettingDict({'test': ('bool', False)})
    assert not setting_dict['test']
    assert isinstance(setting_dict.get_setting('test'), SettingBool)
    # overwrite by Email
    setting_dict['test'] = Setting.new('string', 'some')
    assert setting_dict['test'] == 'some'
    assert isinstance(setting_dict.get_setting('test'), SettingString)


def test_setting_dict_overwriting_by_setting_class():
    setting_dict = SettingDict({'test': ('bool', False)})
    assert not setting_dict['test']
    assert isinstance(setting_dict.get_setting('test'), SettingBool)
    # overwrite by Email
    setting_dict['test'] = SettingInt
    assert setting_dict['test'] == SettingInt.get_default()
    assert isinstance(setting_dict.get_setting('test'), SettingInt)


def test_setting_dict_overwriting_by_tuple():
    setting_dict = SettingDict({'test': ('bool', False)})
    assert not setting_dict['test']
    assert isinstance(setting_dict.get_setting('test'), SettingBool)
    # overwrite by Email
    setting_dict['test'] = ('string', 'some')
    assert setting_dict['test'] == 'some'
    assert isinstance(setting_dict.get_setting('test'), SettingString)


# REQ: When updating a value of a setting maintained by SettingDict, the
# setting object shall remain the same. Rationale: The setting object may
# already be referenced by others like GUI or application.


def test_setting_dict_keeps_setting_object():
    setting_dict = SettingDict({'test': (str, 'init')})
    assert setting_dict['test'] == 'init'
    init_object = setting_dict.get_setting('test')
    # set new value
    setting_dict['test'] = 'new'
    assert setting_dict['test'] == 'new'
    new_object = setting_dict.get_setting('test')
    assert new_object is init_object
    # set overwriting variant
    setting_dict['test'] = (str, 'overwriting')
    assert setting_dict['test'] == 'overwriting'
    new_object = setting_dict.get_setting('test')
    assert new_object is not init_object


def test_setting_dict_get_nonexisting():
    setting_dict = SettingDict()
    with pytest.raises(KeyError):
        setting_dict['test']


def test_setting_dict_set_invalid_after_delete():
    # test case derived from test_setting_dict_set_invalid_value
    setting_dict = SettingDict({'test': ('email', 'my@email.com')})
    del setting_dict['test']
    setting_dict['test'] = 'fail'
    assert setting_dict['test'] == 'fail'
    assert setting_dict.get_setting('test').value == 'fail'
    assert setting_dict.get_setting('test').__class__ == SettingString


def test_setting_dict_delete_non_existing():
    setting_dict = SettingDict()
    with pytest.raises(KeyError):
        del setting_dict['test']


def test_setting_dict_nested():
    setting_dict = SettingDict(
        settings={'int': (int, '42'), 'nested': {'int': (int, '13')}}
    )
    assert setting_dict['int'] == 42
    assert setting_dict['nested'] == {'int': 13}
    assert setting_dict['nested']['int'] == 13
    # verify same based on value
    assert setting_dict.value['int'] == 42
    assert setting_dict.value['nested'] == {'int': 13}
    assert setting_dict.value['nested']['int'] == 13
    # and verify the input which are corresponding strings:
    assert setting_dict.input['int'] == '42'
    assert setting_dict.input['nested'] == {'int': '13'}
    assert setting_dict.input['nested']['int'] == '13'


# REQ: When updating SettingDict via .value with some invalid values, the
# values shall not be applied in case the error is cought.
def test_setting_dict_invalid_not_applied():
    setting_dict = SettingDict(
        settings={
            'A': ('email', 'a@something.de'),
            'B': ('email', 'b@something.de'),
            'C': ('email', 'c@something.de'),
        }
    )
    # some checks of the initialization
    assert 'a@' in setting_dict['A']
    assert 'b@' in setting_dict['B']
    assert 'c@' in setting_dict['C']
    for key in setting_dict:
        assert isinstance(
            setting_dict.get_setting(key), type(Setting.new('email'))
        )
    # cycle through keys and try to apply a wrong value to each of those keys.
    # Only checking one position would not be sufficient in case SettingDict
    # already fails with the first assignment. No assumptions on order of
    # execution are made.
    for change_key in setting_dict:
        change_dict = setting_dict.value
        change_dict[change_key] = 'wrong-email'
        with pytest.raises(AppxfSettingError) as exc_info:
            setting_dict.value = change_dict
        assert 'wrong-email' in str(exc_info.value)
        # same checks as after init (no changes must be applied)
        assert 'a@' in setting_dict['A']
        assert 'b@' in setting_dict['B']
        assert 'c@' in setting_dict['C']
        for key in setting_dict:
            assert isinstance(
                setting_dict.get_setting(key), type(Setting.new('email'))
            )


# REQ: When changing the underlying Setting directly, the value returned by
# SettingDict must appear updated accordingly.
#
# Origin: The initial implementation used UserDict with a duplicate storage
# for values in the UserDict.data. This implementation did not satisfy the
# requirement.
#
# Rationale: The GUI implementation has a GUI for just a Setting on top of
# which the GUI for SettingDict is build.
def test_setting_dict_update_on_setting():
    setting_dict = SettingDict()
    setting_dict['test'] = (str, 'seomething')
    setting = setting_dict.get_setting('test')
    setting.value = 'new'
    assert setting.input == 'new'
    assert setting.value == 'new'
    assert setting_dict['test'] == 'new'
    assert setting_dict.get_setting('test').input == 'new'
    assert setting_dict.get_setting('test').value == 'new'


# REQ: When not mutable, changing maintained settings shall still be possible.
# Rationale: setting values are controlled by THEIR respective mutable obtion.
def test_setting_dict_not_mutable_setting_changes():
    setting_dict = SettingDict(settings={'test': (str, 'init')})
    setting_dict['test'] = (str, 'init')
    setting_dict.options.mutable = False
    assert setting_dict['test'] == 'init'

    setting_dict['test'] = 'changed[]'
    assert setting_dict['test'] == 'changed[]'

    setting_dict.value = {'test': 'changed_value'}
    assert setting_dict['test'] == 'changed_value'


# For the following expected errors on "not mutable", the error messages are
# evaluated by this function:
def evaluate_not_mutable_error(err: Exception, case: str):
    print(err.value)
    print(err.value.__cause__)
    err_string = str(err.value) + str(err.value.__cause__)
    assert 'SettingDict() mutable option is False' in err_string
    if case == 'delete item':
        assert 'items cannot be deleted' in err_string
        assert 'key test' in err_string
    elif case == 'add item':
        assert 'New keys cannot be added' in err_string
        assert 'You provided key test_new as new key'
    elif case == 'overwrite item':
        assert 'settings cannot be replaced' in err_string
        assert 'You provided value' in err_string
        assert 'of type <' in err_string
    else:
        raise Exception(f'Case {case} is unknown.')


# REQ: When not mutable, removing or adding items shall not be possible on all
# interfaces ([] and value) except init. Note that this includes the
# possibility of renaming.


def test_setting_dict_not_mutable_delete_via_value():
    setting_dict = SettingDict(settings={t[0]: t[1] for t in init_values})
    setting_dict['test'] = (str, 'init')
    setting_dict.options.mutable = False

    # try to delete
    values = setting_dict.value
    del values['test']
    with pytest.raises(AppxfSettingError) as exc_info:
        setting_dict.value = values
    evaluate_not_mutable_error(exc_info, 'delete item')
    verify_setting_dict(setting_dict, init_values)
    assert 'test' in setting_dict


def test_setting_dict_not_mutable_delete_via_delitem():
    setting_dict = SettingDict(settings={t[0]: t[1] for t in init_values})
    setting_dict['test'] = (str, 'init')
    setting_dict.options.mutable = False

    # try to delete
    with pytest.raises(AppxfSettingError) as exc_info:
        del setting_dict['test']
    evaluate_not_mutable_error(exc_info, 'delete item')
    verify_setting_dict(setting_dict, init_values)
    assert 'test' in setting_dict


def test_setting_dict_not_mutable_add_via_value():
    setting_dict = SettingDict(settings={t[0]: t[1] for t in init_values})
    setting_dict['test'] = (str, 'init')
    setting_dict.options.mutable = False

    values = setting_dict.value
    values['test_new'] = (str, 'should fail')
    with pytest.raises(AppxfSettingError) as exc_info:
        setting_dict.value = values
    evaluate_not_mutable_error(exc_info, 'add item')
    verify_setting_dict(setting_dict, init_values)
    assert 'test' in setting_dict
    assert 'test_new' not in setting_dict


def test_setting_dict_not_mutable_add_via_setitem():
    setting_dict = SettingDict(settings={t[0]: t[1] for t in init_values})
    setting_dict['test'] = (str, 'init')
    setting_dict.options.mutable = False

    with pytest.raises(AppxfSettingError) as exc_info:
        setting_dict['test_new'] = (str, 'should fail')
    evaluate_not_mutable_error(exc_info, 'add item')
    verify_setting_dict(setting_dict, init_values)
    assert 'test' in setting_dict
    assert 'test_new' not in setting_dict


# REQ: When not mutable, it shall not be possible to replace the setting
# objects by new ones. This includes providing Setting objects, Setting classes
# or tuples.


def test_setting_dict_not_mutable_overwrite_via_value():
    setting_dict = SettingDict(settings={'test': (str, 'init')}, mutable=False)

    values = setting_dict.value
    values['test'] = (str, 'should fail')
    with pytest.raises(AppxfSettingError) as exc_info:
        setting_dict.value = values
    evaluate_not_mutable_error(exc_info, 'overwrite item')

    values['test'] = SettingString
    with pytest.raises(AppxfSettingError) as exc_info:
        setting_dict.value = values
    evaluate_not_mutable_error(exc_info, 'overwrite item')

    values['test'] = SettingString()
    with pytest.raises(AppxfSettingError) as exc_info:
        setting_dict.value = values
    evaluate_not_mutable_error(exc_info, 'overwrite item')


def test_setting_dict_not_mutable_overwrite_via_setitem():
    setting_dict = SettingDict(settings={'test': (str, 'init')}, mutable=False)

    with pytest.raises(AppxfSettingError) as exc_info:
        setting_dict['test'] = (str, 'should fail')
    evaluate_not_mutable_error(exc_info, 'overwrite item')

    with pytest.raises(AppxfSettingError) as exc_info:
        setting_dict['test'] = SettingString
    evaluate_not_mutable_error(exc_info, 'overwrite item')

    with pytest.raises(AppxfSettingError) as exc_info:
        setting_dict['test'] = SettingString()
    evaluate_not_mutable_error(exc_info, 'overwrite item')


# #################/
# Stateful Behavior
# ////////////////
#
# Overview:
#  * test_setting_dict_get_state - evaluating correct returns of get_state()
#  * test_setting_dict_set_state_default - get_state() restoring based on
#    get_state() results when NO additional options apply
#  * test_setting_dict_set_state_type - set_state() handling related to type
#    handling. Either the type export_option is True or the input data contains
#    type information.


# to verify output structures, there will be expectations on the keys in two
# levels. Default output is only {'setting_A': 'value_A'} but with refined
# output options, this is {'setting_A': {'type': 'string', 'value':
# 'value_A'}}. The following function supports checking the expected keys on
# both levels.
def _verify_get_state_keys(
    data: OrderedDict,
    top_level_keys: list[str],
    setting_keys: list[str] | None = None,
    version_expected: bool = True,
):
    print(data)
    assert isinstance(data, OrderedDict), (
        f'Expected data to be OrderedDict. It is: {data.__class__}'
    )
    expected_top_level_keys = (
        ['_version'] if version_expected else []
    ) + top_level_keys

    actual_top_level_keys = list(data.keys())
    for key in expected_top_level_keys:
        assert key in data.keys(), f'Expected key "{key}" not in get_state() result.'
    for key in data.keys():
        assert key in expected_top_level_keys, f'get_state() has unexpected key {key}'
    # check correct order:
    for key in expected_top_level_keys:
        # we already checked that all top_level_keys are present
        assert actual_top_level_keys.index(key) == (
            expected_top_level_keys.index(key)
        ), (
            f'{key} is present but expected index is '
            f'{expected_top_level_keys.index(key)}, '
            f'actual key list is: {actual_top_level_keys}'
        )
    if setting_keys is None:
        # none of the keys should be a dict with 'value':
        for key in top_level_keys:
            assert not isinstance(data[key], OrderedDict) or 'value' not in data[key], (
                f'Key "{key}" is not expected to be a dictionary '
                f'containing "value". It is: {data[key]}'
            )
        return

    for setting_key, setting in data.items():
        if setting_key == '_version':
            continue
        assert isinstance(setting, OrderedDict), (
            f'Expected setting {setting_key} to be OrderedDict. '
            f'It is: {setting.__class__}.'
        )
        actual_setting_keys = list(setting.keys())
        for key in setting_keys:
            assert key in setting, (
                f'Setting "{setting_key}" '
                f'did not include key "{key}" in get_state().'
                f'Complete setting: {setting}'
            )
        for key in setting.keys():
            assert key in setting_keys, (
                f'Setting "{setting_key}" '
                f'had unexpected key "{key}" from get_state(). '
                f'Complete setting: {setting}'
            )
        for key in setting_keys:
            # we already checked that all setting_keys are present
            assert actual_setting_keys.index(key) == setting_keys.index(key), (
                f'{key} is present but expected index is {setting_keys.index(key)}, '
                f'actual key list is: {actual_setting_keys}'
            )


# REQ: get_state() shall include only the INPUT values for all settings. This
# applies to default options and export options.
def test_setting_dict_get_state_content_default():
    setting_dict = SettingDict(settings={'testA': (int, '42'), 'testB': (str, 'test')})
    data = setting_dict.get_state()
    _verify_get_state_keys(data, ['testA', 'testB'])
    assert data['testA'] == '42'
    assert data['testB'] == 'test'


# REQ: get_state() shall only include the setting names (from it's options) in
# the output if it is different from the key name.
def test_setting_dict_get_state_matching_name_handling():
    setting_dict = SettingDict(settings={'test': (int, '42')})
    setting_dict.get_setting('test').options.name = 'test'

    data = setting_dict.get_state(name=True)
    _verify_get_state_keys(data, ['test'])


# repetition with also exporting 'type' to catch an otherwise open branch:
def test_setting_dict_get_state_matching_name_handling2():
    setting_dict = SettingDict(settings={'test': (int, '42')})
    setting_dict.get_setting('test').options.name = 'test'

    data = setting_dict.get_state(name=True, type=True)
    _verify_get_state_keys(data, ['test'], ['type', 'value'])


def test_setting_dict_get_state_non_matching_name_handling():
    setting_dict = SettingDict(settings={'test': (int, '42')})
    setting_dict.get_setting('test').options.name = 'own_name'

    # we also check correct order with type
    data = setting_dict.get_state(name=True, type=True)
    _verify_get_state_keys(data, ['test'], ['type', 'value', 'name'])
    assert data['test']['type'] == 'integer'
    assert data['test']['name'] == 'own_name'


# extra test: setting name is not expected to be in output if export option is
# not set - even if name is different:
def test_setting_dict_get_state_non_matching_name_handling2():
    setting_dict = SettingDict(settings={'test': (int, '42')})
    setting_dict.get_setting('test').options.name = 'own_name'

    # we also check correct order with type
    data = setting_dict.get_state(name=False, type=True)
    _verify_get_state_keys(data, ['test'], ['type', 'value'])
    assert data['test']['type'] == 'integer'


# REQ: get_state() shall report INPUT value and type if type is TRUE in the
# export options.
def test_setting_dict_get_state_content_with_type():
    setting_dict = SettingDict(settings={'test': (int, '42')})
    data = setting_dict.get_state(type=True)
    _verify_get_state_keys(data, ['test'], ['type', 'value'])
    assert data['test']['value'] == '42'
    assert data['test']['type'] == 'integer'


# REQ: nested dicts must not contain the _version field. Rationale: The
# top-most dictionary _version will be the same for every nested version and
# implementation has minimum JSON export in mind.
#
# REQ: when exporting dicts with types, the outer one shall not include the
# type information while nested ones must include type information. Rationale:
# When having data from setting_dict.get_state() it's already clear that it
# must be put into a setting_dict.set_state(). .. And we have minimum JSON
# structures in mind.
def test_setting_dict_get_state_nested_dict():
    setting_dict = SettingDict(settings={'test': {'int': (int, '42')}})
    data = setting_dict.get_state(type=True)
    _verify_get_state_keys(data, ['test'], ['type', '_settings'])
    _verify_get_state_keys(
        data['test']['_settings'], ['int'], ['type', 'value'], version_expected=False
    )
    assert data['test']['type'] == 'dictionary'
    assert data['test']['_settings']['int']['type'] == 'integer'
    assert data['test']['_settings']['int']['value'] == '42'


def test_setting_dict_get_state_nested_dict_with_options():
    export_options = SettingDict.ExportOptions(
        type=True, display_options=True, export_defaults=True
    )
    setting_dict = SettingDict(settings={'test': {'int': (int, '42')}})
    data = setting_dict.get_state(options=export_options)
    _verify_get_state_keys(
        data, ['_settings', 'visible', 'display_width', 'display_columns']
    )
    _verify_get_state_keys(data['_settings'], ['test'], version_expected=False)
    _verify_get_state_keys(
        data['_settings']['test'],
        ['type', '_settings', 'visible', 'display_width', 'display_columns'],
        version_expected=False,
    )
    _verify_get_state_keys(
        data['_settings']['test']['_settings'],
        ['int'],
        ['type', 'value', 'visible', 'display_width'],
        version_expected=False,
    )
    assert data['_settings']['test']['type'] == 'dictionary'
    assert data['_settings']['test']['_settings']['int']['type'] == 'integer'
    assert data['_settings']['test']['_settings']['int']['value'] == '42'


# REQ: set_state() shall restore a setting VALUE and INPUT if the setting is
# already existing.
def test_setting_dict_set_state_default():
    setting_dict = SettingDict(
        settings={
            'testInt': (int, '42'),
            'testEmail': ('email', 'someone@something.com'),
        }
    )
    data = setting_dict.get_state()
    setting_dict['testInt'] = 13
    setting_dict['testEmail'] = 'someoneelse@something.com'
    assert setting_dict.value['testInt'] == 13
    assert setting_dict.input['testInt'] == 13
    assert setting_dict['testEmail'] == 'someoneelse@something.com'

    setting_dict.set_state(data)
    assert setting_dict.value['testInt'] == 42
    assert setting_dict.input['testInt'] == '42'
    assert setting_dict['testEmail'] == 'someone@something.com'


# REQ: set_state() shall catch some stupid errors like wrong type or version of
# input data.
def test_setting_dict_set_state_default_wrong_type():
    setting_dict = SettingDict()
    with pytest.raises(AppxfSettingError) as exc_info:
        setting_dict.set_state(['test'])

    assert 'Input to set_state must be a dictionary.' in str(exc_info.value)


def test_setting_dict_set_state_default_missing_version():
    setting_dict = SettingDict()
    with pytest.raises(AppxfSettingError) as exc_info:
        setting_dict.set_state(OrderedDict())

    # sample: Cannot determine data version, input data is not a dict with
    # field "_version".
    assert (
        'Cannot determine data version, input data is not a dict with field "_version"'
        in str(exc_info.value)
    )


def test_setting_dict_set_state_default_wrong_version():
    setting_dict = SettingDict()
    with pytest.raises(AppxfSettingError) as exc_info:
        setting_dict.set_state(OrderedDict({'_version': 1}))

    # sample: Cannot handle version 1 of data, supported is version 2 only.
    assert 'Cannot handle version 1 of data' in str(exc_info.value)


# REQ: When data for set_state() includes a setting that is not yet maintained
# by SettingDict, there shall be an exception.
def test_setting_dict_set_state_default_new_key_exception():
    setting_dict = SettingDict(settings={'test': (int, '42')})
    data = setting_dict.get_state()

    del setting_dict['test']
    assert 'test' not in setting_dict
    with pytest.raises(AppxfSettingError) as exc_info:
        setting_dict.set_state(data)

    assert not setting_dict.keys()
    assert 'but not yet maintained in SettingDict' in str(exc_info.value)
    assert 'setting export option "add_missing_keys" to True' in str(exc_info.value)
    assert '"exception_on_new_key" to False' in str(exc_info.value)
    assert 'add the missing keys to the input data.' in str(exc_info.value)
    assert 'test' in str(exc_info.value)


# ...unless exceptions are turned off.
def test_setting_dict_set_state_default_new_key_no_exception():
    setting_dict = SettingDict(settings={'test': (int, '42')})
    data = setting_dict.get_state()

    del setting_dict['test']
    assert 'test' not in setting_dict
    setting_dict.set_state(data, exception_on_new_key=False)

    assert not setting_dict.keys()


# REQ: If a key maintained by SettingDict is not included in the input data, it
# shall result in an exception unless export_option exception_on_missing_key is
# False.
def test_setting_dict_set_state_default_missing_key_exception():
    setting_dict = SettingDict(settings={'A': (str, 'initA'), 'B': (str, 'initB')})
    data = setting_dict.get_state()
    setting_dict['testA'] = 'changedA'
    setting_dict['testB'] = 'changedB'

    dataA = deepcopy(data)
    del dataA['A']
    with pytest.raises(AppxfSettingError) as excA_info:
        setting_dict.set_state(dataA)

    # Note: there is NO requirement that the SettingDict state remains the same
    # in case of failures. While this is done for .value setting where validity
    # checks belong to the design of setting behavior - there will not be any
    # validity checks for set_state() and the complexity of adding this
    # behavior is omitted.

    # We repeat the same for B.
    dataB = deepcopy(data)
    del dataB['B']
    with pytest.raises(AppxfSettingError) as excB_info:
        setting_dict.set_state(dataB)

    for exc in [('A', str(excA_info.value)), ('B', str(excB_info.value))]:
        # sample: Key A is maintained by SettingDict() but not included in
        # data. Data for set_state() only included the keys:
        # odict_keys(['_version', 'B']).
        assert 'but not included in data' in exc[1]
        assert f"{exc[0]}" in exc[1]


# REQ: The output of get_state() shall restore missing keys with value AND
# input when applied to set_state() and type export option is true.
def test_setting_dict_set_state_new_key():
    setting_dict = SettingDict(settings={'test': (int, '42')})
    original_setting = setting_dict.get_setting('test')
    data = setting_dict.get_state(type=True)

    del setting_dict['test']
    assert 'test' not in setting_dict

    with pytest.warns(AppxfSettingWarning) as warn_info:
        setting_dict.set_state(data, add_new_keys=True)
    assert setting_dict['test'] == 42
    assert setting_dict.input['test'] == '42'
    assert setting_dict.get_setting('test') is not original_setting

    assert 'but not yet maintained in SettingDict' in str(warn_info[0].message)
    assert 'setting export option "add_missing_keys" to True' in str(
        warn_info[0].message
    )
    assert '"exception_on_new_key" to False' in str(warn_info[0].message)
    assert 'add the missing keys to the input data.' in str(warn_info[0].message)
    assert 'test' in str(warn_info[0].message)


# restoring keys apparently also must work for nested dicts (this covers some
# pecularities when handling nested dicts in set_state()):
def test_setting_dict_set_state_type_new_key_nested_dict():
    setting_dict = SettingDict(settings={'test': (dict, {'int': (int, '42')})})
    original_test: SettingDict = setting_dict.get_setting('test')
    original_int = original_test.get_setting('int')
    data = setting_dict.get_state(type=True)

    del setting_dict['test']
    assert 'test' not in setting_dict

    # default options (exceptions not disables) shall raise a warning:
    setting_dict.set_state(data, add_new_keys=True, exception_on_new_key=False)
    assert setting_dict['test']['int'] == 42
    assert setting_dict.input['test']['int'] == '42'
    assert setting_dict.get_setting('test') is not original_test
    assert setting_dict.get_setting('test').get_setting('int') is not original_int


# REQ: When using set_state() with a new key that does not include the type
# information (exported with type==False), there must be an Exception.
def test_setting_dict_set_state_type_new_key_no_type_exception():
    setting_dict = SettingDict(settings={'test': (int, '42')})
    setting_dict.options.name = 'TestDict'
    data = setting_dict.get_state()

    del setting_dict['test']
    assert 'test' not in setting_dict
    with pytest.raises(AppxfSettingError) as exc_info:
        setting_dict.set_state(data, exception_on_new_key=False, add_new_keys=True)

    assert not setting_dict.keys()
    assert 'Key test does not yet exist in SettingDict(TestDict)' in str(exc_info.value)
    assert 'but import data does not include type information' in str(exc_info.value)


def test_setting_dict_set_state_type_new_key_no_type_no_exception():
    setting_dict = SettingDict(settings={'test': (int, '42')})
    setting_dict.options.name = 'TestDict'
    data = setting_dict.get_state()

    del setting_dict['test']
    assert 'test' not in setting_dict

    setting_dict.set_state(data, type=True, exception_on_new_key=False)

    assert not setting_dict.keys()


# REQ: When using set_state() with type==True and keys already existent and
# type is same, the setting object must be retained. If type does not match,
# there must be an exception.
def test_setting_dict_set_state_type_ok():
    setting_dict = SettingDict(settings={'test': (int, '42')})
    original_setting = setting_dict.get_setting('test')
    data = setting_dict.get_state(type=True)

    setting_dict['test'] = '13'
    setting_dict.set_state(data, type=True, add_new_keys=True)
    assert setting_dict['test'] == 42
    assert setting_dict.input['test'] == '42'
    assert setting_dict.get_setting('test') is original_setting


# unless the type does not match.. ..that's still an exception:
def test_setting_dict_set_state_type_mismatch():
    setting_dict = SettingDict(settings={'test': (int, '42')})
    setting_dict.options.name = 'TestDict'
    data = setting_dict.get_state(type=True)

    print(setting_dict.get_setting('test'))
    setting_dict['test'] = (str, 'new')
    print(setting_dict.get_setting('test'))
    with pytest.raises(AppxfSettingError) as exc_info:
        setting_dict.set_state(data, type=True)
        print(setting_dict.get_setting('test'))

    assert 'Cannot set_state() key "test" in SettingDict(TestDict).' in str(
        exc_info.value
    )
    assert 'Setting is of type SettingString while provided type is integer.' in str(
        exc_info.value
    )


# REQ: According to remove_missing_key option, mising keys of input must be
# removed from SettingDict. Default is False and already tested above.
def test_setting_dict_set_state_missing_key_remove():
    setting_dict = SettingDict(
        settings={'test_int': (int, '42'), 'test_str': (str, 'test')}
    )
    data = setting_dict.get_state()

    setting_dict['test_int'] = 13
    assert setting_dict['test_int'] == 13
    setting_dict['test_str'] = 'changed'

    # remove test_str from input data:
    del data['test_str']
    # without disabling exceptions, there will still be a warning:
    with pytest.warns(AppxfSettingWarning) as warn_info:
        setting_dict.set_state(data, remove_missing_keys=True)
    assert 'test_str' not in setting_dict
    assert setting_dict['test_int'] == 42
    # check warnings content:
    assert 'but not included in data' in str(warn_info[0].message)
    assert 'test_str' in str(warn_info[0].message)
    assert 'test_int' not in str(warn_info[0].message)


# same test as above but not triggering the warning (switched off):
@pytest.mark.filterwarnings("error")
def test_setting_dict_set_state_missing_key_remove_no_warning():
    setting_dict = SettingDict(
        settings={'test_int': (int, '42'), 'test_str': (str, 'test')}
    )
    data = setting_dict.get_state()

    # remove test_str from input data:
    del data['test_str']
    setting_dict.set_state(
        data, remove_missing_keys=True, exception_on_missing_key=False
    )
    assert 'test_str' not in setting_dict
    assert setting_dict['test_int'] == 42


def test_setting_dict_storage_init():
    setting_dict = SettingDict(
        {'entry': ('email', 'some@any.de'), 'input_check': (int, '42')}
    )
    # storage is just dummy:
    assert isinstance(setting_dict._storage, RamStorage)
    # while storing works silently:
    setting_dict.store()
    setting_dict['entry'] = 'another@any.de'
    setting_dict['input_check'] = 13

    setting_dict.load()
    assert setting_dict['entry'] == 'some@any.de'
    assert setting_dict.input['input_check'] == '42'


def test_setting_dict_store_load_cycle():
    # we use an integer here since it differs in "input" and stored "value".
    # And we use an arbitrary string (email) to be a bit more verbose.
    setting_dict = SettingDict({'entry': ('email',), 'input_check': (int,)})
    storage = RamStorage()
    setting_dict.set_storage(storage)
    setting_dict['entry'] = 'before@store.com'
    setting_dict['input_check'] = '1'

    setting_dict.store()
    setting_dict['entry'] = 'after@store.com'
    setting_dict['input_check'] = '2'
    assert setting_dict.value['entry'] == 'after@store.com'
    assert setting_dict.input['input_check'] == '2'
    assert setting_dict.value['input_check'] == 2

    setting_dict_reload = SettingDict({'entry': ('email',), 'input_check': (int,)})
    setting_dict_reload.set_storage(storage)
    setting_dict_reload.load()
    assert setting_dict_reload['entry'] == 'before@store.com'
    assert setting_dict_reload.get_setting('entry').value == 'before@store.com'
    assert setting_dict_reload.get_setting('entry').input == 'before@store.com'
    assert setting_dict_reload['input_check'] == 1
    assert setting_dict_reload.get_setting('input_check').value == 1
    assert setting_dict_reload.get_setting('input_check').input == '1'


def test_setting_dict_store_load_invalid_init():
    storage = RamStorage()
    setting_dict = SettingDict(settings={'entry': ('email',)}, storage=storage)
    setting_dict.store()
    # This load should not fail. Even though we load an invalid value, it shall
    # be accepted since it is the default value:
    setting_dict.load()
    # loading an invalid value while a valid one is stored is intended
    # behavior as long as it is the default value:
    setting_dict['entry'] = 'someone@nowhere.com'
    assert setting_dict['entry'] == 'someone@nowhere.com'
    setting_dict.load()
    assert setting_dict['entry'] == ''
