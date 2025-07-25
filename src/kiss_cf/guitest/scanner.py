# Test directories need to be scanned for guitest_*.py files to initialize the
# test database. In case of renaming or removal, such test cases also must be
# removed. This is done by the Scanner class.
import os
import fnmatch
from pathlib import Path
from appxf import logging
from .database import Database


class Scanner():
    def __init__(self,
                 database: Database,
                 path: str = './tests'):
        self.path = path
        self.database = database

    def scan(self):
        # remove files that are not existing anymore
        remove_list = []
        for case_name, case_data in self.database.data.items():
            if not Path(self.path, case_name).is_file():
                remove_list += [case_data]
        for case in remove_list:
            self.database.remove(case['path'], case['file'])

        # find new files:
        for dirpath, dirnames, filenames in os.walk(self.path):
            for filename in fnmatch.filter(filenames, "guitest_*.py"):
                # strip first level of path (./tests/) since this should not be
                # relevant in database:
                path = Path(*Path(dirpath).parts[1:])
                self.database.new(path.as_posix(), filename)
        self.database.store()