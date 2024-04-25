import mariadb
from pandas import DataFrame
from typing import TypedDict

from appxf import logging
from kiss_cf.property import KissPropertyDict

# Logger must be existing for class logger. Otherwise, hierarchy is lost:
log = logging.getLogger(__name__)

config_property_template = KissPropertyDict(
    {'host': (str,),
     'port': (int,),
     'user': (str,),
     'password': ('password',),
     'database': (str,),
     'ssl': (bool, True),
     })

class Connection():
    ''' wrapping mariadb connection (aggregating)

    Simple wrapper around mariadb.Connection. Providing:
     1) Not connected on construction since querries are assumed to be buffered
        by the using class (see openolitor) such that the connection might
        remain unused after construction.
     2) Still ensure at least proper types of required connection configuration
        upon construction.
     3) Perform querries and put results in pandas DataFrames

    '''
    log = logging.getLogger(__name__ + '.Connection')
    count = 0

    def __init__(self, config: dict | KissPropertyDict, **kwargs):
        super().__init__(**kwargs)

        self.log.debug(f"{config['host']}:{config['port']} [{config['database']}], "
                  f"user: {config['user']}, ssl: {config['ssl']}")

        self._config = config
        self._connection = None

    def ensure_connected(self):
        if self._connection is None:
            self._connection = mariadb.connect(**self._config)
            Connection.count += 1
            self.log.debug(
                f'connected, connection count: {Connection.count}')
            # Note that connections will be closed as soon as the object is
            # deleted or when used with a context handler
        elif not self._connection.open:
            self._connection.reconnect()
            Connection.count += 1
            self.log.debug(
                f'reconnect, connection count: {Connection.count}')

    def querry(self,
               querry: str,
               index: str = '') -> DataFrame:
        ''' Querry MariaDB

        Hint: If you use single quotes, use "" since SQL should use '' for
        string literals.

        Arguments:
            config -- Dictionary of configuration values (host, port, database,
                    user, password, ssl)
            querry -- SQL querry
            index  -- column to be used as pandas row index while column will
                    be removed. Empty string will do nothing. (default: '')

        Returns:
            pandas.DataFrame with column titles taken from the SQL querry.
        '''
        self.ensure_connected()

        # Curser by default returns tuples. Those two variants exist:
        #
        # cur = conn.cursor(named_tuple=True)
        # cur = conn.cursor(dictionary=True)
        #
        # First one should not be used (by mariadb documentation) and the
        # dictionary variant would repeat the column titles for every row.
        cur = self._connection.cursor()
        try:
            cur.execute(querry)
        except Exception:
            self.log.debug(querry)
            raise

        col_names = [col[0] for col in cur.description]
        result = cur.fetchall()
        data = DataFrame(result, columns=col_names)

        self.log.debug(f'got {len(data)} rows with columns {col_names}' +
                  f', column "{index}" will be used as index' if index else '')

        if index:
            data.index = data[index]
            data.drop(columns=[index], inplace=True)

        return data
