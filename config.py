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
import tkinter
import pickle
import os.path
import re
import functools

from kiss_cf.security import Security

from .language import translate
from kiss_cf import security

# TODO: Why do I use configparser at all?? 
#  + It's nice to load INI files (and store back to them)
#  + Everything is a string is good for tkinter Entry?? / It needs validation
#    this way or another
#  
# Configparser: when setting an option, it's converted to string but should be
# validated if matching expected type. Reading must convert string to type.
#
# Dictionary: when writing, input should be velidated agains type. When this was
# guaranteed, reading becomes simple.
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
        # allow "no values" to keep them as keys without values. Other functions
        # must then ignore the "#" keys.
        super(ToolConfigParser, self).__init__(comment_prefixes='/', allow_no_value=True)
        self.optionxform = str

class OptionConfig():
    '''Collect option configuration.
    
    Placeholder for more functionality like input validation.
    '''
    def __init__(self, type = 'str'):
        self.type = type
        self.configurable = True
        
    def set(self, **kwargs):
        self.type         = kwargs.get('type'        , self.type)
        self.configurable = kwargs.get('configurable', self.configurable)
        
    def __str__(self):
        return 'type: {0}, {1}'.format(
            self.type,
            'configurable' if self.configurable else 'not configurable')
    
    def validate(self, value):
        if self.type in ['str', 'string']:
            # string input is always "as is"
            return True
        if self.type in ['email', 'Email']:
            # taken from here: https://stackabuse.com/python-validate-email-address-with-regular-expressions-regex/
            regex = r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+'
            # fallback to generic regexp handling
        elif self.type in ['bool', 'boolean']:
            config = configparser.ConfigParser()
            config.read_string('[DEFAULT]\ntest = {0}'.format(value))
            try:
                config.getboolean('DEFAULT', 'test')
            except Exception:
                return False
            return True
        else:
            raise Exception('Option type "{0}" is unknown'.format(self.type))
        
        regex = re.compile(regex)
        return (True if re.fullmatch(regex, value) else False)
        
        
