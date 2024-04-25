
import pytest

from kiss_cf.setting import SettingDict, AppxfSetting
from kiss_cf.setting import AppxfSettingConversionError, AppxfSettingError
from kiss_cf.setting import AppxfString, AppxfInt, AppxfFloat, AppxfBool

from kiss_cf.storage import StorageMasterMock

sample_input = {
    'string': 'test',
    'int': 42,
    'float': 1.1234,
    'bool': True,
    }

init_values = [
    # Key   Value                                       #Type       Value_Out       String_Out
    # Value based input
    ('v1',  'test',                                     'string',   'test',         'test'),
    ('v2',  42,                                         'int',      42,             '42'),
    ('v3',  1.123,                                      'float',    1.123,          '1.123'),
    ('v4',  True,                                       'bool',     True,           '1'),
    # Type based input (resulting in default values)
    ('t1',  str,                                        'string',   '',             ''),
    ('t2',  int,                                        'int',      0,              '0'),
    ('t3',  float,                                      'float',    0.0,            '0.0'),
    ('t4',  bool,                                       'bool',     False,          '0'),
    # AppxfSetting class based input
    ('PC1', AppxfString,                                 'string',   '',             ''),
    ('PC2', AppxfInt,                                    'int',      0,              '0'),
    ('PC3', AppxfFloat,                                  'float',    0.0,            '0.0'),
    ('PC4', AppxfBool,                                   'bool',     False,          '0'),
    # AppxfSetting object based input
    ('p1',  AppxfSetting.new(str, 'test'),              'string',   'test',         'test'),
    ('p2',  AppxfSetting.new(int,42),                   'int',      42,             '42'),
    ('p3',  AppxfSetting.new(float,1.123),              'float',    1.123,          '1.123'),
    ('p4',  AppxfSetting.new(bool,True),                'bool',     True,           '1'),
    # Tuple based input
    ('T1',   ('pass', '123abc'),                        'pass',     '123abc',       '123abc'),
    ('T2',   ('email', 'some@one.com'),                 'email',    '',             ''),
    ('T3',   ('integer',),                              'int',      0,              '0'),
]

def _get_setting_reference(t):
    if isinstance(t[1], tuple):
        # tuple based init with type+value
        if len(t[1]) == 2:
            return AppxfSetting.new(t[2], value=t[1][1])
        # tuple based init with type, only
        else:
            return AppxfSetting.new(t[2])
    if isinstance(t[1], type):
        # type based input
        return AppxfSetting.new(t[2])
    if isinstance(t[1], AppxfSetting):
        # Direct AppxfSetting based input
        return t[1]
    return AppxfSetting.new(t[2], value=t[1])

def verify_setting_dict(setting_dict: SettingDict, t_list: list[tuple]):
    for t in t_list:
        setting_ref = _get_setting_reference(t)
        assert setting_dict[t[0]] == setting_ref.value
        assert type(setting_dict.get_setting(t[0])) == type(setting_ref)
        assert setting_dict.get_setting(t[0]).value == setting_ref.value
        assert setting_dict.get_setting(t[0]).to_string() == setting_ref.to_string()

# #############/
# Init Variants
# ////////////

# manual filling
def test_setting_dict_init_and_fill():
    setting_dict = SettingDict()
    for t in init_values:
        setting_dict.add({t[0]: t[1]})
    verify_setting_dict(setting_dict, init_values)

# init by dict
def test_setting_dict_init_by_dict():
    # build dict:
    dict_input = {t[0]: t[1]
                  for t in init_values}
    setting_dict = SettingDict(dict_input)
    verify_setting_dict(setting_dict, init_values)

# key value pairs
def test_setting_dict_init_key_value_call():
    # Like dict, but resolving the dict via **
    dict_input = {t[0]: t[1]
                  for t in init_values}
    setting_dict = SettingDict(**dict_input)
    verify_setting_dict(setting_dict, init_values)

# init by list
def test_setting_dict_init_by_list_list():
    # Like dict, but resolving the dict via **
    dict_input = [(t[0], t[1])
                  for t in init_values]
    setting_dict = SettingDict(dict_input)
    verify_setting_dict(setting_dict, init_values)

def test_setting_dict_init_by_list_fail1():
    # iterable without iterable subelement
    with pytest.raises(AppxfSettingError) as exc_info:
        SettingDict([42, 12])
    assert 'No second level iterable.' in str(exc_info.value)
    assert 'SettingDict can be initialized by iterables of iterables where the inner iterables' in str(exc_info.value)

def test_setting_dict_init_by_list_fail2():
    # iterable with a iterable subelement that does not contain key+value
    with pytest.raises(AppxfSettingError) as exc_info:
        SettingDict([('key', 12), ('key2',)])
    assert 'No key and/or value provided.' in str(exc_info.value)

# general unknown init type
def test_setting_dict_init_by_list_fail2():
    # iterable with a iterable subelement that does not contain key+value
    with pytest.raises(AppxfSettingError) as exc_info:
        SettingDict(data = 42)
    assert f'Invalid initialization input of type {type(42)}.' in str(exc_info.value)

# inconsistent type/value combinations
def test_setting_dict_fails_init():
    with pytest.raises(AppxfSettingConversionError):
        SettingDict({
        'test': ('email', 'fail')
        })

def test_setting_dict_tuple_init_fails1():
    with pytest.raises(AppxfSettingError) as exc_info:
        SettingDict({'test': tuple()})
    assert 'SettingDict' in str(exc_info.value)
    assert 'The input tuple had length 0' in str(exc_info.value)

def test_setting_dict_tuple_init_fails2():
    with pytest.raises(AppxfSettingError) as exc_info:
        SettingDict({'test': (1,2,3,4)})
    assert 'SettingDict' in str(exc_info.value)
    assert 'The input tuple had length 4' in str(exc_info.value)

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

def test_setting_dict_set_nonexisting():
    setting_dict = SettingDict()
    with pytest.raises(AppxfSettingError) as exc_info:
        setting_dict['test'] = 'test'
    assert 'Key test does not exist' in str(exc_info.value)

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
    setting_dict.add(test='fail')
    assert setting_dict['test'] == 'fail'
    assert setting_dict.get_setting('test').value == 'fail'

def test_setting_dict_delete_non_existing():
    setting_dict = SettingDict()
    with pytest.raises(KeyError):
        del setting_dict['test']

# REQ: When changing the underlying AppxfSetting directly, the value returned by
# SettingDict must appear updated accordingly.
#
# Origin: The initial implementation used UserDict with a duplicate storage
# for values in the UserDict.data. This implementation did not satisfy the
# requirement.
#
# Rationale: The GUI implementation has a GUI for just a AppxfSetting on top of
# which the GUI for SettingDict is build.
def test_setting_dict_update_on_setting():
    setting_dict = SettingDict()
    setting_dict.add({'test': (str, 'seomething')})
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
    storage = StorageMasterMock().get_storage('test')
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
    storage = StorageMasterMock().get_storage('test')
    setting_dict = SettingDict(
        entry=('email',),
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
