''' AppHarness Class for Testing

The application harness aggregates real APPXF objects for all supported
features that might be used in a real application. It also provides operations
to get the objects into a consistent application state.

Since it uses real APPXF objects, the ApplicationHarness must run on top of a
directory within the file system. See appxf_objects.py for helpers on the test
directory.
'''

from __future__ import annotations

import os

from kiss_cf.security import Security, SecurePrivateStorage
from kiss_cf.registry import Registry, SharedSync, SecureSharedStorage
from kiss_cf.config import Config
from kiss_cf.storage import LocalStorage, Storage

from .restricted_location import CredentialLocationMock

class AppHarness:
    def __init__(self,
                 root_path: str,
                 user: str):
        ''' Get a set of APPXF objects mimicing an application

        A folder "app_<user>" is added to root_path for application specific
        data. Additional directories in the root path are created for remote
        files.

        Note that LocalStorage is gernerating the paths upon construction of
        file objects.
        '''
        self.root_path = root_path
        self.app_path = os.path.join(root_path, f'app_{user}')
        os.makedirs(self.app_path, exist_ok = True)

        self.salt = 'test'
        self.user = user
        self.password = f'{self.user}-password'

        Storage.switch_context(self.user)

        # Create data storage objects (those steps will NOT include any data
        # loading since data would be stored encrypted and no password is set
        # yet OR password was not yet entered)

        # SECURITY
        self.file_sec = os.path.join(self.app_path, 'data/user/security')
        self.security = Security(salt=self.salt, file=self.file_sec)

        # CONFIG::LOCAL USER
        self.path_user_config = os.path.join(self.app_path, 'data/user/config')
        self.storagef_user_config = SecurePrivateStorage.get_factory(
            base_storage_factory=LocalStorage.get_factory(
                path=self.path_user_config),
            security=self.security)
        # CONGIG::SHARED TOOL
        self.path_shared_config = os.path.join(self.app_path, 'data/shared/config')
        self.storagef_shared_config = SecurePrivateStorage.get_factory(
            LocalStorage.get_factory(
                path=self.path_shared_config),
            security=self.security)
        # We still apply one config for all that stores to shared tool storage
        # by default since only few will be user specific.
        self.user_config = Config(default_storage=self.storagef_shared_config)
        # add USER config with some basic user data: email and name
        self.user_config.add_section(
            'USER', storage_factory=self.storagef_user_config,
            settings = {
                'email': ('email',),
                'name': (str,),
                })


        # add credentials options for shared storage (no values!)
        self.user_config.add_section(
            'SHARED_STORAGE',
            settings = CredentialLocationMock.config_properties)
        # add some arbitraty configuration
        self.user_config.add_section(
            'TEST', settings = {'test': (int,)})
        # add a configuration section that is shared during registration in
        # addition to SHARED_STORAGE which must be shared to access remote
        # data.
        self.user_config.add_section(
            'REGISTRATION_SHARED', settings = {'test': (str,)}
        )

        # REGISTRY: local storage (security applied within Regisrty)
        self.path_registry = os.path.join(self.app_path, 'data/registry')
        self.storagef_registry = LocalStorage.get_factory(path=self.path_registry)
        # REGISTRY: remote storage (security applied within Regisrty)
        self.path_remote_registry = os.path.join(self.root_path, 'remote/registry')
        self.storagef_remote_registry = LocalStorage.get_factory(path=self.path_remote_registry)
        # REGISTRY
        self.registry = Registry(
            local_storage_factory=self.storagef_registry,
            remote_storage_factory=self.storagef_remote_registry,
            security=self.security,
            config=self.user_config,
            response_config_sections=['SHARED_STORAGE', 'REGISTRATION_SHARED'])

        # some DATA LOCATION
        self.path_data = os.path.join(self.app_path, 'data')
        self.storagef_data = SecurePrivateStorage.get_factory(
            base_storage_factory=LocalStorage.get_factory(path=self.path_data),
            security=self.security)

        # matching REMOTE LOCATIONs
        # CONFIG: REMOTE STORAGE
        self.path_remote_config = os.path.join(self.root_path, 'remote/config')
        self.storagef_remote_config = SecureSharedStorage.get_factory(
            base_storage_factory=LocalStorage.get_factory(path=self.path_remote_config),
            security=self.security,
            registry=self.registry)
        self.path_remote_data = os.path.join(self.root_path, 'remote/data')
        self.storagef_remote_data = SecureSharedStorage.get_factory(
            base_storage_factory=LocalStorage.get_factory(path=self.path_remote_data),
            security=self.security,
            registry=self.registry)

        # TODO: Setting up remote storage like this is quite cumbersome. A sync
        # short cut should allow some: sync(local_factory, remote_factory(w/o
        # path)). The remote factoy would not have the full path defined, yet.
        # And allow: factory(name=bla, path='sub/location') which would be done
        # by sync.

        # setup shared sync:
        self.shared_sync = SharedSync(registry=self.registry)
        self.shared_sync.add_sync_pair(
            local=self.storagef_data,
            remote=self.storagef_remote_data,
            writing_roles=['user', 'admin']
        )
        self.shared_sync.add_sync_pair(
            local=self.storagef_shared_config,
            remote=self.storagef_remote_config,
            writing_roles=['admin'],
            additional_readers=['user']
        )
        # TODO: registry (USER_DB) is not yet included. How would that be
        # synced? Also by just setting up another pair??


    #######################################################
    ### User initializazion (password) and unlocking
    #/
    def perform_login_init(self):
        ''' Perform login procedure: initialize user

        This includes (1) setting user data, (2) setting the password and (3)
        storing the configuration.

        This use case is covered by login_gui.py.
        '''
        Storage.switch_context(self.user)
        # User would enter their details:
        self._set_user_data()
        # .. at setting the password:
        self.security.init_user(self.password)
        # USER config must be stored accordinly:
        self.user_config.section('USER').store()

    def _set_user_data(self):
        ''' set email and name'''
        section = self.user_config.section('USER')
        section['email'] = f'{self.user}@url.com'
        section['name'] = f'{self.user}'

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
        Storage.switch_context(self.user)
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
        Storage.switch_context(self.user)
        self.registry.initialize_as_admin()
        # The below will likely fail but will commonly be executed after
        # passing registration.
        self._perform_try_load_registration()

        # add some configuration detail for testing:
        #   1) a password to be shared on registration to access the shared storage
        self.user_config.section('SHARED_STORAGE')['credential'] = 'yes, sir!'
        #   2) and some config that is shared after a sync
        self.user_config.section('TEST')['test'] = 42

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
        Storage.switch_context(self.user)
        return self.registry.get_request_bytes()

    def perform_registration_from_request(self, request_bytes: bytes) -> bytes:
        ''' Perform registration from request and return with response '''
        Storage.switch_context(self.user)
        request = self.registry.get_request_data(request_bytes)
        user_id = self.registry.add_user_from_request(request)
        response_bytes = self.registry.get_response_bytes(user_id)
        self.shared_sync.sync()
        return response_bytes

    def perform_registration_set_response(self, response_bytes: bytes):
        ''' Apply registration response to an application '''
        Storage.switch_context(self.user)
        self.registry.set_response_bytes(response_bytes)
        # sync and load configuration:
        self.shared_sync.sync()

        # TODO: the above fails since it tries to sync while registry is not
        # yet updated. The registry does not even contain the user's entry,
        # yet to see if it should sync incoming data.
        #
        # Alternative A: Just include the user row to the USER_DB until next
        # sync. But the question will remain: how to sync registry at all.

        self.user_config.load()

    def perform_registration(self, app_admin: AppHarness):
        request_bytes = self.perform_registration_get_request()
        response_bytes = app_admin.perform_registration_from_request(request_bytes=request_bytes)
        self.perform_registration_set_response(response_bytes=response_bytes)
