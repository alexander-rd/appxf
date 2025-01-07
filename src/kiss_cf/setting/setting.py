''' Abstract AppxfSetting and Appxf* implementations

Settings hold simple data types like strings, booleans or integers. They add
the following support for usage in applications:
 - accepting string inputs while converting to expected base type like boolean
 - ensure validity of stored values
 - maintaining GUI related options like default visibility or masking for
   passwords
'''
from __future__ import annotations
from abc import ABCMeta, abstractmethod
from typing import Generic, TypeVar, Type, Any
from dataclasses import dataclass, fields, replace

import re
import configparser

from kiss_cf import Stateful

class AppxfSettingError(Exception):
    ''' AppxfSetting handling error '''


class AppxfSettingConversionError(Exception):
    ''' AppxfSetting conversion error

    It is used when the AppxfSetting is not able to validate an input or
    convert it to the base type.'''
    def __init__(self, setting_class: type[AppxfSetting[Any]], value, **kwargs):
        super().__init__(**kwargs)
        # The following try/except is required since AppxfString accepts any
        # input converting it with str(). If that fails, the value can also not
        # be displayed.
        try:
            value_str = str(value)
        # pylint: disable=bare-except
        except:  # noqa E722
            value_str = '<conversion by str() failed>'
        value_type = type(value)
        base_type = type(setting_class.get_default())
        self.message = (
            f'Cannot set value [{value_str}] of type {value_type} into '
            f'{setting_class.__name__}. Either the base type {base_type} '
            f'is not valid or the conversion failed.')

    def __str__(self):
        return self.message


# ## Registry implementation
# To simplify the usage of properties, new classes register to the base
# implementation of AppxfSetting such that, for example,
# AppxfSetting.new('email') returns a AppxfEmail object.

# TODO: refactoring according to ticket #16: substitute meta_class by
# __init_subclass__

