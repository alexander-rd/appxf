# Copyright 2025-2026 the contributors of APPXF (github.com/alexander-rd/appxf)
# SPDX-License-Identifier: Apache-2.0
''' Registration Cycle

__Preconditions:__ A ***user application*** has user data and password set and
opens unlocked. The user is not yet registered. An ***admin application*** is
fully initialized with admin privileges and also upens unlocked with access to
registry.

__Scope:__ The test shall cylce through the normal registration process with
following steps.

__Step 1:__ The user generates the registration request. The button should be
directly available after launch of the application. Select any location from
the file picker.

__Step 2:__ The admin sets some values into the configuration "SHARED" and
"SHARED_REGISTRATION" which are checked later on user side.

__Step 3:__ The admin loads the registration data and reviews. You should be
able to see valid user data.

__Step 4:__ The admin adds the user to the registry. There will be a pop-up
displaying the user ID.

__Step 5:__ The admin generates the response data. Again, the file can be
placed wherever you like.

__Step 6:__ The user loads the registration response and should immediately end
up in the application window. He should now have all configuration items filled
exactly like the admin has them.
KNOWN LIMITATION: "SHARED" is not yet working. Data synchronization after
registration is not active.

__Step 7:__ The user remains registered even if closing and reopening the
application.

__Step 8:__ Even if the admin closes the application and reloads the request
and adds the user again, it will be added with the same user ID.
'''
from appxf_matema.case_runner import ManualCaseRunner
from tests._fixtures import test_sandbox
from tests._fixtures.app_harness import AppHarness
from tests._fixtures.app_harness_gui import AppHarnessGui

def setup_once():
    sandbox_path = test_sandbox.init_test_sandbox_for_caller_module(cleanup=True)
    # setup user
    app_user = AppHarness(
        sandbox_path, 'user',
        registry_enabled=True)
    app_user.perform_login_init()
    # setup admin
    app_admin = AppHarness(
        sandbox_path, 'admin',
        registry_enabled=True)
    app_admin.perform_login_init()
    app_admin.perform_registration_admin_init()

def process_app_user():
    ''' Launch User '''
    sandbox_path = test_sandbox.init_test_sandbox_for_caller_module(cleanup=False)
    app_user = AppHarness(sandbox_path, 'user',
                          registry_enabled=True)
    app_user.perform_login_unlock()

    AppHarnessGui(app_user).start()

def process_app_admin():
    ''' Launch Admin '''
    sandbox_path = test_sandbox.init_test_sandbox_for_caller_module(cleanup=False)
    app_admin = AppHarness(sandbox_path, 'admin',
                          registry_enabled=True)
    app_admin.perform_login_unlock()
    AppHarnessGui(app_admin).start()

ManualCaseRunner(logging_context='appxf').run()
