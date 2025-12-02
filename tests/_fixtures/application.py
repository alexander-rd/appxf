''' provide fixtures with test application

Using some of the fixtures includes coverage of considerable functionality
which is required to reach initialized applications.
'''
import os
import shutil
import pytest
import toml
from kiss_cf.storage import Storage
from tests._fixtures import appxf_objects
from tests._fixtures.application_mock import ApplicationMock

# get current kiss_cf version
toml_data = toml.load(open('pyproject.toml'))
version = toml_data['project']['version']
print(f'Current kiss_cf version: {version}')

def perform_registration(app: ApplicationMock, app_admin: ApplicationMock):
    ''' Preform registration

    Note: Both application mocks must be unlocked!
    '''
    request_bytes = app.perform_registration_get_request()
    response_bytes = app_admin.perform_registration(request_bytes=request_bytes)
    app.perform_registration_set_response(response_bytes=response_bytes)

def get_fresh_application(
        request,
        user: str = 'user'
        ) -> ApplicationMock:
    # ensure initialized test directory:
    test_root_path = appxf_objects.get_initialized_test_path(request, cleanup=False)
    # just create the application mock which generates requried folders:
    return ApplicationMock(test_root_path, user)

def get_application_login_initialized(
        request,
        user: str = 'user'
        ) -> ApplicationMock:
    # initialize test directory:
    test_root_path = appxf_objects.get_initialized_test_path(request, cleanup=False)
    # ensure base context is available
    app_context_path = _init_app_context_login_initialized(user=user)
    # copy from base context:
    _init_path_from_origin(target_path=test_root_path,
                           origin_path=app_context_path)
    # open application mock to return
    Storage.switch_context(user)
    return ApplicationMock(test_root_path, user)

def get_application_registration_admin_initialized(
        request,
        user: str = 'user'
        ) -> ApplicationMock:
    # initialize test directory:
    test_root_path = appxf_objects.get_initialized_test_path(request, cleanup=False)
    # ensure base context is available
    app_context_path = _init_app_context_registration_admin_initialized(user=user)
    # copy from base context:
    _init_path_from_origin(target_path=test_root_path,
                           origin_path=app_context_path)
    # open application mock to return
    app = ApplicationMock(test_root_path, user)
    return app

def get_unlocked_application(
        request,
        user: str = 'user'
        ) -> ApplicationMock:
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
    path = os.path.join(appxf_objects.testing_base_dir,
                        f'app_login_initialized_{user}_{version}')
    # do not repeat if already present:
    if os.path.exists(path):
        return path
    # otherwise, create:
    # We need to get the app to set the password
    app_user = ApplicationMock(path, user)
    app_user.perform_login_init()
    return path

def _init_app_context_registration_admin_initialized(user: str = 'user'):
    path = os.path.join(appxf_objects.testing_base_dir,
                        f'app_registration_initialized_{user}_{version}')
    if user != 'admin':
        raise ValueError('Only admin user can be initialized as registration admin')
    # do not repeat if already present:
    if os.path.exists(path):
        return path
    # otherwise, create:
    # We need to get the app to set the password
    app_user = ApplicationMock(path, user)
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
    ''' cleanup current kiss_cf directories

    Function is expected to be executed before any test case. Modelled as test
    case to re-use fixtures.
    '''
    base_dir = appxf_objects.testing_base_dir
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
