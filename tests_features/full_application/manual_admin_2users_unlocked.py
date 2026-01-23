''' Full Applications

__Precondition:__ Admin, User A and User B are initialized and logged in. Users
are registered to admin.

__Scope:__ Feel free to play around and inspect configurations.
'''
from appxf_matema.case_runner import ManualCaseRunner
from kiss_cf.gui import KissApplication
from kiss_cf.storage import Storage
from tests._fixtures import test_sandbox
from tests._fixtures import application
from tests._fixtures.app_harness import AppHarness
from tests._fixtures.app_harness_gui import AppHarnessGui

def setup_once():
    sandbox_path = test_sandbox.init_test_sandbox_for_caller_module(cleanup=True)

    app_admin = AppHarness(sandbox_path, 'admin',
                           registry_enabled=True)
    app_admin.perform_login_init()
    app_admin.perform_registration_admin_init()

    app_userA = AppHarness(sandbox_path, 'userA',
                           registry_enabled=True)
    app_userA.perform_login_init()
    app_userA.perform_registration(app_admin)

    app_userB = AppHarness(sandbox_path, 'userB',
                           registry_enabled=True)
    app_userB.perform_login_init()
    app_userB.perform_registration(app_admin)

def launch_app(user: str):
    sandbox_path = test_sandbox.init_test_sandbox_for_caller_module(cleanup=False)
    app_user = AppHarness(sandbox_path, user)
    AppHarnessGui(app_user).start()

def process_app_admin():
    ''' Launch Admin '''
    launch_app('admin')

def process_app_userA():
    ''' Launch User A '''
    launch_app('userA')

def process_app_userB():
    ''' Launch User B '''
    launch_app('userB')

#Storage.reset()
#Storage.switch_context('invalid')

ManualCaseRunner().run()