class SectionConfig():
    '''Collect section configuration.
    
    Placeholder for more functionality like input validation.
    '''
    def __init__(self, source='', source_type='user encrypted'):
        self.source       = source
        self.source_type  = source_type
        self.configurable = True
        
    def set(self, **kwargs):
        self.source       = kwargs.get('source'      , self.source)
        self.source_type  = kwargs.get('source_type' , self.source_type)
        self.configurable = kwargs.get('configurable', self.configurable)
        
    def __str__(self):
        return 'source_type: {0}, source: {1}, {2}'.format(
            self.source_type, 
            self.source,
            'configurable' if self.configurable else 'not configurable')

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
    
    def __init__(self, security = Security(), storage_dir='./data/config'):
        self._security    = security
        self._storage_dir = storage_dir
        
        self.config         = ToolConfigParser()
        self.config_backup  = ToolConfigParser()
        self.section_config = dict()
        self.option_config  = dict()
        self.language       = dict()
        
        
        # Cross-cutting concerns are deeply coupled. Configuration already
        # prefills USER with expected settings. Where user USER data as part of
        # configuration is stored is business of configuration, not of login
        # (secrurity).
        self.add_section('USER')
        self.section_config['USER'].source_type = 'user encrypted'
        
    def __str__(self):
        outStr = ''
        for section in self.config.sections():
            if outStr: outStr += ', '
            outStr += section + ': ' + str(dict(self.config[section]))
        return outStr
    
    def set_security(self, security: Security):
        self._security = security        
    
    def add_section(self, section):
        '''Add section if not yet existing.'''
        self.config.add_section(section)
        self.section_config[section] = SectionConfig()
        print('added section: {0}'.format(section))
        
    def add_option(self, section, option, value=''):
        '''Add option if not yet existing.
        
        Also adds the section if not yet existing. If option already exists, the
        value will be overwritten.
        '''
        self.option_config[option] = OptionConfig()
        if not section in self.config.sections():
            self.add_section(section)
        if not option in self.config.options(section):
            self.config.set(section, option, value)
            self.option_config[option] = OptionConfig()
            print('added option: {0} in {1}'.format(option, section, value))
        else:
            self.config.set(section, option, value)
            print('updated option: {0} in {1}'.format(option, section, value))
        
    # INI File Handling
    def add_ini_file(self, file):
        config = ToolConfigParser()
        config.read(file)

        for section in config.sections():
            if not self.config.has_section(section):
                self.config.read_dict({section: config[section]})
                self.section_config[section] = SectionConfig(source=file, source_type='ini')
            else:
                print('WARN: section {0} already exists, ignoring from {1}'.format(section, file))
            # ensure OptionConfig exists for each option
            for option in config.options(section):
                if not option in self.option_config.keys():
                    self.option_config[option] = OptionConfig()
                if option.startswith('#'):
                    self.option_config[option].configurable = False
                
    def write_ini_file(self, file='', section=''):
        # input option handling
        if (file):
            # Default input case, easy to handle
            print('File: yes')
        elif (file and section):
            print('Warning: Provided file name "{0}" will have precedence over section {1}'.format(file, section))
        elif (section):
            if (section in self.config.sections()):
                file = self.section_config[section].source
            else:
                raise Exception('Configuration for section {0} not found'.format(section))
        else:
            raise Exception('Writing INI file required either the file name (as precedence) or a section that is stored in this ini file.')
        
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
            raise Exception('Section {0} does not exist'.format(section))
        
    def set_section_config(self, section, **kwargs):
        if not section in self.section_config.keys():
            self.section_config[section] = SectionConfig(**kwargs)
        else:
            self.section_config[section].set(**kwargs)
        
    def set_option_config(self, option, **kwargs):
        if not option in self.option_config.keys():
            self.option_config[option] = OptionConfig(**kwargs)
        else:
            self.option_config[option].set(**kwargs)
    
    # TODO: get(section) is handy to quickly get the dictionary. get(section,
    # option) is also handy to directly get expected output based on config
    # options. Buuuut: a corresponding set is missing! Once this is present, the
    # fields should be private.
    def get(self, section, option=''):
        '''returns cofiguration data from a section. If no option is specified, it
        returns all options as distrionary'''
        if section not in self.config.sections():
            raise Exception('Section "{0}" does not exist.'.format(section))
        elif (option) and (option not in self.config.options(section)):
            raise Exception('Section "{0}" does not have an option "{1}"'.format(section, option))
        elif (option):
            thisOptionType = self.option_config[option].type
            if thisOptionType in ['str', 'string', 'email', 'Email']:
                return self.config[section][option]
            elif thisOptionType == 'bool':
                try:
                    return self.config.getboolean(section, option)
                except Exception as e:
                    print('Following error when handling section {0}, option {1} with type {2}'.format(
                        section, option, thisOptionType))
                    raise e
            elif thisOptionType == 'int':
                try:
                    return self.config.getint(section, option)
                except Exception as e:
                    print('Following error when handling section {0}, option {1} with type {2}'.format(
                        section, option, thisOptionType))
                    raise e
            else:
                raise Exception('Section {0}, option {1} has unknown type {2}'.format(
                    section, option, thisOptionType
                ))
        else:
            # When returning the dictionary, we need to ensure that the ke
            # settings are applied. Hence, we cycle through all options and build
            # up the dictionary manually.
            return {option: self.get(section, option=option) 
                    for option in self.config.options(section)}
         
    def backup(self):
        '''Buffer one backup of config options.
        
        Can be used when providing an edit option that can be aborted. On abort,
        you would simply use restore().
        
        Section or option configuration is not backed up.
        '''
        self.config_backup = ToolConfigParser()
        self.config_backup.read_dict(self.config)
        
    def restore(self):
        '''Restore buffered configuration.
        
        Dangerous if not used with backup()
        '''
        self.config = self.config_backup
     
     
    def apply_to_sections(section_func):
        @functools.wraps(section_func)
        def wrapper(self, section = '', *args, **kwargs):
            #print('wrapping {0}'.format(section_func.__name__))
            if not section:
                section_list = self.config.sections()
            elif type(section) == str:
                section_list = [section]
            elif type(section_list) == list:
                section_list = section_list
            else:
                raise Exception('Called {0} with unknown type for {1}'.format(section_func.__name__, section))
            
            for section in section_list:
                # skip DEFAULT section (not supported)
                if section == 'DEFAULT':
                    continue
                section_func(self, section)
        return wrapper
    
    @apply_to_sections
    def store(self, section):
        #print('store {0}'.format(section))
        if not section in self.config.keys():
            raise Exception('Trying to store section "{0}" which does not exist'.format(section))

        section_config = self.section_config[section]
        source = section_config.source
        if not source:
            source = os.path.join(self._storage_dir, section + '.dat')
        source_type = self.section_config[section].source_type
        
        if source_type == 'user encrypted':
            data = pickle.dumps(self.get(section))
            self._security.encrypt_to_file(data, source)
        elif source_type == 'ini':
            self.write_ini_file(section = section)
        else:
            raise Exception('source_type "{0}" is unknown.'.format(source_type))

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
            raise Exception('source_type "{0}" is unknown.'.format(source_type))
            
        self.__ensure_config_present(section)
    
    def __ensure_config_present(self, section = ''):
        if not section:
            sectionList = self.config.sections()
        elif type(section) == str:
            sectionList = [section]
        else:
            sectionList = section
        
        for section in sectionList:
            # ensure section config
            if not section in self.section_config.keys():
                self.section_config[section] = SectionConfig()
            # ensure option config's
            for option in self.config.options(section):
                if not option in self.option_config.keys():
                    self.option_config[option] = OptionConfig()
         
