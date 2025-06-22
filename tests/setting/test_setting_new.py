import pytest

from collections.abc import MutableMapping
from collections import namedtuple

from kiss_cf.setting import Setting, SettingExtension
from kiss_cf.setting import AppxfSettingError, AppxfSettingConversionError
from kiss_cf.setting import SettingString, SettingText, SettingEmail, SettingPassword
from kiss_cf.setting import SettingBool, SettingInt, SettingFloat

from kiss_cf.setting import setting as setting_module

SettingInput = namedtuple('SettingInput', 'input value')

class BaseSettingTest:
    setting_class = SettingString  # using real setting to avoid type errors below
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
        state = setting.get_state(options=export_options)

        setting.options.display_width = 13
        setting.set_state(state, options=export_options)
        assert setting.options.display_width == 42

class TestSettingString(BaseSettingTest):
    setting_class = SettingString
    setting_types = [str, 'str', 'string']
    simple_input = SettingInput(input='', value='')

    valid_input = [
        SettingInput(input='test', value='test'),
        SettingInput(input='123', value='123'),
        SettingInput(input='', value=''),
    ]