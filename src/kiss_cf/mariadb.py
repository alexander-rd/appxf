import mariadb
from pandas import DataFrame
from typing import TypedDict
from . import logging

log = logging.getLogger(__name__)


# TODO: RecordClass (typed named tuple) should be better suited for DbConfig.
class DbConfig(TypedDict):
    ''' target types for config fields

    INTERNAL USE to catch wrong types for config passed into querry().
    '''
    host: str
    port: int
    database: str
    user: str
    password: str
    ssl: bool


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

    def __init__(self, config: dict, **kwargs):
        super().__init__(**kwargs)
        # Ensure DbConfig (types). isinstance(config, DbConfig) cannot be used
        # because DbConfig is a TypedDict.
        con: DbConfig = {
            'host': config['host'],
            'port': (int(config['port'])
                     if isinstance(config['port'], str)
                     else config['port']),
            'database': config['database'],
            'user': config['user'],
            'password': config['password'],
            'ssl': (config['ssl']
                    if isinstance(config['ssl'], bool)
                    else (True
                          if (config['ssl'].lower() in ('yes', 'true', '1'))
                          else False)
                    )
            }

        log.debug(f"{con['host']}:{con['port']} [{con['database']}], "
                  f"user: {con['user']}, ssl: {con['ssl']}")

        self.config = con
        self.connection = None

    def ensure_connected(self):
        if self.connection is None:
            self.connection = mariadb.connect(**self.config)
            Connection.count += 1
            self.log.debug(
                f'connected, connection count: {Connection.count}')
            # Note that connections will be closed as soon as the object is
            # deleted or when used with a context handler
        elif not self.connection.open:
            self.connection.reconnect()
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
        cur = self.connection.cursor()
        try:
            cur.execute(querry)
        except Exception:
            log.debug(querry)
            raise

        col_names = [col[0] for col in cur.description]
        result = cur.fetchall()
        data = DataFrame(result, columns=col_names)

        log.debug(f'got {len(data)} rows with columns {col_names}' +
                  f', column "{index}" will be used as index' if index else '')

        if index:
            data.index = data[index]
            data.drop(columns=[index], inplace=True)

        return data
