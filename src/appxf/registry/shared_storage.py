# Copyright 2024-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
"""Security layer for files shared between users"""

# allow class name being used before being fully defined (like in same class):
from __future__ import annotations

from appxf.security import Security
from appxf.storage import (
    AppxfStorageError,
    CompactSerializer,
    JsonSerializer,
    Serializer,
    Storage,
    StorageToBytes,
)

from ._public_encryption import PublicEncryption
from ._registry_base import RegistryBase
from ._signature import Signature

# SecureSharedStorage uses two meta files for which we define the serializers:
StorageToBytes.set_meta_serializer("signature", JsonSerializer)
StorageToBytes.set_meta_serializer("keys", CompactSerializer)


class SecureSharedStorage(StorageToBytes):
    """Typical setup for shared storage

    The typical setup consists of the layers:
      1) Public key encryption (to allow others access)
      2) Envelope to control writing permissions and
         provide information for manual inspection
      3) Signature for authenticity
    """

    def __init__(
        self,
        base_storage: StorageToBytes,
        security: Security,
        registry: RegistryBase,
        serializer: type[Serializer] = CompactSerializer,
    ):
        # TODO: "to roles" is missing input. Alternatively "to users" should be
        # supported. Likewise "allowed roles"/"allowed users" is required to
        # ensure (1) only allowed roles are writing the data and (2) receivers
        # can verify authenticity. BEWARE the FACTORY interface: each name in a
        # predefined path may hold files with different permissions.

        super().__init__(
            name=base_storage.name,
            location=base_storage.location,
            base_storage=base_storage,
            serializer=serializer,
        )
        self._security = security
        self._registry = registry
        # indicate unusable user with None
        if self._registry.is_initialized():
            self._user = self._registry.user_id
        else:
            self._user = None
        # TODO: is this the right way of doing it, Storage base class already
        # knows _user and may already act accordingly.

        self._signature = Signature(
            storage=base_storage.get_meta("signature"), security=security
        )
        self._public_encryption = PublicEncryption(
            storage=base_storage.get_meta("keys"), registry=registry
        )

    # TODO: update documentation below. Put elsewhere??

    # Stacking concept: The classes used here shall only:
    #  1) process bytes input/output like encrypting/decrypting while
    #  2) adding additional files
    #
    # In the previous concept, the classes called some load/store instead of
    # getting the bytes.

    # Different concept would be: this class is handling ALL BYTES and the
    # reusable classes just generate new bytes from bytes. This class would
    # then be responsible for storing/loading also the supporting files. <<
    # this is the way to go!

    # TODO: __init__ and get are missing the serializer argument

    # TODO: here and in SecureStorage.. ..document clearly which serializer is
    #  applied. The one from the base_storage or the one added to
    #  SecureShared/SecurePrivate storage.

    @classmethod
    def get(
        cls,
        base_storage: StorageToBytes,
        security: Security,
        registry: RegistryBase,
        serializer: type[Serializer] = CompactSerializer,
    ) -> Storage:
        """Get a known storage object or create one."""
        return super().get(
            name=base_storage.name,
            location=base_storage.location,
            storage_init_fun=lambda: SecureSharedStorage(
                base_storage=base_storage,
                security=security,
                registry=registry,
                serializer=serializer,
            ),
        )

    @classmethod
    def get_factory(
        cls,
        base_storage_factory: Storage.Factory,
        security: Security,
        registry: RegistryBase,
        serializer: type[Serializer] = CompactSerializer,
    ) -> Storage.Factory:
        return super().get_factory(
            base_storage=base_storage_factory,
            storage_get_fun=lambda name: SecureSharedStorage.get(
                base_storage=base_storage_factory(name),
                security=security,
                registry=registry,
                serializer=serializer,
            ),
        )

    def ensure_usable(self):
        """Check security and registry objects

        No storage operation is possible if security is not unlocked and
        registry is not initialized with user id.
        """
        if not self._security.is_user_unlocked():
            return False
        if not self._registry.is_initialized():
            return False
        if self._user is None:
            self._user = self._registry.user_id
        return True

    def exists(self) -> bool:
        if self.base_storage is None:
            raise AppxfStorageError(
                f"{self.__class__.__name__} required a base storage but you used None."
            )
        # security and registry must have appropriate states
        if not self.ensure_usable():
            return False
        # file must exist:
        if not self.base_storage.exists():
            return False
        # if a meta ends up in this function, then it also needs signature and
        # public_encryption (keys). It should, however be using the base
        # storage.
        if not self._signature.exists():
            return False
        if not self._public_encryption.exists():
            return False
        return True

    def store_raw(self, data: bytes):
        # registry and security must be initialized:
        if not self.ensure_usable():
            raise AppxfStorageError(
                "Store on SecureSharedStorage is only possible with "
                "unlocked security and initialized registry."
            )
        # encryption
        data_bytes = self._public_encryption.encrypt(data)
        self._public_encryption.store()
        # signing (encrypted data)
        self._signature.sign(data_bytes)
        self._signature.store()
        self.base_storage.store_raw(data_bytes)

    def load_raw(self) -> bytes:
        if not self.ensure_usable():
            raise AppxfStorageError(
                "Load on SecureSharedStorage is only possible with "
                "unlocked security and initialized registry."
            )
        # load raw
        data_bytes: bytes = self.base_storage.load_raw()
        if data_bytes == b"":
            return b""
        self._signature.load()
        if not self._signature.verify(data_bytes):
            # TODO: test case for failing signature
            # TODO: AppxfException
            # TODO: extend error message with infos like file
            raise Exception("Verification signature failed")
        # decryption
        self._public_encryption.load()
        data_bytes = self._public_encryption.decrypt(data_bytes)
        return data_bytes

    # TODO: id() logged the user under which the registry was opened. User and
    # role details may be reasonable added logging. But here is also no logging
    # concept added to support debug logs. Like: details on init,
