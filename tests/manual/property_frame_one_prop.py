from tests.manual.helper import ManualTestHelper
from kiss_cf.setting import AppxfBool
from kiss_cf.gui import property_gui

tester = ManualTestHelper('''
Resizing: should only affect the right entry part.
Validation: This entry is for a boolean. Latest after loosing focus on entry, wrong values should turn the entry red.
''')  # noqa: E501

prop = AppxfBool()

tester.run_frame(property_gui.PropertyWidget,
                 'Property', prop)
