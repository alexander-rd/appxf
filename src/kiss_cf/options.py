from kiss_cf import Stateful

from dataclasses import dataclass, fields, replace, Field
from typing import Any, Type, TypeVar

_OptionTypeT = TypeVar('_OptionTypeT', bound='AppxfOptions')

@dataclass(eq=False, order=False)
class AppxfOptions(Stateful):
    ''' maintain options for classes to aggregate from

    Base class implementation for option handling of classes, consuming kwarg's
    during construction via new_from_kwarg(). Also allows a reset to defaults
    via reset(). And a fine grained export configuration via
    Stateful.get_state(), all features from there plue a default option
    _export_defaults which can be set to False to reduce the amount of
    variables being stored.
    '''
    # default settings for options - all use a leading "options_" to avoid
    # naming conflicts with usage in applications:
    #  * options may be mutable (in GUI) or from application - this must be
    #    True during construction, construction will fail otherwise (see
    #    __setattr__)
    options_mutable: bool = True
    #  * only non-defaults may be exported via get_state - when restoring
    #    options it is adviced to reset() the options before applying the
    #    state
    options_export_defaults: bool = True
    # Above options should typically not be exported:
    attribute_mask = Stateful.attribute_mask + ['options_mutable',
                                                'options_export_defaults']

    def __setattr__(self, name: str, value: Any) -> None:
        if self.options_mutable or name in ['_mutable']:
            return super().__setattr__(name, value)
        raise AttributeError(
            f'Cannot change {name} to {value}, {self.__class__} is not '
            f'mutable (_mutable=False)')

    def reset(self):
        ''' Reset options to default values '''
        for field in fields(self):
            if field.default_factory:
                setattr(self, field.name, field.default_factory())
            elif field.default_factory:
                setattr(self, field.name, field.default)
            else:
                raise TypeError(
                    f'This should not happen: neither a default value or a '
                    f'default_factors is set for field {field.name} of '
                    f'{self.__class__}')

    def all_default(self) -> bool:
        ''' Identify if options have all fields with default values '''
        all_default = True
        for field in fields(self):
            if getattr(self, field.name) != field.default:
                all_default = False
                break
        return all_default

    @classmethod
    def new_from_kwarg(cls: Type[_OptionTypeT],
                       kwarg_dict: dict[str, Any]
                       ) -> _OptionTypeT:
        ''' Consumes any valid argument from kwargs

        Arguments are applied to this option class and returned. The arguments
        are removed from the kwarg dictionary. Following three cases are
        covered:
          * the named option is one of the kwargs, like gui_options={...} or
            gui_options=GuiOptions(...)
          * any field in the dataclass as kwarg
          * any default field (mutable, stored, loaded) as kwarg, like
            gui_options_mutable or gui_options_stored
        '''
        named_option_kwarg = cls._get_kwarg_from_named_option(kwarg_dict)
        normal_kwarg = cls._get_normal_kwarg(kwarg_dict)
        # merge the three dictionaries and apply to constructor - last update
        # takes precedence and reverse order as in kwarg retrieval applies.
        normal_kwarg.update(named_option_kwarg)
        # need to handle a setting of _mutable after applying all other
        # options:
        if 'options_mutable' in normal_kwarg:
            mutable = normal_kwarg['options_mutable']
            normal_kwarg.pop('options_mutable')
            options = cls(**normal_kwarg)
            options.options_mutable = mutable
            return options
        return cls(**normal_kwarg)

    def new_update_from_kwarg(
            self: _OptionTypeT,
            kwarg_dict: dict[str, Any]
            ) -> _OptionTypeT:
        ''' get updated option

        Arguments work the same as for new_from_kwarg().
        '''
        named_option_kwarg = self._get_kwarg_from_named_option(kwarg_dict)
        normal_kwarg = self._get_normal_kwarg(kwarg_dict)
        # merge the dictionaries and apply to constructor - last update takes
        # precedence and reverse order as in kwarg retrieval applies.
        normal_kwarg.update(named_option_kwarg)
        return replace(self, **normal_kwarg)

    @classmethod
    def _get_normal_kwarg(cls,
                          kwarg_dict: dict[str, Any]
                          ) -> dict[str, Any]:
        normal_kwarg = {key: value
                        for key, value in kwarg_dict.items()
                        if key in [field.name for field in fields(cls)]}
        for key in normal_kwarg:
            kwarg_dict.pop(key)
        return normal_kwarg

    @classmethod
    def _get_kwarg_from_named_option(cls,
                                     kwarg_dict: dict[str, Any]
                                     ) -> dict[str, Any]:
        option_name = 'options'
        if option_name in kwarg_dict:
            if isinstance(kwarg_dict[option_name], cls):
                update_dict = {field.name: kwarg_dict[option_name][field.name]
                          for field in fields(kwarg_dict[option_name])}
                kwarg_dict.pop(option_name)
            elif isinstance(kwarg_dict[option_name], dict):
                update_dict = kwarg_dict[option_name]
                kwarg_dict.pop(option_name)
            else:
                raise AttributeError(
                    f'Argument {option_name} must be {cls}, '
                    f'you provided {kwarg_dict[option_name].__class__.__name__}')
        else:
            update_dict = {}
        return update_dict

    def _get_fields_with_default_values(self) -> list[str]:
        return [field.name for field in fields(self)
                if self._is_default(field)]

    def _is_default(self, field: Field) -> bool:
        if field.default != field.default_factory:
            return getattr(self, field.name) == field.default
        if field.default_factory is not None:
            return getattr(self, field.name) == field.default_factory()
        raise TypeError(
            f'This should not happen: could not determine if field '
            f'{field.name} uses default value or not '
            f'(default: {field.default}).')


    def get_state(self) -> object:
        if self.options_export_defaults:
            attribute_mask = []
        else:
            attribute_mask = self._get_fields_with_default_values()

        return self._get_state_default(
            additional_attribute_mask=attribute_mask)
