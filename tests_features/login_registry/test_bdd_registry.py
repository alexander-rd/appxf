from pytest_bdd import scenarios, scenario, given, when, then, parsers
from pytest import fixture
from kiss_cf.storage import Storage

from tests._fixtures import application
from tests._fixtures.app_harness import AppHarness


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
        app: AppHarness = item
        app.perform_login_unlock()
        Storage.switch_context('')

@given(parsers.parse('{role} has stored {config_data} in the {config_item} configuration'))
@then(parsers.parse('{role} has stored {config_data} in the {config_item} configuration'))
def stored_in_configuration(env, role, config_data, config_item):
    app: AppHarness = env['app_' + role]
    Storage.switch_context(role)
    #if config_item == 'registry shared':
    #    app.store_in_registry_shared_configuration(config_data)
    #elif config_item == 'shared':
    #    app.store_in_shared_configuration(config_data)
    #else:
    #    raise ValueError(f'Unknown configuration item: {config_item}')
    Storage.switch_context('')

@given(parsers.parse('{role} {config_item} is empty'))
def stored_in_configuration(env, role, config_item):
    app: AppHarness = env['app_' + role]
    Storage.switch_context(role)
    # TODO
    Storage.switch_context('')

@when(parsers.parse('{role_user} registers the application to {role_admin}'))
def register_application(env, role_user, role_admin):
    app_user: AppHarness = env['app_' + role_user]
    app_admin: AppHarness = env['app_' + role_admin]
    request = app_user.perform_registration_get_request()
    response = app_admin.perform_registration_from_request(request_bytes=request)
    app_user.perform_registration_set_response(response_bytes=response)