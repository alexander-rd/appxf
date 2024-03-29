
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

def test_gui_option_properties_string_conversion():
    option = KissOption(type='str')
    value = option.to_value('hello')
    assert value == 'hello'
    assert option.to_string('vault') == 'vault'
    assert option.to_value('anything') == 'anything'

def test_gui_option_properties_bool_conversion():
    option = KissOption(type='bool')
    value = option.to_value('yes')
    assert value
    assert option.to_string(False) == '0'
    assert option.to_string(True) == '1'
    assert option.to_value('true')
    assert option.to_value('1')
    assert not option.to_value('no')
    assert not option.to_value('False')
    assert not option.to_value('0')

def test_gui_option_properties_int_conversion():
    option = KissOption(type='int')
    assert option.validate('42')
    value = option.to_value('42')
    assert value
    assert option.to_string(42) == '42'
    assert option.to_string(0) == '0'
    assert option.to_string(-1234567890) == '-1234567890'
    assert option.to_value('123') == 123
    assert option.to_value('0') == 0
    assert option.to_value('-1234567890') == -1234567890

def test_gui_option_properties_wron_conversions():
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
