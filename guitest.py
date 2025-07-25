''' Guitest Runner

Call via:  ./.venv/bin/python guitest.py

Virtual environment (venv) is required since, without, appxf would be unknown.
'''

from kiss_cf.guitest import Scanner, CmdHelper, Database

unit_database = Database()
feature_database = Database(path='guitest_features')

scanner = Scanner(database = unit_database)
scanner.scan()

scanner = Scanner(
    database=feature_database,
    path='tests_features')
scanner.scan()

cmd_helper = CmdHelper(database=feature_database)
cmd_helper.run()