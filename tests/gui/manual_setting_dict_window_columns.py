# Copyright 2024-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
'''
Resizing: should affect columns evenly.
Validation: Entry types are shown. Latest after loosing focus on entry, wrong values should turn the entry red.
Columns: Placing options on top of this widget will test alignement of entry fields. Here, all properties are independent and entry fields start directly after the label.
'''
from appxf_matema.case_runner import ManualCaseRunner
from appxf.setting import SettingBool, SettingDict
from appxf.gui import setting_dict

prop_dict = SettingDict({option: SettingBool() for option in [
    'One', 'Two', 'Three', 'Four',
    'Five', 'Six', 'Seven', 'Eight',
    'Nine', 'Ten']
    })
gui_property = {
    'columns': 4,
    #'properties': {
    #    'Three': {
    #        'frame_type': setting_gui.BoolCheckBoxWidget
    #    }
    #}
}


#for key in prop_dict.keys():
#    print(f'{key}: {prop_dict[key]}')

ManualCaseRunner().run(
    setting_dict.SettingDictWindow,
    'Edit Window Title',
    prop_dict,
    gui_property)

for key in prop_dict.keys():
    print(f'{key}: {prop_dict[key]}')
