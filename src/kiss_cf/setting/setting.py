''' Abstract Setting and Setting* implementations

Settings hold simple data types like strings, booleans or integers. They add
the following support for usage in applications:
 - accepting string inputs while converting to expected base type like boolean
 - ensure validity of stored values
 - maintaining GUI related options like default visibility or masking for
   passwords
'''
from __future__ import annotations
from abc import ABCMeta, abstractmethod
from collections import OrderedDict
from typing import Generic, TypeVar, Any
from dataclasses import dataclass

from kiss_cf import Stateful, Options


class AppxfSettingError(Exception):
    ''' AppxfSetting handling error '''


class AppxfSettingConversionError(Exception):
    ''' AppxfSetting conversion error

    It is used when the Setting is not able to validate an input or convert it
    to the base type.'''
    def __init__(self, setting_class: type[Setting[Any]], value, **kwargs):
        super().__init__(**kwargs)
        # The following try/except is required since SettingString accepts any
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
# implementation of Setting such that, for example, Setting.new('email')
# returns a SettingEmail object.

# TODO: refactoring according to ticket #16: substitute meta_class by
# __init_subclass__

class _SettingMeta(type):
    ''' Meta class collecting Setting implementations '''
    # Mapping of types or string references to derived Setting classes. This
    # map is used when generating a new Setting without the need to import all
    # classes seperately. Note, however, that custom Setting implementations
    # still need to be loaded to get registered.
    type_map: dict[type | str | Setting[Any], type[Setting[Any]]] = {}
    # Settings also support setting extensions that are based on "normal" types
    # but extentding their behavior. The first example was SettingSelect
    # which defines a set of named values to select from. The base setting is
    # preserved, but limited to the named options.
    extension_map: dict[str, type(Setting)] = {}
    # TODO: the above is not fully correct, the referenced type should be
    # SettingExtension but this was moved in separate module. However, this
    # concept is also to be reworked by #17.

    # List of known Setting implementations, mainly intended for logging.
    implementation_names: list[str] = []
    implementations: list[type[Setting[Any]]] = []

    @classmethod
    def _register_setting_class(mcs, cls_register: type[Setting[Any]]):
        ''' Handle the registration of a new Setting '''
        # check class
        if cls_register.__name__ in mcs.implementation_names:
            raise AppxfSettingError(
                f'Setting {cls_register.__name__} is already registered.')
        # check completeness of implementation:
        if cls_register.__abstractmethods__:
            raise AppxfSettingError(
                f'Setting {cls_register.__name__} still has abstract methods: '
                f'{cls_register.__abstractmethods__} '
                f'that need implementation.')
        # I cannot use issubclass to differentiate an SettingExtension from an
        # Setting since the classes are not yet known. We rely on the attribute
        # to be existent or not.
        if getattr(cls_register, 'setting_extension', False):
            mcs._add_extension(cls_register=cls_register)  # type: ignore
        else:
            mcs._add_setting(cls_register=cls_register)

    @classmethod
    def _add_setting(mcs, cls_register: type[Setting[Any]]):
        # check supported types output
        if not cls_register.get_supported_types():
            raise AppxfSettingError(
                f'Setting {cls_register.__name__} does not return any '
                f'supported type. Consider returning at least some '
                f'[''your special type''] from get_supported_types().')
        # verify that no supported type already being registered
        for setting_type in cls_register.get_supported_types():
            if setting_type in mcs.type_map:
                other_cls = mcs.type_map[setting_type].__name__
                raise AppxfSettingError(
                    f'Setting {cls_register.__name__} supported type '
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
    def _add_extension(mcs, cls_register: type[SettingExtension[Any, Any]]):
        '''Adding an extending Setting

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
        if clsname != 'Setting' and clsname != 'SettingExtension':
            mcs._register_setting_class(newclass)
        # TODO: the check above should go against __abstractmethods__ and not
        # against plain names.
        return newclass

    @classmethod
    def get_setting(
            cls,
            requested_type: str | type,
            value: Any,
            name: str,
            **kwargs) -> Setting[Any]:
        ''' Get Setting type from string or base type

        The type may also be an Setting directly
        '''
        # Handle unfinished implementations of Settings:
        if (
            isinstance(requested_type, type) and
            issubclass(requested_type, Setting)
        ):
            if requested_type.__abstractmethods__:
                raise AppxfSettingError(
                    f'You need to provide a fully implemented class like '
                    f'SettingString. {requested_type.__name__} is not '
                    f'fully implemented')
            return requested_type(value=value, name=name, **kwargs)
        # requested type is now either a string or a type, before handling
        # potential SettingExtensions, we look up existing types:
        if requested_type in _SettingMeta.type_map:
            return _SettingMeta.type_map[requested_type](
                value=value, name=name, **kwargs)
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
            extension_options = {
                key: val for key, val in kwargs.items()
                if key != 'base_setting_options'}
            base_options = (kwargs['base_setting_options']
                            if 'base_setting_options' in kwargs
                            else {})
            base_setting = base_setting_type(**base_options)
            if value is None:
                value = base_setting.get_default()
            return extension_type(name=name, value=value,
                                  base_setting=base_setting,
                                  **extension_options)
        raise AppxfSettingError(
            f'Setting type [{requested_type}] is unknown. Did you import the '
            f'Setting implementations you wanted to use? Supported are: '
            f'{_SettingMeta.type_map.keys()}'
        )


# The custom metaclass from registration and the ABC metaclass for abstract
# classes need to be merged. Note that the order actually matters. The
# __abstractmethods__ must be present when executing the _SettingMeta.
class _SettingMetaMerged(_SettingMeta, ABCMeta):
    pass


@dataclass
class SettingExportOptions(Options):
    ''' Options used for get_state() and set_state() '''
    # There is no option to control whether the value is exported.
    #
    # The name is typically maintained by whoever holds the setting object
    # but could be exported if necessary:
    name: bool = False
    # The type of the setting is relevant in context of a configurable
    # configuration where a JSON file defines a set of variables
    # copmletely. This value cannot be restored via get_state() and usage
    # is not implemented, yet.
    type: bool = False
    # The value options is anything that influences the input handling to
    # the setting (validity) or the default value (which also influences
    # validity).
    value_options: bool = False
    # Display options only affect how the setting would be displayed in the
    # GUI.
    display_options: bool = False
    # Control options influence the setting behavior on whether the value (or
    # options) are mutable. The mutable parts are typically reflected in
    # available GUI elements. They may also affect other behavior of the
    # setting which mostly applies to ExtendedSettings.
    control_options: bool = False
    # Exporting default values (like in Options)
    export_defaults: bool = False


# Settings includes dataclass classes for setting specific options and
# gui_options. They are part of the class definition since a derived class
# may also update the contained Options or GuiOptions class. The __init__
# code will then adapt accordingly.
@dataclass(eq=False, order=False)
class SettingOptions(Options):
    ''' options for settings '''
    # Overwrite default values
    options_mutable: bool = True  # must remain true!
    # options for settings define export groups for which the mutable
    # behavior can be controlled separately
    value_options_mutable: bool = False
    display_options_mutable: bool = False
    control_options_mutable: bool = False
    # While the following is for the value itself:
    mutable: bool = True

    # The export groups are defined below together with
    # get_state()/set_state()

    # TODO: the mutable settings above have not yet any blocking effect!

    # name must be maintained with the setting, mainly to handle the
    # display - it is not a display setting, however (has it's own export
    # group)
    name: str = ''
    display_width: int = 0

    # the attribute/attribute_mask concept is not taken over from Options
    # since a more specific concept is needed which options to export -
    # export groups are defined to which the fields are added - any field
    # not in an export group cannot be exported (except name)
    value_options = []
    display_options = ['display_width']
    control_options = ['mutable', 'value_options_mutable',
                       'display_options_mutable', 'control_options_mutable',
                       ]

    # with overwriting the get_state()/set_state(), the Stateful class
    # configuration for attribute/attribute_mask doe not need to be
    # changed.
    def get_state(self,
                  options: SettingExportOptions = SettingExportOptions(),
                  **kwargs) -> OrderedDict[str, Any]:
        attributes = (
            (self.value_options if options.value_options else []) +
            (self.display_options if options.display_options else []) +
            (self.control_options if options.control_options else []))
        if options.name:
            attributes += ['name']
        return super().get_state(
            attributes=attributes,
            attribute_mask=[],
            export_defaults=options.export_defaults,
            **kwargs)

    def set_state(self,
                  data: object,
                  options: SettingExportOptions = SettingExportOptions(),
                  **kwargs):
        attributes = (self.value_options if options.value_options else [] +
                      self.display_options if options.display_options else [] +
                      self.control_options if options.control_options else [])
        return self._set_state_default(data=data,
                                       attributes=attributes,
                                       attribute_mask=[],
                                       **kwargs)


# Setting uses the ValueType below in it's implementation to allow appropriate
# type hints.
_BaseTypeT = TypeVar('_BaseTypeT', bound=object)


class Setting(Generic[_BaseTypeT], Stateful,
              metaclass=_SettingMetaMerged):
    ''' Abstract base class for settings

    Use Setting.new('str') to get matching appxf settings for known types. You
    may list types by Setting.get_registered_types().

    Derive from Setting to add custom types. You have to add:
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
    # Bring ExportOptions and Options directly in scope of the setting class
    # such that those options are always available.
    ExportOptions = SettingExportOptions
    Options = SettingOptions

    def __init__(self,
                 value: _BaseTypeT | None = None,
                 **kwargs):
        super().__init__()
        # consume kwargs into options/gui_options - must apply before applying
        # the value since options typically affect the validation:
        self.options = self.Options.new_from_kwarg(kwargs)
        # throw error for anything that is left over
        self.options.raise_error_on_non_empty_kwarg(kwargs)

        if value is None:
            self._input = self.get_default()
            self._value = self.get_default()
        else:
            self._set_value(value)

    # ##################
    # Stateful Related
    # /
    def get_state(self, **kwarg) -> object:
        export_options = self.ExportOptions.new_from_kwarg(kwarg)
        self.ExportOptions.raise_error_on_non_empty_kwarg(kwarg)

        # Strategy is to fill a dict from the various flags and if this dict
        # remained empty, only the value is returned
        option_list = []
        if export_options.name:
            option_list += ['name']
        if export_options.type:
            raise TypeError('Exporting the type is not yet supported')
        options: OrderedDict = self.options.get_state(options=export_options)
        if not options:
            return self.input
        out = OrderedDict({'value': self.input})
        out.update(options)
        return out

    def set_state(self, data: object, **kwarg):
        if isinstance(data, dict):
            self.options.update_from_kwarg(kwarg_dict=data)
            self.value = data['value']
        else:
            self.value = data

    # #####################/
    #  Registry and Factory
    # /
    @classmethod
    def new(cls,
            setting_type: str | type,
            value: _BaseTypeT | None = None,
            name: str = '',
            **kwargs
            ) -> Setting:
        ''' Get specific Setting implementation by type '''
        # Behavior is more appropriate in the meta class:
        return _SettingMeta.get_setting(setting_type, value, name, **kwargs)

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

        List typically includes strings and if the Setting is intended for a
        specific base class like string, bool or integer, it includes also the
        base type directly.
        '''

    @property
    def input(self) -> _BaseTypeT | str:
        ''' Original input when storing a value '''
        return self._input

    @property
    def value(self) -> _BaseTypeT:
        ''' Stored value of the Setting (converted to python builtin type) '''
        return self._value

    @value.setter
    def value(self, value: Any):
        if not self.options.mutable:
            name = ('(' + self.options.name + ')'
                    if self.options.name
                    else '(no name)')
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
        ''' Validate a string to match the Setting type '''
        # There was a different implementation before with simplified
        # validation check if the base type is already matched, now we just
        # rely on the _validated_convertion.
        return self._validated_conversion(value)[0]

    # Note: neither validate nor _validated_conversion can be class methods.
    # They may rely on instance specific configurations (like in select
    # settings)

    def _validated_conversion(self, value: Any) -> tuple[bool, _BaseTypeT]:
        ''' Validate a string to match the Setting's expectations

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
