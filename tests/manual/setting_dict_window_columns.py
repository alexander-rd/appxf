from helper import ManualTestHelper
from kiss_cf.setting import AppxfBool, SettingDict
from kiss_cf.gui import setting_dict

tester = ManualTestHelper('''
Resizing: should affect columns evenly.
Validation: Entry types are shown. Latest after loosing focus on entry, wrong values should turn the entry red.
Columns: Placing options on top of this widget will test alignement of entry fields. Here, all properties are independent and entry fields start directly after the label.
''')  # noqa: E501

prop_dict = SettingDict({option: AppxfBool() for option in [
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

tester._run_toplevel(setting_dict.SettingDictWindow,
                    'Edit Window Title',
                    prop_dict,
                    gui_property)

for key in prop_dict.keys():
    print(f'{key}: {prop_dict[key]}')
