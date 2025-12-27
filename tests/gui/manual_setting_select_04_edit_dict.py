'''
TBD
'''
from appxf_matema.case_runner import ManualCaseRunner
from kiss_cf.gui.setting_dict import SettingDictSingleFrame
from kiss_cf.gui.setting_select import SettingSelectFrame
from kiss_cf.setting import Setting, SettingDict, SettingSelect

# Scope: SettingSelect edit options functionality
base_setting = Setting.new('dict',
    {'string': (str, 'base setting'),
     'int': (int, 42)
    })
# Default esport options are already such that new or missing keys would cause
# an exception.

settingOne = SettingSelect(
    base_setting=base_setting,
    select_map={
        'Dictionary A': {
            'string': (str, 'A'),
            'int': (int, 1)
        },
        'Dictionary B': {
            'string': (str, 'B'),
            'int': (int, 2)
        }}, name='SelectDict')

ManualCaseRunner().run(SettingSelectFrame, settingOne)
