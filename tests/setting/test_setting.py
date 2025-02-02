
import pytest

from kiss_cf.setting import Setting, SettingExtension
from kiss_cf.setting import AppxfSettingError, AppxfSettingConversionError
from kiss_cf.setting import SettingString, SettingEmail, SettingPassword
from kiss_cf.setting import SettingBool, SettingInt, SettingFloat

from kiss_cf.setting import setting as setting_module
# pylint: disable=protected-access
# pylint: disable=missing-function-docstring

# TODO: test min_length property setting being funcitonal for passwords

class DummyClassErrorOnStrCreation():
    def __str__(self):
        raise TypeError('some failure')

@pytest.mark.parametrize(
    'appxf_class', setting_module._SettingMeta.implementations)
def test_setting_init(appxf_class):
    # skip any AppxfExtension
    if issubclass(appxf_class, SettingExtension):
        return
    setting = appxf_class(name='test')
    assert setting.options.name == 'test'
    assert setting.options.mutable
    #if isinstance(setting, AppxfPassword):
    #    assert setting.masked
    #else:
    #    assert not setting.masked

param_wrong_init = [
    # Type      Value
    (str,       DummyClassErrorOnStrCreation()),
    (bool,      'value'),
    (int,       'int'),
    (float,     'abc')
    ]
@pytest.mark.parametrize(
    'setting_type, value', param_wrong_init)
def test_setting_wrong_init(setting_type, value):
    # Utilizing AppxfSetting.new() still uses the corresponding __init__
    with pytest.raises(AppxfSettingConversionError) as exc_info:
        Setting.new(setting_type, value)
    # general error statement
    assert 'Cannot set' in str(exc_info.value)
    # value type should be included:
    assert str(type(value)) in str(exc_info.value)
    print(exc_info.value)
    # TODO: check more error message content?

def verify_conversion_error(exc_info, setting: Setting, input: object):
    # General formulation
    assert 'Cannot set' in str(exc_info.value)
    # Input value
    assert str(input) in str(exc_info.value)
    # Input type:
    assert str(type(input)) in str(exc_info.value)
    # Setting class name
    assert setting.__class__.__name__ in str(exc_info.value)

param_conversion = [
    # Type      Input           Valid   Value           String
    ('str',     'hello',        True,   'hello',        'hello'),
    (str,       '!"§$%&/()=?\n',True,   '!"§$%&/()=?\n','!"§$%&/()=?\n'),
    (str,       42,             False,  '',             ''),
    ('string',  '42',           True,   '42',           '42'),
    ('email',   'some@thing.it',True,   'some@thing.it','some@thing.it'),
    ('Email',   'something.it', False,  '',             ''),
    ('email',   '@some.it',     False,  '',             ''),
    ('email',   42,             False,  '',             ''),
    ('pass',    'long_enough',  True,   'long_enough',  'long_enough'),
    ('password','short',        False,  '',              'short'),

    # Type      Input           Valid   Value           String
    ('bool',    'yes',          True,   True,           '1'),
    ('boolean', True,           True,   True,           '1'),
    (bool,      False,          True,   False,          '0'),
    ('bool',    'true',         True,   True,           '1'),
    ('bool',    'False',        True,   False,          '0'),
    ('bool',    '1',            True,   True,           '1'),
    ('bool',    'no',           True,   False,          '0'),
    (bool,      'invlaid',      False,  False,          '0'),

    # Type      Input           Valid   Value           String
    ('int',     42,             True,   42,             '42'),
    (int,       0,              True,   0,              '0'),
    ('integer', -1234567890,    True,   -1234567890,    '-1234567890'),
    ('int',     '123',          True,   123,            '123'),
    ('int',     '0',            True,   0,              '0'),
    ('int',     '-1234567890',  True,   -1234567890,    '-1234567890'),
    (int,       True,           True,   1,              '1'),
    (int,       False,          True,   0,              '0'),
    (int,       'a',            False,  0,              '0'),
    (int,       b'',           False,  0,              '0'),

    # Type      Input           Valid   Value           String
    ('float',   12345,          True,   12345,          '12345.0'),
    (float,     1.1234567890,   True,   1.1234567890,   '1.123456789'),
    (float,     False,          True,   0,              '0.0'),
    (float,     False,          True,   0,              '0.0'),
    (float,     True,           True,   1,              '1.0'),
    (float,     'True',         False,  0,              '0.0'),
    (float,     'a',            False,  0,              '0.0'),
    (float,     b'',           False,  0,              '0.0'),
]
@pytest.mark.parametrize(
    'setting_type, input, valid, value, string', param_conversion)
def test_setting_conversions(setting_type, input, valid, value, string):
    setting = Setting.new(setting_type)
    message = (
        f'Failed for type [{setting_type}] with input [{input}] '
        f'(expected valid: {valid}) '
        f'and resulting in value [{value}] and string [{string}]')
    assert setting.validate(input) == valid, 'Validity not as expected. ' + message
    if not valid:
        with pytest.raises(AppxfSettingConversionError) as exc_info:
            setting.value = input
        verify_conversion_error(exc_info, setting, input)
        # Value and input still accoring to default:
        setting_ref = Setting.new(setting_type)
        assert setting.value == setting_ref.value
        assert setting.input == setting_ref.input
        return
    setting.value = input
    assert setting.input == input, 'Input after setting does not match. ' + message
    assert setting.value == value, 'Value after setting does not match. ' + message
    assert setting.to_string() == string, 'String after setting does not match. ' + message

