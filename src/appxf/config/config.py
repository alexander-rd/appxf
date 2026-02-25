# Copyright 2024-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
''' Provide Configuration Handling

The configuration concept is accumulating APPXF SettingDict objects as
sections.
'''
from collections.abc import Mapping
from typing import Any

from appxf import logging
from appxf.setting import SettingDict
from appxf.storage import RamStorage, Storage

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

# TODO: support of translations for section naming since they will pop up in
# menus. Note that this applies likewise to settings in the SettingDict's.

# TODO: Consider enforcing full lower-case (or full upper-case) section names.
# Currently, this is not fixed and when checking for existing sections, it's
# never clear whether upper() should be applied. The best solution would be to
# support the ["this-section" in config] syntax where the implementation
# handles the intended case-insensitivity the current usage is like
# ["this-section" in config.sections()]. This problem applies likewise to
# SettingDict. If touched, it should also consider the translations solution.

# TODO: recover INI file handling:
#   1) Loading sections from INI file
#   2) Store all sections to INI file
#
# Note: Section-wise INI handling would imply each section providing it's part.
# But the file is not section-specific.<


class AppxfConfigError(Exception):
    ''' General config error '''


class Config():
    ''' Organize configuration settings.

    Configuration typically splits into several sets of properties for USER or
    tool access related options. A Config object collects those configuration
    sections (internally as SettingDict objects) and adds some
    convenience:
      * load/store of all sections
      * store/load into one human readable INI file to assist the tool
        developers. !! Everything including passwords !!

    In an application, it is recommended to initialize the the aplication parts
    with the APPXF SettingDict's. They are shared by value and can be loaded
    after initialization.
    '''
    log = logging.getLogger(__name__ + '.Config')

    def __init__(self,
                 default_storage_factory: Storage.Factory | None = None,
                 **kwargs):
        super().__init__()
        self._default_storage_factory = default_storage_factory
        self._sections: dict[str, SettingDict] = {}

    @property
    def sections(self) -> list[str]:
        ''' Return list of sections. '''
        return list(self._sections.keys())

    def section(self, section: str) -> SettingDict:
        ''' Access a section '''
        if section not in self._sections:
            raise AppxfConfigError(
                f'Cannot access section {section}, it does not exist. '
                f'Existing are: {self.sections}.')
        return self._sections[section]

    def add_section(self,
                    section: str,
                    storage_factory: Storage.Factory | None = None,
                    settings: Mapping[str, Any] = None
                    ) -> SettingDict:
        '''Add section if not yet existing.  '''
        # ensure section does not yet exist:
        if section in self._sections:
            raise AppxfConfigError(
                f'Cannot add section {section}, it does already exist.')
        # define storage
        if storage_factory is not None:
            storage = storage_factory(section)
        elif self._default_storage_factory is not None:
            storage = self._default_storage_factory(section)
        else:
            storage = RamStorage()
        # construct section:
        #  * SettingDict will take over the section name
        self._sections[section] = SettingDict(
            storage=storage, settings=settings, name=section)
        #  * Config will, by default, not raise exceptions on import when
        #    a config option is new or missing
        export_options = SettingDict.ExportOptions(
            exception_on_new_key=False,
            exception_on_missing_key=False
            ).get_state()
        self._sections[section].get_state_kwargs = {'options': export_options}
        self._sections[section].set_state_kwargs = {'options': export_options}

        self.log.info(f'added section: {section}')
        return self._sections[section]

    def remove_section(self, section: str):
        ''' Remove section '''
        if section in self._sections:
            del self._sections[section]
            self.log.info('removed section: %s', section)
        else:
            raise AppxfConfigError(
                f'Cannot remove section, it does not exist: {section}')

    def store(self):
        ''' Store all sections '''
        for section in self._sections.values():
            section.store()

    def load(self):
        ''' Load all sections '''
        for section in self._sections.values():
            if section.exists():
                section.load()
