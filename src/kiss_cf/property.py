''' Provide property handlers.

The property classes here are defined with:
 - a validation function
 - bools/integers accept string inputs (as per configparser)
 - if invalid values are stored, it will return default values
   matching the expected type ('', 0, False)

To be clarified: handling of GUI options
'''
import re
import configparser

# DEBUG code:
# from . import logging
#
# logging.console_handler.setFormatter(logging.file_formatter)
# log = logging.getLogger(__name__)


# TODO: backup() and restore() property values


class KissProperty():
    ''' Base class for all properties

    The GUI will rely on this interface.
    '''

    def __init__(self, **kwargs):
        self.mutable = True
        self.valid = False
        self._value = None
        self._backup = None
        self._default = None
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
    def value(self):
        # log.debug(f'{self}')
        if self.valid:
            return self._value
        else:
            return self._default

    @value.setter
    def value(self, value):
        if self.validate(value):
            self._value = value
            self.valid = True

    @staticmethod
    def validate(value):
        return False

    def backup(self):
        self._backup = self._value

    def restore(self):
        self._value = self._backup


class KissString(KissProperty):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._default = ''

    @staticmethod
    def validate(value):
        if isinstance(value, str):
            return True
        else:
            return False


class KissEmail(KissString):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._default = ''

    @staticmethod
    def validate(value):
        if not KissString.validate(value):
            return False
        # taken from here:
        # https://stackabuse.com/python-validate-email-address-with-regular-expressions-regex/
        regex = (r'([A-Za-z0-9]+[.-_])*'
                 r'[A-Za-z0-9]+@'
                 r'[A-Za-z0-9-]+'
                 r'(\.[A-Z|a-z]{2,})+')
        # fallback to generic regexp handling
        regex = re.compile(regex)
        return (True if re.fullmatch(regex, value) else False)


class KissBool(KissProperty):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._default = False

    @staticmethod
    def validate(value):
        # log.debug(f'{value}: {value.__class__}')

        # checking for bool in this way and not via isinstance(value, bool)
        # because integer 0/1 are also True/False:
        if value in [False, True]:
            return True
        elif isinstance(value, str):
            config = configparser.ConfigParser()
            config.read_string(f'[DEFAULT]\ntest = {value}')
            try:
                config.getboolean('DEFAULT', 'test')
            except Exception:
                # this is validation only, failures are expected as normal
                # behavior. This should also not log since it would spam.
                return False
            return True
        else:
            return False
