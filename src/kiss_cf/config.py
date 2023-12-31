'''
The configuration concept is based on configparser for storage. It extends it's
usage for a generic GUI and flexible (encrypted) storage by aggregating:
 * a configparser object with
 * a dictionary of options for each section on
     * how to retreive/store the configparser object (see ConfigSection)
 * a dictionary of options for each key/value pair (see OptionConfig)
     * a dictionary of options for each configuration item in a section (see
       OptionConfig)
'''

import configparser
import pickle
import os.path
import re
import functools

from . import logging
from .security.security import Security

# TODO: Why do I use configparser at all??
#  + It's nice to load INI files (and store back to them)
#  + Everything is a string is good for tkinter Entry?? / It needs validation
#    this way or another
#
# Configparser: when setting an option, it's converted to string but should be
# validated if matching expected type. Reading must convert string to type.
#
# Dictionary: when writing, input should be velidated agains type. When this
# was guaranteed, reading becomes simple.
#  + it would theoretically allow to store complex configuration data.
#    - But for that an automatic GUI is not supported.
#
# Conclusion: looks like I should drop configparser as core data type and just
# retain it for respective sections.
#
# If configparser is valid for a section, we will need to convert to string
# before storing and convert back to types when loading. << support will be
# limited.


class ToolConfigParser(configparser.ConfigParser):
    '''Internal helper with predefined settings for ConfigParser()'''
    def __init__(self):
        # Note that we need to change the comment prefix to something else and
        # allow "no values" to keep them as keys without values. Other
        # functions must then ignore the "#" keys.
        super(ToolConfigParser, self).__init__(
            comment_prefixes='/', allow_no_value=True)
        self.optionxform = str


class OptionConfig():
    '''Collect option configuration.

    Placeholder for more functionality like input validation.
    '''
    log = logging.getLogger(__name__ + '.OptionConfig')

    def __init__(self, type='str'):
        self.type = type
        self.configurable = True

    def set(self, **kwargs):
        self.type = kwargs.get('type', self.type)
        self.configurable = kwargs.get('configurable', self.configurable)

    def __str__(self):
        confstring = ('configurable' if self.configurable
                      else 'not configurable')
        return f'type: {self.type}, {confstring}'

    def validate(self, value):
        if self.type in ['str', 'string']:
            # string input is always "as is"
            return True
        if self.type in ['email', 'Email']:
            # taken from here:
            # https://stackabuse.com/python-validate-email-address-with-regular-expressions-regex/
            regex = (r'([A-Za-z0-9]+[.-_])*'
                     r'[A-Za-z0-9]+@'
                     r'[A-Za-z0-9-]+'
                     r'(\.[A-Z|a-z]{2,})+')
            # fallback to generic regexp handling
        elif self.type in ['bool', 'boolean']:
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
            raise Exception(f'Option type "{self.type}" is unknown')

        regex = re.compile(regex)
        return (True if re.fullmatch(regex, value) else False)


class SectionConfig():
    '''Collect section configuration.

    Placeholder for more functionality like input validation.
    '''
    def __init__(self, source='', source_type='user encrypted'):
        self.source = source
        self.source_type = source_type
        self.configurable = True

    def set(self, **kwargs):
        self.source = kwargs.get('source', self.source)
        self.source_type = kwargs.get('source_type', self.source_type)
        self.configurable = kwargs.get('configurable', self.configurable)

    def __str__(self):
        confstring = ('configurable' if self.configurable
                      else 'not configurable')
        return (f'source_type: {self.source_type}, '
                f'source: {self.source}, {confstring}')


