from pytest_bdd import scenarios, scenario, given, when, then, parsers
from pytest import fixture
from kiss_cf.storage import Storage
# from tests._fixtures.application import app_unlocked_user, app_fresh_user, app_initialized_user, app_registered_unlocked_user_admin_pair, app_unlocked_user_admin_pair
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

    Storage.switch_context('role')
    # env[f'app_{role}'] = application.app_fresh_user(request)
    # print(env)

    # A = app_unlocked_user(request, role)