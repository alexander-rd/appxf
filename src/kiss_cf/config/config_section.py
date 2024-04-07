from copy import deepcopy
from typing import Any
from kiss_cf.storage import DictStorable, Storage, StorageMethodDummy

from kiss_cf.gui import KissOption


class KissConfigSectionError(Exception):
    ''' General config error '''


class ConfigSection(DictStorable):
    ''' Maintain a section of config options

    Relations to other classes:
        Config -- Aggregates sections to an application configuration.
        Option -- Type and display options
    '''

    setting_list = ['configurable', 'format']

    format_list = ['pickle', 'ini']

    def __init__(self,
                 storage: Storage = StorageMethodDummy(),
                 options: list[str] | dict[str, KissOption] |
                 dict[str, dict[str, Any]] | None = None,
                 values: dict[str, KissOption.base_types] | None = None):
        super().__init__(storage=storage)
        if options is None:
            options = {}
        if values is None:
            values = {}
        self._options: dict[str, KissOption] = {}
        self._values: dict[str, KissOption.base_types] = {}
        self._configurable = True
        self._format = 'pickle'
        if isinstance(options, dict):
            for option, setting in options.items():
                if isinstance(setting, KissOption):
                    self._options[option] = deepcopy(setting)
                elif isinstance(setting, dict):
                    self._options[option] = KissOption(**setting)
                else:
                    raise KissConfigSectionError(
                        f'Cannot interpret settings for option "{option}" '
                        f'that is "{setting}". Expected a KissOption instance '
                        f'or a dictionary of options to construct a '
                        f'KissOption instance')
        elif isinstance(options, list):
            self._options = {
                option: KissOption()
                for option in options
                }
        for option in values:
            # ensure option properties exist:
            if option not in self._options:
                self._options[option] = KissOption()
            # ensure value is stored with expected type
            self._values[option] = self._options[option].to_value(
                values[option])

    def __str__(self):
        confstring = ('configurable' if self._configurable
                      else 'not configurable')
        return (f'Configuration in {str(self._storage)} stored as '
                f'{self._format} (format), {confstring}')

    def _get_dict(self):
        return self._values

    def _set_dict(self, data):
        self._values = data

    @property
    def options(self) -> dict[str, KissOption]:
        ''' Return the dictionary of option properties (deepcopy) '''
        return deepcopy(self._options)

    @property
    def configurable(self):
        return self._configurable

    @configurable.setter
    def configurable(self, new_value):
        if not isinstance(new_value, bool):
            raise KissConfigSectionError(
                f'You try to set configurable option of a section '
                f'with {new_value} which is not boolean.')
        self._configurable = new_value

    def _ensure_option_exists(self, option: str):
        if option not in self._options:
            raise KissConfigSectionError(
                f'Option {option} does not exist. '
                f'We have: {list(self._options.keys())}')

    def set(self,
            option: str,
            new_value: KissOption.base_types,
            store: bool = True):
        ''' Set an option value '''
        self._ensure_option_exists(option)
        self._values[option] = self._options[option].to_value(new_value)
        if store:
            self.store()

    # TODO: should this be a property??
    def get_all(self, copy: bool = False) -> dict[str, KissOption.base_types]:
        ''' Get access to value dictionary

        Note that python returns a reference to the dictionary. Changes of
        configuration values at a later point will apply to the obtained
        reference. You may change values directly. This behavior allows to
        provide the configuration options to a class during application
        initialization while the configuration itself may not yet be loaded.
        '''
        if copy:
            return deepcopy(self._values)
        else:
            return self._values

    def set_all(self, data: dict[str, KissOption.base_types], store=True):
        for option, value in data.items():
            self.set(option, value, store=False)
        if store:
            self.store()

    def get(self, option: str = '') -> KissOption.base_types:
        ''' Get one value or whole dictionary '''
        self._ensure_option_exists(option)
        return self._values[option]
