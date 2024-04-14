
import pytest

from kiss_cf.property import KissProperty, KissPropertyError, KissPropertyConversionError
from kiss_cf.property import KissString, KissEmail, KissPassword
from kiss_cf.property import KissBool, KissInt, KissFloat

from kiss_cf.property import property
# pylint: disable=protected-access
# pylint: disable=missing-function-docstring

# TODO: test min_length property setting being funcitonal for passwords

class DummyClassErrorOnStrCreation():
    def __str__(self):
        raise TypeError('some failure')

@pytest.mark.parametrize(
    'kiss_class', property._implementations)
def test_property_init(kiss_class):
    prop = kiss_class(name='test')
    assert prop.name == 'test'
    assert prop.mutable
    assert prop.default_visibility
    if isinstance(prop, KissPassword):
        assert prop.masked
    else:
        assert not prop.masked

param_wrong_init = [
    # Type      Value
    (str,       DummyClassErrorOnStrCreation()),
    (bool,      42),
    (int,       'int'),
    (float,     'abc')
    ]
@pytest.mark.parametrize(
    'prop_type, value', param_wrong_init)
def test_property_wrong_init(prop_type, value):
    # Utiliting KissPoperty.new() still uses the corresponding __init__
    with pytest.raises(KissPropertyConversionError) as exc_info:
        KissProperty.new(prop_type, value)
    # general error statement
    assert 'Cannot set' in str(exc_info.value)
    # value type should be included:
    assert str(type(value)) in str(exc_info.value)
    print(exc_info.value)
    # TODO: check more error message content?

#def test_gui_option_properties_wrong_set_attribute():
#    option = KissOption()
#    with pytest.raises(KissOptionPropertyError) as exc_info:
#        option.set(nothing=42)
#    assert 'nothing' in str(exc_info.value)
#    for setting in KissOption.setting_list:
#        assert setting in str(exc_info.value)
#    assert 'type' in str(exc_info.value)
#    assert 'configurable' in str(exc_info.value)

def verify_conversion_error(exc_info, prop: KissProperty, input: object):
    # General formulation
    assert 'Cannot set' in str(exc_info.value)
    # Input value
    assert str(input) in str(exc_info.value)
    # Input type:
    assert str(type(input)) in str(exc_info.value)
    # Properties class name
    assert prop.__class__.__name__ in str(exc_info.value)

param_conversion = [
    # Type      Input           Valid   Value           String
    ('str',     'hello',        True,   'hello',        'hello'),
    (str,       '!"§$%&/()=?\n',True,   '!"§$%&/()=?\n','!"§$%&/()=?\n'),
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
    'prop_type, input, valid, value, string', param_conversion)
def test_property_conversions(prop_type, input, valid, value, string):
    prop = KissProperty.new(prop_type)
    # if value is None:
    #     with pytest.raises(KissOptionPropertyError) as exec_info:
    message = (
        f'Failed for type [{prop_type}] with input [{input}] '
        f'(expected valid: {valid}) '
        f'and resulting in value [{value}] and string [{string}]')
    assert prop.validate(input) == valid, 'Validity not as expected. ' + message
    if not valid:
        with pytest.raises(KissPropertyConversionError) as exc_info:
            prop.value = input
        verify_conversion_error(exc_info, prop, input)
        # Value and input still accoring to default:
        prop_ref = KissProperty.new(prop_type)
        assert prop.value == prop_ref.value
        assert prop.input == prop_ref.input
        return
    prop.value = input
    assert prop.input == input, 'Input after setting does not match. ' + message
    assert prop.value == value, 'Value after setting does not match. ' + message
    assert prop.to_string() == string, 'String after setting does not match. ' + message

@pytest.mark.parametrize(
    'prop_type, input, valid, value, string', param_conversion)
def test_property_init_with_value(prop_type, input, valid, value, string):
    message = (
        f'Failed for type [{prop_type}] with input [{input}] '
        f'(expected valid: {valid}) '
        f'and resulting in value [{value}] and string [{string}]')
    if not valid:
        prop_ref = KissProperty.new(prop_type)
        with pytest.raises(KissPropertyConversionError) as exc_info:
            prop = KissProperty.new(prop_type, value=input)
        verify_conversion_error(exc_info, prop_ref, input)
        return
    else:
        prop = KissProperty.new(prop_type, value=input)
        assert prop.input == input, 'Input after setting does not match. ' + message
        assert prop.value == value, 'Value after setting does not match. ' + message
        assert prop.to_string() == string, 'String after setting does not match. ' + message


