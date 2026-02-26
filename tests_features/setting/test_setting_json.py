# Copyright 2025-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
'''Serialization of SettingDict into JSON

Tests to ensure that the implementation adheres to the following concept goals:
 * JSON export shall be concise if storage is only about values
 * JSON export shall be flexible to include all sorts and options for a setting
   in the following abstraction steps:
    * values (inputs) only
    * setting options
    * extended settings including their base settings (with options) - like
      for SettingSelect
    * setting type to be able to restore settings for an empty SettingDict
'''

import pytest
from collections import OrderedDict
from appxf.setting import Setting, SettingDict, SettingEmail, SettingSelect
from appxf.storage import RamStorage, JsonSerializer, Storage


# Feature testing must apply context to storage:
@pytest.fixture(autouse=True)
def setup_storage_context():
    Storage.switch_context("test_setting_json")


def overwrite_with_defaults(setting_dict: SettingDict):
    '''Fill values with default values'''
    for key in setting_dict.keys():
        this_setting = setting_dict.get_setting(key)
        if isinstance(this_setting, SettingDict):
            overwrite_with_defaults(this_setting)
        elif isinstance(this_setting, SettingSelect):
            this_setting.value = this_setting.get_select_keys()[0]
        elif isinstance(this_setting, SettingEmail):
            this_setting.value = 'overwritten@something.de'
        else:
            this_setting.value = this_setting.get_default()


def verify_json(
    setting_dict: SettingDict,
    export_options: SettingDict.ExportOptions,
    expected_json: str,
    full_recovery: bool = False,
):
    raw_data = setting_dict.get_state(options=export_options)
    serialized_data = JsonSerializer.serialize(raw_data)

    # check serialization
    print(f'Produced JSON:\n{serialized_data.decode("utf-8")}')
    # print(f'Expected JSON:\n{expected_json}')
    assert expected_json[1:-5] == serialized_data.decode('utf-8')

    # check recovery
    original_inputs = setting_dict.input
    original_values = setting_dict.value
    overwrite_with_defaults(setting_dict)
    recovered_raw_data = JsonSerializer.deserialize(serialized_data)
    if full_recovery:
        recovered_dict = SettingDict()
    else:
        recovered_dict = setting_dict
    recovered_dict.set_state(recovered_raw_data, options=export_options)
    assert recovered_dict.input == original_inputs
    assert recovered_dict.value == original_values


def test_setting_json_simple():
    '''JSON for options with only values included - the most simple/reduced
    form of output (no options being set or set to stored)'''
    verify_json(
        setting_dict=SettingDict(
            OrderedDict(
                [
                    ('string', Setting.new('string', value='test')),
                    ('integer', Setting.new('int', value=42)),
                    (
                        'select',
                        Setting.new(
                            'select::string',
                            value='01',
                            select_map={'01': 'Value'},
                            custom_value=False,
                            mutable_items=False,
                            mutable_list=False,
                        ),
                    ),
                ]
            )
        ),
        export_options=SettingDict.ExportOptions(),
        expected_json='''
{
    "_version": 2,
    "string": "test",
    "integer": 42,
    "select": "01"
}
    ''',
        full_recovery=False,
    )


def test_setting_json_single_display_option():
    '''JSON for a few non-default options'''
    export_options = SettingDict.ExportOptions(value_options=True, display_options=True)
    setting_dict = SettingDict(
        {
            'string': Setting.new('string', value='test'),
            'integer': Setting.new('int', value=42),
            'select': Setting.new(
                'select::string',
                value='01',
                select_map={'01': 'test_value'},
                display_width=42,
                custom_value=False,
            ),
        }
    )

    verify_json(
        setting_dict,
        export_options=export_options,
        expected_json='''
{
    "_version": 2,
    "string": "test",
    "integer": 42,
    "select": {
        "value": "01",
        "display_width": 42,
        "select_map": {"01": "test_value"}
    }
}
    ''',
        full_recovery=False,
    )


def test_setting_json_full_options_export():
    '''JSON for options with and without options being set'''
    setting_dict = SettingDict(
        settings={
            'select': Setting.new(
                'select::string',
                value='01',
                select_map={'01': 'Value'},
                custom_value=True,
            )
        },
        # TODO: integer and select had "options_stored" set to True
        display_columns=3,
    )
    export_options = SettingDict.ExportOptions(
        control_options=True,
        value_options=True,
        display_options=True,
        export_defaults=True,
    )

    verify_json(
        setting_dict,
        export_options=export_options,
        expected_json='''
{
    "_version": 2,
    "_settings": {
        "select": {
            "value": "01",
            "visible": true,
            "display_width": 60,
            "mutable": true,
            "value_options_mutable": false,
            "display_options_mutable": false,
            "control_options_mutable": false,
            "mutable_items": true,
            "mutable_list": true,
            "custom_value": true,
            "select_map": {"01": "Value"},
            "base_setting": {
                "value": "Value",
                "visible": true,
                "display_width": 15,
                "mutable": true,
                "value_options_mutable": false,
                "display_options_mutable": false,
                "control_options_mutable": false
            }
        }
    },
    "visible": true,
    "display_width": 15,
    "display_columns": 3,
    "mutable": true,
    "value_options_mutable": false,
    "display_options_mutable": false,
    "control_options_mutable": false
}
    ''',
        full_recovery=False,
    )


