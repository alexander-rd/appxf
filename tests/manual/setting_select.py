from helper import ManualTestHelper
from kiss_cf.setting import AppxfBool, AppxfString, AppxfEmail
# from kiss_cf.setting import AppxfStringSelect
from kiss_cf.gui.setting_gui import SettingFrame

# Scope: SettingSelect functionality by single SettingFrame

tester = ManualTestHelper('''
To Be Written
''')  # noqa: E501
#! TODO: update testing text

# setting = AppxfStringSelect()
setting = AppxfString(name = 'TestString')

tester.run_frame(SettingFrame,
                 'Titel',
                 setting)
