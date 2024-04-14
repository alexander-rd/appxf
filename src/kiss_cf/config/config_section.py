from copy import deepcopy
from typing import Any
from kiss_cf.storage import Storable, Storage, StorageMethodDummy

from kiss_cf.property import KissProperty

# TODO: Review if the "keep values as separate dict" behavior is worth
# splitting into a separate class in the conrext of property handling and
# corresponding GUI. What would remain for the config section?? Just the
# storage behavior??


class KissConfigSectionError(Exception):
    ''' General config error '''


class ConfigSection(Storable):
    ''' Maintain a section of config options

    Relations to other classes:
        Config -- Aggregates sections to an application configuration.
        Option -- Type and display options
    '''

    # TODO: this is currently unused.
    setting_list = ['configurable', 'format']

    # TODO: extend with INI and JSON
    format_list = ['compact']

    def __init__(self,
                 storage: Storage = StorageMethodDummy(),
                 properties: list[str] | dict[str, KissProperty] |
                 dict[str, dict[str, Any]] | None = None,
                 values: dict[str, Any] | None = None):
        super().__init__(storage=storage)
        if properties is None:
            properties = {}
        if values is None:
            values = {}
        self._properties: dict[str, KissProperty] = {}
        self._values: dict[str, object] = {}
        # Direct access:
        self.configurable = True
        self.format = 'pickle'
        if isinstance(properties, dict):
            for option, setting in properties.items():
                if isinstance(setting, KissProperty):
                    self._properties[option] = deepcopy(setting)
                else:
                    raise KissConfigSectionError(
                        f'Cannot interpret settings for option "{option}" '
                        f'that is "{setting}". Expected a KissOption instance '
                        f'or a dictionary of options to construct a '
                        f'KissOption instance')
        elif isinstance(properties, list):
            self._properties = {
                option: KissProperty()
                for option in properties
                }
        for option in values:
            # ensure option properties exist:
            if option not in self._properties:
                self._properties[option] = KissProperty()
            # ensure value is stored with expected type
            self._values[option] = self._properties[option].to_value(
                values[option])

    def __str__(self):
        confstring = ('configurable' if self._configurable
                      else 'not configurable')
        return (f'Configuration in {str(self._storage)} stored as '
                f'{self.format} (format), {confstring}')

    def _get_state(self) -> object:
        return self._values

    def _set_state(self, data):
        self._values = data

    @property
    def options(self) -> dict[str, Any]:
        ''' Return the dictionary of option properties (deepcopy) '''
        return deepcopy(self._properties)

    def _ensure_option_exists(self, option: str):
        if option not in self._properties:
            raise KissConfigSectionError(
                f'Option {option} does not exist. '
                f'We have: {list(self._properties.keys())}')

    def set(self,
            option: str,
            new_value: Any,
            store: bool = True):
        ''' Set an option value '''
        self._ensure_option_exists(option)
        # setting the value includes validity check:
        self._properties[option] = new_value
        self._values[option] = self._properties[option]
        if store:
            self.store()

    # TODO: should this be a property??
    def get_all(self, copy: bool = False) -> dict[str, Any]:
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

    def set_all(self, data: dict[str, Any], store=True):
        for option, value in data.items():
            self.set(option, value, store=False)
        if store:
            self.store()

    def get(self, option: str = '') -> Any:
        ''' Get one value or whole dictionary '''
        self._ensure_option_exists(option)
        return self._values[option]
