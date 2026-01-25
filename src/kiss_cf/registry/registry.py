
# allow class name being used before being fully defined (like in same class):
from __future__ import annotations
from appxf import logging

from kiss_cf.storage import sync, CompactSerializer, StorageToBytes
from kiss_cf.config import Config
from kiss_cf.setting import SettingDict
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
    '''Registry maintaining user ID and roles

    The registry supports a registration procedure where users:
     * securely share user details
     * obtain a user ID and roles
     * securely obtain (initial) configuration data

    The registry is a prerequisite for two use cases:
     * Users sharing data securely via some remote storage
     * Admins updating access credentials for users (manual and automated)
    '''
    log = logging.getLogger(__name__ + '.Registry')


    def __init__(self,
                 local_storage_factory: StorageToBytes.Factory,
                 security: Security,
                 config: Config,
                 user_config_section: str = 'USER',
                 response_config_sections: list[str] | None = None,
                 remote_storage_factory: StorageToBytes.Factory | None = None,
                 **kwargs):
        ''' Create Registry Handler

        Keyword Arguments:
            local_storage_factory -- The local storage is where your view on
                the user database is stored for offline usage. This is
                typically LocalStorage and Registry stores data via
                SecurePrivateStorage.
            security -- a local login Security object is required to employ the
                SecurePrivate storage for the local use database and
                SecureShared storage for remote_storage (see below).
            config -- The registration procedure allows to convey certain parts
                of the application configuration which may be required to
                access the remote storage mentioned above.
            user_config_section -- The name of the user configuration section
                from [config] which is shared during registration.
            response_config_sections -- A list of configuration section names
                which are exported during registration and during manual
                configuration updates.
            remote_storage_factory -- The remote storage is where the overall
                user database is stored for all users to sync with. A typical
                use case is FtpStorage while also LocalStorage may be used.
                Registry employs a SecureSharedStorage on top for stored files.
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
            base_storage=local_storage_factory('USER_DB'),
            security=security)
        self._user_db = UserDatabase(self._local_user_db_storage)
        # Matching remote storage
        if self._remote_storage_factory is None:
            self._remote_user_db_storage = None
        else:
            self._remote_user_db_storage = SecureSharedStorage(
                base_storage=self._remote_storage_factory('USER_DB'),
                security=security,
                registry=self)

        # Note: USER_DB cannot be synced from __init__ since security module
        # may not yet be unlocked.

    # TODO: response_config_sections likely needs an explicit setter to have
    # the option to define configuration settings after defining the user
    # registry. Also, this list may need to be a mapping since different roles
    # may receive different subsets of configuration data. But this should be
    # reconsidered since this part of the configuration sharing may be handled
    # via the remote synchronization. Main question is: should APPXF support a
    # user registry without shared storage? == A share of credentials without
    # any mode of updating them later?

    # #########################/
    # Some Basics
    # /

    @property
    def user_id(self):
        # Documentation in RegistryBase
        return self._user_id.id

    def is_initialized(self) -> bool:
        # Documentation in RegistryBase
        return (self._loaded or (
                self._user_id.exists() and
                self._user_db.exists()
                ))

    def _ensure_loaded(self):
        if self._loaded:
            return None
        if not self.try_load():
            KissRegistryUnitialized('Registry is not initialized.')

    def try_load(self) -> bool:
        '''Load USER ID and/or USER DB

        Returns: True if both can be loaded
        '''
        # registry is generally not available if security is not unlocked (even
        # though USER ID may be available):
        if not self._security.is_user_unlocked():
            return False

        user_id_loaded = False
        if self._user_id.exists():
            self._user_id.load()
            user_id_loaded = True

        user_db_loaded = False
        if self._user_db.exists():
            self._user_db.load()
            user_db_loaded = True

        self._loaded = user_id_loaded and user_db_loaded
        return self._loaded

    # #########################/
    # Security Support
    # /
    def sign(self, data: bytes):
        '''Sign bytes of data and return public signing key AND signature '''
        signing_key = self._security.get_signing_public_key()
        signature = self._security.sign(data)
        return signing_key, signature
    # TODO: do we really need this sign - it just wraps around the security
    # object

    def verify_signature(self,
                         data: bytes,
                         signing_user: int,
                         signature: bytes,
                         roles: list[str] | None = None
                         ) -> bool:
        ''' Return if signature is verified

        The check includes (in this order):
         * The public signing key must be known
         * The user matching the signing key must have matching role
         * The signature for the data must be verified

        Keyword arguments:
        data -- bytes of data that were signed
        signature -- signature of data
        signing_user -- the user which signed
        roles -- the signing user must have one of the roles in this list
        '''
        self._ensure_loaded()

        # user must exist
        if not self._user_db.is_registered(signing_user):
            self.log.warning(
                'Signing user %i is not available in USER DB.',
                signing_user
            )
            return False

        # verify roles
        if roles:
            if isinstance(roles, str):
                roles = [roles]
            has_role = False
            for role in roles:
                if self._user_db.has_role(signing_user, role):
                    has_role = True
                    break
            if not has_role:
                self.log.warning(
                    'Signing user %i does not have expected roles %s'
                    'they only have %s',
                    signing_user, str(roles), str(self.get_roles(signing_user))
                    )
                return False

        # verify signature:
        public_key = self._user_db.get_verification_key(user_id=signing_user)
        if (
            not self._security.verify_signature(
                data=data,
                signature=signature,
                public_key_bytes=public_key)
            ):
            self.log.warning('Signature from user %i could not be verified.',
                             signing_user)
            return False

        return True

    # #########################/
    # USER DB basic interfaces
    # /
    def get_roles(self, user_id: int | None = None) -> list[str]:
        # Documentation in RegistryBase
        if user_id is None:
            return self._user_db.get_roles()
        if user_id < 0:
            raise ValueError(
                f'User ID {user_id} is unexpected. '
                f'Expected are: None, 0 or positive user ID')
        if user_id == 0:
            # TODO: why does only require access of _user_id an ensure_loaded()
            # but not access of _user_db above and below?
            self._ensure_loaded()
            user_id = self._user_id.id
        return self._user_db.get_roles(user_id)

    def get_users(self, role: str = '') -> set[int]:
        ''' get users IDs as set

        Keyword Arguments:
            role {str} -- only users having role, '' ignores (default: '')
        '''
        return self._user_db.get_users(role=role)

    # #########################/
    # Admin Init OR Admin Keys
    # /

    def initialize_as_admin(self):
        ''' Initialize databse

        This function is expected to be called only once in the entire tool
        life cycle by user 0. New admins will inherit the existing data.
        '''
        self._user_id.id = self._user_db.init_user_db(
            validation_key=self._security.get_signing_public_key(),
            encryption_key=self._security.get_encryption_public_key())
        self._user_db.store()
        self._loaded = True
        # Note: writing into USER_ID and into USER_DB automatically stores
        # them.

        # No update of remote USER_DB - there is no one who would need that
        # with only the admin being registered.

    def get_admin_key_bytes(self) -> bytes:
        ''' Get admin keys as bytes

        Admin keys are required for new users to (1) encrypt their user data
        (registration request) and (2) verify signature of receiving
        registration data (registration response).
        '''
        self._ensure_loaded()
        admin_users = self._user_db.get_users(role='admin')
        # construct data as tuples
        data = [(id,
                 self._user_db.get_verification_key(id),
                 self._user_db.get_encryption_key(id))
                 for id in admin_users]
        return CompactSerializer.serialize(data)

    def set_admin_key_bytes(self, data: bytes):
        ''' Set admin keys from bytes obtained via get_admin_key_bytes()

        Admin keys are required for new users to (1) encrypt their user data
        (registration request) and (2) verify signature of receiving
        registration data (registration response).
        '''
        # Block usage if the user is already registered. In such a case, it
        # must not be possible to add admins.
        if self.is_initialized():
            raise KissRegistryError(
                'Cannot set admin keys on initialized registry.')

        # get original data that was a list of tuples (user_id, encryption_key,
        # signing_key)
        key_list: list[tuple] = CompactSerializer.deserialize(data)  # type: ignore

        # purge existing USER DB
        for user_id in self._user_db.get_users():
            self._user_db.purge_user(user_id)

        # add admin keys:
        for key_tuple in key_list:
            self._user_db.add(
                key_tuple[0],
                key_tuple[1], key_tuple[2],
                roles = ['admin'])
        self._user_db.store()

    def has_admin_keys(self):
        ''' Return True if USER DB has any admin keys
        '''
        admin_keys = self._user_db.get_users(role='admin')
        return bool(admin_keys)

    # ######################################/
    # Request/Response
    # /

    def get_request_bytes(self) -> bytes:
        ''' Get registration request bytes

        Bytes are sent to an admin outside of this tools scope. For example, as
        a file via Email.
        '''
        # construct request object
        if self._user_config_section:
            user_data = dict(self._config.section('USER'))
        else:
            user_data = {}
        request_object = RegistrationRequest.new(user_data, self._security)

        bytes_raw = request_object.get_request_bytes()
        bytes_encrypted, key_blob_dict = self.hybrid_encrypt(bytes_raw, 'admin')
        request = {
            'request': bytes_encrypted,
            'key_blob_dict': key_blob_dict}

        return CompactSerializer.serialize(request)

    # TODO: registry should not expose raw data since it is not encrypted.
    # the idea was that registration is secure.. ..such that insecure
    # interfaces should be removed. As of current scan, 31.12.2025, this
    # function is only used in testing.

    def get_request_data(self, request: bytes) -> RegistrationRequest:
        request_encrypted: dict = CompactSerializer.deserialize(request)

        bytes_decrypted = self.hybrid_decrypt(
            data=request_encrypted['request'],
            key_blob_dict=request_encrypted['key_blob_dict'])

        return RegistrationRequest.from_request(bytes_decrypted)

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
        self._user_db.store()

        # Note: add_new automatically stored the new user DB and sync can be
        # skipped if add_new failed:
        if user_id > 0:
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
        self._ensure_loaded()

        # check sections existing before applying
        for section in self._response_config_sections:
            if section not in self._config.sections:
                raise KissRegistryUnknownConfigSection(
                    f'Section {section} does not exist.')
        response = RegistrationResponse.new(
            user_id=user_id,
            user_db=self._user_db.get_state(),
            config_sections={
                section: dict(self._config.section(section))
                for section in self._response_config_sections
                })

        # The hybrid encryption interface from registry CANNOT be reused here
        # because the response is encrypted ONLY for the corresponding
        # registered user which only get's it's USER ID after consuming the
        # response.
        response_bytes = response.get_response_bytes()
        # encryption
        response_bytes_encrypted, key_blob_dict = self._security.hybrid_encrypt(
            response_bytes,
            public_keys={user_id: self._user_db.get_encryption_key(user_id)})
        # signing
        signature = self._security.sign(response_bytes_encrypted)

        response_data = {
            'response_encrypted': response_bytes_encrypted,
            'key_blob': key_blob_dict[user_id],
            'signing_user': self.user_id,
            'signature': signature,
        }

        return CompactSerializer.serialize(response_data)

    def set_response_bytes(self, response_bytes: bytes):
        ''' Set registration response '''
        if self.is_initialized():
            self.log.warning('User is already initialized with ID %i.', self.user_id)

        response_data: dict = CompactSerializer.deserialize(response_bytes)

        # check signature
        response_encrypted: bytes = response_data['response_encrypted']
        if (
            not self.verify_signature(
                data=response_encrypted,
                signature=response_data['signature'],
                signing_user=response_data['signing_user'],
                roles = ['admin'])
            ):
            raise KissRegistryError('Signature could not be verified')

        response_bytes = self._security.hybrid_decrypt(
            data=response_encrypted,
            key_blob_dict={
                self._security.get_encryption_public_key():
                    response_data['key_blob']
                })

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

        self.log.info(
            'Registration response assigned USER ID %i '
            'and included config section %s.',
            response.user_id, str(response.config_sections.keys())
            )

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

    # ###################
    # Security functions
    # /

    # They are wrapping the Security methods with additional registry steps.

    def hybrid_encrypt(
            self,
            data: bytes,
            roles: str | list[str]
            ) -> tuple[bytes, dict[int, bytes]]:
        # Documentation in RegistryBase
        self._ensure_loaded()

        # input ambiguity:
        if isinstance(roles, str):
            roles = [roles]
        # ensure admin can always read data:
        if 'admin' not in roles:
            roles.append('admin')

        pub_key_dict = self._user_db.get_encryption_key_dict(roles)
        # always add own key (if registry is initialized.. ..hybrid_encrypt is
        # also used for the registration request):
        if self.is_initialized() and self.user_id not in pub_key_dict:
            pub_key_dict[self.user_id] = (
                self._security.get_encryption_public_key())

        return self._security.hybrid_encrypt(data, pub_key_dict)

    def hybrid_decrypt(
            self,
            data: bytes,
            key_blob_dict: dict[int, bytes]
            ) -> bytes:
        # Documentation in RegistryBase
        self._ensure_loaded()

        return self._security.hybrid_decrypt(
            data=data,
            key_blob_dict=key_blob_dict,
            blob_identifier=self.user_id)

    # ############################/
    # Manual Configuration Updates
    # /

    def get_manual_config_update_bytes(
        self,
        sections: list[str] | None = None,
        include_user_db: bool = True
        ) -> bytes:
        ''' get manual configuration update bytes

        Config sections are exported with their full state. Settings would be
        added or removed and all options (like visibility) are included.
        Sections that are included in the section list but are not existing any
        more in the config object are removed on the receiving side. However,
        FILES FOR CONFIG sections ARE NOT DELETED.
        '''
        if sections is None:
            sections = self._response_config_sections
        self._ensure_loaded()

        # TODO: block export if user is not admin.

        data = {
                'config_sections': {},
                'obsolete_config_sections': []
            }
        for section in sections:
            if section not in self._config.sections:
                data['obsolete_config_sections'].append(section)
                continue
            data['config_sections'][section] = self._config.section(
                section
                ).get_state(options=SettingDict.FullExport)
        if include_user_db:
            data['user_db'] = self._user_db.get_state()
        data_bytes = CompactSerializer.serialize(data)

        # sign and encrypt:
        return self._security.hybrid_signed_encrypt(
            data=data_bytes,
            public_keys=self._user_db.get_encryption_key_dict(
                roles=self._user_db.get_roles())
            )

    def set_manual_config_update_bytes(self, data: bytes):
        ''' update configuration and user db

        Bytes are obtained from get_manual_config_update_bytes() on admin side.
        '''
        self._ensure_loaded()

        # decrypt and verify signature:
        data_bytes, author_key = self._security.hybrid_signed_decrypt(
            data=data,
            blob_identifier=self.user_id,
            )

        # TODO: check if author_key is KNOWN and an ADMIN
        author_id = self._user_db.get_user_by_validation_key(author_key)
        if author_id is None:
            raise KissRegistryError(
                'Author of manual configuration update is unknown.')
        if not self._user_db.has_role(author_id, 'admin'):
            raise KissRegistryError(
                'Author of manual configuration update is not an admin.')

        # unpack data
        data_dict: dict = CompactSerializer.deserialize(data_bytes)
        # apply to config sections
        for section in data_dict.get('obsolete_config_sections', []):
            if section in self._config.sections:
                self._config.remove_section(section)
        for section, section_state in data_dict.get('config_sections', {}).items():
            if section not in self._config.sections:
                self._config.add_section(section)
            self._config.section(section).set_state(
                section_state, options=SettingDict.FullExport)
            self._config.section(section).store()
        # update user db
        if 'user_db' in data_dict:
            self._user_db.set_state(data_dict['user_db'])
            self._user_db.store()

    # #########################/
    # Remote Sync Handling
    # /

    def sync_with_remote(self, mode: str):
        ''' Sync local registry with remote location.

        A sync should happen at every startup and/or before any sync of shared
        data. Additionally, sync is executed when admin adds a new member or
        when user adds the registration response.

        The following prerequisites must be met for the sync to be successful:
          * the user has unlocked the Security object
          * the user is registered (is_initialized())
        '''
        if self._remote_user_db_storage is None:
            self.log.debug('No remote storage for sync defined, skipping sync.')
            return

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
