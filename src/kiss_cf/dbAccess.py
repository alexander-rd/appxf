# Access to the open olitor data base.
#
# The class has a single refresh() which queries all required data from the
# data base and stores it with a timestamp (encrypted) to the storage. This
# enables:
#  * further processing can access data multiple times without querrying the
#    data base.
#  * functionality can be used offline based on last querry to data base
#
# The database configuration (includes password) is stored locally in an
# encrypted file.

# Restrictions
# 1. Using this class will require a configuration
# 2. This class returns querried data as panda data frame with columns matching
#    the SQL querry.
# 3. This class does not store data (separation of concerns). If querries are
#    to be limited

# NEW Class: Data store.
#
# This class holds one or more named SQL querries and:
# 1. performs the querry (dbAccess)
# 2. stores the data for further requests
# 3. can receive h./k-ups to extend the data sets
# 4. can report the data in CSV/ODS for debugging

# Considered alternatives
#
# A: Querry all. All database information is querried once at refresh() and,
# otherwise is taken from local storage (persisted).
#  - (+) only one file and timestamp with automation in scope of this class
#  - (-) enforces querrying not required data
#  - (-) this class needs to know the set of all querries
#  - (-) when multiple reports shall be generated, all with most current data
#    but based on user interaction, this solution will enforce querrying not re
#
# B:

import mariadb
import pickle
import os
import pandas


# TODO: pickling data must be removed on new sdt version (any) to avoid clashed
# due to changed data format or pickle format. BUT - this should not apply to
# data that is locally stored! There, I would need compatibility.

def connect(dbConfig):
    print(dbConfig)
    try:
        conn = mariadb.connect(
            user=dbConfig['user'],
            password=dbConfig['password'],
            host=dbConfig['host'],
            port=int(dbConfig['port']),
            database=dbConfig['database'],
            ssl=eval(dbConfig['ssl']))
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB: {e}")
        # TODO: proper error handling
    return conn


# TODO: this one must remain private!! Note that sqlQuerry should be put in ""
# since SQL should use '' for string literals.
def getDbRawData(dbConfig, pickleName, sqlQuerry):
    # TODO: Load, if possible should change to load if DB access fails or
    # switched to offline mode.
    pklFileName = './data/' + pickleName + '.pkl'

    # load, if possible:
    if (os.path.exists(pklFileName)):
        return pickle.load(open(pklFileName, 'rb'))
    dbConfig
    # Otherwise, DB access:
    conn = connect(dbConfig)
    # Those two variants exist. While true that it's easier to access data,
    # storing a backup is much larger since every line also stores header
    # naming.
    #
    # cur = conn.cursor(named_tuple=True)
    # cur = conn.cursor(dictionary=True)

    # TODO: check if conn could be opened as "with" statement to include the
    # close in any exception case.
    cur = conn.cursor()
    # TODO: timeout handling
    cur.execute(sqlQuerry)
    # get column names
    colNames = []
    for col in cur.description:
        colNames.append(col[0])
    # apply result to data frame:
    result = pandas.DataFrame(cur.fetchall(), columns=colNames)
    conn.close()
    # Store for later use
    if not os.path.exists('./data'):
        os.mkdir("./data")
    # pickle.dump(result, open(pklFileName, 'wb'))

    return result


def getTest():
    return getDbRawData(
        'test',
        "SELECT id, name FROM Abotyp")


def getDepotliste(dbConfig):
    print("getDepotliste()")
    return getDbRawData(dbConfig, 'depotListe', """
        SELECT
          -- Abo Details
          da.id as id,
          0 as HauptAboId,
          atyp.name as AboTyp,
          v.beschrieb as Vertrieb,
          IF(da.price, da.price, atyp.preis) as Preis,
          DATE(da.start) as ab,
          DATE(da.ende) as bis,
          -- Depot Details
          d.kurzzeichen as Depot,
          d.name as DepotName,
          -- Kunde Details
          da.kunde_id as KundenId,
          CONCAT('[', GROUP_CONCAT(
            CONCAT('(\"', p.name, '\", \"', p.vorname, '\")')
            ORDER BY
              p.sort SEPARATOR ', '
          ), ']') as kunde
        from
          DepotlieferungAbo da
          LEFT JOIN (Depot d, Vertrieb v, Abotyp atyp, Person p) ON (
            d.id = da.depot_id
            AND da.vertrieb_id = v.id
            AND atyp.id = da.abotyp_id
            AND p.kunde_id = da.kunde_id
          )
        GROUP BY
          da.id
        union
        select
          -- Zusatzabo Details
          za.id as id,
          da.id as HauptAboId,
          zatyp.name as AboTyp,
          v.beschrieb as Vertrieb,
          IF(za.price, za.price, zatyp.preis) as Preis,
          IF(
            ISNULL(za.start),
            DATE(da.start),
            IF(
              ISNULL(da.start),
              DATE(za.start),
              DATE(IF(za.start < da.start, da.start, za.start))
            )
          ) as ab,
          IF(
            ISNULL(za.ende),
            DATE(da.ende),
            IF(
              ISNULL(da.ende),
              DATE(za.ende),
              DATE(IF(za.ende > da.ende, da.ende, za.ende))
            )
          ) as bis,
          -- Depot details
          d.kurzzeichen as Depot,
          d.name as DepotName,
          -- Kunde Details
          za.kunde_id as KundeId,
          CONCAT('[', GROUP_CONCAT(
            CONCAT('(\"', p.name, '\", \"', p.vorname, '\")')
            ORDER BY
              p.sort SEPARATOR ', '
          ), ']') as kunde
          -- za.kunde as kunde
        from
          ZusatzAbo za
          LEFT JOIN (
            DepotlieferungAbo da,
            Vertrieb v,
            Depot d,
            ZusatzAbotyp zatyp,
            Person p
          ) ON (
            za.haupt_abo_id = da.id
            AND da.depot_id = d.id
            AND da.vertrieb_id = v.id
            AND za.abotyp_id = zatyp.id
            AND p.kunde_id = da.kunde_id
            AND da.vertrieb_id = v.id
          )
        GROUP BY
          za.id
        ORDER BY
          kunde""")
