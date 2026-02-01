from pytest_bdd import scenarios, scenario, given, when, then, parsers
from pytest import fixture
import pytest
from appxf.storage import Storage, LocalStorage, sync, StorageToBytes
from appxf.security import SecurePrivateStorage
from appxf.registry import SecureSharedStorage, Registry
from appxf.config import Config
import os.path

# Fixtures upon which the ones we require are depenent on must be included as
# well. Otherwise, we will get a "fixture not found".
from tests._fixtures import appxf_objects
import tests._fixtures.test_sandbox
scenarios('test_bdd_sync.feature')

# TODO: should be rewritten to use the application.py fixture

# define default context/environment
@fixture(autouse=True)
def env(request):
    Storage.reset()

    env = {'dir': tests._fixtures.test_sandbox.init_test_sandbox_from_fixture(request)}
    # commonly used objects:
    env['security'] = appxf_objects.get_security_unlocked(path=env['dir'])
    env['config'] = Config(default_storage=LocalStorage.get_factory(
        path=os.path.join(env['dir'], 'config')))
    registry = Registry(
        local_storage_factory=LocalStorage.get_factory(
            path=os.path.join(env['dir'], 'local_registry')),
        remote_storage_factory=LocalStorage.get_factory(
            path=os.path.join(env['dir'], 'remote_registry')),
        security=env['security'],
        config=env['config'])
    registry.initialize_as_admin()
    env['registry'] = registry
    # empty field for to be added storages
    env['storage_factory'] = {}
    return env

# @given(parsers.parse('Location {locations}'))
@given(parsers.parse('Locations [{locations}]'))
def initialize_locations(env, request, locations):
    ''' Ensure location paths exist '''
    print(f'Locations {locations}')
    # Handle locations parameter:
    locations = locations.split(',')
    if not isinstance(locations, list):
        locations = [locations]
    locations = [loc.strip() for loc in locations]

    # add location objects to context:
    for loc in locations:
        this_path = os.path.join(env['dir'], loc)
        if not os.path.exists(this_path):
            os.makedirs(this_path)

@given(parsers.parse('Location {locations} is using Default'))
def set_storage_method_default(env, locations):
    print(f'Location {locations} is using Default')
    # define and assign the storage method constructor:
    for loc in locations:
        env['storage_factory'][loc] = LocalStorage.get_factory(
            path=os.path.join(env['dir'], loc))

@given(parsers.parse('Location {locations} is using LocalStorage'))
def set_storage_method_local(env, locations):
    print(f'Location {locations} is using LocalStorage')
    for loc in locations:
        env['storage_factory'][loc] = LocalStorage.get_factory(
            path=os.path.join(env['dir'], loc))

@given(parsers.parse('Location {locations} is using SecurePrivateStorage'))
def set_storage_method_secure_private(env, locations):
    print(f'Location {locations} is using SecurePrivateStorage')
    # Handle locations parameter
    locations = locations.split(',')
    if not isinstance(locations, list):
        locations = [locations]
    locations = [loc.strip() for loc in locations]

    # define and assign the storage method constructor:
    for loc in locations:
        env['storage_factory'][loc] = SecurePrivateStorage.get_factory(
            security=env['security'],
            base_storage_factory=LocalStorage.get_factory(
                path=os.path.join(env['dir'], loc))
            )
    # TODO: the keywords for get_factory (and others?) definitely needs to be
    # updated in all the deriving classes - it's not good to work with them.


@given(parsers.parse('Location {locations} is using SecureSharedStorage'))
def define_storage_method_secure_shared(env, locations):
    print(f'Location {locations} is using SecureSharedStorage')
    # Handle locations parameter
    locations = locations.split(',')
    if not isinstance(locations, list):
        locations = [locations]
    locations = [loc.strip() for loc in locations]

    # Ensure security is in context:
    env['user database'] = None
    # Ensure user database is in context:

    for loc in locations:
        # TODO: This is a problem with the factories on derived storages. You
        # cannot construct a reasonable factory if get_factory does not use a
        # factory for base_storage.
        env['storage_factory'][loc] = SecureSharedStorage.get_factory(
            base_storage_factory=LocalStorage.get_factory(
                path=os.path.join(env['dir'], loc)),
            security=env['security'],
            registry=env['registry'])


@given(parsers.parse('{location} writes "{data}" into {file}'))
@when(parsers.parse('{location} writes "{data}" into {file}'))
def write_data(env, location, data, file):
    print(f'{location} writes "{data}" into {file}')

    #storage = env['storage method'][location](file)
    print(env)
    storage: Storage = env['storage_factory'][location](file)
    print(f'Using: {storage.__class__.__name__}')
    storage.store(data.encode('utf-8'))

@then(parsers.parse('There is no data in {loc}'))
def no_data_in_location(env, loc):
    print(f'There is no data in {loc}')
    assert not os.listdir(os.path.join(env['dir'], loc))

@given(parsers.parse('Synchronizing {loc_a} with {loc_b}'))
@when(parsers.parse('Synchronizing {loc_a} with {loc_b}'))
def synchronizing_data(env, loc_a, loc_b):
    print(f'Synchronizing {loc_a} with {loc_b}')
    # we will need to synchronize all files from both locations
    sync(env['storage_factory'][loc_a], env['storage_factory'][loc_b])


@then(parsers.parse('{location} contains "{data}" in {file}'))
def contains_data_in_file(env, location, data, file):
    print(f'{location} contains "{data}" in {file}')
    # load storage and print some info for logging:
    # print(os.listdir(os.path.join(context['dir'], location)))
    print(env)
    print(env['storage_factory'])
    storage: StorageToBytes = env['storage_factory'][location](file)
    print(f'Using: {storage.__class__.__name__}')
    # list sync state for debugging:
    if storage.get_meta('sync').exists():
        print('Sync State JSON: \n' +
            str(storage.get_meta('sync').load()))

    # check file content
    read_data = storage.load().decode('utf-8')
    assert read_data == data


@then(parsers.parse('Data in {loc_a} matches data in {loc_b}'))
def data_matches(env, loc_a, loc_b):
    print(f'Data in {loc_a} matches data in {loc_b}')
    storage_factory_a = env['storage_factory'][loc_a]
    storage_factory_b = env['storage_factory'][loc_b]
    # we use an alternate way to determine the file list and not rely on lists
    # from master:
    file_list = []
    file_list += os.listdir(os.path.join(env['dir'], loc_a))
    file_list += os.listdir(os.path.join(env['dir'], loc_b))
    file_list = [file for file in file_list if '.' not in file]
    # check each file
    for file in set(file_list):
        file_a = os.path.join(env['dir'], loc_a, file)
        file_b = os.path.join(env['dir'], loc_b, file)
        assert os.path.exists(file_a)
        assert os.path.exists(file_b)
        storage_a = storage_factory_a(file)
        data_a = storage_a.load()
        storage_b = storage_factory_b(file)
        data_b = storage_b.load()
        assert data_a == data_b
