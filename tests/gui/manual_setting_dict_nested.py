# Copyright 2023-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
'''
__Display:__ Check if the nested dict displays properly with all elements
clearly visible, operational and reasonably separated. There are three nested
dicts. Dict A, dict B and a boolean are on the first level. Within B, there is
a nested Deict C. All Dicts have a string and an integer.

__Resizing:__ should only affect the right entry part.
'''

from appxf.setting import Setting
from appxf.gui import SettingDictSingleFrame
from appxf_matema.case_runner import ManualCaseRunner

inner_A = Setting.new(
    'dict', {
        'string A': ('str', 'test A'),
        'int A': ('int', 1)
    })
inner_B_C = Setting.new(
    'dict', {
        'string C': ('str', 'test C'),
        'int C': ('int', 2),
    })
inner_B = Setting.new(
    'dict', {
        'string B': ('str', 'test B'),
        'int B': ('int', 2),
        'dict C:': inner_B_C,
        'bool B': ('bool', True),
    })
outer = Setting.new('dict', {'dict A': inner_A, 'dict B': inner_B})


ManualCaseRunner().run(
    SettingDictSingleFrame, outer)
