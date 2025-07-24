# Test directories need to be scanned for guitest_*.py files to initialize the
# test database. In case of renaming or removal, such test cases also must be
# removed. This is done by the Scanner class.

from .databasse import Database

class Scanner():
    def __init__(self,
                 database_path: str = './guitest',
                 test_path: str = './tests'):
        self.test_path = test_path
        self.database_path = database_path
        self.database = Database(path=database_path)

    def scan(self):
        pass