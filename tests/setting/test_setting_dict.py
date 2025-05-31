
import pytest

from kiss_cf.setting import SettingDict, Setting
from kiss_cf.setting import AppxfSettingConversionError, AppxfSettingError
from kiss_cf.setting import SettingString, SettingInt, SettingFloat, SettingBool

from kiss_cf.storage import RamStorage

sample_input = {
    'string': 'test',
    'int': 42,
    'float': 1.1234,
    'bool': True,
    }

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

def verify_setting_dict(setting_dict: SettingDict, t_list: list[tuple]):
    for t in t_list:
        setting_ref = _get_setting_reference(t)
        assert setting_dict[t[0]] == setting_ref.value
        assert type(setting_dict.get_setting(t[0])) == type(setting_ref)
        assert setting_dict.get_setting(t[0]).value == setting_ref.value
        assert setting_dict.get_setting(t[0]).to_string() == setting_ref.to_string()
        # same setting based tests based on value retrieval:
        assert type(setting_dict.value[t[0]]) == type(setting_ref)
        assert setting_dict.value[t[0]].value == setting_ref.value
        assert setting_dict.value[t[0]].to_string() == setting_ref.to_string()
    # check that value retrieval is same as input retrieval
    assert setting_dict.value == setting_dict.input

# #############/
# Init Variants
# ////////////

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

# general unknown init type
def test_setting_dict_init_fail_by_no_dict():
    # iterable with a iterable subelement that does not contain key+value
    with pytest.raises(AppxfSettingError) as exc_info:
        SettingDict(settings = 42)
    assert f'SettingDict' in str(exc_info.value)
    assert f'42 of type {int}' in str(exc_info.value)

# inconsistent type/value combinations
def test_setting_dict_init_fail_by_invalid_value():
    with pytest.raises(AppxfSettingConversionError):
        SettingDict({
        'test': ('email', 'fail')
        })

def test_setting_dict_init_fail_by_empty_tuple():
    with pytest.raises(AppxfSettingError) as exc_info:
        SettingDict({'test': tuple()})
    assert 'SettingDict' in str(exc_info.value)
    assert '()' in str(exc_info.value)

def test_setting_dict_init_fail_by_too_long_tuple():
    with pytest.raises(AppxfSettingError) as exc_info:
        SettingDict({'test': (1,2,3)})
    assert 'SettingDict' in str(exc_info.value)
    assert '(1, 2, 3)' in str(exc_info.value)

def test_setting_dict_init_fail_by_no_str_key():
    with pytest.raises(AppxfSettingError) as exc_info:
        SettingDict({13: SettingInt(42)})
    assert 'SettingDict' in str(exc_info.value)
    assert 'Cannot set key 13' in str(exc_info.value)
    assert 'Only string keys are supported' in str(exc_info.value)


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

def test_setting_dict_set_invalid_value():
    setting_dict = SettingDict({
        'test': ('email', 'my@email.com')
        })
    with pytest.raises(AppxfSettingConversionError):
        setting_dict['test'] = 'fail'
    # error message checks are in scope of setting implementation

def test_setting_dict_overwriting_by_setting_object():
    setting_dict = SettingDict({
        'test': ('bool', False)})
    assert setting_dict['test'] == False
    assert type(setting_dict.value['test']) == SettingBool
    # overwrite by Email
    setting_dict['test'] = Setting.new('string', 'some')
    assert setting_dict['test'] == 'some'
    assert type(setting_dict.value['test']) == SettingString

def test_setting_dict_overwriting_by_setting_class():
    setting_dict = SettingDict({
        'test': ('bool', False)})
    assert setting_dict['test'] == False
    assert type(setting_dict.value['test']) == SettingBool
    # overwrite by Email
    setting_dict['test'] = SettingInt
    assert setting_dict['test'] == SettingInt.get_default()
    assert type(setting_dict.value['test']) == SettingInt

def test_setting_dict_overwriting_by_tuple():
    setting_dict = SettingDict({
        'test': ('bool', False)})
    assert setting_dict['test'] == False
    assert type(setting_dict.value['test']) == SettingBool
    # overwrite by Email
    setting_dict['test'] = ('string', 'some')
    assert setting_dict['test'] == 'some'
    assert type(setting_dict.value['test']) == SettingString

def test_setting_dict_keeps_setting_object():
    setting_dict = SettingDict({
        'test': (str, 'init')})
    assert setting_dict['test'] == 'init'
    init_object = setting_dict.value['test']
    # set new value
    setting_dict['test'] = 'new'
    assert setting_dict['test'] == 'new'
    new_object = setting_dict.value['test']
    assert new_object is init_object
    # set overwriting variant
    setting_dict['test'] = (str, 'overwriting')
    assert setting_dict['test'] == 'overwriting'
    new_object = setting_dict.value['test']
    assert new_object is not init_object

# setting nonexisting is now expected to work:
#def test_setting_dict_set_nonexisting():
#    setting_dict = SettingDict()
#    with pytest.raises(AppxfSettingError) as exc_info:
#        setting_dict['test'] = 'test'
#    assert 'Key test does not exist' in str(exc_info.value)

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
