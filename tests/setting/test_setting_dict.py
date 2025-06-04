
import pytest

from kiss_cf.setting import SettingDict, Setting
from kiss_cf.setting import AppxfSettingConversionError, AppxfSettingError
from kiss_cf.setting import SettingString, SettingInt, SettingFloat, SettingBool

from kiss_cf.storage import RamStorage

# REQ: SettingDict shall be able to be filled with settings by:
#  1) settings parameter on constructor taking a dictionary {key: setting}
#  2) [] assignment (one by one): setting_dict[key] = setting
#  3) .value interface taking a dictionary {key: setting}
#
# REQ: Each setting above can be (1) a plain value, (2) a setting class, (3) a
# setting object or (4) a tuple (type) or (type, value).

# List of sample init values:
init_values = [
    # Key   Value                       Type        Value_Out       String_Out
    # Value based input
    ('v1',  'test',                     'string',   'test',         'test'),
    ('v2',  42,                         'int',      42,             '42'),
    ('v3',  1.123,                      'float',    1.123,          '1.123'),
    ('v4',  True,                       'bool',     True,           '1'),
    # Setting class based input
    ('SC1', SettingString,              'string',   '',             ''),
    ('SC2', SettingInt,                 'int',      0,              '0'),
    ('SC3', SettingFloat,               'float',    0.0,            '0.0'),
    ('SC4', SettingBool,                'bool',     False,          '0'),
    # Setting object based input
    ('SO1',  Setting.new(str, 'test'),   'string',   'test',         'test'),
    ('SO2',  Setting.new(int,42),        'int',      42,             '42'),
    ('SO3',  Setting.new(float,1.123),   'float',    1.123,          '1.123'),
    ('SO4',  Setting.new(bool,True),     'bool',     True,           '1'),
    # Tuple based input
    ('T1',  ('pass', '123abc'),         'pass',     '123abc',       '123abc'),
    ('T2',  ('email', 'some@one.com'),  'email',    '',             ''),
    ('T3',  ('integer',),               'int',      0,              '0'),
]

# construct a Setting object from one of the init_values tuples
def _get_setting_reference(t):
    if isinstance(t[1], tuple):
        # tuple based init with type+value
        if len(t[1]) == 2:
            return Setting.new(t[2], value=t[1][1])
        # tuple based init with type, only
        else:
            return Setting.new(t[2])
    if isinstance(t[1], type):
        # type based input
        return Setting.new(t[2])
    if isinstance(t[1], Setting):
        # Direct Setting based input
        return t[1]
    return Setting.new(t[2], value=t[1])

# verify a setting dict against the init_value tuples
def verify_setting_dict(setting_dict: SettingDict, t_list: list[tuple]):
    for t in t_list:
        setting_ref = _get_setting_reference(t)
        assert setting_dict[t[0]] == setting_ref.value
        assert type(setting_dict.get_setting(t[0])) == type(setting_ref)
        assert setting_dict.get_setting(t[0]).value == setting_ref.value
        assert setting_dict.get_setting(t[0]).to_string() == setting_ref.to_string()
        # checking input/value interfaces:
        assert setting_dict.value[t[0]] == setting_ref.value
        assert setting_dict.input[t[0]] == setting_ref.input

# manual filling
def test_setting_dict_init_and_fill():
    setting_dict = SettingDict()
    for t in init_values:
        setting_dict[t[0]] = t[1]
    verify_setting_dict(setting_dict, init_values)

# init by dict
def test_setting_dict_init_by_dict():
    # build dict:
    dict_input = {t[0]: t[1]
                  for t in init_values}
    setting_dict = SettingDict(dict_input)
    verify_setting_dict(setting_dict, init_values)

# empty init, set by value
def test_setting_dict_init_by_value():
    setting_dict = SettingDict()
    setting_dict.value = {
        t[0]: t[1]
        for t in init_values}
    verify_setting_dict(setting_dict, init_values)

# Testing invalid inputs - three test cases, each - for __init__, [] and .value
# interfaces.

failure_cases = [
    # TC name       # settings input        # list of strings that must be in error message
    ('input type',  42,                     [
        f'42 of type {int}']),
    ('invalid key', {42: (str)},            [
        f'42 of type {int}', 'Only string keys are supported']),
    ('invalid value', {'test': ('email', 'fail')}, [
        ]),
    ('empty tuple', {'test': tuple()},      [
        '()']),
    ('long tuple', {'test': (1,2,3)},      [
        '(1, 2, 3)']),
    ]

@pytest.mark.parametrize('name, settings, error_parts',
                         failure_cases,
                         ids = [t[0] for t in failure_cases])
