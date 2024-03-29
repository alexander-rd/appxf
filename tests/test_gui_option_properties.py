
import pytest

from kiss_cf.gui import KissOption, KissOptionPropertyError

def test_gui_option_properties_self_test():
    ''' Rember to cover all interfaces when adding types. '''
    covered = ['str', 'email', 'Email',
               'bool', 'boolean',
               'int']
    for this_type in KissOption.type_list:
        assert this_type in covered, (
            f'Seems you added {this_type} to OptionProperties. Great! '
            f'Please do not forget to cover the new type in all interfaces '
            f'(and add unit tests).')

def test_gui_option_properties_init():
    option = KissOption()
    assert option.configurable
    assert option.type == 'str'
    assert str(option) == 'type: str, configurable'

def test_gui_option_properties_wrong_init():
    with pytest.raises(KissOptionPropertyError) as exc_info:
        option = KissOption(type='nothing')
    # requested type should be in error message:
    assert 'nothing' in str(exc_info.value)
    # allowed types should be in error message
    for this_type in KissOption.type_list:
        assert this_type in str(exc_info.value)

def test_gui_option_properties_wrong_set():
    option = KissOption()
    option.set(type='boolean')
    assert option.type == 'boolean'
    option.set(configurable=False)
    assert not option.configurable

def test_gui_option_properties_wrong_set_attribute():
    option = KissOption()
    with pytest.raises(KissOptionPropertyError) as exc_info:
        option.set(nothing=42)
    assert 'nothing' in str(exc_info.value)
    for setting in KissOption.setting_list:
        assert setting in str(exc_info.value)
    assert 'type' in str(exc_info.value)
    assert 'configurable' in str(exc_info.value)


conversion_param = [
    # Type      Input           Valid   Value           String
    ('str',    'hello',         True,   'hello',        'hello'),
    ('str',    '!"§$%&/()=?\n', True,   '!"§$%&/()=?\n','!"§$%&/()=?\n'),
    ('bool',    'yes',          True,   True,           'yes'),
    ('bool',    True,           True,   True,           '1'),
    ('bool',    False,          True,   False,          '0'),
    ('bool',    'true',         True,   True,           'true'),
    ('bool',    'False',        True,   False,          'False'),
    ('bool',    '1',            True,   True,           '1'),
    ('bool',    'no',           True,   False,          'no'),
    ('int',     42,             True,   42,             '42'),
    ('int',     0,              True,   0,              '0'),
    ('int',     -1234567890,    True,   -1234567890,    '-1234567890'),
    ('int',     '123',          True,   123,            '123'),
    ('int',     '0',            True,   0,              '0'),
    ('int',     '-1234567890',  True,   -1234567890,    '-1234567890'),
]
@pytest.mark.parametrize(
    'option_type, input, valid, value, string', conversion_param)
def test_gui_option_conversion(option_type, input, valid, value, string):
    option = KissOption(type=option_type)
    # if value is None:
    #     with pytest.raises(KissOptionPropertyError) as exec_info:
    assert option.validate(input) == valid
    if not valid:
        # TODO: add expectations on raised errors for conversion of invalid
        # values.
        return
    assert option.to_value(input) == value
    assert option.to_string(input) == string


def test_gui_option_properties_wrong_conversions():
    option = KissOption(type='Email')
    with pytest.raises(KissOptionPropertyError) as exc_info:
        option.to_value('no_email')
    assert 'Cannot convert' in str(exc_info)
    assert 'no_email' in str(exc_info)
    assert 'Email' in str(exc_info)

    option.set(type='boolean')
    with pytest.raises(KissOptionPropertyError) as exc_info:
        option.to_value('2')
    assert 'Cannot convert' in str(exc_info)
    assert '2' in str(exc_info)
    assert 'boolean' in str(exc_info)

    option.set(type='int')
    with pytest.raises(KissOptionPropertyError) as exc_info:
        option.to_value('12.5')
    assert 'Cannot convert' in str(exc_info)
    assert '12.5' in str(exc_info)
    assert 'int' in str(exc_info)

    option.set(type='str')
    with pytest.raises(KissOptionPropertyError) as exc_info:
        option.to_string({'some': 'value'})
    assert 'does not match configured type' in str(exc_info)
    assert 'dict' in str(exc_info)
    assert 'str' in str(exc_info)
