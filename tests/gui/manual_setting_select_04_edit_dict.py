# Copyright 2025-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
'''
__Scope__: Proper interoperabiltity of SettingSelect with SettingDict.

__Preconditions__: The initial value is filled with a "string" "base string"
and an "int" 42 which are none of the select map values. The select map values
are "A"/1 and "B"/2.

__Selecting__: Switch selections and check the tooltip.

__Edit Window__: Open edit and check appearance of the detailed view.

__Changes__: Perform the following three changes and, each time, check the
result in the initial windows tooltips.
    (1) Add a new entry
    (2) Change an existing entry
    (3) Remove an entry

__Invalid__: Try to set an invalid value (letters for int) and use OK as well
as Cancel.
'''
from appxf_matema.case_runner import ManualCaseRunner
from appxf.gui.setting_select import SettingSelectFrame
from appxf.setting import Setting, SettingSelect

# Scope: SettingSelect edit options functionality
base_setting = Setting.new('dict',
    {'string': (str, 'base setting'),
     'int': (int, 42)
    })
# Default export options are already such that new or missing keys would cause
# an exception.

settingOne = SettingSelect(
    base_setting=base_setting,
    select_map={
        'Dictionary A': {
            'string': 'A',
            'int': 1
        },
        'Dictionary B': {
            'string': 'B',
            'int': 2
        }}, name='SelectDict')

ManualCaseRunner().run(SettingSelectFrame, settingOne)
