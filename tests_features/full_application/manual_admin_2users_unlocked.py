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

tester = ManualCaseRunner(__doc__)

sandbox_path = test_sandbox.init_test_sandbox_for_caller_module()

Storage.reset()
Storage.switch_context('invalid')

app_admin = AppHarness(sandbox_path, 'admin')
app_admin.perform_login_init()
app_admin.perform_registration_admin_init()
launch_admin = lambda: KissApplication().mainloop()

app_userA = AppHarness(sandbox_path, 'userA')
app_userA.perform_login_init()
app_userA.perform_registration(app_admin)
launch_userA = lambda: KissApplication().mainloop()

app_userB = AppHarness(sandbox_path, 'userB')
app_userB.perform_login_init()
app_userB.perform_registration(app_admin)
launch_userB = lambda: KissApplication().mainloop()

tester.run_custom_commands({
    'Run Admin': launch_admin,
    'Run User A': launch_userA,
    'Run User B': launch_userB
    })



# tester.run_custom_commands({})

# running currently requires a window or frame to run.. ..work in progress.
# tester.run()
