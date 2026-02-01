from appxf.storage.sync import SyncData
from appxf.storage import Storage
from datetime import datetime
import pytest

# TODO: check if those test cases are still required.

# class DummyLocation(StorageLocation):
#
#     def get_id(self, file: str = '') -> str:
#         return 'dummy: ' + file
#
#     def exists(self, file: str = '') -> bool:
#         # must be false because StorageLocation still tries to evaluate time
#         # offset by a temporary file.
#         return False
#
#     def _get_location_timestamp(self, file: str) -> datetime | None:
#         return datetime.now()
#
#     def _store(self, file: str, data: bytes):
#         return b''
#
#     def _load(self, file: str) -> bytes:
#         return b''
#
#     def _remove(self, file: str):
#         pass
#
#
# def test_SyncData_set_nonexisting_location():
#     obj = SyncData()
#     location = DummyLocation()
#     date = datetime.now()
#     obj.set_location_uuid(location, b'dummy uuid')
#     obj.set_location_timestamp(location, date)
#
#     assert obj.get_location_uuid(location) == b'dummy uuid'
#     assert obj.get_location_timestamp(location) == date
#
# def test_SyncData_get_nonexisting_location():
#     obj = SyncData()
#     assert obj.get_location_uuid(DummyLocation()) == b''
#     assert obj.get_location_timestamp(DummyLocation()) == None
