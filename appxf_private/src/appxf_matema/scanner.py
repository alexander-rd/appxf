# Test directories need to be scanned for manual_*.py files to initialize the
# test database. In case of renaming or removal, such test cases also must be
# removed. This is done by the Scanner class.
import os
import fnmatch
from pathlib import Path
from .case_data import CaseData


class Scanner():
    def __init__(self,
                 case_data: CaseData,
                 path: str | list[str] = './tests'):
        if isinstance(path, str):
            path = [path]
        self.path = path
        self.database = case_data

    def scan(self):
        # remove files that are not existing anymore
        remove_list = []
        for case_name, case_data in self.database.case_data.items():
            print(f'{case_name}: {case_data}')
            if not Path(case_name).is_file():
                remove_list += [case_name]
        print(f'{self.database.case_data}')
        print(f'{remove_list}')
        for case in remove_list:
            self.database.remove(case)

        # find new files:
        for path in self.path:
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in fnmatch.filter(filenames, "manual_*.py"):
                    # Strip first level of path (./tests/) since this should
                    # not be relevant in database:
                    self.database.new(dirpath, filename)
        self.database.store()