class AppxfSettingMeta(type):
    ''' Meta class collecting AppxfSetting implementations '''
    # Mapping of types or string references to derived AppxfSetting classes. This
    # map is used when generating a new AppxfSetting without the need to import all
    # classes seperately. Note, however, that custom AppxfSetting implementations
    # still need to be loaded to get registered.
    type_map: dict[type | str | AppxfSetting[Any], type[AppxfSetting[Any]]] = {}
    # Settings also support setting extensions that are based on "normal" types
    # but extentding their behavior. The first example was AppxfSettingSelect
    # which defines a set of named values to select from. The base setting is
    # preserved, but limited to the named options.
    extension_map: dict[str, type[AppxfSettingExtension]] = {}

    # List of known AppxfSetting implementations, mainly intended for logging.
    implementation_names: list[str] = []
    implementations: list[type[AppxfSetting[Any]]] = []

    @classmethod
    def _register_setting_class(mcs, cls_register: type[AppxfSetting[Any]]):
        ''' Handle the registration of a new AppxfSetting '''
        # check class
        if cls_register.__name__ in mcs.implementation_names:
            raise AppxfSettingError(
                f'AppxfSetting {cls_register.__name__} is already registered.')
        # check completeness of implementation:
        if cls_register.__abstractmethods__:
            raise AppxfSettingError(
                f'AppxfSetting {cls_register.__name__} still has abstract methods: '
                f'{cls_register.__abstractmethods__} that need implementation.')
        # I cannot use issubclass to differentiate an AppxfExtension from an
        # AppxfSetting since the classes are not yet known. We rely on the
        # attribute to be existent or not.
        if getattr(cls_register, 'setting_extension', False):
            mcs._add_extension(cls_register=cls_register) # type: ignore
        else:
            mcs._add_setting(cls_register=cls_register)

    @classmethod
    def _add_setting(mcs, cls_register: type[AppxfSetting[Any]]):
        # check supported types output
        if not cls_register.get_supported_types():
            raise AppxfSettingError(
                f'AppxfSetting {cls_register.__name__} does not return any '
                f'supported type. Consider returning at least some '
                f'[''your special type''] from get_supported_types().')
        # verify that no supported type already being registered
        for setting_type in cls_register.get_supported_types():
            if setting_type in mcs.type_map:
                other_cls = mcs.type_map[setting_type].__name__
                raise AppxfSettingError(
                    f'AppxfSetting {cls_register.__name__} supported type '
                    f'{setting_type} is already registered for {other_cls}.'
                    )
        # Adding stuff only after ALL checks
        # add class
        mcs.implementation_names.append(cls_register.__name__)
        mcs.implementations.append(cls_register)
        # add setting types
        mcs.type_map.update(
            {setting_type: cls_register
             for setting_type in cls_register.get_supported_types()
             })

    @classmethod
    def _add_extension(mcs, cls_register: type[AppxfSettingExtension[Any, Any]]):
        '''Adding an extending AppxfSetting

        The existance of setting_extension is already checked when calling.
        '''
        # avoid duplicate registration of extension
        if cls_register.setting_extension in mcs.extension_map:
            raise AppxfSettingError('TODO')
        # Adding stuff only after ALL checks
        # add class
        mcs.implementation_names.append(cls_register.__name__)
        mcs.implementations.append(cls_register)
        # add extension
        mcs.extension_map[cls_register.setting_extension] = cls_register

    ''' Metaclass to trigger registration of new AppxfSetting classes '''
    def __new__(mcs, clsname, bases, attrs):
        newclass = super().__new__(mcs, clsname, bases, attrs)
        # Register only non abstract classes:
        if clsname != 'AppxfSetting' and clsname != 'AppxfSettingExtension':
            mcs._register_setting_class(newclass)
        # TODO: the check above should go against __abstractmethods__ and not
        # against plain names.
        return newclass

    @classmethod
    def get_appxf_setting(
        cls,
        requested_type: str | type,
        value: Any,
        name: str,
        **kwargs) -> AppxfSetting[Any]:
        ''' Get AppxfSetting type from string or base type

        The type may also be an AppxfSetting directly
        '''
        # Handle unfinished implementations of AppxfSettings:
        if isinstance(requested_type, type) and issubclass(requested_type, AppxfSetting):
            if requested_type.__abstractmethods__:
                raise AppxfSettingError(
                    f'You need to provide a fully implemented class like '
                    f'AppxfString. {requested_type.__name__} is not '
                    f'fully implemented')
            return requested_type(value=value, name=name)
        # requested type is now either a string or a type, before handling
        # potential AppxfSettingExtensions, we look up existing types:
        if requested_type in AppxfSettingMeta.type_map:
            return AppxfSettingMeta.type_map[requested_type](value=value, name=name)
        # now, we handle extensions which are separated by otherwise untypical
        # '::'
        if isinstance(requested_type, str) and '::' in requested_type:
            type_split = requested_type.split('::')
            # get extension type
            if type_split[0] not in cls.extension_map:
                raise AppxfSettingError(
                    f'Extention [{type_split[0]}] is unknown. '
                    f'Known are: {list(cls.extension_map.keys())}')
            extension_type = cls.extension_map[type_split[0]]
            # get base setting type
            if type_split[1] not in cls.type_map:
                raise AppxfSettingError(
                    f'Base type [{type_split[1]}] is unknown. '
                    f'Known are: {list(cls.type_map.keys())}')
            base_setting_type = cls.type_map[type_split[1]]
            extension_options = {key: val for key, val in kwargs.items() if key != 'base_setting_options'}
            base_options = kwargs['base_setting_options'] if 'base_setting_options' in kwargs else {}
            base_setting = base_setting_type(**base_options)
            if value is None:
                value = base_setting.get_default()
            return extension_type(name=name, value=value,
                                  base_setting=base_setting,
                                  **extension_options)
        raise AppxfSettingError(
            f'Setting type [{requested_type}] is unknown. Did you import the '
            f'AppxfSetting implementations you wanted to use? Supported are: '
            f'{AppxfSettingMeta.type_map.keys()}'
        )