class Config():
    '''Organize configuration settings.

    This class allows to define a list of configuration settings that can be
    stored in various ways (as pickled data or as ini files) and provides a
    generic GUI to adapt the config settings.

    Internally, it is using configparser.

    The following sections are predefined:
     * USER has predetermined section settings to work together with the Login
       feature which collects those settings at app initialization and stores
       them password protected.
     * DEFAULT should not be used at all. See configparser documentation for
       details.
    '''
    log = logging.getLogger(__name__ + '.Config')

    def __init__(self, security=None, storage_dir='./data/config'):
        if security is None:
            security = Security()
        self._security = security
        self._storage_dir = storage_dir

        self.config = ToolConfigParser()
        self.config_backup = ToolConfigParser()
        self.section_config = dict()
        self.option_config = dict()
        self.language = dict()

        # Cross-cutting concerns are deeply coupled. Configuration already
        # prefills USER with expected settings. Where user USER data as part of
        # configuration is stored is business of configuration, not of login
        # (secrurity).
        self.add_section('USER')
        self.section_config['USER'].source_type = 'user encrypted'

    def __str__(self):
        outStr = ''
        for section in self.config.sections():
            if outStr:
                outStr += ', '
            outStr += section + ': ' + str(dict(self.config[section]))
        return outStr

    def set_security(self, security: Security):
        self._security = security

    def add_section(self, section):
        '''Add section if not yet existing.'''
        self.config.add_section(section)
        self.section_config[section] = SectionConfig()
        self.log.info(f'added section: {section}')

    def add_option(self, section, option, value=''):
        '''Add option if not yet existing.

        Also adds the section if not yet existing. If option already exists,
        the value will be overwritten.
        '''
        self.option_config[option] = OptionConfig()
        if section not in self.config.sections():
            self.add_section(section)
        if option not in self.config.options(section):
            self.config.set(section, option, value)
            self.option_config[option] = OptionConfig()
            self.log.info(f'added option: {option} in '
                          f'{section} with value {value}')
        else:
            self.config.set(section, option, value)
            self.log.info(f'updated option: {option} '
                          f'in {section} to {value}')

    # INI File Handling
    def add_ini_file(self, file):
        config = ToolConfigParser()
        config.read(file)

        for section in config.sections():
            if not self.config.has_section(section):
                self.config.read_dict({section: config[section]})
                self.section_config[section] = SectionConfig(
                    source=file, source_type='ini')
            else:
                self.log.warning(f'section {section} already exists, '
                                 f'ignoring from {file}')
            # ensure OptionConfig exists for each option
            for option in config.options(section):
                if option not in self.option_config.keys():
                    self.option_config[option] = OptionConfig()
                if option.startswith('#'):
                    self.option_config[option].configurable = False

    def write_ini_file(self, file='', section=''):
        # input option handling
        if (file):
            # Default input case, easy to handle
            self.log.debug('File: yes')
        elif (file and section):
            self.log.warning(
                f'Provided file name "{file}" '
                f'will have precedence over section {section}')
        elif (section):
            if (section in self.config.sections()):
                file = self.section_config[section].source
            else:
                raise Exception(
                    f'Configuration for section {section} not found')
        else:
            raise Exception(
                'Writing INI file required either the file name '
                '(as precedence) or a section that is stored in '
                'this ini file.')

        # determine affected sections
        config = ToolConfigParser()
        for section in self.config.sections():
            thissection_config = self.section_config[section]
            if (thissection_config.source_type == 'ini' and
                    thissection_config.source == file):
                config.read_dict({section: self.config[section]})
        # write config
        with open(file, 'w') as configfile:
            config.write(configfile)

    def get_section_config(self, section):
        if section in self.section_config.keys():
            return self.section_config[section]
        else:
            raise Exception(f'Section {section} does not exist')

    def set_section_config(self, section, **kwargs):
        if section not in self.section_config.keys():
            self.section_config[section] = SectionConfig(**kwargs)
        else:
            self.section_config[section].set(**kwargs)

    def set_option_config(self, option, **kwargs):
        if option not in self.option_config.keys():
            self.option_config[option] = OptionConfig(**kwargs)
        else:
            self.option_config[option].set(**kwargs)

    # TODO: get(section) is handy to quickly get the dictionary. get(section,
    # option) is also handy to directly get expected output based on config
    # options. Buuuut: a corresponding set is missing! Once this is present,
    # the fields should be private.
    def get(self, section, option=''):
        '''returns cofiguration data from a section.

        If no option is specified, it returns all options as distrionary
        '''
        if section not in self.config.sections():
            raise Exception(f'Section "{section}" does not exist.')
        elif (option) and (option not in self.config.options(section)):
            raise Exception(
                f'Section "{section}" does not have an '
                f'option "{option}"')
        elif (option):
            thisOptionType = self.option_config[option].type
            if thisOptionType in ['str', 'string', 'email', 'Email']:
                return self.config[section][option]
            elif thisOptionType == 'bool':
                try:
                    return self.config.getboolean(section, option)
                except Exception as e:
                    self.log.error(
                        f'Following error when handling section {section}, '
                        f'option {option} with type {thisOptionType}')
                    raise e
            elif thisOptionType == 'int':
                try:
                    return self.config.getint(section, option)
                except Exception as e:
                    self.log.error(
                        f'Following error when handling section {section}, '
                        f'option {option} with type {thisOptionType}')
                    raise e
            else:
                raise Exception(
                    f'Section {section}, option {option}'
                    f'has unknown type {thisOptionType}')
        else:
            # When returning the dictionary, we need to ensure that the ke
            # settings are applied. Hence, we cycle through all options and
            # build up the dictionary manually.
            return {option: self.get(section, option=option)
                    for option in self.config.options(section)}

    def backup(self):
        '''Buffer one backup of config options.

        Can be used when providing an edit option that can be aborted. On
        abort, you would simply use restore().

        Section or option configuration is not backed up.
        '''
        self.config_backup = ToolConfigParser()
        self.config_backup.read_dict(self.config)

    def restore(self):
        '''Restore buffered configuration.

        Dangerous if not used with backup()
        '''
        self.config = self.config_backup

    @staticmethod
    def apply_to_sections(section_func):
        @functools.wraps(section_func)
        def wrapper(self, section='', *args, **kwargs):
            # print(f'wrapping {section_func.__name__}')
            if not section:
                section_list = self.config.sections()
            elif isinstance(section, str):
                section_list = [section]
            elif isinstance(section, list):
                section_list = section
            else:
                raise Exception(
                    f'Called {section_func.__name__} with '
                    f'unknown type for {section}')

            for section in section_list:
                # skip DEFAULT section (not supported)
                if section == 'DEFAULT':
                    continue
                section_func(self, section)
        return wrapper

    @apply_to_sections
    def store(self, section):
        # print(f'store {section}')
        if section not in self.config.keys():
            raise Exception(
                f'Trying to store section "{section}" which does not exist')

        section_config = self.section_config[section]
        source = section_config.source
        if not source:
            source = os.path.join(self._storage_dir, section + '.dat')
        source_type = self.section_config[section].source_type

        if source_type == 'user encrypted':
            data = pickle.dumps(self.get(section))
            self._security.encrypt_to_file(data, source)
        elif source_type == 'ini':
            self.write_ini_file(section=section)
        else:
            raise Exception(f'source_type "{source_type}" is unknown.')

    @apply_to_sections
    def load(self, section):
        section_config = self.section_config[section]
        source = section_config.source
        if not source:
            source = os.path.join(self._storage_dir, section + '.dat')
        source_type = self.section_config[section].source_type

        if source_type == 'user encrypted':
            data = self._security.decrypt_from_file(source)
            data_unpickled = pickle.loads(data)
            self.config.read_dict({section: data_unpickled})
        else:
            raise Exception(f'source_type "{source_type}" is unknown.')

        self.__ensure_config_present(section)

    def __ensure_config_present(self, section=''):
        if not section:
            sectionList = self.config.sections()
        elif isinstance(section, str):
            sectionList = [section]
        else:
            sectionList = section

        for section in sectionList:
            # ensure section config
            if section not in self.section_config.keys():
                self.section_config[section] = SectionConfig()
            # ensure option config's
            for option in self.config.options(section):
                if option not in self.option_config.keys():
                    self.option_config[option] = OptionConfig()
