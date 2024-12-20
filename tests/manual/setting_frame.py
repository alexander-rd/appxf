from helper import ManualTestHelper
from kiss_cf.setting import AppxfBool
from kiss_cf.gui import SettingFrame

tester = ManualTestHelper('''
Resizing: should only affect the right entry part.
Validation: This entry is for a boolean. Latest after loosing focus on entry, wrong values should turn the entry red.
''')  # noqa: E501

prop = AppxfBool(name='bool')

tester.run_frame(SettingFrame, prop)
