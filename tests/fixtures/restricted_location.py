''' Location that requires fake-credentials to access

Implemented as mock for remote locations like FTP during the initialization
procedure.
'''

from kiss_cf.storage import LocalStorageMaster
from kiss_cf.setting import AppxfSetting

global_credential = 'yes, sir!'


class CredentialLocationMock(LocalStorageMaster):

    config_properties = {
        'credential': AppxfSetting.new(str)}

    def __init__(self, path: str, credential):
        if not credential == global_credential:
            raise Exception('Open location without having the credentials')
        super().__init__(path)
