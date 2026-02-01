''' signature behavior for authenticity '''

from __future__ import annotations

from appxf.storage import Storage, Storable
from appxf.security import Security


class Signature(Storable):
    ''' Maintain public key and signature

    Generated is a class that knows a Security object for signing/verification
    and a Storage to store/load the signature data.

    sign() will take a public key and data to fill this class. The class can
    then be stored.

    load() will load a public key and signature. The class can then be used
    to verify() data.
    '''
    def __init__(self,
                 storage: Storage,
                 security: Security,
                 **kwargs):
        super().__init__(storage=storage, **kwargs)
        self._security = security
        self._version = 1
        self.pub_key: bytes = b''
        self.signature: bytes = b''

    @property
    def public_key(self):
        return self.pub_key

    # Set attribute mask to exclude not needed objects
    attribute_mask = Storable.attribute_mask + ['_security']

    def verify(self, data: bytes):
        ''' Verify loaded signature

        load() has to be executed, before.'''
        return self._security.verify_signature(
            data=data,
            signature=self.signature,
            public_key_bytes=self.pub_key)
        # TODO: there is no verification if the signing key was actually
        # authorized to write the data

    def sign(self, data: bytes):
        ''' Sign data based on public key in Security object

        Intended is to store() the signature afterwards '''
        self.pub_key = self._security.get_signing_public_key()
        self.signature = self._security.sign(data)
