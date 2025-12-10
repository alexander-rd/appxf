'''Test case description - test case description could come from here'''

from appxf_matema.case_runner import ManualCaseRunner
from kiss_cf.setting import SettingBool, SettingString, SettingEmail, SettingDict
from kiss_cf.gui.setting_dict import SettingDictWindow
from appxf import logging

#logging.activate_logging()
#logging.console_handler.setFormatter(logging.file_formatter)

tester = ManualCaseRunner('''
Resizing: should only affect the right entry part.
Validation: Entry types are shown. Latest after loosing focus on entry, wrong values should turn the entry red.
Columns: Placing options on top of this widget will test alignement of entry fields. Here, all properties are independent and entr fields start directly after the label.
''')  # noqa: E501

#  - Label length: the dict uses very short and very long names on purpose:
setting_dict = SettingDict({
    'String': SettingString(),
    'Email of the master of disaster': SettingEmail(),
    'Boolean Value': SettingBool(),
    })

tester.run(
    SettingDictWindow,
    'Edit Window Title',
    setting_dict)

#for key, setting in setting_dict.items():
#    print(f'{key}: {setting}')
