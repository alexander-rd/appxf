import os.path
from kiss_cf.security.user_db import UserDatabase
from kiss_cf.storage import StorageMethod

class UserRegistry:
    def __init__(self,
                 admin_storage: StorageMethod,
                 user_storage: StorageMethod,
                 local_path: str = 'data/security',):
        # setup user and admin database
        self.admin_database = UserDatabase(
            storage_method=admin_storage,
            file=os.path.join(local_path, 'ADMIN_DB.data'))
        self.user_database = UserDatabase(
            storage_method=user_storage,
            file=os.path.join(local_path, 'USER_DB.data'))
        #! TODO: The user of kiss_cf should only need to define the two
        #  StorageLocations. This class must add the encryption/singing steps.

        #! TODO: How is it ensured that they will be encrypted?
        #! TODO: How is it ensured that users cannot write admin database?
