''' Test serialization of SettingDict's

Tests to ensure that the implementation adheres to the following concept goals:
 * JSON export shall be concise if storage is only about values
 * JSON expost shall be flexible to include all sorts and options for a setting
   in the following abstraction steps:
    * setting to include options
    * extended settings including base settings (with options)
    * setting being able to restore it's setting type
'''
from kiss_cf.setting import AppxfSetting, SettingDict
from kiss_cf.storage import RamStorage, JsonSerializer

def test_json_values_only():
    setting = SettingDict(
        data={
            'string': AppxfSetting.new('string', value='test'),
            'integer': AppxfSetting.new('int', value=42),
            'select': AppxfSetting.new('select::string', value='01', options={'01': 'Value'})
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
