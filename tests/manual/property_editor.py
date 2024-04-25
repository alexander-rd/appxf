from helper import ManualTestHelper
from kiss_cf.property import KissBool, KissString, KissEmail
from kiss_cf.gui import property_gui
from appxf import logging

logging.activate_logging()
logging.console_handler.setFormatter(logging.file_formatter)

tester = ManualTestHelper('''
Resizing: should only affect the right entry part.
Validation: Entry types are shown. Latest after loosing focus on entry, wrong values should turn the entry red.
Columns: Placing options on top of this widget will test alignement of entry fields. Here, all properties are independent and entr fields start directly after the label.
''')  # noqa: E501

#  - Label length: the dict uses very short and very long names on purpose:
prop_dict = {
    'String:': KissString(),
    'Email of the master of disaster:': KissEmail(),
    'Boolean Value:': KissBool(),
}

for key in prop_dict.keys():
    print(f'{key}: {prop_dict[key]}')

tester.run_toplevel(property_gui.EditPropertyDictWindow,
                    'Edit Window Title',
                    prop_dict)

for key in prop_dict.keys():
    print(f'{key}: {prop_dict[key]}')
