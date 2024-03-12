import builtins
import io
import os
import pickle
from datetime import datetime, timedelta

from kiss_cf.security import Security
from kiss_cf.storage import Storable, StorageMethod, StorageLocation, ClassDictAsJsonStorable
from .user_db import UserDatabase

class Envelope(ClassDictAsJsonStorable):
    ''' Synchronization data

    The envelope collects synchronization data like timestamp, source and
    target information. The envelope is stored in a separate human readable
    file.

    Seprate file. The file name extends the base file name (from the Storable)
    with an ID that is provided by the SyncMethod. While not being encouraged
    (and not tested), this enables synchronization with multiple targerts.

    Human readable: allows to do manual spot checks in the database with
    otherwise encrypted data.
    '''
    def __init__(self, base_file: str, sync_method_id: str, storage_method: StorageMethod):
        super().__init__(storage = storage_method, file=base_file + '.' + sync_method.__class__.__name__)
        self.version = 1
        self.timestamp = datetime.utcnow()
        self.from_user_id: str = ''
        self.from_role: str = ''
        self.to_role_list: list[str] = []

# Shall be stored unencrpted. Otherwise it will be impossible to read. Could be
# signed, though but signature can be checked later.
#
# Storage method can handle the location. If I derive from a generic Storable
# that pickles for unencrypted storage, we might be quite good, here.

class EncryptedSyncMethod(Sync):
    ''' Ensure encryption for specific role '''
    def __init__(self,
                 local: StorageLocation,
                 remote: StorageLocation,
                 user_database: UserDatabase,
                 base_id: str = 'EncryptedSync',
                 sync_threshold_minutes: int = 60,
                 ):
        super().__init__(local, remote,
                         sync_threshold_minutes=sync_threshold_minutes)
        self.version = 1
        self.user_database = user_database
        self.sync_id = base_id + '_' + str(self.version)

    def sync_file(self, file,
                  timedetla_remote_minus_local: timedelta | None):
        # 1) Get more detailed timestamps.
        #   * Local files do not have additional time information.
        #   * The Storage Method should implement the additional timestamp.
        # Intermediate conclusion: The "refined timestamp" might not be worth
        # the effort with the effort being mandating timestamp storage on both
        # sides.
        #
        # Only way to fix this would be that the sync method adds time stamp
        # information into a local envelope (extra file). This would also imply
        # that refined timestamp handling is part of envelope handling.
        local_envelope = self._get_envelope(file, self.location.get_storage_method())
        remote_enevelope = self._get_envelope(file, self.remote_location.get_storage_method())
        # 2) Decide on sync direction

    # TODO UPGRADE: protect against double syncing. Lock or done file? The envelope
    # could be interpreted as 'done' file.
    #
    # Note: Local files are protected well enough (local single thread). Sync
    # Location files will be protected if they follow the same procedure on
    # sync fiels.
    #
    # Hopefully some reuse emerges (Chains) such that the lock/done file will
    # become generic behavior

    def _sync_to_location(self):
        # 1) Verify authorization
        #   * The storable must define which roles are allowed to write.
        #   * requires knowing who we are
        # 2) Load data from storable
        # 3) encrypt to location
        # 4) add signature
        # 5) add location envelope
        pass

    def _sync_from_location(self):
        # 1) Verify location envelope
        #   * author is allowed to write
        # 2) verify signature
        # 3) decrypt from location
        # 4) store locally
        # 5) add storable envelope
        pass

    def _get_envelope(self, file, method):
        # TODO: The storage method for the envelope is a bit of a problem. For
        # remote locations, this is fine (security is added by means of this
        # sync class). But for the method taken just from the storable, this
        # does not work. The storable should use a SecureStorageMethod while
        # the Envelope should use a non-secure one.
        #
        # Conclusion: The sync should sync two locations. Both locations
        # provide the most basic StorageMethod.
        #
        # TODO: The SecureStorageMethod must then be reimplemented to wrap the
        # basic StorageMethod.
        storable = Envelope(base_file=file,
                            sync_method_id=self.__class__.__name__,
                            storage_method=method)
        storable.load()

        return {'timestamp': datetime.utcnow()}


#class EncryptedAndSignedSyncMethod(EncryptedSyncMethod):
#    def __init__(self):
#        pass


# !!! IMPORTANT: Adding the envelope is not anymore a StorageMethod !!!
#
# Intend of the StorageMethod's was to work together with Storables.
# Enveloping, Singing and further stuff is NOT intended to work wit Storables!
# They now work together with StorageLocations via sync.
class EnvelopedStorageMethod(StorageMethod):
    def __init__(self, base_storage_method: StorageMethod):
        super().__init__()
        self.base_storage_method = base_storage_method

    def load(self) -> bytes:
        pass

    def store(self, data: bytes):
        pass