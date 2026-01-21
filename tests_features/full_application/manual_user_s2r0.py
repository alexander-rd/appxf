''' User Initialization without Registration

__Precondition:__ User application with initialized user (Local Security) but
pending registration (no request generated, yet)

__Scope:__ No testing. This case is for development.

__Reset:__ The sandbox is NOT reset during executions to support development
testing. Use the reset button to manualle reset the sandbox. **Do not reset
while the application is launched!**
'''

from appxf_matema.case_runner import ManualCaseRunner
from tests._fixtures import test_sandbox
from tests._fixtures.app_harness import AppHarness
from tests._fixtures.app_harness_gui import AppHarnessGui

# Overwrite language selection for testing:
import os
os.environ["LANGUAGE"] = "de"

def setup_once():
    sandbox_path = test_sandbox.init_test_sandbox_for_caller_module(cleanup=False)
    app_user = AppHarness(sandbox_path, 'user',
                          registry_enabled=True)
    if not app_user.security.is_user_initialized():
        app_user.perform_login_init()

def process_reset_sandbox():
    ''' Reset Sandbox '''
    sandbox_path = test_sandbox.init_test_sandbox_for_caller_module(cleanup=True)
    app_user = AppHarness(sandbox_path, 'user',
                          registry_enabled=True)
    app_user.perform_login_init()

def process_app_user():
    ''' Launch User '''
    sandbox_path = test_sandbox.init_test_sandbox_for_caller_module(cleanup=False)
    app_user = AppHarness(sandbox_path, 'user',
                          registry_enabled=True)
    app_user.perform_login_unlock()
    AppHarnessGui(app_user).start()

# New starter:
ManualCaseRunner().run()
