import inspect
import sys
import pytest

from collections.abc import MutableMapping
from collections import namedtuple

from kiss_cf.setting import Setting, SettingExtension
from kiss_cf.setting import AppxfSettingError, AppxfSettingConversionError
from kiss_cf.setting import SettingString, SettingText, SettingEmail, SettingPassword
from kiss_cf.setting import SettingBool, SettingInt, SettingFloat
from kiss_cf.setting import SettingDict

from kiss_cf.setting import setting as setting_module

SettingInput = namedtuple('SettingInput', 'input value')


# required class that cannot convert to str and would be invalid input for
# SettingStr and SettingText:
class DummyClassErrorOnStrCreation():
    def __str__(self):
        raise TypeError('some failure')

class BaseSettingTest:
    setting_class: type[Setting] = None  # type: ignore
    setting_types: list[str | type] = []
    simple_input: SettingInput = SettingInput(input='', value='')

    invalid_init: list = []
    default_value_is_valid = False
    valid_input: list[SettingInput] = []

    def test_init_simple(self):
        for setting_type in self.setting_types:
            setting = Setting.new(setting_type, self.simple_input.input)
            assert setting.input == self.simple_input.input
            assert setting.value == self.simple_input.value

    def test_init_default(self):
        for setting_type in self.setting_types:
            setting = Setting.new(setting_type)
            assert setting.value == setting.get_default()

    def test_init_invalid(self):
        # Utilizing AppxfSetting.new() still uses the corresponding __init__
        for value in self.invalid_init:
            with pytest.raises((AppxfSettingConversionError, AppxfSettingError)) as exc_info:
                self.setting_class(value)
                pytest.fail(f'{self.setting_class} should raise '
                            f'AppxfSettingConversionError on init '
                            f'for value: {value}')
            # General formulation
            assert 'Cannot set' in str(exc_info.value)
            # Actual input:
            try:
                test = str(value)
            except TypeError:
                # cannot check input that cannot be converted to str (see
                # DummyClassErrorOnStrCreation):
                pass
            else:
                assert str(value) in str(exc_info.value)
            # Input type:
            assert str(type(value)) in str(exc_info.value)
            # Setting class name
            assert self.setting_class.__name__ in str(exc_info.value)

    def test_validate_invalid(self):
        setting = self.setting_class()
        value_list = (self.invalid_init if self.default_value_is_valid
                      else self.invalid_init + [self.setting_class.get_default()]
                      )
        for value in value_list:
            assert not setting.validate(value), (
                f'{self.setting_class} should identify the following '
                f'value as invalid: "{value}"'
                )

    def test_setting_value_valid(self):
        # note: even though the default value may be invalid
        # (test_validate_invalid), it can still be set.

        # TODO
        pass

    def test_setting_value_invalid(self):
        setting = self.setting_class()
        # note: even though the default value may be invalid
        # (test_validate_invalid), it can still be set.
        for value in self.invalid_init:
            with pytest.raises((AppxfSettingConversionError, AppxfSettingError)) as exc_info:
                setting.value = value
                pytest.fail(f'{self.setting_class} should raise '
                            f'AppxfSettingConversionError on setting value '
                            f'for: "{value}"')
                        # General formulation
            assert 'Cannot set' in str(exc_info.value)
            # Actual input:
            try:
                test = str(value)
            except TypeError:
                # cannot check input that cannot be converted to str (see
                # DummyClassErrorOnStrCreation):
                pass
            else:
                assert str(value) in str(exc_info.value)
            # Input type:
            assert str(type(value)) in str(exc_info.value)
            # Setting class name
            assert self.setting_class.__name__ in str(exc_info.value)

            # ensure input/value still according to default constructed
            setting_ref = self.setting_class()
            assert setting.value == setting_ref.value
            assert setting.input == setting_ref.input

    def test_set_state_display_options(self):
        setting = self.setting_class(self.simple_input.input)
        setting.options.display_width = 42
        export_options = Setting.ExportOptions(display_options=True)
        state = setting.get_state(options=export_options.get_state())

        setting.options.display_width = 13
        setting.set_state(state, options=export_options.get_state())
        assert setting.options.display_width == 42

