from pytest_bdd import scenarios, scenario, given, when, then, parsers
from pytest import fixture
from kiss_cf.storage import Storage

from tests._fixtures import application
from tests._fixtures.application_mock import ApplicationMock


# Fixtures upon which the ones we require are depenent on must be included as
# well. Otherwise, we will get a "fixture not found".
from tests._fixtures import appxf_objects
scenarios('test_bdd_registry.feature')

@fixture(autouse=True)
def env():
    return {}


@given(parsers.parse('{role} with an application in status {app_status}'))
def provide_application(env, request, role, app_status):
    print(f'Role {role} with status {app_status}')

    Storage.switch_context(role)
    if app_status in ['unregistered', 'initialized']:
        # unregistered is local app "initialized", the next state would be
        # registered
        app = application.get_application_login_initialized(request, role)
    elif app_status in ['admin initialized']:
        app = application.get_application_registration_admin_initialized(request, role)
    else:
        raise ValueError(f'Unknown application status: {app_status}')
    Storage.switch_context('')
    env['app_' + role] = app

@given(parsers.parse('all applications are unlocked'))
def unlock_all_applications(env):
    for key, item in env.items():
        if not key.startswith('app_'):
            continue
        role = key[len('app_'):]
        print(f'Unlocking {role}')
        Storage.switch_context(role)
        app: ApplicationMock = item
        app.perform_login_unlock()
        Storage.switch_context('')
