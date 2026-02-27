# Copyright 2023-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
"""
__Resizing:__ should only affect the right entry part.

__Validation:__ This entry is for a boolean. Latest after loosing focus on
entry, wrong values *must* turn the entry red.
"""

from appxf.gui import SettingFrameDefault
from appxf.setting import SettingBool
from appxf_matema.case_runner import ManualCaseRunner

prop = SettingBool(name="bool")

ManualCaseRunner().run(SettingFrameDefault, prop)
