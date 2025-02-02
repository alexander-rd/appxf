from collections import OrderedDict
from dataclasses import dataclass, fields, Field, MISSING
from typing import Any, Type, TypeVar

from kiss_cf import Stateful

_OptionTypeT = TypeVar('_OptionTypeT', bound='AppxfOptions')

@dataclass(eq=False, order=False)
class AppxfOptions(Stateful):
    ''' maintain options for classes to aggregate from

    Base class implementation for option handling of classes, consuming kwarg's
    during construction via new_from_kwarg(). Also allows a reset to defaults
    via reset(). Furthermore, it's based on Stateful and the default
    get_state() implementation with an added option to not export options that
    have their default value set.
    '''
    # AppxfOptions does not include any default options. It includes only
    # behavior.

    ###################
    ## User Interfaces
    #/

    # __init__ is provided by dataclass

    @classmethod
    def new_from_kwarg(cls: Type[_OptionTypeT],
                       kwarg_dict: dict[str, Any]
                       ) -> _OptionTypeT:
        ''' consume any valid argument from kwargs and return options instance

        Arguments that are matching fields or "options" are applied to this
        option class and a new instance is returned. The arguments are removed
        from kwarg_dict. The "options" key supports being an options class or a
        dictionary, like: options=AppxfOption() or options={...}.
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
        ''' update options '''
        self.update_from_kwarg(kwarg_dict=kwarg)
        self.raise_error_on_non_empty_kwarg(kwarg)

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

    def reset(self):
        ''' reset options to default values '''
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
    def raise_error_on_non_empty_kwarg(cls, kwarg_dict: dict[str, Any]):
        ''' shortcut error handling

        This function is recommended after manual calls to new_from_kwargs()
        or update_from_kwargs()
        '''
        for key in kwarg_dict:
            raise AttributeError(
                f'Argument [{key}] is unknown, {cls} supports '
                f'{[field.name for field in fields(cls)] + ["options"]}.')

    ######################
    ## Internal Functions and Helpers
    #/
    def _apply_kwarg(self, kwarg_dict: dict[str, Any]):
        ''' Apply an already processed kwarg dictionary

        Function is used in context of new and update.
        '''
        # apply new values by enforcing usage of __setitem__
        for key, value in kwarg_dict.items():
            setattr(self, key, value)

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
            return getattr(self, field.name) == field.default
        elif field.default_factory is not MISSING:
            return getattr(self, field.name) == field.default_factory()
        else: # pragma: no cover
            # this branch is should not be reachable since the dataclass
            # cannot contain options without default values after
            # AppxfOptions already defining some:
            raise TypeError(
                f'This should not happen: could not determine if field '
                f'{field.name} uses default value or not '
                f'(default: {field.default}).')

    ############################
    ## adjust Stateful behavior
    #/

    # get_state needs to handle the options_export_defaults option:
    def get_state(self, **kwarg) -> object:
        export_defaults = True

        if 'export_defaults' in kwarg:
            export_defaults = kwarg['export_defaults']
            kwarg.pop('export_defaults')
        if 'attribute_mask' in kwarg:
            attribute_mask = kwarg['attribute_mask']
            kwarg.pop('attribute_mask')
        else:
            attribute_mask = self.attribute_mask.copy()

        if not export_defaults:
            attribute_mask += self._get_fields_with_default_values()

        # note: attributes option is just forwarded as part of ***kwarg
        return self._get_state_default(attribute_mask=attribute_mask, **kwarg)

    # set_state needs special treatment since it will be commonly be used to
    # restore an object from scratch that may have options_mutable set to
    # False:
    def set_state(self, data: object, **kwarg):
        self.update_from_kwarg(data) # type: ignore -- see get_sate() returning a dict
