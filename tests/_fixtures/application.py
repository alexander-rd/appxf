# Copyright 2024-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
''' provide fixtures with test application

Using some of the fixtures includes coverage of considerable functionality
which is required to reach initialized applications.
'''
import os
import shutil
from appxf.storage import Storage
from tests._fixtures.app_harness import AppHarness
import tests._fixtures.test_sandbox
from tests._fixtures.test_sandbox import project_version

# TODO: Verify if the complexity in this file is actually required.
# Implementation essentially allows to get an application sandbox/context from
# copying an already initialized one. This may make sense if this
# initialization takes very long, but a fresh application or login application
# may not be such cases. Maybe even a registered user with remote files is not
# woth this complexity. The evaluation should anylyze the time savings of the
# most complex cases (like: registeres user with set up remote files).

def get_fresh_application(
        request,
        user: str = 'user'
        ) -> AppHarness:
    # ensure initialized test directory:
    test_root_path = tests._fixtures.test_sandbox.init_test_sandbox_from_fixture(request, cleanup=False)
    # just create the application mock which generates requried folders:
    return AppHarness(test_root_path, user, registry_enabled=True)

def get_application_login_initialized(
        request,
        user: str = 'user'
        ) -> AppHarness:
    # initialize test directory:
    test_root_path = tests._fixtures.test_sandbox.init_test_sandbox_from_fixture(request, cleanup=False)
    # ensure base context is available
    app_context_path = _init_app_context_login_initialized(user=user)
    # copy from base context:
    _init_path_from_origin(target_path=test_root_path,
                           origin_path=app_context_path)
    # open application mock to return
    Storage.switch_context(user)
    return AppHarness(test_root_path, user, registry_enabled=True)

def get_application_registration_admin_initialized(
        request,
        user: str = 'user'
        ) -> AppHarness:
    # initialize test directory:
    test_root_path = tests._fixtures.test_sandbox.init_test_sandbox_from_fixture(request, cleanup=False)
    # ensure base context is available
    app_context_path = _init_app_context_registration_admin_initialized(user=user)
    # copy from base context:
    _init_path_from_origin(target_path=test_root_path,
                           origin_path=app_context_path)
    # open application mock to return
    app = AppHarness(test_root_path, user, registry_enabled=True)
    return app

def get_unlocked_application(
        request,
        user: str = 'user'
        ) -> AppHarness:
    app = get_application_login_initialized(request, user=user)
    app.perform_login_unlock()
    return app

### Application Context Initialization

# The following structure applies to all init functions:
#
# Parameters:
#   path_testing -- the root folder for all testing files
#
# Return: A structure with:
#   'path' -- root of the initialized application context
#   'users' -- list of initialized users It is intentional that the
# ApplicationMock objects are not forwarded

def _init_app_context_login_initialized(user: str = 'user'):
    path = os.path.join(tests._fixtures.test_sandbox.test_sandbox_root,
                        f'app_login_initialized_{user}_{project_version}')
    # do not repeat if already present:
    if os.path.exists(path):
        return path
    # otherwise, create:
    # We need to get the app to set the password
    app_user = AppHarness(path, user, registry_enabled=True)
    app_user.perform_login_init()
    return path

def _init_app_context_registration_admin_initialized(user: str = 'user'):
    path = os.path.join(tests._fixtures.test_sandbox.test_sandbox_root,
                        f'app_registration_initialized_{user}_{project_version}')
    if user != 'admin':
        raise ValueError('Only admin user can be initialized as registration admin')
    # do not repeat if already present:
    if os.path.exists(path):
        return path
    # otherwise, create:
    # We need to get the app to set the password
    app_user = AppHarness(path, user, registry_enabled=True)
    app_user.perform_login_init()
    app_user.perform_registration_admin_init()
    return path

def _init_path_from_origin(target_path, origin_path: str = ''):
    ''' Copy a context to a new test environment

    Arguments:
        target_path -- new path to created
    Keyword Arguments:
        origin_path -- path to copy content from (no copy applied if string
                       is empty)
        keep -- set to true if target_path shall be retained if already existing
    Return: nothing
    '''
    # target path will not be cleaned up. Each test case shall cleanup its
    # directory on its own.
    if origin_path:
        # copy from origin
        shutil.copytree(origin_path, target_path, dirs_exist_ok=True)
        print(f'Initialized {target_path} from {origin_path}')
    else:
        # ensure path existing
        os.makedirs(target_path, exist_ok=True)
        print(f'Created path {target_path}')

### Cleanup support
def test_cleanup(request):
    ''' cleanup current APPXF directories

    Function is expected to be executed before any test case. Modelled as test
    case to re-use fixtures.
    '''
    base_dir = tests._fixtures.test_sandbox.test_sandbox_root
    if not os.path.isdir(base_dir):
        print(f'No cleanup required, base dir missing: {base_dir}')
        return

    for entry in os.listdir(base_dir):
        if not entry.startswith('app_'):
            continue
        path = os.path.join(base_dir, entry)
        if os.path.isdir(path):
            shutil.rmtree(path)
            print(f'Removed {path}')
        else:
            print(f'Skipped non-directory {path}')

# TODO: I think the cleanup above does not work as intenden. (1) The context
# list would not include "app_user". (2) it executes in some folder with
# "test_cleanup" which does not contain the current base application folders.
