
# allow class name being used before being fully defined (like in same class):
from __future__ import annotations

from kiss_cf.storage import sync, Storage
from kiss_cf.config import Config
from kiss_cf.security import Security, SecurePrivateStorage

from ._registration_request import RegistrationRequest
from ._registration_response import RegistrationResponse
from ._user_id import UserId
from ._user_db import UserDatabase
from ._registry_base import RegistryBase
from .shared_storage import SecureSharedStorage


class KissRegistryError(Exception):
    ''' General registry error '''


class KissRegistryUnitialized(Exception):
    ''' Trying to use an uninitialized registry '''


class KissRegistryUnknownConfigSection(Exception):
    ''' Trying to use an uninitialized registry '''


class Registry(RegistryBase):
    ''' User registry maintains the application user's ID and all user
        configurations the user is permitted to see. '''

    def __init__(self,
                 local_storage_factory: Storage.Factory,
                 remote_storage_factory: Storage.Factory,
                 security: Security,
                 config: Config,
                 user_config_section: str = 'USER',
                 response_config_sections: list[str] | None = None,
                 **kwargs):
        ''' Create Registry Handler

        local_storage_factory: The local storage is where your view on the user
            database is stored for offline usage. This is typically
            LocalStorage and Registry stores data via SecurePrivateStorage.
        remote_storage_factory: The remote storage is where the overall user
            database is stored for all users to sync with. A typical use case
            is FtpStorage while also LocalStorage may be used. Registry employs
            a SecureSharedStorage on top for stored files.
        security: a local login Security object is required to employ the
            SecurePrivate and SecureShared storage as mentioned above.
        config: The registration procedure allows to convey certain parts of
            the application configuration which may be required to access the
            remote storage mentioned above.
        '''
        super().__init__(**kwargs)
        self._loaded = False
        self._security = security
        self._config = config
        self._local_storage_factory = local_storage_factory
        self._remote_storage_factory = remote_storage_factory
        self._user_config_section = user_config_section
        if response_config_sections is None:
            response_config_sections = []
        self._response_config_sections = response_config_sections

        # USER_ID does not need to be secured
        self._user_id = UserId(local_storage_factory('USER_ID'))

        # USER_DB must be secured
        self._local_user_db_storage = SecurePrivateStorage(
            base_storage = local_storage_factory('USER_DB'),
            security=security)
        self._user_db = UserDatabase(self._local_user_db_storage)
        # Matching remote storage
        self._remote_user_db_storage = SecureSharedStorage(
            base_storage=remote_storage_factory('USER_DB'),
            security=security,
            registry=self)

        # Note: USER_DB cannot be synced from __init__ since security module
        # will not yet be unlocked

    # TODO: response_config_sections likely needs an explicit setter to have
    # the options to define configuration settings after defining the user
    # registry. Also, this list may need to be a mapping since different roles
    # may receive different subsets of configuration data. But this should be
    # reconsidered since this part of the configuration sharing may be handled
    # via the remote synchronization. Main question is: should APPXF support a
    # user registry without shared storage? == A share of credentials without
    # any mode of updating them later?

    @property
    def user_id(self):
        ''' Get user ID

        Method will raise KissExceptionUserId if registry is not completed.
        See: is_initialized().
        '''
        return self._user_id.id

    def get_roles(self, uid: int | None = None) -> list[str]:
        if uid is None:
            return self._user_db.get_roles()
        elif uid < 0:
            # TODO: why does only require access of _user_id an ensure_loaded()
            # but not access of _user_db above and below?
            self._ensure_loaded()
            uid = self._user_id.id
        return self._user_db.get_roles(uid)

    def is_initialized(self) -> bool:
        return (self._loaded or (
                self._user_id.exists() and
                self._user_db.exists()
                ))

    # TODO: ensure_loaded is only used once. This instance could just use
    # try_load.
    def _ensure_loaded(self):
        if self._loaded:
            return None
        if not self.try_load():
            KissRegistryUnitialized('Registry is not initialized.')

    def try_load(self) -> bool:
        if not self._security.is_user_unlocked():
            return False
        if not self.is_initialized():
            return False
        if not self._user_id.exists():
            return False
        self._user_id.load()
        if not self._user_db.exists():
            return False
        self._user_db.load()
        self._loaded = True
        return self._loaded

    def set_admin_keys(self, keys: list[tuple[bytes, bytes]]):
        for key_set in keys:
            self._user_db.add_new(key_set[0], key_set[1], ['user', 'admin'])

    def initialize_as_admin(self):
        ''' Initialize databse

        This function is expected to be called only once in the entire tool
        life cycle by user 0. New admins will inherit the existing data.
        '''
        self._user_id.id = self._user_db.init_user_db(
            validation_key=self._security.get_signing_public_key(),
            encryption_key=self._security.get_encryption_public_key())
        self._loaded = True
        # Note: writing into USER_ID and into USER_DB automatically stores
        # them.

        # No update of remote USER_DB - there is no one who would need that
        # with only the admin being registered.

    def sync_with_remote(self, mode: str):
        ''' Sync local registry with remote location.

        A sync should happen at every startup and/or before any sync of shared
        data. Additionally, sync is executed when admin adds a new member or
        when user adds the registration response.

        The following prerequisites must be met for the sync to be successful:
          * the user has unlocked the Security object
          * the user is registered (is_initialized())
        '''
        print(f' -- {mode} from user={self.user_id}')
        # TODO: receiving after getting registration response on user side
        # cannot work since try_load() includes trying to load the user_db
        # which is not existent yet? .. .. is it not? It could be if the
        # registration response would already include it, not? But it does not
        # include it. So.. ..what is the original purpose of try_load() OR what
        # is the purpose of the below try_load() protection?
        #
        # AFTER the response, I should already know my roles, not? Or does the
        # user only know it's ID and can access the user_db by ID since it will
        # find the decryption key?
        #
        # ANALYSIS - what is required to RECEIVE data from SharedStorage?
        #
        # (1) To decrypt, I need my private key in my security object >> not a
        #     problem.
        #
        # (2) To check the signature, I need to verify the payload with MY COPY
        #     of the public key which is only available in the user_db.
        #
        # >> For the first sync, all admin public keys should be sent.
        if self.try_load():
            is_admin = self._user_db.has_role(self._user_id.id, 'admin')
            if mode == 'receiving':
                print(' -- receiving')
                # receiving is ALWAYS overwriting local USER_DB
                sync(storage_a=self._remote_user_db_storage,
                     storage_b=self._local_user_db_storage,
                     only_a_to_b=True)
                # reload after sync
                self._user_db.load()
            elif mode == 'sending':
                if is_admin:
                    print(' -- sending')
                    sync(storage_a=self._local_user_db_storage,
                        storage_b=self._remote_user_db_storage,
                        only_a_to_b=True)
            else:
                raise KissRegistryError(f'Mode {mode} is unknown.')

    def get_request_bytes(self) -> bytes:
        ''' Get registration request bytes

        Bytes are sent to an admin outside of this tools scope. For example, as
        a file via Email.
        '''
        return self.get_request().get_request_bytes()

    def get_request(self) -> RegistrationRequest:
        ''' Get registration request '''
        # TODO: add encryption which will require the AMDIN_DB

        # TODO: add warning message when _loaded is True
        if self._user_config_section:
            user_data = dict(self._config.section('USER'))
        else:
            user_data = {}
        return RegistrationRequest.new(user_data, self._security)

    def get_request_data(self, request: bytes) -> RegistrationRequest:
        return RegistrationRequest.from_request(request)

    def add_user_from_request(self,
                              request: RegistrationRequest,
                              roles: list[str] = ['user']) -> int:
        ''' Store user in databse and get user ID

        The admin is expected to use this function. The request bytes are
        generated by get_request_bytes() on user side. After user is added, the
        admin uses get_response_bytes() to send data back to user.
        '''
        if not self._loaded:
            raise KissRegistryUnitialized(
                'registry is not yet loaded, cannot add user')
        # ensure synced state before update - exception being that the admin is
        # still the only existant user in which case, there is nothing to get
        # from the remote USER_DB.
        if len(self._user_db.get_users()) > 1:
            self.sync_with_remote(mode='receiving')
        # update
        user_id = self._user_db.add_new(
            validation_key=request.signing_key,
            encryption_key=request.encryption_key,
            roles=roles)
        # Note: add_new automatically stored the new USER_DB
        self.sync_with_remote(mode='sending')
        return user_id

    def get_response_bytes(
            self,
            user_id: int,
            ) -> bytes:
        ''' Get response bytes from admin to user

        Bytes are sent back to user outside of this tool's scope. For example,
        as file via Email. See: get_request_bytes().
        '''
        if not self._loaded:
            raise KissRegistryUnitialized(
                'registry is not yet loaded, cannot construct a response')
        # check sections existing before applying
        for section in self._response_config_sections:
            if section not in self._config.sections:
                raise KissRegistryUnknownConfigSection(
                    f'Section {section} does not exist.')
        response = RegistrationResponse.new(
            user_id=user_id,
            user_db=self._user_db.get_state(),
            config_sections={section: dict(self._config.section(section))
             for section in self._response_config_sections})
        return response.get_response_bytes()

    def set_response_bytes(self, response_bytes: bytes):
        ''' Set registration response '''

        # TODO: add warning if already loaded

        response = RegistrationResponse.from_response_bytes(response_bytes)

        for section in response.config_sections:
            self._config.section(section).update(
                response.config_sections[section])
            self._config.section(section).store()

        # only store user_id after retrieving all configuration to keep
        # application "uninitialized" until then
        self._user_id.id = response.user_id
        self._user_db.set_state(response.user_db_bytes)
        # set_state does not automatically store the user_db, hence a manual
        # call:
        self._user_db.store()
        # get full user database
        self.sync_with_remote(mode='receiving')

        # TODO: the above line also ensures syncing the user database. Sync
        # behavior of other to-be-shared data is still to be defined. From
        # admin side, everything should be synced upon change immediately while
        # here, on user side, it should receive ALL defined remote data, even
        # overwriting local ones. BUT scenarios can easily arise when
        # registration is optional and a user instance is already generating
        # data locally! >> Classical conflict resolution.
        #
        # >> See comment on #7, 07.12.2025.

        # TODO: check incoming information and log (1) the retrieved ID and (2)
        # and incoming config sections that are updated and (3) the admin that
        # did this (public singing key).

        # TODO: verify the response matching the keys.

        # TODO: update user config (admin might have done adaptions)

        # TODO: update configuration with incoming information
        # TODO: sync (or restart?)

        # TODO: clarfify how it is checked that everything worked

    def get_encryption_keys(self, roles: list[str] | str) -> list[bytes]:
        ''' Return list of (public) encryption keys for defined role(s)
        '''
        return self._user_db.get_encryption_keys(roles)

    def get_encryption_key(self, user_id: int = -1) -> bytes:
        ''' Provide encryption key (bytes) for user ID

        If no ID is provided or a negative ID, the encryption key for the
        current user will be returned.
        '''
        self._ensure_loaded()
        if user_id >= 0:
            return self._user_db.get_encryption_key(user_id)
        else:
            return self._user_db.get_encryption_key(self.user_id)

