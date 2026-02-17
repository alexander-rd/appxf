# Copyright 2025-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
''' Definition of basic types like int or str as settings
'''
from __future__ import annotations
from typing import Type, Any
from dataclasses import dataclass
from email_validator import validate_email, EmailNotValidError

import base64
import binascii
import re
import configparser


from .setting import Setting, _BaseTypeT


class SettingString(Setting[str]):
    ''' Setting for basic strings

    No newline characters supported. The GUI elements would not support a multi
    line entry field. If required, use 'text' instead.
    '''
    @classmethod
    def get_supported_types(cls) -> list[type | str]:
        return ['string', str, 'str']

    @classmethod
    def get_default(cls):
        return ''

    def _validated_conversion(self, value: Any) -> tuple[bool, str]:
        if not issubclass(type(value), str):
            return False, self.get_default()
        if '\r' in value or '\n' in value:
            return False, self.get_default()
        return True, value


class SettingText(SettingString):
    ''' Setting for long texts

    Just a string that has a display_height option and allows newline
    characters.
    '''
    @dataclass
    class Options(Setting.Options):
        ''' Options for SettingText'''
        display_height: int = 5
        display_options = Setting.Options.display_options + ['display_height']

    @classmethod
    def get_supported_types(cls) -> list[type | str]:
        return ['text']

    # get_default() from string remains

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
        if not super()._validated_conversion(value)[0]:
            return False, self.get_default()
        # use email-validator package
        try:
            validate_email(value, check_deliverability=False)
            return True, value
        except EmailNotValidError:
            return False, self.get_default()


class SettingPassword(SettingString):
    ''' Setting for passwords

    Default minimum password length is 6.
    '''
    @dataclass
    class Options(Setting.Options):
        ''' Options for SettingText'''
        min_length: int = 6
        value_options = Setting.Options.value_options + ['min_length']

        display_masked: bool = True
        display_options = Setting.Options.display_options + ['display_masked']
    options: Options

    @classmethod
    def get_supported_types(cls) -> list[type | str]:
        return ['password', 'pass']

    def _validated_conversion(self, value: Any) -> tuple[bool, str]:
        if not super()._validated_conversion(value)[0]:
            return False, self.get_default()
        # only length check:
        if (
            self.options.min_length > 0 and
            len(value) < self.options.min_length
        ):
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
        return ['boolean', bool, 'bool']

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
        return ['integer', int, 'int']

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
        return ['float', float]

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

# TODO: add a SettingBase64 which is deriving from Setting[byte]. Default
# should be b''. Supported types are 'base64' and 'Base64' but NOT byte. The
# options are extended with "size" (value option). The validation would accept
# any byte value but also any string for which it expects a base 64 encoding.
# In addition to the base64 check and conversion, the resulting bytes must
# match the size option. A size=0 (default value) would ignore this size check.


class SettingBase64(Setting[bytes]):
    ''' Setting for bytes encoded as base64 strings

    Accepts raw bytes/bytearray values or base64-encoded strings.
    Options:
      - size: int (value option) -- if >0 the resulting bytes must match this
        length. Default is 0 which disables size checking.
    '''
    @dataclass
    class Options(Setting.Options):
        ''' Options for SettingBase64 '''
        size: int = 0
        value_options = Setting.Options.value_options + ['size']

    options: Options

    @classmethod
    def get_supported_types(cls) -> list[type | str]:
        return ['base64', 'Base64']

    @classmethod
    def get_default(cls) -> bytes:
        return b''

    def _validated_conversion(self, value: Any) -> tuple[bool, bytes]:
        # Accept raw bytes/bytearray directly
        if isinstance(value, (bytes, bytearray)):
            data = bytes(value)
            if self.options.size > 0 and len(data) != self.options.size:
                return False, self.get_default()
            return True, data

        # Accept strings that are base64 encoded
        if isinstance(value, str):
            # Strip whitespace/newlines which are valid in some base64 forms
            cleaned = ''.join(value.split())
            try:
                decoded = base64.b64decode(cleaned, validate=True)
            except (binascii.Error, ValueError):
                return False, self.get_default()
            if self.options.size > 0 and len(decoded) != self.options.size:
                return False, self.get_default()
            return True, decoded

        # Not acceptable
        return False, self.get_default()

    def to_string(self) -> str:
        # Return base64 representation of stored bytes
        return base64.b64encode(self._value).decode('ascii')
