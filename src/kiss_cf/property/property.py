''' Provide Property Handlers

Property handlers store simple data types like strings, booleans or integers.
They add the following support for usage in applications that is mostly visible
in GUI handling or storage in human readable format:
 - accepting string inputs and convert to expected type
 - ensure validity of stored values while some properties like KissEmail may be
   initialized with an invalid empty string.
 - maintenance of GUI related properties like default visibility or masking
   (passwords)
'''
from __future__ import annotations
from abc import ABCMeta, abstractmethod
import re
import configparser
from typing import Generic, TypeVar, Type, Any


class KissPropertyError(Exception):
    ''' KissProperty handling error '''


class KissPropertyConversionError(Exception):
    ''' KissProperty conversion error

    It is used when the KissProperty is not able to validate an input or
    convert it to the base type.'''
    def __init__(self, prop_class: KissProperty[Any], value, **kwargs):
        super().__init__(**kwargs)
        # The following try/except is required since KissString accepts any
        # input converting it with str(). If that fails, the value can also not
        # be printed.
        try:
            value_str = str(value)
        # pylint: disable=bare-except
        except:  # noqa E722
            value_str = '<conversion by str() failed>'
        value_type = type(value)
        base_type = type(prop_class.get_default())
        self.message = (
            f'Cannot set value {value_str} of type {value_type} into '
            f'{prop_class.__name__}. Either the base type {base_type} '
            f'is not valid or the conversion failed.')

    def __str__(self):
        return self.message


# TODO: Update handling of GUI properties as commented in the __init__ function

# ## Registry implementation
# To simplify the usage of properties, new classes register to the base
# implementation of KissProperty such that, for example,
# KissProperty.new('email') returns a KissEmail object.


class KissPropertyMeta(type):
    ''' Meta class collecting KissProperty implementations '''
    # Mapping of types or string references to derived KissProperty classes. This
    # map is used when generating a new KissProperty without the need to import all
    # classes seperately. Note, however, that custom KissProperty implementations
    # still need to be loaded to get registered.
    type_map: dict[type | str | KissProperty[Any],
                    KissProperty[Any]] = {}

    # List of known KissProperty implementations, mainly intended for logging.
    implementation_names: list[str] = []
    implementations: list[KissProperty[Any]] = []

    @classmethod
    def _register_property_class(cls, cls_register: KissProperty[Any]):
        ''' Handle the registration of a new KissProperty '''
        # check class
        if cls_register.__name__ in cls.implementation_names:
            raise KissPropertyError(
                f'KissProperty {cls_register.__name__} is already registered.')
        # check types
        if not cls_register.get_supported_types():
            raise KissPropertyError(
                f'KissProperty {cls_register.__name__} does not return any '
                f'supported type. Consider returning at least some '
                f'[''your special type''] from get_supported_types().')
        for prop_type in cls_register.get_supported_types():
            if prop_type in cls.type_map:
                other_cls = cls.type_map[prop_type].__name__
                raise KissPropertyError(
                    f'KissProperty {cls_register.__name__} supported type '
                    f'{prop_type} is already registered for {other_cls}.'
                    )
        # check completeness of implementation:
        if cls_register.__abstractmethods__:
            raise KissPropertyError(
                f'KissProperty {cls_register.__name__} still has abstract methods: '
                f'{cls_register.__abstractmethods__} that need implementation.')
        # Adding stuff only after ALL checks
        # add class
        cls.implementation_names.append(cls_register.__name__)
        cls.implementations.append(cls_register)
        # add prop types
        cls.type_map.update({prop_type: cls_register
                        for prop_type in cls_register.get_supported_types()})


    ''' Metaclass to trigger registration of new KissProperty classes '''
    def __new__(mcs, clsname, bases, attrs):
        newclass = super().__new__(mcs, clsname, bases, attrs)
        # Register only non KissProperty classes:
        if clsname != 'KissProperty':
            mcs._register_property_class(newclass)
        return newclass


# The custom metaclass from registration and the ABC metaclass for abstract
# classes need to be merged. Note that the order actually matters. The
# __abstractmethods__ must be present when executing the KissPropertyMeta.
class _KissPropertyMetaMerged(KissPropertyMeta, ABCMeta):
    pass


# KissProperty uses the ValueType below in it's implementation to allow
# appropriate type hints.
#
# For some reason, pylint and pylance seem to get the typevar rules wrong. See
# reference:
# https://stackoverflow.com/questions/74589610/whats-pylints-typevar-name-specification
# pylint: disable=typevar-name-mismatch
_BaseTypeT = TypeVar('ValueType', bound=object)  # type: ignore


