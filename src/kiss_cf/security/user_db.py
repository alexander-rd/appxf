from kiss_cf.storage import Storable, StorageMethod
from kiss_cf.security.security import Security


class UserEntry():
    def __init__(self, id: str, validation_key: bytes, encryption_key: bytes, role: str):
        self.version: int = 1
        self.id: str = id
        self.role: str = role
        self.validation_key: bytes = validation_key
        self.encryption_key: bytes = encryption_key

#! TODO: Just a note: the storage method will contain validation/encryption details.


class UserDatabase(Storable):
    def __init__(self, storage_method: StorageMethod, file: str):
        self.version = 1
        # Dictionary will first index role and then ID. For validation, we will
        # always look up ID+Role. For encryption, however, we will need keys
        # for all users of a role. Only removing a user will querry ID only.
        self.data: dict[str, dict[str, UserEntry]] = {}
        #! TODO: load this database

    def _set_bytestream(self, data: bytes):
        pass

    def _get_bytestream(self, data: bytes):
        return b''

    def add_from_security_object(self, security: Security):
        self.add(id='TBD: where to get ID from',
                 validation_key=security.get_public_key(),
                 encryption_key=security.get_public_key(),
                 role = 'USER')

    def add(self, id: str, validation_key: bytes, encryption_key: bytes, role: list[str]|str = 'user'):
        if isinstance(role, str):
            role = [role]
        for this_role in role:
            # ensure role is present
            if role not in self.data.keys():
                self.data[this_role] = {}
            # add user with role to database
            entry = UserEntry(id=id, role=this_role,
                              validation_key=validation_key, encryption_key=encryption_key)
            self.data[this_role][id] = entry

    def remove(self, id:str):
        for role in self.data.keys():
            if id in self.data[role].keys():
                del self.data[role][id]