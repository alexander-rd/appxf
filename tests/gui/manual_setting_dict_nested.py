'''
__Resizing:__ should only affect the right entry part.

__Validation:__ This entry is for a boolean. Latest after loosing focus on entry, wrong values *must* turn the entry red.
'''

from kiss_cf.setting import Setting
from kiss_cf.gui import SettingFrameDefault
from appxf_matema.case_runner import ManualCaseRunner

inner_A = Setting.new(
    'dict', {
        'string A': ('str', 'test A'),
        'int A': ('int', 1)
    },
    name='Inner A')

ManualCaseRunner().run(
    SettingFrameDefault, inner_A)
