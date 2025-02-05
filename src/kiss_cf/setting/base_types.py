''' Definition of basic types like int or str as settings
'''
from __future__ import annotations
from typing import Type, Any

import re
import configparser

from .setting import Setting, _BaseTypeT


class SettingString(Setting[str]):
    ''' Setting for basic strings '''
    @classmethod
    def get_supported_types(cls) -> list[type | str]:
        return [str, 'str', 'string']

    @classmethod
    def get_default(cls):
        return ''

    def _validated_conversion(self, value: Any) -> tuple[bool, str]:
        if not issubclass(type(value), str):
            return False, self.get_default()
        return True, value


class SettingEmail(SettingString):
    ''' Setting for Emails'''
    # get_default() and to_string() are derived from SettingString

    @classmethod
    def get_supported_types(cls) -> list[type | str]:
        return ['email', 'Email']

    def _validated_conversion(self, value: Any) -> tuple[bool, str]:
        if value == self.get_default():
            return True, value
        if not super()._validated_conversion(value)[0]:
            return False, self.get_default()
        # Check Email based on regexp, taken from here:
        # https://stackabuse.com/python-validate-email-address-with-regular-expressions-regex/
        regex = (r'([A-Za-z0-9]+[.-_])*'
                 r'[A-Za-z0-9]+@'
                 r'[A-Za-z0-9-]+'
                 r'(\.[A-Z|a-z]{2,})+')
        # fallback to generic regexp handling
        regex = re.compile(regex)
        if not re.fullmatch(regex, value):
            return False, self.get_default()
        return True, value


class SettingPassword(SettingString):
    ''' Setting for passwords

    Default minimum password length is 6.
    '''
    @classmethod
    def get_supported_types(cls) -> list[type | str]:
        return ['pass', 'password']

    def __init__(self,
                 min_length: int | None = None,
                 **kwargs):
        # min_length must be set before super super().__init__() since it uses
        # the validation before setting the value.
        self.min_length = 6 if min_length is None else min_length
        super().__init__(**kwargs)

        self.masked = True

    def _validated_conversion(self, value: Any) -> tuple[bool, str]:
        if value == self.get_default():
            return True, value
        if not super()._validated_conversion(value)[0]:
            return False, self.get_default()
        # only length check:
        if self.min_length > 0 and len(value) < self.min_length:
            return False, self.get_default()
            # TODO: Error message handling should be better. The specific
            # validate should tell what exactly failed.
        return True, value


def validated_conversion_configparser(
        string: str,
        res_type: Type[_BaseTypeT],
        default: _BaseTypeT) -> tuple[bool, _BaseTypeT]:
    ''' Helper for common conversion by configparser

    It takes a string (no type checks included) and uses the configparser
    implementations getboolean(), getint() or getfloat() dependent on requested
    type.

    Arguments:
        string -- the string to convert
        res_type -- the type to convert to (bool, int or float)
        default -- default value to use when conversion fails

    Returns:
        tuple of (1) a boolean that is True when the conversion was successful
        with (2) the conversion result. If the conversion failed, (1) False
        will be returned and the provided default value.
    '''
    # avoid problems when string contains newlines:
    if '\n' in string:
        return False, default
    config = configparser.ConfigParser()
    config.read_string(f'[DEFAULT]\ntest = {string}')
    try:
        if res_type == bool:
            value = config.getboolean('DEFAULT', 'test')
        elif res_type == int:
            value = config.getint('DEFAULT', 'test')
        elif res_type == float:
            value = config.getfloat('DEFAULT', 'test')
        else:
            return False, default
    except ValueError:
        return False, default
    return True, value  # type: ignore


class SettingBool(Setting[bool]):
    ''' Setting for booleans '''
    @classmethod
    def get_supported_types(cls) -> list[type | str]:
        return [bool, 'bool', 'boolean']

    @classmethod
    def get_default(cls) -> bool:
        return False

    def _validated_conversion(self, value: Any) -> tuple[bool, bool]:
        if (
            issubclass(type(value), bool) or
            issubclass(type(value), int) or
            issubclass(type(value), float)
        ):
            return True, bool(value)
        if isinstance(value, str):
            return validated_conversion_configparser(value, bool,
                                                     self.get_default())
        return False, self.get_default()

    def to_string(self) -> str:
        return '1' if self._value else '0'


class SettingInt(Setting[int]):
    ''' Setting for Integers '''
    @classmethod
    def get_supported_types(cls) -> list[type | str]:
        return [int, 'int', 'integer']

    @classmethod
    def get_default(cls) -> int:
        return 0

    def _validated_conversion(self, value: Any) -> tuple[bool, int]:
        if issubclass(type(value), int):
            return True, int(value)
        if isinstance(value, str):
            return validated_conversion_configparser(value, int,
                                                     self.get_default())
        return False, self.get_default()


class SettingFloat(Setting[float]):
    ''' Setting for Float '''
    @classmethod
    def get_supported_types(cls) -> list[type | str]:
        return [float, 'float']

    @classmethod
    def get_default(cls) -> float:
        return 0.0

    def _validated_conversion(self, value: Any) -> tuple[bool, float]:
        if (
            issubclass(type(value), float) or
            issubclass(type(value), int)
        ):
            return True, float(value)
        if isinstance(value, str):
            return validated_conversion_configparser(value, float,
                                                     self.get_default())
        return False, self.get_default()
