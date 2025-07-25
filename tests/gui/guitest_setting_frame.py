from kiss_cf.setting import SettingBool
from kiss_cf.gui import SettingFrameDefault
from kiss_cf.guitest.case_runner import GuitestCaseRunner

tester = GuitestCaseRunner('''
Resizing: should only affect the right entry part.
Validation: This entry is for a boolean. Latest after loosing focus on entry, wrong values should turn the entry red.
''')  # noqa: E501

prop = SettingBool(name='bool')

tester._run_frame(SettingFrameDefault, prop)
