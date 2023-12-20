# Enable to test for key indexable (object[]) behavior:
import uuid
from ftputil import FTPHost
from datetime import datetime, timedelta
from io import BytesIO, StringIO
import os.path

from kiss_cf.storage.storage import StorageMethod
from kiss_cf import logging
from kiss_cf.ntptime import NtpTime

# Notes on ftputil. While ftputil offers an upload_if_newer and
# download_if_newer together with synchronize_times(), it is based on files on
# the file system and the time detla cannot be retrieved. Kiss_cf needed to
# come up with it's own solution since most operations will be based on storing
# and loading bytestreams.
#
# Nevertheless, ftputil is still more efficient. Example: get modification date
# of of files in directory. With ftplib, we would need to querry the MLSD and
# interpret the result. Also, synchronizing folders of other data might become
# handy. Like: cloud storage.

def retry_method_with_reconnect(method):
    ''' Recover errors with a fresh connection.

    Executes the decorated method to:
        1) execute method an catch errors (logged as warning)
        2) reinitialize the connection (self.connect())
        3) executes the operation a second time
    (2) and (3) are onl if (1) returns errors.
    '''
    def method_wrapper(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except Exception as e:
            self.log.warning(
                f'Error on executing {method.__name__}, '
                f'try reconnect and repeat. Error: {e}', exc_info=True)
        # reconnect and try again. This time failing with original errors.
        self.connect()
        return method(self, *args, **kwargs)
    return method_wrapper


class FtpLocation():

    #! TODO: The verbose logging should be collected and printet to info when
    #  errors occur

    log = logging.getLogger(__name__ + '.RemoteConnection')

    def __init__(self, host: str, user: str, password: str, path: str = ''):
        ''' Maintainer for FTP locations

        The handler will handle one path on an FTP host. The host connections
        are shared between the handles

        Arguments:
            host -- _description_
            user -- _description_
            password -- _description_
        '''
        # Simple sanity checks:
        if not host:
            raise Exception('Provided host is empty.')
        if not user:
            raise Exception('Provided user is empty.')
        if not password:
            raise Exception('Provided password is empty.')
        # store away input
        self.host = host
        self.user = user
        self.password = password
        # initialize connection
        self.connect()

        self.path = path
        #! TODO: ensure that path exists (error, if not). Option to enforce
        #  directory creation.

    def connect(self):
        # ensure any old connection is closed
        try:
            self.connection.close()
        except:
            # nothing to do if above fails
            pass
        # try connecting
        try:
            self.connection = FTPHost(self.host, self.user, self.password)
        except Exception as e:
            raise Exception(f'Not able to initialize FTP object for [{self.host}].')

        #! TODO: ensure login is possible and things are operational

    @retry_method_with_reconnect
    def load(self, file: str) -> bytes:
        file = os.path.join(self.path, file)
        try:
            with self.connection.open(file, 'rb') as remote_file:
                data = remote_file.read()
        except Exception as e:
            #! TODO: better error handling: message, retrieve info from ftplib
            #  object.
            raise e
        return data

    @retry_method_with_reconnect
    def store(self, file: str, data: bytes):
        file = os.path.join(self.path, file)
        try:
            with self.connection.open(file, 'wb') as remote_file:
                remote_file.write(data)
        except Exception as e:
            #! TODO: better error handling: message, retrieve info from ftplib
            #  object.
            raise e

    # def remove(self, file: str):
    #     self._prepare_perform()
    #     self.curl.setopt(pycurl.CUSTOMREQUEST, 'DELE ' + file)
    #     self._perform(expect_fail=True)
    #     # verify deletion successful:
    #     status_code = self.curl.getinfo(pycurl.RESPONSE_CODE)
    #     if not status_code == CURL_RESPONCE_FILE_OP_OK:
    #         message = f'Was not able to remove [{file}]'
    #         self._log_error(message)
    #         raise Exception(message)
    #     # revert unusuals: none

    # def _prepare_perform(self, file: str = ''):
    #     '''Prepare setting common to all commands.'''
    #     # verify file (set URL)
    #     if '/' in file:
    #         message = (f'File [{file}] contained a path separator [/]. '
    #                    'If you want to handle files in subdirectories, '
    #                    'initialize a new RemoteLocation. ')
    #         self.log.exception(message)
    #         raise Exception(message)
    #     self.current_file = file
    #     self.curl.setopt(pycurl.URL, self.url + file)
    #     # set user and password
    #     self.curl.setopt(pycurl.USERNAME, self.user)
    #     self.curl.setopt(pycurl.PASSWORD, self.password)
    #     # ensure fresh head buffer
    #     if self.head_buffer:
    #         self.head_buffer.close()
    #     self.head_buffer = BytesIO()
    #     self.curl.setopt(pycurl.HEADERFUNCTION, self.head_buffer.write)
    #     # ensure fresh verbose buffer
    #     if self.verbose_buffer:
    #         self.verbose_buffer.close()
    #     self.verbose_buffer = StringIO()


    # def _perform(self, expect_fail=False):
    #     '''Curl perform() with error handling.'''
    #     try:
    #         self.curl.perform()
    #     except pycurl.error as e:
    #         if not expect_fail:
    #             self._log_error('pycurl perform() failed.')
    #             raise e

    # def _curl_debugfunction(self, type: int, message: bytes):
    #     '''Catch verbose logging for errors.'''
    #     self.verbose_buffer.write(f'{type}: {message.decode("utf-8")}')

    # def _log_error(self, message: str):
    #     self.log.info('### Curl/Remote Location failed - header buffer:\n'
    #                   f'{self.head_buffer.getvalue().decode("utf-8")}')
    #     self.log.info('### Curl/Remote Location failed - curl verbose logging:\n'
    #                   f'{self.verbose_buffer.getvalue()}')
    #     self.log.error(f'### Curl/Remote Location failed - exception:\n{message}',
    #                    exc_info=True)

#! TODO: StorageMethod is thought for a specific file. If we need to support
#  maintenance of a specific path, then this needs to be added to the specific
#  StorageMethod class.
#
# 1) The base class will do everything directly
# 2) An advanced class will prepare all uploads and require a call of sync()

#! TODO: Generating a StorageMethod out of a RemoteLocation (like FtpLocaion)
#  should be generic. But not needed as long as we don't support another
#  protocol.
class FtpStorageMethod(StorageMethod):
    def __init__(self, remote_location: FtpLocation):
        self.remote_location = remote_location

    def store(self, data: bytes):
        self.remote_location.store(self.file, data)

    def load(self):
        return self.remote_location.load(self.file)