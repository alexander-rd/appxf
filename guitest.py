''' Guitest Runner

Call via:  ./.venv/bin/python guitest.py

Virtual environment (venv) is required since, without, appxf would be unknown.
'''

from kiss_cf.guitest import Scanner

scanner = Scanner()
scanner.scan()

scanner = Scanner(
    database_path='guitest_features',
    test_path='tests_features'
)
scanner.scan()