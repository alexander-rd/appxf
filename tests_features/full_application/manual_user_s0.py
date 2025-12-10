''' User Initialization without Registration

__Precondition:__ Fresh user application.

__Scope:__ Procedure of local user initialization.

__Step 1:__ Upon first opening, the user data initialization window should show
with BUT NOT YET the application window. You should be able to close the
window, launch again with same window appearing and entered data being lost.

__Step 2:__ After entering user data and password, the main application should
pop up. From there, you can review the user data.

__Step 3:__ Closing the app and reopening should call for the password.
Entering the right one should again provide access to the application.
'''
from kiss_cf.storage import Storage

from appxf_matema.case_runner import ManualCaseRunner
from tests._fixtures import test_sandbox
from tests._fixtures.app_harness import AppHarness
from tests._fixtures.app_harness_gui import AppHarnessGui

def setup():
    test_sandbox.init_test_sandbox_for_caller_module(cleanup=True)

# Still requried?
# Storage.reset()
# Storage.switch_context('invalid')

def process_app_user():
    ''' Launch User '''
    sandbox_path = test_sandbox.init_test_sandbox_for_caller_module(cleanup=False)
    app_user = AppHarness(sandbox_path, 'user')
    AppHarnessGui(app_user).start()

# New starter:
ManualCaseRunner().run_by_file_parsing()
