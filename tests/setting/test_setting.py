''' Cover detailed Setting and Setting Meta Class behavior

Note that most functionality is covered with tests in test_setting_types.
'''
import pytest

from kiss_cf.setting import Setting, SettingExtension
from kiss_cf.setting import AppxfSettingError

from kiss_cf.setting import setting as setting_module
from kiss_cf.setting import base_types as base_types_module
# pylint: disable=protected-access
# pylint: disable=missing-function-docstring

# #########################################/
# # AppxfSetting and Registry (Meta Class)
# #/
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

#########################################
# configparser validation specific tests
#/

def test_configparser_validation_newlines():
    # Configparser had problems with newlines and strings are cought
    # explicitly.
    validity, value = base_types_module.validated_conversion_configparser(
        string='\n',
        res_type=str,
        default='default')
    assert not validity
    assert value == 'default'

def test_configparser_validation_wrong_type():
    # Acutally, this case should not even be reachable by the implementation
    # since wrong types are cought already before.
    validity, value = base_types_module.validated_conversion_configparser(
        string='',
        res_type=Setting,
        default='default')
    assert not validity
    assert value == 'default'