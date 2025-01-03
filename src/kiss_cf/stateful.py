''' Interface Contract for stateful classes'''

from typing import Any
from copy import deepcopy

class Stateful():
    ''' base class supporting storing/restoring objects via dictionaries

    This class is an interface contract mainly utilized in the Storable/Storage
    implementation.
    '''

    # There is no particular __init__ required

    def get_state(self) -> dict[str, Any]:
        ''' get object state

        The default implementation uses the class __dict__ which contains all
        class fields. You likely have to update this method for derived classes
        since not all entries in __dict__ will be part of the classes state.
        Especially aggregated classes whould typically be stripped.
        '''
        return deepcopy(self.__dict__)

    def set_state(self, data: dict[str, Any]):
        ''' Set object state

        The default implementation restores the classes __dict__ which contains
        all class fields. You may update this method to adapt the behavior.
        '''
        self.__dict__.update(data)
