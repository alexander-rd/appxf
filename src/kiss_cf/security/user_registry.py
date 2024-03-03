
# allow class name being used before being fully defined (like in same class):
from __future__ import annotations

import os.path
from kiss_cf.storage import StorageMethod, StorageLocation
from kiss_cf.storage import serialize, deserialize
from .security import Security
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
#

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

class UserRegistry:
    ''' User registry maintains the application user's ID an all user
        configurations the user is permitted to see. '''

    ### Methods for user side (concluded registration)
    @classmethod
    def existing_user(self,
                 location: StorageLocation,
                 config: Config,
                 id_file: str = 'user_id'):
        ''' Try to load registration ID

        This init should always be applied in a try/catch. It is intended to
        return error codes <TBD> when the registration process did not yet
        conclude. In this case, UserRegistry.new_user() shall be used.

        The provided location should be a separate path like ./data/registry.
        Files, maintained here are USER_ID (the current user's ID) and USER_123
        files with 123 being any potential user ID. This location must be
        hooked up via storage.sync with some shared storage location.
        '''
        # TODO: define error codes, mentioned above

        # TODO: create ID storable and try to load

        # TODO: update user configuration to load from USER_<ID> and try to load
        pass

    ### Methods for user side (during registration)

    def apply_registration_response(self, response: bytes):
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
