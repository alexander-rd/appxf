from abc import ABC, abstractmethod
from .meta_data import MetaData

class StorageMasterBase(ABC):
    ''' Abstracted StorageMaster interfaces for Storage

    The abstraction is required since Storage shall have access to some
    StorageMaster defined functions like get_meta_data.
    '''
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @abstractmethod
    def id(self, name: str = '') -> str:
        ''' String representing the specific location or file

        Used in logging to indicate which location is failing. Example for FTP
        location, this might be "ftp.your-url.com/path/of/location". Also used
        for synchronization to indicate the source of the file.
        '''

    @abstractmethod
    def get_meta_data(self, name: str) -> MetaData:
        ''' Get meta data of stored data.

        Contains UUID and/or timestamp used for synchronization.
        '''
