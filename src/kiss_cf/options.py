from kiss_cf import Stateful

from dataclasses import dataclass, fields, Field, MISSING
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
    #    True during construction, construction would fail otherwise (see
    #    __setattr__)
    options_mutable: bool = True
    #  * only non-defaults may be exported via get_state - when restoring
    #    options it is adviced to reset() the options before applying the
    #    state. Includes default values in get_state() should match expected
    #    behavior more closely unless users know of this option.
    options_export_defaults: bool = True
    # Above options should typically not be exported:
    attribute_mask = Stateful.attribute_mask + ['options_mutable',
                                                'options_export_defaults']

    # Overwrite __setattr__ to apply options_mutable behavior:
    def __setattr__(self, name: str, value: Any) -> None:
        if self.options_mutable or name in ['_mutable']:
            return super().__setattr__(name, value)
        raise AttributeError(
            f'Cannot change {name} to {value}, {self.__class__} is not '
            f'mutable (_mutable=False)')

    def reset(self):
        ''' Reset options to default values '''
        for field in fields(self):
            if field.default is not MISSING:
                setattr(self, field.name, field.default)
            elif field.default_factory is not MISSING:
                setattr(self, field.name, field.default_factory())
            else: # pragma: no cover
                # this branch is should not be reachable since the dataclass
                # cannot contain options without default values after
                # AppxfOptions already defining some:
                raise TypeError(
                    f'This should not happen: neither a default value or a '
                    f'default_factors is set for field {field.name} of '
                    f'{self.__class__}')

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
        # reuse _apply_kwarg() on a default constructed options object
        options = cls()
        options._apply_kwarg(normal_kwarg)
        return options

    def update(self, **kwarg):
        ''' Update options '''
        self.update_from_kwarg(kwarg_dict=kwarg)
        self.raise_error_on_non_empty_kwarg(kwarg)

    @classmethod
    def raise_error_on_non_empty_kwarg(cls, kwarg_dict: dict[str, Any]):
        for key in kwarg_dict:
            raise AttributeError(
                f'Argument [{key}] is unknown, {cls} supports '
                f'{[field.name for field in fields(cls)] + ["options"]}.')

    def update_from_kwarg(
            self: _OptionTypeT,
            kwarg_dict: dict[str, Any]):
        ''' get updated option

        Arguments work the same as for new_from_kwarg().
        '''
        named_option_kwarg = self._get_kwarg_from_named_option(kwarg_dict)
        normal_kwarg = self._get_normal_kwarg(kwarg_dict)
        # merge the dictionaries - last update takes precedence and
        # reverse order as in kwarg retrieval applies.
        normal_kwarg.update(named_option_kwarg)
        self._apply_kwarg(normal_kwarg)

    def _apply_kwarg(self, kwarg_dict: dict[str, Any]):
        ''' Apply an already processed kwarg dictionary

        Function is used in context of new and update.
        '''
        # apply new values by enforcing usage of __setitem__, but apply any
        # change to options_mutable last:
        for key, value in kwarg_dict.items():
            if key == 'options_mutable':
                continue
            setattr(self, key, value)

        if 'options_mutable' in kwarg_dict:
            setattr(self, 'options_mutable', kwarg_dict['options_mutable'])


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
                update_dict = {field.name: getattr(kwarg_dict[option_name], field.name)
                          for field in fields(kwarg_dict[option_name])}
                kwarg_dict.pop(option_name)
            elif isinstance(kwarg_dict[option_name], dict):
                update_dict = cls._get_normal_kwarg(kwarg_dict[option_name])
                cls.raise_error_on_non_empty_kwarg(kwarg_dict[option_name])
                kwarg_dict.pop(option_name)
            else:
                raise AttributeError(
                    f'Argument {option_name} must be {cls} or '
                    f'a dictionary with valid keys, '
                    f'you provided {kwarg_dict[option_name].__class__.__name__}')
        else:
            update_dict = {}
        return update_dict

    def _get_fields_with_default_values(self) -> list[str]:
        return [field.name for field in fields(self)
                if self._is_default(field)]

    def _is_default(self, field: Field) -> bool:
        if field.default is not MISSING:
            print(f'{field.name} via normal default: {getattr(self, field.name) == field.default}')
            return getattr(self, field.name) == field.default
        elif field.default_factory is not MISSING:
            print(f'{field.name} via factory default: {getattr(self, field.name) == field.default_factory()}')
            print(f'-- {getattr(self, field.name)} versus {field.default_factory()}')
            return getattr(self, field.name) == field.default_factory()
        else: # pragma: no cover
            # this branch is should not be reachable since the dataclass
            # cannot contain options without default values after
            # AppxfOptions already defining some:
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

    # set_state needs special treatment since it will commonly be used to
    # restore an object from scratch that may have options_mutable set to
    # False:
    def set_state(self, data: object):
        self.update_from_kwarg(data)
