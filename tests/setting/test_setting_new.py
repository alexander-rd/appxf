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

class BaseSettingTest:
    setting_class: type[Setting] = None  # type: ignore
    setting_types: list[str | type] = []
    simple_input: SettingInput = SettingInput(input='', value='')

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
    simple_input = SettingInput(input='', value='')

class TestSettingText(BaseSettingTest):
    setting_class = SettingText
    setting_types = ['text']
    simple_input = SettingInput(input='', value='')

class TestSettingPassword(BaseSettingTest):
    setting_class = SettingPassword
    setting_types = ['pass', 'password']
    simple_input = SettingInput(input='123456', value='123456')

class TestSettingEmail(BaseSettingTest):
    setting_class = SettingEmail
    setting_types = ['email', 'Email']
    simple_input = SettingInput(input='some@thing.de', value='some@thing.de')

class TestSettingBool(BaseSettingTest):
    setting_class = SettingBool
    setting_types = [bool, 'bool', 'boolean']
    simple_input = SettingInput(input='1', value=True)

class TestSettingInt(BaseSettingTest):
    setting_class = SettingInt
    setting_types = [int, 'int', 'integer']
    simple_input = SettingInput(input='42', value=42)

class TestSettingFloat(BaseSettingTest):
    setting_class = SettingFloat
    setting_types = [float, 'float']
    simple_input = SettingInput(input='3.14159', value=3.14159)

class TestSettingDict(BaseSettingTest):
    setting_class = SettingDict
    setting_types = [dict, MutableMapping, 'dict', 'dictionary']
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

            assert obj.setting_class is not None
            tested_classes.add(obj.setting_class)

            assert obj.setting_types
            for this_type in obj.setting_types:
                tested_types.add(this_type)

    print(expected_types)
    print(tested_types)

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