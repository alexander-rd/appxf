''' signature behavior for authenticity '''

from .meta_data import MetaData

from .storage import Storage
from .storable import Storable


class MetaDataStorable(MetaData, Storable):
    ''' Hold meta data and provide storage behavior

    Abstraction is required since Storage (on which Storable depends) needs to
    provide MetaData such that the original MetaData cannot yet be a
    Storable.
    '''

    def __init__(self, storage: Storage, **kwargs):
        super().__init__(storage=storage, **kwargs)

    def update(self):
        self.store()
