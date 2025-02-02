''' options module with Options object
'''
from kiss_cf import Options
from dataclasses import dataclass, field

import pytest

@dataclass
class DefaultTestOptions(Options):
    test_int: int = 0
    test_string: str = ''
    test_list: list[str] = field(default_factory=lambda: list(['test']))

def test_init_default():
    ''' values after default initialization '''
    options = DefaultTestOptions()
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
    assert "['test_int', 'test_string', 'test_list', 'options']" in str(exc.value)

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
    assert 'test_int' in str(exc.value)
    assert 'test_string' in str(exc.value)

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

def test_restore_cycle_without_defaults():
    options = DefaultTestOptions(test_string='10')
    state = options.get_state(export_defaults=False)
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
