''' Test serialization of SettingDict's

Tests to ensure that the implementation adheres to the following concept goals:
 * JSON export shall be concise if storage is only about values
 * JSON expost shall be flexible to include all sorts and options for a setting
   in the following abstraction steps:
    * setting to include options
    * extended settings including base settings (with options)
    * setting being able to restore it's setting type
'''
from kiss_cf.setting import Setting, SettingDict
from kiss_cf.storage import RamStorage, JsonSerializer

def test_json_values_only():
    '''JSON for options with only values included
    (no options being set or set to stored)'''
    setting = SettingDict(
        data={
            'string': Setting.new('string', value='test'),
            'integer': Setting.new('int', value=42),
            'select': Setting.new('select::string', value='01',
                                  select_map={'01': 'Value'},
                                  custom_value=False,
                                  mutable_items=False, mutable_list=False)
            },
        storage=RamStorage.get(name='setting_dict', ram_area='test'))
    raw_data = setting.get_state()
    serialized_data = JsonSerializer.serialize(raw_data)
    expected_part = '''
{
    "_version": 2,
    "string": "test",
    "integer": 42,
    "select": "01"
}
    '''
    print(f'Produced JSON:\n{serialized_data.decode("utf-8")}')
    assert expected_part[1:-5] == serialized_data.decode('utf-8')

def test_json_value_and_display_options():
    '''JSON for options with and without options being set'''
    setting = SettingDict(
        data={
            'string': Setting.new('string', value='test'),
            'integer': Setting.new('int', value=42),
            'select': Setting.new('select::string', value='01', select_map={'01': 'test_value'},
                                  display_width = 42, custom_value=False,)
            },
        # TODO: integer and select had "options_stored" set to True
        storage=RamStorage.get(name='setting_dict', ram_area='test')
        )
    setting.export_options.value_options = True
    setting.export_options.display_options = True
    raw_data = setting.get_state()
    serialized_data = JsonSerializer.serialize(raw_data)
    expected_part = '''
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
    '''
    print(f'Produced JSON:\n{serialized_data.decode("utf-8")}')
    assert expected_part[1:-5] == serialized_data.decode('utf-8')

def test_json_full_export():
    '''JSON for options with and without options being set'''
    setting = SettingDict(
        data={
            'select': Setting.new('select::string', value='01', select_map={'01': 'Value'},
                                  custom_value=True)
            },
        # TODO: integer and select had "options_stored" set to True
        storage=RamStorage.get(name='setting_dict', ram_area='test')
        )
    setting.export_options.control_options = True
    setting.export_options.value_options = True
    setting.export_options.display_options = True
    setting.export_options.export_defaults = True
    raw_data = setting.get_state()
    serialized_data = JsonSerializer.serialize(raw_data)
    expected_part = '''
{
    "_version": 2,
    "select": {
        "value": "01",
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
            "display_width": 0,
            "mutable": true,
            "value_options_mutable": false,
            "display_options_mutable": false,
            "control_options_mutable": false
        }
    }
}
    '''
    print(f'Produced JSON:\n{serialized_data.decode("utf-8")}')
    assert expected_part[1:-5] == serialized_data.decode('utf-8')

