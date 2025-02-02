''' Configuration and Settings

Typical use cases for application configuration settings are:
  * user settings like their email
  * parameters to access a database
  * storage paths, language or mode selection of the application
Additionally, settings are helpful when providing options for some
activity of the application.

All above use cases have user interaction in common, demanding for a string
conversion and ensuring validity of input. The following classes assist here:
  AppxfSetting - the abstract base class from which new specific settings can be
      derived.
  Appxf* -- Specific implementations ranging from AppxfString over AppxfInteger down
      to AppxfEmail and AppxfPassword.

Most of the use cases have in common that the settings need to be persisted and
the following classes are the entry points:
  SettingDict -- It behaves like a dict, providing all values but can
      access any Appxf* setting with validation and string conversion that is
      modelled behind.
  Config -- It collects several SettingDict objects as sections with some
      additional conveniance.
'''

# flake8: noqa F401

from .setting import Setting, SettingExtension, AppxfSettingError, AppxfSettingConversionError
from .setting import SettingString, SettingEmail, SettingPassword
from .setting import SettingBool, SettingInt, SettingFloat
from .setting_select import SettingSelect

from .setting_dict import SettingDict

from .setting import validated_conversion_configparser
