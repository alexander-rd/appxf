''' Settings selecting a value from a predefined list '''
from typing import MutableMapping, Any

from .setting import AppxfSettingExtension, _BaseTypeT, _BaseSettingT


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


class AppxfSettingSelect(AppxfSettingExtension[_BaseSettingT, _BaseTypeT]):
    ''' Setting restricted to a named, predefined set

    You typically provide the available options during construction, like:
    [sel = AppxfSetting.new('int', options={'one': 1, 'two': 2})].
    '''
    # This AppxfSetting class is an extention on an existing AppxfSetting type
    # which is marked by this class attribute:
    setting_extension = 'select'
    # The class can be instantiated either by AppxfSetting.new('int_select')
    # for string based type selection or via AppxfSetting[AppxfInt]() for
    # direct type based initialization.

    def __init__(self,
                 base_setting: _BaseSettingT,
                 value: str | None = None,
                 options: dict[str, str] | None = None,
                 name: str = '',
                 **kwargs):
        if value is None:
            value = ''
        # unusual, but select_map in options has to be set before
        # super().__init__ to have it available in _validated_conversion.
        if options is None:
            options = {}
        self.options = {'select_map': options}
        # usualy, options are not mutable
        self.options['mutable'] = False
        super().__init__(base_setting=base_setting,
                         value=value,
                         name=name,
                         **kwargs)

    # Note: get_supported_types and get_default is taken from the
    # AppxfSelect[type] we are deriving from.

    def _validated_conversion(self, value: str) -> tuple[bool, _BaseTypeT]:
        if value == '':
            return True, self.base_setting_class.get_default()
        if value in self.options['select_map']:
            return True, self.options['select_map'][value]
        return False, self.get_default()

    ###################/
    ## Option Handling
    #/

    # a shortcut to the select_map, first used in the GUI implementation
    @property
    def select_map(self) -> MutableMapping[str, Any]:
        ''' Select map (shortcut to options['select_map'])'''
        return self.options['select_map']