class KissProperty(Generic[_BaseTypeT], metaclass=_KissPropertyMetaMerged):
    ''' Base class for all properties

    Use KissProperty.new('str') to get matching kiss properties for known
    types. You may list types by KissProperty.get_registered_types().

    Derive from KissProperty to add custom types. You have to add:
      get_default() classmethod -- providing default values on construction of
        new values and defines the base type.
      get_supported_types() classmethod -- providing a list of the types that
        you intend to support. Those are typically strings like 'email'. If you
        support a new base type like MySpecialType, you should add this type
        directly as well.

    Dependent on the provided type, you may need to overload:
      _validate_base_type() -- where the default implementation returns
        True/False if the input matches the base type.
      _validated_conversion() -- where the default implementation returns
        (False, det_default()) indicating that no conversion is possible. You
        typically need to consider providing conversions from strings.
      to_string() -- where the default implementation will return
        str(self._value) which may not be the expected behavior.

    You do not need to provide anything else, including __init__.
    '''
    def __init__(self,
                 value: _BaseTypeT | None = None,
                 name: str = '',
                 **kwargs):
        super().__init__(**kwargs)
        if value is None:
            self._input = self.get_default()
            self._value = self.get_default()
        else:
            self._set_value(value)

        # A property may be set not being mutable which blocks any changes to
        # it.
        self.mutable = True

        # TODO: except mutable above, the ones below do only support GUI
        # handling (or not yet planned handling by console). Therefore, they
        # should be provided by the GUI implementation like:
        #   KissProperty.gui_option.get(): to get a specific or all GUI options
        #   KissProperty.gui_option.set(): to set a specific or all GUI options
        # While gui_options is an object provided by the GUI implementation.
        # Like: KissGuiItem. Overloading init functions could then alter
        # default settings for certain properties.
        #
        # Dependencies:
        #   * KissGuiItem <- KissProperty
        #   * KissGuiItemWidget <- KissGuiItem
        #
        # Conclusion: if KissProperty derives from KissGuiItem, some list of
        # KissProperties is identical to a list of KissGuiItems. The access
        # from above might now be via property setter/getter to allow
        # overloading:
        #   KissProperty.default_visibility = True

        # Name that may be used in the GUI
        self.name = name

        # A property may be hidded in normal GUI views unless explicitly
        # mentioned.
        self.default_visibility = True
        # TODO: there is no usage/implementation, yet

        # A property may be displayed, masked by asteriks:
        self.masked = False
        # TODO: Implementation in GUI is missing.

    @classmethod
    def new(cls,
            prop_type: str | type | KissProperty[Any],
            value: _BaseTypeT | None = None,
            **kwargs
            ) -> KissProperty:
        ''' Get specific KissProperty implementation by type '''
        if isinstance(prop_type, type) and issubclass(prop_type, KissProperty):
            if prop_type == KissProperty:
                raise KissPropertyError(
                    'You need to provide a derived, fully implemented class '
                    'like KissString, not KissProperty directly.')
            # Note: incomplete KissProperty implementations do not exist. They
            # are blocked upon registration.
            return prop_type(value=value, **kwargs)  # type: ignore
        if prop_type in KissPropertyMeta.type_map:
            return KissPropertyMeta.type_map[prop_type](value=value, **kwargs)
        raise KissPropertyError(
            f'Property type [{prop_type}] is unknown. Did you import the '
            f'KissProperty implementations you wanted to use? Supported are: '
            f'{KissPropertyMeta.type_map.keys()}'
        )

    # Default value that must be defined by the implementing class
    @classmethod
    @abstractmethod
    def get_default(cls) -> _BaseTypeT:
        ''' Provide default value when initializing

        This default value also sets the base type of the storage which decides
        if _validated_conversion() or _validate_base_type() is used to validate
        input.
        '''

    # Implementing class must provide it's supported types
    @classmethod
    @abstractmethod
    def get_supported_types(cls) -> list[type | str]:
        ''' Provide list of suported types

        List typically includes strings and if the KissProperty is intended for
        a specific base class like string, bool or integer, it includes also
        the base type directly.
        '''

    @property
    def input(self) -> _BaseTypeT | str:
        ''' Original input when storing a value '''
        return self._input

    @property
    def value(self) -> _BaseTypeT:
        ''' Stored value of the KissProperty (converted to base type) '''
        return self._value

    @value.setter
    def value(self, value: Any):
        if not self.mutable:
            name = '(' + self.name + ')' if self.name else '(no name)'
            raise KissPropertyError(
                f'{self.__class__.__name__}{name} is set to be not mutable.')
        self._set_value(value)

    def _set_value(self, value: Any):
        ''' Reusable implentation for value setter and __init__ '''
        base_type = type(self.get_default())
        if isinstance(value, base_type):
            # Type is OK but stil needs to be valid:
            if self.validate(value) or value == self.get_default():
                self._input = value
                # enforce base type that we do not store derived types
                self._value = base_type(value)
            else:
                raise KissPropertyConversionError(type(self), value)
        else:
            # the below line handles validity AND any possible conversion to
            # the _BaseTypeT:
            valid, _value = self._validated_conversion(value)
            if not valid:
                raise KissPropertyConversionError(type(self), value)
            self._input = value
            self._value = _value

    def validate(self, value: Any) -> bool:
        ''' Validate a string to match the KissProperty type '''
        # KissProperty implementations for string base classes will NOT
        # convert but rely on the _validate_base_type().
        if isinstance(value, type(self.get_default())):
            return self._validate_base_type(value)
        # Anything else must try a conversion
        return self._validated_conversion(value)[0]

    def _validate_base_type(self, value: _BaseTypeT) -> bool:
        ''' Validate the input of a base type

        When deriving, it's recommended to still check the expected base type.
        '''
        return isinstance(value, type(self.get_default()))

    def _validated_conversion(self, value: Any) -> tuple[bool, _BaseTypeT]:
        ''' Validate a string to match the KissProperty's expectations

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


class KissString(KissProperty[str]):
    ''' KissProperty for basic strings '''
    @classmethod
    def get_supported_types(cls) -> list[type | str]:
        return [str, 'str', 'string']

    @classmethod
    def get_default(cls):
        return ''


class KissEmail(KissString):
    ''' KissProperty for Emails'''
    # get_default() and to_string() are derived from KissString

    @classmethod
    def get_supported_types(cls) -> list[type | str]:
        return ['email', 'Email']

    def _validate_base_type(self, value: str) -> bool:
        # taken from here:
        # https://stackabuse.com/python-validate-email-address-with-regular-expressions-regex/
        regex = (r'([A-Za-z0-9]+[.-_])*'
                 r'[A-Za-z0-9]+@'
                 r'[A-Za-z0-9-]+'
                 r'(\.[A-Z|a-z]{2,})+')
        # fallback to generic regexp handling
        regex = re.compile(regex)
        if not re.fullmatch(regex, value):
            return False
        return True


class KissPassword(KissString):
    ''' KissProperty for passwords

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

    def _validate_base_type(self, value: str) -> bool:
        if self.min_length > 0 and len(value) < self.min_length:
            return False
            # TODO: Error message handling should be better the specific
            # validate should tell what exactly failed.
        return True


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
    config = configparser.ConfigParser()
    config.read_string(f'[DEFAULT]\ntest = {string}')
    try:
        if res_type == bool:
            value = config.getboolean('DEFAULT', 'test')
        if res_type == int:
            value = config.getint('DEFAULT', 'test')
        if res_type == float:
            value = config.getfloat('DEFAULT', 'test')
    except ValueError:
        return False, default
    return True, value  # type: ignore


