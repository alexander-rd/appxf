
# allow class name being used before being fully defined (like in same class):
from __future__ import annotations

import os.path
from kiss_cf.security.user_db import UserDatabase
from kiss_cf.storage import StorageMethod, StorageLocation
from kiss_cf.config import Config

class UserRegistry:

    ### Methods for user side (concluded registration)
    def __init__(self,
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
    @classmethod
    def new_user(cls, config: Config, signing_key: bytes, encrypting_key: bytes):
        obj = cls()
        # TODO: this implementation needs improvement
        obj.config = config
        obj.signing_key = signing_key
        obj.encrypting_key = encrypting_key

    def get_request_bytes(self) -> bytes:
        # TODO: put config and keys into a bytestream

        # TODO: data should be signed to ensure the key is working
        return b''

    def apply_registration_response(self, response: bytes):
        # TODO: check incoming information and log (1) the retrieved ID and (2)
        # and incoming config sections that are updated and (3) the admin that
        # did this (public singing key).

        # TODO: verify the response matching the keys.

        # TODO: update user config (adming might have done adaptions)

        # TODO: update configuration with incoming information
        # TODO: sync (or restart?)

        # TODO: clarfify how it is checked that everything worked
        pass

    ### Methods for admin side
    @classmethod
    def from_request_bytes(cls, request: bytes) -> UserRegistry:
        # TODO unpack the bytes (and store)

        # TODO Open question "config object nature": note that or
        # "for_new_user", the config object can be equivalent to the one
        # aplication config. The one we have here should be only some sections
        # as dictionaries.

        # TODO: How do we ensure the keys are correct? For encryption key:
        # registration will fail on user side. For singing key: could be done
        # here by verifying the content.
        return cls()

    def get_user_config() -> Config:
        ''' Return user config for inspection. '''
        # TODO: See above: Open question "config object nature".
        return Config()

    def register():
        ''' Register current user in user DB '''
        # TODO: add to user_db and retrieve ID

        # TODO: can we register the same user twice? How would we know? We
        # would need to double-check the keys (which we did not want to use as
        # ID's). We could maintain some "ongoing registrations" data. Note that
        # there is currently no tool supported feedback on a registration
        # success (when the user has applied the registration response).
        pass

    def get_response_bytes(self) -> bytes:
        ''' Provide registration response '''
        # TODO: add the config data that shall be passed (missing in interface)

        # TODO: retrieve user ID and add to package
