# Copyright 2023-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
import asyncio
from datetime import datetime, timedelta

import ntplib

from appxf import logging

# TODO: reactivate and document this feature. It was implemented as part of the
# ideas for fily synchronization, relying on time stamps but not on ways to
# retrieve system time (Rationale by example: since years, my system time in
# Windows is hours off and corrects itself eventually after hours.. ..a sync
# decisions should not be based on this). Meaning for this feature: either it
# has other value or it is needed again for file synchronization.


class NtpTime:  # pragma: no cover
    """Provide offset between system time and NTP time servers.

    For timestamp based data synchronization, we do not rely on correctness of
    the system time even though modern operating systems should be properly
    time synced.

    The class is maintaining the time offset, not each object individually.

    This class can also be used to determine active network connection.
    """

    log = logging.getLogger(__name__ + ".NtpTime")

    # default base server is europe
    base_server = "europe.pool.ntp.org"
    # default list of server prefixes
    server_prefix_list = [0, 1, 2]
    # ensure we a last sync timestamp
    last_sync_as_datetime = None
    # time interval after which a re-sync is required
    resync_minutes = 60

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def get_offset_from_utc_now(cls):
        if not cls.last_sync_as_datetime or cls.last_sync_as_datetime < (
            datetime.utcnow() - timedelta(cls.resync_minutes)
        ):
            cls._update_time_sync()
        return cls.offset

    @classmethod
    def _update_time_sync(cls):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(cls._request_servers_and_update(loop))

    @classmethod
    async def _request_servers_and_update(cls, loop):
        timestamp_one = datetime.utcnow()
        servers = [
            str(prefix) + "." + cls.base_server for prefix in cls.server_prefix_list
        ]
        tasks = [asyncio.Task(cls._request_server(server)) for server in servers]
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        timestamp_two = datetime.utcnow()

        elapsed_time = timestamp_two - timestamp_one
        if elapsed_time > timedelta(seconds=1):
            cls.log.warning(
                f"Requesting servers took {elapsed_time.total_seconds()} seconds."
            )

        for task in done:
            result = task.result()
            if result:
                cls.last_sync_as_datetime = timestamp_one + 0.5 * elapsed_time
                cls.last_sync_as_ntp_recv = datetime.utcfromtimestamp(result.recv_time)
                cls.offset = result.offset
                cls.log.info(
                    f"Sync system time [{cls.last_sync_as_datetime}], "
                    f"NTP time [{cls.last_sync_as_ntp_recv}] "
                    f"resulted in offset of {cls.offset} seconds."
                )
                return True
        message = f"None of the server requests succeeded: {servers}"
        cls.log.error(message, exc_info=True)
        raise Exception(message)

    @classmethod
    async def _request_server(cls, server):
        try:
            client = ntplib.NTPClient()
            response = client.request(server)
            return response
        except ntplib.NTPException as e:
            cls.log.warning(
                f"Error in retrieving NTP time from [{server}]. "
                f"It likely timed out. Error: {e}"
            )
            return None
