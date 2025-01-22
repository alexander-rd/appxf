''' options module with Options object
'''
from kiss_cf import AppxfOptions
from dataclasses import dataclass, field

import pytest

@dataclass
class DefaultTestOptions(AppxfOptions):
    test_int: int = 0
    test_string: str = ''
    test_list: list[str] = field(default_factory=lambda: list(['test']))

def test_init_default():
    ''' values after default initialization '''
    options = DefaultTestOptions()
    # Mutable must be true in default objects, it otherwise screws up updating
    # values. mutable can only be set to False after construction:
    assert options.options_mutable == True
    # It is considered that users would expect a full export by default.
    assert options.options_export_defaults == True
    assert options.test_int == 0
    assert options.test_string == ''
    assert options.test_list == ['test']

def test_init_containers():
    ''' cover common error of container initialization '''
    options_a = DefaultTestOptions()
    options_b = DefaultTestOptions()
    assert options_a.test_list == ['test']
    assert options_b.test_list == ['test']
    options_a.test_list.append('new')
    options_b.test_list = ['new']
    options_c = DefaultTestOptions(test_list=['constructed'])
    assert options_a.test_list == ['test', 'new']
    assert options_b.test_list == ['new']
    assert options_c.test_list == ['constructed']

def test_init_named_option_via_class():
    ''' Initialize via named option as class'''
    options = DefaultTestOptions.new_from_kwarg({'options': DefaultTestOptions(
        test_int=40, test_string='40', test_list=['40'])})
    assert options.test_int == 40
    assert options.test_string == '40'
    assert options.test_list == ['40']

def test_init_named_option_via_dict():
    ''' Initialize via named option as dict'''
    options = DefaultTestOptions.new_from_kwarg({'options': {
        'test_int': 40, 'test_string': '40', 'test_list': ['40']}})
    assert options.test_int == 40
    assert options.test_string == '40'
    assert options.test_list == ['40']

def test_init_named_option_invalid_type():
    ''' Test initializazion via options=<invalid type> '''
    with pytest.raises(AttributeError) as exc:
        options = DefaultTestOptions.new_from_kwarg({'options': 42})
    # General error statement with option name:
    assert 'Argument options must be ' in str(exc.value)
    assert 'DefaultTestOptions' in str(exc.value)
    assert 'int' in str(exc.value)

def test_init_named_option_unknown_key():
    ''' Test initializazion via options={} with unknown key '''
    with pytest.raises(AttributeError) as exc:
        options = DefaultTestOptions.new_from_kwarg(
            {'options': {'unknown': 42}})
    # General error statement with option name:
    assert 'Argument [unknown] is unknown' in str(exc.value)
    assert 'DefaultTestOptions' in str(exc.value)
    assert "['options_mutable', 'options_export_defaults', 'test_int', 'test_string', 'test_list', 'options']" in str(exc.value)

def test_mutable_implementation():
    options_A = AppxfOptions()
    options_B = AppxfOptions()
    # mutable must be True
    assert options_A.options_mutable
    # mutable must not be an instance variable - when same Options class is
    # used in different context (like a string setting), on object may have
    # options mutable, the other one not.
    options_B.options_mutable = False
    assert options_A.options_mutable
    assert not options_B.options_mutable

def test_mutable_behavior():
    options = DefaultTestOptions()
    assert options.test_int == 0
    # since mutable is true, test must be changeable:
    options.test_int = 42
    assert options.test_int == 42
    # now, setting mutable to False, we expect an error
    options.options_mutable = False
    with pytest.raises(AttributeError) as exc:
        options.test_int = 0
    # General error statement with option name:
    assert 'Cannot change test_int' in str(exc.value)
    # class should be in error message:
    assert f'{options.__class__}' in str(exc.value)

def test_update():
    options = DefaultTestOptions()
    options.update(test_int=142, test_string='new')
    assert options.test_int == 142
    assert options.test_string == 'new'

def test_update_error_on_unknown():
    options = DefaultTestOptions()
    with pytest.raises(AttributeError) as exc:
        options.update(unknown=14)
    assert 'Argument [unknown] is unknown' in str(exc.value)
    assert 'DefaultTestOptions' in str(exc.value)
    assert 'options_mutable' in str(exc.value)
    assert 'test_int' in str(exc.value)
    assert 'test_string' in str(exc.value)

def test_update_with_mutable_false():
    options = DefaultTestOptions()
    options.update(options_mutable=False, test_int=142, test_string='new')
    assert options.test_int == 142
    assert options.test_string == 'new'
    assert not options.options_mutable
    with pytest.raises(AttributeError) as exc:
        options.test_int = 42

