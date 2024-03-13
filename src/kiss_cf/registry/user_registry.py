
# allow class name being used before being fully defined (like in same class):
from __future__ import annotations
import typing

import os.path
from kiss_cf.storage import StorageMethod, StorageLocation, Storable
from kiss_cf.storage import serialize, deserialize
from kiss_cf.config import Config
from kiss_cf.security import Security, SecurePrivateStorageMethod
from .user_db import UserDatabase

# USER SIDE:
#  * Access to config:
#    * contains USER data
#    * apply config data received via request response
#  * The local Security object:
#    * to get the public encryption/signing keys
#    >> no need to store this information
#
# ADMIN SIDE:
#  * Access to user_db to perform the registration
#  * consistency to USER data serialization

# 11.03.2024: Analysis of required data structure
#
# We need the following data structures
# * request and response messages - to be resolved by the required data
#   structures
# * USER_ID: each application user must know it's ID. No ID known == not
#   registered.
# * USER_DB: application users need to know keys of other users and affected
#   roles
# * ADMIN_DB: required mechanism to verify the USER_DB
# * USER_DATA_DB: possibly merged with USER_DB to contain detailed user
#   information (in addition to the ID's)
#
# From the list above, the ADMIN_DB equals the USER_DB and the USER_DATA_DB
# implementation can be delayed. Only open question is: where to maintain the
# USER_ID.
#
# Alternative A: Maintain in scope of USER_DB. Like config, the (then called)
# REGISTRY would maintain 1xUSER_DB, rolesx USER_DATA_DB and 1x USER_ID files.
# It would need a location object (path) to store all files and the security
# object (to automatically use local encryption).
#
# Registry is constructed with reference to config, security and location.

class KissExceptionUserId(Exception):
    ''' Load/Store error for user ID '''

class KissExceptionRegistrationResponse(Exception):
    ''' Error with handling a registration response '''

class KissExceptionRegistryUnitiialized(Exception):
    ''' Trying to use an uninitialized registry '''


class RegistrationRequest:
    def __init__(self, data):
        self._data = data

    @property
    def encryption_key(self):
        return self._data['encryption_key']
    @property
    def signing_key(self):
        return self._data['signing_key']
    @property
    def user_data(self):
        return self._data['user_data']

    @classmethod
    def new(cls,
            user_data,
            security: Security
           ):
        data = {
            'version': 1,
            'user_data': user_data,
            'signing_key': security.get_signing_public_key(),
            'encryption_key': security.get_encryption_public_key(),
            'test_blob': 'hello',
            'test_signature': security.sign(b'hello'),
            'test_encrypted': b'hello',
            }
        # TODO: no option to test encryption key (on this path) since there is
        # no encryption based on the private key.
        #print(f'RegistrationRequest.from_new(): {data}')
        return cls(data)

    @classmethod
    def from_request(cls, registration_bytes: bytes):
        # TODO: error on wrong version
        data = deserialize(registration_bytes)
        #print(f'RegistrationRequest.from_registration_bytes(): {data}')
        return cls(data)

    def get_request_bytes(self) -> bytes:
        # TODO: verify signing key
        return serialize(self._data)


class RegistrationResponse():
    def __init__(self, data):
        self._data = data

    @property
    def user_id(self):
        return self._data['user_id']

    @property
    def config_sections(self):
        return self._data['config_sections']

    @classmethod
    def new(cls, user_id: int, config_sections: dict[str, dict[str, typing.Any]]):
        data = {
            'version': 1,
            'user_id': user_id,
            'config_sections': config_sections
            }
        return cls(data)

    @classmethod
    def from_response_bytes(cls, registration_response: bytes):
        data = deserialize(registration_response)
        return cls(data)

    def get_response_bytes(self) -> bytes:
        return serialize(self._data)

class UserId(Storable):
    def __init__(self,
                 location: StorageLocation,
                 security: Security):
        super().__init__(SecurePrivateStorageMethod(
            location.get_storage_method('USER_ID'),
            security))
        self._id: int = -1

    @property
    def id(self):
        ''' The USER ID '''
        # error if still unloaded
        if self._id < 0 and not self.storage.exists():
            raise KissExceptionUserId('Cannot access USER ID: not yet written')
        # ensure loaded
        if self._id < 0:
            self.load()
        return self._id

    @id.setter
    def id(self, user_id: int):
        self._id = user_id
        self.store()

    def _set_bytestream(self, data: bytes):
        self._id = int.from_bytes(data, 'big', signed=False)
        return super()._set_bytestream(data)

    def _get_bytestream(self) -> bytes:
        return self._id.to_bytes(2, 'big', signed=False)