def test_setting_json_full_options_and_type():
    '''JSON for options with and without options being set'''
    setting_dict = SettingDict(
        settings={
            'select': Setting.new(
                'select::string',
                value='01',
                select_map={'01': 'Value'},
                custom_value=True,
            )
        },
        # TODO: integer and select had "options_stored" set to True
        storage=RamStorage.get(name='setting_dict', ram_area='test'),
    )
    export_options = SettingDict.ExportOptions(
        type=True,
        add_new_keys=True,
        exception_on_new_key=False,
        control_options=True,
        value_options=True,
        display_options=True,
        export_defaults=True,
    )
    verify_json(
        setting_dict,
        export_options=export_options,
        expected_json='''
{
    "_version": 2,
    "_settings": {
        "select": {
            "type": "select::string",
            "value": "01",
            "visible": true,
            "display_width": 60,
            "mutable": true,
            "value_options_mutable": false,
            "display_options_mutable": false,
            "control_options_mutable": false,
            "mutable_items": true,
            "mutable_list": true,
            "custom_value": true,
            "select_map": {"01": "Value"},
            "base_setting": {
                "type": "string",
                "value": "Value",
                "visible": true,
                "display_width": 15,
                "mutable": true,
                "value_options_mutable": false,
                "display_options_mutable": false,
                "control_options_mutable": false
            }
        }
    },
    "visible": true,
    "display_width": 15,
    "display_columns": 1,
    "mutable": true,
    "value_options_mutable": false,
    "display_options_mutable": false,
    "control_options_mutable": false
}
    ''',
        full_recovery=True,
    )


def test_setting_json_dict_of_dict_simple():
    '''JSON for options with and without options being set'''
    setting_dict = SettingDict(
        settings={
            'dict_one': SettingDict(
                settings={
                    'string_one': (str, 'one'),
                    'integer_one': (int, '01'),
                }
            ),
            'dict_two': SettingDict(
                settings={
                    'string_two': (str, 'two'),
                    'integer_two': (int, 2),
                }
            ),
        }
    )
    verify_json(
        setting_dict,
        export_options=SettingDict.ExportOptions(),
        expected_json='''
{
    "_version": 2,
    "dict_one": {
        "string_one": "one",
        "integer_one": "01"
    },
    "dict_two": {
        "string_two": "two",
        "integer_two": 2
    }
}
    ''',
        full_recovery=False,
    )


def test_setting_json_dict_of_dict_some_options():
    '''JSON for options with and without options being set'''
    setting_dict = SettingDict(
        settings={
            'dict_one': SettingDict(
                settings={
                    'string_one': (str, 'one'),
                    'integer_one': (int, '01'),
                },
                display_width=101,
            ),
            'dict_two': SettingDict(
                settings={
                    'string_two': (str, 'two'),
                    'integer_two': (int, 2),
                },
                display_width=102,
            ),
        },
        display_columns=3,
    )
    export_options = SettingDict.ExportOptions(
        control_options=True,
        value_options=True,
        display_options=True,
        export_defaults=False,
    )
    verify_json(
        setting_dict,
        export_options=export_options,
        expected_json='''
{
    "_version": 2,
    "_settings": {
        "dict_one": {
            "_settings": {
                "string_one": "one",
                "integer_one": "01"
            },
            "display_width": 101
        },
        "dict_two": {
            "_settings": {
                "string_two": "two",
                "integer_two": 2
            },
            "display_width": 102
        }
    },
    "display_columns": 3
}
    ''',
        full_recovery=False,
    )


def test_setting_json_dict_of_dict_type_recovery():
    '''JSON for options with and without options being set'''
    setting_dict = SettingDict(
        settings={
            'dict_one': SettingDict(
                settings={
                    'string_one': (str, 'one'),
                    'integer_one': (int, '01'),
                }
            ),
            'dict_two': SettingDict(
                settings={
                    'string_two': (str, 'two'),
                    'integer_two': (int, 2),
                }
            ),
        }
    )
    export_options = SettingDict.ExportOptions(
        type=True, add_new_keys=True, exception_on_new_key=False
    )
    verify_json(
        setting_dict,
        export_options=export_options,
        expected_json='''
{
    "_version": 2,
    "dict_one": {
        "type": "dictionary",
        "_settings": {
            "string_one": {
                "type": "string",
                "value": "one"
            },
            "integer_one": {
                "type": "integer",
                "value": "01"
            }
        }
    },
    "dict_two": {
        "type": "dictionary",
        "_settings": {
            "string_two": {
                "type": "string",
                "value": "two"
            },
            "integer_two": {
                "type": "integer",
                "value": 2
            }
        }
    }
}
    ''',
        full_recovery=True,
    )
