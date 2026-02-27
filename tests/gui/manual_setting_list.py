# Copyright 2025-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
"""
Test case is less about ... TBD
"""

import tkinter

from appxf import logging
from appxf.gui import GridToplevel, SettingDictColumnFrame
from appxf.setting import Setting
from appxf_matema.case_runner import ManualCaseRunner

# Use Case: Create a bunch of settings let the user edit and handle results
# upon button press.

setting_dict = {
    "String": Setting.new(str),
    "Email": Setting.new("email"),
    "StringSelect": Setting.new(
        "select::string",
        select_map={"01 One": "Text One", "02 Two": "Text Two"},
    ),
    "BooleanTrue": Setting.new(bool, value=True),
    "BooleanFalse": Setting.new(bool, value=False),
}


# This test case put's everything into it's own frame. The tester will need to
# monitor console output upon hitting "OK" button.
class FrameForTesting(GridToplevel):
    def __init__(self, parent: tkinter.BaseWidget, setting):
        super().__init__(parent=parent, title="Testing Setting Lists")
        self.bind("<<OK>>", lambda event: self._handle_ok())

        self.setting = setting
        self.place_frame(SettingDictColumnFrame(self, setting, columns=2))

    def _handle_ok(self):
        print("Current Values:")
        for key, setting in self.setting.items():
            print(f"{key}: {setting.value}")


# TODO: This does not yet work, frame is ineffective and changed values do not
# apply to OK button readout. Also the entries are not marked red, yet.

gui_logger = logging.getLogger("appxf.gui")
gui_logger.setLevel(logging.logging.WARNING)

ManualCaseRunner().run(FrameForTesting, setting_dict)
