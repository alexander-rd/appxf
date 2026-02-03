# Copyright 2024-2026 the contributors of APPXF (github.com/alexander-rd/appxf)
# SPDX-License-Identifier: Apache-2.0
'''Facade for APPXF setting module

Typical use cases for application configuration settings are:
  * user settings like their email
  * parameters to access a database
  * storage paths, language or mode selection of the application
Additionally, settings are helpful when providing options for some
activity of the application.

All above use cases have user interaction in common, demanding for a string
conversion and ensuring validity of input. The following classes assist here:
  Setting - the abstract base class from which new specific settings can be
      derived.
  Setting* -- Specific implementations ranging from SettingString over
      SettingInteger down to SettingEmail and SettingPassword.

Most of the use cases have in common that the settings need to be persisted and
the following classes are the entry points:
  SettingDict -- It behaves like a dict, providing all values but can
      access any Setting* setting with validation and string conversion that is
      modelled behind.
  Config -- It collects several SettingDict objects as sections with some
      additional conveniance.
'''

# TODO: transfer this description into the documentation. I cannot see how this
# description is valuable during development of applications.

from .setting import Setting, AppxfSettingError, AppxfSettingConversionError
from .base_types import SettingString, SettingText, SettingEmail, SettingPassword
from .base_types import SettingBool, SettingInt, SettingFloat
from .base_types import SettingBase64

from .setting_extension import SettingExtension
from .setting_select import SettingSelect

from .setting_dict import SettingDict, AppxfSettingWarning

from .base_types import validated_conversion_configparser
