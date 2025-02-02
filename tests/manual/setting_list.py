import tkinter

from appxf import logging
from helper import ManualTestHelper
from kiss_cf.setting import Setting
from kiss_cf.gui import FrameWindow, SettingDictColumnFrame

# Use Case: Create a bunch of settings let the user edit and handle results
# upon button press.

setting_dict = {
    'String': Setting.new(str),
    'Email': Setting.new('email'),
    'StringSelect': Setting.new(
        'select::string',
        options={'01 One': 'Text One', '02 Two': 'Text Two'},
        ),
    'BooleanTrue': Setting.new(bool, value=True),
    'BooleanFalse': Setting.new(bool, value=False),
}

# This test case put's everything into it's own frame. The tester will need to
# monitor console output upon hitting "OK" button.
class FrameForTesting(FrameWindow):
    def __init__(self, parent: tkinter.BaseWidget, setting):
        super().__init__(parent=parent,
                         title='Testing Setting Lists')
        self.bind('<<OK>>', lambda event: self._handle_ok())

        self.setting = setting
        self.place_frame(SettingDictColumnFrame(self, setting, columns=2))

    def _handle_ok(self):
        print('Current Values:')
        for key, setting in self.setting.items():
            print(f'{key}: {setting.value}')

# TODO: This does not yet work, frame is ineffective and changed values do not
# apply to OK button readout. Also the entries are not marked red, yet.

gui_logger = logging.getLogger('kiss_cf.gui')
gui_logger.setLevel(logging.logging.WARNING)

tester = ManualTestHelper('''
Test case is less about
''')  # noqa: E501

tester._run_toplevel(FrameForTesting, setting_dict)
