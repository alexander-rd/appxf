from pytest_bdd import scenarios, scenario, given, when, then, parsers
from pytest import fixture
import pytest
from kiss_cf.storage import LocalStorageMaster, sync, StorageMasterMock
from kiss_cf.security import SecurePrivateStorageMaster
from kiss_cf.registry import SecureSharedStorageMaster, Registry
from kiss_cf.config import Config
import os.path
import shutil

# Fixtures upon which the ones we require are depenent on must be included as
# well. Otherwise, we will get a "fixture not found".
from tests.fixtures.env_base import env_base
from tests.fixtures.env_storage import env_test_directory
from tests.fixtures.env_security import env_security_unlocked
scenarios('test_bdd_sync.feature')

# TODO: should be rewritten to use the application.py fixture

# define default context/environment
@fixture(autouse=True)
def env(env_test_directory, env_security_unlocked):
    env = env_test_directory
    env.update(env_security_unlocked)
    # ensure commonly used fields being present
    env['location'] = {}
    env['location']['registry'] = LocalStorageMaster(
        os.path.join(env['dir'], 'registry'))
    factory = SecurePrivateStorageMaster(
        LocalStorageMaster(os.path.join(env['dir'], 'config')),
        security=env['security'])
    env['config'] = Config(default_storage=factory)
    env['storage factory'] = {}
    registry = Registry(
        local_base_storage=env['location']['registry'],
        remote_base_storage=StorageMasterMock(),
        security=env['security'],
        config=env['config'])
    registry.initialize_as_admin()
    env['registry'] = registry
    return env

# @given(parsers.parse('Location {locations}'))
@given(parsers.parse('Locations [{locations}]'))
def initialize_locations(env, request, locations):
    print(f'Locations {locations}')
    # Handle locations parameter:
    locations = locations.split(',')
    if not isinstance(locations, list):
        locations = [locations]
    locations = [loc.strip() for loc in locations]
    # add location objects to context:
    for loc in locations:
        loc_storage = LocalStorageMaster(
            os.path.join(env['dir'], loc))
        env['location'][loc] = loc_storage
        #env['storage method'][loc] = loc_storage.get_storage
        env['storage factory'][loc] = loc_storage

@given(parsers.parse('Location {locations} is using Default'))
def set_storage_method_default(env, locations):
    print(f'Location {locations} is using Default')
    # Nothing to do
    pass

    # define and assign the storage method constructor:
    for loc in locations:
        #env['storage method'][loc] = lambda file: SecurePrivateStorage(
        #    base_method = env['location'][loc].get_storage(file),
        #    security = env['security'])
        env['storage factory'][loc] = SecurePrivateStorageMaster(
            storage=env['location'][loc],
            security=env['security'])

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
        #env['storage method'][loc] = lambda file: SecurePrivateStorage(
        #    base_method = env['location'][loc].get_storage(file),
        #    security = env['security'])
        env['storage factory'][loc] = SecurePrivateStorageMaster(
            storage=env['location'][loc],
            security=env['security'])


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
        #env['storage method'][loc] = lambda file: SecureSharedStorage(
        #    file,
        #    location = env['location'][loc],
        #    security = env['security'],
        #    user_database=env['user database'])
        env['storage factory'][loc] = SecureSharedStorageMaster(
            storage=env['location'][loc],
            security=env['security'],
            registry=env['registry'])


@given(parsers.parse('{location} writes "{data}" into {file}'))
@when(parsers.parse('{location} writes "{data}" into {file}'))
def write_data(env, location, data, file):
    print(f'{location} writes "{data}" into {file}')

    #storage = env['storage method'][location](file)
    storage = env['storage factory'][location].get_storage(file)
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
    file_list = []
    file_list += os.listdir(os.path.join(env['dir'], loc_a))
    file_list += os.listdir(os.path.join(env['dir'], loc_b))
    file_list = list(set(file_list))
    file_list = [file for file in file_list if '.' not in file]
    # to have a sync, corresponding storage must exist
    storage_list_a = [env['storage factory'][loc_a].get_storage(file)
                      for file in file_list]
    storage_list_b = [env['storage factory'][loc_b].get_storage(file)
                      for file in file_list]
    sync(env['location'][loc_a], env['location'][loc_b])
    del storage_list_a
    del storage_list_b


@then(parsers.parse('{location} contains "{data}" in {file}'))
def contains_data_in_file(env, location, data, file):
    print(f'{location} contains "{data}" in {file}')
    # just for debugging:
    # print(os.listdir(os.path.join(context['dir'], location)))
    if env['location'][location].exists(file + '.sync'):
        print('Sync State JSON: \n' +
            env['location'][location].load(file + '.sync').decode('utf-8'))

    print(env)
    print(env['storage factory'])
    storage = env['storage factory'][location].get_storage(file)
    print(f'Using: {storage.__class__.__name__}')
    read_data = storage.load().decode('utf-8')
    assert read_data == data


@then(parsers.parse('Data in {loc_a} matches data in {loc_b}'))
def data_matches(env, loc_a, loc_b):
    print(f'Data in {loc_a} matches data in {loc_b}')
    master_a: LocalStorageMaster = env['storage factory'][loc_a]
    master_b: LocalStorageMaster = env['storage factory'][loc_b]
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
        storage_a = master_a.get_storage(file, create=False)
        data_a = storage_a.load()
        storage_b = master_b.get_storage(file, create=False)
        data_b = storage_b.load()
        assert data_a == data_b
