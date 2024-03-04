from __future__ import annotations
from os import path
from kiss_cf.security import Security, UserDatabase
from kiss_cf.config import Config
from kiss_cf.storage import LocalStorageLocation

class ApplicationMock:
    def __init__(self,
                 root_path: str,
                 user: str = 'user'):
        self._root_path = root_path

        self.salt = 'test'
        self.user = user
        self.password = f'{self.user}-password'

        self.reset()

    ########################
    ### initialize and reset
    #/
    def _init_security(self):
        self._file_sec = path.join(self._root_path, 'data/security')
        self.security = Security(salt=self.salt, file=self._file_sec)

    def _init_config(self):
        self._path_config = path.join(self._root_path, 'data/config')
        self.config = Config(self.security, storage_dir = self._path_config)
        self._init_config_base()

    def _init_config_user(self):
        ''' configure add email and name as basic user data '''
        self.config.add_option('USER', 'email')
        self.config.add_option('USER', 'name')

    def _set_user_data(self):
        ''' set email and name'''
        self.config.set('USER', 'email',
                        f'{self.user}@url.com')
        self.config.set('USER', 'name',
                        f'{self.user}')

    def _init_config_base(self):
        self.config.add_option('TEST', 'test', '42')

    def _init_registry(self):
        self._path_registry = path.join(self._root_path, 'data/registry')
        self.location_registry = LocalStorageLocation(self._path_registry)
        self._file_user_db = 'user_db'
        self.user_db = UserDatabase(self.location_registry .get_storage_method(self._file_user_db))

    def _init_data_location(self):
        self._path_data = path.join(self._root_path, 'data')
        self.location_data = LocalStorageLocation(self._path_data)

    def reset(self):
        ''' Reset application like for a new startup.

        Creates new object instances. Result is as if the application was
        freshly created while the persisted information (file system) remains.
        '''
        self._init_security()
        self._init_config()
        self._init_registry()
        self._init_data_location()

    # TODO: initialization of UserDatabase, Security, Config is quite
    # inconsistent.
    #   * Security specified a single file
    #   * Config specifies a path location
    #   * UserDatabase specifies a storage method
    #
    # Security should be consistent to UserDatabase. Config is different
    # since it handles multiple files (per section configuration). But
    # UserDatabase may not remain like this when other user's information
    # is added to the DB.

    def init_password(self):
        ''' Initialize password (registration missing) '''
        self.security.init_user(self.password)

    def unlock_user(self):
        ''' Unlock user with password '''
        self.security.unlock_user(self.password)

    def init_registration(self, app_admin: ApplicationMock):
        pass

    def init_full(self):
        ''' '''
        self.init_password()
