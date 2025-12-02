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

@pytest.fixture
def app_fresh(request):
    Storage.reset()
    app = get_fresh_application(request, 'user')
    return {
        'path': app.root_path,
        'users': ['user'],
        'app_user': app}

@pytest.fixture
def app_initialized_user(request):
    Storage.reset()
    app = get_initialized_application(request, 'user')
    return {
        'path': app.root_path,
        'users': ['user'],
        'app_user': app}

# TODO: below and further: remove dependencies on fixtures. Problem is that ALL
# fixtures in whole dependency tree must be included in a test case using them.

@pytest.fixture
def app_unlocked_user(app_initialized_user):
    ''' This fixture uses same data as intialized_user '''
    app: ApplicationMock = app_initialized_user['app_user']
    app.perform_login_unlock()
    return app_initialized_user

@pytest.fixture
def app_unlocked_user_admin_pair(request, app_unlocked_user):
    # app_unlocked_user is already initialized and unlocked, we just need to
    # add the admin instance:
    Storage.switch_context('admin')
    app_admin = get_initialized_application(request, 'admin')
    app_admin.perform_login_unlock()
    app_admin.perform_registration_admin_init()
    # remove storage context to ensure tests are aware of context switching:
    Storage.switch_context('')
    # extend environment data:
    app_unlocked_user['users'].append('admin')
    app_unlocked_user['app_admin'] = app_admin
    return app_unlocked_user

@pytest.fixture
def app_registered_unlocked_user_admin_pair(app_unlocked_user_admin_pair):
    # Fixture is based on already unlocked USER/ADMIN and steps are consistent
    # to test case test_app_02_registry_basic_cycle.
    #
    # Admin is already initialized (as admin). Both are already logged in.
    # Missing is the user registration:
    data = app_unlocked_user_admin_pair
    # registration procedure:
    app_admin: ApplicationMock = data['app_admin']
    app_user: ApplicationMock = data['app_user']
    request_bytes = app_user.perform_registration_get_request()
    response_bytes = app_admin.perform_registration(request_bytes=request_bytes)
    app_user.perform_registration_set_response(response_bytes=response_bytes)
    # TODO: test case missing that reopens USER/ADMIN application after
    # registration
    return data

def get_fresh_application(
        request,
        user: str = 'user'
        ) -> ApplicationMock:
    # initialize test directory:
    test_root_path = appxf_objects.get_initialized_test_path(request)
    # ensure base context is available
    original_context = _init_app_context_fresh()
    # copy from base context:
    _init_path_from_origin(target_path=test_root_path,
                           origin_path=original_context['path'])
    # open application mock to return
    Storage.switch_context(user)
    return ApplicationMock(test_root_path, user)

def get_initialized_application(
        request,
        user: str = 'user'
        ) -> ApplicationMock:
    # initialize test directory:
    test_root_path = appxf_objects.get_initialized_test_path(request)
    # ensure base context is available
    original_context = _init_app_context_initialized_user(user=user)
    # copy from base context:
    _init_path_from_origin(target_path=test_root_path,
                           origin_path=original_context['path'])
    # open application mock to return
    Storage.switch_context(user)
    return ApplicationMock(test_root_path, user)

def get_admin_initialized_application(
        request,
        user: str = 'user'
        ) -> ApplicationMock:
    # initialize test directory:
    test_root_path = appxf_objects.get_initialized_test_path(request)
    # ensure base context is available
    original_context = _init_app_context_initialized_user(user=user)
    # copy from base context:
    _init_path_from_origin(target_path=test_root_path,
                           origin_path=original_context['path'])
    # open application mock to return
    Storage.switch_context(user)
    return ApplicationMock(test_root_path, user)

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
def _init_app_context_fresh():
    path_origin = os.path.join(appxf_objects.testing_base_dir,
                               f'app_fresh_{version}')
    return_dict = {'path': path_origin, 'users': ['user']}
    # do not repeat if already present:
    if os.path.exists(path_origin):
        return return_dict
    # otherwise, create:
    _init_path_from_origin(path_origin, keep = True)
    # A fresh user has no data on the path but the user's application path is
    # generated on adding application:
    Storage.switch_context('user')
    app_user = ApplicationMock(root_path=path_origin, user='user')
    return return_dict

def _init_app_context_initialized_user(user: str = 'user'):
    path_origin = os.path.join(appxf_objects.testing_base_dir,
                               f'app_initialized_{user}_{version}')
    # we rely on fresh user:
    data_derive = _init_app_context_fresh()
    return_dict = {'path': path_origin, 'users': data_derive['users']}
    # do not repeat if already present:
    if os.path.exists(path_origin):
        return return_dict
    # otherwise, create:
    _init_path_from_origin(path_origin, origin_path=data_derive['path'], keep = True)
    # We need to get the app to set the password
    Storage.switch_context(user)
    app_user = ApplicationMock(path_origin, user)
    app_user.perform_login_init()
    return return_dict

def _init_path_from_origin(target_path, origin_path: str = '', keep: bool = False):
    ''' Copy a context to a new test environment

    Arguments:
        target_path -- new path to created
    Keyword Arguments:
        origin_path -- path to copy content from (no copy applied if string
                       is empty)
        keep -- set to true if target_path shall be retained if already existing
    Return: nothing
    '''
    # clear target path
    if os.path.exists(target_path):
        if keep:
            # folder is present and shall be retained
            return
        shutil.rmtree(target_path)
        print(f'Deleted path {target_path}')
    # re-create path
    if origin_path:
        # copy from origin
        shutil.copytree(origin_path, target_path)
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
