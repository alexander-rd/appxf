from appxf_matema.case_runner import ManualCaseRunner
from kiss_cf.setting import SettingBool, SettingString, SettingEmail
from kiss_cf.gui import setting_dict

tester = ManualCaseRunner('''
Resizing: should only affect the right entry part.
Validation: Entry types are shown. Latest after loosing focus on entry, wrong values should turn the entry red.
Columns: Placing options on top of this widget will test alignement of entry fields. Here, all properties are independent and entry fields start directly after the label.
''')  # noqa: E501

#! TODO: update testing text

#  - Label length: the dict uses very short and very long names on purpose:
prop_dict = {
    'String': SettingString(),
    'Email of the master of disaster': SettingEmail(),
    'Boolean Value': SettingBool(),
    'Already having content': SettingString('some content')
}

tester.run(
    setting_dict.SettingDictColumnFrame,
    prop_dict, columns=2)
