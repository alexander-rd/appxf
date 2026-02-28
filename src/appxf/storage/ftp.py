# Copyright 2023-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
# Enable to test for key indexable (object[]) behavior:
import os.path
from contextlib import suppress

from ftputil import FTPHost

from appxf import logging

from .storage_to_bytes import StorageToBytes

# Notes on ftputil. While ftputil offers an upload_if_newer and
# download_if_newer together with synchronize_times(), it is based on files on
# the file system and the time detla cannot be retrieved. APPXF needed to
# come up with it's own solution since most operations will be based on storing
# and loading bytestreams.
#
# Nevertheless, ftputil is still more efficient. Example: get modification date
# of of files in directory. With ftplib, we would need to querry the MLSD and
# interpret the result. Also, synchronizing folders of other data might become
# handy. Like: cloud storage.

# TODO UPGRADE: review when starting to use this


def retry_method_with_reconnect(method):
    """Recover errors with a fresh connection.

    Executes the decorated method to:
        1) execute method an catch errors (logged as warning)
        2) reinitialize the connection (self.connect())
        3) executes the operation a second time
    (2) and (3) are onl if (1) returns errors.
    """

    def method_wrapper(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except Exception as e:
            self.log.warning(
                f"Error on executing {method.__name__}, "
                f"try reconnect and repeat. Error: {e}",
                exc_info=True,
            )
        # reconnect and try again. This time failing with original errors.
        self.connect()
        return method(self, *args, **kwargs)

    return method_wrapper


class FtpLocation(StorageToBytes):
    # TODO UPGRADE: The verbose logging should be collected and printet to info
    # when errors occur

    log = logging.get_logger(__name__ + ".RemoteConnection")

    def __init__(self, host: str, user: str, password: str, path: str = "", **kwargs):
        """Maintainer for FTP locations

        The handler will handle one path on an FTP host. The host connections
        are shared between the handles

        Arguments:
            host -- _description_
            user -- _description_
            password -- _description_
        """
        # Simple sanity checks:
        if not host:
            raise Exception("Provided host is empty.")
        if not user:
            raise Exception("Provided user is empty.")
        if not password:
            raise Exception("Provided password is empty.")
        # store away input
        self.host = host
        self.user = user
        self.password = password
        # initialize connection
        self._connect()
        self.path = path
        # TODO: ensure that path exists (error, if not). Option to enforce
        # directory creation.

        # Important: super().__init__() already utilizes the specific
        # implementation. Attributes must be available.
        super().__init__(**kwargs)

    def id(self, name: str = ""):
        name = f"::{name}" if name else ""
        return f"FTP({self.user}@{self.host}://{self.path}){name}"

    def _connect(self):
        # ensure any old connection is closed
        with suppress(Exception):
            self.connection.close()
        # try connecting
        try:
            self.connection = FTPHost(self.host, self.user, self.password)
        except Exception as e:
            raise Exception(
                f"Not able to initialize FTP object for [{self.host}]: {e}."
            ) from e

        # TODO LATER: ensure login to FTP server is possible and things are
        # operational. An initial stat of the location could be of interes.

    def exists(self, file: str) -> bool:
        file = os.path.join(self.path, file)
        try:
            return self.connection.path.exists(file)
        except Exception as e:
            # TODO UPGRADE: better error handling: message, retrieve info from
            # ftplib object. Consider collecting from obsolete pycurl
            # implementation.
            raise e

    @retry_method_with_reconnect
    def load_raw(self, file: str) -> bytes:
        file = os.path.join(self.path, file)
        try:
            with self.connection.open(file, "rb") as remote_file:
                data = remote_file.read()
        except Exception as e:
            # TODO UPGRADE: better error handling: message, retrieve info from
            # ftplib object. Consider collecting from obsolete pycurl
            # implementation.
            raise e
        return data

    @retry_method_with_reconnect
    def store_raw(self, file: str, data: bytes):
        file = os.path.join(self.path, file)
        try:
            with self.connection.open(file, "wb") as remote_file:
                remote_file.write(data)
        except Exception as e:
            # TODO UPGRADE: better error handling: message, retrieve info from
            # ftplib object. Consider collecting from obsolete pycurl
            # implementation.
            raise e

    @retry_method_with_reconnect
    def _remove(self, file: str):
        file = os.path.join(self.path, file)
        try:
            self.connection.remove(file)
        except Exception as e:
            # TODO UPGRADE: better error handling: message, retrieve info from
            # ftplib object. Consider collecting from obsolete pycurl
            # implementation.
            raise e
