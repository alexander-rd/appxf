''' Location that requires fake-credentials to access

Implemented as mock for remote locations like FTP during the initialization
procedure.
'''

from appxf_private.storage import LocalStorage
from appxf_private.setting import Setting

class CredentialLocationMock(LocalStorage):

    credential = 'yes, sir!'

    config_properties = {
        'credential': Setting.new(str)}

    def __init__(self, path: str, credential: str = ''):
        if credential != self.credential:
            raise Exception('Open location without having the credentials')
        super().__init__(path)