# The custom metaclass from registration and the ABC metaclass for abstract
# classes need to be merged. Note that the order actually matters. The
# __abstractmethods__ must be present when executing the AppxfSettingMeta.
class _AppxfSettingMetaMerged(AppxfSettingMeta, ABCMeta):
    pass


# AppxfSetting uses the ValueType below in it's implementation to allow
# appropriate type hints.
_BaseTypeT = TypeVar('_BaseTypeT', bound=object)

_OptionTypeT = TypeVar('_OptionTypeT', bound='BaseSettingOption')

@dataclass(eq=False, order=False)
class BaseSettingOption(Stateful):
    ''' common class for setting options/gui_options '''
    # default settings for options:
    #  * options may be mutable (in GUI) or from application - this must be
    #    True during construction, construction will fail otherwise (see
    #    __setattr__)
    _mutable: bool = True
    #  * only non-defaults may be exported via get_state - when restoring
    #    options it is adviced to reset() the options before applying the
    #    state:
    _export_non_defaults: bool = False

    def __setattr__(self, name: str, value: Any) -> None:
        if self._mutable or name in ['_mutable']:
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
                       option_name: str,
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
        named_option_kwarg = cls._get_kwarg_from_named_option(option_name, kwarg_dict)
        normal_kwarg = cls._get_normal_kwarg(kwarg_dict)
        protected_kwarg = cls._get_protected_kwarg(option_name, kwarg_dict)
        # merge the three dictionaries and apply to constructor - last update
        # takes precedence and reverse order as in kwarg retrieval applies.
        protected_kwarg.update(normal_kwarg)
        protected_kwarg.update(named_option_kwarg)
        return cls(**protected_kwarg)

    def new_update_from_kwarg(
            self: _OptionTypeT,
            option_name: str,
            kwarg_dict: dict[str, Any]
            ) -> _OptionTypeT:
        ''' get updated option

        Arguments work the same as for new_from_kwarg().
        '''
        named_option_kwarg = self._get_kwarg_from_named_option(option_name, kwarg_dict)
        normal_kwarg = self._get_normal_kwarg(kwarg_dict)
        protected_kwarg = self._get_protected_kwarg(option_name, kwarg_dict)
        # merge the three dictionaries and apply to constructor - last update
        # takes precedence and reverse order as in kwarg retrieval applies.
        protected_kwarg.update(normal_kwarg)
        protected_kwarg.update(named_option_kwarg)
        return replace(self, **protected_kwarg)

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
                                     option_name: str,
                                     kwarg_dict: dict[str, Any]
                                     ) -> dict[str, Any]:
        if option_name in kwarg_dict:
            if isinstance(kwarg_dict[option_name], cls):
                update_dict = {field.name: kwarg_dict[option_name][field.name]
                          for field in fields(kwarg_dict[option_name])}
                kwarg_dict.pop(option_name)
            elif isinstance(kwarg_dict[option_name], dict):
                update_dict = kwarg_dict[option_name]
                kwarg_dict.pop(option_name)
            else:
                raise AppxfSettingError(
                    f'Argument {option_name} must be {cls}, '
                    f'you provided {kwarg_dict[option_name].__class__.__name__}')
        else:
            update_dict = {}
        return update_dict

    @classmethod
    def _get_protected_kwarg(cls,
                             option_name: str,
                             kwarg_dict: dict[str, Any]) -> dict[str, Any]:
        protected_kwarg = {}
        for field in fields(cls):
            option = field.name
            if not option.startswith('_'):
                continue
            this_kwarg_key = f'{option_name}{option}'
            if this_kwarg_key in kwarg_dict:
                protected_kwarg[option] = kwarg_dict[this_kwarg_key]
                kwarg_dict.pop(this_kwarg_key)
        return protected_kwarg


