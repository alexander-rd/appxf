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
def app_fresh_user(request):
    Storage.reset()
    dir = appxf_objects.get_initialized_test_path(request)
    return _init_application_fixture(
        dir,
        _init_app_context_fresh_user,
        request)

@pytest.fixture
def app_initialized_user(request):
    Storage.reset()
    dir = appxf_objects.get_initialized_test_path(request)
    return _init_application_fixture(
        dir,
        _init_app_context_initialized_user,
        request)

@pytest.fixture
def app_unlocked_user(app_initialized_user):
    ''' This fixture uses same data as intialized_user '''
    app: ApplicationMock = app_initialized_user['app_user']
    app.perform_login_unlock()
    return app_initialized_user

@pytest.fixture
def app_unlocked_user_admin_pair(request):
    Storage.reset()
    dir = appxf_objects.get_initialized_test_path(request)
    data = _init_application_fixture(
        dir,
        _init_app_context_user_admin_pair,
        request)
    # unlock users
    for user in data['users']:
        Storage.switch_context('user')
        app: ApplicationMock = data[f'app_{user}']
        app.perform_login_unlock()
    Storage.switch_context('')
    return data

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


### Application Context Initialization

# This function applies general handling of the context initialization to be
# applied to the test setup:
def _init_application_fixture(path_testing, context_init_fun, request):
    ''' Ensure context intialization and apply to test case

    Arguments:
    path_testing -- base directory for testing
    context_init_fun -- defines the context initialization
    request -- test case details via pytest fixture

    Returns: Dictionary with:
      'path' -- root of application context
      'users' -- list of initialized applications
      'app_<user>' -- The ApplicationMock objects for each user.
    '''
    original_dict = context_init_fun()
    path_origin = original_dict['path']
    path = os.path.join(path_testing,
                        request.node.name)
    _init_path_from_origin(path, path_origin)
    fixed_dict = {'path': path,
                  'users': original_dict['users']}
    def add_app(path, user):
        Storage.switch_context(user)
        return ApplicationMock(path, user)
    app_dict = {f'app_{user}': add_app(path, user)
                for user in original_dict['users']}
    return {**fixed_dict, **app_dict}

# The following structure applies to all init functions:
#
# Parameters:
#   path_testing -- the root folder for all testing files
#
# Return: A structure with:
#   'path' -- root of the initialized application context
#   'users' -- list of initialized users It is intentional that the
# ApplicationMock objects are not forwarded
def _init_app_context_fresh_user():
    path_origin = os.path.join(appxf_objects.testing_base_dir,
                               f'app_fresh_user_{version}')
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

def _init_app_context_initialized_user():
    path_origin = os.path.join(appxf_objects.testing_base_dir,
                               f'app_initialized_user_{version}')
    # we rely on fresh user:
    data_derive = _init_app_context_fresh_user()
    return_dict = {'path': path_origin, 'users': data_derive['users']}
    # do not repeat if already present:
    if os.path.exists(path_origin):
        return return_dict
    # otherwise, create:
    _init_path_from_origin(path_origin, origin_path=data_derive['path'], keep = True)
    # We need to get the app to set the password
    Storage.switch_context('user')
    app_user = ApplicationMock(path_origin, 'user')
    app_user.perform_login_init()
    return return_dict

def _init_app_context_user_admin_pair():
    path_origin = os.path.join(appxf_objects.testing_base_dir,
                               f'app_admin_user_pair_{version}')
    return_dict = {'path': path_origin, 'users': ['admin', 'user']}
    # do not repeat if already present:
    if os.path.exists(path_origin):
        return return_dict
    # otherwise, create:
    _init_path_from_origin(path_origin, keep = True)
    # Admin and user will be, at least initialized with their own passwords.
    # Admin will be initialized with registry.
    Storage.switch_context('admin')
    app_user = ApplicationMock(path_origin, 'admin')
    app_user.perform_login_init()
    app_user.perform_registration_admin_init()
    Storage.switch_context('user')
    app_admin = ApplicationMock(path_origin, 'user')
    app_admin.perform_login_init()
    Storage.switch_context('')
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

    Fucntion is expected to be executed before any test case. Modelled as test
    case to re-use fixtures.
    '''
    dir = appxf_objects.get_initialized_test_path(request)
    for context in ['fresh_user', 'initialized_user', 'app_admin_user_pair', ]:
        path = os.path.join(dir, f'app_{context}_{version}')
        if os.path.exists(path):
            shutil.rmtree(path)
            print(f'Removed {path}')
        else:
            print(f'No cleanup required for {path}')
