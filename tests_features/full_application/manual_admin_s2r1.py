''' Admin Application

__Precondition:__ Admin application, with initialized security and regsitry.

__Scope:__ No testing. This case is for development.

__Reset:__ The sandbox is NOT reset during executions to support development
testing. Use the reset button to manualle reset the sandbox. **Do not reset
while the application is launched!**
'''
from appxf_matema.case_runner import ManualCaseRunner
from tests._fixtures import test_sandbox
from tests._fixtures.app_harness import AppHarness
from tests._fixtures.app_harness_gui import AppHarnessGui

def setup_once():
    sandbox_path = test_sandbox.init_test_sandbox_for_caller_module(cleanup=False)
    app_admin = AppHarness(sandbox_path, 'user',
                          registry_enabled=True)
    if not app_admin.security.is_user_initialized():
        app_admin.perform_login_init()
    if not app_admin.registry.is_initialized():
        app_admin.perform_registration_admin_init()

def process_app_admin():
    ''' Launch Admin '''
    sandbox_path = test_sandbox.init_test_sandbox_for_caller_module(cleanup=False)
    app_admin = AppHarness(sandbox_path, 'user',
                          registry_enabled=True)
    app_admin.perform_login_unlock()
    AppHarnessGui(app_admin).start()

def process_reset_sandbox():
    ''' Reset Sandbox '''
    sandbox_path = test_sandbox.init_test_sandbox_for_caller_module(cleanup=True)
    app_admin = AppHarness(sandbox_path, 'user',
                          registry_enabled=True)
    app_admin.perform_login_init()
    app_admin.perform_registration_admin_init()

ManualCaseRunner().run_by_file_parsing()
