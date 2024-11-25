from helper import ManualTestHelper
from kiss_cf.setting import AppxfBool, AppxfString, AppxfEmail
from kiss_cf.gui import setting_gui

tester = ManualTestHelper('''
Resizing: should only affect the right entry part.
Validation: Entry types are shown. Latest after loosing focus on entry, wrong values should turn the entry red.
Columns: Placing options on top of this widget will test alignement of entry fields. Here, all properties are independent and entry fields start directly after the label.
''')  # noqa: E501

#! TODO: update testing text

#  - Label length: the dict uses very short and very long names on purpose:
prop_dict = {
    'String': AppxfString(),
    'Email of the master of disaster:': AppxfEmail(),
    'Boolean Value': AppxfBool(),
    'Already having content': AppxfString('some content')
}

tester.run_frame(setting_gui.SettingDictColumnFrame,
                 prop_dict, columns=2)
