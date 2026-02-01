'''
__Resizing:__ should only affect the right entry part.

__Validation:__ This entry is for a boolean. Latest after loosing focus on entry, wrong values *must* turn the entry red.
'''

from appxf.setting import SettingBool
from appxf.gui import SettingFrameDefault
from appxf_matema.case_runner import ManualCaseRunner

prop = SettingBool(name='bool')

ManualCaseRunner().run(
    SettingFrameDefault, prop)
