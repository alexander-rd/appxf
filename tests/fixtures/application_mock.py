from __future__ import annotations

import os

from kiss_cf.security import Security, SecurePrivateStorageMaster
from kiss_cf.registry import Registry
from kiss_cf.config import Config
from kiss_cf.storage import LocalStorageMaster
from kiss_cf.property import KissProperty

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
        self.file_sec = os.path.join(self._app_path, 'data/user/security')
        self.security = Security(salt=self.salt, file=self.file_sec)

        # CONFIG::LOCAL USER
        self.path_user_config = os.path.join(self._app_path, 'data/user/config')
        self.storage_user_config = SecurePrivateStorageMaster(
            LocalStorageMaster(self.path_user_config), self.security)
        # CONGIG::SHARED TOOL
        self.path_shared_config = os.path.join(self._app_path, 'data/shared/config')
        self.storage_shared_config = SecurePrivateStorageMaster(
            LocalStorageMaster(self.path_shared_config), self.security)
        # We still apply one config for all that stores to shared tool storage
        # by default since only few will be user specific.
        self.user_config = Config(default_storage=self.storage_shared_config)
        # add USER config with some basic user data: email and name
        self.user_config.add_section('USER', options={
            'email': KissProperty.new('email'),
            'name': KissProperty.new('str')},
            storage_master = self.storage_user_config)
        # TODO: the above would be simpler by using:
        #   self.user_config.add_section('USER').add_properties(
        #           'email:email',
        #           'name:str)
        #
        #  * (+) The property adding gets in the context where it belongs (the
        #    config section implementation)
        #  * (+) The most common setting is the type which is now much simpler.
        #    BUT...
        #  * (-) The above would make ':' a non allowed character for property
        #    names.
        #  * (/) While being shorter, the syntax will be unknown or uncommon.
        #
        # The main problem by using KissProperty was needing to import it. This
        # is not required when adapting this pattern:
        #
        #  self.user_config.add_section('USER').add_properties(
        #           'email', config.property('str', further options),
        #           'name', 'more', 'even more',
        #           'last one with spec', condig.property('email')
        #           )
        #
        #  * (+) All benefits from above
        #  * (+) Any characters for property names
        #  * (+) Easy syntax: no additional brakets - the property config just
        #    comes after each name
        #
        # Conclusion: use this above approach
        #
        # Open question: should it be called "add_property" or
        # "add_properties"? In the usage above, it's clearly for adding
        # multiple  properties but adding a single one should not use a
        # different syntax and should be like:
        #
        #   config.section('USER').add_property('name', config.property('str'))#
        #
        # The function definition would be:
        #
        #  def add_property(name: str, settings: KissProperty = , *args)
        #
        # The following would NOT work when 'email' should determine the type
        # simply because we cannot distinguish the property name from the type
        # name.:
        #
        #  config.section('USER').add_property('name', 'email')
        #
        # Remaining drawback of this solution: we have to use
        # config.property('type'). Essentially:
        #
        #   config.section('USER').add_property('name', config.property('email'))
        #   versus
        #   config.section('USER').add_property('name', {'type': 'email'})
        #
        # ^^ The second version is not really shorter while the first one
        # enables more convinience.

        # add credentials options for shared storage (no values!)
        self.user_config.add_section('SHARED_STORAGE', options=CredentialLocationMock.config_properties)
        # add some arbitraty configuration
        self.user_config.add_section('TEST', options={
            'test': KissProperty.new(int)
            })
        # TODO: reconsider the add_section interface and convert to add_section('TEST').add_properties(..)

        # REGISTRY
        self.path_registry = os.path.join(self._app_path, 'data/registry')
        self.location_registry = LocalStorageMaster(self.path_registry)
        self.registry = Registry(self.location_registry, self.security, self.user_config)

        # some DATA LOCATION
        self.path_data = os.path.join(self._app_path, 'data')
        self.location_data = LocalStorageMaster(self.path_data)

        # some REMOTE LOCATION
        self.path_remote = os.path.join(self._app_path, 'data')


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
        self.user_config.section('USER').store()

    def _set_user_data(self):
        ''' set email and name'''
        section = self.user_config.section('USER')
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
        # After unlocking, registration should be continued (if possible)
        if not self.registry.try_load():
            return
        # TODO: any "privately stored" configuration can be loaded
        # USER configuration can now be loaded:
        self.user_config.section('USER').load()
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
        self.user_config.section('SHARED_STORAGE').set('credential', 'yes, sir!')
        #   2) and some config that is shared after a sync
        self.user_config.section('TEST').set('test', 42)

        self.user_config.store()



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

