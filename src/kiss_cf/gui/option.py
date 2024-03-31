
import re
import configparser
from typing import Union

from kiss_cf.logging import logging


class KissOptionPropertyError(Exception):
    ''' OptionProperties related error '''


_OptionBaseType = Union[str, bool, int]


# TODO: extend to passwords to control "stars" during entry. Or add property
# "masked".

# TODO (low prio): extend to floats.

class KissOption():
    '''Collect option configuration.

    Placeholder for more functionality like input validation.
    '''
    log = logging.getLogger(__name__ + '.OptionProperties')

    setting_list = ['type', 'configurable']

    type_list = ['str', 'email', 'Email',
                 'bool', 'boolean',
                 'int']

    base_types = _OptionBaseType

    def __init__(self, type='str'):
        self._verify_type(type)
        self._type = type
        self._configurable = True

    @property
    def type(self) -> str:
        ''' Type of the option

        Affects the behavior of validate(), to_string() and to_value()
        '''
        return self._type

    @property
    def configurable(self) -> bool:
        ''' Option is configurable

        A value of False shall hide the option in GUI's.
        '''
        return self._configurable

    @classmethod
    def _verify_type(cls, type):
        if type not in cls.type_list:
            raise KissOptionPropertyError(
                f'Option type {type} is unknown. '
                f'Known types are {cls.type_list}'
                )

    @classmethod
    def _verify_setting(cls, setting):
        if setting not in cls.setting_list:
            raise KissOptionPropertyError(
                f'Setting {setting} is unknown. '
                f'Known settings are {cls.setting_list}')

    def set(self, **kwargs):
        ''' Set an option '''
        # type
        this_type = kwargs.get('type', self._type)
        self._verify_type(this_type)
        self._type = this_type
        # configurable
        self._configurable = kwargs.get('configurable', self._configurable)
        # in case of unknown settings
        for setting in kwargs:
            self._verify_setting(setting)

    def __str__(self):
        confstring = ('configurable' if self._configurable
                      else 'not configurable')
        return f'type: {self._type}, {confstring}'

    def validate(self, string: str) -> bool:
        return self._validate_string(string)[0]

    def _validate_string(
            self,
            string: str
            ) -> tuple[bool, _OptionBaseType | None]:
        ''' Validate string against type '''
        if self._type in ['str', 'string']:
            # string input is always "as is"
            return True, string
        if self._type in ['email', 'Email']:
            # taken from here:
            # https://stackabuse.com/python-validate-email-address-with-regular-expressions-regex/
            regex = (r'([A-Za-z0-9]+[.-_])*'
                     r'[A-Za-z0-9]+@'
                     r'[A-Za-z0-9-]+'
                     r'(\.[A-Z|a-z]{2,})+')
            # fallback to generic regexp handling
        elif self._type in ['bool', 'boolean']:
            config = configparser.ConfigParser()
            config.read_string(f'[DEFAULT]\ntest = {string}')
            try:
                value = config.getboolean('DEFAULT', 'test')
            except Exception:
                # this is validation only, failures are expected as normal
                # behavior. This should also not log since it would spam.
                return False, None
            return True, value
        elif self._type in ['int']:
            config = configparser.ConfigParser()
            config.read_string(f'[DEFAULT]\ntest = {string}')
            try:
                value = config.getint('DEFAULT', 'test')
            except Exception:
                # this is validation only, failures are expected as normal
                # behavior. This should also not log since it would spam.
                return False, None
            return True, value
        else:
            raise KissOptionPropertyError(
                f'Option was set to type "{self._type}". '
                f'This should not have been possible.')

        regex = re.compile(regex)
        return (True if re.fullmatch(regex, string) else False), string

    def to_string(self, value: _OptionBaseType) -> str:
        ''' convert value to string according to type

        If the value is already a string, it just validates it.
        '''
        if isinstance(value, str):
            self._validate_string(value)
            return value
        if isinstance(value, bool) and self._type in ['bool', 'boolean']:
            # Using 1/0 to avoid language dependency
            return '1' if value else '0'
        if isinstance(value, int) and self._type in ['int']:
            return str(value)
        raise KissOptionPropertyError(
            f'Provided value of type {type(value)} does not match configured '
            f'type: {self._type}')

    def to_value(self, string) -> _OptionBaseType:
        ''' convert string to value according to type

        If the input string is already of the right type, it just returns the
        input.
        '''
        # Handle already fitting types:
        if ((
                isinstance(string, bool) and self._type in ['bool', 'boolean']
                ) or (
                isinstance(string, int) and self._type in ['int'])):
            return string
        # Catch non-matching input type
        if not isinstance(string, str):
            raise KissOptionPropertyError(
                f'Input type {type(string)} cannot be converted.')
        # TODO: reconsider where to put this type check - here or within
        # _validate_string()
        valid, value = self._validate_string(string)
        if not valid or value is None:
            raise KissOptionPropertyError(
                f'Cannot convert "{string}" for type {self._type}')
        return value
