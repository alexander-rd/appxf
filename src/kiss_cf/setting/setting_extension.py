''' Extending settings with additional behavior.

Fancy and planned to be reworked!
'''
# TODO: refactoring according to ticket #17: aggregate Setting instead of
# deriving from it.

from __future__ import annotations
from typing import Generic, Any, TypeVar

from .setting import Setting, _BaseTypeT, AppxfSettingError

# SettingExtension needs to remain generic with respect to the original base
# type (like int or str) but also with respect to the specific Setting it
# extends. To remain a Setting, it also needs to derive from Setting.
_BaseSettingT = TypeVar('_BaseSettingT', bound=Setting)


class SettingExtension(Generic[_BaseSettingT, _BaseTypeT],
                       Setting[_BaseTypeT]):
    ''' Class for extended setting behavior

    Class behavior relies on a base_setting (maintained as an attribute).
    '''
    setting_extension = ''

    def __init__(self,
                 base_setting: _BaseSettingT,
                 value: _BaseTypeT | None = None,
                 **kwargs):
        # base_setting has to be available during __init__ of Setting
        # since it will validate the value which should rely on the
        # base_setting. ++ base_setting also has to be an instance:
        #   * to consistently store base setting options
        #   * the base_setting is used in GUI (example is text that is
        #     supported by templates via SettingSelect but the final output
        #     being the changed entry that may or may not be stored as a new
        #     template)
        #   * to allow extensions of extensions (no use case, yet)
        if isinstance(base_setting, type):
            raise AppxfSettingError(
                f'base_setting input must be a Setting instance, not '
                f'just a type. You provided {base_setting}')
        self.base_setting = base_setting
        super().__init__(value=value, **kwargs)
        # also apply initial value to the base_setting - this needs to be
        # self.value since original value may be tranlated by the extension to
        # something else like SettingSelect does it
        if value is not None:
            self.base_setting.value = self.value

    # This realization only applies to instances. The class registration for
    # SettingExtensions will not rely on get_default().
    def get_default(self) -> _BaseTypeT:
        return self.base_setting.get_default()
    # To still provide an implementaiton of the classmethod, we provide a dummy
    # implementation (which violates the assumed types)

    @classmethod
    def get_default(cls) -> _BaseTypeT:
        return None  # type: ignore
    # TODO: the above double definition of get_default() is not correct and one
    # of the main reasons why the SettingExtension concept must be reworked.

    # Same applies to get_supported_types
    @classmethod
    def get_supported_types(cls) -> list[type | str]:
        return []

    def get_type(self) -> str:
        return f'{self.setting_extension}::{self.base_setting.get_type()}'

    # TODO: the below should become obsolete, setting_select already overwrites
    # it again since updating the getter removes the setter anyways. This may
    # go along with a complete removal of a generic "SeeingExtension" class.
    @Setting.value.setter
    def value(self, value: Any):
        # first step is like in base implementation - whatever the extension
        # does
        Setting.value.fset(self, value)  # type: ignore
        # but the result is also applied to the base_setting
        self.base_setting.value = self._value