class UserRegistry:
    ''' User registry maintains the application user's ID an all user
        configurations the user is permitted to see. '''

    def __init__(self,
                 location: StorageLocation,
                 security: Security,
                 config: Config):
        self._loaded = False
        self._location = location
        self._security = security
        self._config = config

        self._user_db = UserDatabase(location, security)
        self._user_id = UserId(location, security)

    def is_initialized(self) -> bool:
        return (self._loaded or (
                self._user_id.storage.exists() and
                self._user_db.storage.exists()
                ))

    def try_load(self) -> bool:
        if not self.is_initialized():
            return False
        self._user_id.load()
        self._user_db.load()
        self._loaded = True
        return True


    def initialize_as_admin(self):
        ''' Initialize databse

        This function is expected to be called only once in the entire tool
        life cycle by user 0. New admins will inherit the existing data.
        '''
        self._user_id.id = self._user_db.init_user_db(
            validation_key=self._security.get_signing_public_key(),
            encryption_key=self._security.get_encryption_public_key())
        self._loaded = True

    def get_request_bytes(self) -> bytes:
        ''' Get registration request bytes

        Bytes are sent to an admin outside of this tools scope. For example, as
        a file via Email.
        '''
        # TODO: add encryption which will require the AMDIN_DB

        # TODO: add warning message the _loaded is True
        return RegistrationRequest.new(
            self._config.get('USER'),
            self._security).get_request_bytes()

    def get_request_data(self, request: bytes) -> RegistrationRequest:
        return RegistrationRequest.from_request(request)

    def add_user_from_request(self,
                              request: RegistrationRequest,
                              roles: list[str]=['user']) -> int:
        ''' Store user in databse and get user ID

        The admin is expected to use this function. The request bytes are
        generated by get_request_bytes() on user side. After user is added, the
        admin uses get_response_bytes() to send data back to user.
        '''
        if not self._loaded:
            raise KissExceptionRegistryUnitiialized('registry is not yet loaded, cannot add user')
        return self._user_db.add_new(
            validation_key=request.signing_key,
            encryption_key=request.encryption_key,
            roles=roles)

    def get_response_bytes(self, user_id: int, sections: list[str] = []) -> bytes:
        ''' Get response bytes from admin to user

        Bytes are sent back to user outside of tis tool's scope. For example,
        as file via Email. See: get_request_bytes().
        '''
        if not self._loaded:
            raise KissExceptionRegistryUnitiialized('registry is not yet loaded, cannot construct a response')
        # check sections existing before applying
        for section in sections:
            if section not in self._config.sections:
                raise KissExceptionRegistrationResponse(
                    f'Section {section} does not exist.')
        response = RegistrationResponse.new(
            user_id,
            {section: self._config.get(section) for section in sections})
        return response.get_response_bytes()

    def set_response_bytes(self, response_bytes: bytes):
        ''' Set registration response '''

        # TODO: add warning if already loaded

        response = RegistrationResponse.from_response_bytes(response_bytes)

        for section in response.config_sections.keys():
            print(f'{section}: {response.config_sections[section]}')
            # TODO: store configuration
            for option in response.config_sections[section].keys():
                self._config.set(
                    section, option,
                    response.config_sections[section][option])
        self._config.store()

        # only store user_id only after retrieving all configuration to keep
        # application "uninitialized"
        self._user_id.id = response.user_id
        self._user_id.store()

        # TODO: check incoming information and log (1) the retrieved ID and (2)
        # and incoming config sections that are updated and (3) the admin that
        # did this (public singing key).

        # TODO: verify the response matching the keys.

        # TODO: update user config (admin might have done adaptions)

        # TODO: update configuration with incoming information
        # TODO: sync (or restart?)

        # TODO: clarfify how it is checked that everything worked
        pass

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
# If user information size is SIZE_UI and size of encryption data is SIZE_KEY, the
# total size is:
#   * For one file, each user: USERS * (SIZE_UI + AVG_USER_IN_ROLE * SIZE_KEY)
#   * For one file, each group: ROLES * (AVG_USER_IN_ROLE * SIZE_UI + AVG_USER_IN_ROLE * SIZE_KEY)
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
