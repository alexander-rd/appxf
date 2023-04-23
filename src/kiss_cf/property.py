''' Provide property handlers.

The property classes here are defined with:
 - bools/integers accept string inputs (as per configparser)
 - KissProperty.vlue always returns the expected type
 - invalid values cannot be stored (will result in an exception) note however
   that KissEmail, for example, starts as invalid
 - a static function unify_value() can be used for conversions without
   constructing a KissProperty object

To be clarified: handling of GUI options
'''
import re
import configparser
from typing import Generic, TypeVar

# DEBUG code:
# from . import logging
#
# logging.console_handler.setFormatter(logging.file_formatter)
# log = logging.getLogger(__name__)

# TODO: review the whole thing and settle things with documentation, perhaps
# together with substituting the stuff in config

ValueType = TypeVar('ValueType', bound=object)


class KissProperty(Generic[ValueType]):
    ''' Base class for all properties

    The GUI will rely on this interface.
    '''

    def __init__(self, default: ValueType, **kwargs):
        self.mutable = True
        self.valid = False
        self._value = default
        self._default = default
        self._backup = default
        # the following line updates _value valid
        self.value = default

        self.set(**kwargs)

    def set(self, **kwargs):
        self.mutable = kwargs.get('mutable', self.mutable)

    def __str__(self):
        mutablestr = ('mutable' if self.mutable
                      else 'not mutable')
        validstr = '(valid)' if self.valid else '(invalid)'
        return (f'{mutablestr} {self.__class__.__name__}: '
                f'{self._value} {validstr}')

    @property
    def value(self) -> ValueType:
        # log.debug(f'{self}')
        return self._value

    @value.setter
    def value(self, value: ValueType):
        try:
            self._value = self.unify_value(value)
            self.valid = True
        except Exception:
            # If we cannot get a proper value, we don't change the stored value
            pass

    @staticmethod
    def unify_value(value: ValueType | str) -> ValueType:
        raise Exception('KissProperty does not support unify_value. '
                        'Use one of the subclasses.')

    def backup(self):
        self._backup = self._value

    def restore(self):
        self.value = self._backup


class KissString(KissProperty[str]):
    def __init__(self, value: str = '', **kwargs):
        super().__init__(str(), **kwargs)
        self._default = ''
        self.value = value

    @staticmethod
    def unify_value(value: str) -> str:
        if isinstance(value, str):
            return value
        else:
            raise ValueError(
                f'KissString only accepts string input but got {type(value)}')


class KissEmail(KissString):
    def __init__(self, value: str = '', **kwargs):
        super().__init__(**kwargs)
        self._default = ''
        self.value = value

    @staticmethod
    def unify_value(value: str) -> str:
        value = KissString.unify_value(value)
        # taken from here:
        # https://stackabuse.com/python-validate-email-address-with-regular-expressions-regex/
        regex = (r'([A-Za-z0-9]+[.-_])*'
                 r'[A-Za-z0-9]+@'
                 r'[A-Za-z0-9-]+'
                 r'(\.[A-Z|a-z]{2,})+')
        # fallback to generic regexp handling
        regex = re.compile(regex)
        if re.fullmatch(regex, value):
            return value
        else:
            raise ValueError(f'"{value}" is not an Email')


class KissBool(KissProperty[bool]):
    def __init__(self, value: bool = False, **kwargs):
        super().__init__(bool(), **kwargs)
        self._default = False
        self.value = value

    @staticmethod
    def unify_value(value: bool) -> bool:
        # log.debug(f'{value}: {value.__class__}')

        # checking for bool in this way and not via isinstance(value, bool)
        # because integer 0/1 are also True/False:
        if value in [False, True]:
            return bool(value)
        elif isinstance(value, str):
            config = configparser.ConfigParser()
            config.read_string(f'[DEFAULT]\ntest = {value}')
            try:
                value = bool(config.getboolean('DEFAULT', 'test'))
                # log.debug(f'Result: {value}, {value.__class__}')
                return value
            except Exception:
                # this is validation only, failures are expected as normal
                # behavior. This should also not log since it would spam.
                raise ValueError(f'"{value}" cannot be intepreted as boolean.')
        else:
            raise ValueError(
                f'KissBool only accepts bool or string input '
                f'but got {type(value)}')

    @staticmethod
    def get_selection_dict(option_list: list[str], init: bool = False):
        option_dict = {option: KissBool(value=init)
                       for option in option_list}
        return option_dict
