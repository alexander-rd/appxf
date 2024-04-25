from helper import ManualTestHelper
from kiss_cf.property import KissBool
from kiss_cf.gui import property_gui

tester = ManualTestHelper('''
Resizing: should only affect the right entry part.
Validation: Entry types are shown. Latest after loosing focus on entry, wrong values should turn the entry red.
Columns: Placing options on top of this widget will test alignement of entry fields. Here, all properties are independent and entr fields start directly after the label.
''')  # noqa: E501

#  - Label length: the dict uses very short and very long names on purpose:

# TODO: review and remove this test. get_selection_dict() is not supported
# anymore since it's replacement is a simple generator:
#   {option: property.KissBool(True) for option in some_list}

prop_dict = KissBool.get_selection_dict([
    'One', 'Two', 'Three', 'Four',
    'Five', 'Six', 'Seven', 'Eight',
    'Nine', 'Ten'],
    init=True)
gui_property = {
    'columns': 4,
    'properties': {
        'Three': {
            'frame_type': property_gui.BoolCheckBoxWidget
        }
    }
}


for key in prop_dict.keys():
    print(f'{key}: {prop_dict[key]}')

tester.run_toplevel(property_gui.EditPropertyDictWindow,
                    prop_dict,
                    'Edit Window Title',
                    gui_property)

for key in prop_dict.keys():
    print(f'{key}: {prop_dict[key]}')