class TestSettingString(BaseSettingTest):
    setting_class = SettingString
    setting_types = [str, 'str', 'string']
    invalid_init = [DummyClassErrorOnStrCreation(), '\n', 42]
    default_value_is_valid = True
    simple_input = SettingInput(input='', value='')

class TestSettingText(BaseSettingTest):
    setting_class = SettingText
    setting_types = ['text']
    invalid_init = [DummyClassErrorOnStrCreation(), DummyClassErrorOnStrCreation, 42]
    default_value_is_valid = True
    simple_input = SettingInput(input='', value='')

class TestSettingPassword(BaseSettingTest):
    setting_class = SettingPassword
    setting_types = ['pass', 'password']
    invalid_init = ['short', 42]
    default_value_is_valid = False
    simple_input = SettingInput(input='123456', value='123456')

class TestSettingEmail(BaseSettingTest):
    setting_class = SettingEmail
    setting_types = ['email', 'Email']
    invalid_init = ['no email', 'no email@some.de', 'some@nope', 'nope.de', 42]
    default_value_is_valid = False
    simple_input = SettingInput(input='some@thing.de', value='some@thing.de')

class TestSettingBool(BaseSettingTest):
    setting_class = SettingBool
    setting_types = [bool, 'bool', 'boolean']
    invalid_init = ['', b'', 'nope']
    default_value_is_valid = True
    simple_input = SettingInput(input='1', value=True)

class TestSettingInt(BaseSettingTest):
    setting_class = SettingInt
    setting_types = [int, 'int', 'integer']
    invalid_init = ['', '42.2', 'test']
    default_value_is_valid = True
    simple_input = SettingInput(input='42', value=42)

class TestSettingFloat(BaseSettingTest):
    setting_class = SettingFloat
    setting_types = [float, 'float']
    invalid_init = ['', b'', 'test']
    default_value_is_valid = True
    simple_input = SettingInput(input='3.14159', value=3.14159)

class TestSettingDict(BaseSettingTest):
    setting_class = SettingDict
    setting_types = [dict, MutableMapping, 'dict', 'dictionary']
    invalid_init = ['', 'test', 42]
    default_value_is_valid = True
    simple_input = SettingInput(input={}, value={})

def test_setting_completeness():
    # Get expected classes and type declarations:
    expected_classes = set(setting_module._SettingMeta.type_map.values())
    expected_types = set(setting_module._SettingMeta.type_map.keys())

    # Get covered classes and type declarations from this module inspection:
    current_module = sys.modules[__name__]
    tested_classes = set()
    tested_types = set()
    for name, obj in inspect.getmembers(current_module):
        if (inspect.isclass(obj) and
            issubclass(obj, BaseSettingTest) and
            obj is not BaseSettingTest
            ):
            obj: BaseSettingTest = obj

            assert obj.invalid_init, (
                f'Test class {obj.__name__} must define '
                f'invalid input values (invalid_input).'
                )

            assert obj.setting_class is not None
            tested_classes.add(obj.setting_class)

            assert obj.setting_types
            for this_type in obj.setting_types:
                tested_types.add(this_type)

    # Check for missing coverage
    missing_classes = expected_classes - tested_classes
    missing_types = expected_types - tested_types
    assert not missing_classes, (
        f'The following setting classes are not yet covered: '
        f'{missing_classes}')
    assert not missing_types,  (
        f'The following setting types are not yet covered: '
        f'{missing_types}')

    extra_classes = tested_classes - expected_classes
    extra_types = tested_types - expected_types
    assert not missing_classes, (
        f'Odd, the following UNKNOWN setting classes are covered: '
        f'{extra_classes}')
    assert not missing_types,  (
        f'Odd, the following UNKNOWN setting types are covered: '
        f'{extra_types}')