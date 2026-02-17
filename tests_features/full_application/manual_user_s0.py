# Copyright 2025-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
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
from appxf_matema.case_runner import ManualCaseRunner
from tests._fixtures import test_sandbox
from tests._fixtures.app_harness import AppHarness
from tests._fixtures.app_harness_gui import AppHarnessGui

def setup_once():
    test_sandbox.init_test_sandbox_for_caller_module(cleanup=True)

def process_app_user():
    ''' Launch User '''
    sandbox_path = test_sandbox.init_test_sandbox_for_caller_module(cleanup=False)
    app_user = AppHarness(sandbox_path, 'user')
    AppHarnessGui(app_user).start()

ManualCaseRunner().run()
