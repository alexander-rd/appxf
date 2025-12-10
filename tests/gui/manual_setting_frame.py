from kiss_cf.setting import SettingBool
from kiss_cf.gui import SettingFrameDefault
from appxf_matema.case_runner import ManualCaseRunner

tester = ManualCaseRunner('''
__Resizing:__ should only affect the right entry part.

__Validation:__ This entry is for a boolean. Latest after loosing focus on entry, wrong values *must* turn the entry red.
''')  # noqa: E501

prop = SettingBool(name='bool')

tester.run(
    SettingFrameDefault, prop)
