''' access an open olitor database

The module is buffered. Any querry will only be done once unless you call
`clear_buffer()`. The buffer is NOT persisted and any new session will querry
the database.

Evetry call to get data will require a database configuration.
'''
import kiss_cf.mariadb
from .buffer import Buffer, buffered
from . import logging
from pandas import DataFrame


class Database():
    ''' Querry OpenOlitor Database

    This class is expected to be used with a context handler to use the same
    database connection while querrying multiple tables, like:

    ```
    with Database(config) as connection:
        abo_data = connection.get_abo()
        person_data = connection.get_person()
    ```

    Every table result is buffered statically such that querrying with a new
    Database object would not need a databse connection. If you have to ensure
    querrying fresh data from OpenOlitor, you should use
    `Database.clear_buffer()`
    '''
    log = logging.getLogger(__name__ + 'DataBase')
    buffer = Buffer()

    def __init__(self, config: dict):
        self.connection = kiss_cf.mariadb.Connection(config)

    @staticmethod
    def clear_buffer():
        Database.buffer.clear()

    def __enter__(self):
        ''' context handler

        Nothing to do on entry. Connection is only created on demand.
        '''
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        ''' context handler

        Nothing really to do. Database connection will be closed on
        __del__() which should be good enough.'''
        pass

    def get_table(self, table: str, index: str = '') -> DataFrame:
        @buffered(self.buffer)
        def _get_table(table: str):
            data = self.connection.querry(
                f'SELECT * FROM {table}',
                index)
            return data
        return _get_table(table)

    def get_abo(self) -> DataFrame:
        ''' get all abo data

        This includes DepotAbo, HeimlieferungAbo and PostlieferungAbo which
        have a lot in common while DepotAbo has additional (depot_id,
        depot_name) and HeimlieferungAbo has additional (tour_id, tour_name).
        Correspdoning fields will contain None, dependent on abo type.

        The table will additionally contain or alter:
         - boolean columns for filtering: [is_depot], [is_heimlieferung] and
           [is_postlieferung].
         - include AboTyp details: abotyp_name
         - [Preis] takes the price column, if present. If not present, it takes
           AboTyp.preis

        Note: some columns might not yet be available because they were yet
        unused.

        Returns:
            pandas DataFrame with all abos.
        '''
        def common_querry(type: str) -> str:
            # default entries:
            post_column = 'False as is_post'
            heim_column = 'False as is_heim'
            depot_column = 'False as is_depot'
            depot_columns = '''
                NULL as depot_id,
                NULL as depot_kurzzeichen,
                NULL as depot_name,
                '''
            extra_join = ''

            if type == 'post':
                table = 'PostlieferungAbo'
                post_column = 'True as is_post'
            elif type == 'heim':
                table = 'HeimlieferungAbo'
                heim_column = 'True as is_heim'
            elif type == 'depot':
                table = 'DepotlieferungAbo'
                depot_column = 'True as is_depot'
                depot_columns = '''
                d.id as depot_id,
                d.kurzzeichen as depot_kurzzeichen,
                d.name as depot_name,
                '''
                extra_join = 'LEFT JOIN (Depot d) ON (d.id = t.depot_id)'
            else:
                raise Exception(f'type "{type}" is not supported')
            return f'''
                SELECT
                    t.id as id,
                    {post_column},
                    {heim_column},
                    {depot_column},
                    -- Kunde Details
                    t.kunde_id as kunde_id,
                    t.kunde as kunde,
                    -- Vertrieb/Vertriebsart ignored (not yet used)
                    -- AboTyp
                    t.abotyp_id as abotyp_id,
                    atyp.name as abotyp_name,
                    IF(t.price, t.price, atyp.preis) as Preis,
                    DATE(t.start) as start,
                    DATE(t.ende) as ende,
                    -- Guthaben ignored (not yet used)
                    -- Depot Details
                    {depot_columns}
                    -- keep this last to always use commas in the parts above
                    t.aktiv as aktiv
                FROM
                    {table} as t
                    LEFT JOIN (Abotyp atyp) ON (atyp.id = t.abotyp_id)
                    {extra_join}
            '''

        @buffered(self.buffer)
        def _get_abo():
            data = self.connection.querry(
                common_querry('heim')
                + 'UNION'
                + common_querry('post')
                + 'UNION'
                + common_querry('depot')
                + ';', index='id')
            return data
        return _get_abo()

    def get_zusatzabo(self) -> DataFrame:
        ''' Get zusatz abo data

        Columns are like get_abo() and remarks apply likewise. You could
        concatanate the result from get_zusatzabo() with the result from
        get_abo(). Additionally:
         - start/end dates are merged with the main abo dates. A ZusatzAbo
           cannot start before the main abo AND cannot end after the main abo.

        Returns:
            pandas DataFrame with all zusatz abos.
        '''
        @buffered(self.buffer)
        def _get_zusatzabo():
            data = self.connection.querry('''-- --sql
                SELECT
                    -- Zusatzabo Details
                    za.id as id,
                    -- Kunde Details
                    za.kunde_id as kunde_id,
                    za.kunde as kunde,
                    -- Vertrieb/Vertriebsart ignored (not yet used)
                    -- AboTyp
                    zatyp.id as abotyp_id,
                    zatyp.name as abotyp_name,
                    IF(za.price, za.price, zatyp.preis) as Preis,
                    -- start/ende from the three abo tables
                    (SELECT
                        IF(da.start IS NOT NULL, da.start,
                        IF(ha.start IS NOT NULL, ha.start,
                        IF(pa.start IS NOT NULL, pa.start, NULL)))
                    ) as abo_start,
                    (SELECT
                        IF(da.ende IS NOT NULL, da.ende,
                        IF(ha.ende IS NOT NULL, ha.ende,
                        IF(pa.ende IS NOT NULL, pa.ende, NULL)))
                    ) as abo_ende,
                    -- start ende wither from zusatz_abo or from the three
                    -- main abo types
                    (SELECT
                        IF(ISNULL(za.start), DATE(abo_start),
                        IF(ISNULL(abo_start), DATE(za.start),
                        DATE(IF(za.start < abo_start, abo_start, za.start))
                        ))
                    ) as start,
                    (SELECT
                        IF(ISNULL(za.ende), DATE(abo_ende),
                        IF(ISNULL(abo_ende), DATE(za.ende),
                        DATE(IF(za.ende > abo_ende, abo_ende, za.ende))
                        ))
                    ) as ende,
                    -- Depot details
                    d.id as depot_id,
                    d.kurzzeichen as depot_kurzzeichen,
                    d.name as depot_name,
                    -- Extras for Zusatzabo
                    za.haupt_abo_id as haupt_abo_id,
                    za.aktiv as aktiv
                FROM
                    ZusatzAbo za
                LEFT JOIN (ZusatzAbotyp zatyp) ON (za.abotyp_id = zatyp.id)
                LEFT JOIN (DepotlieferungAbo da) ON (da.id = za.haupt_abo_id)
                LEFT JOIN (Depot d) ON (d.id = da.depot_id)
                LEFT JOIN (HeimlieferungAbo ha) ON (ha.id = za.haupt_abo_id)
                LEFT JOIN (PostlieferungAbo pa) ON (pa.id = za.haupt_abo_id)
                ;''', index='id')
            return data
        return _get_zusatzabo()

    def get_arbeitseinsaetze(self) -> DataFrame:
        ''' Get Mitarbeit data

        ???

        Returns:
            pandas DataFrame with ???.
        '''
        @buffered(self.buffer)
        def _get_arbeitseinsaetze():
            data = self.connection.querry('''-- --sql
            SELECT
                ae.id as id,
                ae.arbeitsangebot_id as arbeitsangebot_id,
                ae.arbeitsangebot_titel as arbeitsangebot_titel,
                ae.arbeitsangebot_status as arbeitsangebot_status,
                ae.kunde_id as kunde_id,
                ae.zeit_von as zeit_von,
                ae.zeit_bis as zeit_bis,
                IFNULL(ae.einsatz_zeit, 0) as einsatz_zeit,
                IFNULL(ae.anzahl_personen, 0) as anzahl_personen,
                ae.bemerkungen as bemerkungen
            FROM
                Arbeitseinsatz ae
            ;''', index='id')
            return data
        return _get_arbeitseinsaetze()
