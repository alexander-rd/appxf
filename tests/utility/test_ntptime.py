# Copyright 2023-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
import pytest
from datetime import datetime, timedelta
from appxf.utility.ntptime import NtpTime
import ntplib


def ntplib_request_failing(server):
    raise ntplib.NTPException('dummy')


class NtpStatStub:
    recv_time = None
    offset = None


ntpstat = NtpStatStub()


def ntplib_request_ok(server):
    return ntpstat


@pytest.fixture(autouse=True)
def fresh_NtpTime():
    # copied initialization
    NtpTime.last_sync_as_datetime = None
    NtpTime.base_server = 'europe.pool.ntp.org'
    NtpTime.server_prefix_list = [0, 1, 2]
    return NtpTime


@pytest.mark.skip(reason='NTP server is currently not used and occasionally fails')
def test_functional(fresh_NtpTime):
    # fresh_NtpTime.base_server = 'pool.ntp.org'
    # fresh_NtpTime.server_prefix_list = ['0']
    offset = NtpTime.get_offset_from_utc_now()
    corrected_time = NtpTime.last_sync_as_datetime + timedelta(seconds=offset)
    assert abs((corrected_time - NtpTime.last_sync_as_ntp_recv).total_seconds()) < 1


@pytest.mark.skip(reason='NTP server is currently not used and occasionally fails')
def test_server_all_fail(mocker, fresh_NtpTime):
    mocker.patch('ntplib.NTPClient.request', side_effect=ntplib_request_failing)
    with pytest.raises(Exception) as excinfo:
        fresh_NtpTime.get_offset_from_utc_now()
    assert 'None of the server requests succeeded' in str(excinfo.value)


@pytest.mark.skip(reason='NTP server is currently not used and occasionally fails')
def test_no_second_call(mocker, fresh_NtpTime):
    m = mocker.patch('ntplib.NTPClient.request', side_effect=ntplib_request_ok)
    NtpStatStub.offset = 0
    NtpStatStub.recv_time = datetime.utcnow().timestamp()
    offset = NtpTime.get_offset_from_utc_now()
    assert offset == 0
    assert NtpTime.last_sync_as_ntp_recv == datetime.utcfromtimestamp(
        NtpStatStub.recv_time
    )
    assert m.call_count == 3
    # will not be called again:
    m.offset = NtpTime.get_offset_from_utc_now()
    assert m.call_count == 3