@pytest.mark.parametrize(
    'prop_type, input, valid, value, string', param_conversion)
def test_property_init_with_value_pre_lookup(prop_type, input, valid, value, string):
    message = (
        f'Failed for type [{prop_type}] with input [{input}] '
        f'(expected valid: {valid}) '
        f'and resulting in value [{value}] and string [{string}]')
    prop_type = property._type_map[prop_type]
    if not valid:
        prop_ref = KissProperty.new(prop_type)
        with pytest.raises(KissPropertyConversionError) as exc_info:
            prop = KissProperty.new(prop_type, value=input)
        verify_conversion_error(exc_info, prop_ref, input)
        return
    else:
        prop = KissProperty.new(prop_type, value=input)
        assert prop.input == input, 'Input after setting does not match. ' + message
        assert prop.value == value, 'Value after setting does not match. ' + message
        assert prop.to_string() == string, 'String after setting does not match. ' + message

def test_property_self_test():
    # conversions covering all registered types:
    uncovered_type = set(property._type_map.keys()) - set([t[0] for t in param_conversion])
    assert not uncovered_type, (
        f'Following registered types are not covered in '
        f'test_property_conversions: {uncovered_type}')
    # valid conversions covering all implementations
    uncovered_valid = (
        set(property._implementation_names) -
        set([property._type_map[t[0]].__name__
             for t in param_conversion
             if t[2]
        ]))
    uncovered_invalid = (
        set(property._implementation_names) -
        set([property._type_map[t[0]].__name__
             for t in param_conversion
             if not t[2]
        ]))
    # Invalid KissString is covered differently
    uncovered_invalid -= set(['KissString'])
    assert not uncovered_valid, (
        f'Following KissProperty implementations do not have a valid test '
        f'case in test_property_conversions: {uncovered_valid}')
    assert not uncovered_invalid, (
        f'Following KissProperty implementations do not have an invalid test '
        f'case in test_property_conversions: {uncovered_invalid}')

def test_property_mutable():
    prop = KissProperty.new(str)
    prop.mutable = False
    with pytest.raises(KissPropertyError) as exc_info:
        prop.value = 'new'
    assert 'is set to be not mutable' in str(exc_info.value)

# #######################################/
# # KissProperty base class functionality
# #/////////////////////////////////////

def test_property_register_type_twice():
    with pytest.raises(KissPropertyError) as exc_info:
        class DummyKissString(KissProperty):
            @classmethod
            def get_supported_types(cls) -> list[type | str]:
                return ['email']
    assert 'is already registered' in str(exc_info.value)
    assert 'DummyKissString' in str(exc_info.value)
    assert 'KissEmail' in str(exc_info.value)

def test_property_register_class_twice():
    with pytest.raises(KissPropertyError) as exc_info:
        class KissEmail(KissProperty):
            @classmethod
            def get_supported_types(cls) -> list[type | str]:
                return ['moreEmail']
    assert 'is already registered' in str(exc_info.value)
    assert 'KissEmail' in str(exc_info.value)

def test_property_register_no_supported_type():
    with pytest.raises(KissPropertyError) as exc_info:
        class DummyKissString(KissProperty):
            @classmethod
            def get_supported_types(cls) -> list[type | str]:
                return []
    assert 'does not return any supported type' in str(exc_info.value)

def test_property_register_incopmlete_class():
    with pytest.raises(KissPropertyError) as exc_info:
        class DummyKissString(KissProperty):
            @classmethod
            def get_supported_types(cls) -> list[type | str]:
                return ['myEmail']
    # The class above has get_default_value() missing
    print(f'{exc_info.value}')

def test_property_init_with_base_class():
    with pytest.raises(KissPropertyError) as exc_info:
        KissProperty.new(KissProperty)
    assert 'You need to provide a derived, fully implemented class' in str(exc_info.value)
    assert 'not KissProperty directly' in str(exc_info.value)

def test_property_init_with_unknown_type():
    with pytest.raises(KissPropertyError) as exc_info:
        KissProperty.new('non_existing_type')
    assert 'Property type [non_existing_type] is unknown.' in str(exc_info.value)