class AppxfSetting(Generic[_BaseTypeT], Stateful,
                   metaclass=_AppxfSettingMetaMerged):
    ''' Abstract base class for settings

    Use AppxfSetting.new('str') to get matching appxf settings for known
    types. You may list types by AppxfSetting.get_registered_types().

    Derive from AppxfSetting to add custom types. You have to add:
      get_default() classmethod -- providing default values on construction of
        new values and defines the base type.
      get_supported_types() classmethod -- providing a list of the types that
        you intend to support. Those are typically strings like 'email'. If you
        support a new base type like MySpecialType, you should add this type
        directly as well.

    Dependent on the provided type, you may need to overload:
      _validated_conversion() -- where the default implementation returns
        (False, det_default()) indicating that no conversion is possible. You
        typically need to consider providing conversions from strings.
      to_string() -- where the default implementation will return
        str(self._value) which may not be the expected behavior.

    You do not need to provide anything else, including __init__.
    '''

    # AppxfSettings includes dataclass classes for setting specific options and
    # gui_options. They are part of the class definition since a derived class
    # may also update the contained Options or GuiOptions class. The __init__
    # code will then adapt accordingly.
    @dataclass(eq=False, order=False)
    class Options(BaseSettingOption):
        ''' options for settings '''
        # Likewise to _mutable (base class), the settings need to mark whether
        # the options are stored/loaded which can be set individually for
        # options and gui_options:
        _stored: bool = False
        _loaded: bool = False
        # Note: Loading but not storing may make sense when the settings are
        # defined by an admin, users are loading them (may even change them) but
        # only the admin applies new default settings.

        # In constrast to the _mutable in the base class that determines if the
        # options are mutable, this mutable determines if the setting value is
        # mutable
        mutable: bool = True

        name: str = ''
        display_height: int = 0
        display_width: int = 0
        # TODO: "masked" (for passwords) and "visibility" whether GUI option is
        # to be displayed not yet included

    def set_option(self, **kwargs):
        ''' update options or gui_options'''
        self.options = self.options.new_update_from_kwarg('options', kwargs)
        # throw error for anything that is left over
        for key in kwargs:
            raise AppxfSettingError(
                f'Argument [{key}] is unknown, {self.__class__.__name__} '
                f'supports '
                f'for options: {[field.name for field in fields(self.options)]} and '
                f'for gui_options: {[field.name for field in fields(self.gui_options)]}')

    def __init__(self,
                 value: _BaseTypeT | None = None,
                 **kwargs):
        super().__init__()
        # consume kwargs into options/gui_options - must apply before applying
        # the value since options typically affect the validation:
        #self.options: AppxfSetting.Options = self.Options.consume_kwargs('options', kwargs)
        #self.gui_options: AppxfSetting.GuiOptions = self.GuiOptions.consume_kwargs('gui_options', kwargs)
        self.options = self.Options.new_from_kwarg('options', kwargs)
        # throw error for anything that is left over
        for key in kwargs:
            raise AppxfSettingError(
                f'Argument [{key}] is unknown, {self.__class__.__name__} '
                f'supports [value] and '
                f'for options: {[field.name for field in fields(self.options)]}.')

        if value is None:
            self._input = self.get_default()
            self._value = self.get_default()
        else:
            self._set_value(value)

    ###################/
    ## Stateful Related
    def get_state(self) -> object:
        if not self.options._stored:
            return self.input
        out: dict[str, Any] = {'value': self.input}
        if self.options._stored:
            out['options'] = self.options.get_state()
        return out

    def set_state(self, data: object):
        self.value = data

    #######################/
    ## Registry and Factory
    @classmethod
    def new(cls,
            setting_type: str | type,
            value: _BaseTypeT | None = None,
            name: str = '',
            **kwargs
            ) -> AppxfSetting:
        ''' Get specific AppxfSetting implementation by type '''
        # Behavior is more appropriate in the meta class:
        return AppxfSettingMeta.get_appxf_setting(setting_type, value, name, **kwargs)

    # Default value that must be defined by the implementing class
    @classmethod
    @abstractmethod
    def get_default(cls) -> _BaseTypeT:
        ''' Provide default value when initializing '''

    # Implementing class must provide it's supported types
    @classmethod
    @abstractmethod
    def get_supported_types(cls) -> list[type | str]:
        ''' Provide list of suported types

        List typically includes strings and if the AppxfSetting is intended for
        a specific base class like string, bool or integer, it includes also
        the base type directly.
        '''

    @property
    def input(self) -> _BaseTypeT | str:
        ''' Original input when storing a value '''
        return self._input

    @property
    def value(self) -> _BaseTypeT:
        ''' Stored value of the AppxfSetting (converted to python builtin type) '''
        return self._value

    @value.setter
    def value(self, value: Any):
        print(f'Options for {self.__class__.__name__}: {self.options}')
        if not self.options.mutable:
            name = '(' + self.options.name + ')' if self.options.name else '(no name)'
            raise AppxfSettingError(
                f'{self.__class__.__name__}{name} is set to be not mutable.')
        self._set_value(value)

    def _set_value(self, value: Any):
        ''' Reusable implentation for value setter and __init__ '''
        valid, _value = self._validated_conversion(value)
        if not valid:
            raise AppxfSettingConversionError(type(self), value)
        self._input = value
        self._value = _value

    def validate(self, value: Any) -> bool:
        ''' Validate a string to match the AppxfSetting type '''
        # There was a different implementation before with simplified
        # validation check if the base type is already matched, now we just
        # rely on the _validated_convertion.
        return self._validated_conversion(value)[0]

    # Note: neither validate nor _validated_conversion can be class methods.
    # They may rely on instance specific configurations (like in select
    # settings)

    def _validated_conversion(self, value: Any) -> tuple[bool, _BaseTypeT]:
        ''' Validate a string to match the AppxfSetting's expectations

        Shall also provide the conversion to it's base type.

        Arguments:
            string -- the string to check and convert

        Returns:
            1) The check result
            2) The converted string
        '''
        return False, self.get_default()

    def to_string(self) -> str:
        ''' Return stored value as string '''
        return str(self._value)


