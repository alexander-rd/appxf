import pytest
import datetime
from dotenv import load_dotenv
import os
from appxf_private.storage.ftp import FtpLocation

load_dotenv()
host = os.environ.get('KISS_FTP_HOST')
user = os.environ.get('KISS_FTP_USER')
passwd = os.environ.get('KISS_FTP_PASSWORD')

@pytest.fixture
def remote_connection():
    print(f'[{host}] with [{user}] and [{passwd}]')
    location = FtpLocation(host=host, user=user, password=passwd)
    return location

# TODO UPGRADE: activate testing again (github fails)
@pytest.mark.skip(reason='FTP connection not yet used. Will be fixed in short time.')
def test_write_read(remote_connection):
    # data and file
    data = datetime.datetime.now().strftime('%H %M %S')
    file = 'test.txt'
    # writing data
    print(f'Writing time: {data}')
    remote_connection.store(file, data.encode('utf-8'))
    # Read the file
    read_data = remote_connection.load(file).decode('utf-8')
    print(f'Loaded data: {read_data}')
    assert read_data == data

#! TODO: Test case that covers the automatic reconnect.

#! TODO: Functional test case that makes file operations on two path locations

#! TODO: RemoteLocation should verify if the login credentials work to provide
#  a meaningful error before continuing.

#! TODO: There should be a class verifying general internet connectivity to
#  provide meaningful error messages.

#! TODO: Test must include subfolders. (There was one article reporting DEL
#  only working on providing the full path)

#! TODO: Initialization must check obtained time deltas. This test is
#  reasonable based on unit test. But mocking CURL might get awkward.

#! TODO: Test upload and download after initialization.

#! TODO: On upload or remove: ensure file_info is updated accordingly.

#! TODO: Should keep testing FUNCTIONAL against a test FTP account. While not
#  unit testing, it covers "the real problems".
#   * credentials can come from github actions and are typically environment
#     variables
#   * for local execution, a .env file can be used and loaded via dotenv python
#     library: load_dotenv()

#! TODO: There is a problem with the NTP library. Contacting servers
#  occasionally fails. I have to add retries. Possibly, I should add a higher
#  level class support.

#! TODO: Remote storage should ensure local storage is removed if user cannot
#  decrypt anymore. Note: this might be only a permission change, not a data
#  change. Timestamp for data&envelope. Timestamp for encrption data. Let's use
#  the encryption data as "done" and let it also contain an evelope and
#  validation.