def test_construct_direct():
    option = DefaultTestOptions(test_int=42, test_string='test')
    assert option.test_int == 42
    assert option.test_string == 'test'

def test_construct_kwarg_simple():
    kwarg = {'test_int': 42, 'test_string': 'test'}
    option = DefaultTestOptions.new_from_kwarg(kwarg_dict=kwarg)
    assert not kwarg # kwarg should be empty after consuming kwargs in new_from_kwarg()
    assert option.test_int == 42
    assert option.test_string == 'test'

def test_construct_kwarg_protected_other():
    # checking default value before test
    option = DefaultTestOptions()
    assert option.options_export_defaults
    # testing with direct protected name
    kwarg = {'options_export_defaults': False}
    option = DefaultTestOptions.new_from_kwarg(kwarg_dict=kwarg)
    assert not kwarg # kwarg should be empty after consuming kwargs in new_from_kwarg()
    assert not option.options_export_defaults
    # testing with options prefix
    kwarg = {'options_export_defaults': False}
    option = DefaultTestOptions.new_from_kwarg(kwarg_dict=kwarg)
    assert not kwarg # kwarg should be empty after consuming kwargs in new_from_kwarg()
    assert not option.options_export_defaults

def test_construct_kwarg_protected_mutable():
    kwarg = {'options_mutable': False}
    option = DefaultTestOptions.new_from_kwarg(kwarg_dict=kwarg)
    assert not kwarg # kwarg should be empty after consuming kwargs in new_from_kwarg()
    assert not option.options_mutable

def test_restore_cycle():
    ''' test basic cycle of get_state() and set_state() '''
    options = DefaultTestOptions(test_int=10, test_string='10', test_list=['10', '20'])
    assert options.test_int == 10
    assert options.test_string == '10'
    assert options.test_list == ['10', '20']
    state = options.get_state()
    print(state)
    options = DefaultTestOptions()
    options.set_state(state)
    assert options.test_int == 10
    assert options.test_string == '10'
    assert options.test_list == ['10', '20']

def test_restore_cycle_masked_ones():
    ''' options in attribute mask are not restored '''
    options = DefaultTestOptions()
    assert options.options_mutable
    assert options.options_export_defaults
    options.options_export_defaults = False
    options.options_mutable = False
    state = options.get_state()
    options = DefaultTestOptions()
    options.set_state(state)
    assert options.options_mutable
    assert options.options_export_defaults

def test_restore_cycle_while_not_mutable():
    ''' test restore while mutable is exported '''
    @dataclass
    class OptionsExportingMutable(DefaultTestOptions):
        attribute_mask = [attr for attr in DefaultTestOptions.attribute_mask
                          if attr != 'options_mutable']
    print(OptionsExportingMutable.attribute_mask)
    options = OptionsExportingMutable(test_int=10, test_string='10', test_list=['10', '20'])
    # initial value checks are covered in test_restore_cycle()
    options.options_mutable = False
    assert options.options_mutable == False
    state = options.get_state()
    assert 'options_mutable' in state
    assert state['options_mutable'] == False
    options = DefaultTestOptions()
    options.set_state(state)
    assert options.test_int == 10
    assert options.test_string == '10'
    assert options.test_list == ['10', '20']
    assert options.options_mutable == False

def test_restore_cycle_without_defaults():
    options = DefaultTestOptions(test_string='10')
    options.options_export_defaults = False
    state = options.get_state()
    # only test_list included in exported state
    print(state)
    assert 'test_string' in state
    assert len(state) == 1
    options = DefaultTestOptions(test_int=42, test_list=['baa'])
    # when only exporting defaults, the reset must be used
    options.reset()
    options.set_state(state)
    assert options.test_int == 0
    assert options.test_string == '10'
    assert options.test_list == ['test']

def test_restore_cycle_without_defaults_mutable():
    ''' get_state/set_state without defaults and mutable exported as False '''
    @dataclass
    class OptionsExportingMutable(DefaultTestOptions):
        options_export_defaults: bool = False
        attribute_mask = [key for key in DefaultTestOptions.attribute_mask if key != 'options_mutable']
    options = OptionsExportingMutable(test_string='10')
    options.options_mutable = False
    state = options.get_state()
    # only test_string and mutable included in exported state
    print(state)
    assert 'test_string' in state
    assert 'options_mutable' in state
    assert len(state) == 2
    options = DefaultTestOptions(test_int=42, test_list=['baa'])
    # when only exporting defaults, the reset must be used
    options.reset()
    options.set_state(state)
    assert options.options_mutable == False
    assert options.test_int == 0
    assert options.test_string == '10'
    assert options.test_list == ['test']