# Fancy: an AppxfSetting can also be extended with additional behavior. An
# AppxfExtension needs to remain generic with respect to the original base type
# (like int or str) but also with respect to the specific AppxfSetting it
# extends. To remain an AppxfSetting, it also needs to derive from
# AppxfSetting.
_BaseSettingT = TypeVar('_BaseSettingT', bound=AppxfSetting)

# TODO: refactoring according to ticket #17: aggregate AppxfSetting instead of
# deriving from it.

class AppxfSettingExtension(Generic[_BaseSettingT, _BaseTypeT], AppxfSetting[_BaseTypeT]):
    setting_extension = ''

    def __init__(self,
                 base_setting: _BaseSettingT,
                 value: _BaseTypeT | None = None,
                 **kwargs):
        # base_setting has to be available during __init__ of AppxfSetting
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
                f'base_setting input must be an AppxfSetting instance, not '
                f'just a type. You provided {base_setting}')
        self.base_setting = base_setting
        super().__init__(value=value, **kwargs)
        # also apply initial value to the base_setting - this needs to be
        # self.value since original value may be tranlated by the extension to
        # something else like SettingSelect does it
        if value is not None:
            self.base_setting.value = self.value

    # This realization only applies to instances. The class registration for
    # AppxfExtensions will not rely on get_default().
    def get_default(self) -> _BaseTypeT:
        return self.base_setting.get_default()
    # To still provide an implementaiton of the classmethod, we provide a dummy
    # implementation (which violates the assumed types)
    @classmethod
    def get_default(cls) -> _BaseTypeT:
        return None # type: ignore
    # Same applies to get_supported_types
    @classmethod
    def get_supported_types(cls) -> list[type | str]:
        return []

    @AppxfSetting.value.setter
    def value(self, value: Any):
        # first step is like in base implementation - whatever the extension does
        AppxfSetting.value.fset(self, value)  # type: ignore
        # but the result is also applied to the base_setting
        self.base_setting.value = self.value


