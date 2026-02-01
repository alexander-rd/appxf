''' SettingSelect for altering existing content

__Main Scope:__ Use case is "templating" where the SettingSelect comprises a
fixed set of options which the user can alter.

__Behavior:__ Upon "OK" button, the current text must be printed correctly into
the console while it is not stored. Upon Save, there must not be a prompt for
the list name while the current text is stored to the list item.

__GUI:__ General appearance and stretching shall be OK. There must only be a
save button on top, not a delete button.
'''

# The SettingSelectDetailFrame could need those basic test cases:
# 1) Readonly (all false)
# 2) Custom Values from fixed list (+custom_value)
# 3) Template List wich changing options (+mutable_items)
# 4) full edit
# however, some may be included in other frame examples

import tkinter

from appxf_matema.case_runner import ManualCaseRunner
from appxf.setting import Setting
from appxf.gui import GridToplevel, SettingSelectDetailFrame

setting = Setting.new('select::text',
    select_map={'01 One': 'Template text 01 to be adapted.',
                '02 Two': 'Template text 02 to be adapted.',
                '42 Fourty Two': 'Template text 42 to be adapted.',
                },
    name='Templated String',
    base_setting_options={'display_height': 20, 'display_width': 60},
    mutable_list = False,
    mutable_items = True,
    custom_value = True)

class WindowForTesting(GridToplevel):
    def __init__(self, parent: tkinter.BaseWidget):
        super().__init__(parent=parent,
                         title='Testing Templated Text via SettingSelect')
        self.bind('<<OK>>', lambda event: self._handle_ok())
        self.place_frame(SettingSelectDetailFrame(self, setting))

    def _handle_ok(self):
        print(f'Current Text:\n{setting.base_setting.value}')

ManualCaseRunner().run(WindowForTesting)

print(f'Final Text:\n{setting.base_setting.value}')
