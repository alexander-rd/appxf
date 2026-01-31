''' Covers all setting types
Includes:
 * init, value setting and validity
 * basic option handling

Note: due to the self-test that ensures all registered settings being covered,
the type test classes must be added here. No effort spent in searching the
whole test database for subclasses of BaseSettingTest.
'''

import inspect
import sys
import pytest

from collections.abc import MutableMapping
from typing import Any, Callable

from appxf_private.setting import Setting
from appxf_private.setting import AppxfSettingError, AppxfSettingConversionError
from appxf_private.setting import SettingString, SettingText, SettingEmail, SettingPassword
from appxf_private.setting import SettingBool, SettingInt, SettingFloat
from appxf_private.setting import SettingBase64
from appxf_private.setting import SettingDict

from appxf_private.setting import setting as setting_module


class SettingCase():
    def __init__(self,
                 input,
                 value: Any | None = None,
                 string: str | None = None,
                 input_check: Any | None = None):
        self.input = input

        if value is None:
            self._value = input
        else:
            self._value = value

        if string is None:
            self._string = str(self.value)
        else:
            self._string = string

        if input_check is None:
            self.input_check = self.input
        else:
            self.input_check = input_check

    def __str__(self):
        return f'Case(input={self.input}, value={self.value}, string={self.string})'

    @property
    def value(self):
        if isinstance(self._value, Callable):
            return self._value(self)
        else:
            return self._value

    @property
    def string(self):
        if isinstance(self._string, Callable):
            return self._string(self)
        else:
            return self._string

# required class that cannot convert to str and would be invalid input for
# SettingStr and SettingText:
class DummyClassErrorOnStrCreation():
    def __str__(self):
        raise TypeError('some failure')

class BaseSettingTest:
    setting_class: type[Setting] = None  # type: ignore
    setting_types: list[str | type] = []
    simple_input: SettingCase = SettingCase(input='')

    invalid_init: list = []
    default_value_is_valid = False
    valid_input: list[SettingCase] = []

    def verify_valid(self, pre_comment: str,
                     setting: Setting, case: SettingCase):
        assert setting.input == case.input_check, (
            f'{pre_comment} for {self.setting_class.__name__} '
            f'failed for INPUT on case {case}. '
            f'It returned {setting.input}.'
            )
        assert setting.value == case.value, (
            f'{pre_comment} for {self.setting_class.__name__} '
            f'failed for VALUE on case {case}. '
            f'It returned {setting.value}.'
            )
        assert setting.to_string() == case.string, (
            f'{pre_comment} for {self.setting_class.__name__} '
            f'failed for STRING on case {case}. '
            f'It returned {setting.to_string()}.'
            )

    ### cases for initialization

    def test_meta_type_lookup(self):
        for setting_type in self.setting_types:
            setting_class, dump = setting_module._SettingMeta.get_setting_type(setting_type)
            assert setting_class == self.setting_class

    def test_init_simple(self):
        for setting_type in self.setting_types:
            setting = Setting.new(setting_type, self.simple_input.input)
            assert setting.input == self.simple_input.input_check
            assert setting.value == self.simple_input.value

    def test_init_default(self):
        for setting_type in self.setting_types:
            setting = Setting.new(setting_type)
            assert setting.value == setting.get_default()

    def test_init_default_options(self):
        for setting_type in self.setting_types:
            setting = Setting.new(setting_type, name='this name')
            assert setting.options.mutable
            assert setting.options.name == 'this name'

    def test_init_valid(self):
        # default value must initialize:
        for case in self.valid_input:
            setting = self.setting_class(case.input)
            self.verify_valid('Verifying valid init', setting, case)

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

    ### cases for validation and setting values

    def test_validate_valid(self):
        setting = self.setting_class()
        for case in self.valid_input:
            assert setting.validate(case.input), (
                f'{self.setting_class} should identify the following '
                f'value as valid: "{case.input}"'
                )

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
        for case in self.valid_input:
            setting = self.setting_class()
            setting.value = case.input
            self.verify_valid('Verifying valid value setting', setting, case)

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

    ### set_state / get_state
    def test_set_state(self):
        for case in self.valid_input:
            setting = self.setting_class(value=case.input)
            self.verify_valid('Verifying valid value init before set_state', setting, case)
            state = setting.get_state(type=True)

            # Note: "type=True" above is required for the SettingDict cases.
            # Same for add_new_keys=True below.

            setting = self.setting_class()
            if issubclass(self.setting_class, SettingDict):
                setting.set_state(state, type=True, add_new_keys=True, exception_on_new_key=False)
            else:
                setting.set_state(state)
            self.verify_valid('Verifying valid value after SET_STATE', setting, case)

    ### option handling

    # REQ: If mutable is False, there must be an exception when assigning new
    # values:
    def test_setting_not_mutable(self):
        setting = self.setting_class()
        setting.options.mutable = False
        with pytest.raises(AppxfSettingError) as exc_info:
            setting.value = self.simple_input.input
        if issubclass(self.setting_class, SettingDict):
            assert 'SettingDict() mutable option is False' in str(exc_info.value) + str(exc_info.value.__cause__)
        else:
            assert 'is set to be not mutable' in str(exc_info.value)


    # REQ: Even if mutable is set to False upon initialization, the initialization
    # must not fail. Note that the setting options are set before the value is
    # taken over.
    def test_setting_not_mutable_init(self):
        setting = self.setting_class(value=self.simple_input.value, mutable = False)
        assert not setting.options.mutable
        assert setting.value == self.simple_input.value

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
    simple_input = SettingCase(input='', value='')
    valid_input = [
            SettingCase(input='hello'),
            SettingCase(input='!"§$%&/()=?'),
            SettingCase(input='42'),
    ]

