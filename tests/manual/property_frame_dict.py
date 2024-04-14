from helper import ManualTestHelper
from kiss_cf.property import KissBool, KissString, KissEmail
from kiss_cf.gui import property_gui

tester = ManualTestHelper('''
Resizing: should only affect the right entry part.
Validation: Entry types are shown. Latest after loosing focus on entry, wrong values should turn the entry red.
Columns: Placing options on top of this widget will test alignement of entry fields. Here, all properties are independent and entr fields start directly after the label.
''')  # noqa: E501

#  - Label length: the dict uses very short and very long names on purpose:
prop_dict = {
    'String': KissString(),
    'Email of the master of disaster:': KissEmail(),
    'Boolean Value': KissBool(),
}

tester.run_frame(property_gui.PropertyDictWidget,
                 prop_dict)
