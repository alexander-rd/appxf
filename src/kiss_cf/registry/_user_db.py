from appxf import logging
from kiss_cf.storage import Storable, Storage, CompactSerializer
from typing import Set, TypedDict


class KissUserDatabaseException(Exception):
    ''' Error in User Database handling '''


class UserEntry(TypedDict):
    id: int
    roles: list[str]
    validation_key: bytes
    encryption_key: bytes

# TODO: do we need the extra role storage in the UserEntry?


class UserDatabase(Storable):
    log = logging.getLogger(__name__ + '.UserDatabase')

    def __init__(self, storage_method: Storage, **kwargs):
        super().__init__(storage_method, **kwargs)

        self._version = 1
        # ID handling:
        self._unused_id_list = []
        # negative user IDs are not allowed: we use negative user IDs as error
        # indicator for adding new users which indicates potential duplicates
        # with negative user ID such that even the initial admin should not use
        # ID 0.
        self._next_id = 1
        # The user_map maps ID's to UserEntry objects (dictionaries).
        self._user_db: dict[int, UserEntry] = {}
        # The role_map maps roles to lists of ID's to quickly collect lists of
        # keys.
        self._role_map: dict[str, Set] = {'admin': set(), 'user': set()}


    attributes = ['_version', '_next_id', '_unused_id_list', '_user_db', '_role_map']
    # TODO: should apply custom get_state to apply version check

    # TODO: next_id / unused_id_list should rather be re-created than stored
    # and loaded (more prone for errors)

    # serialized get_state/set_state to transfer an initial user_db from admin
    # to new user:
    def get_state_serialized(self) -> bytes:
        return CompactSerializer.serialize(self.get_state())

    def set_serialized_state(self, data: bytes):
        self.set_state(CompactSerializer.deserialize(data))
        self.store()

    def init_user_db(self,
                     validation_key: bytes,
                     encryption_key: bytes) -> int:
        # forward to reuse function with add_new()
        user_id = self.add_new(
            validation_key=validation_key,
            encryption_key=encryption_key,
            roles=['user', 'admin'])
        return user_id

    def get_users(self) -> list[int]:
        return list(self._user_db.keys())

    def add_new(self,
                validation_key: bytes,
                encryption_key: bytes,
                roles: list[str] | str = 'user') -> int:
        ''' add user with UNKNOWN user Id, returning new user ID

        Negative user IDs are invalid: Existing keys are checked. If the keys
        already exist and are consistent, the existing user ID is returned and
        no new user ID will be added. If one of the keys already exists but the
        entry is inconsistent, a NEGATIVE user ID is returned. This implies
        that duplicate keys are not possible.
        '''
        if isinstance(roles, str):
            roles = [roles.lower()]
        else:
            roles = [role.lower() for role in roles]

        # check for existing keys (users)
        for user_id, user_entry in self._user_db.items():
            match_found = 0
            if user_entry['validation_key'] == validation_key:
                match_found += 1
            if user_entry['encryption_key'] == encryption_key:
                match_found += 1
            # if keys exist with consistent IDs, update roles and conclude
            if match_found == 2:
                self.log.info(f'new user already existing with ID {user_id}')
                self.set_roles(user_id, roles)
                self.store()
                return user_id
            # if keys exist but are inconsistent:
            if match_found == 1:
                # return the negative user ID (we ensured that user IDs start
                # with 1, not with 0)
                self.log.info(f'new user keys already exist for user ID {user_id}')
                return -user_id

        # TODO: get determine new ID (implementation might already consider
        # sys.maxsize)
        user_id = self._next_id
        self._next_id += 1
        self.log.info(f'adding new user with {user_id}, next: {self._next_id}')

        # forward to reuse function with init_user_db()
        self.add(user_id=user_id,
                 validation_key=validation_key,
                 encryption_key=encryption_key,
                 roles=roles)
        self.store()
        return user_id

    def add(self,
            user_id: int,
            validation_key: bytes,
            encryption_key: bytes,
            roles: list[str]):

        roles = [role.lower() for role in roles]

        entry = UserEntry(id=user_id, roles=roles,
                          validation_key=validation_key,
                          encryption_key=encryption_key
                          )
        # entry = UserEntry2(id=user_id, validation_key=validation_key)
        self._user_db[user_id] = entry

        for role in roles:
            # ensure role is present
            if role not in self._role_map.keys():
                self._role_map[role] = set()
            self._role_map[role].add(user_id)

    def remove_user(self, user_id: int):
        ''' Remove user by deleting all role assignments

        The user's signing key remains existent in case there is still shared
        data from this user that might need signature validation.
        '''
        for role in self._role_map:
            if user_id in self._role_map[role]:
                self._role_map[role].remove(id)
            if (not self._role_map[role] and
                    not role == 'user' and
                    not role == 'admin'):
                del self._role_map[role]

    def purge_user(self, user_id: int):
        ''' Like remove_user but also deleting the public keys

        Using this should ensure that there is no data present anymore that
        needs to be authenticated against this user's signing key.
        '''
        pass
        # TODO: implementation is missing

    def is_registered(self, user_id):
        return user_id in self._user_db

    def _get_user_entry(self, user_id) -> UserEntry:
        if not self.is_registered(user_id):
            raise KissUserDatabaseException(f'{user_id} is not registered.')
        return self._user_db[user_id]

    def has_role(self, user_id: int, role: str):
        role = role.lower()
        if role not in self._role_map.keys():
            return False
        return user_id in self._role_map[role]

    def get_validation_key(self, user_id: int) -> bytes:
        return self._get_user_entry(user_id)['validation_key']

    def get_encryption_key(self, user_id: int) -> bytes:
        return self._get_user_entry(user_id)['encryption_key']

    def get_encryption_keys(self, roles: list[str] | str) -> list[bytes]:
        keys: list[bytes] = []
        if isinstance(roles, str):
            roles = [roles.lower()]
        else:
            roles = [role.lower() for role in roles]

        for this_role in roles:
            keys += [
                self._user_db[user]['encryption_key']
                for user in self._user_db.keys()
                if self.has_role(user, this_role)
                ]
        # TODO: the above may cycle multiple times over the same users. It
        # would be more efficient to collect user ID's from _role_map and then
        # accumulate the keys from that.
        keys = list(set(keys))
        return keys

    def get_roles(self, user_id: int | None = None) -> list[str]:
        if user_id is None:
            # admin and user will always be present given that _role_map is
            # intialized with those two roles and those two roles are never
            # removed.
            return list(self._role_map.keys())
        entry = self._get_user_entry(user_id)
        return entry['roles']

    def set_roles(self, user_id: int, roles: list[str] | str):
        ''' set roles for user ID '''
        if user_id not in self._user_db:
            raise ValueError(f'User ID {user_id} is not registered.')

        if isinstance(roles, str):
            roles = [roles]

        current_roles = self.get_roles(user_id)
        for role in current_roles:
            if role not in roles:
                self._role_map[role].remove(user_id)
        for role in roles:
            if role not in current_roles:
                self._role_map[role].add(user_id)
        self._user_db[user_id]['roles'] = roles
        self.store()

    def get_user_config(self, user_id: int):
        # TODO: implementation and define return value. Might be a dictionary
        # or a Config object.
        #  1) It shall only contain a USER section
        #  2) It shall be usable with a config editor (read only)
        pass

    # Adding logging to store/load
    def store(self, **kwargs):
        self.log.debug(f'Storing USER DB')
        return super().store(**kwargs)

    def load(self, **kwargs):
        self.log.debug(f'Loading USER DB')
        return super().load(**kwargs)

# TODO: Support is needed to verify conditions to purge a user. This requires a
# complete registry of all files the user may have stored in the past. This
# data would need to be re-written by the admin before purging.
