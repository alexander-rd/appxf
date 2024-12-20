''' Settings selecting a value from a predefined list '''
from .setting import AppxfSetting, AppxfString
from typing import NewType

# Intent is to support complex data like long text templates by selecting and
# referencing it by a title.
#
# The following differences apply to standard settings:
#   * Input is a string from a predefined list (drop down, no reason for other
#     types since it's purpose is "name for the setting value")
#   * It will be uncommon or not even possible to set the value directly
#
# A further extention is a configurable and storable selection. For standard
# settings, the application only knows the type of the setting. Select settings
# will have a changeable list of options which can be stored along or separate
# to the setting.

# TODO: should the custom type be the "storable" selection or at least
# something that supports the serialization?

# Simple Use Case: Text Inspection.
#
# The tool provides a set of Email texts that can be displayed by a list
# select. The select would be too long to reference the whole text such that
# only a title appears in the list.

# Storable Use Case: Storable Email Templates
#
# The tool user can store Email text templates into the configuration for
# reuse.

# Storable Focus Use Case: Translations
#
# The transtlation keywords (list selection keys) are fixed but the user can
# edit the translations (the values behind an AppxfStringSelection). The tool
# would use use the AppxfStringSelect conversions.

# Given from the above examples, there is different behavior that may or may
# not be possible:
#   1) Adding or removing new selectable items
#   2) Changing the value behind a selectable item
#
# If neither (1) or (2) is possible, the selection list is known at
# construction time and no storage is necessary. Only (1) possible is not
# reasonable, but only (2) has valid use cases.

AppxfSelect = NewType('AppxfSelect', object)

class AppxfStringSelect(AppxfSetting[str]):
    ''''''
    def __init__(self,
                 value: str | None = None,
                 options: dict[str, str] | None = None,
                 name: str = '',
                 **kwargs):
        super().__init__(value, name, **kwargs)
        if options is None:
            options = {}
        self._options = options
    #def __init__(self, options: dict | None = None):
    #    if options is None:
    #        options = {}
    #    self._options = options

    @classmethod
    def get_supported_types(cls) -> list[type | str]:
        return [AppxfSelect, 'StringSelect']

    def _validate_base_type(self, value: str) -> bool:
        return False
    # TODO: Problem is that despite string input, just verifying input is not
    # sufficient.

    def _validated_conversion(self, value: str) -> tuple[bool, AppxfSelect]:
        if value == '':
            return True, self._options.values()[0]
        if value in self._options:
            return True, self._options[value]
        return False, self.get_default()

    @classmethod
    def get_default(cls):
        return ''