class TestSettingText(BaseSettingTest):
    setting_class = SettingText
    setting_types = ['text']
    invalid_init = [DummyClassErrorOnStrCreation(), DummyClassErrorOnStrCreation, 42]
    default_value_is_valid = True
    simple_input = SettingCase(input='', value='')
    valid_input = [
        SettingCase(input='!"§$%&/()=?\n'),
    ]

class TestSettingPassword(BaseSettingTest):
    setting_class = SettingPassword
    setting_types = ['pass', 'password']
    invalid_init = ['short', 42]
    default_value_is_valid = False
    simple_input = SettingCase(input='123456', value='123456')
    valid_input = [
        SettingCase(input='long_enough'),
    ]

class TestSettingEmail(BaseSettingTest):
    setting_class = SettingEmail
    setting_types = ['email', 'Email']
    invalid_init = ['no email', 'no email@some.de', 'some@nope', 'nope.de', 42]
    default_value_is_valid = False
    simple_input = SettingCase(input='some@thing.de', value='some@thing.de')
    valid_input = [
        SettingCase(input='some@thing.it'),
        SettingCase(input='with-minus@domain.net'),
    ]

class TestSettingBool(BaseSettingTest):
    setting_class = SettingBool
    setting_types = [bool, 'bool', 'boolean']
    invalid_init = ['', b'', 'nope']
    default_value_is_valid = True
    simple_input = SettingCase(input='1', value=True)
    valid_input = [
        SettingCase(input=True, value=1),
        SettingCase(input=False, value=0),
        SettingCase(input='yes', value=1),
        SettingCase(input='no', value=0),
        SettingCase(input='true', value=1),
        SettingCase(input='False', value=0),
        SettingCase(input='1', value=1),
        ]

class TestSettingInt(BaseSettingTest):
    setting_class = SettingInt
    setting_types = [int, 'int', 'integer']
    invalid_init = ['', b'', '42.2', 'test']
    default_value_is_valid = True
    simple_input = SettingCase(input='42', value=42)
    valid_input = [
        SettingCase(input=0),
        SettingCase(input=42),
        SettingCase(input='0042', value=42),
        SettingCase(input=-1234567890),
        SettingCase(input='123', value=123),
        SettingCase(input='-1234567890', value=-1234567890),
        SettingCase(input=True, value=1),
        SettingCase(input=False, value=0),
        ]

class TestSettingFloat(BaseSettingTest):
    setting_class = SettingFloat
    setting_types = [float, 'float']
    invalid_init = ['', b'', 'test']
    default_value_is_valid = True
    simple_input = SettingCase(input='3.14159', value=3.14159)
    valid_input = [
        SettingCase(input=12345,        value=12345,        string='12345.0'),
        SettingCase(input=1.1234567890, value=1.1234567890, string='1.123456789'),
        SettingCase(input=False,        value=0,            string='0.0'),
        SettingCase(input=False,        value=0,            string='0.0'),
        SettingCase(input=True,         value=1,            string='1.0'),
    ]

class TestSettingDict(BaseSettingTest):
    setting_class = SettingDict
    setting_types = [dict, MutableMapping, 'dict', 'dictionary']
    invalid_init = ['', 'test', 42]
    default_value_is_valid = True
    simple_input = SettingCase(
        input={'key': (str, 'value')},
        value={'key': 'value'},
        input_check={'key': 'value'})
    valid_input = [
        SettingCase(input={'int': 42},
                    value={'int': 42},
                    input_check={'int': 42}),
        SettingCase(input={'int': (int, '0042')},
                    value={'int': 42},
                    input_check={'int': '0042'}),
        SettingCase(input={},
                    value={},
                    string='')
    ]


class TestSettingBase64(BaseSettingTest):
    setting_class = SettingBase64
    setting_types = ['base64', 'Base64']
    default_value_is_valid = True
    simple_input = SettingCase(input=b'', value=b'', string='')
    valid_input = [
        SettingCase(input=b'\x00\x01', value=b'\x00\x01', string='AAE='),
        SettingCase(input=bytearray(b'\x00\x01'), value=b'\x00\x01', string='AAE='),
        SettingCase(input='AAE=', value=b'\x00\x01', string='AAE='),
        SettingCase(input='AAE=\n', value=b'\x00\x01', string='AAE='),
    ]
    invalid_init = [42, 'not_base64!!', object()]

def test_base64_wrong_size():
    setting = SettingBase64(size=3)
    assert not setting.validate(b'')
    assert not setting.validate(b'\x00\x01')
    assert not setting.validate(b'\x00\x00\x00\x00')
    assert setting.validate(b'\x00\x00\x00')
    assert not setting.validate('AAE=')
    assert setting.validate('AAEA')

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
            assert obj.valid_input, (
                f'Test class {obj.__name__} must define '
                f'valid test cases SettingCase.'
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