# This code ended up in being obsolete. Main reasons:
#  * core focus was an FTP client since you get FTP storage almost everyhwere.
#  * pycurl/libcurl is powerfull in enabling other protocols like SFTP but
#    there are still differences in like files information is retrieved.
#    Furhter example is how directories are scanned for file details. FTP has
#    MLSD, SFTP does not.
#  * getting it running for windows became an effort. While I might have
#    succeeded at one point, it results in the main two core reasons:
#    * at least MEDIUM risk to include problems due to incompatibilities of
#      C libraries (like dependency to SSL)
#    * kiss_cf users in windows would face similar problems for their
#      application. This would not be acceptable.
#    * at least MEDIUM effort to maintain the build pipeline
#
# However - the code as of now was working (in linux).

# Enable to test for key indexable (object[]) behavior:
import ntplib
import pycurl
import uuid
from datetime import datetime, timedelta
from io import BytesIO, StringIO

from kiss_cf.storage.storage import StorageMethod
from kiss_cf import logging
from kiss_cf.ntptime import NtpTime

CURL_RESPONSE_CODE_OK = 200
CURL_RESPONSE_CODE_FILE_NOT_FOUND = 550
CURL_RESPONCE_FILE_OP_OK = 250


class RemoteLocation():

    #! TODO: The verbose logging should be collected and printet to info when
    #  errors occur

    log = logging.getLogger(__name__ + '.RemoteConnection')

    # Using a single curl handle to reuse connection for various folders.
    # Downside is that details like user/password needs to be set up before
    # every call.
    curl = pycurl.Curl()

    def __init__(self, url: str, user: str, password: str):
        # verify that URL will be supported
        #
        #! TODO: For now, only FTP is supported. Main reason are differences in
        #  ensuring proper time synchronization (file stat) which is different
        #  for SFTP.
        if (isinstance(url, str) and
            (url.startswith('ftp:'))
            ):
            # everything fine
            pass
        else:
            self.log.warning(
                'The URL should start with "ftp:". '
                'Other protocols might work but were never tested.')
        if not url.endswith('/'):
            url += '/'
        # store away input
        self.url = url
        self.user = user
        self.password = password
        # setup other attributes
        self.current_file = ''
        self.file_info = {}
        # make timestamp very old to ensure updates
        self.file_info_timestamp = datetime.now() - timedelta(days = 1000)
        self.file_info_max_age = timedelta(minutes=10)
        self.head_buffer = BytesIO()
        # enable debugging
        self.verbose_buffer = StringIO()
        self.curl.setopt(pycurl.VERBOSE, 2)
        self.curl.setopt(pycurl.DEBUGFUNCTION, self._curl_debugfunction)
        # initialize connection and obtain time deltas for sync. This also
        # includes a full self test of being able to read/write.
        self.test_count = 0
        # Positive offsets imply that local time is behind NTP time or file
        # timestamps. Like 0.5s implies that NTP time is 0.5s ahead of local
        # time. Or 600s implies that server file stamps are 10min ahead of
        # local time.
        self.update_remote_offset()

    def update_remote_offset(self):
        file = 'self.test.' + str(uuid.uuid4())
        if self.test_count > 2:
            message = 'Was not able to self-test for two times now. Quitting'
            self.log.error(message, exc_info=True)
        # ensure file does not exist
        if (self.file_exists(file)):
            # file collision - try again:
            self.log.warning(f'Test file [{file}] already exists on [{self.config["url"]}]')
            return self.update_remote_offset()
        # put file (and remember time):
        timestamp_one = datetime.now()
        self.store(file, b'')
        timestamp_two = datetime.now()
        timestamp = timestamp_one + 0.5*(timestamp_two - timestamp_one)
        # get timestamp of file:
        self.update_file_timestamps()
        # compute time offset:
        try:
            self.remote_offset = self.file_info[file]['timestamp'] - timestamp
        except Exception as e:
            message = 'Something went wrong in prior evaluation of file properties.'
            self._log_error(message)
            raise e
        # remove tmp file again:
        del self.file_info[file]
        self.remove(file)

    def file_exists(self, file: str):
        self._querry_file_info(file)
        return self._evaluate_stat_file_exist()

    def _evaluate_stat_file_exist(self):
        status_code = self.curl.getinfo(pycurl.RESPONSE_CODE)
        if status_code == CURL_RESPONSE_CODE_OK:
            return True
        elif status_code == CURL_RESPONSE_CODE_FILE_NOT_FOUND:
            return False
        else:
            message = (f'Return code {status_code} does not allow to '
                       f'determine if file [{self.current_file}] '
                       f'exists on [{self.url}]')
            self._log_error(message)
            raise Exception(message)

    def _querry_file_info(self, file:str):
        self._prepare_perform(file)
        self.curl.setopt(pycurl.NOBODY, 1)
        try:
            self._perform(expect_fail=True)
        finally:
            # revert unusuals:
            self.curl.setopt(pycurl.NOBODY, 0)

    def update_file_timestamps(self):
        self._prepare_perform('')
        buffer = BytesIO()
        self.curl.setopt(pycurl.CUSTOMREQUEST, 'MLSD')
        self.curl.setopt(pycurl.WRITEDATA, buffer)
        #self.connection.setopt(pycurl.NOBODY, 1)
        self._perform()
        # revert unusuals: none

        # cycle through list
        buffer.seek(0)
        #! TODO: this function is main reason to limit to FTP. Evaluation of lines
        #  for SFTP is not in MLSD format
        self.file_info = {}
        for line in buffer:
            self._update_file_info_from_mlsd(line.decode('utf-8'))

    def _update_file_info_from_mlsd(self, line):
        # Lines look like:
        # Type=cdir;Modify=20231218101626;Unique=0010001d7796eb7e;Perm=cmpdfe; .
        # Type=file;Size=3766;Modify=20231218094934;Unique=0010001d7f23bcca;Perm=adfrw; README.md
        # Type=file;Size=8;Modify=20231218212735;Unique=0010001d7629fba3;Perm=adfrw; test.txt
        fields = line.split(';')
        this_file_info = {'name': fields[-1].strip()}
        try:
            for field in fields:
                parts = field.split('=')
                if len(parts) < 2:
                    continue
                if parts[0] == 'Type':
                    this_file_info['type'] = parts[1]
                elif parts[0] == 'Size':
                    this_file_info['size'] = parts[1]
                elif parts[0] == 'Modify':
                    this_file_info['timestamp'] = datetime.strptime(parts[1], '%Y%m%d%H%M%S')
        except Exception as e:
            message = 'FTP MLSD interpretation failed in interpreting a field.'
            self._log_error(message)
            raise e
        if (not 'type' in this_file_info.keys() and
            not 'size' in this_file_info.keys() and
            not 'timestamp' in this_file_info.keys()
            ):
            message = 'FTP MLSD interpretation did not work as expected (elements missing).'
            self._log_error(message)

        self.file_info[this_file_info['name']] = this_file_info

    def load(self, file: str):
        self._prepare_perform(file)
        # upload
        buffer = BytesIO()
        self.curl.setopt(pycurl.WRITEDATA, buffer)
        self._perform()
        # revert unusuals: none

        return buffer.getvalue()

    def store(self, file: str, data: bytes):
        self._prepare_perform(file)
        # upload
        buffer = BytesIO(data)
        self.curl.setopt(pycurl.UPLOAD, 1)
        self.curl.setopt(pycurl.READDATA, buffer)
        try:
            self._perform()
        finally:
            # revert unusuals:
            self.curl.setopt(pycurl.UPLOAD, 0)

    def remove(self, file: str):
        self._prepare_perform()
        self.curl.setopt(pycurl.CUSTOMREQUEST, 'DELE ' + file)
        self._perform(expect_fail=True)
        # verify deletion successful:
        status_code = self.curl.getinfo(pycurl.RESPONSE_CODE)
        if not status_code == CURL_RESPONCE_FILE_OP_OK:
            message = f'Was not able to remove [{file}]'
            self._log_error(message)
            raise Exception(message)
        # revert unusuals: none

    def _prepare_perform(self, file: str = ''):
        '''Prepare setting common to all commands.'''
        # verify file (set URL)
        if '/' in file:
            message = (f'File [{file}] contained a path separator [/]. '
                       'If you want to handle files in subdirectories, '
                       'initialize a new RemoteLocation. ')
            self.log.exception(message)
            raise Exception(message)
        self.current_file = file
        self.curl.setopt(pycurl.URL, self.url + file)
        # set user and password
        self.curl.setopt(pycurl.USERNAME, self.user)
        self.curl.setopt(pycurl.PASSWORD, self.password)
        # ensure fresh head buffer
        if self.head_buffer:
            self.head_buffer.close()
        self.head_buffer = BytesIO()
        self.curl.setopt(pycurl.HEADERFUNCTION, self.head_buffer.write)
        # ensure fresh verbose buffer
        if self.verbose_buffer:
            self.verbose_buffer.close()
        self.verbose_buffer = StringIO()


    def _perform(self, expect_fail=False):
        '''Curl perform() with error handling.'''
        try:
            self.curl.perform()
        except pycurl.error as e:
            if not expect_fail:
                self._log_error('pycurl perform() failed.')
                raise e

    def _curl_debugfunction(self, type: int, message: bytes):
        '''Catch verbose logging for errors.'''
        self.verbose_buffer.write(f'{type}: {message.decode("utf-8")}')

    def _log_error(self, message: str):
        self.log.info('### Curl/Remote Location failed - header buffer:\n'
                      f'{self.head_buffer.getvalue().decode("utf-8")}')
        self.log.info('### Curl/Remote Location failed - curl verbose logging:\n'
                      f'{self.verbose_buffer.getvalue()}')
        self.log.error(f'### Curl/Remote Location failed - exception:\n{message}',
                       exc_info=True)

#! TODO: StorageMethod is thought for a specific file. If we need to support
#  maintenance of a specific path, then this needs to be added to the specific
#  StorageMethod class.
#
# 1) The base class will do everything directly
# 2) An advanced class will prepare all uploads and require a call of sync()

class RemoteStorageMethod(StorageMethod):
    def __init__(self, remote_location: RemoteLocation):
        self.remote_location = remote_location

    def store(self, data: bytes):
        self.remote_location.store(self.file, data)

    def load(self):
        return self.remote_location.load(self.file)