def test_setting_dict_invalid_init(name, settings, error_parts):
    with pytest.raises(AppxfSettingError) as exc_info:
        SettingDict(settings = settings)
    print(exc_info.value)
    print(exc_info.value.__cause__)
    assert 'Cannot set/initialize SettingDict' in str(exc_info.value)
    for part in error_parts:
        assert part in str(exc_info.value) + str(exc_info.value.__cause__)

@pytest.mark.parametrize('name, settings, error_parts',
                         failure_cases,
                         ids = [t[0] for t in failure_cases])
def test_setting_dict_invalid_value(name, settings, error_parts):
    setting_dict = SettingDict()
    with pytest.raises(AppxfSettingError) as exc_info:
        setting_dict.value = settings
    print(exc_info.value)
    print(exc_info.value.__cause__)
    for part in error_parts:
        assert part in str(exc_info.value) + str(exc_info.value.__cause__)

@pytest.mark.parametrize('name, settings, error_parts',
                         failure_cases,
                         ids = [t[0] for t in failure_cases])
def test_setting_dict_invalid_setitem(name, settings, error_parts):
    setting_dict = SettingDict()
    if not isinstance(settings, dict):
        # those cases are only for __init__and value assignments
        return
    with pytest.raises(AppxfSettingError) as exc_info:
        for key, value in settings.items():
            setting_dict[key] = value
    print(exc_info.value)
    print(exc_info.value.__cause__)
    for part in error_parts:
        assert part in str(exc_info.value) + str(exc_info.value.__cause__)


# ####################/
# Value Manipulations
# ///////////////////

def test_setting_dict_set_valid_value():
    setting_dict = SettingDict({
        'test': ('email', 'my@email.com')
        })
    setting_dict['test'] = 'new@email.com'
    assert setting_dict['test'] == 'new@email.com'
    assert setting_dict.get_setting('test').value == 'new@email.com'

def test_setting_dict_set_via_value():
    setting_dict = SettingDict({
        'test': ('email', 'my@email.com')
        })
    setting_dict.value = {'test': 'new@email.com'}
    assert setting_dict['test'] == 'new@email.com'
    assert setting_dict.get_setting('test').value == 'new@email.com'

def test_setting_dict_overwriting_by_setting_object():
    setting_dict = SettingDict({
        'test': ('bool', False)})
    assert setting_dict['test'] == False
    assert type(setting_dict.get_setting('test')) == SettingBool
    # overwrite by Email
    setting_dict['test'] = Setting.new('string', 'some')
    assert setting_dict['test'] == 'some'
    assert type(setting_dict.get_setting('test')) == SettingString

def test_setting_dict_overwriting_by_setting_class():
    setting_dict = SettingDict({
        'test': ('bool', False)})
    assert setting_dict['test'] == False
    assert type(setting_dict.get_setting('test')) == SettingBool
    # overwrite by Email
    setting_dict['test'] = SettingInt
    assert setting_dict['test'] == SettingInt.get_default()
    assert type(setting_dict.get_setting('test')) == SettingInt

def test_setting_dict_overwriting_by_tuple():
    setting_dict = SettingDict({
        'test': ('bool', False)})
    assert setting_dict['test'] == False
    assert type(setting_dict.get_setting('test')) == SettingBool
    # overwrite by Email
    setting_dict['test'] = ('string', 'some')
    assert setting_dict['test'] == 'some'
    assert type(setting_dict.get_setting('test')) == SettingString

def test_setting_dict_keeps_setting_object():
    setting_dict = SettingDict({
        'test': (str, 'init')})
    assert setting_dict['test'] == 'init'
    init_object = setting_dict.get_setting('test')
    # set new value
    setting_dict['test'] = 'new'
    assert setting_dict['test'] == 'new'
    new_object = setting_dict.get_setting('test')
    assert new_object is init_object
    # set overwriting variant
    setting_dict['test'] = (str, 'overwriting')
    assert setting_dict['test'] == 'overwriting'
    new_object = setting_dict.get_setting('test')
    assert new_object is not init_object

def test_setting_dict_get_nonexisting():
    setting_dict = SettingDict()
    with pytest.raises(KeyError):
        setting_dict['test']

def test_setting_dict_set_invalid_after_delete():
    # test case derived from test_setting_dict_set_invalid_value
    setting_dict = SettingDict({
        'test': ('email', 'my@email.com')
        })
    del setting_dict['test']
    setting_dict['test'] = 'fail'
    assert setting_dict['test'] == 'fail'
    assert setting_dict.get_setting('test').value == 'fail'
    assert setting_dict.get_setting('test').__class__ == SettingString

def test_setting_dict_delete_non_existing():
    setting_dict = SettingDict()
    with pytest.raises(KeyError):
        del setting_dict['test']

