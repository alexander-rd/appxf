from kiss_cf import logging
logging.activate_logging(__name__)

import datetime
import pycurl
from io import BytesIO
from ftplib import FTP, FTP_TLS
from kiss_cf.storage.remote import RemoteLocation
from dotenv import load_dotenv
import os

load_dotenv()

# required install for pycurl: sudo apt install libcurl4-openssl-dev libssl-dev

host = 'ftp://ftp.strato.de/'
#host = 'sftp://ssh.strato.de/'
user = 'testing@alexander-reinhold.de'
passwd = 'QtTfRq8B?(aH$.sg'

host = os.environ.get('KISS_FTP_HOST').strip('"')
user = os.environ.get('KISS_FTP_USER').strip('"')
passwd = os.environ.get('KISS_FTP_PASSWORD').strip('"')
print(f'{host} ## {user} ## {passwd}')

location = RemoteLocation(url=host, user=user, password=passwd)
print(f'NTP time offset {location.local_offset}. Remote location file time offset {location.remote_offset}')
print(f'NTP time offset {location.local_offset.total_seconds()}. Remote location file time offset {location.remote_offset.total_seconds()}')
location.store('test.upload', b'test')
print(location.file_info)
print('###########################################')
location = RemoteLocation(url=host+'subfolder', user=user, password=passwd)
print(f'NTP time offset {location.local_offset}. Remote location file time offset {location.remote_offset}')
print(f'NTP time offset {location.local_offset.total_seconds()}. Remote location file time offset {location.remote_offset.total_seconds()}')
location.store('test.upload2', b'test2')
print(location.file_info)
print('###########################################')

# Read file (must be present)
file = 'test.txt'
read_data = location.load(file).decode('utf-8')
print(f'Loaded data: {read_data}')
# Write a file
data = datetime.datetime.now().strftime('%H %M %S')
print(f'Writing time: {data}')
location.store(file, data.encode('utf-8'))
# Read the file
read_data = location.load(file).decode('utf-8')
print(f'Loaded data: {read_data}')