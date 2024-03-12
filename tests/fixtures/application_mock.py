from __future__ import annotations

import os

from kiss_cf.security import Security, SecurePrivateStorageMethod
from kiss_cf.registry import UserDatabase, UserRegistry
from kiss_cf.config import Config
from kiss_cf.storage import LocalStorageLocation

class ApplicationMock:
    def __init__(self,
                 root_path: str,
                 user: str):
        ''' Get a dummy application including folder structure

        A folder "app_<user>" is added to root_path for application specific
        data. Additional directories are created for simulating remote file
        transer:
          * "remote-pub" will share the public admin keys for
            encryption
          * "remote" is the shared database.
        '''
        self._root_path = root_path
        self._app_path = os.path.join(root_path, f'app_{user}')
        os.makedirs(self._app_path, exist_ok = True)

        self.salt = 'test'
        self.user = user
        self.password = f'{self.user}-password'

        # Create data storage objects (those steps will NOT include any data
        # loading since data would be stored encrypted and no password is set
        # yet OR password was not yet entered)

        # SECURITY
        self.file_sec = os.path.join(self._app_path, 'data/security')
        self.security = Security(salt=self.salt, file=self.file_sec)

        # CONFIG
        self.path_config = os.path.join(self._app_path, 'data/config')
        self.config = Config(self.security, storage_dir = self.path_config)
        # add some basic user data: email and name
        self.config.add_option('USER', 'email')
        self.config.set_option_config('email', type='email')
        self.config.add_option('USER', 'name')
        # add some arbitraty configuration
        self.config.add_option('TEST', 'test', '42')

        # REGISTRY
        self.path_registry = os.path.join(self._app_path, 'data/registry')
        self.location_registry = LocalStorageLocation(self.path_registry)
        self.registry = UserRegistry(self.location_registry, self.security, self.config)

        # some DATA LOCATION
        self.path_data = os.path.join(self._app_path, 'data')
        self.location_data = LocalStorageLocation(self.path_data)

        # some REMOTE LOCATION
        self.path_remote = os.path.join(self._app_path, 'data')

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


    #######################################################
    ### User initializazion (password) and unlocking
    #/
    def perform_login_init(self):
        ''' Perform login procedure: initialize user

        This includes (1) setting user data, (2) setting the password and (3)
        storing the configuration.

        This use case is covered by login_gui.py.
        '''
        # User would enter their details:
        self._set_user_data()
        # .. at setting the password:
        self.security.init_user(self.password)
        # And config must be stored accordinly:
        self.config.store()

    def _set_user_data(self):
        ''' set email and name'''
        self.config.set('USER', 'email',
                        f'{self.user}@url.com')
        self.config.set('USER', 'name',
                        f'{self.user}')

    def perform_login_unlock(self):
        ''' Perform login procedure: unlock with password

        This includes (1) unlock the Security object with password and (2)
        loading configuration data.

        This use case is covered by login_gui.py.
        '''
        self.security.unlock_user(self.password)
        # After unlocking, configuration should be loaded:
        self.config.load()

    ######################
    ### User Registration
    #/
    def perform_registration_admin_init(self):
        ''' Perform registration procedure: initialize DB as admin '''
        self.registry.initialize_as_admin()

    def perform_registration_get_request(self) -> bytes:
        ''' Perform registration procedure: get registration bytes

        This operation retrieves the registration bytes from the application to
        be sent to the admin (perform_registration_set_request).

        This use case is covered by registration_gui.py where the registration
        bytes would be handled by a file intended to be sent via Email to the
        admin
        '''
        # TODO: encryption is missing
        return self.registry.get_request_bytes()

    def Xinit_full(self):
        ''' '''
        self.perform_login_unlock()