def test_setting_dict_nested():
    setting_dict = SettingDict(settings={
        'int': (int, '42'),
        'nested': {'int': (int, '13')}
    })
    assert setting_dict['int'] == 42
    assert setting_dict['nested'] == {'int': 13}
    assert setting_dict['nested']['int'] == 13
    # verify same based on value
    assert setting_dict.value['int'] == 42
    assert setting_dict.value['nested'] == {'int': 13}
    assert setting_dict.value['nested']['int'] == 13
    # and verify the input which are corresponding strings:
    assert setting_dict.input['int'] == '42'
    assert setting_dict.input['nested'] == {'int': '13'}
    assert setting_dict.input['nested']['int'] == '13'

# REQ: When updating SettingDict via .value with some invalid values, the
# values shall not be applied in case the error is cought.
def test_setting_dict_invalid_not_applied():
    setting_dict = SettingDict(settings={
        'A': ('email', 'a@something.de'),
        'B': ('email', 'b@something.de'),
        'C': ('email', 'c@something.de'),
    })
    # some checks of the initialization
    assert 'a@' in setting_dict['A']
    assert 'b@' in setting_dict['B']
    assert 'c@' in setting_dict['C']
    for key in setting_dict:
        assert type(setting_dict.get_setting(key)) == type(Setting.new('email'))
    # cycle through keys and try to apply a wrong value to each of those keys.
    # Only checking one position would not be sufficient in case SettingDict
    # already fails with the first assignment. No assumptions on order of
    # execution are made.
    for change_key in setting_dict:
        change_dict = setting_dict.value
        change_dict[change_key] = 'wrong-email'
        with pytest.raises(AppxfSettingError) as exc_info:
            setting_dict.value = change_dict
        assert 'wrong-email' in str(exc_info.value)
        # same checks as after init (no changes must be applied)
        assert 'a@' in setting_dict['A']
        assert 'b@' in setting_dict['B']
        assert 'c@' in setting_dict['C']
        for key in setting_dict:
            assert type(setting_dict.get_setting(key)) == type(Setting.new('email'))


# REQ: When changing the underlying Setting directly, the value returned by
# SettingDict must appear updated accordingly.
#
# Origin: The initial implementation used UserDict with a duplicate storage
# for values in the UserDict.data. This implementation did not satisfy the
# requirement.
#
# Rationale: The GUI implementation has a GUI for just a Setting on top of
# which the GUI for SettingDict is build.
def test_setting_dict_update_on_setting():
    setting_dict = SettingDict()
    setting_dict['test'] = (str, 'seomething')
    setting = setting_dict.get_setting('test')
    setting.value = 'new'
    assert setting.input == 'new'
    assert setting.value == 'new'
    assert setting_dict['test'] == 'new'
    assert setting_dict.get_setting('test').input == 'new'
    assert setting_dict.get_setting('test').value == 'new'

# #################/
# Storable Behavior
# ////////////////

def test_setting_dict_store_load_cycle():
    # we use an integer here since it differs in "input" and stored "value".
    # And we use an arbitrary string (email) to be a bit more verbose.
    setting_dict = SettingDict({'entry': ('email',), 'input_check': (int,)})
    storage = RamStorage()
    setting_dict.set_storage(storage, on_load_unknown='ignore', store_setting_object=False)
    setting_dict['entry'] = 'before@store.com'
    setting_dict['input_check'] = '1'

    setting_dict.store()
    setting_dict['entry'] = 'after@store.com'
    setting_dict['input_check'] = '2'
    assert setting_dict['entry'] == 'after@store.com'
    assert setting_dict.get_setting('entry').value == 'after@store.com'
    assert setting_dict.get_setting('entry').input == 'after@store.com'
    assert setting_dict['input_check'] == 2
    assert setting_dict.get_setting('input_check').value == 2
    assert setting_dict.get_setting('input_check').input == '2'

    setting_dict_reload = SettingDict({'entry': ('email',), 'input_check': (int,)})
    setting_dict_reload.set_storage(storage)
    setting_dict_reload.load()
    assert setting_dict_reload['entry'] == 'before@store.com'
    assert setting_dict_reload.get_setting('entry').value == 'before@store.com'
    assert setting_dict_reload.get_setting('entry').input == 'before@store.com'
    assert setting_dict_reload['input_check'] == 1
    assert setting_dict_reload.get_setting('input_check').value == 1
    assert setting_dict_reload.get_setting('input_check').input == '1'

def test_setting_dict_store_load_invalid_init():
    storage = RamStorage()
    setting_dict = SettingDict(
        settings={'entry': ('email',)},
        storage=storage
        )
    setting_dict.store()
    # This load should not fail. Even though we load an invalid value, it shall
    # be accepted since it is the default value:
    setting_dict.load()
    # loading an invalid value while a valid one is stored is intended
    # behavior as long as it is the default value:
    setting_dict['entry'] = 'someone@nowhere.com'
    assert setting_dict['entry'] == 'someone@nowhere.com'
    setting_dict.load()
    assert setting_dict['entry'] == ''
