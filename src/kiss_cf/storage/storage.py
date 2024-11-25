''' Basic Storage Methods '''

from abc import ABC, abstractmethod

from ._storage_master_base import StorageMasterBase
from .meta_data import MetaData


class Storage(ABC):
    ''' Abstract class to model a storage method.

    The Storage class represents _how_ data is stored (to a file system). It
    abstracts any details on:
      * the actual storage device (local disc, FTP, ..)
      * serialization (convert python objects to bytes)
      * encryption/decryption
      * supporting functionality like data synchronization
    In addition to store()/load(), a Storage object has a function exists() to
    determine if data may be loaded.

    A Storage class may work together with a Storable which represents _what_
    is to be stored. They collaborate by:
      1) The Storable get's a Storage object upon construction
      2) The Storable sets the file name of a Storage
    construction and set the file name to represent a specific storage. It will
    then rely on the load() and store() implementation by consuming/providing a
    byte stream.
    '''
    def __init__(self,
                 storage: StorageMasterBase,
                 name: str,
                 **kwargs):
        super().__init__(**kwargs)
        self._storage_master = storage
        self._name = name

    @property
    def name(self):
        ''' Name of the Storage'''
        return self._name

    @property
    def storage_master(self):
        ''' StorageMaster from which the Storage was generated '''
        return self._storage_master

    def id(self) -> str:
        ''' ID for the storage object.

        The ID shall use the StorageMaster ID's which, themselves shall be
        unique. Main purpose of the id() is loggin.
        '''
        return f'{self.__class__.__name__} for {self._name} from {self._storage_master.id()}'

    def get_meta_data(self) -> MetaData:
        ''' Get storage meta data like UUID and timestamp '''
        return self._storage_master.get_meta_data(self._name)

    @abstractmethod
    def exists(self) -> bool:
        ''' Check existance of storage before loading '''

    @abstractmethod
    def load(self) -> object:
        ''' Load data from Storage '''

    @abstractmethod
    def store(self, data: object):
        ''' Store data to Storage '''
