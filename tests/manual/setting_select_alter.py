''' SettingSelect test case for altering the content

__Main Scope:__ Templating use case where the SettingSelect serves as
template text and the final value is whatever the user changes in the
text.

__Behavior:__ Upon "OK" button, the current text must be printed
correctly.

__GUI:__ General appearance and stretching shall be OK.

__Optional:__ The edit buttons should be functional but this detail is
not in scope of this test.
'''
import tkinter

from helper import ManualTestHelper
from kiss_cf.setting import Setting
from kiss_cf.gui import FrameWindow, SettingSelectFrameDetail

tester = ManualTestHelper(__doc__)

setting = Setting.new('select::string',
    options={'01 One': 'Template text 01 to be adapted.',
             '02 Two': 'Template text 02 to be adapted.',
             '42 Fourty Two': 'Template text 42 to be adapted.',
             },
    name='Templated String',
    base_setting_options={'height': 20, 'width': 60})
setting.options['mutable'] = True

class WindowForTesting(FrameWindow):
    def __init__(self, parent: tkinter.BaseWidget):
        super().__init__(parent=parent,
                         title='Testing Templated Text via SettingSelect')
        self.bind('<<OK>>', lambda event: self._handle_ok())
        self.place_frame(SettingSelectFrameDetail(self, setting))

    def _handle_ok(self):
        print(f'Current Text:\n{setting.base_setting.value}')

tester.run(WindowForTesting)

print(f'Final Text:\n{setting.base_setting.value}')
