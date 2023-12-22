from pytest_bdd import scenarios, given, when, then, parsers
from pytest import fixture
from kiss_cf.storage import LocalStorageLocation, sync
import os.path
import shutil

scenarios('test_bdd_sync.feature')

@fixture(autouse=True)
def context():
    'Provide basic test location'
    env = {}
    env['dir'] = './testing'
    env['file'] = 'some_data'
    env['data'] = ['some data', 'some new data', 'even newer data']
    # ensure clean path
    if os.path.exists(env['dir']):
        shutil.rmtree(env['dir'])
    print(f'Setup: Cleaned path {env["dir"]}')
    yield env
    # remove files again
    if os.path.exists(env['dir']):
        shutil.rmtree(env['dir'])
    print(f'Tear-Down: Cleaned path {env["dir"]}')

@given(parsers.parse('Location {locations}'))
@given(parsers.parse('Locations [{locations}]'))
def initialize_locations(context, locations):
    # Handle locations parameter:
    locations = locations.split(',')
    if not isinstance(locations, list):
        locations = [locations]
    locations = [loc.strip() for loc in locations]
    # ensure locations exists in context:
    if not 'location' in context.keys():
        context['location'] = {}
    # add location objects to context:
    for loc in locations:
        context['location'][loc] = LocalStorageLocation(
            os.path.join(context['dir'], loc))

@given(parsers.parse('{location} writes "{data}" into {file}'))
@when(parsers.parse('{location} writes "{data}" into {file}'))
def write_data(context, location, data, file):
    storage = context['location'][location].get_storage_method(file)
    storage.store(data.encode('utf-8'))

@then(parsers.parse('There is no data in {loc}'))
def no_data_in_location(context, loc):
    assert not os.listdir(os.path.join(context['dir'], loc))

@given(parsers.parse('Synchronizing {loc_a} with {loc_b}'))
@when(parsers.parse('Synchronizing {loc_a} with {loc_b}'))
def synchronizing_data(context, loc_a, loc_b):
    # we will need to synchronize all files from both locations
    file_list = []
    file_list += os.listdir(os.path.join(context['dir'], loc_a))
    file_list += os.listdir(os.path.join(context['dir'], loc_b))
    file_list = list(set(file_list))
    file_list = [file for file in file_list if '.' not in file]
    # to have a sync, corresponding storage must exist
    storage_list_a = [context['location'][loc_a].get_storage_method(file)
                      for file in file_list]
    storage_list_b = [context['location'][loc_b].get_storage_method(file)
                      for file in file_list]
    # Initialize sync
    sync(context['location'][loc_a], context['location'][loc_b])
    del storage_list_a
    del storage_list_b


@then(parsers.parse('{location} contains "{data}" in {file}'))
def contains_data_in_file(context, location, data, file):
    # TODO: remove again - printing sync data
    print(os.listdir(os.path.join(context['dir'], location)))
    print(f'{location} contains "{data}" in {file}')
    if context['location'][location].file_exists(file + '.sync'):
        print('Sync State JSON: \n' +
            context['location'][location].load(file + '.sync').decode('utf-8'))

    storage = context['location'][location].get_storage_method(file)
    read_data = storage.load().decode('utf-8')
    assert read_data == data


@then(parsers.parse('Data in {loc_a} matches data in {loc_b}'))
def data_matches(context, loc_a, loc_b):
    file_list = []
    file_list += os.listdir(os.path.join(context['dir'], loc_a))
    file_list += os.listdir(os.path.join(context['dir'], loc_b))
    file_list = [file for file in file_list if '.' not in file]
    for file in set(file_list):
        file_a = os.path.join(context['dir'], loc_a, file)
        file_b = os.path.join(context['dir'], loc_b, file)
        assert os.path.exists(file_a)
        assert os.path.exists(file_b)
        assert open(file_a).read() == open(file_b).read()