class KissBool(KissProperty[bool]):
    ''' KissProperty for booleans '''
    @classmethod
    def get_supported_types(cls) -> list[type | str]:
        return [bool, 'bool', 'boolean']

    @classmethod
    def get_default(cls) -> bool:
        return False

    def _validated_conversion(self, value: Any) -> tuple[bool, bool]:
        if isinstance(value, str):
            return validated_conversion_configparser(value, bool,
                                                     self.get_default())
        return False, self.get_default()

    def to_string(self) -> str:
        return '1' if self._value else '0'


class KissInt(KissProperty[int]):
    ''' KissProperty for Integers '''
    @classmethod
    def get_supported_types(cls) -> list[type | str]:
        return [int, 'int', 'integer']

    @classmethod
    def get_default(cls) -> int:
        return 0

    def _validated_conversion(self, value: Any) -> tuple[bool, int]:
        if isinstance(value, str):
            return validated_conversion_configparser(value, int,
                                                     self.get_default())
        return False, self.get_default()


class KissFloat(KissProperty[float]):
    ''' KissProperty for Float '''
    @classmethod
    def get_supported_types(cls) -> list[type | str]:
        return [float, 'float']

    @classmethod
    def get_default(cls) -> float:
        return 0.0

    def _validated_conversion(self, value: Any) -> tuple[bool, float]:
        if isinstance(value, int):
            return True, float(value)
        if isinstance(value, str):
            return validated_conversion_configparser(value, float,
                                                     self.get_default())
        return False, self.get_default()
