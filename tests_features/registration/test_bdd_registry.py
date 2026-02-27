# Copyright 2025-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
from pytest import fixture
from pytest_bdd import given, parsers, scenarios, then, when

from appxf.storage import Storage
from tests._fixtures import application, test_sandbox
from tests._fixtures.app_harness import AppHarness

# Fixtures upon which the ones we require are depenent on must be included as
# well. Otherwise, we will get a "fixture not found".
scenarios('test_bdd_registry.feature')


@fixture(autouse=True)
def env(request):
    # cleanup
    test_sandbox.init_test_sandbox_from_fixture(request, cleanup=True)
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
        role = key[len('app_') :]
        print(f'Unlocking {role}')
        Storage.switch_context(role)
        app: AppHarness = item
        app.perform_login_unlock()
        Storage.switch_context('')


def map_config_section_name(config_section: str) -> str:
    '''Map config sections to application harness

    Map config_section fields as used in BDD test cases to names used in the application
    harness.
    '''
    if config_section in ['registry shared']:
        config_section = 'REGISTRATION_SHARED'
    if config_section in ['shared']:
        config_section = 'SHARED'
    return config_section


@given(
    parsers.parse(
        '{role} is storing {config_data} in the {config_section} configuration'
    )
)
def store_value_in_configuration(env, role, config_data, config_section):
    '''Check value of test configuration

    Arguments:
    role -- determines the application harness to be used
    config_section -- the config section which must contain a setting "test"
    config_data -- the value of the "test" setting in the config_section
    '''
    app: AppHarness = env['app_' + role]
    config_section = map_config_section_name(config_section)

    Storage.switch_context(role)
    # section must exist:
    assert config_section in app.config.sections
    # the "test" setting must exist
    assert 'test' in app.config.section(config_section)
    # and it must have the right value
    app.config.section(config_section)['test'] = config_data
    # just to ensure setting the value worked:
    assert config_data == app.config.section(config_section)['test']
    # ensure information being persisted
    app.config.store()
    Storage.switch_context('')


@then(
    parsers.parse(
        '{role} has stored {config_data} in the {config_section} configuration'
    )
)
def verify_stored_in_configuration(env, role, config_data, config_section):
    '''Check value of test configuration

    Arguments:
    role -- determines the application harness to be used
    config_section -- the config section which must contain a setting "test"
    config_data -- the value of the "test" setting in the config_section
    '''
    app: AppHarness = env['app_' + role]
    config_section = map_config_section_name(config_section)

    Storage.switch_context(role)
    # section must exist:
    assert config_section in app.config.sections
    # the "test" setting must exist
    assert 'test' in app.config.section(config_section)
    # and it must have the right value
    assert config_data == app.config.section(config_section)['test']
    Storage.switch_context('')


@given(parsers.parse('{role} {config_section} configuration is empty'))
def empty_value_in_configuration(env, role, config_section):
    env['app_' + role]
    verify_stored_in_configuration(env, role, '', config_section)


@when(parsers.parse('{role_user} registers the application to {role_admin}'))
def register_application(env, role_user, role_admin):
    app_user: AppHarness = env['app_' + role_user]
    app_admin: AppHarness = env['app_' + role_admin]
    # Share admin keys:
    admin_keys = app_admin.perform_registration_get_admin_keys()
    app_user.perform_registration_load_admin_keys(admin_keys)
    # Request/Response cycle:
    request = app_user.perform_registration_get_request()
    response = app_admin.perform_registration_from_request(request_bytes=request)
    app_user.perform_registration_set_response(response_bytes=response)
