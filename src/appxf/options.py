''' Implementation of Options class '''

from __future__ import annotations
from collections import OrderedDict
from dataclasses import dataclass, fields, Field, MISSING
from typing import Any, TypeVar, Type

from appxf import Stateful


# This TypeVar is required for correct type hints when using new_from_kwarg().
# The resulting Options object must be of the derived Options class to contain
# the expected options.
_OptionTypeT = TypeVar('_OptionTypeT', bound='Options')


@dataclass(eq=False, order=False)
class Options(Stateful):
    ''' implementation helper for options

    Base class implementation for option handling of classes, consuming kwarg's
    during construction via new_from_kwarg(). Also allows a reset to defaults
    via reset(). Furthermore, it's based on Stateful and the default
    get_state() implementation with an added option to not export options that
    have their default value set.
    '''

    # Options does not include any default options. It includes only behavior.

    # #################
    # User Interfaces
    # /

    # __init__ is provided by dataclass

    @classmethod
    def new_from_kwarg(cls: Type[_OptionTypeT],
                       kwarg_dict: dict[str, Any]
                       ) -> _OptionTypeT:
        ''' consume any valid argument from kwargs and return options instance

        Arguments that are matching fields are applied to this option class and
        a new instance is returned. The arguments are removed from kwarg_dict.

        An argument "options" can also be used to directly pass a constructed
        Options object or dictionary of key/value pairs.
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

    @classmethod
    def new(cls: Type[_OptionTypeT], **kwarg) -> _OptionTypeT:
        ''' new options from kwarg

        Calls new_from_kwarg() followed by raise_error_on_non_empty_kwarg().
        See those functions for details.
        '''
        out = cls.new_from_kwarg(kwarg_dict=kwarg)
        cls.raise_error_on_non_empty_kwarg(kwarg)
        return out

    def update_from_kwarg(self, kwarg_dict: dict[str, Any]):
        ''' get updated option

        Arguments work the same as for new_from_kwarg().
        '''
        named_option_kwarg = self._get_kwarg_from_named_option(kwarg_dict)
        normal_kwarg = self._get_normal_kwarg(kwarg_dict)
        # merge the dictionaries - last update takes precedence and
        # reverse order as in kwarg retrieval applies.
        normal_kwarg.update(named_option_kwarg)
        self._apply_kwarg(normal_kwarg)

    def update(self, **kwarg):
        ''' update options

        See update_from_kwarg. This function also calls
        raise_error_on_non_empty_kwarg afterwards.
        '''
        self.update_from_kwarg(kwarg_dict=kwarg)
        self.raise_error_on_non_empty_kwarg(kwarg)

    def reset(self):
        ''' reset options to default values '''
        for field in fields(self):
            if field.default is not MISSING:
                setattr(self, field.name, field.default)
            elif field.default_factory is not MISSING:
                setattr(self, field.name, field.default_factory())
            else:  # pragma: no cover
                # this branch is should not be reachable since the dataclass
                # cannot contain options without default values after Options
                # already defining some:
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

    # #####################
    # Internal Functions and Helpers
    # /
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
        options = kwarg_dict.pop('options', None)
        if options is not None:
            if isinstance(options, cls):
                update_dict = {
                    field.name: getattr(options, field.name)
                    for field in fields(options)}
            elif isinstance(options, dict):
                update_dict = cls._get_normal_kwarg(options)
                cls.raise_error_on_non_empty_kwarg(options)
            else:
                raise AttributeError(
                    f'Argument options must be {cls} or '
                    f'a dictionary with valid keys, you provided '
                    f'{options.__class__.__name__}')
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
        else:  # pragma: no cover
            # this branch is should not be reachable since the dataclass cannot
            # contain options without default values after Options already
            # defining some:
            raise TypeError(
                f'This should not happen: could not determine if field '
                f'{field.name} uses default value or not '
                f'(default: {field.default}).')

    # ##########################
    # adjust Stateful behavior
    # /

    # get_state needs to handle the export_defaults parameter which runs via
    # the attribute_mask:
    def get_state(self, **kwarg) -> OrderedDict[str, Any]:
        export_defaults = kwarg.pop('export_defaults', True)
        attribute_mask = kwarg.pop(
            'attribute_mask', self.attribute_mask.copy())

        if not export_defaults:
            attribute_mask += self._get_fields_with_default_values()

        # note: attributes option is just forwarded as part of **kwarg
        return self._get_state_default(attribute_mask=attribute_mask, **kwarg)

    # handle set_state() input like direct updates to ensure same behavior it
    # this may be updated in future:
    def set_state(self, data: dict[str, Any], **kwarg):
        self.update_from_kwarg(data)