# TODO: can we register the same user twice? How would we know? We
# would need to double-check the keys (which we did not want to use as
# ID's). We could maintain some "ongoing registrations" data. Note that
# there is currently no tool supported feedback on a registration
# success (when the user has applied the registration response).

# TODO: add user information to some DB? Users may distribute to admins and
# admins re-distribute to users.
#
# We do not want to write different USER_DB versions for each user.
# Likewise, we do not want to write an information file for each user that
# is encrypted for lot's of users. However, we want to use the default
# shared file sync mechanism. This leaves:
#   * Write bulks of user data information per role.
# Consequences:
#   * One file per ROLE (not per USER)
#   * User information may be contained in multiple ROLE files.
# If user information size is SIZE_UI and size of encryption data is SIZE_KEY,
# the total size is:
#   * For one file, each user:
#       USERS * (SIZE_UI + AVG_USER_IN_ROLE * SIZE_KEY)
#   * For one file, each group:
#       ROLES * (AVG_USER_IN_ROLE * SIZE_UI + AVG_USER_IN_ROLE * SIZE_KEY)
#   * Assuming AVG_USER_IN_ROLE ~ USERS/ROLES
#       * First: USERS * SIZE_UI + USERS^2/ROLES * SIZE_KEY
#           USERS * SIZE_UI >> guaranteed
#           USERS^2/ROLES * SIZE_KEY >> certainly a problem
#       * Second: USERS * SIZE_UI + USERS * SIZE_KEY
#           USERS * SIZE_UI >> not correct admin will know all, depot
#             responsibles will be known by most roles. Worst case:
#             each role knows all users: USERS * ROLES * SIZE_UI.
#           USERS * SIZE_KEY >> also not correct since users may know
#             multiple roles input. Worst case here is, again:
#             USERS * ROLES * SIZE_UI
#       * Second corrected but worst case:
#             ROLES * USERS * (SIZE_UI + SIZE_KEY)
#
# Number examples, assuming email (16 bytes) plus name (20 bytes) rounded
# up to 50 bytes for SIZE_UI. And an encrpted key blob with 256 bytes.
#   * 10 USERS shared with all users (worst case): 10*50 + 10*10*256 = 26k
#   * 10 USERS shared with 5 ROLES: 10*5*50 + 10*5*256 = 15k
#
#   * 20 USERS shared with all users (worst case): 103k
#   * 20 USERS shared with 5 roles: 31k
