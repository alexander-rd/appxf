# Copyright 2023-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
"""
Resizing: should only affect the right entry part.
Validation: Entry types are shown. Latest after loosing focus on entry,
wrong values should turn the entry red.
Columns: Placing options on top of this widget will test alignement of entry
fields. Here, all properties are independent and entry fields start directly
after the label.
"""
#! TODO: update testing text

from appxf.gui import setting_dict
from appxf.setting import SettingBool, SettingEmail, SettingString
from appxf_matema.case_runner import ManualCaseRunner

#  - Label length: the dict uses very short and very long names on purpose:
prop_dict = {
    "String": SettingString(),
    "Email of the master of disaster": SettingEmail(),
    "Boolean Value": SettingBool(),
    "Already having content": SettingString("some content"),
}

ManualCaseRunner().run(setting_dict.SettingDictColumnFrame, prop_dict, columns=2)
