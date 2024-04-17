
import pytest

from kiss_cf.property import KissPropertyDict, KissProperty
from kiss_cf.property import KissPropertyConversionError, KissPropertyError
from kiss_cf.property import KissString, KissInt, KissFloat, KissBool

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
    # KissProperty class based input
    ('PC1', KissString,                                 'string',   '',             ''),
    ('PC2', KissInt,                                    'int',      0,              '0'),
    ('PC3', KissFloat,                                  'float',    0.0,            '0.0'),
    ('PC4', KissBool,                                   'bool',     False,          '0'),
    # KissProperty object based input
    ('p1',  KissProperty.new(str, 'test'),              'string',   'test',         'test'),
    ('p2',  KissProperty.new(int,42),                   'int',      42,             '42'),
    ('p3',  KissProperty.new(float,1.123),              'float',    1.123,          '1.123'),
    ('p4',  KissProperty.new(bool,True),                'bool',     True,           '1'),
    # Tuple based input
    ('T1',   ('pass', '123abc'),                        'pass',     '123abc',       '123abc'),
    ('T2',   ('email', 'some@one.com'),                 'email',    '',             ''),
    ('T3',   ('integer',),                              'int',      0,              '0'),
]

def _get_prop_reference(t):
    if isinstance(t[1], tuple):
        # tuple based init with type+value
        if len(t[1]) == 2:
            return KissProperty.new(t[2], value=t[1][1])
        # tuple based init with type, only
        else:
            return KissProperty.new(t[2])
    if isinstance(t[1], type):
        # type based input
        return KissProperty.new(t[2])
    if isinstance(t[1], KissProperty):
        # Direct KissProperty based input
        return t[1]
    return KissProperty.new(t[2], value=t[1])

def verify_property_dict(prop_dict: KissPropertyDict, t_list: list[tuple]):
    for t in t_list:
        prop_ref = _get_prop_reference(t)
        assert prop_dict[t[0]] == prop_ref.value
        assert type(prop_dict.get_property(t[0])) == type(prop_ref)
        assert prop_dict.get_property(t[0]).value == prop_ref.value
        assert prop_dict.get_property(t[0]).to_string() == prop_ref.to_string()

# #############/
# Init Variants
# ////////////

def test_property_dict_init_and_fill():
    prop_dict = KissPropertyDict()
    for t in init_values:
        prop_dict[t[0]] = t[1]
    verify_property_dict(prop_dict, init_values)

def test_property_dict_init_by_dict():
    # build dict:
    dict_input = {t[0]: t[1]
                  for t in init_values}
    prop_dict = KissPropertyDict(dict_input)
    verify_property_dict(prop_dict, init_values)

def test_property_dict_init_key_value_call():
    # Like dict, but resolving the dict via **
    dict_input = {t[0]: t[1]
                  for t in init_values}
    prop_dict = KissPropertyDict(**dict_input)
    verify_property_dict(prop_dict, init_values)

def test_property_dict_fails_init():
    with pytest.raises(KissPropertyConversionError):
        KissPropertyDict({
        'test': ('email', 'fail')
        })

def test_property_dict_tuple_init_fails1():
    with pytest.raises(KissPropertyError) as exc_info:
        KissPropertyDict({'test': tuple()})
    assert 'KissPropertyDict' in str(exc_info.value)
    assert 'The input tuple had length 0' in str(exc_info.value)

def test_property_dict_tuple_init_fails2():
    with pytest.raises(KissPropertyError) as exc_info:
        KissPropertyDict({'test': (1,2,3,4)})
    assert 'KissPropertyDict' in str(exc_info.value)
    assert 'The input tuple had length 4' in str(exc_info.value)

# ####################/
# Values Manipulations
# ///////////////////

def test_property_dict_set_valid_value():
    prop_dict = KissPropertyDict({
        'test': ('email', 'my@email.com')
        })
    prop_dict['test'] = 'new@email.com'
    assert prop_dict['test'] == 'new@email.com'
    assert prop_dict.get_property('test').value == 'new@email.com'

def test_property_dict_set_invalid_value():
    prop_dict = KissPropertyDict({
        'test': ('email', 'my@email.com')
        })
    with pytest.raises(KissPropertyConversionError):
        prop_dict['test'] = 'fail'

def test_property_dict_set_invalid_after_delete():
    # test case derived from test_property_dict_set_invalid_value
    prop_dict = KissPropertyDict({
        'test': ('email', 'my@email.com')
        })
    del prop_dict['test']
    prop_dict['test'] = 'fail'
    assert prop_dict['test'] == 'fail'
    assert prop_dict.get_property('test').value == 'fail'

def test_property_dict_delete_non_existing():
    prop_dict = KissPropertyDict()
    del prop_dict['test']

# #################/
# Storable Behavior
# ////////////////


def test_property_dict_store_load_cycle():
    # we use an integer here since it differs in "input" and stored "value".
    # And we use an arbitrary string (email) to be a bit more verbose.
    prop_dict = KissPropertyDict({'entry': ('email',), 'input_check': (int,)})
    storage = StorageMasterMock().get_storage('test')
    prop_dict.set_storage(storage, on_load_unknown='ignore', store_property_config=False)
    prop_dict['entry'] = 'before@store.com'
    prop_dict['input_check'] = '1'

    prop_dict.store()
    prop_dict['entry'] = 'after@store.com'
    prop_dict['input_check'] = '2'
    assert prop_dict['entry'] == 'after@store.com'
    assert prop_dict.get_property('entry').value == 'after@store.com'
    assert prop_dict.get_property('entry').input == 'after@store.com'
    assert prop_dict['input_check'] == 2
    assert prop_dict.get_property('input_check').value == 2
    assert prop_dict.get_property('input_check').input == '2'

    prop_dict_reload = KissPropertyDict({'entry': ('email',), 'input_check': (int,)})
    prop_dict_reload.set_storage(storage)
    prop_dict_reload.load()
    assert prop_dict_reload['entry'] == 'before@store.com'
    assert prop_dict_reload.get_property('entry').value == 'before@store.com'
    assert prop_dict_reload.get_property('entry').input == 'before@store.com'
    assert prop_dict_reload['input_check'] == 1
    assert prop_dict_reload.get_property('input_check').value == 1
    assert prop_dict_reload.get_property('input_check').input == '1'


# TODO: data element loaded that is not in config anymore
# TODO: data element missing from load >> nothing ??
# TODO: reload "only data"
# TODO: reloas "data + KissProperty".. ..but KissProperty are not storable