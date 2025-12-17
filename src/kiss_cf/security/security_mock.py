'''Define security algorithms.'''
from .security import Security


class SecurityMock(Security):
    ''' Provide a mock for testing

    Only the writing/loading of the key material is stripped. Writing/loading
    encrypted files would still work.
    '''

    def __init__(self):
        '''Get security context.

        The salt used to generate secret keys from password is set with
        something but you should provide your own salt. Any string does.
        '''
        super().__init__(salt='mock', file='')

    def _write_keys(self):
        # keys will NOT be written to file system
        pass

    def _load_keys(self):
        # keys CANNOT be loaded
        pass

    def is_user_initialized(self):
        # initialization is determined based on keys being present or not
        return bool(self._derived_key)
