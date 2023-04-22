from manual_helper import ManualTestHelper
from kiss_cf.property import KissBool
from kiss_cf import property_gui

tester = ManualTestHelper('''
Resizing: should only affect the right entry part.
Validation: This entry is for a boolean. Latest after loosing focus on entry, wrong values should turn the entry red.
''')  # noqa: E501

prop = KissBool()

tester.run_frame(property_gui.PropertyWidget,
                 prop, 'Property')
