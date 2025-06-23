
import pytest

from collections.abc import MutableMapping

from kiss_cf.setting import Setting, SettingExtension
from kiss_cf.setting import AppxfSettingError, AppxfSettingConversionError
from kiss_cf.setting import SettingString, SettingText, SettingEmail, SettingPassword
from kiss_cf.setting import SettingBool, SettingInt, SettingFloat

from kiss_cf.setting import setting as setting_module
# pylint: disable=protected-access
# pylint: disable=missing-function-docstring

# TODO: test min_length property setting being funcitonal for passwords

@pytest.mark.parametrize(
    'appxf_class', setting_module._SettingMeta.implementations)
def test_setting_init(appxf_class):
    # skip any SettingExtension
    if issubclass(appxf_class, SettingExtension):
        return
    setting = appxf_class(name='test')
    assert setting.options.name == 'test'
    assert setting.options.mutable
    #if isinstance(setting, AppxfPassword):
    #    assert setting.masked
    #else:
    #    assert not setting.masked

def verify_conversion_error(exc_info, setting: Setting, input: object):
    # General formulation
    assert 'Cannot set' in str(exc_info.value)
    # Input value
    assert str(input) in str(exc_info.value)
    # Input type:
    assert str(type(input)) in str(exc_info.value)
    # Setting class name
    assert setting.__class__.__name__ in str(exc_info.value)

# REQ: If mutable is False, there must be an exception when assigning new
# values:
def test_setting_mutable():
    setting = Setting.new(str)
    setting.options.mutable = False
    with pytest.raises(AppxfSettingError) as exc_info:
        setting.value = 'new'
    assert 'is set to be not mutable' in str(exc_info.value)

# REQ: Even if mutable is set to False upon initialization, the initialization
# must not fail. Note that the setting options are set before the value is
# taken over.
def test_setting_not_mutable_init():
    setting = Setting.new(str, 'test', mutable = False)
    assert not setting.options.mutable
    assert setting.value == 'test'

# #######################################/
# # AppxfSetting base class functionality
# #/////////////////////////////////////

def test_setting_register_type_twice():
    with pytest.raises(AppxfSettingError) as exc_info:
        class DummyAppxfString(Setting):
            @classmethod
            def get_supported_types(cls) -> list[type | str]:
                return ['email']
            @classmethod
            def get_default(cls) -> str:
                return ''
    assert 'is already registered' in str(exc_info.value)
    assert 'DummyAppxfString' in str(exc_info.value)
    assert 'SettingEmail' in str(exc_info.value)

def test_setting_register_class_twice():
    with pytest.raises(AppxfSettingError) as exc_info:
        class SettingEmail(Setting):
            @classmethod
            def get_supported_types(cls) -> list[type | str]:
                return ['moreEmail']
            @classmethod
            def get_default(cls) -> str:
                return ''
    assert 'is already registered' in str(exc_info.value)
    assert 'SettingEmail' in str(exc_info.value)

def test_setting_register_no_supported_type():
    with pytest.raises(AppxfSettingError) as exc_info:
        class DummyAppxfString(Setting):
            @classmethod
            def get_supported_types(cls) -> list[type | str]:
                return []
            @classmethod
            def get_default(cls) -> str:
                return ''
    assert 'does not return any supported type' in str(exc_info.value)

def test_setting_register_incopmlete_class():
    with pytest.raises(AppxfSettingError) as exc_info:
        class DummyAppxfString(Setting):
            @classmethod
            def get_supported_types(cls) -> list[type | str]:
                return ['myEmail']
    # The class above has get_default_value() missing
    print(f'{exc_info.value}')

def test_setting_init_with_base_class():
    with pytest.raises(AppxfSettingError) as exc_info:
        Setting.new(Setting)
    assert 'You need to provide a fully implemented class' in str(exc_info.value)
    assert 'Setting is not' in str(exc_info.value)

def test_setting_init_with_unknown_type():
    with pytest.raises(AppxfSettingError) as exc_info:
        Setting.new('non_existing_type')
    assert 'Setting type [non_existing_type] is unknown.' in str(exc_info.value)
