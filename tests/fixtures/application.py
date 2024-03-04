''' provide fixtures with test application

Using some of the fixtures includes coverage of considerable functionality
which is required to reach initialized applications.
'''
import os
import shutil
import pytest
import toml

from tests.fixtures.env_base import env_base
from tests.fixtures.application_mock import ApplicationMock

# get current kiss_cf version
toml_data = toml.load(open('pyproject.toml'))
version = toml_data['project']['version']
print(f'Current kiss_cf version: {version}')

@pytest.fixture
def app_fresh_user(env_base, request):
    env = env_base
    path_origin = _init_app_fresh_user(env['path_testing'])
    test_name = request.node.name
    # Provide basic test location:
    path = os.path.join(env['path_testing'], test_name)
    _init_test_path(path, path_origin)
    data = _add_application({}, path, 'user')
    return data

@pytest.fixture
def app_initialized_user(env_base, request):
    env = env_base
    path_origin = _init_app_initialized_user(env['path_testing'])
    test_name = request.node.name
    # Provide basic test location:
    path = os.path.join(env['path_testing'], test_name)
    _init_test_path(path, path_origin)
    data = _add_application({}, path, 'user')
    return data

@pytest.fixture
def app_unlocked_user(app_initialized_user, request):
    ''' This fixture uses same data as intialized_user '''
    app: ApplicationMock = app_initialized_user['app_user']
    app.unlock_user()
    return app_initialized_user

@pytest.fixture
def app_fresh_admin(env_base, request):
    pass

def _init_app_fresh_user(path_testing: str):
    path_origin = os.path.join(path_testing, f'app_fresh_user_{version}')
    # do not repeat if already present:
    if os.path.exists(path_origin):
        return path_origin
    # otherwise, create:
    _init_test_path(path_origin, keep = True)
    # A fresh user has no data on the path but the user's application path is
    # not generated on adding application:
    _add_application({}, path_origin, 'user')
    return path_origin

def _init_app_initialized_user(path_testing: str):
    path_origin = os.path.join(path_testing, f'app_initialized_user_{version}')
    # we rely on fresh user:
    path_derive = _init_app_fresh_user(path_testing)
    # do not repeat if already present:
    if os.path.exists(path_origin):
        return path_origin
    # otherwise, create:
    _init_test_path(path_origin, origin_path=path_derive, keep = True)
    # We need to get the app to set the password
    data = _add_application({}, path_origin, 'user')
    app: ApplicationMock = data['app_user']
    app.init_password()
    return path_origin

def _init_app_fresh_admin():
    pass

def _init_test_path(path, origin_path: str = '', keep: bool = False):
    # clear target path
    if os.path.exists(path):
        if keep:
            # folder is present and shall be retained
            return
        shutil.rmtree(path)
        print(f'Deleted path {path}')
    # re-create path
    if origin_path:
        # copy from origin
        shutil.copytree(origin_path, path)
        print(f'Initialized {path} from {origin_path}')
    else:
        # ensure path existing
        os.makedirs(path, exist_ok=True)
        print(f'Created path {path}')


def _add_application(data, root_dir: str, user: str):
    # ensure directory exists
    path = os.path.join(root_dir, f'app_{user}')
    os.makedirs(path, exist_ok = True)
    # add application to data
    data[f'app_{user}'] = ApplicationMock(path, user)
    return data

def _init_fresh_admin(root_dir: str):
    return _add_application({}, root_dir, 'admin')

def _init_fresh_user(root_dir: str):
    data = _init_fresh_admin(root_dir)
    # TODO: initialize admin
    return _add_application(data, root_dir, 'user')

def test_cleanup(env_base):
    ''' cleanup current kiss_cf directories

    Fucntion is expected to be executed before any test case. Modelled as test
    case to re-use fixtures.
    '''
    env = env_base
    for context in ['fresh_user', 'fresh_admin', 'multi_user']:
        path = os.path.join(env['path_testing'], f'app_{context}_{version}')
        if os.path.exists(path):
            shutil.rmtree(path)
            print(f'Removed {path}')
        else:
            print(f'No cleanup required for {path}')
