''' Location that requires fake-credentials to access

Implemented as mock for remote locations like FTP during the initialization
procedure.
'''

from kiss_cf.storage import LocalStorageLocation
from kiss_cf.gui import KissOption

global_credential = 'yes, sir!'


class CredentialLocationMock(LocalStorageLocation):

    config_options = {
        'credential': KissOption(type='str')}

    def __init__(self, path: str, credential):
        if not credential == global_credential:
            raise Exception('Open location without having the credentials')
        super().__init__(path)
