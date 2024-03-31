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

from typing import Any

from kiss_cf import logging
from kiss_cf.gui import KissOption
from kiss_cf.storage import StorageMethodDummy, StorageMaster

from .config_section import ConfigSection

# TODO: config refactoring
#  1) I need the serialize/deserialize on dictionaries as storable >> to mary
#     it with a factory
#   >> Storage does not exist until storing or loading!
#  2) Same as above based on configparser. Intended is to combine with
#     unsecured storage but could theoretically be secured.
#
# NOTE: (1) and (2) could initially be the same. I do not care much about
# storage size such I could implement only (1)
#
#  3) option config must become section-specific
#  4) fields must become private
#  5) get on section must return the same dict as used internally!
#     !! The options maintaining dict must use appropriate types
#     ?? Will it become necessary to define the type on option definition
#     ** It would be nice to configure an option directly on creation

# TODO: recover INI file handling:
#   1) Loading sections from INI file
#   2) Store all sections to INI file
#
# Note: Section-wise INI handling would imply each section providing it's part.
# But the file is not section-specific.


class KissConfigError(Exception):
    ''' General config error '''


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

    def __init__(self, default_storage: StorageMaster | None = None):
        self._default_storage = default_storage
        self._sections: dict[str, ConfigSection] = {}

        # TODO: clarify how USER section is created. I do not see why this has
        # to be this way
        #
        # Cross-cutting concerns are deeply coupled. Configuration already
        # prefills USER with expected settings. Where user USER data as part of
        # configuration is stored is business of configuration, not of login
        # (secrurity).
        # self.add_section('USER')
        # self.section_config['USER'].source_type = 'user encrypted'

    def __str__(self):
        outStr = ''
        for section in self._sections:
            if outStr:
                outStr += ', '
            outStr += section + ': ' + str(self._sections[section])
        return outStr

    @property
    def sections(self) -> list[str]:
        ''' Return list of sections. '''
        return list(self._sections.keys())

    def section(self, section: str) -> ConfigSection:
        ''' Access a section '''
        if section not in self._sections:
            raise KissConfigError(
                f'Cannot access section {section}, it does not exist. '
                f'Existing are: {self.sections}.')
        return self._sections[section]

    def add_section(self,
                    section: str,
                    options: dict[str, KissOption] |
                    dict[str, dict[str, Any]] | None = None,
                    storage_master: StorageMaster | None = None):
        '''Add section if not yet existing.  '''
        # ensure section does not yet exist:
        if section in self._sections:
            raise KissConfigError(
                f'Cannot add section {section}, it does already exist.')
        # define storage
        if storage_master is not None:
            storage = storage_master.get_storage(section)
        elif self._default_storage is not None:
            storage = self._default_storage.get_storage(section)
        else:
            storage = StorageMethodDummy()
        # construct section
        if options is None:
            options = {}
        self._sections[section] = ConfigSection(
            storage=storage,
            options=options)
        self.log.info(f'added section: {section}')

    def store(self):
        ''' Store all sections '''
        for section in self._sections.values():
            section.store()

    def load(self):
        ''' Losd all sections '''
        for section in self._sections.values():
            section.load()
