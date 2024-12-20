from helper import ManualTestHelper
from kiss_cf.setting import AppxfStringSelect
# from kiss_cf.setting import AppxfStringSelect
from kiss_cf.gui.setting_gui import SettingFrame
from kiss_cf.gui import SettingSelectFrame

# Scope: SettingSelect functionality by single SettingFrame

tester = ManualTestHelper('''
Frame shall only show the label and the dropdown. The edit button must not be
presented. The dropdown must be empty at startup (nothing selected) and contain
two options.
Hovering: must show the long selected value.
Resizing: should only affect the right entry part.
''')  # noqa: E501
#! TODO: update testing text

setting = AppxfStringSelect(
    options={'Option 1': 'Lorem ipsum.',
             'Option 2': 'Zwei'},
    name='Dropdown')
# TODO: text to be extended

tester.run_frame(SettingSelectFrame,
                 setting)
