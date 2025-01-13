''' Test base Options object
'''
from kiss_cf import AppxfOptions
from dataclasses import dataclass

import pytest

@dataclass
class DefaultTestOptions(AppxfOptions):
    test_int: int = 0
    test_string: str = ''

def test_mutable_implementation():
    options_A = AppxfOptions()
    options_B = AppxfOptions()
    # _mutable must be True
    assert options_A.options_mutable
    # _mutable must be a instance variable
    options_B.options_mutable = False
    assert options_A.options_mutable
    assert not options_B.options_mutable

def test_mutable_behavior():
    @dataclass
    class Options(AppxfOptions):
        test: int = 0
    options = Options()
    assert options.test == 0
    # since mutable is true, test must be changeable:
    options.test = 42
    assert options.test == 42
    # now, setting mutable to False, we expect an error
    options.options_mutable = False
    with pytest.raises(AttributeError) as exc:
        options.test = 0
    # General error statement with option name:
    assert 'Cannot change test ' in str(exc.value)
    # class should be in error message:
    assert f'{options.__class__}' in str(exc.value)

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