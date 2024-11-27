from __future__ import annotations
from copy import deepcopy

import uuid

from .storage import Storage, AppxfStorageWarning


class RamStorage(Storage):
    # store data and metadata in class data is accessed by _data[group][name]:
    _data: dict[str, dict[str, object]] = {}
    # meta is accessed by _meta[group][name][meta]. This order allows
    # pre-initializing the dicts in __init__ up to the point where we do not
    # know which meta will exist >> meta must be last.
    _meta_data: dict[str, dict[str, dict[str, object]]] = {}

    def __init__(self,
                 name: str | None = None,
                 ram_area: str = ''):
        # It is possible to use RamStorage() as a functional dummy storage. In
        # this case, get() will never work.
        if name is None:
            name = str(uuid.uuid4())
            while self.is_registered(name, location=ram_area):
                name = str(uuid.uuid4())
        super().__init__(name=name,
                         location=ram_area)

        # initialize the ram area:
        if ram_area not in self._data:
            self._data[ram_area] = {}
            self._meta_data[ram_area] = {}
        # warning if constructing for the same memory
        if name in self._data[ram_area]:
            raise AppxfStorageWarning(
                f'RAM storage for {ram_area}::{name} already exists: risk of '
                f'writing to same storage. You should use RamStorage.get() '
                f'instead of RamStorage() constructor.')
            #! TODO: the error message is wrong unless we keep get()

    @classmethod
    def get(cls,
            name: str,
            ram_area: str = '',
            ) -> Storage:
        return super().get(name=name, location=ram_area,
                           storage_init_fun=lambda: RamStorage(
                               name=name, ram_area=ram_area))

    @classmethod
    def get_factory(cls, ram_area: str = '') -> Storage.Factory:
        return super().get_factory(location=ram_area,
                                   storage_get_fun=lambda name: RamStorage.get(
                                       name=name, ram_area=ram_area
                                   ))

    @classmethod
    def reset(cls):
        cls._data = {}
        cls._meta_data = {}
        return super().reset()

    def exists(self) -> bool:
        # print(f'Checking for {self.id()}: {self._data} - {self}')
        if not self._meta:
            if self._location not in self._data:
                return False
            if self._name not in self._data[self._location]:
                return False
            return True
        # in case of meta:
        if self._location not in self._meta_data:
            return False
        if self._name not in self._meta_data[self._location]:
            return False
        return self._meta in self._meta_data[self._location][self._name]


    def store_raw(self, data: object):
        if self._meta:
            if self._location not in self._meta_data:
                self._meta_data[self._location] = {}
            if self._name not in self._meta_data[self._location]:
                self._meta_data[self._location][self._name] = {}
            self._meta_data[self._location][self._name][self._meta] = deepcopy(data)
        else:
            if self._location not in self._data:
                self._data[self._location] = {}
            if self._name not in self._data[self._location]:
                self._data[self._location][self._name] = {}
            self._data[self._location][self._name] = deepcopy(data)

    def load_raw(self) -> object:
        if not self.exists():
            return None
        if self._meta:
            return deepcopy(self._meta_data[self._location][self._name][self._meta])
        # not meta:
        return deepcopy(self._data[self._location][self._name])
