from helper import ManualTestHelper
from kiss_cf.setting import AppxfBool
from kiss_cf.gui import SettingFrameDefault

tester = ManualTestHelper('''
Resizing: should only affect the right entry part.
Validation: This entry is for a boolean. Latest after loosing focus on entry, wrong values should turn the entry red.
''')  # noqa: E501

prop = AppxfBool(name='bool')

tester._run_frame(SettingFrameDefault, prop)
