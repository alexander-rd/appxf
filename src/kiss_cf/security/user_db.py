from kiss_cf.storage import Storable, StorageMethod
from kiss_cf.security.security import Security
from typing import Dict, Set

class UserEntry(dict):
    def __init__(self, user_id: int, validation_key: bytes, encryption_key: bytes, roles: list[str]):
        self.version: int = 1
        self.id: int = user_id
        self.roles: list[str] = roles
        self.validation_key: bytes = validation_key
        self.encryption_key: bytes = encryption_key

#! TODO: Just a note: the storage method will contain validation/encryption details.


class UserDatabase(Storable):
    def __init__(self, storage_method: StorageMethod):
        super().__init__(storage_method)

        self.version = 1
        # ID handling:
        self._unused_id_list = []
        self._next_id = 0
        # The user_map maps ID's to UserEntry objects (dictionaries).
        self._user_db: Dict[int, UserEntry] = {}
        # The role_map maps roles to lists of ID's to quickly collect lists of
        # keys.
        self._role_map: Dict[str, Set] = {}

    ### ID Hanlinng

    # TODO: implementation for storage shall serialize __init__.
    def _set_bytestream(self, data: bytes):
        pass
    def _get_bytestream(self, data: bytes):
        return b''

    def add_new(self,
                validation_key: bytes,
                encryption_key: bytes,
                roles: list[str]|str = 'user'):
        if isinstance(roles, str):
            roles = [roles]

        # TODO: get determine new ID (implementation might already consider
        # sys.maxsize)
        user_id = self._next_id
        self._next_id += 1

        entry = UserEntry(user_id=user_id,
                          validation_key=validation_key,
                          encryption_key=encryption_key,
                          roles=roles)
        self._user_db[user_id] = entry

        for role in roles:
            # ensure role is present
            if roles not in self._role_map.keys():
                self._role_map[role] = set()
            self._role_map[role].add(user_id)

    def remove_user(self, user_id: int):
        ''' Remove user by deleting all role assignments

        The user's signing key remains existent in case there is still shared
        data from this user that might need signature validation.
        '''
        for role in self.data.keys():
            if id in self.data[role].keys():
                del self.data[role][id]

    def purge_user(self, user_id: int):
        ''' Like remove_user but also deleting the public keys

        Using this should ensure that there is no data present anymore that
        needs to be authenticated against this user's signing key.
        '''

    def has_role(user_id: int, role: str):
        # TODO: implementation
        return False

    def get_validation_key(self, user_id: int) -> bytes:
        # TODO: implementation
        return b''

    def get_encryption_key(self, user_id: int) -> bytes:
        # TODO: implementation
        return b''

    def get_encryption_keys(self, roles: list[str]|str) -> list[bytes]:
        # TODO: implementation
        return []

    def get_roles(self, user_id: int) -> list[str]:
        return []

    def get_user_config(self, user_id: int):
        # TODO: implementation and define return value. Might be a dictionary
        # or a Config object.
        #  1) It shall only contain a USER section
        #  2) It shall be usable with a config editor (read only)
        pass

# TODO: Support is needed to verify conditions to purge a user. This can only
# be done together with StorageLocation implementation that needs to track all
# StorageLocations and registered storages.