class AppxfString(AppxfSetting[str]):
    ''' AppxfSetting for basic strings '''
    @classmethod
    def get_supported_types(cls) -> list[type | str]:
        return [str, 'str', 'string']

    @classmethod
    def get_default(cls):
        return ''

    def _validated_conversion(self, value: Any) -> tuple[bool, str]:
        if not issubclass(type(value), str):
            return False, self.get_default()
        return True, value

class AppxfEmail(AppxfString):
    ''' AppxfSetting for Emails'''
    # get_default() and to_string() are derived from AppxfString

    @classmethod
    def get_supported_types(cls) -> list[type | str]:
        return ['email', 'Email']

    def _validated_conversion(self, value: Any) -> tuple[bool, str]:
        if value == self.get_default():
            return True, value
        if not super()._validated_conversion(value)[0]:
            return False, self.get_default()
        # Check Email based on regexp, taken from here:
        # https://stackabuse.com/python-validate-email-address-with-regular-expressions-regex/
        regex = (r'([A-Za-z0-9]+[.-_])*'
                 r'[A-Za-z0-9]+@'
                 r'[A-Za-z0-9-]+'
                 r'(\.[A-Z|a-z]{2,})+')
        # fallback to generic regexp handling
        regex = re.compile(regex)
        if not re.fullmatch(regex, value):
            return False, self.get_default()
        return True, value


class AppxfPassword(AppxfString):
    ''' AppxfSetting for passwords

    Default minimum password length is 6.
    '''
    @classmethod
    def get_supported_types(cls) -> list[type | str]:
        return ['pass', 'password']

    def __init__(self,
                 min_length: int | None = None,
                 **kwargs):
        # min_length must be set before super super().__init__() since it uses
        # the validation before setting the value.
        self.min_length = 6 if min_length is None else min_length
        super().__init__(**kwargs)

        self.masked = True

    def _validated_conversion(self, value: Any) -> tuple[bool, str]:
        if value == self.get_default():
            return True, value
        if not super()._validated_conversion(value)[0]:
            return False, self.get_default()
        # only length check:
        if self.min_length > 0 and len(value) < self.min_length:
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
    return True, value # type: ignore


class AppxfBool(AppxfSetting[bool]):
    ''' AppxfSetting for booleans '''
    @classmethod
    def get_supported_types(cls) -> list[type | str]:
        return [bool, 'bool', 'boolean']

    @classmethod
    def get_default(cls) -> bool:
        return False

    def _validated_conversion(self, value: Any) -> tuple[bool, bool]:
        if (issubclass(type(value), bool) or
            issubclass(type(value), int) or
            issubclass(type(value), float)):
            return True, bool(value)
        if isinstance(value, str):
            return validated_conversion_configparser(value, bool,
                                                     self.get_default())
        return False, self.get_default()

    def to_string(self) -> str:
        return '1' if self._value else '0'


class AppxfInt(AppxfSetting[int]):
    ''' AppxfSetting for Integers '''
    @classmethod
    def get_supported_types(cls) -> list[type | str]:
        return [int, 'int', 'integer']

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


class AppxfFloat(AppxfSetting[float]):
    ''' AppxfSetting for Float '''
    @classmethod
    def get_supported_types(cls) -> list[type | str]:
        return [float, 'float']

    @classmethod
    def get_default(cls) -> float:
        return 0.0

    def _validated_conversion(self, value: Any) -> tuple[bool, float]:
        if (issubclass(type(value), float) or
            issubclass(type(value), int)):
            return True, float(value)
        if isinstance(value, str):
            return validated_conversion_configparser(value, float,
                                                     self.get_default())
        return False, self.get_default()
