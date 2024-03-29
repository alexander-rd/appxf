from __future__ import annotations

import os

from kiss_cf.security import Security, SecurePrivateStorageFactory
from kiss_cf.registry import Registry
from kiss_cf.config import Config
from kiss_cf.storage import LocalStorageLocation

from .restricted_location import CredentialLocationMock

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
        self.factory_config = SecurePrivateStorageFactory(
            LocalStorageLocation(self.path_config), self.security)
        self.config = Config(default_factory=self.factory_config)
        # add some basic user data: email and name

        self.config.add_section('USER', options={
            'email': {'type': 'email'},
            'name': {'type': 'str'}
            })
        # add credentials for shared storage
        self.config.add_section('SHARED_STORAGE', options=CredentialLocationMock.config_options)
        # add some arbitraty configuration
        self.config.add_section('TEST', options={
            'test': {'type': 'int'}
            })

        # REGISTRY
        self.path_registry = os.path.join(self._app_path, 'data/registry')
        self.location_registry = LocalStorageLocation(self.path_registry)
        self.registry = Registry(self.location_registry, self.security, self.config)

        # some DATA LOCATION
        self.path_data = os.path.join(self._app_path, 'data')
        self.location_data = LocalStorageLocation(self.path_data)

        # some REMOTE LOCATION
        self.path_remote = os.path.join(self._app_path, 'data')

        # TODO: initialization of UserDatabase, Security, Config is quite
        # inconsistent.
        #   * Security specified a single file
        #   * Config specifies a path location
        #   * Registry specifies a storage location
        #
        # Security should be consistent to Registry. Config is different
        # since it handles multiple files (per section configuration). But
        # Registry may not remain like this when other user's information
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
        # USER config must be stored accordinly:
        self.config.section('USER').store()

    def _set_user_data(self):
        ''' set email and name'''
        section = self.config.section('USER')
        section.set('email', f'{self.user}@url.com', store=False)
        section.set('name', f'{self.user}', store=False)

    def perform_login_unlock(self):
        ''' Perform login procedure: unlock with password

        This activity includes
          (1) unlock the Security object with password and
          (2) loading configuration data which may be incomplete if
              registration is incomplete
          (3) forward to registration check and potential post-registration
              procedures

        This use case is covered by login_gui.py.
        '''
        self.security.unlock_user(self.password)
        # After unlocking, registration should be continues (if possible)
        if not self.registry.try_load():
            return
        # USER configuration can now be loaded:
        self.config.section('USER').load()
        #self._perform_try_load_registration()

    ######################
    ### User Registration
    #/
    def _perform_try_load_registration(self):
        ''' Check if registered and perform post-registration actions

         Will happen always after login and execute:
           (1) will try to sync
           (2) will reload registration and config (may have changed after
               sync)
        '''
        if not self.registry.is_initialized():
            return

    def perform_registration_admin_init(self):
        ''' Perform registration procedure: initialize DB as admin '''
        self.registry.initialize_as_admin()
        # The below will likely fail but will commonly be executed after
        # passing registration.
        self._perform_try_load_registration()

        # add some configuration detail for testing:
        #   1) a password to be shared on registration to access the shared storage
        self.config.section('SHARED_STORAGE').set('credential', 'yes, sir!')
        #   2) and some config that is shared after a sync
        self.config.section('TEST').set('test', 42)

        self.config.store()



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

