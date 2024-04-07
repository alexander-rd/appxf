
from typing import Any

from .storage import Storage, StorageMethodDummy
from .storable import Storable
from .serialize import serialize, deserialize

# MetaData (aka "Two Class serializers"):
#
# Data Class: has fields for the data and can provide it's data as
# bytestream.
#   * from_bytes() / to_bytes()
#
# Storable Class: embeds the data class, may forward data from it.
#
# WHY DO WE NEED TWO CLASSES?!
#
# Others: PublicEncryptionData, SignatureData
#
# Only byte until now: RegistrationRequest, RegistrationResponse (and based on
# typed dict)
#
# Weird embedding with SyncData. It's file handling is manually done in the
# sync routines (and based on dict derivation)

# UserDataBase (aka "Manual dict handling"): uses a from_dict constructor and
# would apply version checks here as well as manually taking over the data.

# ConfigSection (aka "Late format decision"): it does not act as a Storable. It
# would store only it's values (not it's configuratoin). It relies on
# serialize/deserialize but not more.

# Summary:
#   * It is a good idea to abstract a class to bundle data.
#   * Using dict/typed dict leads to code, I do not like and where code
#     completion does not work well.
#   * when coupling to the generic storable, it may be helpful to support
#     _update_dict_state() and _get_dict_state() which default to apply self
#     while encourage to handle version correctness and manual transition.

# Next steps:
#   * (/) Write the byte handler (default option)
#   * (/) Rewrite meta to use the new class
#   * (/) Extend to JSON writing and test with meta data
#   ? Format identification > TODO
#   * Roll out to other classes above or place TODO remarks
#

class DictStorable(Storable):
    ''' Store class state as dictionaty.

    By default implementation, it stores the classes __dict__ which contains
    all class fields. You may update _set_dict() and _get_dict() to store
    another dictionary or perform modifications.

    It is recommended that the deriving class applies a _version field. Onc a
    new version is introduced and you want to achieve compatibility, you can
    overload _set_dict().
    '''
    def __init__(self,
                 storage: Storage = StorageMethodDummy(),
                 format: str = ''):
        super().__init__(storage)
        self._format = format

    def _get_dict(self) -> dict[str, Any]:
        data = self.__dict__.copy()
        # strip storage and settings
        del data['_storage']
        return data

    def _set_dict(self, data: dict[str, Any]):
        self.__dict__.update(data)

    def _get_bytestream(self) -> bytes:
        data = self._get_dict()
        return serialize(data)

    def _set_bytestream(self, data: bytes):
        dict_data: dict[str, Any] = deserialize(data)
        self._set_dict(dict_data)