@pytest.mark.parametrize(
    'setting_type, input, valid, value, string', param_conversion)
def test_setting_init_with_value(setting_type, input, valid, value, string):
    message = (
        f'Failed for type [{setting_type}] with input [{input}] '
        f'(expected valid: {valid}) '
        f'and resulting in value [{value}] and string [{string}]')
    if not valid:
        setting_ref = Setting.new(setting_type)
        with pytest.raises(AppxfSettingConversionError) as exc_info:
            setting = Setting.new(setting_type, value=input)
        verify_conversion_error(exc_info, setting_ref, input)
        return
    else:
        setting = Setting.new(setting_type, value=input)
        assert setting.input == input, 'Input after setting does not match. ' + message
        assert setting.value == value, 'Value after setting does not match. ' + message
        assert setting.to_string() == string, 'String after setting does not match. ' + message


@pytest.mark.parametrize(
    'setting_type, input, valid, value, string', param_conversion)
def test_setting_init_with_value_pre_lookup(setting_type, input, valid, value, string):
    message = (
        f'Failed for type [{setting_type}] with input [{input}] '
        f'(expected valid: {valid}) '
        f'and resulting in value [{value}] and string [{string}]')
    setting_type = setting_module._SettingMeta.type_map[setting_type]
    if not valid:
        setting_ref = Setting.new(setting_type)
        with pytest.raises(AppxfSettingConversionError) as exc_info:
            setting = Setting.new(setting_type, value=input)
        verify_conversion_error(exc_info, setting_ref, input)
        return
    else:
        setting = Setting.new(setting_type, value=input)
        assert setting.input == input, 'Input after setting does not match. ' + message
        assert setting.value == value, 'Value after setting does not match. ' + message
        assert setting.to_string() == string, 'String after setting does not match. ' + message

def test_setting_self_test():
    # conversions covering all registered types:
    tested_types = set([t[0] for t in param_conversion])
    uncovered_type = [setting_type for setting_type in setting_module._SettingMeta.type_map.keys()
                      if setting_type not in tested_types]
    assert not uncovered_type, (
        f'Following registered types are not covered in '
        f'test_setting_conversions: {uncovered_type}')
    # valid conversions covering all implementations
    implementation_list = [setting_type for setting_type in setting_module._SettingMeta.implementations
                           if not issubclass(setting_type, SettingExtension)]
    uncovered_valid = (
        set(implementation_list) -
        set([setting_module._SettingMeta.type_map[t[0]]
             for t in param_conversion
             if t[2]
        ]))
    uncovered_invalid = (
        set(implementation_list) -
        set([setting_module._SettingMeta.type_map[t[0]]
             for t in param_conversion
             if not t[2]
        ]))
    # Invalid SettingString is covered differently
    uncovered_invalid -= set(['SettingString'])
    assert not uncovered_valid, (
        f'Following Setting implementations do not have a valid test '
        f'case in test_setting_conversions: {uncovered_valid}')
    assert not uncovered_invalid, (
        f'Following Setting implementations do not have an invalid test '
        f'case in test_setting_conversions: {uncovered_invalid}')

def test_setting_mutable():
    setting = Setting.new(str)
    setting.options.mutable = False
    with pytest.raises(AppxfSettingError) as exc_info:
        setting.value = 'new'
    assert 'is set to be not mutable' in str(exc_info.value)

# #######################################/
# # AppxfSetting base class functionality
# #/////////////////////////////////////

def test_setting_register_type_twice():
    with pytest.raises(AppxfSettingError) as exc_info:
        class DummyAppxfString(Setting):
            @classmethod
            def get_supported_types(cls) -> list[type | str]:
                return ['email']
            @classmethod
            def get_default(cls) -> str:
                return ''
    assert 'is already registered' in str(exc_info.value)
    assert 'DummyAppxfString' in str(exc_info.value)
    assert 'SettingEmail' in str(exc_info.value)

def test_setting_register_class_twice():
    with pytest.raises(AppxfSettingError) as exc_info:
        class SettingEmail(Setting):
            @classmethod
            def get_supported_types(cls) -> list[type | str]:
                return ['moreEmail']
            @classmethod
            def get_default(cls) -> str:
                return ''
    assert 'is already registered' in str(exc_info.value)
    assert 'SettingEmail' in str(exc_info.value)

def test_setting_register_no_supported_type():
    with pytest.raises(AppxfSettingError) as exc_info:
        class DummyAppxfString(Setting):
            @classmethod
            def get_supported_types(cls) -> list[type | str]:
                return []
            @classmethod
            def get_default(cls) -> str:
                return ''
    assert 'does not return any supported type' in str(exc_info.value)

def test_setting_register_incopmlete_class():
    with pytest.raises(AppxfSettingError) as exc_info:
        class DummyAppxfString(Setting):
            @classmethod
            def get_supported_types(cls) -> list[type | str]:
                return ['myEmail']
    # The class above has get_default_value() missing
    print(f'{exc_info.value}')

def test_setting_init_with_base_class():
    with pytest.raises(AppxfSettingError) as exc_info:
        Setting.new(Setting)
    assert 'You need to provide a fully implemented class' in str(exc_info.value)
    assert 'Setting is not' in str(exc_info.value)

def test_setting_init_with_unknown_type():
    with pytest.raises(AppxfSettingError) as exc_info:
        Setting.new('non_existing_type')
    assert 'Setting type [non_existing_type] is unknown.' in str(exc_info.value)
