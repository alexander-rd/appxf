
# allow class name being used before being fully defined (like in same class):
from __future__ import annotations

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
    ''' Load/Store error for user ID'''

class RegistrationRequest:
    def __init__(self, data):
        self._data = data

    @property
    def encryption_key(self):
        return self._data['encryption_key']
    @property
    def signing_key(self):
        return self._data['signing_key']

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
        print(f'RegistrationRequest.from_new(): {data}')
        return cls(data)

    @classmethod
    def from_request(cls, registration_bytes: bytes):
        # TODO: error on wrong version
        data = deserialize(registration_bytes)
        print(f'RegistrationRequest.from_registration_bytes(): {data}')
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
    def new(cls, user_id, config_sections):
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
        self._location = location
        self._security = security
        self._config = config

        self._user_db = UserDatabase(location, security)
        self._user_id = UserId(location, security)

    def initialize_as_admin(self):
        ''' Initialize databse

        This function is expected to be called only once in the entire tool
        life cycle by user 0. New admins will inherit the existing data.
        '''
        self._user_id.id = 0
        self._user_db.init_user_db(user_id=self._user_id.id,
                                   validation_key=self._security.get_signing_public_key(),
                                   encryption_key=self._security.get_encryption_public_key())

    def get_request_bytes(self) -> bytes:
        ''' Get registration request bytes

        Bytes are sent to an admin outside of this tools scope. For example, as
        a file via Email.
        '''
        # TODO: add encryption which will require the AMDIN_DB
        return RegistrationRequest.new(
            self._config.get('USER'),
            self._security).get_request_bytes()

    def add_user_from_request(self, request: bytes) -> int:
        ''' Store user in databse and get user ID

        The admin is expected to use this function. The request bytes are
        generated by get_request_bytes() on user side. After user is added, the
        admin uses get_response_bytes() to send data back to user.
        '''
        return 0

    def get_response_bytes(self, user_id: int) -> bytes:
        ''' Get response bytes from admin to user

        Bytes are sent back to user outside of tis tool's scope. For example,
        as file via Email. See: get_request_bytes().
        '''
        return b''

    def set_response_bytes(self, response: bytes):
        ''' Set registration response '''

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

# TODO: add user information to some DB??
